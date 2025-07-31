"""Human-In-The-Loop (HITL) Manager for automated escalation to human agents."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .confidence_evaluator import confidence_evaluator, ConfidenceResult
from .chatwoot_service import chatwoot_service
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class EscalationResult:
    """Result of an escalation attempt."""

    success: bool
    reason: str
    confidence_score: float
    escalation_time: str
    conversation_id: int
    hotel_id: str
    details: Dict[str, Any]


class HITLManager:
    """Manages Human-In-The-Loop escalations based on AI confidence levels."""

    def __init__(self):
        self.escalation_count = 0
        self.escalation_history: Dict[str, list] = {}

    async def evaluate_and_handle_response(
        self,
        hotel_id: str,
        conversation_id: int,
        ai_response: str,
        user_question: str = "",
        context: str = "",
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate AI response confidence and handle escalation if needed.

        Args:
            hotel_id: Hotel identifier
            conversation_id: Chatwoot conversation ID
            ai_response: The AI agent's generated response
            user_question: Original user question
            context: Conversation context
            confidence_threshold: Custom threshold (uses config default if None)

        Returns:
            Dict with decision, confidence info, and escalation result if applicable
        """
        logger.info(f"🤖 Evaluating response for hotel {hotel_id}, conversation {conversation_id}")

        # Use configured threshold if not provided
        if confidence_threshold is None:
            confidence_threshold = getattr(settings, 'hitl_confidence_threshold', 0.7)

        # Evaluate response confidence
        confidence_result = await confidence_evaluator.evaluate_response_confidence(
            response=ai_response,
            context=context,
            user_question=user_question,
            threshold=confidence_threshold
        )

        result = {
            "should_escalate": confidence_result.should_escalate,
            "confidence_score": confidence_result.confidence_score,
            "confidence_reasons": confidence_result.reasons,
            "threshold_used": confidence_threshold,
            "evaluation_method": confidence_result.evaluation_method,
            "hotel_id": hotel_id,
            "conversation_id": conversation_id,
            "ai_response_length": len(ai_response)
        }

        # If escalation is needed, perform it
        if confidence_result.should_escalate:
            logger.warning(f"🚨 Low confidence detected "f"({confidence_result.confidence_score:.2f} < {confidence_threshold})")

            escalation_result = await self._escalate_to_human(
                hotel_id=hotel_id,
                conversation_id=conversation_id,
                confidence_result=confidence_result,
                ai_response=ai_response,
                user_question=user_question
            )

            result["escalation_result"] = escalation_result
            result["action_taken"] = "escalated_to_human"

        else:
            logger.info(f"✅ High confidence ({confidence_result.confidence_score:.2f} >= {confidence_threshold}), proceeding with AI response")
            result["action_taken"] = "send_ai_response"

        return result

    async def _escalate_to_human(
        self,
        hotel_id: str,
        conversation_id: int,
        confidence_result: ConfidenceResult,
        ai_response: str,
        user_question: str
    ) -> EscalationResult:
        """
        Escalate conversation to human agent by changing status to 'open'.

        Args:
            hotel_id: Hotel identifier
            conversation_id: Conversation to escalate
            confidence_result: Confidence evaluation result
            ai_response: The AI response that triggered escalation
            user_question: Original user question

        Returns:
            EscalationResult with success status and details
        """
        escalation_time = datetime.now().isoformat()

        try:
            logger.info(f"🔀 Escalating conversation {conversation_id} to human agent...")

            # Step 1: Change conversation status to 'open' to trigger auto-assignment
            status_result = await chatwoot_service.mark_conversation_open(
                hotel_id=hotel_id,
                conversation_id=conversation_id
            )

            if not status_result.get("success"):
                logger.error(f"❌ Failed to change conversation status: {status_result}")
                return EscalationResult(
                    success=False,
                    reason="Failed to change conversation status",
                    confidence_score=confidence_result.confidence_score,
                    escalation_time=escalation_time,
                    conversation_id=conversation_id,
                    hotel_id=hotel_id,
                    details=status_result
                )

            # Step 2: Send private note to inform human agent
            escalation_reason = self._format_escalation_reason(
                confidence_result, ai_response, user_question
            )

            note_result = await chatwoot_service.send_message(
                hotel_id=hotel_id,
                conversation_id=conversation_id,
                content=escalation_reason,
                message_type="outgoing",
                private=True  # Private note only visible to agents
            )

            # Step 3: Record escalation
            self._record_escalation(hotel_id, conversation_id, confidence_result)

            logger.info(f"✅ Successfully escalated conversation {conversation_id}")

            return EscalationResult(
                success=True,
                reason="AI confidence below threshold",
                confidence_score=confidence_result.confidence_score,
                escalation_time=escalation_time,
                conversation_id=conversation_id,
                hotel_id=hotel_id,
                details={
                    "status_change": status_result,
                    "private_note": note_result,
                    "confidence_reasons": confidence_result.reasons
                }
            )

        except Exception as e:
            logger.error(f"❌ Escalation failed: {str(e)}")
            import traceback
            logger.error(f"📚 Traceback: {traceback.format_exc()}")

            return EscalationResult(
                success=False,
                reason=f"Escalation error: {str(e)}",
                confidence_score=confidence_result.confidence_score,
                escalation_time=escalation_time,
                conversation_id=conversation_id,
                hotel_id=hotel_id,
                details={"error": str(e)}
            )

    def _format_escalation_reason(
        self,
        confidence_result: ConfidenceResult,
        ai_response: str,
        user_question: str
    ) -> str:
        """Format escalation reason message for human agent."""

        reasons_text = ", ".join(confidence_result.reasons)
        confidence_percentage = f"{confidence_result.confidence_score * 100:.1f}%"

        escalation_message = f"""🤖 **ESCALACIÓN AUTOMÁTICA - Agente IA**

**Motivo:** Confianza baja en la respuesta ({confidence_percentage})
**Razones:** {reasons_text}
**Método:** {confidence_result.evaluation_method}

**Pregunta del usuario:** {user_question[:200]}{'...' if len(user_question) > 200 else ''}

**Respuesta que iba a enviar el AI:**
{ai_response[:300]}{'...' if len(ai_response) > 300 else ''}

Por favor, revisa la conversación y proporciona una respuesta adecuada al cliente."""

        return escalation_message

    def _record_escalation(
        self,
        hotel_id: str,
        conversation_id: int,
        confidence_result: ConfidenceResult
    ):
        """Record escalation for analytics and monitoring."""

        if hotel_id not in self.escalation_history:
            self.escalation_history[hotel_id] = []

        escalation_record = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "confidence_score": confidence_result.confidence_score,
            "reasons": confidence_result.reasons,
            "evaluation_method": confidence_result.evaluation_method
        }

        self.escalation_history[hotel_id].append(escalation_record)
        self.escalation_count += 1

        logger.info(f"📊 Recorded escalation #{self.escalation_count} for hotel {hotel_id}")

    async def get_escalation_stats(self, hotel_id: Optional[str] = None) -> Dict[str, Any]:
        """Get escalation statistics."""

        if hotel_id:
            hotel_escalations = self.escalation_history.get(hotel_id, [])
            return {
                "hotel_id": hotel_id,
                "total_escalations": len(hotel_escalations),
                "recent_escalations": hotel_escalations[-10:],  # Last 10
                "average_confidence": sum(e["confidence_score"] for e in hotel_escalations) / len(hotel_escalations) if hotel_escalations else 0
            }
        else:
            return {
                "total_escalations": self.escalation_count,
                "hotels_with_escalations": len(self.escalation_history),
                "escalation_history": {k: len(v) for k, v in self.escalation_history.items()}
            }

    def is_hitl_enabled(self) -> bool:
        """Check if HITL system is enabled in configuration."""
        return getattr(settings, 'hitl_enabled', True)

    async def force_escalate_conversation(
        self,
        hotel_id: str,
        conversation_id: int,
        reason: str = "Manual escalation"
    ) -> EscalationResult:
        """
        Force escalation of a conversation regardless of confidence level.

        Args:
            hotel_id: Hotel identifier
            conversation_id: Conversation to escalate
            reason: Reason for manual escalation

        Returns:
            EscalationResult
        """
        logger.info(f"🔧 Force escalating conversation {conversation_id}: {reason}")

        # Create artificial confidence result for manual escalation
        confidence_result = ConfidenceResult(
            confidence_score=0.0,
            reasons=[reason],
            should_escalate=True,
            evaluation_method="manual"
        )

        return await self._escalate_to_human(
            hotel_id=hotel_id,
            conversation_id=conversation_id,
            confidence_result=confidence_result,
            ai_response="Manual escalation requested",
            user_question="N/A"
        )


# Global HITL manager instance
hitl_manager = HITLManager()

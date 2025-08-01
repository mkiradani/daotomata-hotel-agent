"""Service for evaluating AI agent response confidence."""

import logging
import re
from typing import List
from dataclasses import dataclass
from openai import AsyncOpenAI

from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')  # Simplified format
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class ConfidenceResult:
    """Result of confidence evaluation."""

    confidence_score: float  # 0.0 to 1.0
    reasons: List[str]  # List of reasons affecting confidence
    should_escalate: bool  # Based on threshold
    evaluation_method: str  # Which method was used


class ConfidenceEvaluator:
    """Evaluates AI agent response confidence to determine if human escalation is needed."""

    # Keywords that indicate uncertainty or low confidence
    UNCERTAINTY_KEYWORDS = [
        "no estoy seguro", "no estoy segura", "no sé", "no se",
        "podría ser", "tal vez", "quizás", "probablemente",
        "creo que", "parece que", "supongo", "asumo",
        "no tengo información", "no puedo confirmar",
        "disculpa", "lo siento", "perdón", "no entiendo",
        "no comprendo", "no está claro", "confuso",
        # Escalation/referral patterns
        "te recomiendo contactar", "te recomiendo hablar", "recomiendo contactar",
        "necesitarías hablar", "deberías contactar", "deberías hablar",
        "hablar con alguien", "contactar con", "hablar directamente",
        "departamento de", "equipo de", "especialista", "especializado",
        "para ayudarte mejor", "más detalles", "información específica",
        "mejor tarifa", "tarifa especial", "condiciones especiales",
        "obtener la mejor", "para obtener", "conseguir la mejor",
        # False action claims (AI claiming to do things it cannot do)
        "he transferido", "he enviado", "he contactado", "he llamado",
        "transferí", "envié", "contacté", "llamé", "comuniqué",
        "se pondrán en contacto", "se comunicarán", "recibirás una llamada",
        "gerente se contactará", "equipo se comunicará", "alguien te contactará",
        # English equivalents
        "I'm not sure", "I don't know", "maybe", "perhaps",
        "probably", "I think", "seems like", "I assume",
        "sorry", "I don't understand", "unclear", "confused",
        "recommend contacting", "recommend speaking", "suggest contacting",
        "you should contact", "speak with someone", "need more details",
        "department", "specialist", "team", "better rate", "special rate",
        "I have transferred", "I have sent", "I have contacted", "I have called",
        "someone will contact", "will get in touch", "will reach out"
    ]

    # Keywords that indicate high confidence
    CONFIDENCE_KEYWORDS = [
        "definitivamente", "seguramente", "ciertamente", "absolutamente",
        "sin duda", "por supuesto", "exactamente", "precisamente",
        "confirmo", "garantizo", "aseguro", "certifica",
        "definitely", "certainly", "absolutely", "surely",
        "without doubt", "of course", "exactly", "precisely",
        "confirm", "guarantee", "assure", "certified"
    ]

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def evaluate_response_confidence(
        self,
        response: str,
        context: str = "",
        user_question: str = "",
        threshold: float = 0.7
    ) -> ConfidenceResult:
        """
        Evaluate the confidence level of an AI agent response.

        Args:
            response: The AI agent's response to evaluate
            context: Optional context about the conversation
            user_question: The original user question
            threshold: Confidence threshold for escalation decision (default: 0.7)

        Returns:
            ConfidenceResult with confidence score and escalation recommendation
        """
        logger.info(f"🔍 Evaluating confidence: {len(response)} chars, threshold={threshold}")

        # Step 1: Check for empty or error responses
        if self._is_empty_or_error_response(response):
            logger.warning("⚠️ Empty or error response detected")
            return ConfidenceResult(
                confidence_score=0.0,
                reasons=["Empty or error response"],
                should_escalate=True,
                evaluation_method="error_detection"
            )
        
        # Step 2: Check if request requires special handling (groups, events, etc.)
        if self._requires_special_handling(user_question, response):
            logger.warning("⚠️ Special handling required - escalating")
            return ConfidenceResult(
                confidence_score=0.3,
                reasons=["Large group or complex request requiring specialist"],
                should_escalate=True,
                evaluation_method="special_handling_detection"
            )

        # Step 3: Keyword analysis
        keyword_confidence, keyword_reasons = self._analyze_keywords(response)

        # Step 4: LLM self-evaluation
        try:
            llm_confidence, llm_reasons = await self._llm_self_evaluation(
                response, context, user_question
            )
        except Exception as e:
            logger.error(f"❌ LLM evaluation failed: {str(e)}")
            llm_confidence = keyword_confidence
            llm_reasons = ["LLM evaluation unavailable"]

        # Step 5: Combine scores (weighted average)
        # Keyword analysis: 30%, LLM evaluation: 70%
        final_confidence = (keyword_confidence * 0.3) + (llm_confidence * 0.7)

        # Combine reasons
        all_reasons = keyword_reasons + llm_reasons

        should_escalate = final_confidence < threshold

        result = ConfidenceResult(
            confidence_score=final_confidence,
            reasons=all_reasons,
            should_escalate=should_escalate,
            evaluation_method="hybrid"
        )

        logger.info(f"📊 Confidence: {final_confidence:.2f} ({'ESCALATE' if should_escalate else 'PROCEED'}) - {', '.join(all_reasons[:2])}{'...' if len(all_reasons) > 2 else ''}")

        return result

    def _requires_special_handling(self, user_question: str, response: str) -> bool:
        """Check if the request requires special handling that should trigger escalation."""
        combined_text = (user_question + " " + response).lower()
        
        # Check for large group requests
        import re
        # Match patterns like "20 personas", "grupo de 15", "group of 20", etc.
        group_patterns = [
            r'\b(\d+)\s*personas\b',
            r'\bgrupo\s+de\s+(\d+)\b',
            r'\bgroup\s+of\s+(\d+)\b',
            r'\bpara\s+(\d+)\s+personas\b',
            r'\b(\d+)\s+people\b',
            r'\b(\d+)\s+guests\b'
        ]
        
        for pattern in group_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                try:
                    num_people = int(match)
                    if num_people >= 10:  # Groups of 10+ should escalate
                        logger.info(f"🚨 Large group detected: {num_people} people")
                        return True
                except ValueError:
                    continue
        
        # Check if AI is claiming to be a specialist for complex requests
        if any(phrase in combined_text for phrase in ["retiro", "evento corporativo", "conferencia", "retreat", "corporate event"]):
            if any(claim in response.lower() for claim in ["soy el especialista", "soy especialista", "puedo ayudarte con", "estoy aquí para ayudarte"]):
                logger.info("🚨 AI claiming expertise for complex request")
                return True
        
        return False

    def _is_empty_or_error_response(self, response: str) -> bool:
        """Check if response is empty, error, or placeholder."""
        if not response or not response.strip():
            return True

        # Check for common error patterns
        error_patterns = [
            r"error",
            r"exception",
            r"failed to",
            r"unable to",
            r"cannot process",
            r"something went wrong",
            r"internal error",
            r"timeout",
            r"service unavailable"
        ]

        response_lower = response.lower()
        for pattern in error_patterns:
            if re.search(pattern, response_lower):
                return True

        # Check if response is too short to be meaningful
        if len(response.strip()) < 10:
            return True

        return False

    def _analyze_keywords(self, response: str) -> tuple[float, List[str]]:
        """Analyze response for uncertainty/confidence keywords."""
        response_lower = response.lower()
        reasons = []

        # Count uncertainty keywords
        uncertainty_count = 0
        found_uncertainty = []
        for keyword in self.UNCERTAINTY_KEYWORDS:
            if keyword in response_lower:
                uncertainty_count += 1
                found_uncertainty.append(keyword)

        # Count confidence keywords
        confidence_count = 0
        found_confidence = []
        for keyword in self.CONFIDENCE_KEYWORDS:
            if keyword in response_lower:
                confidence_count += 1
                found_confidence.append(keyword)

        # Calculate base confidence (start with 0.8 as baseline)
        base_confidence = 0.8

        # Decrease confidence for uncertainty keywords
        # Give higher penalty for escalation/referral keywords  
        escalation_keywords = [
            "te recomiendo contactar", "te recomiendo hablar", "recomiendo contactar",
            "departamento de", "contactar con", "mejor tarifa", "para obtener",
            # False action claims - AI claiming to do actions it cannot perform
            "he transferido", "he enviado", "he contactado", "he llamado",
            "se pondrán en contacto", "se comunicarán", "gerente se contactará"
        ]
        
        escalation_found = any(keyword in response_lower for keyword in escalation_keywords)
        
        if escalation_found:
            # Strong penalty for escalation patterns - should trigger escalation
            confidence_penalty = min(uncertainty_count * 0.3, 0.8)  # Higher penalty for escalations
        else:
            confidence_penalty = min(uncertainty_count * 0.2, 0.6)  # Normal penalty

        # Increase confidence for confidence keywords
        confidence_bonus = min(confidence_count * 0.1, 0.2)  # Max bonus: 0.2

        final_confidence = max(0.0, min(1.0, base_confidence - confidence_penalty + confidence_bonus))

        # Add reasons
        if found_uncertainty:
            reasons.append(f"Uncertainty keywords: {', '.join(found_uncertainty[:3])}")
        if found_confidence:
            reasons.append(f"Confidence keywords: {', '.join(found_confidence[:3])}")
        if not found_uncertainty and not found_confidence:
            reasons.append("No strong confidence indicators")

        return final_confidence, reasons

    async def _llm_self_evaluation(
        self,
        response: str,
        context: str,
        user_question: str
    ) -> tuple[float, List[str]]:
        """Use LLM to evaluate its own response confidence."""

        evaluation_prompt = f"""
Evalúa la confianza de esta respuesta de un agente de hotel AI en una escala de 0.0 a 1.0.

PREGUNTA DEL USUARIO: {user_question}

CONTEXTO ADICIONAL: {context}

RESPUESTA A EVALUAR: {response}

Considera estos factores:
1. ¿La respuesta es específica y directa?
2. ¿Contiene información precisa y verificable?
3. ¿Hay palabras de incertidumbre o dudas?
4. ¿La respuesta resuelve completamente la pregunta?
5. ¿El agente admite no saber algo?

Responde SOLO con este formato JSON:
{{
    "confidence": 0.85,
    "reasons": ["Respuesta específica", "Información verificable", "Sin incertidumbres"]
}}
"""

        try:
            evaluation_model = getattr(settings, 'HITL_EVALUATION_MODEL', 'gpt-4o-mini')
            response_obj = await self.openai_client.chat.completions.create(
                model=evaluation_model,
                messages=[
                    {"role": "system", "content": "Eres un evaluador experto de confianza en respuestas de AI. Responde siempre con JSON válido."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            result_text = response_obj.choices[0].message.content.strip()
            # Removed verbose debug logging

            # Parse JSON response
            import json
            result_data = json.loads(result_text)

            confidence = float(result_data.get("confidence", 0.5))
            reasons = result_data.get("reasons", ["LLM evaluation completed"])

            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, confidence))

            return confidence, reasons

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM evaluation JSON: {str(e)}")
            return 0.5, ["LLM evaluation parse error"]
        except Exception as e:
            logger.error(f"❌ LLM evaluation error: {str(e)}")
            return 0.5, ["LLM evaluation failed"]

    async def should_escalate_conversation(
        self,
        response: str,
        context: str = "",
        user_question: str = "",
        threshold: float = 0.7
    ) -> bool:
        """
        Quick method to determine if conversation should be escalated.

        Returns:
            True if conversation should be escalated to human agent
        """
        result = await self.evaluate_response_confidence(
            response, context, user_question, threshold
        )
        return result.should_escalate


# Global confidence evaluator instance
confidence_evaluator = ConfidenceEvaluator()

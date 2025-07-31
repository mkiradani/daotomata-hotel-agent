"""Tests for HITL (Human-In-The-Loop) integration."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from app.services.confidence_evaluator import ConfidenceEvaluator, ConfidenceResult
from app.services.hitl_manager import HITLManager, EscalationResult
from app.services.chatwoot_service import ChatwootService


class TestConfidenceEvaluator:
    """Test confidence evaluation functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.evaluator = ConfidenceEvaluator()
    
    @pytest.mark.asyncio
    async def test_high_confidence_response(self):
        """Test response with high confidence keywords."""
        response = "Definitivamente tenemos disponibilidad para el 15 de enero. El precio es exactamente $120 por noche."
        user_question = "¿Tienen disponibilidad para el 15 de enero?"
        
        with patch.object(self.evaluator, '_llm_self_evaluation', return_value=(0.9, ["High confidence response"])):
            result = await self.evaluator.evaluate_response_confidence(
                response=response,
                user_question=user_question,
                threshold=0.7
            )
        
        assert result.confidence_score > 0.7
        assert not result.should_escalate
        assert "hybrid" in result.evaluation_method
    
    @pytest.mark.asyncio
    async def test_low_confidence_response(self):
        """Test response with uncertainty keywords."""
        response = "No estoy seguro si tenemos disponibilidad. Tal vez podría verificar con recepción."
        user_question = "¿Tienen disponibilidad para mañana?"
        
        with patch.object(self.evaluator, '_llm_self_evaluation', return_value=(0.3, ["Uncertain response"])):
            result = await self.evaluator.evaluate_response_confidence(
                response=response,
                user_question=user_question,
                threshold=0.7
            )
        
        assert result.confidence_score < 0.7
        assert result.should_escalate
        assert any("Uncertainty keywords" in reason for reason in result.reasons)
    
    @pytest.mark.asyncio
    async def test_empty_response_detection(self):
        """Test detection of empty or error responses."""
        empty_responses = ["", "   ", "Error occurred", "Unable to process", "Service unavailable"]
        
        for response in empty_responses:
            result = await self.evaluator.evaluate_response_confidence(
                response=response,
                user_question="Test question",
                threshold=0.7
            )
            
            assert result.confidence_score == 0.0
            assert result.should_escalate
            assert result.evaluation_method == "error_detection"
    
    def test_keyword_analysis(self):
        """Test keyword analysis functionality."""
        # Test uncertainty keywords
        uncertainty_response = "No sé si podemos hacer eso. Quizás sea posible."
        confidence, reasons = self.evaluator._analyze_keywords(uncertainty_response)
        assert confidence < 0.7
        assert any("Uncertainty keywords" in reason for reason in reasons)
        
        # Test confidence keywords
        confident_response = "Definitivamente podemos confirmar esa reserva. Absolutamente garantizado."
        confidence, reasons = self.evaluator._analyze_keywords(confident_response)
        assert confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_llm_evaluation_fallback(self):
        """Test LLM evaluation with API failure."""
        response = "Test response for evaluation"
        
        with patch.object(self.evaluator.openai_client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = await self.evaluator.evaluate_response_confidence(
                response=response,
                user_question="Test question",
                threshold=0.7
            )
        
        # Should fall back to keyword analysis
        assert result.confidence_score >= 0.0
        assert any("LLM evaluation" in reason for reason in result.reasons)


class TestHITLManager:
    """Test HITL manager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.hitl_manager = HITLManager()
    
    @pytest.mark.asyncio
    async def test_high_confidence_no_escalation(self):
        """Test that high confidence responses don't trigger escalation."""
        with patch('app.services.hitl_manager.confidence_evaluator') as mock_evaluator:
            mock_evaluator.evaluate_response_confidence.return_value = ConfidenceResult(
                confidence_score=0.9,
                reasons=["High confidence"],
                should_escalate=False,
                evaluation_method="test"
            )
            
            result = await self.hitl_manager.evaluate_and_handle_response(
                hotel_id="1",
                conversation_id=123,
                ai_response="Tenemos disponibilidad confirmada",
                user_question="¿Tienen habitaciones?"
            )
            
            assert not result["should_escalate"]
            assert result["action_taken"] == "send_ai_response"
            assert result["confidence_score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_low_confidence_escalation(self):
        """Test that low confidence responses trigger escalation."""
        with patch('app.services.hitl_manager.confidence_evaluator') as mock_evaluator, \
             patch.object(self.hitl_manager, '_escalate_to_human') as mock_escalate:
            
            mock_evaluator.evaluate_response_confidence.return_value = ConfidenceResult(
                confidence_score=0.3,
                reasons=["Low confidence", "Uncertainty detected"],
                should_escalate=True,
                evaluation_method="test"
            )
            
            mock_escalate.return_value = EscalationResult(
                success=True,
                reason="Low confidence",
                confidence_score=0.3,
                escalation_time="2024-01-01T10:00:00",
                conversation_id=123,
                hotel_id="1",
                details={}
            )
            
            result = await self.hitl_manager.evaluate_and_handle_response(
                hotel_id="1",
                conversation_id=123,
                ai_response="No estoy seguro de la disponibilidad",
                user_question="¿Tienen habitaciones?"
            )
            
            assert result["should_escalate"]
            assert result["action_taken"] == "escalated_to_human"
            assert result["confidence_score"] == 0.3
            mock_escalate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_escalation_to_human(self):
        """Test the escalation process to human agents."""
        confidence_result = ConfidenceResult(
            confidence_score=0.3,
            reasons=["Low confidence"],
            should_escalate=True,
            evaluation_method="test"
        )
        
        with patch('app.services.hitl_manager.chatwoot_service') as mock_chatwoot:
            # Mock successful status change
            mock_chatwoot.mark_conversation_open.return_value = {
                "success": True,
                "conversation_id": 123,
                "status": "open",
                "hotel_id": "1"
            }
            
            # Mock successful private note
            mock_chatwoot.send_message.return_value = {
                "success": True,
                "message_id": "msg_123"
            }
            
            result = await self.hitl_manager._escalate_to_human(
                hotel_id="1",
                conversation_id=123,
                confidence_result=confidence_result,
                ai_response="Uncertain response",
                user_question="Test question"
            )
            
            assert result.success
            assert result.conversation_id == 123
            assert result.hotel_id == "1"
            assert result.confidence_score == 0.3
            
            # Verify Chatwoot service calls
            mock_chatwoot.mark_conversation_open.assert_called_once_with(
                hotel_id="1",
                conversation_id=123
            )
            mock_chatwoot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_escalation_failure_handling(self):
        """Test handling of escalation failures."""
        confidence_result = ConfidenceResult(
            confidence_score=0.3,
            reasons=["Low confidence"],
            should_escalate=True,
            evaluation_method="test"
        )
        
        with patch('app.services.hitl_manager.chatwoot_service') as mock_chatwoot:
            # Mock failed status change
            mock_chatwoot.mark_conversation_open.return_value = {
                "success": False,
                "error": "API Error"
            }
            
            result = await self.hitl_manager._escalate_to_human(
                hotel_id="1",
                conversation_id=123,
                confidence_result=confidence_result,
                ai_response="Uncertain response",
                user_question="Test question"
            )
            
            assert not result.success
            assert "Failed to change conversation status" in result.reason
    
    def test_escalation_reason_formatting(self):
        """Test escalation reason message formatting."""
        confidence_result = ConfidenceResult(
            confidence_score=0.4,
            reasons=["Uncertainty keywords", "Low confidence"],
            should_escalate=True,
            evaluation_method="hybrid"
        )
        
        reason = self.hitl_manager._format_escalation_reason(
            confidence_result=confidence_result,
            ai_response="Test AI response",
            user_question="Test user question"
        )
        
        assert "ESCALACIÓN AUTOMÁTICA" in reason
        assert "40.0%" in reason  # confidence percentage
        assert "Uncertainty keywords" in reason
        assert "Test user question" in reason
        assert "Test AI response" in reason
    
    @pytest.mark.asyncio
    async def test_force_escalation(self):
        """Test manual/forced escalation."""
        with patch.object(self.hitl_manager, '_escalate_to_human') as mock_escalate:
            mock_escalate.return_value = EscalationResult(
                success=True,
                reason="Manual escalation",
                confidence_score=0.0,
                escalation_time="2024-01-01T10:00:00",
                conversation_id=123,
                hotel_id="1",
                details={}
            )
            
            result = await self.hitl_manager.force_escalate_conversation(
                hotel_id="1",
                conversation_id=123,
                reason="Customer request"
            )
            
            assert result.success
            assert result.reason == "Manual escalation"
            mock_escalate.assert_called_once()
    
    def test_escalation_statistics(self):
        """Test escalation statistics tracking."""
        # Record some escalations
        self.hitl_manager._record_escalation(
            hotel_id="1",
            conversation_id=123,
            confidence_result=ConfidenceResult(0.3, ["test"], True, "test")
        )
        
        self.hitl_manager._record_escalation(
            hotel_id="1",
            conversation_id=124,
            confidence_result=ConfidenceResult(0.4, ["test"], True, "test")
        )
        
        # Test hotel-specific stats
        stats = asyncio.run(self.hitl_manager.get_escalation_stats("1"))
        assert stats["hotel_id"] == "1"
        assert stats["total_escalations"] == 2
        assert stats["average_confidence"] == 0.35
        
        # Test global stats
        global_stats = asyncio.run(self.hitl_manager.get_escalation_stats())
        assert global_stats["total_escalations"] == 2
        assert global_stats["hotels_with_escalations"] == 1
    
    def test_hitl_enabled_configuration(self):
        """Test HITL enabled/disabled configuration."""
        with patch('app.services.hitl_manager.settings') as mock_settings:
            mock_settings.hitl_enabled = True
            assert self.hitl_manager.is_hitl_enabled()
            
            mock_settings.hitl_enabled = False
            assert not self.hitl_manager.is_hitl_enabled()


class TestChatwootServiceHITL:
    """Test Chatwoot service HITL extensions."""
    
    def setup_method(self):
        """Setup test environment."""
        self.service = ChatwootService()
        # Add test config
        from app.services.chatwoot_service import ChatwootConfig
        self.service.add_hotel_config("1", ChatwootConfig(
            base_url="https://test.chatwoot.com",
            api_access_token="test_token",
            account_id=1
        ))
    
    @pytest.mark.asyncio
    async def test_mark_conversation_open(self):
        """Test marking conversation as open for human assignment."""
        with patch.object(self.service.http_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "open"}
            mock_post.return_value = mock_response
            
            result = await self.service.mark_conversation_open(
                hotel_id="1",
                conversation_id=123
            )
            
            assert result["success"]
            assert result["status"] == "open"
            assert result["conversation_id"] == 123
            
            # Verify API call
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert "toggle_status" in args[0]
            assert kwargs["json"]["status"] == "open"
    
    @pytest.mark.asyncio
    async def test_mark_conversation_open_failure(self):
        """Test handling of failed conversation status change."""
        with patch.object(self.service.http_client, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            result = await self.service.mark_conversation_open(
                hotel_id="1",
                conversation_id=123
            )
            
            assert not result["success"]
            assert "Chatwoot API error: 400" in result["error"]
            assert result["error_details"] == "Bad Request"
    
    @pytest.mark.asyncio
    async def test_send_private_note(self):
        """Test sending private notes to agents."""
        with patch.object(self.service, 'send_message') as mock_send:
            mock_send.return_value = {"success": True, "message_id": "msg_123"}
            
            result = await self.service.send_private_note(
                hotel_id="1",
                conversation_id=123,
                content="Private note for agent"
            )
            
            assert result["success"]
            mock_send.assert_called_once_with(
                hotel_id="1",
                conversation_id=123,
                content="Private note for agent",
                message_type="outgoing",
                private=True
            )
    
    @pytest.mark.asyncio
    async def test_get_conversation_status(self):
        """Test getting conversation status."""
        with patch.object(self.service, 'get_conversation') as mock_get:
            mock_get.return_value = {
                "success": True,
                "conversation": {
                    "status": "open",
                    "assignee": {"id": 1, "name": "Agent Smith"}
                }
            }
            
            result = await self.service.get_conversation_status(
                hotel_id="1",
                conversation_id=123
            )
            
            assert result["success"]
            assert result["status"] == "open"
            assert result["assignee"]["name"] == "Agent Smith"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
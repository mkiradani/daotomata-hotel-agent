"""Tests for webhook endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_chatwoot_webhook_test_endpoint():
    """Test the Chatwoot webhook test endpoint."""
    hotel_id = "test_hotel_123"
    response = client.get(f"/webhook/chatwoot/test/{hotel_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["hotel_id"] == hotel_id
    assert data["webhook_url"] == f"/webhook/chatwoot/{hotel_id}"


def test_chatwoot_webhook_with_valid_message():
    """Test Chatwoot webhook with valid message payload."""
    hotel_id = "test_hotel_456"
    
    payload = {
        "event": "message_created",
        "content": "Hello, I need help with my booking",
        "conversation": {
            "id": "conv_123"
        },
        "sender": {
            "type": "contact",
            "id": "contact_789",
            "name": "John Doe"
        }
    }
    
    response = client.post(f"/webhook/chatwoot/{hotel_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["hotel_id"] == hotel_id
    assert "response" in data
    assert "session_id" in data


def test_chatwoot_webhook_ignores_agent_messages():
    """Test that webhook ignores messages from agents."""
    hotel_id = "test_hotel_789"
    
    payload = {
        "event": "message_created",
        "content": "Agent response",
        "conversation": {
            "id": "conv_456"
        },
        "sender": {
            "type": "user",  # Agent type
            "id": "agent_123",
            "name": "Support Agent"
        }
    }
    
    response = client.post(f"/webhook/chatwoot/{hotel_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "agent" in data["reason"].lower()


def test_chatwoot_webhook_ignores_non_message_events():
    """Test that webhook ignores non-message events."""
    hotel_id = "test_hotel_abc"
    
    payload = {
        "event": "conversation_updated",
        "conversation": {
            "id": "conv_789"
        }
    }
    
    response = client.post(f"/webhook/chatwoot/{hotel_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "Event type" in data["reason"]


def test_chatwoot_webhook_with_empty_payload():
    """Test webhook with empty payload."""
    hotel_id = "test_hotel_xyz"
    
    response = client.post(f"/webhook/chatwoot/{hotel_id}", json=None)
    
    # FastAPI returns 422 for validation errors, not 400
    assert response.status_code == 422
    # Check for validation error in the response
    assert "detail" in response.json()


def test_chatwoot_webhook_hotel_id_passed_to_chat_service():
    """Test that hotel_id from URL is properly passed to chat service."""
    hotel_id = "specific_hotel_999"
    
    payload = {
        "event": "message_created",
        "content": "What's the hotel name?",
        "conversation": {
            "id": "conv_test"
        },
        "sender": {
            "type": "contact",
            "id": "contact_test",
            "name": "Test Guest"
        }
    }
    
    response = client.post(f"/webhook/chatwoot/{hotel_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["hotel_id"] == hotel_id
    # The session_id should include the conversation ID from Chatwoot
    assert "chatwoot_conv_test" in data["session_id"]
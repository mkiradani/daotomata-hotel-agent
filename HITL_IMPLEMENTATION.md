# HITL (Human-In-The-Loop) Implementation Guide

## 📋 Overview

Esta implementación añade capacidades de escalación automática al agente de hotel para transferir conversaciones a agentes humanos cuando el AI tiene baja confianza en sus respuestas.

## 🏗️ Architecture

### Core Components

1. **ConfidenceEvaluator** (`app/services/confidence_evaluator.py`)
   - Evalúa la confianza de las respuestas del AI (0.0-1.0)
   - Usa análisis de palabras clave + autoevaluación LLM
   - Detecta respuestas vacías o errores

2. **HITLManager** (`app/services/hitl_manager.py`)
   - Maneja la lógica de escalación basada en threshold
   - Integra con ChatwootService para cambio de status
   - Registra estadísticas de escalaciones

3. **ChatwootService Extensions** (`app/services/chatwoot_service.py`)
   - `mark_conversation_open()`: Cambia status a "open"
   - `send_private_note()`: Envía notas privadas a agentes
   - `get_conversation_status()`: Consulta status actual

4. **Integration Layer** (`app/services/chat_service_mcp.py`)
   - Integra evaluación HITL en el flujo principal
   - Modifica respuestas cuando hay escalación
   - Mantiene compatibilidad con sistema existente

## 🔄 Flow Diagram

```
Usuario → Mensaje → Agente AI → Genera Respuesta
                                      ↓
                           Evaluar Confianza
                                      ↓
                   ¿Confianza < Threshold (0.7)?
                          ↙              ↘
                        SÍ               NO
                         ↓                ↓
              Escalar a Humano      Enviar Respuesta AI
                         ↓
              1. Cambiar status → "open"
              2. Enviar nota privada
              3. Notificar usuario
              4. Chatwoot asigna agente
```

## ⚙️ Configuration

### Environment Variables

```bash
# Enable/disable HITL system
HITL_ENABLED=true

# Confidence threshold (0.0-1.0)
HITL_CONFIDENCE_THRESHOLD=0.7

# Model for confidence evaluation
HITL_EVALUATION_MODEL=gpt-4o-mini
```

### Per-Hotel Configuration

No se requiere configuración adicional por hotel. El sistema usa las configuraciones existentes de Chatwoot almacenadas en Directus.

## 🔧 Implementation Details

### Confidence Evaluation

#### Keyword Analysis (30% weight)
```python
UNCERTAINTY_KEYWORDS = [
    "no estoy seguro", "no sé", "tal vez", "quizás", 
    "creo que", "parece que", "no tengo información"
]

CONFIDENCE_KEYWORDS = [
    "definitivamente", "seguramente", "sin duda", 
    "confirmo", "garantizo", "absolutamente"
]
```

#### LLM Self-Evaluation (70% weight)
- Usa GPT-4o-mini para autoevaluación
- Considera contexto y pregunta original
- Retorna score 0.0-1.0 con razones

#### Error Detection
- Respuestas vacías o muy cortas
- Patrones de error ("error", "failed", "timeout")
- Respuestas de servicio no disponible

### Escalation Process

1. **Status Change**: Conversación → "open" (trigger auto-assignment)
2. **Private Note**: Información para agente humano
3. **User Notification**: Respuesta modificada informando escalación
4. **Logging**: Registro para analytics y monitoring

### Message Templates

#### Escalation Note (Private)
```
🤖 **ESCALACIÓN AUTOMÁTICA - Agente IA**

**Motivo:** Confianza baja en la respuesta (X%)
**Razones:** [lista de razones]
**Método:** [método de evaluación]

**Pregunta del usuario:** [pregunta original]
**Respuesta que iba a enviar el AI:** [respuesta original]

Por favor, revisa la conversación y proporciona una respuesta adecuada al cliente.
```

#### User Notification
```
He transferido tu consulta a uno de nuestros agentes humanos 
para brindarte la mejor asistencia posible. Un miembro de nuestro 
equipo se pondrá en contacto contigo muy pronto.

Mientras tanto, aquí tienes la información que pude recopilar:
[respuesta AI original]
```

## 🧪 Testing

### Unit Tests (`tests/test_hitl_integration.py`)

- **ConfidenceEvaluator Tests**
  - High/low confidence responses
  - Empty response detection
  - Keyword analysis
  - LLM evaluation fallback

- **HITLManager Tests**
  - Escalation logic
  - Chatwoot integration
  - Error handling
  - Statistics tracking

- **ChatwootService Tests**
  - Status change operations
  - Private note sending
  - API error handling

### Running Tests

```bash
# Run specific HITL tests
pytest tests/test_hitl_integration.py -v

# Run with coverage
pytest tests/test_hitl_integration.py --cov=app.services.confidence_evaluator --cov=app.services.hitl_manager
```

## 🔍 Monitoring & Analytics

### Escalation Statistics

```python
# Hotel-specific stats
await hitl_manager.get_escalation_stats("hotel_id")

# Global stats
await hitl_manager.get_escalation_stats()
```

### Logging

El sistema registra logs detallados en todos los niveles:
- 🔍 Evaluación de confianza
- 🚨 Decisiones de escalación
- ✅ Éxito/fallo de operaciones Chatwoot
- 📊 Métricas y estadísticas

## 🚀 Deployment

### 1. Environment Setup
```bash
# Add to .env
HITL_ENABLED=true
HITL_CONFIDENCE_THRESHOLD=0.7
HITL_EVALUATION_MODEL=gpt-4o-mini
```

### 2. Chatwoot Configuration
Asegurar que cada hotel tiene configurado en Directus:
- `chatwoot_base_url`
- `chatwoot_api_access_token`
- `chatwoot_account_id`

### 3. Restart Services
```bash
# Restart the application
docker-compose restart hotel-agent
```

## 🔧 Troubleshooting

### Common Issues

1. **HITL Not Triggering**
   - Verificar `HITL_ENABLED=true`
   - Revisar logs de evaluación de confianza
   - Confirmar que conversation_id está presente

2. **Chatwoot API Errors**
   - Verificar tokens de API válidos
   - Confirmar account_id correcto
   - Revisar logs de ChatwootService

3. **High False Positive Rate**
   - Ajustar `HITL_CONFIDENCE_THRESHOLD`
   - Revisar keywords de incertidumbre
   - Analizar logs de evaluación LLM

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("app.services.hitl_manager").setLevel(logging.DEBUG)
logging.getLogger("app.services.confidence_evaluator").setLevel(logging.DEBUG)
```

## 📈 Performance Impact

- **Latency**: +200-500ms per message (LLM evaluation)
- **API Calls**: +1 OpenAI call per message
- **Memory**: Minimal (~50KB per session)
- **Storage**: Escalation history in memory (configurable)

## 🔮 Future Enhancements

1. **Persistent Analytics**
   - Store escalation metrics in database
   - Dashboard for monitoring escalation rates

2. **Advanced Confidence Models**
   - Training custom confidence models
   - Context-aware thresholds

3. **Multi-language Support**
   - Language-specific uncertainty keywords
   - Localized escalation messages

4. **Agent Workload Balancing**
   - Smart agent assignment based on availability
   - Skill-based routing integration

## 📚 API Reference

### HITLManager

```python
# Evaluate and handle response
result = await hitl_manager.evaluate_and_handle_response(
    hotel_id="1",
    conversation_id=123,
    ai_response="Response text",
    user_question="User question",
    context="Conversation context"
)

# Force escalation
await hitl_manager.force_escalate_conversation(
    hotel_id="1",
    conversation_id=123,
    reason="Customer request"
)

# Get statistics
stats = await hitl_manager.get_escalation_stats("hotel_id")
```

### ConfidenceEvaluator

```python
# Evaluate confidence
result = await confidence_evaluator.evaluate_response_confidence(
    response="AI response",
    context="Conversation context",
    user_question="Original question",
    threshold=0.7
)

# Quick escalation check
should_escalate = await confidence_evaluator.should_escalate_conversation(
    response="AI response",
    threshold=0.7
)
```

### ChatwootService

```python
# Mark conversation as open
await chatwoot_service.mark_conversation_open(
    hotel_id="1",
    conversation_id=123
)

# Send private note
await chatwoot_service.send_private_note(
    hotel_id="1",
    conversation_id=123,
    content="Private message for agents"
)
```

---

## ✅ Implementation Status

- [x] ConfidenceEvaluator service
- [x] HITLManager service  
- [x] ChatwootService extensions
- [x] Integration with chat service
- [x] Configuration setup
- [x] Comprehensive testing
- [x] Webhook integration
- [x] Documentation complete

**Sistema HITL completamente implementado y listo para producción.**
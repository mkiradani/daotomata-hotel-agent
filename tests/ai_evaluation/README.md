# AI Evaluation Suite for Hotel Agent

Sistema completo de evaluación con AI para probar conversaciones del agente hotelero, validar respuestas y generar análisis detallados.

## 🎯 Características

### ✅ Funcionalidades Implementadas

- **Simulador de Conversaciones**: Simula interacciones reales entre clientes y el agente hotelero
- **Evaluación con AI**: Usa GPT-4 para evaluar la calidad, precisión y utilidad de las respuestas
- **Pruebas de Herramientas**: Verifica el funcionamiento de todas las herramientas del agente
- **Sistema de Logging**: Registro completo y detallado de todas las interacciones y evaluaciones
- **Evaluación Secundaria**: AI adicional que analiza los resultados y patrones del sistema
- **Múltiples Hoteles**: Soporte para probar diferentes configuraciones hoteleras
- **Exportación de Datos**: Resultados en JSON, CSV y reportes detallados

### 🏨 Hoteles de Prueba Configurados

1. **Hotel Madrid Palace** (Madrid) - Hotel de lujo con spa, gym, piscina
2. **Barcelona Beach Resort** (Barcelona) - Resort costero con acceso a playa
3. **Sevilla Heritage Hotel** (Sevilla) - Hotel boutique histórico

### 🎭 Escenarios de Prueba

1. **basic_info_inquiry** - Consulta de información básica del hotel
2. **availability_check** - Verificación de disponibilidad de habitaciones  
3. **weather_and_activities** - Consulta del clima y actividades locales
4. **service_request** - Solicitud de servicios del hotel
5. **complex_multi_tool** - Escenario complejo que requiere múltiples herramientas

### 🛠️ Herramientas Probadas

- `get_hotel_info` - Información del hotel
- `check_room_availability` - Disponibilidad de habitaciones
- `get_hotel_activities` - Actividades disponibles
- `get_hotel_facilities` - Instalaciones del hotel
- `get_local_weather` - Información meteorológica
- `request_hotel_service` - Solicitud de servicios
- Herramientas PMS (Cloudbeds integration)

## 🚀 Uso Rápido

### Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar API key de OpenAI
export OPENAI_API_KEY="tu_api_key_aquí"
```

### Ejecutar Evaluación Completa

```bash
# Evaluación completa (herramientas + conversaciones + análisis secundario)
python -m tests.ai_evaluation.main --run-all

# Solo pruebas de herramientas
python -m tests.ai_evaluation.main --tools-only

# Solo conversaciones y evaluación
python -m tests.ai_evaluation.main --conversations-only

# Escenarios específicos
python -m tests.ai_evaluation.main --conversations-only --scenarios basic_info_inquiry availability_check

# Hoteles específicos
python -m tests.ai_evaluation.main --run-all --hotels hotel_madrid_luxury
```

## 📊 Resultados y Análisis

### Archivos Generados

```
logs/ai_evaluation/
├── conversations_YYYYMMDD_HHMMSS.jsonl    # Conversaciones detalladas
├── evaluations_YYYYMMDD_HHMMSS.jsonl      # Evaluaciones AI
├── results_YYYYMMDD_HHMMSS.csv            # Resultados en CSV
├── summary_YYYYMMDD_HHMMSS.json           # Resumen de sesión
├── system_YYYYMMDD_HHMMSS.log             # Logs del sistema
├── tool_test_results_YYYYMMDD_HHMMSS.json # Resultados de herramientas
└── secondary_analysis_report_YYYYMMDD_HHMMSS.json # Análisis secundario
```

### Métricas de Evaluación

- **Overall Score** (0.0-1.0): Puntuación general de la conversación
- **Accuracy**: Precisión de la información proporcionada
- **Helpfulness**: Utilidad de las respuestas para el cliente
- **Tool Usage**: Uso apropiado de las herramientas disponibles
- **Conversation Flow**: Fluidez y coherencia de la conversación
- **Politeness**: Profesionalidad y cortesía en el trato

### Análisis Secundario

El evaluador secundario proporciona:

- **Pattern Analysis**: Patrones de éxito y fallo
- **System Performance Score**: Puntuación general del sistema
- **Key Findings**: Hallazgos más importantes
- **Strategic Recommendations**: Recomendaciones de mejora
- **Quality Assessment**: Evaluación de la calidad del sistema de evaluación

## 🔧 Configuración Avanzada

### Añadir Nuevos Hoteles

Edita `tests/ai_evaluation/config.py`:

```python
TEST_HOTELS.append(HotelConfig(
    id=\"nuevo_hotel_id\",
    name=\"Nuevo Hotel\",
    city=\"Ciudad\",
    coordinates=(lat, lon),
    contact_email=\"contacto@hotel.com\",
    contact_phone=\"+34 XXX XXX XXX\",
    description=\"Descripción del hotel\",
    facilities=[\"spa\", \"gym\", \"pool\"],
    activities=[...]
))
```

### Añadir Nuevos Escenarios

```python
TEST_SCENARIOS.append(ConversationScenario(
    scenario_id=\"nuevo_escenario\",
    hotel_id=\"hotel_id\",
    title=\"Título del Escenario\",
    description=\"Descripción detallada\",
    initial_message=\"Mensaje inicial del cliente\",
    expected_tools=[\"tool1\", \"tool2\"],
    success_criteria=[\"Criterio 1\", \"Criterio 2\"]
))
```

### Criterios de Evaluación

Modifica `EVALUATION_CONFIG` en `config.py`:

```python
EVALUATION_CONFIG = EvaluationCriteria(
    accuracy_weight=0.3,      # Peso de precisión
    helpfulness_weight=0.2,   # Peso de utilidad
    tool_usage_weight=0.2,    # Peso de uso de herramientas
    conversation_flow_weight=0.15,  # Peso de fluidez
    politeness_weight=0.15,   # Peso de cortesía
    minimum_passing_score=0.75  # Puntuación mínima para aprobar
)
```

## 📈 Interpretación de Resultados

### Puntuaciones de Éxito

- **0.90-1.00**: Excelente - El agente maneja la conversación perfectamente
- **0.75-0.89**: Bueno - Conversación exitosa con mejoras menores
- **0.60-0.74**: Aceptable - Funcional pero necesita mejoras
- **0.00-0.59**: Necesita Mejora - Problemas significativos identificados

### Indicadores Clave

- **Pass Rate**: % de conversaciones que superan el umbral mínimo
- **Tool Coverage**: % de herramientas esperadas que se usaron correctamente
- **Average Response Time**: Tiempo promedio de respuesta del agente
- **Error Rate**: % de conversaciones que fallaron por errores técnicos

### Recomendaciones Típicas

1. **Improve tool utilization** - Usar más herramientas relevantes
2. **Enhance response accuracy** - Mejorar la precisión de la información
3. **Better conversation flow** - Mantener mejor contexto conversacional
4. **Optimize response time** - Reducir tiempos de respuesta
5. **Professional tone consistency** - Mantener tono profesional

## 🔍 Debugging y Solución de Problemas

### Logs Detallados

```bash
# Ejecutar con salida verbose
python -m tests.ai_evaluation.main --run-all --verbose
```

### Problemas Comunes

1. **OpenAI API Key**: Asegúrate de tener configurada la variable de entorno
2. **PMS Integration**: Algunas herramientas pueden fallar si no hay integración PMS
3. **Rate Limiting**: El sistema incluye delays automáticos para evitar límites de API
4. **Memory Usage**: Las evaluaciones completas pueden usar bastante memoria

### Configuración de API

```bash
# Usar API key específica
python -m tests.ai_evaluation.main --run-all --openai-api-key \"tu_key\"

# Variables de entorno adicionales
export OPENAI_ORG_ID=\"org_id_opcional\"
```

## 🤝 Contribución

### Añadir Nuevos Tipos de Evaluación

1. Extiende `EvaluationCriteria` para nuevas métricas
2. Modifica `AIEvaluator._evaluate_single_response` para nuevos criterios
3. Actualiza prompts de evaluación en `evaluator.py`

### Mejorar Análisis Secundario

1. Extiende `PatternAnalysis` para nuevos patrones
2. Añade métodos de análisis en `AdvancedSecondaryEvaluator`
3. Actualiza prompts de análisis para nuevos insights

## 📚 Arquitectura del Sistema

```
tests/ai_evaluation/
├── __init__.py
├── config.py           # Configuración de hoteles y escenarios
├── simulator.py        # Simulador de conversaciones
├── evaluator.py        # Evaluador AI principal
├── secondary_evaluator.py  # Evaluador AI secundario
├── tool_tests.py       # Pruebas de herramientas
├── logger.py           # Sistema de logging
├── main.py            # Script principal
└── README.md          # Esta documentación
```

### Flujo de Ejecución

1. **Setup**: Configuración de hoteles y agentes de prueba
2. **Tool Testing**: Verificación de funcionamiento de herramientas
3. **Conversation Simulation**: Simulación de conversaciones reales
4. **AI Evaluation**: Evaluación de calidad con GPT-4
5. **Secondary Analysis**: Análisis de patrones y meta-evaluación
6. **Reporting**: Generación de reportes y exportación de datos

## 🎯 Casos de Uso

### Desarrollo

- Validar nuevas funcionalidades antes del deploy
- Identificar regresiones en el comportamiento del agente
- Optimizar prompts y lógica de herramientas

### QA y Testing

- Pruebas automatizadas de regresión
- Validación de calidad en diferentes hoteles
- Benchmarking de rendimiento

### Análisis de Producto

- Identificar patrones de uso de herramientas
- Optimizar flujos de conversación más comunes
- Análisis de satisfacción de usuarios simulados

### Investigación y Mejora

- Experimentos A/B con diferentes configuraciones
- Análisis de efectividad de diferentes estrategias
- Identificación de oportunidades de mejora

---

**Nota**: Este sistema está diseñado para ser extensible y configurable. Puedes adaptarlo fácilmente a tus necesidades específicas modificando los archivos de configuración y añadiendo nuevos tipos de evaluación.
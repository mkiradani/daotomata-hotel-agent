#!/usr/bin/env python3
"""
Test simple del MCP de Directus
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import Agent
from agents.mcp import MCPServerStdio

# Cargar variables de entorno
load_dotenv()

async def test_directus_mcp():
    """Test simple de conectividad MCP con Directus."""
    print("🧪 Testing Directus MCP Connection...")
    
    try:
        # Crear servidor MCP exactamente como en la configuración de Claude
        directus_server = MCPServerStdio(
            params={
                "command": "npx",
                "args": ["@directus/content-mcp@latest"],
                "env": {
                    "DIRECTUS_URL": "https://hotels.daotomata.io",
                    "DIRECTUS_TOKEN": "rYncRSsu41KQQLvZYczPJyC8-8yzyED3"
                }
            }
        )
        
        print("✅ MCP Server configurado")
        
        # Conectar el servidor MCP
        await directus_server.connect()
        print("✅ MCP Server conectado")
        
        # Verificar qué tools están disponibles
        tools = await directus_server.list_tools()
        print(f"🔧 Tools disponibles: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        if not tools:
            print("❌ No se encontraron tools")
            return False
        
        # Crear un agente simple con el MCP server
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent with access to Directus data. Use the available tools to get hotel information.",
            mcp_servers=[directus_server],
            model="gpt-4o"
        )
        
        print("✅ Agent creado con MCP")
        
        # Test simple
        from agents import Runner
        
        result = await Runner.run(
            agent,
            [{"role": "user", "content": "What hotels are available in the system? List their names and IDs."}],
            max_turns=5
        )
        
        print("✅ Test ejecutado")
        print(f"📄 Response: {result.final_output}")
        
        # Cerrar conexión MCP
        await directus_server.close()
        print("✅ MCP Server desconectado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_directus_mcp())
    if success:
        print("\n🎉 MCP test completado exitosamente!")
    else:
        print("\n💥 MCP test falló")
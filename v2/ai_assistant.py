"""
ai_assistant.py - Asistente de IA conversacional para Kali Linux
"""

import json
from typing import Dict, Optional
from pathlib import Path
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, AI_MAX_CONTEXT, AI_TEMPERATURE, AI_MAX_TOKENS
from tool_discovery import get_tool_discovery


class AIAssistant:
    """Asistente de IA que puede conversar y ejecutar herramientas"""
    
    def __init__(self):
        self.client = None
        if OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        self.user_contexts = {}  # Contexto por usuario
        self.tool_discovery = get_tool_discovery()
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Carga el prompt del sistema"""
        prompt_file = Path(__file__).parent / "prompts" / "ai_assistant.txt"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        else:
            # Prompt por defecto si no existe el archivo
            prompt = "Eres un asistente de pentesting profesional y amigable."
        
        # Insertar herramientas instaladas
        tools_info = self._get_installed_tools_summary()
        prompt = prompt.replace("{INSTALLED_TOOLS}", tools_info)
        
        return prompt
    
    def _get_installed_tools_summary(self) -> str:
        """Genera resumen de herramientas instaladas"""
        summary = "HERRAMIENTAS INSTALADAS EN ESTE SISTEMA:\\n\\n"
        
        # Agrupar por categoría
        categories = self.tool_discovery.get_all_categories()
        
        for category in sorted(categories):
            tools = self.tool_discovery.get_tools_by_category(category)
            if tools:
                cat_name = category.replace("_", " ").title()
                summary += f"{cat_name}:\\n"
                for tool in sorted(tools):
                    info = self.tool_discovery.get_tool_info(tool)
                    summary += f"  - {tool}: {info.get('description', 'N/A')}\\n"
                summary += "\\n"
        
        return summary
    
    def is_available(self) -> bool:
        """Verifica si la IA está disponible"""
        return self.client is not None
    
    async def chat(self, user_message: str, user_id: int = 0) -> Dict:
        """
        Procesa un mensaje del usuario
        
        Returns:
            Dict con uno de estos formatos:
            - {"conversation": "respuesta"}
            - {"tool": "nombre", "parameters": {...}, "explanation": "..."}
            - {"question": "...", "suggestions": [...]}
            - {"tool_not_installed": "...", "install_command": "...", ...}
            - {"error": "...", "suggestion": "..."}
        """
        if not self.is_available():
            return {
                "error": "IA no disponible",
                "suggestion": "Configura OPENAI_API_KEY en el archivo .env"
            }
        
        # Obtener contexto del usuario
        context = self.user_contexts.get(user_id, [])
        
        # Construir mensajes
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Agregar contexto previo (últimos N mensajes)
        for ctx in context[-AI_MAX_CONTEXT:]:
            messages.append(ctx)
        
        # Agregar mensaje actual
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=AI_TEMPERATURE,
               max_tokens=AI_MAX_TOKENS
            )
            
            # Extraer respuesta
            ai_response = response.choices[0].message.content.strip()
            
            # LOG DETALLADO
            print(f"\n{'='*60}")
            print(f"📨 RESPUESTA DE OPENAI:")
            print(f"{'='*60}")
            print(ai_response)
            print(f"{'='*60}\n")
            
            # Guardar en contexto
            self.user_contexts[user_id] = context + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            
            # Parsear respuesta JSON
            parsed = self._parse_ai_response(ai_response)
            
            # Si la herramienta no está instalada, verificar y ofrecer instalación
            if "tool" in parsed:
                tool_name = parsed["tool"]
                if not self.tool_discovery.check_tool_installed(tool_name):
                    install_info = self.tool_discovery.suggest_install(tool_name)
                    return {
                        "tool_not_installed": tool_name,
                        "install_command": install_info["install_command"],
                        "offer_install": True,
                        "explanation": f"{tool_name} no está instalada. ¿Quieres que la instale?"
                    }
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"\n{'='*60}")
            print(f"❌ ERROR AL PARSEAR JSON")
            print(f"{'='*60}")
            print(f"Raw response: {ai_response if 'ai_response' in locals() else 'No disponible'}")
            print(f"Error: {str(e)}")
            print(f"{'='*60}\n")
            
            return {
                "error": "Error al parsear respuesta de IA",
                "suggestion": "Intenta reformular tu pregunta. La IA está respondiendo texto en lugar de JSON."
            }
        except Exception as e:
            print(f"\n❌ ERROR GENERAL: {str(e)}")
            return {
                "error": f"Error de IA: {str(e)}",
                "suggestion": "Intenta de nuevo o usa comandos directos"
            }
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parsea la respuesta JSON de la IA"""
        original = response
        
        # Limpiar markdown si existe
        if response.strip().startswith("```json"):
            response = response.split("```json")[1].split("```")[0].strip()
            print(f"🔧 Removido markdown ```json")
        elif response.strip().startswith("```"):
            response = response.split("```")[1].split("```")[0].strip()
            print(f"🔧 Removido markdown ```")
        else:
            response = response.strip()
        
        # Parsear JSON
        try:
            parsed = json.loads(response)
            print(f"✅ JSON parseado: {list(parsed.keys())}")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido")
            print(f"Original ({len(original)} chars): {original[:100]}...")
            print(f"Limpio ({len(response)} chars): {response[:100]}...")
            raise
    
    def clear_context(self, user_id: int):
        """Limpia el contexto de un usuario"""
        if user_id in self.user_contexts:
            self.user_contexts[user_id] = []
    
    def get_context_size(self, user_id: int) -> int:
        """Obtiene el tamaño del contexto de un usuario"""
        return len(self.user_contexts.get(user_id, []))


# Singleton
_ai_assistant = None

def get_ai_assistant():
    """Obtiene la instancia global del asistente"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIAssistant()
    return _ai_assistant

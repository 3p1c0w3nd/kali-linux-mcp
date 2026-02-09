"""
telegram_bot.py - Bot de Telegram para Kali Assistant
"""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from ai_assistant import get_ai_assistant
from tool_executor import get_tool_executor
from tool_discovery import get_tool_discovery


class KaliTelegramBot:
    """Bot de Telegram para Kali Linux"""
    
    def __init__(self):
        self.ai = get_ai_assistant()
        self.executor = get_tool_executor()
        self.discovery = get_tool_discovery()
        self.app = None
        
    def check_authorization(self, user_id: int) -> bool:
        """Verifica si el usuario está autorizado"""
        if not ALLOWED_USER_IDS:
            return True
        return user_id in ALLOWED_USER_IDS
    
    # === COMANDOS ===
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /start"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text("❌ No estás autorizado para usar este bot.")
            return
        
        ai_status = "✅ Activada" if self.ai.is_available() else "❌ Desactivada"
        tools_count = len(self.discovery.discovered_tools)
        
        welcome = f"""
🔐 *KaliBot - Tu Llave para Pentesting*

¡Qué más parce! Soy Blizzacjk, tu asistente personal para Kali Linux.

*🤖 IA:* {ai_status}
*🛠 Herramientas instaladas:* {tools_count}

*Puedo:*
• Ejecutar herramientas de pentesting
• Descargar archivos y diccionarios
• Instalar programas
• Leer y mover archivos
• Clonar repositorios

*Ejemplos:*
"Descarga SecLists"
"Instala metasploit" 
"Lee /etc/hosts"
"Escanea google.com"

*Comandos:*
/tools - Ver herramientas
/categories - Ver por categorías
/status - Estado del sistema
/help - Ayuda
/clear - Limpiar contexto

⚠️ *Solo en sistemas autorizados, llave*
"""
        
        await update.message.reply_text(welcome, parse_mode='Markdown')
    
    async def tools_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra herramientas instaladas"""
        if not self.check_authorization(update.effective_user.id):
            await update.message.reply_text("❌ No autorizado")
            return
        
        tools = self.discovery.discovered_tools
        
        message = f"🛠 *Herramientas Instaladas ({len(tools)}):*\n\n"
        
        for tool_name in sorted(tools.keys())[:30]:  # Primeras 30
            info = tools[tool_name]
            message += f"• `{tool_name}` - {info.get('description', 'N/A')[:50]}...\n"
        
        if len(tools) > 30:
            message += f"\n_Y {len(tools) - 30} más..._"
        
        message += "\n\nUsa /categories para ver por categorías"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra herramientas por categorías"""
        if not self.check_authorization(update.effective_user.id):
            await update.message.reply_text("❌ No autorizado")
            return
        
        categories = self.discovery.get_all_categories()
        
        keyboard = []
        for i in range(0, len(categories), 2):
            row = []
            cat = categories[i].replace("_", " ").title()
            row.append(InlineKeyboardButton(cat, callback_data=f"cat_{categories[i]}"))
            
            if i + 1 < len(categories):
                cat2 = categories[i+1].replace("_", " ").title()
                row.append(InlineKeyboardButton(cat2, callback_data=f"cat_{categories[i+1]}"))
            
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📂 *Categorías de Herramientas:*\n\nSelecciona una categoría:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra herramientas de una categoría"""
        query = update.callback_query
        await query.answer()
        
        category = query.data.replace("cat_", "")
        tools = self.discovery.get_tools_by_category(category)
        
        cat_name = category.replace("_", " ").title()
        message = f"📂 *{cat_name}* ({len(tools)} herramientas):\n\n"
        
        for tool in sorted(tools):
            info = self.discovery.get_tool_info(tool)
            message += f"• `{tool}` - {info.get('description', 'N/A')}\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra estado del sistema"""
        if not self.check_authorization(update.effective_user.id):
            await update.message.reply_text("❌ No autorizado")
            return
        
        ai_status = "✅ Activa" if self.ai.is_available() else "❌ Inactiva"
        tools_count = len(self.discovery.discovered_tools)
        context_size = self.ai.get_context_size(update.effective_user.id)
        
        status = f"""
📊 *Estado del Sistema*

*IA:* {ai_status}
*Herramientas instaladas:* {tools_count}
*Contexto conversacional:* {context_size} mensajes

*Categorías disponibles:*
"""
        for cat in self.discovery.get_all_categories():
            count = len(self.discovery.get_tools_by_category(cat))
            cat_name = cat.replace("_", " ").title()
            status += f"  • {cat_name}: {count}\n"
        
        await update.message.reply_text(status, parse_mode='Markdown')
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Limpia el contexto de IA"""
        user_id = update.effective_user.id
        self.ai.clear_context(user_id)
        await update.message.reply_text("🧹 Contexto de IA limpiado")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra ayuda"""
        help_text = """
*🔐 KaliBot - Ayuda*

*Conversación Natural:*
Podés hablarme normalmente, parce. Ejemplos:
• "Hola, ¿cómo estás?"
• "Qué es SQL injection?"
• "Dame consejos de seguridad"
• "Explicame qué hace nmap"

*Ejecutar Herramientas:*
• "Escanea google.com"
• "Analiza las tecnologías de facebook.com"
• "Busca directorios en example.com"
• "Haz whois de amazon.com"

*Descargar e Instalar:*
• "Descarga SecLists"
• "Instala hashcat"
• "Clona https://github.com/user/repo"

*Archivos:*
• "Lee /etc/passwd"
• "Mueve archivo.txt a /tmp"

*Comandos:*
/tools - Ver herramientas instaladas
/categories - Ver por categorías
/status - Estado del sistema
/clear - Limpiar contexto de IA
/help - Esta ayuda

⚠️ *Importante:*
Solo usá estas herramientas en sistemas donde tengas autorización explícita, llave. El pentesting no autorizado es ilegal.
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    # === MANEJO DE MENSAJES ===
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto con IA"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Mostrar "escribiendo..."
        await update.message.chat.send_action("typing")
        
        # Procesar con IA
        ai_result = await self.ai.chat(user_message, user_id)
        
        # Manejar diferentes tipos de respuesta
        await self._handle_ai_response(update, ai_result)
    
    async def _handle_ai_response(self, update: Update, ai_result: dict):
        """Maneja la respuesta de la IA"""
        
        # 1. Conversación normal
        if "conversation" in ai_result:
            await update.message.reply_text(ai_result["conversation"])
            return
        
        # 2. Pregunta al usuario
        if "question" in ai_result:
            question = ai_result["question"]
            suggestions = ai_result.get("suggestions", [])
            
            message = f"❓ {question}\n\n"
            if suggestions:
                message += "*Sugerencias:*\n"
                for i, sug in enumerate(suggestions, 1):
                    message += f"{i}. {sug}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        # 3. Herramienta no instalada
        if "tool_not_installed" in ai_result:
            tool = ai_result["tool_not_installed"]
            install_cmd = ai_result["install_command"]
            explanation = ai_result.get("explanation", "")
            
            message = f"⚠️ *Herramienta no instalada*\n\n"
            message += f"{explanation}\n\n"
            message += f"Comando: `{install_cmd}`\n\n"
            message += "¿Quieres que la instale ahora?"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Sí, instalar", callback_data=f"install_{tool}"),
                    InlineKeyboardButton("❌ No", callback_data="install_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # 4. Ejecutar herramienta
        if "tool" in ai_result and "parameters" in ai_result:
            tool_name = ai_result["tool"]
            parameters = ai_result["parameters"]
            explanation = ai_result.get("explanation", "Ejecutando...")
            
            # Mostrar lo que se va a hacer
            await update.message.reply_text(
                f"🤖 *{explanation}*\n\n"
                f"🛠 Herramienta: `{tool_name}`\n"
                f"⚙️ Parámetros: ```json\n{json.dumps(parameters, indent=2)}\n```",
                parse_mode='Markdown'
            )
            
            # Ejecutar
            await update.message.reply_text(f"⏳ Ejecutando {tool_name}...")
            
            try:
                result = await self.executor.execute_tool(tool_name, parameters)
                result_data = json.loads(result)
                
                if result_data.get("success"):
                    output = result_data["stdout"]
                    
                    # Dividir si es muy largo
                    if len(output) > 4000:
                        for i in range(0, len(output), 4000):
                            await update.message.reply_text(
                                f"```\n{output[i:i+4000]}\n```",
                                parse_mode='Markdown'
                            )
                    else:
                        await update.message.reply_text(
                            f"```\n{output}\n```",
                            parse_mode='Markdown'
                        )
                else:
                    error = result_data.get("error", "Error desconocido")
                    await update.message.reply_text(f"❌ Error: {error}")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Error al ejecutar: {str(e)}")
            
            return
        
        # 5. Error
        if "error" in ai_result:
            error = ai_result["error"]
            suggestion = ai_result.get("suggestion", "")
            
            message = f"❌ {error}\n\n"
            if suggestion:
                message += f"💡 {suggestion}"
            
            await update.message.reply_text(message)
            return
        
        # Respuesta desconocida
        await update.message.reply_text(
            "🤔 No entendí esa respuesta. Intenta reformular tu pregunta."
        )
    
    async def install_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la instalación de herramientas"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "install_cancel":
            await query.edit_message_text("❌ Instalación cancelada")
            return
        
        tool_name = query.data.replace("install_", "")
        install_info = self.discovery.suggest_install(tool_name)
        
        await query.edit_message_text(f"📦 Instalando {tool_name}...")
        
        result = await self.executor.install_tool(tool_name, install_info["install_command"])
        
        if result.get("success"):
            # Reescanear herramientas
            self.discovery.scan_installed_tools()
            await query.message.reply_text(f"✅ {tool_name} instalado correctamente")
        else:
            error = result.get("error", "Error desconocido")
            await query.message.reply_text(f"❌ Error al instalar: {error}")
    
    # === SETUP ===
    
    def setup(self):
        """Configura el bot"""
        if not TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN no configurado")
            return None
        
        print("🤖 Configurando KaliBot...")
        
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Comandos
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("tools", self.tools_command))
        self.app.add_handler(CommandHandler("categories", self.categories_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("clear", self.clear_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Callbacks
        self.app.add_handler(CallbackQueryHandler(self.category_callback, pattern="^cat_"))
        self.app.add_handler(CallbackQueryHandler(self.install_callback, pattern="^install_"))
        
        # Mensajes de texto
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        print("✅ KaliBot configurado")
        return self.app
    
    async def run(self):
        """Ejecuta el bot"""
        if not self.app:
            self.setup()
        
        if self.app:
            print("🚀 Iniciando KaliBot...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            print("✅ KaliBot en ejecución")

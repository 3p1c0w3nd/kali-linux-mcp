#!/usr/bin/env python3
"""
main.py - Punto de entrada principal de KaliBot
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
from telegram_bot import KaliTelegramBot
from tool_discovery import get_tool_discovery
from ai_assistant import get_ai_assistant


def print_banner():
    """Muestra el banner de inicio"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║      🔐 KaliBot - Asistente Profesional de Pentesting  ║
║                                                       ║
║      Sistema Modular para Kali Linux                  ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)


def check_config():
    """Verifica la configuración"""
    print("🔍 Verificando configuración...")
    
    issues = []
    
    if not TELEGRAM_BOT_TOKEN:
        issues.append("❌ TELEGRAM_BOT_TOKEN no configurado")
    else:
        print("  ✅ Telegram Bot Token configurado")
    
    if not OPENAI_API_KEY:
        print("  ⚠️  OpenAI API Key no configurada (IA desactivada)")
    else:
        print("  ✅ OpenAI API Key configurada")
    
    if issues:
        print("\n⚠️  Problemas encontrados:")
        for issue in issues:
            print(f"  {issue}")
        print("\nConfigura las variables en el archivo .env")
        return False
    
    return True


async def main():
    """Función principal"""
    print_banner()
    
    # Verificar configuración
    if not check_config():
        print("\n❌ Configuración incompleta. Saliendo...")
        return
    
    print()
    
    # Inicializar componentes
    print("🔧 Inicializando componentes...")
    
    # 1. Descubrir herramientas
    print("\n1️⃣  Descubriendo herramientas instaladas...")
    discovery = get_tool_discovery()
    print(f"   ✅ {len(discovery.discovered_tools)} herramientas encontradas")
    
    # Mostrar resumen por categorías
    print("\n   📊 Resumen por categorías:")
    for category in sorted(discovery.get_all_categories()):
        tools = discovery.get_tools_by_category(category)
        cat_name = category.replace("_", " ").title()
        print(f"      • {cat_name}: {len(tools)} herramientas")
    
    # 2. Inicializar IA
    print("\n2️⃣  Inicializando IA...")
    ai = get_ai_assistant()
    if ai.is_available():
        print("   ✅ IA activada")
    else:
        print("   ⚠️  IA desactivada (sin OpenAI API Key)")
    
    # 3. Iniciar bot de Telegram
    print("\n3️⃣  Iniciando bot de Telegram...")
    bot = KaliTelegramBot()
    bot.setup()
    
    if bot.app:
        print("\n" + "="*60)
        print("✅ KaliBot está listo!")
        print("="*60)
        print("\n📱 Abre Telegram y envía /start a tu bot")
        print("\n💡 Puedes:")
        print("   • Conversar naturalmente con el bot")
        print("   • Pedirle que ejecute herramientas")
        print("   • Preguntarle sobre seguridad")
        print("   • Pedirle que instale herramientas")
        print("\n⚠️  Solo usa en sistemas autorizados")
        print("\nPresiona Ctrl+C para detener\n")
        print("="*60)
        
        # Ejecutar bot
        await bot.run()
        
        # Mantener corriendo
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n\n👋 Deteniendo KaliBot...")
            await bot.app.stop()
            print("✅ KaliBot detenido correctamente")
    else:
        print("❌ No se pudo iniciar el bot")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Saliendo...")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

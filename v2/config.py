"""
config.py - Configuración central del sistema
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Archivo .env cargado")
else:
    script_dir = Path(__file__).parent
    env_path = script_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Archivo .env cargado")

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
ALLOWED_USER_IDS = [int(uid.strip()) for uid in ALLOWED_USER_IDS if uid.strip()]

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Contraseña root para operaciones sudo (OPCIONAL, RIESGO DE SEGURIDAD)
ROOT_PASSWORD = os.getenv("ROOT_PASSWORD", "")

# Rutas de Kali Linux
KALI_BIN_PATHS = [
    "/usr/bin",
    "/usr/sbin",
    "/usr/local/bin",
    "/bin",
    "/sbin"
]

# Wordlists comunes
WORDLISTS = {
    "common": "/usr/share/wordlists/dirb/common.txt",
    "medium": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
    "big": "/usr/share/wordlists/dirbuster/directory-list-2.3-big.txt",
    "dns": "/usr/share/wordlists/dnsmap.txt",
    "rockyou": "/usr/share/wordlists/rockyou.txt"
}

# Timeouts por herramienta
TOOL_TIMEOUTS = {
    "nmap": 600,
    "nikto": 600,
    "gobuster": 600,
    "sqlmap": 600,
    "whatweb": 120,
    "hydra": 1800,
    "msfvenom": 120,
    "netcat": 30,
    "dig": 30,
    "whois": 30,
    "traceroute": 120,
    "masscan": 600,
    "enum4linux": 300,
    "searchsploit": 30,
    "wpscan": 600,
    "default": 300
}

# Configuración de IA
AI_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "ai_assistant.txt"
AI_MAX_CONTEXT = 10  # Últimos N mensajes a recordar
AI_TEMPERATURE = 0.3  # Creatividad de la IA (0-1)
AI_MAX_TOKENS = 800

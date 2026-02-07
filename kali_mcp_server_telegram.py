#!/usr/bin/env python3
"""
Servidor MCP para herramientas de Kali Linux con Bot de Telegram e IA
Permite ejecutar herramientas de pentesting usando lenguaje natural con IA
"""

import asyncio
import subprocess
import json
import os
import re
from dotenv import load_dotenv
from typing import Any, Optional, Dict, List
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, LoggingLevel

# Importar telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
    )

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print(
        "⚠️  python-telegram-bot no está instalado. Instala con: pip install python-telegram-bot"
    )

# Importar OpenAI
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai no está instalado. Instala con: pip install openai")

load_dotenv()
# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USER_IDS = os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
ALLOWED_USER_IDS = [int(uid.strip()) for uid in ALLOWED_USER_IDS if uid.strip()]

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Modelo económico y rápido

# Cliente OpenAI
openai_client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Crear el servidor MCP
server = Server("kali-tools-mcp")

# Estado global para Telegram
telegram_app = None
active_scans = {}
user_contexts = {}  # Contexto de conversación por usuario

# Definir las herramientas disponibles
TOOLS = [
    Tool(
        name="nmap",
        description="Escaneo de puertos y servicios con Nmap. Útil para descubrir hosts activos, puertos abiertos y servicios.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP, rango CIDR o dominio a escanear (ej: 192.168.1.1, 192.168.1.0/24, example.com)",
                },
                "ports": {
                    "type": "string",
                    "description": "Puertos a escanear (ej: 80, 1-1000, -, 80,443,8080)",
                    "default": "1-1000",
                },
                "scan_type": {
                    "type": "string",
                    "description": "Tipo de escaneo a realizar",
                    "enum": [
                        "quick",
                        "basic",
                        "version",
                        "aggressive",
                        "stealth",
                        "udp",
                    ],
                    "default": "basic",
                },
                "output_format": {
                    "type": "string",
                    "description": "Formato de salida",
                    "enum": ["normal", "verbose", "xml"],
                    "default": "normal",
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="nikto",
        description="Escáner de vulnerabilidades web. Detecta configuraciones inseguras, archivos peligrosos, software obsoleto.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "URL del sitio web (ej: http://example.com, https://192.168.1.1:8443)",
                },
                "ssl": {
                    "type": "boolean",
                    "description": "Forzar uso de SSL/TLS",
                    "default": False,
                },
                "port": {
                    "type": "integer",
                    "description": "Puerto específico a escanear",
                    "default": 80,
                },
                "tuning": {
                    "type": "string",
                    "description": "Tipo de pruebas: 1=Interesante, 2=Mal configuración, 3=Info disclosure, 4=Injection, etc.",
                    "default": "1234",
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="gobuster",
        description="Fuzzing de directorios, archivos, subdominios y vhosts. Muy rápido y eficiente.",
        inputSchema={
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Modo de operación",
                    "enum": ["dir", "dns", "vhost"],
                    "default": "dir",
                },
                "target": {
                    "type": "string",
                    "description": "URL (para dir/vhost) o dominio (para dns)",
                },
                "wordlist": {
                    "type": "string",
                    "description": "Wordlist: common, medium, big o ruta personalizada",
                    "default": "common",
                },
                "extensions": {
                    "type": "string",
                    "description": "Extensiones de archivo a buscar (ej: php,html,txt)",
                    "default": "php,html,txt",
                },
                "threads": {
                    "type": "integer",
                    "description": "Número de hilos concurrentes",
                    "default": 10,
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="sqlmap",
        description="Detección y explotación automática de SQL injection. Incluye extracción de bases de datos.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL vulnerable con parámetros (ej: http://site.com/page?id=1)",
                },
                "data": {
                    "type": "string",
                    "description": "Datos POST (ej: username=admin&password=pass)",
                    "default": None,
                },
                "cookie": {
                    "type": "string",
                    "description": "Cookie de sesión si es necesaria",
                    "default": None,
                },
                "level": {
                    "type": "integer",
                    "description": "Nivel de pruebas (1-5, mayor=más exhaustivo)",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 5,
                },
                "risk": {
                    "type": "integer",
                    "description": "Nivel de riesgo (1-3, mayor=más agresivo)",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 3,
                },
                "technique": {
                    "type": "string",
                    "description": "Técnicas: B=Boolean, E=Error, U=Union, S=Stacked, T=Time",
                    "default": "BEUST",
                },
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="whatweb",
        description="Identificación de tecnologías web: CMS, frameworks, servidores, versiones, plugins.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "URL del sitio (ej: https://example.com)",
                },
                "aggression": {
                    "type": "integer",
                    "description": "Nivel de agresividad (1=pasivo, 3=agresivo, 4=heavy)",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 4,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Salida detallada",
                    "default": True,
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="hydra",
        description="Ataque de fuerza bruta a servicios de autenticación (SSH, FTP, HTTP, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP o hostname del objetivo",
                },
                "service": {
                    "type": "string",
                    "description": "Servicio a atacar",
                    "enum": [
                        "ssh",
                        "ftp",
                        "http-get",
                        "http-post-form",
                        "mysql",
                        "postgres",
                        "rdp",
                        "smb",
                    ],
                },
                "username": {
                    "type": "string",
                    "description": "Usuario específico o ruta a lista de usuarios",
                },
                "password_list": {
                    "type": "string",
                    "description": "Ruta al wordlist de contraseñas",
                    "default": "/usr/share/wordlists/rockyou.txt",
                },
                "threads": {
                    "type": "integer",
                    "description": "Número de tareas paralelas",
                    "default": 4,
                },
                "port": {
                    "type": "integer",
                    "description": "Puerto personalizado (opcional)",
                },
            },
            "required": ["target", "service", "username"],
        },
    ),
    Tool(
        name="netcat",
        description="Conexión a puertos TCP/UDP, banner grabbing, transferencia de archivos.",
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Host a conectar"},
                "port": {"type": "integer", "description": "Puerto"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout en segundos",
                    "default": 5,
                },
                "udp": {
                    "type": "boolean",
                    "description": "Usar UDP en lugar de TCP",
                    "default": False,
                },
                "send_data": {
                    "type": "string",
                    "description": "Datos a enviar (opcional)",
                },
            },
            "required": ["host", "port"],
        },
    ),
    Tool(
        name="dig",
        description="Consultas DNS avanzadas: registros A, MX, NS, TXT, etc.",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Dominio a consultar"},
                "record_type": {
                    "type": "string",
                    "description": "Tipo de registro DNS",
                    "enum": ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "ANY"],
                    "default": "A",
                },
                "dns_server": {
                    "type": "string",
                    "description": "Servidor DNS a usar (opcional, ej: 8.8.8.8)",
                },
            },
            "required": ["domain"],
        },
    ),
    Tool(
        name="whois",
        description="Información de registro de dominios e IPs: propietario, fechas, servidores.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Dominio o IP a consultar"}
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="traceroute",
        description="Traza la ruta de paquetes hasta un destino, mostrando saltos intermedios.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "IP o dominio destino"},
                "max_hops": {
                    "type": "integer",
                    "description": "Máximo número de saltos",
                    "default": 30,
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="masscan",
        description="Escáner de puertos ultra-rápido. Puede escanear internet completo en minutos.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP, rango o red (ej: 192.168.1.0/24)",
                },
                "ports": {
                    "type": "string",
                    "description": "Puertos a escanear (ej: 80,443,8080 o 1-10000)",
                    "default": "1-1000",
                },
                "rate": {
                    "type": "integer",
                    "description": "Paquetes por segundo (cuidado con valores altos)",
                    "default": 100,
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="enum4linux",
        description="Enumeración de información de sistemas Windows/Samba vía SMB.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP del sistema Windows/Samba",
                },
                "scan_type": {
                    "type": "string",
                    "description": "Tipo de escaneo",
                    "enum": ["all", "users", "shares", "groups", "password_policy"],
                    "default": "all",
                },
            },
            "required": ["target"],
        },
    ),
    Tool(
        name="searchsploit",
        description="Búsqueda en la base de datos de exploits de Exploit-DB.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término de búsqueda (software, CVE, etc.)",
                },
                "exact": {
                    "type": "boolean",
                    "description": "Búsqueda exacta",
                    "default": False,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="wpscan",
        description="Escáner de vulnerabilidades específico para WordPress.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL del sitio WordPress"},
                "enumerate": {
                    "type": "string",
                    "description": "Qué enumerar: p=plugins, t=themes, u=users, vp=vulnerable plugins",
                    "default": "vp,vt,u",
                },
                "api_token": {
                    "type": "string",
                    "description": "Token de WPScan API (opcional, para más info)",
                },
            },
            "required": ["url"],
        },
    ),
]

# Wordlists comunes
WORDLISTS = {
    "common": "/usr/share/wordlists/dirb/common.txt",
    "medium": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
    "big": "/usr/share/wordlists/dirbuster/directory-list-2.3-big.txt",
    "dns": "/usr/share/wordlists/dnsmap.txt",
    "rockyou": "/usr/share/wordlists/rockyou.txt",
}


async def run_command(command: str, timeout: int = 300) -> dict:
    """Ejecuta un comando del sistema y devuelve el resultado"""
    try:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            return {
                "success": True,
                "command": command,
                "stdout": stdout.decode("utf-8", errors="ignore"),
                "stderr": stderr.decode("utf-8", errors="ignore"),
                "returncode": process.returncode,
            }
        except asyncio.TimeoutError:
            process.kill()
            return {
                "success": False,
                "command": command,
                "error": f"Comando excedió el timeout de {timeout} segundos",
            }

    except Exception as e:
        return {"success": False, "command": command, "error": str(e)}


# Funciones para cada herramienta
async def tool_nmap(args: dict) -> str:
    """Ejecuta nmap"""
    target = args["target"]
    ports = args.get("ports", "1-1000")
    scan_type = args.get("scan_type", "basic")
    output_format = args.get("output_format", "normal")

    scan_options = {
        "quick": f"-F",
        "basic": f"-p {ports}",
        "version": f"-sV -p {ports}",
        "aggressive": f"-A -p {ports}",
        "stealth": f"-sS -p {ports}",
        "udp": f"-sU -p {ports}",
    }

    verbose_flag = "-v" if output_format == "verbose" else ""
    xml_flag = "-oX -" if output_format == "xml" else ""

    command = f"nmap {scan_options[scan_type]} {verbose_flag} {xml_flag} {target}"
    result = await run_command(command, timeout=600)

    return json.dumps(result, indent=2)


async def tool_nikto(args: dict) -> str:
    """Ejecuta nikto"""
    target = args["target"]
    ssl = "-ssl" if args.get("ssl", False) else ""
    port = args.get("port", 80)
    tuning = args.get("tuning", "1234")

    command = f"nikto -h {target} -p {port} {ssl} -Tuning {tuning}"
    result = await run_command(command, timeout=600)

    return json.dumps(result, indent=2)


async def tool_gobuster(args: dict) -> str:
    """Ejecuta gobuster"""
    mode = args.get("mode", "dir")
    target = args["target"]
    wordlist = args.get("wordlist", "common")
    threads = args.get("threads", 10)

    wl_path = WORDLISTS.get(wordlist, wordlist)

    if mode == "dir":
        extensions = args.get("extensions", "php,html,txt")
        command = f"gobuster dir -u {target} -w {wl_path} -x {extensions} -t {threads}"
    elif mode == "dns":
        command = f"gobuster dns -d {target} -w {wl_path} -t {threads}"
    elif mode == "vhost":
        command = f"gobuster vhost -u {target} -w {wl_path} -t {threads}"

    result = await run_command(command, timeout=600)
    return json.dumps(result, indent=2)


async def tool_sqlmap(args: dict) -> str:
    """Ejecuta sqlmap"""
    url = args["url"]
    level = args.get("level", 1)
    risk = args.get("risk", 1)
    technique = args.get("technique", "BEUST")
    data = args.get("data")
    cookie = args.get("cookie")

    command = f"sqlmap -u '{url}' --batch --level={level} --risk={risk} --technique={technique}"

    if data:
        command += f" --data='{data}'"
    if cookie:
        command += f" --cookie='{cookie}'"

    result = await run_command(command, timeout=600)
    return json.dumps(result, indent=2)


async def tool_whatweb(args: dict) -> str:
    """Ejecuta whatweb"""
    target = args["target"]
    aggression = args.get("aggression", 1)
    verbose = "-v" if args.get("verbose", True) else ""

    command = f"whatweb -a {aggression} {verbose} {target}"
    result = await run_command(command, timeout=120)

    return json.dumps(result, indent=2)


async def tool_hydra(args: dict) -> str:
    """Ejecuta hydra"""
    target = args["target"]
    service = args["service"]
    username = args["username"]
    password_list = args.get("password_list", WORDLISTS["rockyou"])
    threads = args.get("threads", 4)
    port = args.get("port")

    port_flag = f"-s {port}" if port else ""

    command = f"hydra -l {username} -P {password_list} -t {threads} {port_flag} {target} {service}"
    result = await run_command(command, timeout=1800)

    return json.dumps(result, indent=2)


async def tool_netcat(args: dict) -> str:
    """Ejecuta netcat"""
    host = args["host"]
    port = args["port"]
    timeout = args.get("timeout", 5)
    udp = "-u" if args.get("udp", False) else ""
    send_data = args.get("send_data")

    if send_data:
        command = f"echo '{send_data}' | nc -w {timeout} {udp} {host} {port}"
    else:
        command = f"nc -w {timeout} -vz {udp} {host} {port}"

    result = await run_command(command, timeout=timeout + 5)
    return json.dumps(result, indent=2)


async def tool_dig(args: dict) -> str:
    """Ejecuta dig"""
    domain = args["domain"]
    record_type = args.get("record_type", "A")
    dns_server = args.get("dns_server", "")

    command = f"dig {domain} {record_type} {dns_server if dns_server else ''}"
    result = await run_command(command, timeout=30)

    return json.dumps(result, indent=2)


async def tool_whois(args: dict) -> str:
    """Ejecuta whois"""
    target = args["target"]

    command = f"whois {target}"
    result = await run_command(command, timeout=30)

    return json.dumps(result, indent=2)


async def tool_traceroute(args: dict) -> str:
    """Ejecuta traceroute"""
    target = args["target"]
    max_hops = args.get("max_hops", 30)

    command = f"traceroute -m {max_hops} {target}"
    result = await run_command(command, timeout=120)

    return json.dumps(result, indent=2)


async def tool_masscan(args: dict) -> str:
    """Ejecuta masscan"""
    target = args["target"]
    ports = args.get("ports", "1-1000")
    rate = args.get("rate", 100)

    command = f"sudo masscan {target} -p{ports} --rate={rate}"
    result = await run_command(command, timeout=600)

    return json.dumps(result, indent=2)


async def tool_enum4linux(args: dict) -> str:
    """Ejecuta enum4linux"""
    target = args["target"]
    scan_type = args.get("scan_type", "all")

    flags = {
        "all": "-a",
        "users": "-U",
        "shares": "-S",
        "groups": "-G",
        "password_policy": "-P",
    }

    command = f"enum4linux {flags[scan_type]} {target}"
    result = await run_command(command, timeout=300)

    return json.dumps(result, indent=2)


async def tool_searchsploit(args: dict) -> str:
    """Ejecuta searchsploit"""
    query = args["query"]
    exact = "--exact" if args.get("exact", False) else ""

    command = f"searchsploit {exact} {query}"
    result = await run_command(command, timeout=30)

    return json.dumps(result, indent=2)


async def tool_wpscan(args: dict) -> str:
    """Ejecuta wpscan"""
    url = args["url"]
    enumerate = args.get("enumerate", "vp,vt,u")
    api_token = args.get("api_token")

    command = f"wpscan --url {url} --enumerate {enumerate}"
    if api_token:
        command += f" --api-token {api_token}"

    result = await run_command(command, timeout=600)
    return json.dumps(result, indent=2)


# Mapeo de herramientas a funciones
TOOL_HANDLERS = {
    "nmap": tool_nmap,
    "nikto": tool_nikto,
    "gobuster": tool_gobuster,
    "sqlmap": tool_sqlmap,
    "whatweb": tool_whatweb,
    "hydra": tool_hydra,
    "netcat": tool_netcat,
    "dig": tool_dig,
    "whois": tool_whois,
    "traceroute": tool_traceroute,
    "masscan": tool_masscan,
    "enum4linux": tool_enum4linux,
    "searchsploit": tool_searchsploit,
    "wpscan": tool_wpscan,
}

# ========== FUNCIONES DE IA ==========


def get_tools_documentation() -> str:
    """Genera documentación de herramientas para la IA"""
    docs = "HERRAMIENTAS DISPONIBLES:\n\n"

    for tool in TOOLS:
        docs += f"## {tool.name.upper()}\n"
        docs += f"Descripción: {tool.description}\n"
        docs += "Parámetros:\n"

        properties = tool.inputSchema.get("properties", {})
        required = tool.inputSchema.get("required", [])

        for param, details in properties.items():
            req = " (REQUERIDO)" if param in required else " (opcional)"
            docs += f"  - {param}{req}: {details.get('description', 'N/A')}\n"

            if "enum" in details:
                docs += f"    Valores permitidos: {', '.join(details['enum'])}\n"
            if "default" in details:
                docs += f"    Default: {details['default']}\n"

        docs += "\n"

    return docs


async def ai_parse_command(user_message: str, user_id: int = 0) -> Dict:
    """
    Usa IA para interpretar el mensaje del usuario y generar el comando apropiado
    """
    if not openai_client:
        return {
            "error": "IA no disponible. Configura OPENAI_API_KEY",
            "suggestion": "Usa comandos directos como: /nmap 192.168.1.1",
        }

    # Obtener contexto del usuario si existe
    context = user_contexts.get(user_id, [])

    # Crear el prompt para la IA
    system_prompt = f"""Eres un chat normal. Saludas, respondes, chateas como cualquiera.

Por defecto: responde SIEMPRE con {{"conversation": "tu respuesta"}} para cualquier mensaje que sea saludo, pregunta, chateo, etc.

Solo cuando el usuario pida EXPLÍCITAMENTE ejecutar una herramienta (escaneo, nmap, nikto, gobuster, etc.) usa {{"tool": "nombre", "parameters": {{...}}, "explanation": "breve"}}.

{get_tools_documentation()}

Ejemplos:
- "hola" → {{"conversation": "¡Hola! ¿En qué te ayudo?"}}
- "qué tal" → {{"conversation": "Bien, ¿y tú? ¿Necesitas algo?"}}
- "escanea google.com" → {{"tool": "nmap", "parameters": {{"target": "google.com", "ports": "1-1000", "scan_type": "basic"}}, "explanation": "Escaneo nmap"}}
"""

    try:
        # Construir mensajes con contexto
        messages = [{"role": "system", "content": system_prompt}]

        # Agregar contexto previo (últimos 5 mensajes)
        for ctx in context[-5:]:
            messages.append(ctx)

        # Agregar mensaje actual
        messages.append({"role": "user", "content": user_message})

        # Llamar a la API de OpenAI
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,  # Baja temperatura para respuestas más consistentes
            max_tokens=500,
        )

        # Extraer la respuesta
        ai_response = response.choices[0].message.content.strip()

        # Guardar en contexto
        user_contexts[user_id] = context + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response},
        ]

        # Parsear JSON
        # Limpiar markdown si existe
        if ai_response.startswith("```json"):
            ai_response = ai_response.split("```json")[1].split("```")[0].strip()
        elif ai_response.startswith("```"):
            ai_response = ai_response.split("```")[1].split("```")[0].strip()

        parsed = json.loads(ai_response)
        return parsed

    except json.JSONDecodeError as e:
        return {
            "error": f"Error al parsear respuesta de IA: {str(e)}",
            "raw_response": ai_response if "ai_response" in locals() else "No response",
        }
    except Exception as e:
        return {
            "error": f"Error al comunicarse con IA: {str(e)}",
            "suggestion": "Intenta reformular tu solicitud o usa comandos directos",
        }


# ========== TELEGRAM BOT HANDLERS ==========


def check_authorization(user_id: int) -> bool:
    """Verifica si el usuario está autorizado"""
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start"""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("❌ No estás autorizado para usar este bot.")
        return

    ai_status = (
        "✅ Activada" if openai_client else "❌ Desactivada (configura OPENAI_API_KEY)"
    )

    welcome_message = f"""
🔐 *Kali Tools MCP Bot con IA*

Bienvenido al controlador remoto de herramientas de pentesting con asistente de IA.

*🤖 IA: {ai_status}*

*Modo IA (Natural):*
Simplemente escribe lo que quieres hacer:
• "escanea google.com"
• "qué tecnologías usa example.com"
• "busca subdominios de site.com"
• "prueba SQL injection en http://site.com/page?id=1"

*Comandos directos:*
• /nmap <target>
• /whatweb <url>
• /whois <domain>
• /dig <domain>

*Otros comandos:*
• /tools - Ver herramientas
• /status - Escaneos activos
• /help - Ayuda completa
• /clear - Limpiar contexto IA

⚠️ *Advertencia:* Solo en sistemas autorizados.
"""

    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def clear_context_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Limpia el contexto de conversación con la IA"""
    user_id = update.effective_user.id
    if user_id in user_contexts:
        user_contexts[user_id] = []
    await update.message.reply_text("🧹 Contexto de IA limpiado")


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todas las herramientas disponibles"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    keyboard = []
    for i in range(0, len(TOOLS), 2):
        row = []
        row.append(
            InlineKeyboardButton(TOOLS[i].name, callback_data=f"tool_{TOOLS[i].name}")
        )
        if i + 1 < len(TOOLS):
            row.append(
                InlineKeyboardButton(
                    TOOLS[i + 1].name, callback_data=f"tool_{TOOLS[i+1].name}"
                )
            )
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛠 *Herramientas disponibles:*\n\nSelecciona una herramienta:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def tool_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información sobre una herramienta"""
    query = update.callback_query
    await query.answer()

    tool_name = query.data.replace("tool_", "")
    tool = next((t for t in TOOLS if t.name == tool_name), None)

    if not tool:
        await query.edit_message_text("❌ Herramienta no encontrada")
        return

    info = f"*{tool.name.upper()}*\n\n"
    info += f"{tool.description}\n\n"
    info += "*Parámetros requeridos:*\n"

    required = tool.inputSchema.get("required", [])
    properties = tool.inputSchema.get("properties", {})

    for param in required:
        param_info = properties.get(param, {})
        info += f"• `{param}`: {param_info.get('description', 'N/A')}\n"

    info += f"\n*Uso con IA:*\n"
    info += f"Ejemplo: 'usa {tool_name} para escanear example.com'\n"
    info += f"\n*Uso directo:*\n`/{tool_name} <parámetros>`"

    await query.edit_message_text(info, parse_mode="Markdown")


async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto usando IA"""
    if not check_authorization(update.effective_user.id):
        return

    user_message = update.message.text
    user_id = update.effective_user.id

    # Enviar indicador de "escribiendo..."
    await update.message.chat.send_action("typing")

    # Parsear con IA
    ai_result = await ai_parse_command(user_message, user_id)

    # Manejar diferentes tipos de respuesta
    if "error" in ai_result:
        error_msg = f"❌ *Error:* {ai_result['error']}\n\n"
        if "suggestion" in ai_result:
            error_msg += f"💡 *Sugerencia:* {ai_result['suggestion']}"
        await update.message.reply_text(error_msg, parse_mode="Markdown")
        return

    if "conversation" in ai_result:
        await update.message.reply_text(ai_result["conversation"])
        return

    if "question" in ai_result:
        question_msg = f"❓ {ai_result['question']}\n\n"
        if "suggestions" in ai_result:
            question_msg += "*Opciones:*\n"
            for i, sug in enumerate(ai_result["suggestions"], 1):
                question_msg += f"{i}. {sug}\n"
        await update.message.reply_text(question_msg, parse_mode="Markdown")
        return

    if "tool" in ai_result and "parameters" in ai_result:
        tool_name = ai_result["tool"]
        parameters = ai_result["parameters"]
        explanation = ai_result.get("explanation", "Ejecutando comando...")

        # Mostrar comando (breve)
        await update.message.reply_text(
            f"🛠 *{tool_name}* → {explanation}",
            parse_mode="Markdown",
        )

        # Ejecutar el comando
        await update.message.reply_text(f"⏳ Ejecutando {tool_name}...")

        try:
            if tool_name not in TOOL_HANDLERS:
                await update.message.reply_text(
                    f"❌ Herramienta '{tool_name}' no encontrada"
                )
                return

            handler = TOOL_HANDLERS[tool_name]
            result = await handler(parameters)
            result_data = json.loads(result)

            if result_data.get("success"):
                output = result_data["stdout"]
                if len(output) > 4000:
                    for i in range(0, len(output), 4000):
                        await update.message.reply_text(
                            f"```\n{output[i:i+4000]}\n```", parse_mode="Markdown"
                        )
                else:
                    await update.message.reply_text(
                        f"```\n{output}\n```", parse_mode="Markdown"
                    )
            else:
                await update.message.reply_text(
                    f"❌ Error: {result_data.get('error', 'Desconocido')}"
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Error al ejecutar: {str(e)}")
    else:
        await update.message.reply_text(
            "❌ No pude interpretar tu solicitud. Intenta ser más específico o usa /help"
        )


async def nmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta nmap rápido"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: `/nmap <target> [ports] [scan_type]`\n"
            "Ejemplo: `/nmap 192.168.1.1 80,443 quick`",
            parse_mode="Markdown",
        )
        return

    target = context.args[0]
    ports = context.args[1] if len(context.args) > 1 else "1-1000"
    scan_type = context.args[2] if len(context.args) > 2 else "basic"

    await update.message.reply_text(f"🔍 Iniciando escaneo Nmap de {target}...")

    args = {"target": target, "ports": ports, "scan_type": scan_type}

    result = await tool_nmap(args)
    result_data = json.loads(result)

    if result_data.get("success"):
        output = result_data["stdout"]
        if len(output) > 4000:
            for i in range(0, len(output), 4000):
                await update.message.reply_text(
                    f"```\n{output[i:i+4000]}\n```", parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                f"```\n{output}\n```", parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            f"❌ Error: {result_data.get('error', 'Desconocido')}"
        )


async def whatweb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta whatweb"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: `/whatweb <url>`\nEjemplo: `/whatweb https://example.com`",
            parse_mode="Markdown",
        )
        return

    target = context.args[0]
    await update.message.reply_text(f"🔍 Analizando {target}...")

    result = await tool_whatweb({"target": target})
    result_data = json.loads(result)

    if result_data.get("success"):
        output = result_data["stdout"]
        await update.message.reply_text(
            f"```\n{output[:4000]}\n```", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Error: {result_data.get('error')}")


async def whois_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta whois"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    if not context.args:
        await update.message.reply_text("Uso: `/whois <domain>`")
        return

    target = context.args[0]
    await update.message.reply_text(f"🔍 Consultando WHOIS para {target}...")

    result = await tool_whois({"target": target})
    result_data = json.loads(result)

    if result_data.get("success"):
        output = result_data["stdout"]
        await update.message.reply_text(
            f"```\n{output[:4000]}\n```", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Error: {result_data.get('error')}")


async def dig_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta dig"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    if not context.args:
        await update.message.reply_text("Uso: `/dig <domain> [record_type]`")
        return

    domain = context.args[0]
    record_type = context.args[1] if len(context.args) > 1 else "A"

    await update.message.reply_text(
        f"🔍 Consultando DNS {record_type} para {domain}..."
    )

    result = await tool_dig({"domain": domain, "record_type": record_type})
    result_data = json.loads(result)

    if result_data.get("success"):
        output = result_data["stdout"]
        await update.message.reply_text(
            f"```\n{output[:4000]}\n```", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ Error: {result_data.get('error')}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado de escaneos activos"""
    if not check_authorization(update.effective_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    if not active_scans:
        await update.message.reply_text("ℹ️ No hay escaneos activos")
        return

    status_msg = "*Escaneos activos:*\n\n"
    for scan_id, scan_info in active_scans.items():
        status_msg += f"• {scan_info['tool']} - {scan_info['target']}\n"
        status_msg += f"  Iniciado: {scan_info['started']}\n\n"

    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ayuda detallada"""
    ai_status = "activada ✅" if openai_client else "desactivada ❌"

    help_text = f"""
*🔐 Kali Tools MCP Bot con IA - Ayuda*

*🤖 IA: {ai_status}*

*Modo IA (Lenguaje Natural):*
Simplemente escribe lo que quieres:
```
escanea 192.168.1.1
qué tecnologías usa facebook.com
busca directorios en example.com
prueba subdominios de google.com
información whois de microsoft.com
```

*Comandos básicos:*
• `/start` - Iniciar el bot
• `/tools` - Ver herramientas
• `/status` - Estado de escaneos
• `/clear` - Limpiar contexto IA
• `/help` - Esta ayuda

*Comandos directos:*
• `/nmap <target> [ports] [type]`
• `/whatweb <url>`
• `/whois <domain>`
• `/dig <domain> [type]`

*Ejemplos:*
```
/nmap 192.168.1.1
escanea los puertos 80 y 443 de google.com
qué CMS usa wordpress.com
```

⚠️ *Disclaimer:*
Solo en sistemas autorizados.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


def setup_telegram_bot():
    """Configura el bot de Telegram"""
    if not TELEGRAM_AVAILABLE:
        print("❌ Telegram bot no disponible - falta python-telegram-bot")
        return None

    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return None

    print("🤖 Configurando bot de Telegram...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_context_command))

    # Herramientas rápidas
    application.add_handler(CommandHandler("nmap", nmap_command))
    application.add_handler(CommandHandler("whatweb", whatweb_command))
    application.add_handler(CommandHandler("whois", whois_command))
    application.add_handler(CommandHandler("dig", dig_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(tool_info_callback, pattern="^tool_"))

    # Mensajes de texto (IA)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message)
    )

    print("✅ Bot de Telegram configurado")
    return application


# ========== MCP SERVER HANDLERS ==========


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Lista todas las herramientas disponibles"""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecuta una herramienta"""
    try:
        if name not in TOOL_HANDLERS:
            raise ValueError(f"Herramienta desconocida: {name}")

        handler = TOOL_HANDLERS[name]
        result = await handler(arguments)

        return [TextContent(type="text", text=result)]

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "tool": name,
            "arguments": arguments,
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def run_telegram_bot():
    """Ejecuta el bot de Telegram"""
    global telegram_app
    telegram_app = setup_telegram_bot()

    if telegram_app:
        print("🚀 Iniciando bot de Telegram...")
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("✅ Bot de Telegram en ejecución")


async def main():
    """Inicia el servidor MCP y el bot de Telegram"""
    print("🚀 Iniciando Kali Tools MCP Server con Telegram Bot e IA")
    print(f"🤖 OpenAI: {'✅ Configurado' if openai_client else '❌ No configurado'}")

    # Iniciar bot de Telegram en segundo plano
    if TELEGRAM_AVAILABLE and TELEGRAM_BOT_TOKEN:
        asyncio.create_task(run_telegram_bot())
    else:
        print("⚠️  Bot de Telegram no iniciado - configura TELEGRAM_BOT_TOKEN")

    # Iniciar servidor MCP
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kali-tools-mcp",
                server_version="3.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

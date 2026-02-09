# 🚀 Instalación Rápida de KaliBot

## 📦 Descargar e Instalar

### Opción 1: Desde el archivo comprimido

```bash
# Descargar kali_assistant.tar.gz

# Extraer
tar -xzf kali_assistant.tar.gz

# Entrar al directorio
cd kali_assistant

# Instalar dependencias
pip install --break-system-packages -r requirements.txt
```

### Opción 2: Clonar estructura manualmente

Descarga todos los archivos y organízalos así:

```
kali_assistant/
├── main.py
├── config.py
├── ai_assistant.py
├── tool_discovery.py
├── tool_executor.py
├── telegram_bot.py
├── prompts/
│   └── ai_assistant.txt
├── requirements.txt
├── .env.example
└── README.md
```

## ⚙️ Configuración

```bash
# 1. Copiar plantilla
cp .env.example .env

# 2. Editar con tus credenciales
nano .env
```

Contenido del `.env`:
```env
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
TELEGRAM_ALLOWED_USERS=tu_user_id
OPENAI_API_KEY=sk-proj-tu_api_key  # Opcional
OPENAI_MODEL=gpt-4o-mini
```

## 🎯 Obtener Credenciales

### Telegram Bot Token
1. Abre Telegram
2. Busca: `@BotFather`
3. Envía: `/newbot`
4. Sigue instrucciones
5. **Copia el token**

### Telegram User ID
1. Busca: `@userinfobot`
2. Envía: `/start`
3. **Copia tu ID**

### OpenAI API Key (Opcional)
1. Ve a: https://platform.openai.com/api-keys
2. Regístrate
3. Crea API key
4. **Cópiala**

## ▶️ Ejecutar

```bash
chmod +x main.py
python3 main.py
```

Deberías ver:

```
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║  🔐 KaliBot - Asistente Profesional de Pentesting     ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝

🔍 Verificando configuración...
  ✅ Telegram Bot Token configurado
  ✅ OpenAI API Key configurada

🔧 Inicializando componentes...

1️⃣  Descubriendo herramientas instaladas...
   ✅ 47 herramientas encontradas

   📊 Resumen por categorías:
      • DNS: 6 herramientas
      • Enumeration: 5 herramientas
      • Network Scan: 8 herramientas
      ...

2️⃣  Inicializando IA...
   ✅ IA activada

3️⃣  Iniciando bot de Telegram...

============================================================
✅ KaliBot está listo!
============================================================

📱 Abre Telegram y envía /start a tu bot
```

## 📱 Usar en Telegram

```
/start - Ver bienvenida y estado
```

Luego puedes:
- Conversar: "Hola, ¿qué puedes hacer?"
- Ejecutar: "Escanea google.com"
- Preguntar: "Qué es nmap?"
- Instalar: "Instala aircrack-ng"

## 🐛 Solución de Problemas

### Error: "TELEGRAM_BOT_TOKEN no configurado"
```bash
# Verifica que .env exista y tenga el token
cat .env
```

### Error: "No module named 'dotenv'"
```bash
pip install --break-system-packages python-dotenv
```

### Error: "No module named 'telegram'"
```bash
pip install --break-system-packages python-telegram-bot
```

### Instalar todo de una vez
```bash
pip install --break-system-packages python-dotenv python-telegram-bot openai
```

## ✅ Checklist

- [ ] Archivos extraídos en `kali_assistant/`
- [ ] Dependencias instaladas
- [ ] Archivo `.env` creado con credenciales
- [ ] `main.py` tiene permisos de ejecución
- [ ] Bot de Telegram creado
- [ ] User ID obtenido

## 🎉 ¡Listo!

Ahora tienes un asistente profesional de pentesting con:
- 🤖 IA conversacional
- 🔍 80+ herramientas detectadas automáticamente
- 📦 Instalación automática de herramientas
- 📱 Interfaz de Telegram

---

¿Necesitas ayuda? Revisa el `README.md` completo.

# 🔐 KaliBot - AI-Powered Pentesting Assistant

<p align="center">
  <img src="demo.gif" alt="KaliBotMCP Demo" width="600"/>
</p>

<p align="center">
  <strong>Conversational AI assistant for Kali Linux security tools via Telegram</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#extending">Extending</a>
</p>

---

## Overview

KaliBotMCP combines the power of Kali Linux pentesting tools with OpenAI's GPT models and the Model Context Protocol (MCP) to create an intelligent, conversational security assistant accessible through Telegram.

Instead of memorizing complex command syntax, users can interact with security tools using natural language in Colombian Spanish, making pentesting more accessible while maintaining the full capabilities of native Kali tools.

---

![alt text](ccc-1.gif)

## Features

### 🤖 Natural Language Interface
- Speak naturally to execute complex security tools
- Colombian Spanish conversational AI powered by GPT-4
- Contextual awareness maintains conversation history
- Educational explanations of security concepts

### 🛠️ Pentesting Toolset
- **Network Scanning** - nmap, masscan
- **Web Analysis** - nikto, gobuster, sqlmap, whatweb  
- **Password Cracking** - hydra, john, hashcat
- **Wireless Security** - aircrack-ng, reaver
- **Exploitation** - msfvenom, metasploit
- **Reconnaissance** - whois, dig, theHarvester

### 📦 System Operations
- Download files and clone repositories
- Install packages via apt, pip, gem, npm, cargo
- Read, move, and copy system files
- Optional sudo password integration

### 💬 Telegram Integration
- Mobile-first interface
- Interactive command buttons
- User access control
- Long output pagination

---

## Installation

### Prerequisites

- Kali Linux / Debian / Ubuntu
- Python 3.10+
- Telegram Bot Token ([obtain from @BotFather](https://t.me/botfather))
- OpenAI API Key ([obtain from platform.openai.com](https://platform.openai.com))

### Setup

Clone the repository:

```bash
git clone https://github.com/3p1c0w3nd/kali-linux-mcp.git
cd kali-linux-mcp/v2
```

Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment:

```bash
cp .env.example .env
nano .env
```

Set your credentials in `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALLOWED_USERS=your_user_id_here
OPENAI_API_KEY=sk-your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

> Get your Telegram User ID from [@userinfobot](https://t.me/userinfobot)

Run the bot:

```bash
python3 main.py
```

---

## Usage

### Natural Language Examples

```
User: hola
Bot: ¡Qué más parce! 👋 Soy Blizzacjk, your pentesting assistant...

User: scan google.com for open ports
Bot: Scanning ports 1-1000 on google.com with Nmap...
     [Executes: nmap -p 1-1000 google.com]

User: download seclists
Bot: Downloading complete SecLists repository (~1GB)...
     [Clones: https://github.com/danielmiessler/SecLists.git]

User: install hashcat
Bot: Installing hashcat via apt...
     [Executes: sudo apt install hashcat]

User: read /etc/hosts
Bot: Reading /etc/hosts...
     [Displays file contents]
```

### Direct Commands

| Command | Description |
|---------|-------------|
| `/tools` | List all installed tools |
| `/categories` | Browse tools by category |
| `/status` | System status (AI, tools) |
| `/clear` | Clear AI context |
| `/help` | Full help menu |

---

## Architecture

```
┌─────────────────┐
│   Telegram      │
│   Interface     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  telegram_bot   │  ← User validation, routing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ai_assistant   │  ← OpenAI GPT-4, NLP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ tool_executor   │  ← Command execution
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│tool_sys │ │tool_discovery│
│• DL     │ │• Detection   │
│• PKG    │ │• Cataloging  │
└─────────┘ └──────────────┘
```

### Core Modules

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point, bot initialization |
| `telegram_bot.py` | Telegram interface, message handling |
| `ai_assistant.py` | OpenAI integration, JSON parsing |
| `tool_executor.py` | Kali Linux tool execution |
| `tool_system.py` | System operations (downloads, installs) |
| `tool_discovery.py` | Automatic tool detection |
| `config.py` | Centralized configuration |

---

## Extending

### Adding a New Tool

**1. Register in `tool_discovery.py`**

Add to the `common_kali_tools` dictionary:

```python
self.common_kali_tools = {
    # ...
    "subfinder": {
        "category": "info_gathering",
        "description": "Subdomain discovery tool"
    },
}
```

Available categories: `reconnaissance`, `scanning`, `web_scan`, `exploitation`, `password`, `wireless`, `sniffing`, `forensics`, `info_gathering`

**2. Create executor in `tool_executor.py`**

```python
async def execute_subfinder(self, params: Dict) -> str:
    """Execute subfinder for subdomain discovery"""
    domain = params["domain"]
    output = params.get("output", f"{domain}_subdomains.txt")
    
    command = f"subfinder -d {domain} -o {output}"
    
    if params.get("silent"):
        command += " -silent"
    
    result = await self.run_command(command, timeout=300)
    
    if result.get("success") and os.path.exists(output):
        lines = open(output).readlines()
        result["subdomains_found"] = len(lines)
        result["output_file"] = output
    
    return self._format_result(result)
```

**3. Register executor**

In `execute_tool` method, add to `tool_methods`:

```python
tool_methods = {
    "nmap": self.execute_nmap,
    "subfinder": self.execute_subfinder,
    # ...
}
```

**4. Update AI prompts**

Add examples to `prompts/ai_assistant.txt`:

```
Usuario: "busca subdominios de example.com"
{"tool": "subfinder", "parameters": {"domain": "example.com"}, "explanation": "Buscando subdominios de example.com con subfinder"}
```

**5. Restart bot**

```bash
pkill -f main.py
python3 main.py
```

### Removing a Tool

**1. Delete from `tool_discovery.py`**

Remove the tool entry from `common_kali_tools`

**2. Remove executor (if exists)**

Delete the `execute_*` method from `tool_executor.py`

**3. Remove from mapping**

Delete from `tool_methods` dictionary

**4. Update prompts**

Remove examples from `prompts/ai_assistant.txt`

---

## Security

> **⚠️ WARNING:** This is an experimental project intended for controlled testing environments only.

### Best Practices

- Only use in authorized testing environments
- Restrict user access via `TELEGRAM_ALLOWED_USERS`
- Avoid storing `ROOT_PASSWORD` in production
- Run only on dedicated Kali Linux systems
- Always obtain written authorization before pentesting

### ROOT_PASSWORD Configuration

For development, you can set:

```env
ROOT_PASSWORD=your_password
```

**Recommended:** Configure passwordless sudo instead:

```bash
sudo visudo
# Add:
your_username ALL=(ALL) NOPASSWD: ALL
```

---

## Resources

- [Kali Linux Documentation](https://www.kali.org/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

## Contributing

Contributions are welcome! Areas of interest:

- Additional tool executors (Burp Suite CLI, advanced SQLMap, etc.)
- Input sanitization improvements
- Rate limiting implementation
- Web interface alternative
- Documentation and tutorials

**Process:**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-tool`)
3. Commit changes (`git commit -am 'Add new tool'`)
4. Push to branch (`git push origin feature/new-tool`)
5. Open Pull Request

---

## License

This project is open source and available under the MIT License.

---

## Disclaimer

This project is **for educational and research purposes only**. Using pentesting tools without explicit written authorization is **illegal** in most jurisdictions.

The authors are not responsible for misuse of this software. Always practice ethical hacking and obtain proper certifications (OSCP, CEH, etc.).

**Use KaliBotMCP only on:**
- Your own systems
- Authorized testing environments (HackTheBox, TryHackMe)
- Legally contracted security audits

---

## Acknowledgments

- [Offensive Security](https://www.offensive-security.com/) - Kali Linux
- [OpenAI](https://openai.com/) - GPT Models
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram API

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/3p1c0w3nd">3p1c0w3nd</a>
</p>

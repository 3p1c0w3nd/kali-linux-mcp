"""
tool_executor.py - Ejecuta herramientas de Kali Linux
"""

import asyncio
import subprocess
from typing import Dict, Optional
from config import TOOL_TIMEOUTS, WORDLISTS, ROOT_PASSWORD
from tool_system import get_system_manager


class ToolExecutor:
    """Ejecuta herramientas de pentesting"""
    
    def __init__(self):
        self.active_processes = {}
        self.system_manager = get_system_manager(ROOT_PASSWORD)
    
    async def run_command(self, command: str, timeout: int = 300) -> Dict:
        """Ejecuta un comando del sistema"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "success": True,
                    "command": command,
                    "stdout": stdout.decode('utf-8', errors='ignore'),
                    "stderr": stderr.decode('utf-8', errors='ignore'),
                    "returncode": process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "command": command,
                    "error": f"Comando excedió el timeout de {timeout} segundos"
                }
                
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    async def install_tool(self, tool_name: str, install_command: str) -> Dict:
        """Instala una herramienta"""
        print(f"📦 Instalando {tool_name}...")
        result = await self.run_command(install_command, timeout=600)
        
        if result.get("success"):
            return {
                "success": True,
                "tool": tool_name,
                "message": f"{tool_name} instalado correctamente"
            }
        else:
            return {
                "success": False,
                "tool": tool_name,
                "error": result.get("error", "Error desconocido")
            }
    
    # === HERRAMIENTAS ESPECÍFICAS ===
    
    async def execute_nmap(self, params: Dict) -> str:
        """Ejecuta nmap"""
        target = params["target"]
        ports = params.get("ports", "1-1000")
        scan_type = params.get("scan_type", "basic")
        output_format = params.get("output_format", "normal")
        
        scan_options = {
            "quick": "-F",
            "basic": f"-p {ports}",
            "version": f"-sV -p {ports}",
            "aggressive": f"-A -p {ports}",
            "stealth": f"-sS -p {ports}",
            "udp": f"-sU -p {ports}"
        }
        
        verbose = "-v" if output_format == "verbose" else ""
        xml = "-oX -" if output_format == "xml" else ""
        
        command = f"nmap {scan_options[scan_type]} {verbose} {xml} {target}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("nmap", 600))
        
        return self._format_result(result)
    
    async def execute_nikto(self, params: Dict) -> str:
        """Ejecuta nikto"""
        target = params["target"]
        ssl = "-ssl" if params.get("ssl", False) else ""
        port = params.get("port", 80)
        tuning = params.get("tuning", "1234")
        
        command = f"nikto -h {target} -p {port} {ssl} -Tuning {tuning}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("nikto", 600))
        
        return self._format_result(result)
    
    async def execute_gobuster(self, params: Dict) -> str:
        """Ejecuta gobuster"""
        mode = params.get("mode", "dir")
        target = params["target"]
        wordlist = params.get("wordlist", "common")
        threads = params.get("threads", 10)
        
        wl_path = WORDLISTS.get(wordlist, wordlist)
        
        if mode == "dir":
            extensions = params.get("extensions", "php,html,txt")
            command = f"gobuster dir -u {target} -w {wl_path} -x {extensions} -t {threads}"
        elif mode == "dns":
            command = f"gobuster dns -d {target} -w {wl_path} -t {threads}"
        elif mode == "vhost":
            command = f"gobuster vhost -u {target} -w {wl_path} -t {threads}"
        
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("gobuster", 600))
        return self._format_result(result)
    
    async def execute_sqlmap(self, params: Dict) -> str:
        """Ejecuta sqlmap"""
        url = params["url"]
        level = params.get("level", 1)
        risk = params.get("risk", 1)
        technique = params.get("technique", "BEUST")
        data = params.get("data")
        cookie = params.get("cookie")
        
        command = f"sqlmap -u '{url}' --batch --level={level} --risk={risk} --technique={technique}"
        
        if data:
            command += f" --data='{data}'"
        if cookie:
            command += f" --cookie='{cookie}'"
        
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("sqlmap", 600))
        return self._format_result(result)
    
    async def execute_whatweb(self, params: Dict) -> str:
        """Ejecuta whatweb"""
        target = params["target"]
        aggression = params.get("aggression", 1)
        verbose = "-v" if params.get("verbose", True) else ""
        
        command = f"whatweb -a {aggression} {verbose} {target}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("whatweb", 120))
        
        return self._format_result(result)
    
    async def execute_hydra(self, params: Dict) -> str:
        """Ejecuta hydra"""
        target = params["target"]
        service = params["service"]
        username = params["username"]
        password_list = params.get("password_list", WORDLISTS["rockyou"])
        threads = params.get("threads", 4)
        port = params.get("port")
        
        port_flag = f"-s {port}" if port else ""
        
        command = f"hydra -l {username} -P {password_list} -t {threads} {port_flag} {target} {service}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("hydra", 1800))
        
        return self._format_result(result)
    
    async def execute_dig(self, params: Dict) -> str:
        """Ejecuta dig"""
        domain = params["domain"]
        record_type = params.get("record_type", "A")
        dns_server = params.get("dns_server", "")
        
        command = f"dig {domain} {record_type} {dns_server if dns_server else ''}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("dig", 30))
        
        return self._format_result(result)
    
    async def execute_whois(self, params: Dict) -> str:
        """Ejecuta whois"""
        target = params["target"]
        
        command = f"whois {target}"
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("whois", 30))
        
        return self._format_result(result)
    
    async def execute_msfvenom(self, params: Dict) -> str:
        """Ejecuta msfvenom para generar payloads"""
        payload_type = params.get("payload", "android/meterpreter/reverse_tcp")
        lhost = params["lhost"]
        lport = params.get("lport", 4444)
        output_format = params.get("format", "raw")
        output_file = params.get("output", "payload.apk")
        
        # Construir comando base
        command = f"msfvenom -p {payload_type} LHOST={lhost} LPORT={lport}"
        
        # Agregar formato si no es raw
        if output_format != "raw":
            command += f" -f {output_format}"
        
        # Agregar archivo de salida
        command += f" -o {output_file}"
        
        # Opciones adicionales
        if "arch" in params:
            command += f" --arch {params['arch']}"
        if "platform" in params:
            command += f" --platform {params['platform']}"
        if "encoder" in params:
            command += f" -e {params['encoder']}"
        if "iterations" in params:
            command += f" -i {params['iterations']}"
        
        result = await self.run_command(command, timeout=TOOL_TIMEOUTS.get("msfvenom", 120))
        
        # Verificar si el archivo se creó
        if result.get("success") and output_file:
            import os
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                result["file_info"] = {
                    "path": os.path.abspath(output_file),
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2)
                }
        
        return self._format_result(result)
    
    async def execute_download(self, params: Dict) -> str:
        """Descarga archivo"""
        result = await self.system_manager.download_file(
            params["url"],
            params.get("output")
        )
        return self.system_manager.format_result(result)
    
    async def execute_git_clone(self, params: Dict) -> str:
        """Clona repositorio"""
        result = await self.system_manager.git_clone(
            params["repo"],
            params.get("dest")
        )
        return self.system_manager.format_result(result)
    
    async def execute_install_package(self, params: Dict) -> str:
        """Instala paquete"""
        result = await self.system_manager.install_package(
            params["package"],
            params.get("manager", "apt")
        )
        return self.system_manager.format_result(result)
    
    async def execute_read_file(self, params: Dict) -> str:
        """Lee archivo"""
        result = await self.system_manager.read_file(
            params["file"],
            params.get("lines", 50)
        )
        return self.system_manager.format_result(result)
    
    async def execute_move_file(self, params: Dict) -> str:
        """Mueve archivo"""
        result = await self.system_manager.move_file(
            params["source"],
            params["dest"],
            params.get("sudo", False)
        )
        return self.system_manager.format_result(result)
    
    async def execute_copy_file(self, params: Dict) -> str:
        """Copia archivo"""
        result = await self.system_manager.copy_file(
            params["source"],
            params["dest"],
            params.get("sudo", False)
        )
        return self.system_manager.format_result(result)
    
    async def execute_tool(self, tool_name: str, parameters: Dict) -> str:
        """Ejecuta cualquier herramienta por nombre"""
        # Mapeo de herramientas a métodos
        tool_methods = {
            "nmap": self.execute_nmap,
            "nikto": self.execute_nikto,
            "gobuster": self.execute_gobuster,
            "sqlmap": self.execute_sqlmap,
            "whatweb": self.execute_whatweb,
            "hydra": self.execute_hydra,
            "dig": self.execute_dig,
            "whois": self.execute_whois,
            "msfvenom": self.execute_msfvenom,
            "download": self.execute_download,
            "git_clone": self.execute_git_clone,
            "install_package": self.execute_install_package,
            "read_file": self.execute_read_file,
            "move_file": self.execute_move_file,
            "copy_file": self.execute_copy_file,
        }
        
        if tool_name in tool_methods:
            return await tool_methods[tool_name](parameters)
        else:
            # Herramienta genérica
            return await self._execute_generic_tool(tool_name, parameters)
    
    async def _execute_generic_tool(self, tool_name: str, parameters: Dict) -> str:
        """Ejecuta una herramienta genérica"""
        # Construir comando básico
        args = " ".join([f"{v}" for v in parameters.values()])
        command = f"{tool_name} {args}"
        
        timeout = TOOL_TIMEOUTS.get(tool_name, TOOL_TIMEOUTS["default"])
        result = await self.run_command(command, timeout=timeout)
        
        return self._format_result(result)
    
    def _format_result(self, result: Dict) -> str:
        """Formatea el resultado para enviar al usuario"""
        import json
        return json.dumps(result, indent=2)


# Singleton
_tool_executor = None

def get_tool_executor():
    """Obtiene la instancia global del ejecutor"""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor

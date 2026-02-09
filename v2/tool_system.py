"""
tool_system.py - Operaciones de sistema para el bot (descargas, instalaciones, archivos)
"""

import os
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
import json

class ToolSystemManager:
    """Maneja operaciones de sistema: archivos, descargas, instalaciones"""
    
    def __init__(self, root_password: str = ""):
        self.download_dir = Path("/tmp/kali_bot_downloads")
        self.download_dir.mkdir(exist_ok=True, parents=True)
        self.root_password = root_password
        
    async def _run_command(self, command: str, timeout: int = 300, use_sudo: bool = False) -> Dict:
        """Ejecuta comando con soporte para sudo"""
        try:
            if use_sudo and self.root_password:
                # Usar echo password | sudo -S command
                command = f'echo "{self.root_password}" | sudo -S {command}'
            elif use_sudo:
                # Sudo sin password (asume NOPASSWD configurado)
                command = f'sudo {command}'
            
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
                    "command": command.replace(self.root_password, "***") if self.root_password else command,
                    "stdout": stdout.decode('utf-8', errors='ignore'),
                    "stderr": stderr.decode('utf-8', errors='ignore'),
                    "returncode": process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "command": command.replace(self.root_password, "***") if self.root_password else command,
                    "error": f"Comando excedió el timeout de {timeout} segundos"
                }
                
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    async def download_file(self, url: str, output_path: Optional[str] = None) -> Dict:
        """Descarga archivo con wget"""
        if not output_path:
            filename = url.split('/')[-1] or "downloaded_file"
            output_path = str(self.download_dir / filename)
        
        command = f"wget -O '{output_path}' '{url}'"
        result = await self._run_command(command, timeout=600)
        
        if result.get("success") and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            result["file_info"] = {
                "path": os.path.abspath(output_path),
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
                "size_mb": round(file_size / (1024 * 1024), 2)
            }
        
        return result
    
    async def git_clone(self, repo_url: str, dest_dir: Optional[str] = None) -> Dict:
        """Clona repositorio Git"""
        if not dest_dir:
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            dest_dir = str(self.download_dir / repo_name)
        
        command = f"git clone '{repo_url}' '{dest_dir}'"
        result = await self._run_command(command, timeout=1800)  # 30 min para repos grandes
        
        if result.get("success") and os.path.exists(dest_dir):
            # Calcular tamaño del directorio
            total_size = sum(f.stat().st_size for f in Path(dest_dir).rglob('*') if f.is_file())
            result["repo_info"] = {
                "path": os.path.abspath(dest_dir),
                "size_mb": round(total_size / (1024 * 1024), 2)
            }
        
        return result
    
    async def install_package(self, package_name: str, package_manager: str = "apt") -> Dict:
        """Instala paquete (apt/pip/gem)"""
        commands = {
            "apt": f"apt-get update && apt-get install -y {package_name}",
            "pip": f"pip install {package_name}",
            "pip3": f"pip3 install {package_name}",
            "gem": f"gem install {package_name}",
            "cargo": f"cargo install {package_name}",
            "npm": f"npm install -g {package_name}"
        }
        
        if package_manager not in commands:
            return {
                "success": False,
                "error": f"Package manager '{package_manager}' no soportado. Usa: {', '.join(commands.keys())}"
            }
        
        command = commands[package_manager]
        use_sudo = package_manager in ["apt", "npm"]
        
        result = await self._run_command(command, timeout=1800, use_sudo=use_sudo)
        result["package"] = package_name
        result["package_manager"] = package_manager
        
        return result
    
    async def move_file(self, source: str, destination: str, use_sudo: bool = False) -> Dict:
        """Mueve archivo o directorio"""
        try:
            if use_sudo:
                command = f"mv '{source}' '{destination}'"
                return await self._run_command(command, timeout=60, use_sudo=True)
            else:
                shutil.move(source, destination)
                return {
                    "success": True,
                    "operation": "move",
                    "source": source,
                    "destination": destination
                }
        except Exception as e:
            return {
                "success": False,
                "operation": "move",
                "error": str(e)
            }
    
    async def copy_file(self, source: str, destination: str, use_sudo: bool = False) -> Dict:
        """Copia archivo o directorio"""
        try:
            if use_sudo:
                command = f"cp -r '{source}' '{destination}'"
                return await self._run_command(command, timeout=300, use_sudo=True)
            else:
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                else:
                    shutil.copytree(source, destination)
                return {
                    "success": True,
                    "operation": "copy",
                    "source": source,
                    "destination": destination
                }
        except Exception as e:
            return {
                "success": False,
                "operation": "copy",
                "error": str(e)
            }
    
    async def read_file(self, filepath: str, lines: int = 50) -> Dict:
        """Lee contenido de archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content_lines = f.readlines()
                
            total_lines = len(content_lines)
            display_lines = content_lines[:lines]
            
            return {
                "success": True,
                "filepath": filepath,
                "total_lines": total_lines,
                "showing_lines": len(display_lines),
                "content": ''.join(display_lines),
                "truncated": total_lines > lines
            }
        except Exception as e:
            return {
                "success": False,
                "filepath": filepath,
                "error": str(e)
            }
    
    async def install_to_bin(self, binary_path: str, bin_dir: str = "/usr/local/bin") -> Dict:
        """Copia binario a /usr/local/bin con sudo"""
        if not os.path.exists(binary_path):
            return {
                "success": False,
                "error": f"Archivo no encontrado: {binary_path}"
            }
        
        filename = os.path.basename(binary_path)
        dest_path = f"{bin_dir}/{filename}"
        
        # Copiar y dar permisos de ejecución
        command = f"cp '{binary_path}' '{dest_path}' && chmod +x '{dest_path}'"
        result = await self._run_command(command, timeout=60, use_sudo=True)
        
        if result.get("success"):
            result["installed_to"] = dest_path
        
        return result
    
    async def download_seclists(self, dest_dir: str = "/usr/share/wordlists/seclists") -> Dict:
        """Descarga SecLists completo desde GitHub"""
        repo_url = "https://github.com/danielmiessler/SecLists.git"
        
        # Verificar si ya existe
        if os.path.exists(dest_dir):
            return {
                "success": False,
                "error": f"SecLists ya existe en {dest_dir}. Usa 'git pull' para actualizar."
            }
        
        # Clonar (puede requerir sudo dependiendo del destino)
        needs_sudo = dest_dir.startswith("/usr/") or dest_dir.startswith("/opt/")
        
        if needs_sudo:
            command = f"git clone {repo_url} {dest_dir}"
            result = await self._run_command(command, timeout=1800, use_sudo=True)
        else:
            result = await self.git_clone(repo_url, dest_dir)
        
        return result
    
    def format_result(self, result: Dict) -> str:
        """Formatea resultado como JSON"""
        return json.dumps(result, indent=2, ensure_ascii=False)


# Singleton
_system_manager = None

def get_system_manager(root_password: str = ""):
    """Obtiene la instancia global del system manager"""
    global _system_manager
    if _system_manager is None:
        _system_manager = ToolSystemManager(root_password)
    return _system_manager

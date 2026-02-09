"""
tool_discovery.py - Descubrimiento automático de herramientas instaladas en Kali
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json

class ToolDiscovery:
    """Descubre y cataloga herramientas instaladas en Kali Linux"""
    
    def __init__(self):
        self.bin_paths = [
            "/usr/bin",
            "/usr/sbin", 
            "/usr/local/bin",
            "/bin",
            "/sbin"
        ]
        self.discovered_tools = {}
        self.common_kali_tools = self._load_common_tools()
        
    def _load_common_tools(self) -> Dict:
        """Carga lista de herramientas comunes de Kali"""
        return {
            # Escaneo de red
            "nmap": {"category": "network_scan", "description": "Network exploration and security auditing"},
            "masscan": {"category": "network_scan", "description": "Ultra-fast port scanner"},
            "netcat": {"category": "network_scan", "description": "TCP/UDP connections and listening"},
            "nc": {"category": "network_scan", "description": "Netcat alias"},
            "ping": {"category": "network_scan", "description": "ICMP echo requests"},
            "traceroute": {"category": "network_scan", "description": "Trace route to host"},
            "arp-scan": {"category": "network_scan", "description": "ARP network scanner"},
            "unicornscan": {"category": "network_scan", "description": "Advanced network scanner"},
            
            # Web scanning
            "nikto": {"category": "web_scan", "description": "Web server vulnerability scanner"},
            "wpscan": {"category": "web_scan", "description": "WordPress vulnerability scanner"},
            "whatweb": {"category": "web_scan", "description": "Web technology identifier"},
            "gobuster": {"category": "web_scan", "description": "Directory/file/DNS brute forcer"},
            "dirb": {"category": "web_scan", "description": "Web content scanner"},
            "wfuzz": {"category": "web_scan", "description": "Web application fuzzer"},
            "ffuf": {"category": "web_scan", "description": "Fast web fuzzer"},
            
            # Exploitation
            "sqlmap": {"category": "exploitation", "description": "SQL injection tool"},
            "msfconsole": {"category": "exploitation", "description": "Metasploit Framework console"},
            "msfvenom": {"category": "exploitation", "description": "Metasploit payload generator"},
            "searchsploit": {"category": "exploitation", "description": "Exploit-DB search tool"},
            "exploit-db": {"category": "exploitation", "description": "Exploit database"},
            
            # Password cracking
            "hydra": {"category": "password", "description": "Network login cracker"},
            "john": {"category": "password", "description": "John the Ripper password cracker"},
            "hashcat": {"category": "password", "description": "Advanced password recovery"},
            "crunch": {"category": "password", "description": "Wordlist generator"},
            "cewl": {"category": "password", "description": "Custom wordlist generator"},
            
            # Wireless
            "aircrack-ng": {"category": "wireless", "description": "WiFi security auditing"},
            "airodump-ng": {"category": "wireless", "description": "WiFi packet capture"},
            "aireplay-ng": {"category": "wireless", "description": "WiFi packet injection"},
            "reaver": {"category": "wireless", "description": "WPS attack tool"},
            "wash": {"category": "wireless", "description": "WPS scanner"},
            "bully": {"category": "wireless", "description": "WPS brute force"},
            
            # Enumeration
            "enum4linux": {"category": "enumeration", "description": "SMB enumeration tool"},
            "smbclient": {"category": "enumeration", "description": "SMB/CIFS client"},
            "rpcclient": {"category": "enumeration", "description": "RPC client tool"},
            "snmp-check": {"category": "enumeration", "description": "SNMP enumerator"},
            "ldapsearch": {"category": "enumeration", "description": "LDAP search tool"},
            
            # DNS
            "dig": {"category": "dns", "description": "DNS lookup tool"},
            "nslookup": {"category": "dns", "description": "DNS query tool"},
            "host": {"category": "dns", "description": "DNS lookup utility"},
            "dnsenum": {"category": "dns", "description": "DNS enumeration tool"},
            "dnsrecon": {"category": "dns", "description": "DNS reconnaissance tool"},
            "fierce": {"category": "dns", "description": "DNS reconnaissance"},
            
            # Information gathering
            "whois": {"category": "info_gathering", "description": "Domain/IP information"},
            "theHarvester": {"category": "info_gathering", "description": "Email/subdomain gatherer"},
            "recon-ng": {"category": "info_gathering", "description": "Reconnaissance framework"},
            "shodan": {"category": "info_gathering", "description": "Shodan CLI"},
            
            # Sniffing
            "tshark": {"category": "sniffing", "description": "CLI network analyzer"},
            "tcpdump": {"category": "sniffing", "description": "Packet analyzer"},
            
            # Forensics
            "binwalk": {"category": "forensics", "description": "Firmware analysis tool"},
            "foremost": {"category": "forensics", "description": "File carving tool"},
            "volatility": {"category": "forensics", "description": "Memory forensics"},
            
            # Social Engineering
            "setoolkit": {"category": "social_eng", "description": "Social Engineering Toolkit"},
            
            # Utilities
            "curl": {"category": "utilities", "description": "HTTP client"},
            "wget": {"category": "utilities", "description": "File downloader"},
            "git": {"category": "utilities", "description": "Version control"},
            "python3": {"category": "utilities", "description": "Python interpreter"},
        }
    
    def check_tool_installed(self, tool_name: str) -> bool:
        """Verifica si una herramienta está instalada"""
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def get_tool_path(self, tool_name: str) -> Optional[str]:
        """Obtiene la ruta completa de una herramienta"""
        try:
            result = subprocess.run(
                ["which", tool_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """Intenta obtener la versión de una herramienta"""
        version_flags = ["--version", "-v", "-V", "version"]
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [tool_name, flag],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and result.stdout:
                    # Tomar primera línea
                    return result.stdout.split('\n')[0][:100]
            except:
                continue
        
        return "Unknown version"
    
    def scan_installed_tools(self) -> Dict:
        """Escanea todas las herramientas instaladas"""
        print("🔍 Escaneando herramientas instaladas...")
        
        installed = {}
        
        for tool_name, info in self.common_kali_tools.items():
            if self.check_tool_installed(tool_name):
                path = self.get_tool_path(tool_name)
                version = self.get_tool_version(tool_name)
                
                installed[tool_name] = {
                    "installed": True,
                    "path": path,
                    "version": version,
                    "category": info["category"],
                    "description": info["description"]
                }
                print(f"  ✅ {tool_name}")
        
        self.discovered_tools = installed
        print(f"\n✅ Encontradas {len(installed)} herramientas")
        return installed
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """Obtiene herramientas por categoría"""
        return [
            name for name, info in self.discovered_tools.items()
            if info.get("category") == category
        ]
    
    def get_all_categories(self) -> List[str]:
        """Obtiene todas las categorías disponibles"""
        categories = set()
        for info in self.discovered_tools.values():
            categories.add(info.get("category", "unknown"))
        return sorted(list(categories))
    
    def suggest_install(self, tool_name: str) -> Dict:
        """Sugiere cómo instalar una herramienta"""
        install_commands = {
            # APT packages
            "nmap": "sudo apt install nmap",
            "nikto": "sudo apt install nikto",
            "gobuster": "sudo apt install gobuster",
            "sqlmap": "sudo apt install sqlmap",
            "hydra": "sudo apt install hydra",
            "john": "sudo apt install john",
            "hashcat": "sudo apt install hashcat",
            "aircrack-ng": "sudo apt install aircrack-ng",
            "wireshark": "sudo apt install wireshark",
            "metasploit-framework": "sudo apt install metasploit-framework",
            "msfvenom": "sudo apt install metasploit-framework",
            "wpscan": "sudo gem install wpscan",
            "whatweb": "sudo apt install whatweb",
            "enum4linux": "sudo apt install enum4linux",
            "masscan": "sudo apt install masscan",
            "reaver": "sudo apt install reaver",
            "ettercap": "sudo apt install ettercap-graphical",
            "binwalk": "sudo apt install binwalk",
            "volatility": "sudo apt install volatility",
        }
        
        command = install_commands.get(tool_name, f"sudo apt install {tool_name}")
        
        return {
            "tool": tool_name,
            "installed": self.check_tool_installed(tool_name),
            "install_command": command,
            "package_manager": "apt"
        }
    
    def export_tools_list(self, filepath: str = "installed_tools.json"):
        """Exporta la lista de herramientas a JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.discovered_tools, f, indent=2)
        print(f"✅ Lista exportada a {filepath}")
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Obtiene información completa de una herramienta"""
        if tool_name in self.discovered_tools:
            return self.discovered_tools[tool_name]
        
        # Si no está descubierta, buscar en la lista común
        if tool_name in self.common_kali_tools:
            info = self.common_kali_tools[tool_name].copy()
            info["installed"] = False
            info["path"] = None
            return info
        
        return None


# Singleton para uso global
_tool_discovery = None

def get_tool_discovery():
    """Obtiene la instancia global de ToolDiscovery"""
    global _tool_discovery
    if _tool_discovery is None:
        _tool_discovery = ToolDiscovery()
        _tool_discovery.scan_installed_tools()
    return _tool_discovery


if __name__ == "__main__":
    # Test
    td = ToolDiscovery()
    tools = td.scan_installed_tools()
    
    print(f"\n📊 Resumen por categorías:")
    for cat in td.get_all_categories():
        tools_in_cat = td.get_tools_by_category(cat)
        print(f"  {cat}: {len(tools_in_cat)} herramientas")
    
    td.export_tools_list()

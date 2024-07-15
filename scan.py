import subprocess
import pandas as pd
from datetime import datetime

def realizar_escaneo(ip_range):
    comando = f"nmap -sn {ip_range}"
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    
    ip_list = []
    for line in resultado.stdout.split('\n'):
        if 'Nmap scan report for' in line:
            ip = line.split(' ')[-1]
            ip_list.append({'ip': ip, 'estado': 'up', 'fecha_escaneo': datetime.now()})
        elif 'Host is down' in line:
            ip = line.split(' ')[-1]
            ip_list.append({'ip': ip, 'estado': 'down', 'fecha_escaneo': datetime.now()})
    
    df = pd.DataFrame(ip_list)
    return df

def realizar_escaneo_puertos(ip_list):
    ip_str = ' '.join(ip_list)
    comando = f"nmap -p- {ip_str}"
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    
    port_list = []
    current_ip = None
    for line in resultado.stdout.split('\n'):
        if 'Nmap scan report for' in line:
            current_ip = line.split(' ')[-1]
        elif '/tcp' in line or '/udp' in line:
            parts = line.split()
            port = parts[0]
            state = parts[1]
            port_list.append({'ip': current_ip, 'puerto': port, 'estado': state, 'fecha_escaneo': datetime.now()})
    
    df = pd.DataFrame(port_list)
    return df

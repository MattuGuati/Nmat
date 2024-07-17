import subprocess
import pandas as pd
from datetime import datetime

def limpiar_ip(ip):
    return ip.strip('()')

def realizar_escaneo(ip_range):
    comando = f"nmap -sn {ip_range}"
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    
    ip_list = []
    for line in resultado.stdout.split('\n'):
        if 'Nmap scan report for' in line:
            ip = line.split(' ')[-1]
            ip_list.append({'ip': limpiar_ip(ip), 'estado': 'up', 'fecha_escaneo': datetime.now()})
        elif 'Host is down' in line:
            ip = line.split(' ')[-1]
            ip_list.append({'ip': limpiar_ip(ip), 'estado': 'down', 'fecha_escaneo': datetime.now()})
    
    df = pd.DataFrame(ip_list)
    return df

def realizar_escaneo_puertos(ip_list):
    ip_str = ' '.join(ip_list)
    puertos = '22,25,80,3389,443'
    comando = f"nmap -p {puertos} {ip_str}"
    resultado = subprocess.run(comando, capture_output=True, text=True, shell=True)
    
    port_list = []
    current_ip = None
    for line in resultado.stdout.split('\n'):
        if 'Nmap scan report for' in line:
            current_ip = limpiar_ip(line.split(' ')[-1])
        elif '/tcp' in line or '/udp' in line:
            parts = line.split()
            port = parts[0]
            state = parts[1]
            port_list.append({'ip': current_ip, 'puerto': port, 'estado': state, 'fecha_escaneo': datetime.now()})
    
    df = pd.DataFrame(port_list)
    return df

def leer_escaneo_anterior(tipo='ip'):
    try:
        if tipo == 'ip':
            return pd.read_csv('scan_results.csv')
        else:
            return pd.read_csv('port_results.csv')
    except FileNotFoundError:
        if tipo == 'ip':
            return pd.DataFrame(columns=['ip', 'estado', 'fecha_escaneo'])
        else:
            return pd.DataFrame(columns=['ip', 'puerto', 'estado', 'fecha_escaneo'])

def guardar_escaneo(df, tipo='ip'):
    if tipo == 'ip':
        df.to_csv('scan_results.csv', index=False)
    else:
        df.to_csv('port_results.csv', index=False)

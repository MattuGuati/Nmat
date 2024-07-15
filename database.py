import mysql.connector
import pandas as pd

# Configuración de la base de datos
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Dogchog123'
DB_NAME = 'escaneored'

def conectar_bd():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def guardar_resultados_bd(scan_results_df, port_results_df):
    conn = conectar_bd()
    cursor = conn.cursor()

    for index, row in scan_results_df.iterrows():
        cursor.execute("""
            INSERT INTO scan_results (ip, estado, fecha_escaneo)
            VALUES (%s, %s, %s)
        """, (row['ip'], row['estado'], row['fecha_escaneo']))

    for index, row in port_results_df.iterrows():
        cursor.execute("""
            INSERT INTO port_results (ip, puerto, protocolo, estado, fecha_escaneo)
            VALUES (%s, %s, %s, %s, %s)
        """, (row['ip'], row['puerto'], row['protocolo'], row['estado'], row['fecha_escaneo']))

    conn.commit()
    cursor.close()
    conn.close()

def obtener_resultados_anteriores():
    conn = conectar_bd()
    query = """
        SELECT * FROM (
            SELECT ip, estado, fecha_escaneo FROM scan_results ORDER BY fecha_escaneo DESC LIMIT 1
        ) AS last_scan
        UNION ALL
        SELECT * FROM (
            SELECT ip, puerto, protocolo, estado, fecha_escaneo FROM port_results ORDER BY fecha_escaneo DESC LIMIT 1
        ) AS last_ports
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

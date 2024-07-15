import schedule
import time
from scan import realizar_escaneo, realizar_escaneo_puertos, guardar_resultados_bd
from database import connect_to_db

def job():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, rango FROM Rangos_IPs")
    rangos = cursor.fetchall()
    
    for rango in rangos:
        scan_results_df = realizar_escaneo(rango[1])
        port_results_df = realizar_escaneo_puertos(rango[1])
        guardar_resultados_bd(scan_results_df, port_results_df, rango[0])

    conn.close()

schedule.every().day.at("01:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

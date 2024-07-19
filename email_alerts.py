import smtplib
from email.mime.text import MIMEText

def enviar_alerta(alertas):
    remitente = "apismatteo@gmail.com"
    destinatario = "apismatteo@gmail.com"
    asunto = "Alerta de Cambio en Estado de IPs y Puertos"

    mensaje = "\n".join(alertas)

    msg = MIMEText(mensaje)
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = destinatario

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, 'jiqk fmba zmld hlpf')
            server.sendmail(remitente, destinatario, msg.as_string())
        print("Correo enviado correctamente")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, body):
    # Configuración del servidor SMTP y credenciales
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "apismatteo@gmail.com"
    sender_password = "avrj xjgl kszy uvow"
    recipient_email = "apismatteo@gmail.com"

    # Crear el mensaje
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Conectar al servidor SMTP y enviar el correo
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Habilitar depuración
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print("Correo enviado con éxito")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

if __name__ == "__main__":
    subject = "Prueba de Envío de Correo"
    body = "Este es un mensaje de prueba para verificar el envío de correos electrónicos."
    send_email(subject, body)

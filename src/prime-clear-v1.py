import os, time, msvcrt, datetime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def main_menu():
    print("< Bienvenido! >")
    time.sleep(0.5)
    print("Prime-Clear Beta 0.1.15 es un una herramienta que verifica que seas un jugador legit...")
    time.sleep(0.5)
    while True:
        welcome_quest = input(
            "¿Quieres continuar?\nY = Si, N = No, X = Salir: "
        ).upper()

        if welcome_quest == "Y":
            print(">> Iniciando validacion...")
            time.sleep(1)
            res = prime_clear()
            time.sleep(1)
            user_result(res)

        elif welcome_quest == "N":
            print(">> Lamentamos que no quieras continuar...")

        elif welcome_quest == "X":
            print(">> Adios!!")
            time.sleep(2)
            break

        else:
            print("Opcion no valida, prueba de nuevo.")

        if welcome_quest in ["N", "Y"]:
            time.sleep(2)
            print("Presiona cualquier tecla para salir...")
            msvcrt.getch()  # Espera a que el usuario presione cualquier tecla
            break

def prime_clear():
    user = input("Ingresa tu gamertag de Valorant (Ejemplo: SEN TenZ#81619): ")
    print(">> Procesando...")

    ## ==[Valida los usuarios]==
    pass_s1 = True
    account_list = []
    path_accounts = os.path.join(
        os.environ.get("LOCALAPPDATA"), os.path.expanduser("VALORANT\saved\Config")
    )

    for account in os.listdir(path_accounts):
        if account not in ["CrashReportClient", "Windows"]:
            account_list.append(account)

    if len(account_list) > 2:
        pass_s1 = False

    ## ==[Valida logs del juego]==
    pass_s2 = True
    path_logs = os.path.join(
        os.environ.get("LOCALAPPDATA"), os.path.expanduser("VALORANT\saved\Logs")
    )
    find_text = "/Game/Maps/Menu/MainMenuV2"
    file_log_list = []
    logs_list = []

    for raiz, directorios, archivos in os.walk(path_logs):
        for archivo in archivos:
            if archivo.endswith(".log"):  # Filtrar solo archivos con extensión .log
                file_log_list.append(archivo)
                ruta_completa = os.path.join(raiz, archivo)
                logs_list = log_filter(ruta_completa, find_text)
                logs_list.extend(logs_list)

    ## """Indica si paso la prueba""" 
    res = pass_s1 == pass_s2

    ## ==[Envia por correo los resultados]==
    res_mail = send_mail(account_list, file_log_list, logs_list, user, res)
    
    if res_mail:
        return res
    else:
        return "error"

def send_mail(accounts, files, logs, user, res):
    try:
        # Configura los detalles del servidor SMTP
        smtp_server = "smtp.gmail.com"  # Por ejemplo, smtp.gmail.com para Gmail
        smtp_port = 587  # Puerto para TLS
        smtp_username = "valorant.notify.apps@gmail.com"  # Tu dirección de correo electrónico
        smtp_password = "ewko ctwq zddx bdoi"  # Tu contraseña de correo electrónico

        from datetime import timezone

        # Obten la fecha y hora actual en UTC
        now_utc = datetime.datetime.now(timezone.utc)

        # Calcula la diferencia de tiempo entre UTC y la Ciudad de México (CDMX), que es UTC-5 horas en horario estándar (UTC-6 en horario de verano)
        diferencia_cdmx = datetime.timedelta(hours=-5)

        # Ajusta la fecha y hora actual a la zona horaria de la Ciudad de México
        now_cdmx = now_utc + diferencia_cdmx

        # Formatea la fecha y hora en el formato deseado
        fecha_hora_cdmx = now_cdmx.strftime('%Y-%m-%d %H:%M:%S CDMX')

        # Configura los detalles del correo electrónico
        sender = "PrimeClear"
        recipient = "osperez.contacto@gmail.com"
        subject = "[PrimeClear] ¡Nuevos resultados de" + user + " ! - " + str(fecha_hora_cdmx)
        body =  "Legit: "+ str(res) +"\n\n uuids: "+", ".join(accounts) + "\n\n filter log: " + ";;, ".join(logs)

        # Crea un objeto MIMEMultipart para el correo
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject

        # Adjunta el cuerpo del correo
        message.attach(MIMEText(body, "plain"))

        path_logs = os.path.join(
            os.environ.get("LOCALAPPDATA"), os.path.expanduser("VALORANT\saved\Logs")
        )
        log_files = files

        # Lista para almacenar los archivos adjuntos que exceden el límite
        oversized_attachments = []

        # Tamaño total de los archivos adjuntos
        total_size = 0

        # Adjuntar cada archivo .log y calcular el tamaño total
        for log_file in log_files:
            ruta_completa = os.path.join(path_logs, log_file)
            if os.path.exists(ruta_completa):
                file_size = os.path.getsize(ruta_completa)
                total_size += file_size
                if total_size <= 20 * 1024 * 1024:  # 20 MB en bytes
                    with open(ruta_completa, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(ruta_completa)}",
                        )
                        message.attach(part)
                else:
                    oversized_attachments.append(ruta_completa)

        # Si hay archivos adjuntos que superan el límite
        if oversized_attachments:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            for attachment_path in oversized_attachments:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(attachment_path)}",
                    )
                    new_message = MIMEMultipart()
                    new_message.attach(MIMEText(body, "plain"))
                    new_message.attach(part)
                    new_message["From"] = sender
                    new_message["To"] = recipient
                    new_message["Subject"] = subject #+ " ("+str(part)+")"
                    # Envía el correo electrónico
                    server.send_message(new_message)

            # Cierra la conexión con el servidor SMTP
            server.quit()

        # Si no se excedió el límite, envía el correo normalmente
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
            # Cierra la conexión con el servidor SMTP
            server.quit()

        return True
    except Exception as e:
        # Captura la excepción y muestra el mensaje de error
        #print(f"Ocurrió un error: {e}")
        print("[⚠️] Error de ejecucion... Busca una nueva version o notifica al creador.")
        return False
    
def log_filter(file, text):
    find_log = []
    try:
        with open(file, "r") as f:
            for linea in f:
                if text in linea:
                    find_log.append(linea.strip())
    except FileNotFoundError:
        find_log.append("[NO FOUND LOGS]:" + os.path.basename(file))

    return find_log


def user_result(result):
    if result == True:
        print("Felicidades eres completamente legit!!")
    elif result == "error":
        print()
    else:
        print(
            "Prueba terminada!! Validaremos tus resultados y muy pronto te lo notificaremos"
        )


if __name__ == "__main__":

    main_menu()

import os
import base64
import smtplib
import logging
import mimetypes
from email.message import EmailMessage
import requests
from python_multipart import parse_form

# Настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Переменные окружения
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', 'user')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'user123')
MAIL_TO = os.environ.get('MAIL_TO', 'user@test')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '123')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '123')


def send_email(phone, data, photo_content=None, photo_filename=None):
    """Отправка email"""
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Новое сообщение от {phone}'
        msg['From'] = SMTP_USER
        msg['To'] = MAIL_TO
        msg.set_content(f"""
    {data}
""")

        if photo_content and photo_filename:
            mime_type, _ = mimetypes.guess_type(photo_filename)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            maintype, subtype = mime_type.split('/')
            msg.add_attachment(photo_content, maintype=maintype,
                               subtype=subtype, filename=photo_filename)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent")
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False


def send_telegram(name, email, message, photo_content=None, photo_filename=None):
    """Отправка в Telegram (используем HTML для избежания проблем с экранированием)"""
    try:
        # Используем HTML вместо Markdown
        text = f"<b>Новое сообщение</b>\nИмя: {name}\nEmail: {email}\nСообщение: {message}"
        if photo_content and photo_filename:
            files = {'photo': (photo_filename, photo_content, 'image/jpeg')}
            data = {'chat_id': TELEGRAM_CHAT_ID,
                    'caption': text, 'parse_mode': 'HTML'}
            resp = requests.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto', data=data, files=files)
        else:
            data = {'chat_id': TELEGRAM_CHAT_ID,
                    'text': text, 'parse_mode': 'HTML'}
            resp = requests.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', data=data)
        resp.raise_for_status()
        logger.info("Telegram sent")
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


def handler(event, context):
    """
    Обработчик Yandex Cloud Function.
    Ожидает POST запрос с multipart/form-data (форма с файлом).
    """
    try:
        headers = event.get('headers', {})
        content_type = headers.get(
            'content-type') or headers.get('Content-Type', '')
        is_base64 = event.get('isBase64Encoded', False)
        body = event.get('body', '')

        if is_base64:
            body = base64.b64decode(body)
        else:
            if isinstance(body, str):
                body = body.encode('utf-8')

        from io import BytesIO
        stream = BytesIO(body)

        form = {}
        files = []

        def on_field(field):
            form[field.field_name.decode()] = field.value.decode()

        def on_file(file):
            files.append(file)

        parse_form(headers, stream, on_field, on_file)

        brand = form.get('brand', [''])[0]
        model = form.get('model', [''])[0]
        year = form.get('year', [''])[0]
        condition = form.get('condition', [''])[0]
        not_beaten = form.get('notBeaten', [''])[0]
        price = form.get('price', [''])[0]
        phone = form.get('phone', [''])[0]

        data = {
            'brand': brand,
            'model': model,
            'year': year,
            'condition': condition,
            'not_beaten': not_beaten,
            'price': price,
            'phone': phone
        }

        if files:
            photo_file = files[0]
        else:
            photo_file = None
        photo_content = None
        photo_filename = None

        if photo_file:
            photo_content = photo_file.file.read()
            photo_filename = photo_file.filename

        email_ok = send_email(phone, data,
                              photo_content, photo_filename)

        # telegram_ok = send_telegram(
        #    name, email, message, photo_content, photo_filename)

        if email_ok:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': '{"status": "ok", "message": "Сообщение отправлено"}'
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': '{"error": "Failed to send notifications"}'
            }

    except Exception as e:
        logger.exception("Unhandled error")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "Internal server error: {str(e)}"}}'
        }

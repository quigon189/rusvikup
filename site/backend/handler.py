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


def send_email(phone, data, attachments=None):
    """
    Отправка email с возможными вложениями.
    attachments: список кортежей (file_content, filename)
    """
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Новая заявка на выкуп авто от {phone}'
        msg['From'] = SMTP_USER
        msg['To'] = MAIL_TO

        # Формируем текст письма из всех полей формы
        body = f"""
Марка: {data.get('brand', '')}
Модель: {data.get('model', '')}
Год: {data.get('year', '')}
Состояние: {data.get('condition', '')}
Не битый: {'Да' if data.get('notBeaten') else 'Нет'}
Желаемая цена: {data.get('price', '')} ₽
Телефон: {data.get('phone', '')}
Сообщение: {data.get('message', '')}
"""
        msg.set_content(body)

        # Прикрепляем все файлы, если есть
        if attachments:
            for file_content, filename in attachments:
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                maintype, subtype = mime_type.split('/')
                msg.add_attachment(file_content, maintype=maintype,
                                   subtype=subtype, filename=filename)

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
    """Отправка в Telegram (используем HTML) — пока без изменений, отправляет только одно фото"""
    try:
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
    Ожидает POST запрос с multipart/form-data (форма с файлами).
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

        # Извлекаем поля формы
        brand = form.get('brand', '')
        model = form.get('model', '')
        year = form.get('year', '')
        condition = form.get('condition', '')
        not_beaten = form.get('notBeaten', '')  # будет 'on' если отмечен
        price = form.get('price', '')
        phone = form.get('phone', '')
        message = form.get('message', '')  # новое необязательное поле

        data = {
            'brand': brand,
            'model': model,
            'year': year,
            'condition': condition,
            'not_beaten': not_beaten,
            'price': price,
            'phone': phone,
            'message': message
        }

        # Обрабатываем все приложенные файлы
        attachments = []
        # if files:
        #     for file_obj in files:
        #         # Читаем содержимое файла
        #         file_content = file_obj.file.read()
        #         filename = file_obj.filename
        #         attachments.append((file_content, filename))

        # Отправляем email
        email_ok = send_email(phone, data, attachments)

        # При необходимости можно добавить отправку в Telegram,
        # но с несколькими фото это потребует доработки (например, отправка медиагруппой)

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

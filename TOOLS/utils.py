# tools/utils.py
"""
Narzędzia pomocnicze dla aplikacji TOOLS
"""

from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_html_email(recipient_email, subject, html_content, attachments=None):
    """
    Wysyła email HTML na wskazany adres.

    Args:
        recipient_email (str): Adres email odbiorcy
        subject (str): Temat wiadomości
        html_content (str): Treść HTML wiadomości
        attachments (list, optional): Lista plików do załączenia [(filename, content, mimetype), ...]

    Returns:
        dict: {'success': bool, 'message': str}

    Example:
        result = send_html_email(
            recipient_email='test@example.com',
            subject='Test Email',
            html_content='<h1>Hello</h1><p>This is a test.</p>'
        )
        if result['success']:
            print("Email wysłany!")
        else:
            print(f"Błąd: {result['message']}")
    """
    try:
        # Walidacja podstawowa
        if not recipient_email:
            return {
                'success': False,
                'message': 'Adres email odbiorcy jest wymagany.'
            }

        if not subject:
            return {
                'success': False,
                'message': 'Temat wiadomości jest wymagany.'
            }

        if not html_content:
            return {
                'success': False,
                'message': 'Treść wiadomości jest wymagana.'
            }

        # Sprawdź czy email jest skonfigurowany
        if not settings.EMAIL_HOST_USER:
            return {
                'success': False,
                'message': 'Brak konfiguracji konta email w settings.py'
            }

        # Tworzenie wiadomości email
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )

        # Ustawienie typu treści jako HTML
        email.content_subtype = "html"

        # Dodawanie załączników jeśli są
        if attachments:
            for filename, content, mimetype in attachments:
                email.attach(filename, content, mimetype)

        # Wysyłka
        email.send(fail_silently=False)

        logger.info(f"Email wysłany pomyślnie do: {recipient_email}")

        return {
            'success': True,
            'message': f'Email wysłany pomyślnie na adres: {recipient_email}'
        }

    except Exception as e:
        error_message = f"Błąd wysyłki email: {str(e)}"
        logger.error(error_message)

        return {
            'success': False,
            'message': error_message
        }


def send_test_email(recipient_email=None):
    """
    Wysyła testowy email HTML.

    Args:
        recipient_email (str, optional): Adres testowy. Jeśli None, używa EMAIL_TEST_ADDRESS z settings.

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not recipient_email:
        recipient_email = getattr(settings, 'EMAIL_TEST_ADDRESS', None)

    if not recipient_email:
        return {
            'success': False,
            'message': 'Brak adresu testowego w konfiguracji.'
        }

    subject = "Test Email - CNC Tools"

    html_content = """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }
            .email-container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: 0 auto;
            }
            h1 {
                color: #007bff;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }
            .info-box {
                background-color: #e7f3ff;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 20px 0;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #777;
                font-size: 0.9em;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>🔧 CNC Tools - Test Email</h1>

            <p>To jest <strong>testowa wiadomość email</strong> z systemu CNC Tools.</p>

            <div class="info-box">
                <strong>✅ Konfiguracja email działa poprawnie!</strong><br>
                System jest gotowy do wysyłania wiadomości.
            </div>

            <p>Możesz teraz używać funkcji wysyłki emaili w aplikacji:</p>
            <ul>
                <li>Wysyłka zamówień do dostawców</li>
                <li>Powiadomienia o stanach magazynowych</li>
                <li>Raporty i zestawienia</li>
            </ul>

            <div class="footer">
                <p><strong>CNC Tools</strong> - System Zarządzania Narzędziami CNC</p>
                <p>Ten email został wygenerowany automatycznie.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_html_email(
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content
    )

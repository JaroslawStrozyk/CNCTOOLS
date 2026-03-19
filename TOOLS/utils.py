# tools/utils.py
"""
Narzędzia pomocnicze dla aplikacji TOOLS
"""

from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_html_email(recipient_email, subject, html_content, attachments=None, cc_email=None):
    """
    Wysyła email HTML na wskazany adres.

    Args:
        recipient_email (str): Adres email odbiorcy
        subject (str): Temat wiadomości
        html_content (str): Treść HTML wiadomości
        attachments (list, optional): Lista plików do załączenia [(filename, content, mimetype), ...]
        cc_email (str, optional): Adres email DW (kopia wiadomości)

    Returns:
        dict: {'success': bool, 'message': str}

    Example:
        result = send_html_email(
            recipient_email='test@example.com',
            subject='Test Email',
            html_content='<h1>Hello</h1><p>This is a test.</p>',
            cc_email='dw@example.com'
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

        # Przygotuj listę odbiorców
        to_list = [recipient_email]
        cc_list = []

        # Dodaj kopię DW jeśli podano
        if cc_email:
            cc_list.append(cc_email)

        # Tworzenie wiadomości email
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_list,
            cc=cc_list if cc_list else None,
        )

        # Ustawienie typu treści jako HTML
        email.content_subtype = "html"

        # Dodawanie załączników jeśli są
        if attachments:
            for filename, content, mimetype in attachments:
                email.attach(filename, content, mimetype)

        # Wysyłka
        email.send(fail_silently=False)

        recipients_info = recipient_email
        if cc_email:
            recipients_info += f" (DW: {cc_email})"

        logger.info(f"Email wysłany pomyślnie do: {recipients_info}")

        return {
            'success': True,
            'message': f'Email wysłany pomyślnie na adres: {recipients_info}'
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
    Wysyła testowy email HTML z kopią DW.

    Args:
        recipient_email (str, optional): Adres testowy. Jeśli None, używa EMAIL_TEST_ADDRESS z settings.

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from django.utils import timezone

    if not recipient_email:
        recipient_email = getattr(settings, 'EMAIL_TEST_ADDRESS', None)

    if not recipient_email:
        return {
            'success': False,
            'message': 'Brak adresu testowego w konfiguracji.'
        }

    # Pobierz adres DW z settings
    cc_email = getattr(settings, 'EMAIL_DW', None)

    subject = "Test Email - CNC Tools"

    # Pobierz aktualną datę i czas
    now = timezone.now()
    data_wyslania = now.strftime('%Y-%m-%d %H:%M:%S')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
                margin: 0;
            }}
            .email-container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 900px;
                margin: 0 auto;
            }}
            .header {{
                background: linear-gradient(to bottom, #FF0000, #8B0000);
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 20px -30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .info-box {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .info-box p {{
                margin: 5px 0;
                line-height: 1.6;
            }}
            .success-box {{
                background-color: #d4edda;
                border-left: 4px solid #198754;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #ff7b00;
                color: #666;
                font-size: 0.9em;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔧 CNC Tools - Test Email</h1>
            </div>

            <div class="info-box">
                <p><strong>Data:</strong> {data_wyslania}</p>
                <p><strong>Adresat:</strong> {recipient_email}</p>
            </div>

            <p>To jest <strong>testowa wiadomość email</strong> z systemu CNC Tools.</p>

            <div class="success-box">
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
                <p style="color: #666; margin-bottom: 15px;">Ten email został wygenerowany automatycznie przez system CNC Tools.</p>
                <p><strong>CNC Tools</strong> — System Zarządzania Narzędziami CNC</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_html_email(
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content,
        cc_email=cc_email
    )


def send_zamowienie_email(zamowienie, override_email=None):
    """
    Wysyła email z zamówieniem do dostawcy (+ kopia DW).

    Args:
        zamowienie: Obiekt Zamowienie z powiązanymi pozycjami
        override_email: Opcjonalny adres email (tryb testowy)

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from django.utils import timezone

    # Pobierz email DW z settings
    cc_email = getattr(settings, 'EMAIL_DW', None)

    # Przygotuj dane
    dostawca = zamowienie.dostawca
    pozycje = zamowienie.pozycje.all()

    # Data wysłania
    now = timezone.now()
    data_wyslania_data = now.strftime('%Y-%m-%d')

    # Tytuł emaila
    subject = f"Zamówienie nr {zamowienie.numer} - CNC Milling"

    # Generuj wiersze tabeli pozycji
    pozycje_html = ''
    suma_ilosc = 0
    for poz in pozycje:
        suma_ilosc += poz.ilosc_zamowiona
        jednostka_display = f"kompl. ({poz.ilosc_w_komplecie} szt.)" if poz.jednostka == 'kompl' else 'szt.'

        pozycje_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.kategoria_nazwa}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.podkategoria_nazwa}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;"><strong>{poz.narzedzie_opis}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.numer_katalogowy}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;"><strong>{poz.ilosc_zamowiona}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{jednostka_display}</td>
        </tr>
        """

    # Uwagi (jeśli są)
    uwagi_html = ''
    if zamowienie.uwagi:
        uwagi_html = f"""
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <strong style="color: #856404;">📝 Uwagi do zamówienia:</strong><br>
            <p style="margin: 10px 0 0 0; color: #856404;">{zamowienie.uwagi}</p>
        </div>
        """

    # Szablon HTML emaila
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
                margin: 0;
            }}
            .email-container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 900px;
                margin: 0 auto;
            }}
            .header {{
                background: linear-gradient(to bottom, #FF0000, #8B0000);
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 20px -30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .info-box {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .info-box p {{
                margin: 5px 0;
                line-height: 1.6;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: #ADADAD;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            .total-row {{
                background-color: #DADADA;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #ff7b00;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔧 Zamówienie dla CNC Milling sp. z o.o. sp. K. </h1>
            </div>

            <div class="info-box">
                <p><strong>Data:</strong> {data_wyslania_data}</p>
                <p><strong>Numer zamówienia:</strong> {zamowienie.numer}</p>
                <p><strong>Dostawca:</strong> {dostawca.nazwa_firmy}</p>
                <p><strong>NIP:</strong> {dostawca.nip or '-'}</p>
                <p><strong>Email:</strong> {zamowienie.email_docelowy}</p>
            </div>

            {uwagi_html}

            <h3 style="color: #ff7b00; margin-top: 30px;">Pozycje zamówienia:</h3>

            <table>
                <thead>
                    <tr>
                        <th>Kategoria</th>
                        <th>Podkategoria</th>
                        <th>Narzędzie</th>
                        <th>Nr katalogowy</th>
                        <th style="text-align: center;">Ilość</th>
                        <th style="text-align: center;">Jednostka</th>
                    </tr>
                </thead>
                <tbody>
                    {pozycje_html}
                    <tr class="total-row">
                        <td colspan="4" style="padding: 15px; text-align: right;">RAZEM POZYCJI:</td>
                        <td style="padding: 15px; text-align: center;"><strong style="font-size: 1.2em;">{suma_ilosc}</strong></td>
                        <td></td>
                    </tr>
                </tbody>
            </table>

            <div class="footer">
                <p style="color: #666; text-align: center; margin-bottom: 30px;">Ten email został wygenerowany automatycznie przez system CNC Tools (email: zakupy@cncmilling.pl).</p>
                <p>Pozdrawiam,</p>
                <p>
                    <strong>Tomasz Olejniczak</strong><br>
                    <span style="color: #999999;">Specjalista ds. zaopatrzenia, narzędzi i kooperacji</span><br><br>
                    tel.: +48 605 077 306<br>
                    e-mail: <a href="mailto:t.olejniczak@cncmilling.pl" style="color: #ff7b00; text-decoration: none;">t.olejniczak@cncmilling.pl</a>
                </p>
                <table style="width: 100%; max-width: 580px; border-collapse: collapse; margin-top: 15px;" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="width: 170px; padding: 5px; vertical-align: top;">
                            <img src="data:image/png;base64,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" alt="CNC Milling" style="width: 168px; height: 74px;" />
                        </td>
                        <td style="width: 10px;"></td>
                        <td style="padding: 5px; vertical-align: top; color: #999999; font-size: 12px; line-height: 1.5;">
                            CNC Milling Spółka<br>
                            z ograniczoną<br>
                            odpowiedzialnością, sp. k.<br>
                            ul. Przemysłowa 12<br>
                            62-023&nbsp;Żerniki
                        </td>
                        <td style="width: 5px;"></td>
                        <td style="padding: 5px; vertical-align: top; color: #999999; font-size: 12px; line-height: 1.5;">
                            <br>
                            <a href="http://www.cncmilling.pl/" style="color: #ff7b00; text-decoration: none;">www.cncmilling.pl</a><br>
                            <a href="mailto:biuro@cncmilling.pl" style="color: #ff7b00; text-decoration: none;">biuro@cncmilling.pl</a>
                        </td>
                        <td style="width: 5px;"></td>
                        <td style="padding: 5px; vertical-align: top; color: #999999; font-size: 12px; line-height: 1.5;">
                            <br>
                            KRS: 0000467896<br>
                            NIP: 779-241-45-18
                        </td>
                    </tr>
                </table>
                <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #e0e0e0;">
                    <p style="font-size: 10px; color: #999999; text-align: justify; line-height: 1.4;">
                        <i>UWAGA: Treść tej wiadomości, oraz wszelkie załączone do niej pliki są poufne i zawierają informacje przeznaczone tylko dla adresata. Z tego względu podlegają ochronie prawnej. Jeżeli nie jesteście Państwo zamierzonym adresatem niniejszej wiadomości, bądź otrzymaliście ją przez pomyłkę, nie możecie Państwo jej ujawniać, kopiować, dystrybuować ani też w żaden inny sposób udostępniać lub wykorzystywać. O błędnym zaadresowaniu wiadomości prosimy niezwłocznie poinformować nadawcę a wiadomość wraz z ewentualnymi załącznikami usunąć w sposób trwały.</i>
                    </p>
                    <p style="font-size: 10px; color: #999999; text-align: justify; line-height: 1.4; margin-top: 10px;">
                        <i>ATTENTION: This e-mail message is confidential and is intended for receipt solely by the individual or entity to which it is addressed. That is why it is lawfully protected. If you have received this message in error, or are not the named recipient(s), you are hereby notified that any disclosure, dissemination or duplication of the whole message or its parts is forbidden. Please immediately notify the sender and delete this e-mail message from your computer.</i>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return send_html_email(
        recipient_email=override_email or zamowienie.email_docelowy,
        subject=subject,
        html_content=html_content,
        cc_email=cc_email
    )
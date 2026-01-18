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
            }}
            .email-container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: 0 auto;
            }}
            h1 {{
                color: #007bff;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }}
            .info-box {{
                background-color: #e7f3ff;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 20px 0;
            }}
            .date-time {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
                text-align: center;
                font-size: 0.95em;
                color: #495057;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #777;
                font-size: 0.9em;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>🔧 CNC Tools - Test Email</h1>

            <div class="date-time">
                <strong>📅 Data i godzina wysłania:</strong><br>
                {data_wyslania}
            </div>

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
        html_content=html_content,
        cc_email=cc_email
    )


def send_zamowienie_email(zamowienie):
    """
    Wysyła email z zamówieniem do dostawcy (+ kopia DW).

    Args:
        zamowienie: Obiekt Zamowienie z powiązanymi pozycjami

    Returns:
        dict: {'success': bool, 'message': str}
    """
    from django.utils import timezone

    # Pobierz email DW z settings
    cc_email = getattr(settings, 'EMAIL_DW', None)

    # Przygotuj dane
    dostawca = zamowienie.dostawca
    pozycje = zamowienie.pozycje.all()

    # Data i godzina wysłania
    now = timezone.now()
    data_wyslania = now.strftime('%Y-%m-%d %H:%M:%S')

    # Tytuł emaila
    subject = f"Zamówienie nr {zamowienie.numer} - CNC Milling"

    # Generuj wiersze tabeli pozycji
    pozycje_html = ''
    for poz in pozycje:
        jednostka_display = f"kompl. ({poz.ilosc_w_komplecie} szt.)" if poz.jednostka == 'kompl' else 'szt.'

        pozycje_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.kategoria_nazwa}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.podkategoria_nazwa}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;"><strong>{poz.narzedzie_opis}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{poz.numer_katalogowy}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;"><strong>{poz.ilosc_zamowiona}</strong></td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{jednostka_display}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;">{poz.cena_jednostkowa} zł</td>
            <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: right;"><strong>{poz.wartosc_pozycji} zł</strong></td>
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
            .date-time {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
                text-align: center;
                font-size: 0.95em;
                color: #495057;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔧 Zamówienie dla CNC Milling sp. z o.o. sp. K. </h1>
            </div>

            <div class="date-time">
                <strong>📅 Data i godzina wysłania:</strong> {data_wyslania}
            </div>

            <div class="info-box">
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
                        <th style="text-align: right;">Cena jedn.</th>
                        <th style="text-align: right;">Wartość</th>
                    </tr>
                </thead>
                <tbody>
                    {pozycje_html}
                    <tr class="total-row">
                        <td colspan="7" style="padding: 15px; text-align: right;">WARTOŚĆ CAŁKOWITA:</td>
                        <td style="padding: 15px; text-align: right;"><strong style="font-size: 1.2em;">{zamowienie.wartosc_zamowienia} zł</strong></td>
                    </tr>
                </tbody>
            </table>

            <div class="footer">
                <p>Ten email został wygenerowany automatycznie przez system CNC Tools (email: zakupy@cncmilling.pl).</p>
                <br>
                <p><strong>CNC Milling</strong><br>
                <strong><i>Tomasz Olejniczak</i></strong><br>
                email: t.olejniczak@cncmilling.pl<br>
                <i>tel: +48 605-077-306</i></p>
                <br>
            </div>
        </div>
    </body>
    </html>
    """

    return send_html_email(
        recipient_email=zamowienie.email_docelowy,
        subject=subject,
        html_content=html_content,
        cc_email=cc_email
    )
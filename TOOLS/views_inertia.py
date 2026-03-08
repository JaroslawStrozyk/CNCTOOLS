import json
from inertia import render
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Pracownik
from .logging_service import app_logger, get_user_display_name


def get_info_program():
    """Pobiera informacje o programie z settings, włącznie z ustawieniami PDF"""
    info = {}
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        info = dict(settings.INFO_PROGRAM[0])

    # Dodaj ustawienia PDF
    info['PDF_ZAPOTRZEBOWANIE_WERSJA'] = getattr(settings, 'PDF_ZAPOTRZEBOWANIE_WERSJA', 1)
    info['PDF_ZAPOTRZEBOWANIE_DATA'] = getattr(settings, 'PDF_ZAPOTRZEBOWANIE_DATA', '')
    info['PDF_USZKODZENIE_WERSJA'] = getattr(settings, 'PDF_USZKODZENIE_WERSJA', 1)
    info['PDF_USZKODZENIE_DATA'] = getattr(settings, 'PDF_USZKODZENIE_DATA', '')
    info['PDF_LOGI_WERSJA'] = getattr(settings, 'PDF_LOGI_WERSJA', 1)
    info['PDF_LOGI_DATA'] = getattr(settings, 'PDF_LOGI_DATA', '')
    info['PDF_LISTA_USZKODZEN_WERSJA'] = getattr(settings, 'PDF_LISTA_USZKODZEN_WERSJA', 1)
    info['PDF_LISTA_USZKODZEN_DATA'] = getattr(settings, 'PDF_LISTA_USZKODZEN_DATA', '')
    info['PDF_INWENTURA_WERSJA'] = getattr(settings, 'PDF_INWENTURA_WERSJA', 1)
    info['PDF_INWENTURA_DATA'] = getattr(settings, 'PDF_INWENTURA_DATA', '')

    return info


def get_common_urls():
    """Zwraca wspólne URL-e dla wszystkich widoków Inertia"""
    return {
        'magazyn': '/magazyn/',
        'zakupy': '/zakupy/',
        'zamowienia': '/zamowienia/',
        'ustawienia': '/ustawienia/',
        'generator': '/generator/',
        'realizacja': '/realizacja/',
        'faktury': '/faktury/',
        'zwroty': '/zwroty/',
        'zapotrzebowania': '/zapotrzebowania/',
        'produkcja': '/produkcja/',
        'technologia': '/technologia/',
        'kierownik': '/kierownik/',
        'logi': '/logi/',
        'logout': '/logout/',
    }


def get_redirect_url_for_user(user):
    """Zwraca URL przekierowania na podstawie grupy użytkownika"""
    if user.groups.filter(name='logistyka').exists():
        return 'zakupy'
    elif user.groups.filter(name='produkcja-magazyn').exists():
        return 'produkcja'
    elif user.groups.filter(name='produkcja').exists():
        return 'produkcja'
    elif user.groups.filter(name='kierownik').exists():
        return 'kierownik'
    elif user.groups.filter(name='technologia').exists():
        return 'technologia'
    elif user.groups.filter(name='magazyn').exists():
        return 'magazyn'
    else:
        # Domyślnie magazyn dla użytkowników bez grupy
        return 'magazyn'


def get_auth_data(request):
    """Zwraca wspólne dane auth dla wszystkich widoków"""
    is_logistyka = request.user.groups.filter(name='logistyka').exists()
    is_produkcja_magazyn = request.user.groups.filter(name='produkcja-magazyn').exists()
    is_administrator = request.user.groups.filter(name='administrator').exists()
    # Pobierz pierwszą grupę użytkownika jako "dział"
    user_groups = list(request.user.groups.values_list('name', flat=True))
    grupa = user_groups[0] if user_groups else ''
    return {
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'first_name': request.user.first_name or request.user.username,
            'last_name': request.user.last_name or '',
            'email': request.user.email,
            'grupa': grupa,
        },
        'isLogistyka': is_logistyka,
        'isProdukcjaMagazyn': is_produkcja_magazyn,
        'isAdministrator': is_administrator,
    }


# ===== Widoki Inertia =====

@login_required
def test_inertia(request):
    return render(request, 'Test', {
        'message': 'Hello from Django + Inertia!',
        'auth': {
            'user': {
                'username': request.user.username,
                'email': request.user.email,
            }
        }
    })


@login_required
def magazyn_view(request):
    """Panel magazynu - Inertia"""
    # Tryb produkcja - ograniczony dostęp (tylko wydanie/zwrot)
    tryb_produkcja = request.GET.get('tryb') == 'produkcja'

    data = {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
        'trybProdukcja': tryb_produkcja,
    }

    # Auto-wylogowanie dla grup produkcyjnych
    if request.user.groups.filter(name__in=['produkcja', 'produkcja-magazyn']).exists():
        data['autoLogoutMinutes'] = getattr(settings, 'AUTO_LOGOUT_IDLE_MINUTES', 5)

    return render(request, 'Magazyn', data)


@login_required
def zakupy_view(request):
    """Panel zakupów - Inertia"""
    return render(request, 'Zakupy', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def zamowienia_view(request):
    """Panel zamówień - Inertia"""
    return render(request, 'Zamowienia', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def ustawienia_view(request):
    """Panel ustawień - Inertia"""
    return render(request, 'Ustawienia', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def generator_view(request):
    """Generator zamówień - Inertia"""
    return render(request, 'Generator', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def realizacja_view(request):
    """Realizacja zamówień - Inertia"""
    return render(request, 'Realizacja', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def faktury_view(request):
    """Faktury - Inertia"""
    return render(request, 'Faktury', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def zwroty_view(request):
    """Zwroty - Inertia"""
    return render(request, 'Zwroty', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def zapotrzebowania_view(request):
    """Zapotrzebowania technologów - Inertia"""
    return render(request, 'Zapotrzebowania', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def produkcja_view(request):
    """Produkcja - Inertia (tylko podgląd)"""
    data = {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    }

    # Auto-wylogowanie dla grup produkcyjnych
    if request.user.groups.filter(name__in=['produkcja', 'produkcja-magazyn']).exists():
        data['autoLogoutMinutes'] = getattr(settings, 'AUTO_LOGOUT_IDLE_MINUTES', 5)

    return render(request, 'Produkcja', data)


@login_required
def kierownik_view(request):
    """Kierownik - Inertia (podgląd stanów magazynowych)"""
    return render(request, 'Kierownik', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
        'pageSize': getattr(settings, 'TECHNOLOG_PAGE_SIZE', 50),
    })


@login_required
def technologia_view(request):
    """Technologia - Inertia (tylko podgląd)"""
    return render(request, 'Technolog', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
        'pageSize': getattr(settings, 'TECHNOLOG_PAGE_SIZE', 50),
    })


@login_required
def logi_view(request):
    """Logi systemowe - Inertia (tylko dla administratorów)"""
    # Sprawdź czy użytkownik jest administratorem
    if not request.user.groups.filter(name='administrator').exists():
        return redirect('magazyn')

    return render(request, 'Logi', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


# ===== Logowanie/Wylogowanie =====

@ensure_csrf_cookie
def login_view(request):
    """Strona logowania"""
    if request.user.is_authenticated:
        redirect_url = get_redirect_url_for_user(request.user)
        return redirect(redirect_url)

    return render(request, 'Login')


@require_http_methods(["POST"])
def login_submit(request):
    """Obsługa POST logowania"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except:
        username = request.POST.get('username')
        password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        # Loguj sukces
        app_logger.success(get_user_display_name(user), f"Zalogowano do systemu (login: {username})")
        # Przekieruj na podstawie grupy użytkownika
        redirect_url = get_redirect_url_for_user(user)
        return redirect(redirect_url)
    else:
        # Loguj nieudaną próbę
        app_logger.warning('-', f"Nieudana próba logowania (login: {username})")
        return render(request, 'Login', props={
            'errors': {
                'error': 'Nieprawidłowa nazwa użytkownika lub hasło'
            }
        })


@ensure_csrf_cookie
def logout_view(request):
    """Wylogowanie"""
    # Loguj przed wylogowaniem (żeby mieć dostęp do usera)
    user_name = get_user_display_name(request.user)
    app_logger.info(user_name, "Wylogowano z systemu")

    auth_logout(request)
    response = redirect('login')
    response.delete_cookie('csrftoken')
    return response


@require_http_methods(["POST"])
def login_by_card(request):
    """Logowanie kartą zbliżeniową"""
    try:
        data = json.loads(request.body)
        card_number = data.get('card_number', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Nieprawidłowy format danych'}, status=400)

    # Walidacja: 10 cyfr
    if not card_number.isdigit() or len(card_number) != 10:
        return JsonResponse({'error': 'Nieprawidłowy format karty'}, status=400)

    # Szukaj pracownika z tą kartą
    try:
        pracownik = Pracownik.objects.select_related('user').get(karta=card_number)
    except Pracownik.DoesNotExist:
        app_logger.warning('-', f"Nieudane logowanie kartą - karta niezarejestrowana ({card_number})")
        return JsonResponse({'error': 'Karta nie jest zarejestrowana w systemie'}, status=404)

    # Sprawdź czy ma powiązane konto użytkownika
    if not pracownik.user:
        app_logger.warning('-', f"Nieudane logowanie kartą - brak konta ({pracownik.nazwisko} {pracownik.imie})")
        return JsonResponse({
            'error': f'Pracownik {pracownik.nazwisko} {pracownik.imie} nie ma przypisanego konta'
        }, status=403)

    # Sprawdź czy konto jest aktywne
    if not pracownik.user.is_active:
        app_logger.warning('-', f"Nieudane logowanie kartą - konto nieaktywne ({pracownik.nazwisko} {pracownik.imie})")
        return JsonResponse({'error': 'Konto użytkownika jest nieaktywne'}, status=403)

    # Zaloguj użytkownika
    login(request, pracownik.user)
    user_name = f"{pracownik.imie} {pracownik.nazwisko}"
    app_logger.success(user_name, f"Zalogowano kartą zbliżeniową")
    redirect_url = '/' + get_redirect_url_for_user(pracownik.user) + '/'

    return JsonResponse({
        'success': True,
        'redirect': redirect_url,
        'user': {
            'username': pracownik.user.username,
            'first_name': pracownik.imie,
            'last_name': pracownik.nazwisko
        }
    })

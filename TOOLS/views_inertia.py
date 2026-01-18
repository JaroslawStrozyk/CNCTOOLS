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


def get_info_program():
    """Pobiera informacje o programie z settings"""
    if hasattr(settings, 'INFO_PROGRAM') and settings.INFO_PROGRAM:
        return settings.INFO_PROGRAM[0]
    return {}


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
        'produkcja': '/produkcja/',
        'technologia': '/technologia/',
        'logout': '/logout/',
    }


def get_redirect_url_for_user(user):
    """Zwraca URL przekierowania na podstawie grupy użytkownika"""
    if user.groups.filter(name='logistyka').exists():
        return 'zakupy'
    elif user.groups.filter(name='produkcja').exists():
        return 'produkcja'
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
    return {
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'first_name': request.user.first_name or request.user.username,
            'last_name': request.user.last_name or '',
            'email': request.user.email,
        },
        'isLogistyka': is_logistyka,
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
    return render(request, 'Magazyn', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


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
def produkcja_view(request):
    """Produkcja - Inertia (tylko podgląd)"""
    return render(request, 'Produkcja', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
    })


@login_required
def technologia_view(request):
    """Technologia - Inertia (tylko podgląd)"""
    return render(request, 'Technologia', {
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
        # Przekieruj na podstawie grupy użytkownika
        redirect_url = get_redirect_url_for_user(user)
        return redirect(redirect_url)
    else:
        return render(request, 'Login', props={
            'errors': {
                'error': 'Nieprawidłowa nazwa użytkownika lub hasło'
            }
        })


@ensure_csrf_cookie
def logout_view(request):
    """Wylogowanie"""
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
        return JsonResponse({'error': 'Karta nie jest zarejestrowana w systemie'}, status=404)

    # Sprawdź czy ma powiązane konto użytkownika
    if not pracownik.user:
        return JsonResponse({
            'error': f'Pracownik {pracownik.nazwisko} {pracownik.imie} nie ma przypisanego konta'
        }, status=403)

    # Sprawdź czy konto jest aktywne
    if not pracownik.user.is_active:
        return JsonResponse({'error': 'Konto użytkownika jest nieaktywne'}, status=403)

    # Zaloguj użytkownika
    login(request, pracownik.user)
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

import json
from collections import defaultdict
from inertia import render
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.db import transaction
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Pracownik, HistoriaUzyciaNarzedzia, Uszkodzenie
from .logging_service import app_logger, get_user_display_name


# ============================================================================
# Role produkcyjne — mapowanie stanowisk na poziom uprawnień
# ----------------------------------------------------------------------------
# "produkcja"          → tylko podgląd /produkcja/, brak dostępu do magazynu
# "produkcja-magazyn"  → podgląd + przycisk "Narzędzia" (magazyn w trybie produkcja)
#
# Nowe stanowiska (sesja 2026-05-13): brygadzista/tokarz mają poziom
# 'produkcja-magazyn', frezer/ślusarz — 'produkcja'. Stara grupa 'produkcja-magazyn'
# znika po data migration 0049.
# ============================================================================
PRODUKCJA_GROUPS = {'produkcja', 'frezer', 'ślusarz'}
PRODUKCJA_MAGAZYN_GROUPS = {'brygadzista', 'tokarz'}

# Grupy stanowiskowe, które filtrują listę narzędzi do Kategoria.grupa_stanowiska.
# Brygadzista i produkcja widzą wszystko — tylko poniższe trzy ograniczają zakres.
GRUPY_FILTRUJACE_NARZEDZIA = {'tokarz', 'frezer', 'ślusarz'}


def has_produkcja_perms(user):
    """User ma poziom uprawnień 'produkcja' (podgląd /produkcja/, auto-logout)."""
    return user.groups.filter(name__in=PRODUKCJA_GROUPS).exists()


def has_produkcja_magazyn_perms(user):
    """User ma poziom 'produkcja-magazyn' (podgląd + magazyn w trybie produkcja)."""
    return user.groups.filter(name__in=PRODUKCJA_MAGAZYN_GROUPS).exists()


def get_user_grupa_stanowiska(user):
    """Zwraca nazwę grupy stanowiska usera ('tokarz'/'frezer'/'ślusarz') lub None.

    Używane do filtrowania queryset narzędzi: tylko te 3 grupy widzą zawężoną
    listę narzędzi (po Kategoria.grupa_stanowiska). Pozostałe role widzą wszystko.
    """
    return (
        user.groups
        .filter(name__in=GRUPY_FILTRUJACE_NARZEDZIA)
        .values_list('name', flat=True)
        .first()
    )


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
        'uzycie': '/uzycie/',
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
        'pomoc_zamowienia': '/pomoc/zamowienia/',
        'pomoc_magazyn': '/pomoc/magazyn/',
        'pomoc_zakupy': '/pomoc/zakupy/',
    }


def get_redirect_url_for_user(user):
    """Zwraca URL przekierowania na podstawie grupy użytkownika"""
    if user.groups.filter(name='logistyka').exists():
        return 'zakupy'
    elif has_produkcja_magazyn_perms(user) or has_produkcja_perms(user):
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
    is_magazyn = request.user.groups.filter(name='magazyn').exists()
    # isProdukcjaMagazyn = poziom uprawnień (nie literalna nazwa grupy) — pokrywa
    # nowe stanowiska brygadzista/tokarz oraz legacy produkcja-magazyn.
    is_produkcja_magazyn = has_produkcja_magazyn_perms(request.user)
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
        'isMagazyn': is_magazyn,
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
    if has_produkcja_perms(request.user) or has_produkcja_magazyn_perms(request.user):
        data['autoLogoutMinutes'] = getattr(settings, 'AUTO_LOGOUT_IDLE_MINUTES', 5)

    return render(request, 'Magazyn', data)


@login_required
def uzycie_view(request):
    """Narzędzia aktualnie w użyciu - Inertia.

    Zakładka wyniesiona z Magazyn.vue na osobną stronę (odciąża panel magazynu).
    Powrót kieruje na /magazyn/ — w trybie produkcja z zachowaniem ?tryb=produkcja.
    """
    tryb_produkcja = request.GET.get('tryb') == 'produkcja'

    data = {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
        'trybProdukcja': tryb_produkcja,
    }

    # Auto-wylogowanie dla grup produkcyjnych
    if has_produkcja_perms(request.user) or has_produkcja_magazyn_perms(request.user):
        data['autoLogoutMinutes'] = getattr(settings, 'AUTO_LOGOUT_IDLE_MINUTES', 5)

    return render(request, 'Uzycie', data)


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
    can_generate = (
        request.user.is_superuser
        or request.user.groups.filter(name__in=['logistyka', 'administrator']).exists()
    )

    return render(request, 'Zamowienia', {
        'auth': get_auth_data(request),
        'urls': get_common_urls(),
        'infoProgram': get_info_program(),
        'canGenerateOrders': can_generate,
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
    if has_produkcja_perms(request.user) or has_produkcja_magazyn_perms(request.user):
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

    # Szukaj aktywnego pracownika z tą kartą (nieaktywni i bez konta zwalniają kartę do reuse)
    try:
        pracownik = Pracownik.objects.select_related('user').get(
            karta=card_number, user__isnull=False, user__is_active=True
        )
    except Pracownik.DoesNotExist:
        app_logger.warning('-', f"Nieudane logowanie kartą - karta niezarejestrowana ({card_number})")
        return JsonResponse({'error': 'Karta nie jest zarejestrowana w systemie'}, status=404)
    except Pracownik.MultipleObjectsReturned:
        app_logger.error('-', f"Konflikt kart - karta '{card_number}' przypisana do wielu aktywnych kont")
        return JsonResponse(
            {'error': 'Konflikt konfiguracji: karta przypisana do wielu aktywnych kont. Skontaktuj się z administratorem.'},
            status=500,
        )

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


def _scal_duplikaty_pracownikow(execute=False):
    """Idempotentne scalanie duplikatów Pracownik (po nazwisko+imie).

    Strategia:
      - Grupuje Pracowników po (nazwisko, imie) gdzie oba pola są niepuste
      - W grupach z >1 elementem wybiera 'real' (z user_id; jeśli ambiwalentne, min(id))
      - Migruje FK z duplikatów (HistoriaUzyciaNarzedzia.pracownik / pracownik_zwracajacy,
        Uszkodzenie.pracownik) do reala
      - Usuwa duplikaty bez user_id

    Args:
        execute: gdy False — tylko raport (dry-run). True — wykonuje zmiany w transakcji.

    Returns:
        dict z polami: dry_run, grupy, naprawione_imie_nazwisko, polaczenia, usunieci, bledy
    """
    raport = {
        'dry_run': not execute,
        'naprawione_imie_nazwisko': [],
        'grupy': [],
        'polaczenia': [],
        'usunieci': [],
        'bledy': [],
    }

    def _wykonaj():
        # Krok 1: uzupełnij imie/nazwisko z User dla rekordów z pustymi polami
        for p in Pracownik.objects.filter(user__isnull=False).select_related('user'):
            zmieniono = False
            if not p.nazwisko and p.user.last_name:
                p.nazwisko = p.user.last_name
                zmieniono = True
            if not p.imie and p.user.first_name:
                p.imie = p.user.first_name
                zmieniono = True
            if zmieniono:
                raport['naprawione_imie_nazwisko'].append({
                    'id': p.id, 'user': p.user.username,
                    'nazwisko': p.nazwisko, 'imie': p.imie,
                })
                if execute:
                    p.save()

        # Krok 2: grupowanie po (nazwisko, imie) — tylko niepuste
        grupy = defaultdict(list)
        for p in Pracownik.objects.exclude(nazwisko='').exclude(imie='').order_by('id'):
            grupy[(p.nazwisko.strip().lower(), p.imie.strip().lower())].append(p)

        # Krok 3: dla każdej grupy z >1 → wybierz reala, zmigruj FK, skasuj duplikaty
        for klucz, pracownicy in grupy.items():
            if len(pracownicy) < 2:
                continue

            z_user = [p for p in pracownicy if p.user_id]
            if len(z_user) == 1:
                real = z_user[0]
            elif len(z_user) > 1:
                raport['bledy'].append({
                    'grupa': f'{pracownicy[0].nazwisko} {pracownicy[0].imie}',
                    'powod': f'wielu pracowników z user_id ({[p.id for p in z_user]}) - pominięto',
                })
                continue
            else:
                real = pracownicy[0]  # min(id)

            duplikaty = [p for p in pracownicy if p.id != real.id]
            opis_grupy = {
                'nazwisko': real.nazwisko, 'imie': real.imie,
                'real_id': real.id, 'real_user': real.user.username if real.user else None,
                'duplikaty_ids': [p.id for p in duplikaty],
            }
            raport['grupy'].append(opis_grupy)

            for dup in duplikaty:
                hist_pob = HistoriaUzyciaNarzedzia.objects.filter(pracownik_id=dup.id)
                hist_zwr = HistoriaUzyciaNarzedzia.objects.filter(pracownik_zwracajacy_id=dup.id)
                uszk = Uszkodzenie.objects.filter(pracownik_id=dup.id)

                liczby = {
                    'duplikat_id': dup.id, 'real_id': real.id,
                    'historia_pobran': hist_pob.count(),
                    'historia_zwrotow': hist_zwr.count(),
                    'uszkodzenia': uszk.count(),
                }
                raport['polaczenia'].append(liczby)

                if execute:
                    hist_pob.update(pracownik_id=real.id)
                    hist_zwr.update(pracownik_zwracajacy_id=real.id)
                    uszk.update(pracownik_id=real.id)

                if not dup.user_id:
                    raport['usunieci'].append({'id': dup.id, 'karta': dup.karta})
                    if execute:
                        dup.delete()
                else:
                    raport['bledy'].append({
                        'grupa': opis_grupy['nazwisko'] + ' ' + opis_grupy['imie'],
                        'powod': f'duplikat id={dup.id} ma user_id={dup.user_id} - nie usunięto',
                    })

    if execute:
        with transaction.atomic():
            _wykonaj()
    else:
        _wykonaj()

    return raport


@login_required
def magazyn_update_view(request):
    """Jednorazowy skrypt naprawczy bazy danych — deduplikacja pracowników.

    GET /magazyn/update          — dry-run (raport bez zmian)
    GET /magazyn/update?execute=1 — wykonuje migrację

    Wymaga uprawnień superuser.
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Wymagane uprawnienia superuser'}, status=403)

    execute = request.GET.get('execute') == '1'
    try:
        raport = _scal_duplikaty_pracownikow(execute=execute)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    if execute:
        opis = (f"Scalono {len(raport['polaczenia'])} duplikatów, "
                f"usunięto {len(raport['usunieci'])}, "
                f"uzupełniono imie/nazwisko: {len(raport['naprawione_imie_nazwisko'])}")
        app_logger.success(get_user_display_name(request.user),
                           f"Skrypt /magazyn/update: {opis}")

    return JsonResponse(raport, json_dumps_params={'indent': 2, 'ensure_ascii': False})

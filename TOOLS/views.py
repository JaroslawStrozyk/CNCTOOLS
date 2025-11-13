# tools/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime

from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji
)
from .serializers import (
    KategoriaSerializer, PodkategoriaSerializer, NarzedzieMagazynoweSerializer,
    EgzemplarzNarzedziaSerializer, LokalizacjaSerializer, MaszynaSerializer,
    HistoriaUzyciaNarzedziaSerializer, FakturaZakupuSerializer,
    DostawcaSerializer, PracownikSerializer, UszkodzenieSerializer,
    ZamowienieSerializer, PozycjaZamowieniaSerializer,
    RealizacjaZamowieniaSerializer, PozycjaRealizacjiSerializer
)
from .services import EgzemplarzService, LokalizacjaService


# ========== WIDOKI HTML ==========

def index_view(request):
    """Strona główna - przekierowanie"""
    if request.user.is_authenticated:
        return redirect('magazyn')
    return redirect('login')


def login_view(request):
    """Panel logowania"""
    if request.user.is_authenticated:
        return redirect('magazyn')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'magazyn')
                return redirect(next_url)
        messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Wylogowanie"""
    logout(request)
    return redirect('login')


@login_required
def magazyn_view(request):
    return render(request, 'magazyn.html')


@login_required
def zakupy_view(request):
    return render(request, 'zakupy.html')


@login_required
def faktury_view(request):
    return render(request, 'faktury.html')


@login_required
def ustawienia_view(request):
    return render(request, 'ustawienia.html')


@login_required
def zamowienia_view(request):
    return render(request, 'zamowienia.html')


# ========== EMAIL API ==========

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .utils import send_test_email


@login_required
@require_http_methods(["POST"])
def test_email_view(request):
    """Endpoint do testowania wysyłki emaili"""
    result = send_test_email()
    return JsonResponse(result)


@login_required
@require_http_methods(["GET"])
def email_config_view(request):
    """Endpoint zwracający konfigurację email (bez hasła)"""
    from django.conf import settings

    config = {
        'email_host': getattr(settings, 'EMAIL_HOST', ''),
        'email_port': getattr(settings, 'EMAIL_PORT', ''),
        'email_use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', ''),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        'email_test_address': getattr(settings, 'EMAIL_TEST_ADDRESS', ''),
        'email_configured': bool(getattr(settings, 'EMAIL_HOST_USER', '')),
    }

    return JsonResponse(config)


# ========== API VIEWSETS ==========

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class KategoriaViewSet(viewsets.ModelViewSet):
    queryset = Kategoria.objects.prefetch_related('podkategorie').all()
    serializer_class = KategoriaSerializer


class PodkategoriaViewSet(viewsets.ModelViewSet):
    queryset = Podkategoria.objects.select_related('kategoria').all()
    serializer_class = PodkategoriaSerializer


class DostawcaViewSet(viewsets.ModelViewSet):
    queryset = Dostawca.objects.all()
    serializer_class = DostawcaSerializer


class LokalizacjaViewSet(viewsets.ModelViewSet):
    queryset = Lokalizacja.objects.all()
    serializer_class = LokalizacjaSerializer

    @action(detail=False, methods=['post'])
    def dodaj_seryjnie(self, request):
        """Dodaje lokalizacje seryjnie używając serwisu"""
        from django.core.exceptions import ValidationError

        szafa = request.data.get('szafa')
        liczba_kolumn = request.data.get('liczba_kolumn', 1)
        liczba_polek = request.data.get('liczba_polek', 1)

        try:
            liczba_utworzonych = LokalizacjaService.utworz_lokalizacje_seryjnie(
                szafa=szafa,
                liczba_kolumn=liczba_kolumn,
                liczba_polek=liczba_polek
            )
            return Response(
                {'message': f'Dodano {liczba_utworzonych} lokalizacji dla szafy {szafa}.'},
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MaszynaViewSet(viewsets.ModelViewSet):
    queryset = Maszyna.objects.all()
    serializer_class = MaszynaSerializer


class PracownikViewSet(viewsets.ModelViewSet):
    queryset = Pracownik.objects.all()
    serializer_class = PracownikSerializer
    pagination_class = StandardResultsSetPagination


class FakturaZakupuViewSet(viewsets.ModelViewSet):
    queryset = FakturaZakupu.objects.select_related('dostawca').all()
    serializer_class = FakturaZakupuSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)

        if narzedzie_id:
            queryset = queryset.filter(
                egzemplarze__narzedzie_typ_id=narzedzie_id
            ).distinct()

        return queryset.order_by('-data_wystawienia')


class NarzedzieMagazynoweViewSet(viewsets.ModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer

    def get_queryset(self):
        from django.db.models import Case, When, Value, IntegerField

        queryset = NarzedzieMagazynowe.objects.select_related(
            'podkategoria__kategoria',
            'ostatni_dostawca',
            'domyslna_lokalizacja'
        ).prefetch_related('egzemplarze').annotate(
            ilosc_nowych=Sum(
                Case(
                    When(egzemplarze__stan='nowe', then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            ilosc_uzywanych_dostepnych=Sum(
                Case(
                    When(
                        Q(egzemplarze__stan='uzywane') &
                        (Q(egzemplarze__historia__data_zwrotu__isnull=False) | Q(egzemplarze__historia__isnull=True)),
                        then='egzemplarze__ilosc_w_komplecie'
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            ilosc_w_uzyciu=Sum(
                Case(
                    When(egzemplarze__historia__data_zwrotu__isnull=True, then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            calkowita_ilosc=Sum(
                Case(
                    When(~Q(egzemplarze__stan__in=['uszkodzone', 'uszkodzone_regeneracja']), then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class NarzedzieMagazynoweZakupyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NarzedzieMagazynoweSerializer

    def get_queryset(self):
        from django.db.models import Case, When, Value, IntegerField

        queryset = NarzedzieMagazynowe.objects.select_related(
            'podkategoria__kategoria',
            'ostatni_dostawca',
            'domyslna_lokalizacja'
        ).prefetch_related('egzemplarze').annotate(
            ilosc_nowych=Sum(
                Case(
                    When(egzemplarze__stan='nowe', then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            ilosc_uzywanych_dostepnych=Sum(
                Case(
                    When(
                        Q(egzemplarze__stan='uzywane') &
                        (Q(egzemplarze__historia__data_zwrotu__isnull=False) | Q(egzemplarze__historia__isnull=True)),
                        then='egzemplarze__ilosc_w_komplecie'
                    ),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            ilosc_w_uzyciu=Sum(
                Case(
                    When(egzemplarze__historia__data_zwrotu__isnull=True, then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),
            calkowita_ilosc=Sum(
                Case(
                    When(~Q(egzemplarze__stan__in=['uszkodzone', 'uszkodzone_regeneracja']), then='egzemplarze__ilosc_w_komplecie'),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
        return queryset.order_by('podkategoria__kategoria__nazwa', 'podkategoria__nazwa', 'opis')


class EgzemplarzNarzedziaViewSet(viewsets.ModelViewSet):
    queryset = EgzemplarzNarzedzia.objects.select_related(
        'narzedzie_typ__podkategoria__kategoria',
        'lokalizacja',
        'faktura_zakupu'
    ).all()
    serializer_class = EgzemplarzNarzedziaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_typ_id = self.request.query_params.get('narzedzie_typ_id', None)

        if narzedzie_typ_id:
            queryset = queryset.filter(narzedzie_typ_id=narzedzie_typ_id)

        return queryset.order_by('-data_zakupu')


class HistoriaUzyciaNarzedziaViewSet(viewsets.ModelViewSet):
    queryset = HistoriaUzyciaNarzedzia.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'maszyna',
        'pracownik'
    ).all()
    serializer_class = HistoriaUzyciaNarzedziaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        narzedzie_id = self.request.query_params.get('narzedzie_id', None)
        w_uzyciu = self.request.query_params.get('w_uzyciu', None)

        if narzedzie_id:
            queryset = queryset.filter(egzemplarz__narzedzie_typ_id=narzedzie_id)

        if w_uzyciu and w_uzyciu.lower() == 'true':
            queryset = queryset.filter(data_zwrotu__isnull=True)

        return queryset.order_by('-data_wydania')

    @action(detail=False, methods=['post'])
    def wydanie(self, request):
        """Wydaje narzędzie pracownikowi używając serwisu"""
        from django.core.exceptions import ValidationError

        egzemplarz_id = request.data.get('egzemplarz_id')
        maszyna_id = request.data.get('maszyna_id')
        pracownik_id = request.data.get('pracownik_id')

        try:
            historia = EgzemplarzService.wydaj_egzemplarz(
                egzemplarz_id=egzemplarz_id,
                maszyna_id=maszyna_id,
                pracownik_id=pracownik_id
            )
            serializer = self.get_serializer(historia)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def zwrot(self, request, pk=None):
        """Zwraca narzędzie używając serwisu"""
        from django.core.exceptions import ValidationError

        historia = self.get_object()
        stan_po_zwrocie = request.data.get('stan_po_zwrocie', 'uzywane')

        try:
            historia = EgzemplarzService.zwroc_egzemplarz(
                historia_id=historia.id,
                stan_po_zwrocie=stan_po_zwrocie
            )

            # Jeśli uszkodzone lub uszkodzone_regeneracja, utwórz wpis w tabeli uszkodzeń
            if stan_po_zwrocie in ['uszkodzone', 'uszkodzone_regeneracja']:
                opis_domyslny = 'Uszkodzenie podczas użycia' if stan_po_zwrocie == 'uszkodzone' else 'Uszkodzenie do regeneracji'
                Uszkodzenie.objects.create(
                    egzemplarz=historia.egzemplarz,
                    opis_uszkodzenia=request.data.get('uwagi', opis_domyslny),
                    pracownik=historia.pracownik
                )

            serializer = self.get_serializer(historia)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UszkodzenieViewSet(viewsets.ModelViewSet):
    queryset = Uszkodzenie.objects.select_related(
        'egzemplarz__narzedzie_typ__podkategoria__kategoria',
        'pracownik'
    ).all()
    serializer_class = UszkodzenieSerializer

    def get_queryset(self):
        return super().get_queryset().order_by('-data_uszkodzenia')


class ZamowienieViewSet(viewsets.ModelViewSet):
    queryset = Zamowienie.objects.select_related('dostawca').prefetch_related('pozycje').all()
    serializer_class = ZamowienieSerializer

    @action(detail=False, methods=['post'])
    def generuj_automatyczne(self, request):
        """Generuje zamówienia dla narzędzi poniżej limitu"""
        pass

    @action(detail=True, methods=['post'])
    def wyslij_email(self, request, pk=None):
        """Wysyła zamówienie mailem do dostawcy"""
        pass

    @action(detail=True, methods=['post'])
    def rozpocznij_realizacje(self, request, pk=None):
        """Tworzy realizację do zaznaczania przychodzących pozycji"""
        pass


class PozycjaZamowieniaViewSet(viewsets.ModelViewSet):
    queryset = PozycjaZamowienia.objects.select_related(
        'zamowienie',
        'narzedzie_typ__podkategoria__kategoria'
    ).all()
    serializer_class = PozycjaZamowieniaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        zamowienie_id = self.request.query_params.get('zamowienie_id', None)
        if zamowienie_id:
            queryset = queryset.filter(zamowienie_id=zamowienie_id)
        return queryset


class RealizacjaZamowieniaViewSet(viewsets.ModelViewSet):
    queryset = RealizacjaZamowienia.objects.select_related(
        'zamowienie__dostawca',
        'lokalizacja_domyslna'
    ).prefetch_related('pozycje').all()
    serializer_class = RealizacjaZamowieniaSerializer

    @action(detail=True, methods=['post'])
    def zatwierdz(self, request, pk=None):
        """Tworzy egzemplarze, loguje, aktualizuje status"""
        pass


class PozycjaRealizacjiViewSet(viewsets.ModelViewSet):
    queryset = PozycjaRealizacji.objects.select_related(
        'realizacja',
        'pozycja_zamowienia__narzedzie_typ',
        'lokalizacja'
    ).all()
    serializer_class = PozycjaRealizacjiSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        realizacja_id = self.request.query_params.get('realizacja_id', None)
        if realizacja_id:
            queryset = queryset.filter(realizacja_id=realizacja_id)
        return queryset




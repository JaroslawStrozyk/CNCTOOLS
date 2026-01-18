# tools/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_inertia import (
    login_view as login_inertia_view,
    login_submit,
    login_by_card,
    logout_view as logout_inertia_view,
    magazyn_view as magazyn_inertia_view,
    zakupy_view as zakupy_inertia_view,
    zamowienia_view as zamowienia_inertia_view,
    ustawienia_view as ustawienia_inertia_view,
    generator_view as generator_inertia_view,
    realizacja_view as realizacja_inertia_view,
    faktury_view as faktury_inertia_view,
    zwroty_view as zwroty_inertia_view,
    produkcja_view as produkcja_inertia_view,
    technologia_view as technologia_inertia_view,
)

router = DefaultRouter()

# Podstawowe endpointy
router.register(r'kategorie', views.KategoriaViewSet, basename='kategoria')
router.register(r'podkategorie', views.PodkategoriaViewSet, basename='podkategoria')
router.register(r'dostawcy', views.DostawcaViewSet, basename='dostawca')
router.register(r'lokalizacje', views.LokalizacjaViewSet, basename='lokalizacja')
router.register(r'maszyny', views.MaszynaViewSet, basename='maszyna')
router.register(r'pracownicy', views.PracownikViewSet, basename='pracownik')
router.register(r'faktury', views.FakturaZakupuViewSet, basename='faktura')

# Narzędzia magazynowe
router.register(r'narzedzia', views.NarzedzieMagazynoweViewSet, basename='narzedzie')
router.register(r'narzedzia-zakupy', views.NarzedzieMagazynoweZakupyViewSet, basename='narzedzie-zakupy')
router.register(r'egzemplarze', views.EgzemplarzNarzedziaViewSet, basename='egzemplarz')
router.register(r'historia', views.HistoriaUzyciaNarzedziaViewSet, basename='historia')
router.register(r'uszkodzenia', views.UszkodzenieViewSet, basename='uszkodzenie')

# Zamówienia
router.register(r'zamowienia', views.ZamowienieViewSet, basename='zamowienie')
router.register(r'pozycje-zamowien', views.PozycjaZamowieniaViewSet, basename='pozycja-zamowienia')
router.register(r'realizacje', views.RealizacjaZamowieniaViewSet, basename='realizacja')
router.register(r'pozycje-realizacji', views.PozycjaRealizacjiViewSet, basename='pozycja-realizacji')

urlpatterns = [
    # ===== NOWY SYSTEM INERTIA (Vue SPA) =====
    path('', login_inertia_view, name='login'),
    path('login/', login_submit, name='login-submit'),
    path('api/login-card/', login_by_card, name='login-card'),
    path('logout/', logout_inertia_view, name='logout'),
    path('magazyn/', magazyn_inertia_view, name='magazyn'),
    path('zakupy/', zakupy_inertia_view, name='zakupy'),
    path('zamowienia/', zamowienia_inertia_view, name='zamowienia'),
    path('ustawienia/', ustawienia_inertia_view, name='ustawienia'),
    path('generator/', generator_inertia_view, name='generator'),
    path('realizacja/', realizacja_inertia_view, name='realizacja'),
    path('faktury/', faktury_inertia_view, name='faktury'),
    path('zwroty/', zwroty_inertia_view, name='zwroty'),
    path('produkcja/', produkcja_inertia_view, name='produkcja'),
    path('technologia/', technologia_inertia_view, name='technologia'),

    # ===== STARY SYSTEM (backup - do usunięcia po pełnej migracji) =====
    path('old/', views.login_view, name='login-old'),
    path('old/magazyn/', views.magazyn_view, name='magazyn-old'),
    path('old/zakupy/', views.zakupy_view, name='zakupy-old'),
    path('old/zamowienia/', views.zamowienia_view, name='zamowienia-old'),
    path('old/ustawienia/', views.ustawienia_view, name='ustawienia-old'),
    path('old/generator/', views.generator_view, name='generator-old'),
    path('old/realizacja/', views.realizacja_view, name='realizacja-old'),
    path('old/faktury/', views.faktury_view, name='faktury-old'),
    path('old/odpady/', views.odpady_view, name='odpady-old'),

    # ===== API =====
    path('api/', include(router.urls)),
    path('api/generator-zamowien/', views.generator_zamowien_api, name='generator-zamowien'),
    path('api/generator-zamowien/add/', views.generator_zamowien_add_api, name='generator-zamowien-add'),
    path('api/generator-zamowien/gotowe/', views.generator_zamowien_gotowe_api, name='generator-zamowien-gotowe'),
    path('api/generator-zamowien/<int:narzedzie_id>/update/', views.generator_zamowien_update_api,
         name='generator-zamowien-update'),
    path('api/generator-zamowien/<int:narzedzie_id>/delete/', views.generator_zamowien_delete_api,
         name='generator-zamowien-delete'),

    # Email endpoints
    path('api/email/test/', views.test_email_view, name='test_email'),
    path('api/email/config/', views.email_config_view, name='email_config'),
    path('api/zamowienia/<int:zamowienie_id>/wyslij-email/', views.wyslij_email_zamowienie_api,
         name='zamowienia-wyslij-email'),
]
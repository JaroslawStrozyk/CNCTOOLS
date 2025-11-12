# tools/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
    path('api/', include(router.urls)),
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('magazyn/', views.magazyn_view, name='magazyn'),
    path('zakupy/', views.zakupy_view, name='zakupy'),
    path('faktury/', views.faktury_view, name='faktury'),
    path('ustawienia/', views.ustawienia_view, name='ustawienia'),
    path('zamowienia/', views.zamowienia_view, name='zamowienia'),

    # Email endpoints
    path('api/email/test/', views.test_email_view, name='test_email'),
    path('api/email/config/', views.email_config_view, name='email_config'),
]

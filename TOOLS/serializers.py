# tools/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji,
    ZapotrzebowanieTechnologa, PozycjaZapotrzebowania
)


class UserSimpleSerializer(serializers.ModelSerializer):
    """Prosty serializer dla User do wyświetlania w dropdown"""
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']

    def get_display_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name} ({obj.username})"
        return obj.username


class KategoriaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategoria
        fields = ['id', 'nazwa']


class PodkategoriaSerializer(serializers.ModelSerializer):
    kategoria_nazwa = serializers.CharField(source='kategoria.nazwa', read_only=True)
    kategoria = KategoriaSimpleSerializer(read_only=True)
    kategoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Kategoria.objects.all(),
        source='kategoria',
        write_only=True
    )

    class Meta:
        model = Podkategoria
        fields = ['id', 'nazwa', 'kategoria', 'kategoria_id', 'kategoria_nazwa']


class KategoriaSerializer(serializers.ModelSerializer):
    podkategorie = PodkategoriaSerializer(many=True, read_only=True)

    class Meta:
        model = Kategoria
        fields = ['id', 'nazwa', 'podkategorie']


class DostawcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dostawca
        fields = '__all__'


class LokalizacjaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lokalizacja
        fields = '__all__'


class MaszynaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maszyna
        fields = '__all__'


class PracownikSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Pracownik
        fields = ['id', 'karta', 'nazwisko', 'imie', 'user', 'user_id', 'pobieranie_narzedzi']


class FakturaZakupuSerializer(serializers.ModelSerializer):
    dostawca = DostawcaSerializer(read_only=True)
    dostawca_id = serializers.PrimaryKeyRelatedField(
        queryset=Dostawca.objects.all(),
        source='dostawca',
        write_only=True
    )

    class Meta:
        model = FakturaZakupu
        fields = '__all__'


class NarzedzieMagazynoweSerializer(serializers.ModelSerializer):
    podkategoria = PodkategoriaSerializer(read_only=True)
    kategoria_nazwa = serializers.CharField(source='podkategoria.kategoria.nazwa', read_only=True)
    podkategoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Podkategoria.objects.all(),
        source='podkategoria',
        write_only=True,
        required=False,
        allow_null=True
    )
    ostatni_dostawca = DostawcaSerializer(read_only=True)
    ostatni_dostawca_id = serializers.PrimaryKeyRelatedField(
        queryset=Dostawca.objects.all(),
        source='ostatni_dostawca',
        write_only=True,
        required=False,
        allow_null=True
    )
    domyslna_lokalizacja = LokalizacjaSerializer(read_only=True)
    domyslna_lokalizacja_id = serializers.PrimaryKeyRelatedField(
        queryset=Lokalizacja.objects.all(),
        source='domyslna_lokalizacja',
        write_only=True,
        required=False,
        allow_null=True
    )
    ilosc_nowych = serializers.IntegerField(read_only=True)
    ilosc_uzywanych_dostepnych = serializers.IntegerField(read_only=True)
    ilosc_w_uzyciu = serializers.IntegerField(read_only=True)
    calkowita_ilosc = serializers.IntegerField(read_only=True)

    class Meta:
        model = NarzedzieMagazynowe
        fields = '__all__'


class EgzemplarzNarzedziaSerializer(serializers.ModelSerializer):
    narzedzie_typ = NarzedzieMagazynoweSerializer(read_only=True)
    narzedzie_typ_id = serializers.PrimaryKeyRelatedField(
        queryset=NarzedzieMagazynowe.objects.all(),
        source='narzedzie_typ',
        write_only=True
    )
    lokalizacja = LokalizacjaSerializer(read_only=True)
    lokalizacja_id = serializers.PrimaryKeyRelatedField(
        queryset=Lokalizacja.objects.all(),
        source='lokalizacja',
        write_only=True,
        required=False,
        allow_null=True
    )
    faktura_zakupu = FakturaZakupuSerializer(read_only=True)
    faktura_zakupu_id = serializers.PrimaryKeyRelatedField(
        queryset=FakturaZakupu.objects.all(),
        source='faktura_zakupu',
        write_only=True,
        required=False,
        allow_null=True
    )
    zamowienie_id = serializers.PrimaryKeyRelatedField(
        queryset=Zamowienie.objects.all(),
        source='zamowienie',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = EgzemplarzNarzedzia
        fields = '__all__'

    def create(self, validated_data):
        # Pobierz typ narzędzia
        narzedzie_typ = validated_data.get('narzedzie_typ')

        # Jeśli nie podano jednostki i ilosc_w_komplecie, użyj wartości z typu narzędzia
        # Pozwala to na dodawanie "luźnych sztuk" dla narzędzi typu komplet
        if narzedzie_typ:
            if 'jednostka' not in validated_data:
                validated_data['jednostka'] = narzedzie_typ.opakowanie
            if 'ilosc_w_komplecie' not in validated_data:
                validated_data['ilosc_w_komplecie'] = narzedzie_typ.ilosc_w_opakowaniu

        return super().create(validated_data)


class HistoriaUzyciaNarzedziaSerializer(serializers.ModelSerializer):
    egzemplarz = EgzemplarzNarzedziaSerializer(read_only=True)
    egzemplarz_id = serializers.PrimaryKeyRelatedField(
        queryset=EgzemplarzNarzedzia.objects.all(),
        source='egzemplarz',
        write_only=True
    )
    maszyna = MaszynaSerializer(read_only=True)
    maszyna_id = serializers.PrimaryKeyRelatedField(
        queryset=Maszyna.objects.all(),
        source='maszyna',
        write_only=True,
        required=False,
        allow_null=True
    )
    pracownik = PracownikSerializer(read_only=True)
    pracownik_id = serializers.PrimaryKeyRelatedField(
        queryset=Pracownik.objects.all(),
        source='pracownik',
        write_only=True,
        required=False,
        allow_null=True
    )
    pracownik_zwracajacy = PracownikSerializer(read_only=True)
    pracownik_zwracajacy_id = serializers.PrimaryKeyRelatedField(
        queryset=Pracownik.objects.all(),
        source='pracownik_zwracajacy',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = HistoriaUzyciaNarzedzia
        fields = '__all__'


class UszkodzenieSerializer(serializers.ModelSerializer):
    egzemplarz = EgzemplarzNarzedziaSerializer(read_only=True)
    egzemplarz_id = serializers.PrimaryKeyRelatedField(
        queryset=EgzemplarzNarzedzia.objects.all(),
        source='egzemplarz',
        write_only=True
    )
    pracownik = PracownikSerializer(read_only=True)
    pracownik_id = serializers.PrimaryKeyRelatedField(
        queryset=Pracownik.objects.all(),
        source='pracownik',
        write_only=True,
        required=False,
        allow_null=True
    )

    # Dodatkowe pola dla ułatwienia wyświetlania
    kategoria_narzedzia = serializers.SerializerMethodField()
    opis_narzedzia = serializers.SerializerMethodField()
    numer_katalogowy = serializers.SerializerMethodField()
    ostatnia_lokalizacja = serializers.SerializerMethodField()
    maszyna_uszkodzenia = serializers.SerializerMethodField()
    ostatni_pracownik = serializers.SerializerMethodField()
    stan_egzemplarza = serializers.SerializerMethodField()

    class Meta:
        model = Uszkodzenie
        fields = [
            'id', 'egzemplarz', 'egzemplarz_id', 'narzedzie_typ', 'narzedzie_opis',
            'lokalizacja_opis', 'stan', 'maszyna_nazwa',
            'pracownik_nazwisko', 'pracownik_imie', 'data_uszkodzenia', 'opis_uszkodzenia',
            'pracownik', 'pracownik_id',
            # SerializerMethodFields (nadpisują pola modelu o tej samej nazwie)
            'kategoria_narzedzia', 'opis_narzedzia', 'numer_katalogowy', 'ostatnia_lokalizacja',
            'maszyna_uszkodzenia', 'ostatni_pracownik', 'stan_egzemplarza'
        ]

    def get_kategoria_narzedzia(self, obj):
        # Najpierw sprawdź pole kategoria_narzedzia (dla usuniętych)
        if obj.kategoria_narzedzia:
            return obj.kategoria_narzedzia
        # Potem sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ and obj.egzemplarz.narzedzie_typ.podkategoria:
            return f"{obj.egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa} / {obj.egzemplarz.narzedzie_typ.podkategoria.nazwa}"
        return '-'

    def get_opis_narzedzia(self, obj):
        # Najpierw sprawdź pole narzedzie_opis (dla usuniętych)
        if obj.narzedzie_opis:
            return obj.narzedzie_opis
        # Potem sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ:
            return obj.egzemplarz.narzedzie_typ.opis
        return '-'

    def get_numer_katalogowy(self, obj):
        # Najpierw sprawdź pole numer_katalogowy (dla usuniętych)
        if obj.numer_katalogowy:
            return obj.numer_katalogowy
        # Potem sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ:
            return obj.egzemplarz.narzedzie_typ.numer_katalogowy or None
        return None

    def get_ostatnia_lokalizacja(self, obj):
        # Najpierw sprawdź pole lokalizacja_opis (dla usuniętych)
        if obj.lokalizacja_opis:
            return obj.lokalizacja_opis
        # Potem sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz and obj.egzemplarz.lokalizacja:
            lok = obj.egzemplarz.lokalizacja
            return f"{lok.szafa}/{lok.polka}/{lok.kolumna}"
        return None

    def get_maszyna_uszkodzenia(self, obj):
        # Najpierw sprawdź pole maszyna_nazwa (dla usuniętych)
        if obj.maszyna_nazwa:
            return obj.maszyna_nazwa
        # Potem sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz:
            ostatnia_historia = obj.egzemplarz.historia.order_by('-data_wydania').first()
            if ostatnia_historia and ostatnia_historia.maszyna:
                return ostatnia_historia.maszyna.nazwa
        return None

    def get_ostatni_pracownik(self, obj):
        # Najpierw sprawdź pola pracownik_nazwisko/imie (dla usuniętych)
        if obj.pracownik_nazwisko or obj.pracownik_imie:
            return {
                'nazwisko': obj.pracownik_nazwisko,
                'imie': obj.pracownik_imie
            }
        # Potem sprawdź pracownika przypisanego do uszkodzenia
        if obj.pracownik:
            return PracownikSerializer(obj.pracownik).data
        # Na koniec sprawdź ostatnią historię egzemplarza
        if obj.egzemplarz:
            ostatnia_historia = obj.egzemplarz.historia.order_by('-data_wydania').first()
            if ostatnia_historia and ostatnia_historia.pracownik:
                return PracownikSerializer(ostatnia_historia.pracownik).data
        return None

    def get_stan_egzemplarza(self, obj):
        # Najpierw sprawdź czy jest stan zapisany bezpośrednio w modelu (dla usuniętych egzemplarzy)
        if obj.stan:
            return obj.stan

        # Jeśli nie, sprawdź egzemplarz (dla nieusunietych)
        if obj.egzemplarz:
            # Mapowanie stanów na czytelne nazwy
            stan_map = {
                'nowe': 'Nowe',
                'uzywane': 'Używane',
                'uszkodzone': 'Uszkodzone',
                'uszkodzone_regeneracja': 'Uszkodzone do regeneracji'
            }
            return stan_map.get(obj.egzemplarz.stan, obj.egzemplarz.stan)
        return None


class PozycjaZamowieniaSerializer(serializers.ModelSerializer):
    narzedzie_typ = NarzedzieMagazynoweSerializer(read_only=True)
    narzedzie_typ_id = serializers.PrimaryKeyRelatedField(
        queryset=NarzedzieMagazynowe.objects.all(),
        source='narzedzie_typ',
        write_only=True
    )

    class Meta:
        model = PozycjaZamowienia
        fields = '__all__'


class ZamowienieSerializer(serializers.ModelSerializer):
    dostawca = DostawcaSerializer(read_only=True)
    dostawca_id = serializers.PrimaryKeyRelatedField(
        queryset=Dostawca.objects.all(),
        source='dostawca',
        write_only=True
    )
    pozycje = PozycjaZamowieniaSerializer(many=True, read_only=True)

    class Meta:
        model = Zamowienie
        fields = '__all__'


class PozycjaRealizacjiSerializer(serializers.ModelSerializer):
    pozycja_zamowienia = PozycjaZamowieniaSerializer(read_only=True)
    pozycja_zamowienia_id = serializers.PrimaryKeyRelatedField(
        queryset=PozycjaZamowienia.objects.all(),
        source='pozycja_zamowienia',
        write_only=True
    )
    lokalizacja = LokalizacjaSerializer(read_only=True)
    lokalizacja_id = serializers.PrimaryKeyRelatedField(
        queryset=Lokalizacja.objects.all(),
        source='lokalizacja',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = PozycjaRealizacji
        fields = '__all__'


class RealizacjaZamowieniaSerializer(serializers.ModelSerializer):
    zamowienie = ZamowienieSerializer(read_only=True)
    zamowienie_id = serializers.PrimaryKeyRelatedField(
        queryset=Zamowienie.objects.all(),
        source='zamowienie',
        write_only=True
    )
    lokalizacja_domyslna = LokalizacjaSerializer(read_only=True)
    lokalizacja_domyslna_id = serializers.PrimaryKeyRelatedField(
        queryset=Lokalizacja.objects.all(),
        source='lokalizacja_domyslna',
        write_only=True,
        required=False,
        allow_null=True
    )
    pozycje = PozycjaRealizacjiSerializer(many=True, read_only=True)

    class Meta:
        model = RealizacjaZamowienia
        fields = '__all__'


class PozycjaZapotrzebowaniaSerializer(serializers.ModelSerializer):
    narzedzie_typ = NarzedzieMagazynoweSerializer(read_only=True)
    narzedzie_typ_id = serializers.PrimaryKeyRelatedField(
        queryset=NarzedzieMagazynowe.objects.all(),
        source='narzedzie_typ',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = PozycjaZapotrzebowania
        fields = '__all__'


class ZapotrzebowanieTechnologaSerializer(serializers.ModelSerializer):
    technolog = UserSimpleSerializer(read_only=True)
    zrealizowany_przez = UserSimpleSerializer(read_only=True)
    pozycje = PozycjaZapotrzebowaniaSerializer(many=True, read_only=True)
    pozycje_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ZapotrzebowanieTechnologa
        fields = '__all__'

    def get_pozycje_count(self, obj):
        return obj.pozycje.count()
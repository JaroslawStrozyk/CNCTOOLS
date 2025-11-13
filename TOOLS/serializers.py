# tools/serializers.py
from rest_framework import serializers
from .models import (
    Kategoria, Podkategoria, NarzedzieMagazynowe, EgzemplarzNarzedzia,
    Lokalizacja, Maszyna, HistoriaUzyciaNarzedzia, FakturaZakupu,
    Dostawca, Pracownik, Uszkodzenie, Zamowienie, PozycjaZamowienia,
    RealizacjaZamowienia, PozycjaRealizacji
)


class KategoriaSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategoria
        fields = ['id', 'nazwa']


class PodkategoriaSerializer(serializers.ModelSerializer):
    kategoria_nazwa = serializers.CharField(source='kategoria.nazwa', read_only=True)
    kategoria = KategoriaSimpleSerializer(read_only=True)

    class Meta:
        model = Podkategoria
        fields = ['id', 'nazwa', 'kategoria', 'kategoria_nazwa']


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
    class Meta:
        model = Pracownik
        fields = '__all__'


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

        # Automatycznie ustaw jednostka i ilosc_w_komplecie na podstawie typu narzędzia
        if narzedzie_typ:
            validated_data['jednostka'] = narzedzie_typ.opakowanie
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
        fields = '__all__'

    def get_kategoria_narzedzia(self, obj):
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ and obj.egzemplarz.narzedzie_typ.podkategoria:
            return f"{obj.egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa} / {obj.egzemplarz.narzedzie_typ.podkategoria.nazwa}"
        return '-'

    def get_opis_narzedzia(self, obj):
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ:
            return obj.egzemplarz.narzedzie_typ.opis
        return '-'

    def get_numer_katalogowy(self, obj):
        if obj.egzemplarz and obj.egzemplarz.narzedzie_typ:
            return obj.egzemplarz.narzedzie_typ.numer_katalogowy or None
        return None

    def get_ostatnia_lokalizacja(self, obj):
        if obj.egzemplarz and obj.egzemplarz.lokalizacja:
            lok = obj.egzemplarz.lokalizacja
            return f"{lok.szafa}/{lok.kolumna}/{lok.polka}"
        return None

    def get_maszyna_uszkodzenia(self, obj):
        if obj.egzemplarz:
            # Pobierz ostatnią historię użycia
            ostatnia_historia = obj.egzemplarz.historia.order_by('-data_wydania').first()
            if ostatnia_historia and ostatnia_historia.maszyna:
                return ostatnia_historia.maszyna.nazwa
        return None

    def get_ostatni_pracownik(self, obj):
        # Zwraca pracownika przypisanego do uszkodzenia (który zgłosił)
        if obj.pracownik:
            return PracownikSerializer(obj.pracownik).data
        return None

    def get_stan_egzemplarza(self, obj):
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



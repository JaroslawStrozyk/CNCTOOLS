# TOOLS/management/commands/sync_pracownicy.py
"""
Management command do synchronizacji tabeli Pracownik z auth_user.

Użycie:
    python manage.py sync_pracownicy          # synchronizacja wszystkich
    python manage.py sync_pracownicy --dry-run  # tylko podgląd zmian
    python manage.py sync_pracownicy --id 5   # tylko konkretny Pracownik
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from TOOLS.models import Pracownik


class Command(BaseCommand):
    help = 'Synchronizuje tabelę Pracownik z auth_user (tworzy User jeśli brak, synchronizuje imię/nazwisko)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tylko podgląd zmian, bez zapisywania',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Synchronizuj tylko Pracownika o podanym ID',
        )
        parser.add_argument(
            '--direction',
            choices=['to_user', 'to_pracownik', 'both'],
            default='both',
            help='Kierunek synchronizacji: to_user (Pracownik→User), to_pracownik (User→Pracownik), both (obustronna)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        pracownik_id = options['id']
        direction = options['direction']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== TRYB PODGLĄDU (--dry-run) - żadne zmiany nie zostaną zapisane ===\n'))

        # Pobierz pracowników do synchronizacji
        if pracownik_id:
            pracownicy = Pracownik.objects.filter(id=pracownik_id)
            if not pracownicy.exists():
                self.stdout.write(self.style.ERROR(f'Nie znaleziono Pracownika o ID={pracownik_id}'))
                return
        else:
            pracownicy = Pracownik.objects.all()

        stats = {
            'utworzono_user': 0,
            'zsynchronizowano': 0,
            'bez_zmian': 0,
            'bledy': 0,
        }

        for pracownik in pracownicy:
            try:
                result = self.sync_pracownik(pracownik, direction, dry_run)
                stats[result] += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  BŁĄD: {pracownik} - {e}'))
                stats['bledy'] += 1

        # Podsumowanie
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('PODSUMOWANIE:'))
        self.stdout.write(f'  Utworzono nowych User: {stats["utworzono_user"]}')
        self.stdout.write(f'  Zsynchronizowano: {stats["zsynchronizowano"]}')
        self.stdout.write(f'  Bez zmian: {stats["bez_zmian"]}')
        if stats['bledy']:
            self.stdout.write(self.style.ERROR(f'  Błędy: {stats["bledy"]}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n(tryb podglądu - zmiany NIE zostały zapisane)'))

    def sync_pracownik(self, pracownik, direction, dry_run):
        """
        Synchronizuje pojedynczego Pracownika.
        Zwraca: 'utworzono_user', 'zsynchronizowano', 'bez_zmian'
        """
        # Pobierz grupę "produkcja" (domyślna dla nowych użytkowników)
        grupa_produkcja = Group.objects.filter(name='produkcja').first()

        # Przypadek 1: Pracownik nie ma User - trzeba utworzyć
        if pracownik.user is None:
            username = self.generate_username(pracownik.imie, pracownik.nazwisko)

            self.stdout.write(f'  [NOWY USER] {pracownik.imie} {pracownik.nazwisko} → username: {username}')

            if not dry_run:
                user = User.objects.create_user(
                    username=username,
                    password='cnctools!',
                    first_name=pracownik.imie,
                    last_name=pracownik.nazwisko,
                    is_active=True,
                )
                # Przypisz grupę "produkcja"
                if grupa_produkcja:
                    user.groups.add(grupa_produkcja)
                pracownik.user = user
                pracownik.save(update_fields=['user'])

            return 'utworzono_user'

        # Przypadek 2: Pracownik ma User - synchronizacja pól
        user = pracownik.user
        zmiany = []

        # Sprawdź czy User ma jakąkolwiek grupę, jeśli nie - dodaj "produkcja"
        if not user.groups.exists() and grupa_produkcja:
            zmiany.append(f'Dodano grupę: produkcja')
            if not dry_run:
                user.groups.add(grupa_produkcja)

        if direction in ('to_user', 'both'):
            # Pracownik → User
            if user.first_name != pracownik.imie:
                zmiany.append(f'User.first_name: "{user.first_name}" → "{pracownik.imie}"')
                if not dry_run:
                    user.first_name = pracownik.imie
            if user.last_name != pracownik.nazwisko:
                zmiany.append(f'User.last_name: "{user.last_name}" → "{pracownik.nazwisko}"')
                if not dry_run:
                    user.last_name = pracownik.nazwisko

        if direction in ('to_pracownik', 'both'):
            # User → Pracownik (tylko jeśli direction=to_pracownik lub both)
            # Przy 'both' priorytet ma Pracownik (już obsłużone wyżej)
            if direction == 'to_pracownik':
                if pracownik.imie != user.first_name:
                    zmiany.append(f'Pracownik.imie: "{pracownik.imie}" → "{user.first_name}"')
                    if not dry_run:
                        pracownik.imie = user.first_name
                if pracownik.nazwisko != user.last_name:
                    zmiany.append(f'Pracownik.nazwisko: "{pracownik.nazwisko}" → "{user.last_name}"')
                    if not dry_run:
                        pracownik.nazwisko = user.last_name

        if zmiany:
            self.stdout.write(f'  [SYNC] {pracownik.imie} {pracownik.nazwisko} (ID={pracownik.id}):')
            for zmiana in zmiany:
                self.stdout.write(f'         {zmiana}')

            if not dry_run:
                user.save()
                pracownik.save()

            return 'zsynchronizowano'

        return 'bez_zmian'

    def generate_username(self, imie, nazwisko):
        """
        Generuje username w formacie imie.nazwisko (małe litery, bez polskich znaków).
        Obsługuje duplikaty przez dodanie sufixu: jan.kowalski, jan.kowalski2, jan.kowalski3...
        """
        # Normalizacja - małe litery, zamiana polskich znaków
        import unicodedata

        def normalize(text):
            # Usuń akcenty (ą→a, ł→l, etc.)
            nfkd = unicodedata.normalize('NFKD', text.lower())
            ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
            # Specjalna obsługa ł
            ascii_text = ascii_text.replace('ł', 'l')
            # Usuń wszystko co nie jest literą
            return ''.join(c for c in ascii_text if c.isalnum())

        base_username = f"{normalize(imie)}.{normalize(nazwisko)}"
        username = base_username

        # Sprawdź czy istnieje, jeśli tak - dodaj suffix
        counter = 2
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

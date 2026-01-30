"""
System logowania operacji użytkowników.
Logi z dzisiejszego dnia przechowywane w bazie danych.
Starsze logi archiwizowane do plików JSON.
"""

import os
import json
from datetime import datetime, date, timedelta
from threading import Lock
from django.conf import settings
from django.utils import timezone


class LoggingService:
    """
    Serwis do logowania operacji użytkowników.
    Logi z dzisiaj w bazie danych, starsze w plikach.
    """
    _instance = None
    _lock = Lock()

    # Katalog na pliki archiwalne
    LOGS_DIR = os.path.join(settings.BASE_DIR, 'logs')

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._file_lock = Lock()

        # Utwórz katalog logs jeśli nie istnieje
        if not os.path.exists(self.LOGS_DIR):
            os.makedirs(self.LOGS_DIR)

    def _get_log_model(self):
        """Lazy import modelu LogEntry"""
        from .models import LogEntry
        return LogEntry

    def log(self, status: str, osoba: str, operacja: str):
        """
        Dodaj wpis do logu (baza danych).

        Args:
            status: Status operacji (INFO, SUCCESS, WARNING, ERROR)
            osoba: Nazwa zalogowanego użytkownika
            operacja: Opis wykonanej operacji
        """
        LogEntry = self._get_log_model()
        LogEntry.objects.create(
            status=status.upper(),
            osoba=osoba or '-',
            operacja=operacja
        )

        # Archiwizuj stare logi (starsze niż dzisiaj)
        self._archive_old_logs()

    def info(self, osoba: str, operacja: str):
        """Log z poziomem INFO"""
        self.log('INFO', osoba, operacja)

    def success(self, osoba: str, operacja: str):
        """Log z poziomem SUCCESS"""
        self.log('SUCCESS', osoba, operacja)

    def warning(self, osoba: str, operacja: str):
        """Log z poziomem WARNING"""
        self.log('WARNING', osoba, operacja)

    def error(self, osoba: str, operacja: str):
        """Log z poziomem ERROR"""
        self.log('ERROR', osoba, operacja)

    def get_recent_logs(self) -> list:
        """
        Pobierz logi z dzisiaj (bieżące).

        Returns:
            Lista logów posortowana od najnowszych
        """
        LogEntry = self._get_log_model()
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))

        logs = LogEntry.objects.filter(timestamp__gte=today_start).order_by('-timestamp')

        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'status': log.status,
                'osoba': log.osoba,
                'operacja': log.operacja
            }
            for log in logs
        ]

    def _archive_old_logs(self):
        """
        Archiwizuj logi starsze niż dzisiaj do plików JSON.
        """
        LogEntry = self._get_log_model()
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))

        # Pobierz logi starsze niż dzisiaj
        old_logs = LogEntry.objects.filter(timestamp__lt=today_start).order_by('timestamp')

        if not old_logs.exists():
            return

        # Grupuj po dacie
        logs_by_date = {}
        for log in old_logs:
            log_date = log.timestamp.strftime('%Y-%m-%d')
            if log_date not in logs_by_date:
                logs_by_date[log_date] = []
            logs_by_date[log_date].append({
                'timestamp': log.timestamp.isoformat(),
                'status': log.status,
                'osoba': log.osoba,
                'operacja': log.operacja
            })

        # Zapisz do plików
        with self._file_lock:
            for date_str, date_logs in logs_by_date.items():
                filepath = os.path.join(self.LOGS_DIR, f'{date_str}.log')

                # Dopisz do istniejącego pliku lub utwórz nowy
                existing_logs = []
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            existing_logs = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        existing_logs = []

                # Połącz i posortuj (od najnowszych)
                all_logs = existing_logs + date_logs
                all_logs.sort(key=lambda x: x['timestamp'], reverse=True)

                # Zapisz
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(all_logs, f, ensure_ascii=False, indent=2)

        # Usuń zarchiwizowane logi z bazy
        old_logs.delete()

    def get_log_files(self) -> list:
        """
        Pobierz listę plików logów archiwalnych.

        Returns:
            Lista słowników z informacjami o plikach
        """
        files = []

        if not os.path.exists(self.LOGS_DIR):
            return files

        for filename in sorted(os.listdir(self.LOGS_DIR), reverse=True):
            if filename.endswith('.log'):
                filepath = os.path.join(self.LOGS_DIR, filename)
                stat = os.stat(filepath)
                files.append({
                    'nazwa': filename,
                    'rozmiar': stat.st_size,
                    'data_modyfikacji': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return files

    def get_file_content(self, filename: str) -> list:
        """
        Pobierz zawartość pliku logu jako listę słowników.

        Args:
            filename: Nazwa pliku

        Returns:
            Lista logów w formacie identycznym jak get_recent_logs()
        """
        # Zabezpieczenie przed path traversal
        safe_filename = os.path.basename(filename)
        filepath = os.path.join(self.LOGS_DIR, safe_filename)

        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            return logs
        except (json.JSONDecodeError, IOError):
            return []


# Singleton instance
app_logger = LoggingService()


def get_user_display_name(user) -> str:
    """
    Pobierz wyświetlaną nazwę użytkownika.

    Args:
        user: Obiekt User Django

    Returns:
        Nazwa w formacie "Imię Nazwisko" lub username
    """
    if not user or not user.is_authenticated:
        return '-'

    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return user.username

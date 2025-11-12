// static/js/main_faktury.js

const { createApp } = Vue;
const API_URL = '/api';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            faktury: [],
            dostawcy: [], // Lista dostawców do selecta
            isLoading: false,
            isSaving: false, // Flaga do blokowania przycisku zapisu

            // Dane dla modala
            modal: {
                instance: null,
                mode: 'add', // 'add' lub 'edit'
                title: '',
                currentItem: {}, // Obiekt faktury do edycji/dodania
                fileToUpload: null, // Plik wybrany przez użytkownika
                errorMessage: '',
            },
            // Dane dla modala usuwania
            deleteModal: {
                instance: null,
                idToDelete: null,
            },
            // Dane paginacji
            pagination: {
                count: 0,
                next: null,
                previous: null,
                currentPage: 1,
                totalPages: 1,
                pageSize: 100, // Domyślny rozmiar strony (powinien pasować do backendu)
                pageNumbers: [] // Lista numerów stron do wyświetlenia
            },
            baseUrl: `${API_URL}/faktury/` // Bazowy URL dla API faktur
        };
    },
    async mounted() {
        this.modal.instance = new bootstrap.Modal(this.$refs.itemModal);
        this.deleteModal.instance = new bootstrap.Modal(this.$refs.deleteModal);
        await this.fetchDostawcy(); // Pobierz dostawców najpierw
        await this.fetchFaktury(this.baseUrl); // Pobierz pierwszą stronę faktur
    },
    methods: {
        // --- Metody pobierania danych ---
        async fetchDostawcy() {
            try {
                const response = await axios.get(`${API_URL}/dostawcy/`);
                this.dostawcy = response.data;
            } catch (error) {
                console.error("Błąd podczas pobierania dostawców:", error);
                alert("Nie udało się pobrać listy dostawców.");
            }
        },
        async fetchFaktury(url) {
            this.isLoading = true;
            try {
                // Dodajemy parametr page_size do URL, jeśli go nie ma
                const urlWithPageSize = new URL(url, window.location.origin);
                if (!urlWithPageSize.searchParams.has('page_size')) {
                    urlWithPageSize.searchParams.set('page_size', this.pagination.pageSize);
                }

                const response = await axios.get(urlWithPageSize.toString());
                this.faktury = response.data.results;
                this.updatePagination(response.data);
            } catch (error) {
                console.error("Błąd podczas pobierania faktur:", error);
                alert("Nie udało się pobrać listy faktur.");
            } finally {
                this.isLoading = false;
            }
        },

        // --- Metody obsługi modala ---
        getInitialItem() {
            return {
                numer_faktury: '',
                data_wystawienia: new Date().toISOString().split('T')[0], // Domyślnie dzisiaj
                dostawca_id: null,
                plik: null,
                rozliczone: false,
            };
        },
        openModal(mode, item = null) {
            this.modal.mode = mode;
            this.modal.errorMessage = '';
            this.modal.fileToUpload = null; // Resetuj plik
            // Wyczyść input pliku, aby można było wybrać ten sam plik ponownie
            const fileInput = document.getElementById('invoiceFile');
            if(fileInput) fileInput.value = '';

            if (mode === 'add') {
                this.modal.title = 'Dodaj nową fakturę';
                this.modal.currentItem = this.getInitialItem();
            } else {
                this.modal.title = 'Edytuj fakturę';
                // Kopiujemy obiekt i upewniamy się, że mamy dostawca_id
                this.modal.currentItem = {
                    ...item,
                    dostawca_id: item.dostawca ? item.dostawca.id : null,
                };
            }
            this.modal.instance.show();
        },
        handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                this.modal.fileToUpload = file;
            } else {
                this.modal.fileToUpload = null;
            }
        },
        async saveItem() {
            this.isSaving = true;
            this.modal.errorMessage = '';

            // Walidacja pól wymaganych
            if (!this.modal.currentItem.numer_faktury || !this.modal.currentItem.data_wystawienia || !this.modal.currentItem.dostawca_id) {
                this.modal.errorMessage = 'Pola: Numer faktury, Data wystawienia i Dostawca są wymagane.';
                this.isSaving = false;
                return;
            }

            const formData = new FormData();
            formData.append('numer_faktury', this.modal.currentItem.numer_faktury);
            formData.append('data_wystawienia', this.modal.currentItem.data_wystawienia);
            formData.append('dostawca_id', this.modal.currentItem.dostawca_id);
            formData.append('rozliczone', this.modal.currentItem.rozliczone);

            // Dodaj plik tylko jeśli został wybrany
            if (this.modal.fileToUpload) {
                formData.append('plik', this.modal.fileToUpload);
            } else if (this.modal.mode === 'add') {
                 // Jeśli dodajemy i nie ma pliku, wyślij pustą wartość lub null
                 // (zależy od konfiguracji DRF, FormData może mieć z tym problem)
                 // Bezpieczniej jest po prostu nie dodawać klucza 'plik'
            }
             // Przy edycji, jeśli nie wybrano nowego pliku, pole 'plik' nie jest wysyłane,
             // więc backend nie powinien go modyfikować (chyba że używamy PUT zamiast PATCH).

            const method = this.modal.mode === 'add' ? 'post' : 'patch'; // Używamy PATCH do edycji, aby nie trzeba było wysyłać pliku za każdym razem
            const url = this.modal.mode === 'add' ? this.baseUrl : `${this.baseUrl}${this.modal.currentItem.id}/`;

            try {
                await axios({
                    method: method,
                    url: url,
                    data: formData,
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                this.modal.instance.hide();
                // Odśwież bieżącą stronę po zapisie
                await this.fetchFaktury(this.getCurrentPageUrl());
            } catch (error) {
                console.error("Błąd zapisu faktury:", error.response?.data);
                if (error.response && error.response.data) {
                    if (typeof error.response.data === 'object') {
                         this.modal.errorMessage = Object.entries(error.response.data)
                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
                        .join('; ');
                    } else {
                        this.modal.errorMessage = error.response.data;
                    }
                } else {
                    this.modal.errorMessage = 'Wystąpił nieznany błąd podczas zapisu.';
                }
            } finally {
                this.isSaving = false;
            }
        },

        // --- Metody obsługi usuwania ---
        showDeleteModal(id) {
            this.deleteModal.idToDelete = id;
            this.deleteModal.instance.show();
        },
        async confirmDeleteItem() {
            if (!this.deleteModal.idToDelete) return;
            try {
                await axios.delete(`${this.baseUrl}${this.deleteModal.idToDelete}/`);
                this.deleteModal.instance.hide();
                // Sprawdź, czy po usunięciu bieżąca strona nie będzie pusta
                if (this.faktury.length === 1 && this.pagination.currentPage > 1) {
                    // Jeśli tak, cofnij się do poprzedniej strony
                    await this.fetchFaktury(this.pagination.previous || this.baseUrl);
                } else {
                    // W przeciwnym razie odśwież bieżącą
                    await this.fetchFaktury(this.getCurrentPageUrl());
                }
            } catch (error) {
                console.error("Błąd usuwania faktury:", error);
                this.deleteModal.instance.hide();
                alert('Nie można usunąć faktury. Sprawdź, czy nie jest powiązana z egzemplarzami narzędzi.');
            }
        },

         // --- Metody paginacji ---
        updatePagination(data) {
            this.pagination.count = data.count;
            this.pagination.next = data.next;
            this.pagination.previous = data.previous;
            this.pagination.totalPages = Math.ceil(data.count / this.pagination.pageSize);

            // Wyciągnij numer bieżącej strony z URL (jeśli jest) lub ustaw 1
            let currentPage = 1;
            const currentUrl = new URL(window.location.href); // Użyj bieżącego URL okna lub innego
            // Spróbuj pobrać z 'previous' lub 'next' jeśli dostępne
            let urlToParse = this.baseUrl;
            if(this.pagination.previous) urlToParse = this.pagination.previous;
            else if(this.pagination.next) urlToParse = this.pagination.next;

            try {
                 const parsedUrl = new URL(urlToParse);
                 const pageParam = parsedUrl.searchParams.get('page');
                 if(pageParam) {
                    currentPage = parseInt(pageParam);
                    if(this.pagination.previous && this.pagination.next === null) currentPage += 1; // Przypadek ostatniej strony
                    else if(this.pagination.previous === null && this.pagination.next) currentPage = 1; // Przypadek pierwszej strony
                    else if(this.pagination.previous && this.pagination.next) currentPage +=1; // Przypadek strony pośredniej
                 }
            } catch(e) {
                // Jeśli URL jest nieprawidłowy lub nie ma parametru, zostaje 1
                console.warn("Nie można sparsować URL paginacji, ustawiam stronę 1");
            }
             this.pagination.currentPage = currentPage;


            this.pagination.pageNumbers = this.generatePageNumbers(this.pagination.currentPage, this.pagination.totalPages);
        },
         generatePageNumbers(currentPage, totalPages) {
            const delta = 2; // Ile numerów pokazać wokół bieżącej strony
            const range = [];
            for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
                range.push(i);
            }

            if (currentPage - delta > 2) {
                range.unshift("...");
            }
            if (currentPage + delta < totalPages - 1) {
                range.push("...");
            }

            range.unshift(1);
            if (totalPages > 1) {
                range.push(totalPages);
            }

            // Usuń duplikaty '...' jeśli strony graniczne są blisko
            return [...new Set(range)].filter(page => page !== "..." || (range.indexOf(page) === range.lastIndexOf("...") && range.length > 5) || (range.indexOf(page) !== range.lastIndexOf("...") && range[range.indexOf(page)-1] !== 1 && range[range.lastIndexOf(page)+1] !== totalPages) ) ;
         },
        getPageUrl(pageNumber) {
            if (pageNumber === "...") return '#'; // Nie klikalne '...'
            const url = new URL(this.baseUrl, window.location.origin);
            url.searchParams.set('page', pageNumber);
            url.searchParams.set('page_size', this.pagination.pageSize);
            return url.toString();
        },
        getCurrentPageUrl() {
            // Zwraca URL bieżącej strony dla odświeżenia
            return this.getPageUrl(this.pagination.currentPage);
        }

    }
}).mount('#app');
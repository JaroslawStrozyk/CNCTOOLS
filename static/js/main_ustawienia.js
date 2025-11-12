// static/js/main_ustawienia.js

const { createApp } = Vue;
const API_URL = '/api';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            kategorie: [],
            podkategorie: [],
            machines: [],
            locations: [],
            suppliers: [],
            pracownicy: [],

            selectedKategoriaId: null,

            // Email configuration
            emailConfig: {},
            emailLoading: false,
            emailTestSending: false,
            emailTestResult: null,

            modal: {
                instance: null,
                type: '',
                mode: 'add',
                title: '',
                currentItem: {},
                errorMessage: '',
            },
            deleteModal: {
                instance: null,
                type: null,
                id: null,
                message: '' // NOWA ZMIENNA NA KOMUNIKAT
            },
            bulkAddModal: {
                instance: null
            },
            bulkAddData: {
                szafa: '',
                liczba_kolumn: null,
                liczba_polek: null
            },
            endpoints: {
                kategoria: 'kategorie',
                podkategoria: 'podkategorie',
                machine: 'maszyny',
                location: 'lokalizacje',
                supplier: 'dostawcy',
                pracownik: 'pracownicy',
            }
        };
    },
    computed: {
        selectedKategoriaNazwa() {
            if (!this.selectedKategoriaId) return "Wybierz kategorię";
            const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
            return kat ? kat.nazwa : "";
        }
    },
    async mounted() {
        this.modal.instance = new bootstrap.Modal(this.$refs.itemModal);
        this.deleteModal.instance = new bootstrap.Modal(this.$refs.deleteModal);
        this.bulkAddModal.instance = new bootstrap.Modal(this.$refs.bulkAddModal);
        await this.fetchAllData();
        await this.fetchEmailConfig();
    },
    methods: {
        async fetchAllData() {
            try {
                const [katRes, macRes, locRes, supRes, praRes] = await Promise.all([
                    axios.get(`${API_URL}/kategorie/`),
                    axios.get(`${API_URL}/maszyny/`),
                    axios.get(`${API_URL}/lokalizacje/`),
                    axios.get(`${API_URL}/dostawcy/`),
                    axios.get(`${API_URL}/pracownicy/`),
                ]);

                // Filtruj null/undefined z danych
                this.kategorie = (katRes.data || []).filter(item => item != null);
                this.machines = (macRes.data || []).filter(item => item != null);
                this.locations = (locRes.data || []).filter(item => item != null);
                this.suppliers = (supRes.data || []).filter(item => item != null);

                // Pracownicy mają paginację - sprawdź czy results istnieje
                const pracownicyData = praRes.data.results || praRes.data;
                this.pracownicy = (pracownicyData || []).filter(item => item != null);

                if (this.selectedKategoriaId) {
                    const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
                    if (kat) {
                        this.selectKategoria(this.selectedKategoriaId);
                    } else {
                        this.selectedKategoriaId = null;
                        this.podkategorie = [];
                    }
                }

            } catch (error) {
                console.error("Błąd ładowania danych:", error);
            }
        },
        selectKategoria(kategoriaId) {
            this.selectedKategoriaId = kategoriaId;
            const kat = this.kategorie.find(k => k.id === kategoriaId);
            this.podkategorie = kat ? kat.podkategorie : [];
        },
        getInitialItem(type) {
            if (type === 'location') return { szafa: '', kolumna: '', polka: '' };
            if (type === 'supplier') return { kod_dostawcy: '', nazwa_firmy: '', nip: '', adres: '', telefon: '', email: '' };
            if (type === 'kategoria') return { nazwa: '' };
            if (type === 'podkategoria') return { nazwa: '', kategoria: this.selectedKategoriaId };
            if (type === 'pracownik') return { karta: '', nazwisko: '', imie: '' };
            return { nazwa: '' };
        },
        openModal(type, mode, item = null) {
            this.modal.type = type;
            this.modal.mode = mode;
            this.modal.errorMessage = '';

            if (mode === 'add') {
                this.modal.title = `Dodaj ${type}`;
                this.modal.currentItem = this.getInitialItem(type);
            } else {
                this.modal.title = `Edytuj ${type}`;
                if(type === 'podkategoria') {
                    this.modal.currentItem = { ...item, kategoria: item.kategoria.id };
                } else {
                    this.modal.currentItem = { ...item };
                }
            }
            this.modal.instance.show();
        },
        async saveItem() {
            const endpoint = this.endpoints[this.modal.type];
            const method = this.modal.mode === 'add' ? 'post' : 'put';
            const url = this.modal.mode === 'add' ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${this.modal.currentItem.id}/`;

            let payload;

            if (this.modal.type === 'podkategoria') {
                payload = { nazwa: this.modal.currentItem.nazwa, kategoria: this.modal.currentItem.kategoria };
            } else {
                payload = this.modal.currentItem;
            }

            try {
                await axios({ method: method, url: url, data: payload });
                this.modal.instance.hide();
                await this.fetchAllData();

                // Odśwież podkategorie dla aktualnie wybranej kategorii
                if (this.modal.type === 'podkategoria' && this.selectedKategoriaId) {
                    this.selectKategoria(this.selectedKategoriaId);
                }
            } catch (error) {
                console.error(`Błąd zapisu (${this.modal.type}):`, error.response?.data);
                if (error.response && error.response.data) {
                    if (typeof error.response.data === 'object') {
                         this.modal.errorMessage = Object.entries(error.response.data)
                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
                        .join('; ');
                    } else {
                        this.modal.errorMessage = error.response.data;
                    }
                } else {
                    this.modal.errorMessage = 'Wystąpił nieznany błąd.';
                }
            }
        },
        // ZMIANA: Dodajemy logikę ustawiania komunikatu
        showDeleteModal(type, itemId) {
            this.deleteModal.type = type;
            this.deleteModal.id = itemId;

            // Ustawienie odpowiedniego komunikatu
            if (type === 'kategoria') {
                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę kategorię? Usunięcie kategorii głównej usunie również wszystkie jej podkategorie. Operacja nie powiedzie się, jeśli element jest w użyciu.`;
            } else if (type === 'podkategoria') {
                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę podkategorię? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
            } else if (type === 'pracownik') {
                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tego pracownika? Operacja nie powiedzie się, jeśli pracownik ma przypisaną historię użycia narzędzi.`;
            } else {
                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć ten element? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
            }

            this.deleteModal.instance.show();
        },
        async confirmDeleteItem() {
            const endpoint = this.endpoints[this.deleteModal.type];
            try {
                await axios.delete(`${API_URL}/${endpoint}/${this.deleteModal.id}/`);
                this.deleteModal.instance.hide();
                await this.fetchAllData();
            } catch (error) {
                console.error(`Błąd usuwania (${this.deleteModal.type}):`, error);
                this.deleteModal.instance.hide();
                 // Można by tu dodać bardziej szczegółowy komunikat błędu
                alert('Nie można usunąć elementu. Sprawdź, czy nie jest powiązany z innymi danymi (np. narzędziami, historią użycia).');
            }
        },
        openBulkAddModal() {
            this.bulkAddData = { szafa: '', liczba_kolumn: 1, liczba_polek: 1 };
            this.bulkAddModal.instance.show();
        },
        async saveBulkItems() {
            if (!this.bulkAddData.szafa || !this.bulkAddData.liczba_kolumn || !this.bulkAddData.liczba_polek) {
                alert('Wszystkie pola są wymagane.');
                return;
            }
            try {
                await axios.post(`${API_URL}/lokalizacje/dodaj_seryjnie/`, this.bulkAddData);
                this.bulkAddModal.instance.hide();
                await this.fetchAllData();
            } catch (error) {
                console.error('Błąd podczas seryjnego dodawania lokalizacji:', error.response.data);
                alert('Wystąpił błąd: ' + (error.response.data.error || 'Błąd serwera.'));
            }
        },

        // ========== EMAIL METHODS ==========
        async fetchEmailConfig() {
            console.log('📧 Rozpoczynam ładowanie konfiguracji email...');
            this.emailLoading = true;
            try {
                console.log('📧 Wysyłam request GET /api/email/config/');
                const response = await axios.get('/api/email/config/');
                console.log('📧 Odpowiedź otrzymana:', response.data);
                this.emailConfig = response.data;
                console.log('📧 emailConfig ustawiony:', this.emailConfig);
            } catch (error) {
                console.error('❌ Błąd ładowania konfiguracji email:', error);
                console.error('❌ Response:', error.response);
                alert('Nie udało się załadować konfiguracji email: ' + (error.response?.data?.message || error.message));
            } finally {
                this.emailLoading = false;
                console.log('📧 emailLoading = false');
            }
        },

        async sendTestEmail() {
            this.emailTestSending = true;
            this.emailTestResult = null;

            try {
                const response = await axios.post('/api/email/test/');
                this.emailTestResult = response.data;
            } catch (error) {
                console.error('Błąd wysyłki testowego emaila:', error);
                this.emailTestResult = {
                    success: false,
                    message: error.response?.data?.message || 'Wystąpił nieoczekiwany błąd podczas wysyłki.'
                };
            } finally {
                this.emailTestSending = false;
            }
        }
    }
}).mount('#app');





























//// static/js/main_ustawienia.js
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//    data() {
//        return {
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            locations: [],
//            suppliers: [],
//            pracownicy: [],
//
//            selectedKategoriaId: null,
//
//            // Email configuration
//            emailConfig: {},
//            emailLoading: false,
//            emailTestSending: false,
//            emailTestResult: null,
//
//            modal: {
//                instance: null,
//                type: '',
//                mode: 'add',
//                title: '',
//                currentItem: {},
//                errorMessage: '',
//            },
//            deleteModal: {
//                instance: null,
//                type: null,
//                id: null,
//                message: '' // NOWA ZMIENNA NA KOMUNIKAT
//            },
//            bulkAddModal: {
//                instance: null
//            },
//            bulkAddData: {
//                szafa: '',
//                liczba_kolumn: null,
//                liczba_polek: null
//            },
//            endpoints: {
//                kategoria: 'kategorie',
//                podkategoria: 'podkategorie',
//                machine: 'maszyny',
//                location: 'lokalizacje',
//                supplier: 'dostawcy',
//                pracownik: 'pracownicy',
//            }
//        };
//    },
//    computed: {
//        selectedKategoriaNazwa() {
//            if (!this.selectedKategoriaId) return "Wybierz kategorię";
//            const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kat ? kat.nazwa : "";
//        }
//    },
//    async mounted() {
//        this.modal.instance = new bootstrap.Modal(this.$refs.itemModal);
//        this.deleteModal.instance = new bootstrap.Modal(this.$refs.deleteModal);
//        this.bulkAddModal.instance = new bootstrap.Modal(this.$refs.bulkAddModal);
//        await this.fetchAllData();
//        await this.fetchEmailConfig();
//    },
//    methods: {
//        async fetchAllData() {
//            try {
//                const [katRes, macRes, locRes, supRes, praRes] = await Promise.all([
//                    axios.get(`${API_URL}/kategorie/`),
//                    axios.get(`${API_URL}/maszyny/`),
//                    axios.get(`${API_URL}/lokalizacje/`),
//                    axios.get(`${API_URL}/dostawcy/`),
//                    axios.get(`${API_URL}/pracownicy/`),
//                ]);
//
//                // Filtruj null/undefined z danych
//                this.kategorie = (katRes.data || []).filter(item => item != null);
//                this.machines = (macRes.data || []).filter(item => item != null);
//                this.locations = (locRes.data || []).filter(item => item != null);
//                this.suppliers = (supRes.data || []).filter(item => item != null);
//                this.pracownicy = (praRes.data || []).filter(item => item != null);
//
//                if (this.selectedKategoriaId) {
//                    const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                    if (kat) {
//                        this.selectKategoria(this.selectedKategoriaId);
//                    } else {
//                        this.selectedKategoriaId = null;
//                        this.podkategorie = [];
//                    }
//                }
//
//            } catch (error) {
//                console.error("Błąd ładowania danych:", error);
//            }
//        },
//        selectKategoria(kategoriaId) {
//            this.selectedKategoriaId = kategoriaId;
//            const kat = this.kategorie.find(k => k.id === kategoriaId);
//            this.podkategorie = kat ? kat.podkategorie : [];
//        },
//        getInitialItem(type) {
//            if (type === 'location') return { szafa: '', kolumna: '', polka: '' };
//            if (type === 'supplier') return { kod_dostawcy: '', nazwa_firmy: '', nip: '', adres: '', telefon: '', email: '' };
//            if (type === 'kategoria') return { nazwa: '' };
//            if (type === 'podkategoria') return { nazwa: '', kategoria: this.selectedKategoriaId };
//            if (type === 'pracownik') return { karta: '', nazwisko: '', imie: '' };
//            return { nazwa: '' };
//        },
//        openModal(type, mode, item = null) {
//            this.modal.type = type;
//            this.modal.mode = mode;
//            this.modal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.modal.title = `Dodaj ${type}`;
//                this.modal.currentItem = this.getInitialItem(type);
//            } else {
//                this.modal.title = `Edytuj ${type}`;
//                if(type === 'podkategoria') {
//                    this.modal.currentItem = { ...item, kategoria: item.kategoria.id };
//                } else {
//                    this.modal.currentItem = { ...item };
//                }
//            }
//            this.modal.instance.show();
//        },
//        async saveItem() {
//            const endpoint = this.endpoints[this.modal.type];
//            const method = this.modal.mode === 'add' ? 'post' : 'put';
//            const url = this.modal.mode === 'add' ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${this.modal.currentItem.id}/`;
//
//            let payload;
//
//            if (this.modal.type === 'podkategoria') {
//                payload = { nazwa: this.modal.currentItem.nazwa, kategoria: this.modal.currentItem.kategoria };
//            } else {
//                payload = this.modal.currentItem;
//            }
//
//            try {
//                await axios({ method: method, url: url, data: payload });
//                this.modal.instance.hide();
//                await this.fetchAllData();
//
//                // Odśwież podkategorie dla aktualnie wybranej kategorii
//                if (this.modal.type === 'podkategoria' && this.selectedKategoriaId) {
//                    this.selectKategoria(this.selectedKategoriaId);
//                }
//            } catch (error) {
//                console.error(`Błąd zapisu (${this.modal.type}):`, error.response?.data);
//                if (error.response && error.response.data) {
//                    if (typeof error.response.data === 'object') {
//                         this.modal.errorMessage = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                    } else {
//                        this.modal.errorMessage = error.response.data;
//                    }
//                } else {
//                    this.modal.errorMessage = 'Wystąpił nieznany błąd.';
//                }
//            }
//        },
//        // ZMIANA: Dodajemy logikę ustawiania komunikatu
//        showDeleteModal(type, itemId) {
//            this.deleteModal.type = type;
//            this.deleteModal.id = itemId;
//
//            // Ustawienie odpowiedniego komunikatu
//            if (type === 'kategoria') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę kategorię? Usunięcie kategorii głównej usunie również wszystkie jej podkategorie. Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'podkategoria') {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę podkategorię? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'pracownik') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tego pracownika? Operacja nie powiedzie się, jeśli pracownik ma przypisaną historię użycia narzędzi.`;
//            } else {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć ten element? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            }
//
//            this.deleteModal.instance.show();
//        },
//        async confirmDeleteItem() {
//            const endpoint = this.endpoints[this.deleteModal.type];
//            try {
//                await axios.delete(`${API_URL}/${endpoint}/${this.deleteModal.id}/`);
//                this.deleteModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error(`Błąd usuwania (${this.deleteModal.type}):`, error);
//                this.deleteModal.instance.hide();
//                 // Można by tu dodać bardziej szczegółowy komunikat błędu
//                alert('Nie można usunąć elementu. Sprawdź, czy nie jest powiązany z innymi danymi (np. narzędziami, historią użycia).');
//            }
//        },
//        openBulkAddModal() {
//            this.bulkAddData = { szafa: '', liczba_kolumn: 1, liczba_polek: 1 };
//            this.bulkAddModal.instance.show();
//        },
//        async saveBulkItems() {
//            if (!this.bulkAddData.szafa || !this.bulkAddData.liczba_kolumn || !this.bulkAddData.liczba_polek) {
//                alert('Wszystkie pola są wymagane.');
//                return;
//            }
//            try {
//                await axios.post(`${API_URL}/lokalizacje/dodaj_seryjnie/`, this.bulkAddData);
//                this.bulkAddModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error('Błąd podczas seryjnego dodawania lokalizacji:', error.response.data);
//                alert('Wystąpił błąd: ' + (error.response.data.error || 'Błąd serwera.'));
//            }
//        },
//
//        // ========== EMAIL METHODS ==========
//        async fetchEmailConfig() {
//            console.log('📧 Rozpoczynam ładowanie konfiguracji email...');
//            this.emailLoading = true;
//            try {
//                console.log('📧 Wysyłam request GET /api/email/config/');
//                const response = await axios.get('/api/email/config/');
//                console.log('📧 Odpowiedź otrzymana:', response.data);
//                this.emailConfig = response.data;
//                console.log('📧 emailConfig ustawiony:', this.emailConfig);
//            } catch (error) {
//                console.error('❌ Błąd ładowania konfiguracji email:', error);
//                console.error('❌ Response:', error.response);
//                alert('Nie udało się załadować konfiguracji email: ' + (error.response?.data?.message || error.message));
//            } finally {
//                this.emailLoading = false;
//                console.log('📧 emailLoading = false');
//            }
//        },
//
//        async sendTestEmail() {
//            this.emailTestSending = true;
//            this.emailTestResult = null;
//
//            try {
//                const response = await axios.post('/api/email/test/');
//                this.emailTestResult = response.data;
//            } catch (error) {
//                console.error('Błąd wysyłki testowego emaila:', error);
//                this.emailTestResult = {
//                    success: false,
//                    message: error.response?.data?.message || 'Wystąpił nieoczekiwany błąd podczas wysyłki.'
//                };
//            } finally {
//                this.emailTestSending = false;
//            }
//        }
//    }
//}).mount('#app');


























//// static/js/main_ustawienia.js
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//    data() {
//        return {
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            locations: [],
//            suppliers: [],
//            pracownicy: [],
//
//            selectedKategoriaId: null,
//
//            // Email configuration
//            emailConfig: {},
//            emailLoading: false,
//            emailTestSending: false,
//            emailTestResult: null,
//
//            modal: {
//                instance: null,
//                type: '',
//                mode: 'add',
//                title: '',
//                currentItem: {},
//                errorMessage: '',
//            },
//            deleteModal: {
//                instance: null,
//                type: null,
//                id: null,
//                message: '' // NOWA ZMIENNA NA KOMUNIKAT
//            },
//            bulkAddModal: {
//                instance: null
//            },
//            bulkAddData: {
//                szafa: '',
//                liczba_kolumn: null,
//                liczba_polek: null
//            },
//            endpoints: {
//                kategoria: 'kategorie',
//                podkategoria: 'podkategorie',
//                machine: 'maszyny',
//                location: 'lokalizacje',
//                supplier: 'dostawcy',
//                pracownik: 'pracownicy',
//            }
//        };
//    },
//    computed: {
//        selectedKategoriaNazwa() {
//            if (!this.selectedKategoriaId) return "Wybierz kategorię";
//            const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kat ? kat.nazwa : "";
//        }
//    },
//    async mounted() {
//        this.modal.instance = new bootstrap.Modal(this.$refs.itemModal);
//        this.deleteModal.instance = new bootstrap.Modal(this.$refs.deleteModal);
//        this.bulkAddModal.instance = new bootstrap.Modal(this.$refs.bulkAddModal);
//        await this.fetchAllData();
//        await this.fetchEmailConfig();
//    },
//    methods: {
//        async fetchAllData() {
//            try {
//                const [katRes, macRes, locRes, supRes, praRes] = await Promise.all([
//                    axios.get(`${API_URL}/kategorie/`),
//                    axios.get(`${API_URL}/maszyny/`),
//                    axios.get(`${API_URL}/lokalizacje/`),
//                    axios.get(`${API_URL}/dostawcy/`),
//                    axios.get(`${API_URL}/pracownicy/`),
//                ]);
//
//                // Filtruj null/undefined z danych
//                this.kategorie = (katRes.data || []).filter(item => item != null);
//                this.machines = (macRes.data || []).filter(item => item != null);
//                this.locations = (locRes.data || []).filter(item => item != null);
//                this.suppliers = (supRes.data || []).filter(item => item != null);
//                this.pracownicy = (praRes.data || []).filter(item => item != null);
//
//                if (this.selectedKategoriaId) {
//                    const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                    if (kat) {
//                        this.selectKategoria(this.selectedKategoriaId);
//                    } else {
//                        this.selectedKategoriaId = null;
//                        this.podkategorie = [];
//                    }
//                }
//
//            } catch (error) {
//                console.error("Błąd ładowania danych:", error);
//            }
//        },
//        selectKategoria(kategoriaId) {
//            this.selectedKategoriaId = kategoriaId;
//            const kat = this.kategorie.find(k => k.id === kategoriaId);
//            this.podkategorie = kat ? kat.podkategorie : [];
//        },
//        getInitialItem(type) {
//            if (type === 'location') return { szafa: '', kolumna: '', polka: '' };
//            if (type === 'supplier') return { kod_dostawcy: '', nazwa_firmy: '', nip: '', adres: '', telefon: '', email: '' };
//            if (type === 'kategoria') return { nazwa: '' };
//            if (type === 'podkategoria') return { nazwa: '', kategoria: this.selectedKategoriaId };
//            if (type === 'pracownik') return { karta: '', nazwisko: '', imie: '' };
//            return { nazwa: '' };
//        },
//        openModal(type, mode, item = null) {
//            this.modal.type = type;
//            this.modal.mode = mode;
//            this.modal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.modal.title = `Dodaj ${type}`;
//                this.modal.currentItem = this.getInitialItem(type);
//            } else {
//                this.modal.title = `Edytuj ${type}`;
//                if(type === 'podkategoria') {
//                    this.modal.currentItem = { ...item, kategoria: item.kategoria.id };
//                } else {
//                    this.modal.currentItem = { ...item };
//                }
//            }
//            this.modal.instance.show();
//        },
//        async saveItem() {
//            const endpoint = this.endpoints[this.modal.type];
//            const method = this.modal.mode === 'add' ? 'post' : 'put';
//            const url = this.modal.mode === 'add' ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${this.modal.currentItem.id}/`;
//
//            let payload;
//
//            if (this.modal.type === 'podkategoria') {
//                payload = { nazwa: this.modal.currentItem.nazwa, kategoria: this.modal.currentItem.kategoria };
//            } else {
//                payload = this.modal.currentItem;
//            }
//
//            try {
//                await axios({ method: method, url: url, data: payload });
//                this.modal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error(`Błąd zapisu (${this.modal.type}):`, error.response?.data);
//                if (error.response && error.response.data) {
//                    if (typeof error.response.data === 'object') {
//                         this.modal.errorMessage = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                    } else {
//                        this.modal.errorMessage = error.response.data;
//                    }
//                } else {
//                    this.modal.errorMessage = 'Wystąpił nieznany błąd.';
//                }
//            }
//        },
//        // ZMIANA: Dodajemy logikę ustawiania komunikatu
//        showDeleteModal(type, itemId) {
//            this.deleteModal.type = type;
//            this.deleteModal.id = itemId;
//
//            // Ustawienie odpowiedniego komunikatu
//            if (type === 'kategoria') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę kategorię? Usunięcie kategorii głównej usunie również wszystkie jej podkategorie. Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'podkategoria') {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę podkategorię? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'pracownik') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tego pracownika? Operacja nie powiedzie się, jeśli pracownik ma przypisaną historię użycia narzędzi.`;
//            } else {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć ten element? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            }
//
//            this.deleteModal.instance.show();
//        },
//        async confirmDeleteItem() {
//            const endpoint = this.endpoints[this.deleteModal.type];
//            try {
//                await axios.delete(`${API_URL}/${endpoint}/${this.deleteModal.id}/`);
//                this.deleteModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error(`Błąd usuwania (${this.deleteModal.type}):`, error);
//                this.deleteModal.instance.hide();
//                 // Można by tu dodać bardziej szczegółowy komunikat błędu
//                alert('Nie można usunąć elementu. Sprawdź, czy nie jest powiązany z innymi danymi (np. narzędziami, historią użycia).');
//            }
//        },
//        openBulkAddModal() {
//            this.bulkAddData = { szafa: '', liczba_kolumn: 1, liczba_polek: 1 };
//            this.bulkAddModal.instance.show();
//        },
//        async saveBulkItems() {
//            if (!this.bulkAddData.szafa || !this.bulkAddData.liczba_kolumn || !this.bulkAddData.liczba_polek) {
//                alert('Wszystkie pola są wymagane.');
//                return;
//            }
//            try {
//                await axios.post(`${API_URL}/lokalizacje/dodaj_seryjnie/`, this.bulkAddData);
//                this.bulkAddModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error('Błąd podczas seryjnego dodawania lokalizacji:', error.response.data);
//                alert('Wystąpił błąd: ' + (error.response.data.error || 'Błąd serwera.'));
//            }
//        },
//
//        // ========== EMAIL METHODS ==========
//        async fetchEmailConfig() {
//            console.log('📧 Rozpoczynam ładowanie konfiguracji email...');
//            this.emailLoading = true;
//            try {
//                console.log('📧 Wysyłam request GET /api/email/config/');
//                const response = await axios.get('/api/email/config/');
//                console.log('📧 Odpowiedź otrzymana:', response.data);
//                this.emailConfig = response.data;
//                console.log('📧 emailConfig ustawiony:', this.emailConfig);
//            } catch (error) {
//                console.error('❌ Błąd ładowania konfiguracji email:', error);
//                console.error('❌ Response:', error.response);
//                alert('Nie udało się załadować konfiguracji email: ' + (error.response?.data?.message || error.message));
//            } finally {
//                this.emailLoading = false;
//                console.log('📧 emailLoading = false');
//            }
//        },
//
//        async sendTestEmail() {
//            this.emailTestSending = true;
//            this.emailTestResult = null;
//
//            try {
//                const response = await axios.post('/api/email/test/');
//                this.emailTestResult = response.data;
//            } catch (error) {
//                console.error('Błąd wysyłki testowego emaila:', error);
//                this.emailTestResult = {
//                    success: false,
//                    message: error.response?.data?.message || 'Wystąpił nieoczekiwany błąd podczas wysyłki.'
//                };
//            } finally {
//                this.emailTestSending = false;
//            }
//        }
//    }
//}).mount('#app');












































//// static/js/main_ustawienia.js
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//    data() {
//        return {
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            locations: [],
//            suppliers: [],
//            pracownicy: [],
//
//            selectedKategoriaId: null,
//
//            // Email configuration
//            emailConfig: {},
//            emailLoading: false,
//            emailTestSending: false,
//            emailTestResult: null,
//
//            modal: {
//                instance: null,
//                type: '',
//                mode: 'add',
//                title: '',
//                currentItem: {},
//                errorMessage: '',
//            },
//            deleteModal: {
//                instance: null,
//                type: null,
//                id: null,
//                message: '' // NOWA ZMIENNA NA KOMUNIKAT
//            },
//            bulkAddModal: {
//                instance: null
//            },
//            bulkAddData: {
//                szafa: '',
//                liczba_kolumn: null,
//                liczba_polek: null
//            },
//            endpoints: {
//                kategoria: 'kategorie',
//                podkategoria: 'podkategorie',
//                machine: 'maszyny',
//                location: 'lokalizacje',
//                supplier: 'dostawcy',
//                pracownik: 'pracownicy',
//            }
//        };
//    },
//    computed: {
//        selectedKategoriaNazwa() {
//            if (!this.selectedKategoriaId) return "Wybierz kategorię";
//            const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kat ? kat.nazwa : "";
//        }
//    },
//    async mounted() {
//        this.modal.instance = new bootstrap.Modal(this.$refs.itemModal);
//        this.deleteModal.instance = new bootstrap.Modal(this.$refs.deleteModal);
//        this.bulkAddModal.instance = new bootstrap.Modal(this.$refs.bulkAddModal);
//        await this.fetchAllData();
//        await this.fetchEmailConfig();
//    },
//    methods: {
//        async fetchAllData() {
//            try {
//                const [katRes, macRes, locRes, supRes, praRes] = await Promise.all([
//                    axios.get(`${API_URL}/kategorie/`),
//                    axios.get(`${API_URL}/maszyny/`),
//                    axios.get(`${API_URL}/lokalizacje/`),
//                    axios.get(`${API_URL}/dostawcy/`),
//                    axios.get(`${API_URL}/pracownicy/`),
//                ]);
//
//                // Filtruj null/undefined z danych
//                this.kategorie = (katRes.data || []).filter(item => item != null);
//                this.machines = (macRes.data || []).filter(item => item != null);
//                this.locations = (locRes.data || []).filter(item => item != null);
//                this.suppliers = (supRes.data || []).filter(item => item != null);
//                this.pracownicy = (praRes.data || []).filter(item => item != null);
//
//                if (this.selectedKategoriaId) {
//                    const kat = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                    if (kat) {
//                        this.selectKategoria(this.selectedKategoriaId);
//                    } else {
//                        this.selectedKategoriaId = null;
//                        this.podkategorie = [];
//                    }
//                }
//
//            } catch (error) {
//                console.error("Błąd ładowania danych:", error);
//            }
//        },
//        selectKategoria(kategoriaId) {
//            this.selectedKategoriaId = kategoriaId;
//            const kat = this.kategorie.find(k => k.id === kategoriaId);
//            this.podkategorie = kat ? kat.podkategorie : [];
//        },
//        getInitialItem(type) {
//            if (type === 'location') return { szafa: '', kolumna: '', polka: '' };
//            if (type === 'supplier') return { kod_dostawcy: '', nazwa_firmy: '', nip: '', adres: '', telefon: '', email: '' };
//            if (type === 'kategoria') return { nazwa: '' };
//            if (type === 'podkategoria') return { nazwa: '', kategoria: this.selectedKategoriaId };
//            if (type === 'pracownik') return { karta: '', nazwisko: '', imie: '' };
//            return { nazwa: '' };
//        },
//        openModal(type, mode, item = null) {
//            this.modal.type = type;
//            this.modal.mode = mode;
//            this.modal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.modal.title = `Dodaj ${type}`;
//                this.modal.currentItem = this.getInitialItem(type);
//            } else {
//                this.modal.title = `Edytuj ${type}`;
//                if(type === 'podkategoria') {
//                    this.modal.currentItem = { ...item, kategoria: item.kategoria.id };
//                } else {
//                    this.modal.currentItem = { ...item };
//                }
//            }
//            this.modal.instance.show();
//        },
//        async saveItem() {
//            const endpoint = this.endpoints[this.modal.type];
//            const method = this.modal.mode === 'add' ? 'post' : 'put';
//            const url = this.modal.mode === 'add' ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${this.modal.currentItem.id}/`;
//
//            let payload;
//
//            if (this.modal.type === 'podkategoria') {
//                payload = { nazwa: this.modal.currentItem.nazwa, kategoria_id: this.modal.currentItem.kategoria };
//            } else {
//                payload = this.modal.currentItem;
//            }
//
//            try {
//                await axios({ method: method, url: url, data: payload });
//                this.modal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error(`Błąd zapisu (${this.modal.type}):`, error.response?.data);
//                if (error.response && error.response.data) {
//                    if (typeof error.response.data === 'object') {
//                         this.modal.errorMessage = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                    } else {
//                        this.modal.errorMessage = error.response.data;
//                    }
//                } else {
//                    this.modal.errorMessage = 'Wystąpił nieznany błąd.';
//                }
//            }
//        },
//        // ZMIANA: Dodajemy logikę ustawiania komunikatu
//        showDeleteModal(type, itemId) {
//            this.deleteModal.type = type;
//            this.deleteModal.id = itemId;
//
//            // Ustawienie odpowiedniego komunikatu
//            if (type === 'kategoria') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę kategorię? Usunięcie kategorii głównej usunie również wszystkie jej podkategorie. Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'podkategoria') {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tę podkategorię? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            } else if (type === 'pracownik') {
//                this.deleteModal.message = `Czy na pewno chcesz trwale usunąć tego pracownika? Operacja nie powiedzie się, jeśli pracownik ma przypisaną historię użycia narzędzi.`;
//            } else {
//                 this.deleteModal.message = `Czy na pewno chcesz trwale usunąć ten element? Operacja nie powiedzie się, jeśli element jest w użyciu.`;
//            }
//
//            this.deleteModal.instance.show();
//        },
//        async confirmDeleteItem() {
//            const endpoint = this.endpoints[this.deleteModal.type];
//            try {
//                await axios.delete(`${API_URL}/${endpoint}/${this.deleteModal.id}/`);
//                this.deleteModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error(`Błąd usuwania (${this.deleteModal.type}):`, error);
//                this.deleteModal.instance.hide();
//                 // Można by tu dodać bardziej szczegółowy komunikat błędu
//                alert('Nie można usunąć elementu. Sprawdź, czy nie jest powiązany z innymi danymi (np. narzędziami, historią użycia).');
//            }
//        },
//        openBulkAddModal() {
//            this.bulkAddData = { szafa: '', liczba_kolumn: 1, liczba_polek: 1 };
//            this.bulkAddModal.instance.show();
//        },
//        async saveBulkItems() {
//            if (!this.bulkAddData.szafa || !this.bulkAddData.liczba_kolumn || !this.bulkAddData.liczba_polek) {
//                alert('Wszystkie pola są wymagane.');
//                return;
//            }
//            try {
//                await axios.post(`${API_URL}/lokalizacje/dodaj_seryjnie/`, this.bulkAddData);
//                this.bulkAddModal.instance.hide();
//                await this.fetchAllData();
//            } catch (error) {
//                console.error('Błąd podczas seryjnego dodawania lokalizacji:', error.response.data);
//                alert('Wystąpił błąd: ' + (error.response.data.error || 'Błąd serwera.'));
//            }
//        },
//
//        // ========== EMAIL METHODS ==========
//        async fetchEmailConfig() {
//            console.log('📧 Rozpoczynam ładowanie konfiguracji email...');
//            this.emailLoading = true;
//            try {
//                console.log('📧 Wysyłam request GET /api/email/config/');
//                const response = await axios.get('/api/email/config/');
//                console.log('📧 Odpowiedź otrzymana:', response.data);
//                this.emailConfig = response.data;
//                console.log('📧 emailConfig ustawiony:', this.emailConfig);
//            } catch (error) {
//                console.error('❌ Błąd ładowania konfiguracji email:', error);
//                console.error('❌ Response:', error.response);
//                alert('Nie udało się załadować konfiguracji email: ' + (error.response?.data?.message || error.message));
//            } finally {
//                this.emailLoading = false;
//                console.log('📧 emailLoading = false');
//            }
//        },
//
//        async sendTestEmail() {
//            this.emailTestSending = true;
//            this.emailTestResult = null;
//
//            try {
//                const response = await axios.post('/api/email/test/');
//                this.emailTestResult = response.data;
//            } catch (error) {
//                console.error('Błąd wysyłki testowego emaila:', error);
//                this.emailTestResult = {
//                    success: false,
//                    message: error.response?.data?.message || 'Wystąpił nieoczekiwany błąd podczas wysyłki.'
//                };
//            } finally {
//                this.emailTestSending = false;
//            }
//        }
//    }
//}).mount('#app');
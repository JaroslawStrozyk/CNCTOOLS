// static/js/main_realizacja.js

const { createApp } = Vue;
const API_URL = '/api';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            realizacje: [],
            selectedRealizacja: null,
            selectedPozycje: [],
            selectedDeleteRealizacja: null,
            isPrzyjecieLoading: false,
            isDeleting: false,
            przyjmijError: '',
            utworzoneEgzemplarze: [],
            modals: {}
        };
    },

    async mounted() {
        this.initModals();
        await this.fetchRealizacje();
    },

    methods: {
        initModals() {
            if (this.$refs.przyjmijModal) {
                this.modals.przyjmijModal = new bootstrap.Modal(this.$refs.przyjmijModal);
            }
            if (this.$refs.wynikModal) {
                this.modals.wynikModal = new bootstrap.Modal(this.$refs.wynikModal);
            }
            if (this.$refs.deleteModal) {
                this.modals.deleteModal = new bootstrap.Modal(this.$refs.deleteModal);
            }
        },

        async fetchRealizacje() {
            try {
                const response = await axios.get(`${API_URL}/realizacje/`);
                this.realizacje = response.data.results || response.data;
            } catch (error) {
                console.error("Błąd ładowania realizacji:", error);
            }
        },

        openPrzyjmijModal(realizacja) {
            this.selectedRealizacja = realizacja;
            this.przyjmijError = '';

            // Przygotuj pozycje z polami do edycji
            this.selectedPozycje = realizacja.pozycje.map(poz => ({
                ...poz,
                przyjmij: false,
                ilosc_przyjeta_input: poz.pozycja_zamowienia.ilosc_zamowiona
            }));

            if (this.modals.przyjmijModal) {
                this.modals.przyjmijModal.show();
            }
        },

        async zatwierdzPrzyjecie() {
            this.przyjmijError = '';

            // Walidacja - czy zaznaczono jakieś pozycje
            const zaznaczone = this.selectedPozycje.filter(p => p.przyjmij);
            if (zaznaczone.length === 0) {
                this.przyjmijError = 'Zaznacz przynajmniej jedną pozycję do przyjęcia';
                return;
            }

            // Walidacja - czy ilości są > 0
            for (const poz of zaznaczone) {
                if (!poz.ilosc_przyjeta_input || poz.ilosc_przyjeta_input <= 0) {
                    this.przyjmijError = 'Wszystkie zaznaczone pozycje muszą mieć ilość > 0';
                    return;
                }
            }

            this.isPrzyjecieLoading = true;

            try {
                // Przygotuj dane do wysłania
                const pozycje_dane = zaznaczone.map(poz => ({
                    id: poz.id,
                    ilosc_przyjeta: poz.ilosc_przyjeta_input
                }));

                const response = await axios.post(
                    `${API_URL}/realizacje/${this.selectedRealizacja.id}/zatwierdz/`,
                    { pozycje: pozycje_dane }
                );

                if (response.data.success) {
                    this.utworzoneEgzemplarze = response.data.utworzone_egzemplarze;

                    // Zamknij modal przyjęcia
                    if (this.modals.przyjmijModal) {
                        this.modals.przyjmijModal.hide();
                    }

                    // Pokaż modal wyniku
                    if (this.modals.wynikModal) {
                        this.modals.wynikModal.show();
                    }

                    // Odśwież listę
                    await this.fetchRealizacje();
                }

            } catch (error) {
                console.error("Błąd zatwierdzania przyjęcia:", error);
                this.przyjmijError = error.response?.data?.error || 'Wystąpił błąd podczas zatwierdzania';
            } finally {
                this.isPrzyjecieLoading = false;
            }
        },

        isRealizacjaZakonczona(realizacja) {
            // Sprawdź czy wszystkie pozycje mają ilosc_przyjeta > 0
            if (!realizacja.pozycje || realizacja.pozycje.length === 0) {
                return false;
            }
            return realizacja.pozycje.every(poz => poz.ilosc_przyjeta > 0);
        },

        openDeleteModal(realizacja) {
            this.selectedDeleteRealizacja = realizacja;
            if (this.modals.deleteModal) {
                this.modals.deleteModal.show();
            }
        },

        async confirmDelete() {
            this.isDeleting = true;

            try {
                await axios.delete(`${API_URL}/realizacje/${this.selectedDeleteRealizacja.id}/`);

                if (this.modals.deleteModal) {
                    this.modals.deleteModal.hide();
                }

                await this.fetchRealizacje();

            } catch (error) {
                console.error("Błąd usuwania realizacji:", error);
                alert('Wystąpił błąd podczas usuwania realizacji');
            } finally {
                this.isDeleting = false;
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';

            const date = new Date(dateString);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');

            return `${year}-${month}-${day} ${hours}:${minutes}`;
        }
    }
}).mount('#app');
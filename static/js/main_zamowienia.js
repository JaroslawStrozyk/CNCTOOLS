// static/js/main_zamowienia.js

const { createApp } = Vue;
const API_URL = '/api';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            zamowienia: [],
            dostawcy: [],
            narzedzia: [],
            selectedZamowienie: null,

            isSaving: false,

            zamowienieModal: {
                instance: null,
                mode: 'add',
                title: '',
                currentItem: {},
                errorMessage: ''
            },

            statusLabels: {
                'draft': 'Wersja robocza',
                'verified': 'Zweryfikowane',
                'sent': 'Wysłane',
                'partially_received': 'Częściowo odebrane',
                'completed': 'Zrealizowane'
            }
        };
    },

    async mounted() {
        this.initModals();
        await this.fetchInitialData();
    },

    methods: {
        initModals() {
            if (this.$refs.zamowienieModal) {
                this.zamowienieModal.instance = new bootstrap.Modal(this.$refs.zamowienieModal);
            }
        },

        async fetchInitialData() {
            try {
                const [zamowieniaRes, dostawcyRes, narzedziaRes] = await Promise.all([
                    axios.get(`${API_URL}/zamowienia/`),
                    axios.get(`${API_URL}/dostawcy/`),
                    axios.get(`${API_URL}/narzedzia/`)
                ]);

                this.zamowienia = zamowieniaRes.data;
                this.dostawcy = dostawcyRes.data;
                this.narzedzia = narzedziaRes.data.results || narzedziaRes.data;
            } catch (error) {
                console.error("Błąd ładowania danych:", error);
                alert("Wystąpił błąd podczas ładowania danych.");
            }
        },

        selectZamowienie(zamowienie) {
            this.selectedZamowienie = zamowienie;
        },

        openZamowienieModal(mode, zamowienie = null) {
            this.zamowienieModal.mode = mode;
            this.zamowienieModal.errorMessage = '';

            if (mode === 'add') {
                this.zamowienieModal.title = 'Nowe zamówienie';
                this.zamowienieModal.currentItem = {
                    numer: this.generateZamowienieNumer(),
                    dostawca_id: null,
                    uwagi: ''
                };
            } else {
                this.zamowienieModal.title = 'Edytuj zamówienie';
                this.zamowienieModal.currentItem = {
                    ...zamowienie,
                    dostawca_id: zamowienie.dostawca.id
                };
            }

            if (this.zamowienieModal.instance) {
                this.zamowienieModal.instance.show();
            }
        },

        generateZamowienieNumer() {
            const date = new Date();
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const random = Math.floor(Math.random() * 1000);
            return `ZAM/${year}/${month}/${random}`;
        },

        async saveZamowienie() {
            this.isSaving = true;
            this.zamowienieModal.errorMessage = '';

            if (!this.zamowienieModal.currentItem.numer || !this.zamowienieModal.currentItem.dostawca_id) {
                this.zamowienieModal.errorMessage = 'Numer zamówienia i dostawca są wymagane.';
                this.isSaving = false;
                return;
            }

            const method = this.zamowienieModal.mode === 'add' ? 'post' : 'patch';
            const url = this.zamowienieModal.mode === 'add' ?
                `${API_URL}/zamowienia/` :
                `${API_URL}/zamowienia/${this.zamowienieModal.currentItem.id}/`;

            try {
                await axios({
                    method: method,
                    url: url,
                    data: this.zamowienieModal.currentItem
                });

                if (this.zamowienieModal.instance) {
                    this.zamowienieModal.instance.hide();
                }

                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd zapisu zamówienia:", error);
                this.zamowienieModal.errorMessage = 'Wystąpił błąd podczas zapisu: ' +
                    (error.response?.data?.detail || error.message);
            } finally {
                this.isSaving = false;
            }
        },

        async generujAutomatyczne() {
            if (!confirm('Czy na pewno chcesz wygenerować zamówienia automatycznie dla narzędzi poniżej stanu minimalnego?')) {
                return;
            }

            try {
                await axios.post(`${API_URL}/zamowienia/generuj_automatyczne/`);
                alert('Zamówienia zostały wygenerowane automatycznie.');
                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd generowania zamówień:", error);
                alert('Wystąpił błąd podczas generowania zamówień: ' +
                    (error.response?.data?.detail || error.message));
            }
        },

        async wyslijEmail(zamowienieId) {
            if (!confirm('Czy na pewno chcesz wysłać to zamówienie e-mailem do dostawcy?')) {
                return;
            }

            try {
                await axios.post(`${API_URL}/zamowienia/${zamowienieId}/wyslij_email/`);
                alert('Zamówienie zostało wysłane e-mailem.');
                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd wysyłania e-maila:", error);
                alert('Wystąpił błąd podczas wysyłania e-maila: ' +
                    (error.response?.data?.detail || error.message));
            }
        },

        async rozpocznijRealizacje(zamowienieId) {
            try {
                await axios.post(`${API_URL}/zamowienia/${zamowienieId}/rozpocznij_realizacje/`);
                alert('Rozpoczęto realizację zamówienia.');
                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd rozpoczęcia realizacji:", error);
                alert('Wystąpił błąd podczas rozpoczęcia realizacji: ' +
                    (error.response?.data?.detail || error.message));
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
        },

        getStatusLabel(status) {
            return this.statusLabels[status] || status;
        }
    }
}).mount('#app');
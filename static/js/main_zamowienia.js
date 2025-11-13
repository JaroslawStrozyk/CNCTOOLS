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
            selectedUwagiZamowienie: null,
            selectedEmailZamowienie: null,
            selectedDeleteZamowienie: null,

            isSaving: false,
            isSendingEmail: false,
            isDeleting: false,

            emailResult: {
                success: false,
                message: ''
            },

            modals: {},

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
            if (this.$refs.detailsModal) {
                this.modals.detailsModal = new bootstrap.Modal(this.$refs.detailsModal);
            }
            if (this.$refs.uwagiModal) {
                this.modals.uwagiModal = new bootstrap.Modal(this.$refs.uwagiModal);
            }
            if (this.$refs.emailConfirmModal) {
                this.modals.emailConfirmModal = new bootstrap.Modal(this.$refs.emailConfirmModal);
            }
            if (this.$refs.emailResultModal) {
                this.modals.emailResultModal = new bootstrap.Modal(this.$refs.emailResultModal);
            }
            if (this.$refs.deleteConfirmModal) {
                this.modals.deleteConfirmModal = new bootstrap.Modal(this.$refs.deleteConfirmModal);
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

        async fetchZamowienia() {
            try {
                const response = await axios.get(`${API_URL}/zamowienia/`);
                this.zamowienia = response.data;
            } catch (error) {
                console.error("Błąd ładowania zamówień:", error);
            }
        },

        selectZamowienie(zamowienie) {
            this.selectedZamowienie = zamowienie;
            if (this.modals.detailsModal) {
                this.modals.detailsModal.show();
            }
        },

        showUwagi(zamowienie) {
            this.selectedUwagiZamowienie = zamowienie;
            if (this.modals.uwagiModal) {
                this.modals.uwagiModal.show();
            }
        },

        openEmailConfirmModal(zamowienie) {
            this.selectedEmailZamowienie = zamowienie;
            if (this.modals.emailConfirmModal) {
                this.modals.emailConfirmModal.show();
            }
        },

        async confirmWyslijEmail() {
            this.isSendingEmail = true;

            try {
                // TODO: Endpoint do wysyłki email
                const response = await axios.post(`${API_URL}/zamowienia/${this.selectedEmailZamowienie.id}/wyslij-email/`);

                if (this.modals.emailConfirmModal) {
                    this.modals.emailConfirmModal.hide();
                }

                this.emailResult = {
                    success: true,
                    message: 'Email został wysłany pomyślnie!'
                };

                if (this.modals.emailResultModal) {
                    this.modals.emailResultModal.show();
                }

                await this.fetchZamowienia();

            } catch (error) {
                console.error("Błąd wysyłki email:", error);

                if (this.modals.emailConfirmModal) {
                    this.modals.emailConfirmModal.hide();
                }

                this.emailResult = {
                    success: false,
                    message: error.response?.data?.error || 'Wystąpił błąd podczas wysyłki email'
                };

                if (this.modals.emailResultModal) {
                    this.modals.emailResultModal.show();
                }
            } finally {
                this.isSendingEmail = false;
            }
        },

        openDeleteConfirmModal(zamowienie) {
            this.selectedDeleteZamowienie = zamowienie;
            if (this.modals.deleteConfirmModal) {
                this.modals.deleteConfirmModal.show();
            }
        },

        async confirmDeleteZamowienie() {
            this.isDeleting = true;

            try {
                await axios.delete(`${API_URL}/zamowienia/${this.selectedDeleteZamowienie.id}/`);

                if (this.modals.deleteConfirmModal) {
                    this.modals.deleteConfirmModal.hide();
                }

                await this.fetchZamowienia();

            } catch (error) {
                console.error("Błąd usuwania:", error);

                this.emailResult = {
                    success: false,
                    message: 'Wystąpił błąd podczas usuwania: ' + (error.response?.data?.error || error.message)
                };

                if (this.modals.emailResultModal) {
                    this.modals.emailResultModal.show();
                }
            } finally {
                this.isDeleting = false;
                this.selectedDeleteZamowienie = null;
            }
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

        generujAutomatyczne() {
            // Przekieruj do strony generatora
            window.location.href = '/generator/';
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
// static/js/main_generator.js

const { createApp } = Vue;
const API_URL = '/api';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            toolsToOrder: [],
            dostawcy: [],
            kategorie: [],
            narzedzia: [],
            isLoading: true,
            isSaving: false,
            isDeleting: false,
            isAdding: false,
            isGenerating: false,

            editForm: {
                id: null,
                element: '',
                dostawca_id: null,
                numer_katalogowy: '',
                ilosc_do_zamowienia: 1,
                cena_jednostkowa: 0
            },
            editError: '',

            deleteItem: null,

            addForm: {
                dostawca_id: null,
                kategoria_id: null,
                podkategoria_id: null,
                narzedzie_id: null,
                ilosc_do_zamowienia: 1,
                cena_jednostkowa: 0
            },
            addError: '',
            selectedNarzedzie: null,

            modals: {}
        };
    },

    computed: {
        filteredPodkategorie() {
            if (!this.addForm.kategoria_id) return [];
            const kategoria = this.kategorie.find(k => k.id === this.addForm.kategoria_id);
            return kategoria ? kategoria.podkategorie : [];
        },

        filteredNarzedzia() {
            if (!this.addForm.podkategoria_id) return [];
            return this.narzedzia.filter(n =>
                n.podkategoria && n.podkategoria.id === this.addForm.podkategoria_id
            );
        }
    },

    async mounted() {
        this.initModals();
        await this.fetchDostawcy();
        await this.fetchKategorie();
        await this.fetchNarzedzia();
        await this.fetchToolsToOrder();
    },

    methods: {
        initModals() {
            if (this.$refs.editModal) {
                this.modals.editModal = new bootstrap.Modal(this.$refs.editModal);
            }
            if (this.$refs.deleteModal) {
                this.modals.deleteModal = new bootstrap.Modal(this.$refs.deleteModal);
            }
            if (this.$refs.addModal) {
                this.modals.addModal = new bootstrap.Modal(this.$refs.addModal);
            }
            if (this.$refs.confirmOrderModal) {
                this.modals.confirmOrderModal = new bootstrap.Modal(this.$refs.confirmOrderModal);
            }
        },

        async fetchDostawcy() {
            try {
                const response = await axios.get(`${API_URL}/dostawcy/`);
                this.dostawcy = response.data;
            } catch (error) {
                console.error("Błąd ładowania dostawców:", error);
            }
        },

        async fetchKategorie() {
            try {
                const response = await axios.get(`${API_URL}/kategorie/`);
                this.kategorie = response.data;
            } catch (error) {
                console.error("Błąd ładowania kategorii:", error);
            }
        },

        async fetchNarzedzia() {
            try {
                const response = await axios.get(`${API_URL}/narzedzia/`);
                this.narzedzia = response.data.results || response.data;
            } catch (error) {
                console.error("Błąd ładowania narzędzi:", error);
            }
        },

        async fetchToolsToOrder() {
            this.isLoading = true;

            try {
                const response = await axios.get(`${API_URL}/generator-zamowien/`);
                this.toolsToOrder = response.data;

            } catch (error) {
                console.error("Błąd ładowania narzędzi do zamówienia:", error.response?.data || error.message);
                alert('Wystąpił błąd podczas ładowania danych.');
            } finally {
                this.isLoading = false;
            }
        },

        onKategoriaChange() {
            this.addForm.podkategoria_id = null;
            this.addForm.narzedzie_id = null;
            this.selectedNarzedzie = null;
        },

        onPodkategoriaChange() {
            this.addForm.narzedzie_id = null;
            this.selectedNarzedzie = null;
        },

        onNarzedzieChange() {
            if (this.addForm.narzedzie_id) {
                this.selectedNarzedzie = this.narzedzia.find(n => n.id === this.addForm.narzedzie_id);
            } else {
                this.selectedNarzedzie = null;
            }
        },

        openAddModal() {
            this.addForm = {
                dostawca_id: null,
                kategoria_id: null,
                podkategoria_id: null,
                narzedzie_id: null,
                ilosc_do_zamowienia: 1,
                cena_jednostkowa: 0
            };
            this.selectedNarzedzie = null;
            this.addError = '';

            if (this.modals.addModal) {
                this.modals.addModal.show();
            }
        },

        async saveAdd() {
            this.isAdding = true;
            this.addError = '';

            if (!this.addForm.narzedzie_id) {
                this.addError = 'Wybierz narzędzie';
                this.isAdding = false;
                return;
            }

            try {
                await axios.post(
                    `${API_URL}/generator-zamowien/add/`,
                    this.addForm
                );

                if (this.modals.addModal) {
                    this.modals.addModal.hide();
                }

                await this.fetchToolsToOrder();

            } catch (error) {
                console.error("Błąd dodawania:", error);
                this.addError = error.response?.data?.error || 'Wystąpił błąd podczas dodawania';
            } finally {
                this.isAdding = false;
            }
        },

        openEditModal(tool) {
            this.editForm = {
                id: tool.id,
                element: tool.element,
                dostawca_id: tool.dostawca_id,
                numer_katalogowy: tool.numer_katalogowy || '',
                ilosc_do_zamowienia: tool.ilosc_do_zamowienia,
                cena_jednostkowa: tool.cena_jednostkowa || 0
            };
            this.editError = '';

            if (this.modals.editModal) {
                this.modals.editModal.show();
            }
        },

        async saveEdit() {
            this.isSaving = true;
            this.editError = '';

            try {
                await axios.patch(
                    `${API_URL}/generator-zamowien/${this.editForm.id}/update/`,
                    this.editForm
                );

                if (this.modals.editModal) {
                    this.modals.editModal.hide();
                }

                await this.fetchToolsToOrder();

            } catch (error) {
                console.error("Błąd zapisu:", error);
                this.editError = error.response?.data?.error || 'Wystąpił błąd podczas zapisu';
            } finally {
                this.isSaving = false;
            }
        },

        openDeleteModal(tool) {
            this.deleteItem = tool;

            if (this.modals.deleteModal) {
                this.modals.deleteModal.show();
            }
        },

        async confirmDelete() {
            if (!this.deleteItem) return;

            this.isDeleting = true;

            try {
                await axios.delete(
                    `${API_URL}/generator-zamowien/${this.deleteItem.id}/delete/`
                );

                if (this.modals.deleteModal) {
                    this.modals.deleteModal.hide();
                }

                await this.fetchToolsToOrder();

            } catch (error) {
                console.error("Błąd usuwania:", error);
                alert('Wystąpił błąd podczas usuwania: ' + (error.response?.data?.error || error.message));
            } finally {
                this.isDeleting = false;
                this.deleteItem = null;
            }
        },

        zamowienieGotowe() {
            if (this.toolsToOrder.length === 0) {
                alert('Brak pozycji w generatorze!');
                return;
            }

            // Otwórz modal potwierdzenia
            if (this.modals.confirmOrderModal) {
                this.modals.confirmOrderModal.show();
            }
        },

        async confirmZamowienieGotowe() {
            this.isGenerating = true;

            try {
                const response = await axios.post(`${API_URL}/generator-zamowien/gotowe/`);

                if (response.data.success) {
                    // Zamknij modal
                    if (this.modals.confirmOrderModal) {
                        this.modals.confirmOrderModal.hide();
                    }

                    // Bezpośrednie przekierowanie bez alert()
                    window.location.href = '/zamowienia/';
                }

            } catch (error) {
                console.error("Błąd generowania zamówień:", error);
                alert('Wystąpił błąd: ' + (error.response?.data?.error || error.message));
            } finally {
                this.isGenerating = false;
            }
        }
    }
}).mount('#app');
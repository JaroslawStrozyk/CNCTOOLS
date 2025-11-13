// static/js/main_zakupy.js

const { createApp, nextTick } = Vue; // Dodajemy nextTick
const API_URL = '/api';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            tools: [],
            kategorie: [],
            podkategorie: [],
            invoices: [], // Zawsze inicjuj jako pusta tablica
            damages: [],

            selectedKategoriaId: null,
            selectedPodkategoriaId: null,

            selectedTool: null,
            searchQuery: '',
            isLoadingInvoices: false,
            modals: {},
            isEditMode: false,
            currentTool: {},
            toolImagePreview: null,
            toolImageFile: null,
        };
    },
    computed: {
        filteredTools() {
            let filtered = [...this.tools];

            if (this.selectedPodkategoriaId) {
                filtered = this.filterByPodkategoria(filtered);
            } else if (this.selectedKategoriaId) {
                filtered = this.filterByKategoria(filtered);
            }

            if (this.searchQuery.trim() !== '') {
                filtered = this.filterBySearchQuery(filtered);
            }

            return this.sortToolsByKategoria(filtered);
        },

        filteredPodkategorie() {
            if (!this.selectedKategoriaId) {
                return [];
            }

            const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
            return kategoria ? kategoria.podkategorie : [];
        }
    },
    async mounted() {
        this.initModals();
        await this.fetchInitialData();
    },
    methods: {
        initModals() {
            if (this.$refs.toolModal) {
                this.modals.toolModal = new bootstrap.Modal(this.$refs.toolModal);
            }
        },

        async fetchInitialData() {
            try {
                const [toolsRes, categoriesRes, damagesRes, podkategorieRes] = await Promise.all([
                    axios.get(`${API_URL}/narzedzia-zakupy/`),
                    axios.get(`${API_URL}/kategorie/`),
                    axios.get(`${API_URL}/uszkodzenia/`),
                    axios.get(`${API_URL}/podkategorie/`)
                ]);

                this.tools = toolsRes.data.results || toolsRes.data;
                this.kategorie = categoriesRes.data;
                this.damages = (damagesRes.data.results || damagesRes.data)
                    .sort((a, b) => new Date(b.data_uszkodzenia) - new Date(a.data_uszkodzenia));
                this.podkategorie = podkategorieRes.data;
            } catch (error) {
                console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
            }
        },

        onKategoriaChange() {
            this.selectedPodkategoriaId = null;
        },

        filterByPodkategoria(tools) {
            return tools.filter(tool => {
                return tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId;
            });
        },

        filterByKategoria(tools) {
            return tools.filter(tool => {
                return tool.podkategoria &&
                       tool.podkategoria.kategoria.id === this.selectedKategoriaId;
            });
        },

        filterBySearchQuery(tools) {
            const query = this.searchQuery.toLowerCase();

            return tools.filter(tool => {
                const catalogNumber = tool.numer_katalogowy || '';
                const kategoriaNazwa = tool.podkategoria ?
                    tool.podkategoria.kategoria.nazwa.toLowerCase() : '';
                const podkategoriaNazwa = tool.podkategoria ?
                    tool.podkategoria.nazwa.toLowerCase() : '';

                return kategoriaNazwa.includes(query) ||
                       podkategoriaNazwa.includes(query) ||
                       tool.opis.toLowerCase().includes(query) ||
                       catalogNumber.toLowerCase().includes(query);
            });
        },

        sortToolsByKategoria(tools) {
            return tools.sort((a, b) => {
                const katA = a.podkategoria ? a.podkategoria.kategoria.nazwa.toLowerCase() : '';
                const katB = b.podkategoria ? b.podkategoria.kategoria.nazwa.toLowerCase() : '';

                if (katA < katB) return -1;
                if (katA > katB) return 1;

                const podkatA = a.podkategoria ? a.podkategoria.nazwa.toLowerCase() : '';
                const podkatB = b.podkategoria ? b.podkategoria.nazwa.toLowerCase() : '';

                if (podkatA < podkatB) return -1;
                if (podkatA > podkatB) return 1;

                return 0;
            });
        },

        getStatusClass(tool) {
            const iloscCalkowita = tool.calkowita_ilosc;
            const limitMin = tool.stan_minimalny !== undefined ? tool.stan_minimalny : 0;
            const limitMax = tool.stan_maksymalny !== undefined ? tool.stan_maksymalny : 10;

            if (iloscCalkowita >= limitMax) {
                return 'bg-success'; // Zielony - ilość >= limit maksymalny
            } else if (iloscCalkowita > limitMin && iloscCalkowita < limitMax) {
                return 'bg-warning-dark'; // Ciemno pomarańczowy - ilość między limitami
            } else {
                return 'bg-danger'; // Czerwony - ilość <= limit minimalny
            }
        },

        formatCustomDate(dateString) {
            if (!dateString) {
                return '';
            }

            try {
                const date = new Date(dateString);

                if (isNaN(date.getTime())) {
                    return 'Nieprawidłowa data';
                }

                const pad = (num) => num.toString().padStart(2, '0');
                const year = date.getFullYear();
                const month = pad(date.getMonth() + 1);
                const day = pad(date.getDate());
                const hours = pad(date.getHours());
                const minutes = pad(date.getMinutes());

                return `${year}-${month}-${day} [${hours}:${minutes}]`;
            } catch (e) {
                console.error("Błąd formatowania daty:", dateString, e);
                return 'Błąd daty';
            }
        },

        async selectTool(tool) {
            if (this.selectedTool && this.selectedTool.id === tool.id) {
                this.selectedTool = null;
                this.invoices = [];
                return;
            }

            this.selectedTool = tool;

            try {
                await this.getToolInvoices(tool);
            } catch (error) {
                console.error("Błąd w selectTool po wywołaniu getToolInvoices:", error);
            }
        },

        async getToolInvoices(tool) {
            if (!tool || !tool.id) {
                console.warn("getToolInvoices wywołane bez poprawnego narzędzia.");
                this.invoices = [];
                this.isLoadingInvoices = false;
                return;
            }

            console.log(`Pobieranie faktur dla narzędzia ID: ${tool.id}`);
            this.isLoadingInvoices = true;
            this.invoices = [];

            try {
                const url = `${API_URL}/faktury/?narzedzie_id=${tool.id}`;
                console.log(`Wysyłanie zapytania GET na: ${url}`);
                const response = await axios.get(url);
                console.log("Otrzymano odpowiedź dla faktur:", JSON.parse(JSON.stringify(response.data)));

                let results = this.extractInvoicesFromResponse(response.data);
                console.log("Wyniki po przetworzeniu i filtrowaniu:", JSON.parse(JSON.stringify(results)));

                this.invoices = results.sort((a, b) =>
                    new Date(b.data_wystawienia) - new Date(a.data_wystawienia)
                );

                console.log("Stan this.invoices tuż po przypisaniu:", JSON.parse(JSON.stringify(this.invoices)));

                await nextTick();
                console.log("Stan this.invoices po nextTick:", JSON.parse(JSON.stringify(this.invoices)));

            } catch (error) {
                console.error(`Błąd ładowania faktur dla narzędzia ${tool.id}:`, error.response?.data || error.message);
                this.invoices = [];
            } finally {
                console.log("Zakończono ładowanie faktur, isLoadingInvoices = false");
                this.isLoadingInvoices = false;
            }
        },

        extractInvoicesFromResponse(data) {
            let results = [];

            if (data && typeof data === 'object' && 'results' in data) {
                results = Array.isArray(data.results) ?
                    data.results.filter(item => item !== null) : [];
            } else if (Array.isArray(data)) {
                results = data.filter(item => item !== null);
            } else {
                console.warn("Otrzymano nieoczekiwaną strukturę danych dla faktur:", data);
                results = [];
            }

            return results;
        },

        openToolModal(tool = null) {
            this.isEditMode = !!tool;
            this.toolImagePreview = null;
            this.toolImageFile = null;

            if (this.isEditMode) {
                this.currentTool = {
                    ...tool,
                    podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null
                };

                if (tool.obraz) {
                    this.toolImagePreview = tool.obraz;
                }
            } else {
                this.currentTool = {
                    podkategoria_id: null,
                    opis: '',
                    numer_katalogowy: '',
                    stan_minimalny: 0,
                    stan_maksymalny: 10,
                    obraz: null,
                };
            }

            if (this.modals.toolModal) {
                this.modals.toolModal.show();
            }
        },

        handleToolImageUpload(event) {
            const file = event.target.files[0];

            if (!file) {
                this.toolImageFile = null;
                this.toolImagePreview = (this.isEditMode && this.currentTool.obraz) ?
                    this.currentTool.obraz : null;
                return;
            }

            this.toolImageFile = file;
            this.toolImagePreview = URL.createObjectURL(file);
        },

        async saveTool() {
            const formData = new FormData();
            formData.append('opis', this.currentTool.opis);
            formData.append('stan_minimalny', this.currentTool.stan_minimalny !== undefined ? this.currentTool.stan_minimalny : 0);
            formData.append('stan_maksymalny', this.currentTool.stan_maksymalny !== undefined ? this.currentTool.stan_maksymalny : 10);

            if (this.currentTool.podkategoria_id) {
                formData.append('podkategoria_id', this.currentTool.podkategoria_id);
            }

            if (this.currentTool.numer_katalogowy) {
                formData.append('numer_katalogowy', this.currentTool.numer_katalogowy);
            }

            if (this.toolImageFile) {
                formData.append('obraz', this.toolImageFile);
            }

            const method = this.isEditMode ? 'patch' : 'post';
            const url = this.isEditMode ?
                `${API_URL}/narzedzia/${this.currentTool.id}/` :
                `${API_URL}/narzedzia/`;

            try {
                await axios({
                    method: method,
                    url: url,
                    data: formData,
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (this.modals.toolModal) {
                    this.modals.toolModal.hide();
                }

                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
                alert('Wystąpił błąd podczas zapisu narzędzia: ' +
                      JSON.stringify(error.response?.data || error.message));
            }
        }
    }
}).mount('#app');
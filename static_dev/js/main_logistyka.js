// static/js/main_logistyka.js

const { createApp } = Vue;
const API_URL = '/api';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            tools: [],
            kategorie: [], // Zawiera zagnieżdżone podkategorie
            podkategorie: [], // Płaska lista podkategorii dla modali
            invoices: [],
            damages: [],

            // Filtry
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

            // POPRAWKA: Logika filtrowania
            if (this.selectedPodkategoriaId) {
                // Filtruj dokładnie po tej podkategorii
                filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId);
            } else if (this.selectedKategoriaId) {
                // Filtruj po wszystkich podkategoriach danej kategorii
                filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.kategoria.id === this.selectedKategoriaId);
            }

            if (this.searchQuery.trim() !== '') {
                const lowerCaseQuery = this.searchQuery.toLowerCase();
                filtered = filtered.filter(tool => {
                    const catalogNumber = tool.numer_katalogowy || '';
                    // Sprawdź, czy podkategoria istnieje przed próbą dostępu
                    const kategoriaNazwa = tool.podkategoria ? tool.podkategoria.kategoria.nazwa.toLowerCase() : '';
                    const podkategoriaNazwa = tool.podkategoria ? tool.podkategoria.nazwa.toLowerCase() : '';

                    return (
                        kategoriaNazwa.includes(lowerCaseQuery) ||
                        podkategoriaNazwa.includes(lowerCaseQuery) ||
                        tool.opis.toLowerCase().includes(lowerCaseQuery) ||
                        catalogNumber.toLowerCase().includes(lowerCaseQuery)
                    );
                });
            }

            // Sortowanie po nazwie kategorii, potem podkategorii
            filtered.sort((a, b) => {
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
            return filtered;
        },
        // Zwraca podkategorie dla wybranego filtra kategorii
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
                // Używamy 'narzedzia-logistyka' dla tego panelu
                const [toolsRes, categoriesRes, damagesRes, podkategorieRes] = await Promise.all([
                    axios.get(`${API_URL}/narzedzia-logistyka/`),
                    axios.get(`${API_URL}/kategorie/`),
                    axios.get(`${API_URL}/uszkodzenia/`),
                    axios.get(`${API_URL}/podkategorie/`) // Płaska lista do formularzy
                ]);
                this.tools = toolsRes.data;
                this.kategorie = categoriesRes.data;
                this.damages = damagesRes.data;
                this.podkategorie = podkategorieRes.data;
            } catch (error) {
                console.error("Błąd ładowania danych początkowych:", error);
            }
        },
        // Resetuje filtr podkategorii, gdy zmienia się kategoria główna
        onKategoriaChange() {
            this.selectedPodkategoriaId = null;
        },
        formatCustomDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            const pad = (num) => num.toString().padStart(2, '0');
            return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} [${pad(date.getHours())}:${pad(date.getMinutes())}]`;
        },
        async selectTool(tool) {
            if (this.selectedTool && this.selectedTool.id === tool.id) {
                this.selectedTool = null;
                this.invoices = [];
                return;
            }
            this.selectedTool = tool;
            this.getToolInvoices(tool);
        },
        async getToolInvoices(tool) {
            this.isLoadingInvoices = true;
            this.invoices = [];
            try {
                // Zapytanie o faktury pozostaje bez zmian
                const response = await axios.get(`${API_URL}/faktury/?narzedzie_id=${tool.id}`);
                this.invoices = response.data;
            } catch (error) {
                console.error("Błąd ładowania faktur:", error);
            } finally {
                this.isLoadingInvoices = false;
            }
        },
        openToolModal(tool = null) {
            this.isEditMode = !!tool;
            this.toolImagePreview = null;
            this.toolImageFile = null;

            if (this.isEditMode) {
                this.currentTool = { ...tool, podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null };
                if (tool.obraz) {
                    this.toolImagePreview = tool.obraz;
                }
            } else {
                this.currentTool = {
                    podkategoria_id: null,
                    opis: '',
                    numer_katalogowy: '',
                    limit_minimalny: 0,
                    obraz: null,
                };
            }
            this.modals.toolModal.show();
        },
        handleToolImageUpload(event) {
            const file = event.target.files[0];
            if (!file) {
                this.toolImageFile = null;
                this.toolImagePreview = (this.isEditMode && this.currentTool.obraz) ? this.currentTool.obraz : null;
                return;
            }
            this.toolImageFile = file;
            this.toolImagePreview = URL.createObjectURL(file);
        },
        async saveTool() {
            const formData = new FormData();
            formData.append('opis', this.currentTool.opis);
            formData.append('limit_minimalny', this.currentTool.limit_minimalny);

            // POPRAWKA: Wysyłaj podkategoria_id tylko jeśli jest wybrane
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
            // Ważne: zapis idzie do głównego endpointu 'narzedzia', nie 'narzedzia-logistyka'
            const url = this.isEditMode ? `${API_URL}/narzedzia/${this.currentTool.id}/` : `${API_URL}/narzedzia/`;

            try {
                await axios({
                    method: method,
                    url: url,
                    data: formData,
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                this.modals.toolModal.hide();
                await this.fetchInitialData();
            } catch (error) {
                console.error("Błąd zapisu typu narzędzia:", error.response.data);
                alert('Wystąpił błąd podczas zapisu: ' + JSON.stringify(error.response.data));
            }
        }
    }
}).mount('#app');
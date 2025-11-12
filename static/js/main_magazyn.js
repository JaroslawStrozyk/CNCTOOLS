/**
 * Panel Magazyniera - Frontend
 * Zarządzanie narzędziami CNC
 */

const { createApp } = Vue;
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
            machines: [],
            pracownicy: [],
            faktury: [],
            zamowienia: [],
            usagesInUse: [],
            toolInstances: [],
            toolHistory: [],
            locations: [],

            selectedKategoriaId: null,
            selectedPodkategoriaId: null,
            selectedToolForDetails: null,
            selectedMaszynaFilter: null,

            activeTab: 'details',
            isLoadingDetails: false,
            isLoadingHistory: false,
            isEditMode: false,
            isSavingInstance: false,

            error: '',
            issueData: {
                machine_id: null,
                instance: null,
                pracownik_id: null
            },
            currentTool: {},
            returnStatus: 'uzywane',
            usageToReturnId: null,
            modals: {},
            searchQuery: '',
            toolValidationError: '',

            instanceModal: {
                instance: null,
                title: '',
                mode: 'add',
                currentInstance: {
                    id: null,
                    narzedzie_typ_id: null,
                    stan: 'nowe',
                    lokalizacja_id: null,
                    faktura_zakupu_id: null,
                    zamowienie_id: null,
                    ilosc: 1
                },
                errorMessage: '',
            },

            instanceToDelete: null,
            deleteModalMessage: '',

            toolImagePreview: null,
            toolImageFile: null,
        };
    },

    computed: {
        filteredTools() {
            let filtered = this.tools;

            if (this.selectedPodkategoriaId) {
                filtered = this.filterByPodkategoria(filtered);
            } else if (this.selectedKategoriaId) {
                filtered = this.filterByKategoria(filtered);
            }

            if (this.searchQuery.trim() !== '') {
                filtered = this.filterBySearchQuery(filtered);
            }

            return filtered;
        },

        inUseInstanceIds() {
            return new Set(this.usagesInUse.map(usage => usage.egzemplarz.id));
        },

        filteredPodkategorie() {
            if (!this.selectedKategoriaId) {
                return [];
            }

            const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
            return kategoria ? kategoria.podkategorie : [];
        },

        unsettledInvoices() {
            return this.faktury
                .filter(f => !f.rozliczone)
                .sort((a, b) => new Date(b.data_wystawienia) - new Date(a.data_wystawienia));
        },

        sortedLocations() {
            return [...this.locations].sort((a, b) => {
                if (a.szafa < b.szafa) return -1;
                if (a.szafa > b.szafa) return 1;

                const kolumnaA = parseInt(a.kolumna) || 0;
                const kolumnaB = parseInt(b.kolumna) || 0;
                if (kolumnaA < kolumnaB) return -1;
                if (kolumnaA > kolumnaB) return 1;

                const polkaA = parseInt(a.polka) || 0;
                const polkaB = parseInt(b.polka) || 0;
                return polkaA - polkaB;
            });
        },

        filteredUsagesInUse() {
            if (!this.selectedMaszynaFilter) {
                return this.usagesInUse;
            }

            return this.usagesInUse.filter(usage => {
                return usage.maszyna && usage.maszyna.id === this.selectedMaszynaFilter;
            });
        }
    },

    async mounted() {
        this.initModals();
        await this.fetchInitialData();
    },

    methods: {
        initModals() {
            const modalRefs = ['issueModal', 'returnModal', 'toolModal', 'instanceModal', 'deleteInstanceModal'];

            modalRefs.forEach(ref => {
                if (this.$refs[ref]) {
                    const modalInstance = new bootstrap.Modal(this.$refs[ref]);

                    if (ref === 'instanceModal') {
                        this.instanceModal.instance = modalInstance;
                    } else {
                        this.modals[ref] = modalInstance;
                    }
                } else {
                    console.warn(`Modal ref "${ref}" not found during init.`);
                }
            });
        },

        async fetchInitialData() {
            this.isLoading = true;

            try {
                const responses = await this.fetchAllApiData();
                this.assignFetchedData(responses);
            } catch (error) {
                this.handleFetchError(error);
            } finally {
                this.isLoading = false;
            }
        },

        async fetchAllApiData() {
            const [
                toolsRes,
                categoriesRes,
                machinesRes,
                usagesRes,
                locationsRes,
                podkategorieRes,
                pracownicyRes,
                fakturyRes,
                zamowieniaRes
            ] = await Promise.all([
                axios.get(`${API_URL}/narzedzia/`),
                axios.get(`${API_URL}/kategorie/`),
                axios.get(`${API_URL}/maszyny/`),
                axios.get(`${API_URL}/historia/?w_uzyciu=true`),
                axios.get(`${API_URL}/lokalizacje/`),
                axios.get(`${API_URL}/podkategorie/`),
                axios.get(`${API_URL}/pracownicy/`),
                axios.get(`${API_URL}/faktury/`),
                axios.get(`${API_URL}/zamowienia/`)
            ]);

            return {
                toolsRes,
                categoriesRes,
                machinesRes,
                usagesRes,
                locationsRes,
                podkategorieRes,
                pracownicyRes,
                fakturyRes,
                zamowieniaRes
            };
        },

        assignFetchedData(responses) {
            this.tools = responses.toolsRes.data.results || responses.toolsRes.data;
            this.kategorie = responses.categoriesRes.data;
            this.machines = responses.machinesRes.data;
            this.usagesInUse = responses.usagesRes.data.results || responses.usagesRes.data;
            this.locations = responses.locationsRes.data;
            this.podkategorie = responses.podkategorieRes.data;
            this.pracownicy = responses.pracownicyRes.data.results || responses.pracownicyRes.data;
            this.faktury = responses.fakturyRes.data.results || responses.fakturyRes.data;
            this.zamowienia = responses.zamowieniaRes.data.results || responses.zamowieniaRes.data;
        },

        handleFetchError(error) {
            console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
            alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
        },

        onKategoriaChange() {
            this.selectedPodkategoriaId = null;
        },

        async selectTool(tool) {
            if (this.selectedToolForDetails && this.selectedToolForDetails.id === tool.id) {
                this.selectedToolForDetails = null;
                this.toolInstances = [];
                this.toolHistory = [];
                return;
            }

            this.selectedToolForDetails = tool;
            this.activeTab = 'details';

            await this.getToolInstances(tool);
            await this.getToolHistory(tool);
        },

        async getToolInstances(tool) {
            this.isLoadingDetails = true;

            try {
                const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
                const instances = response.data.results || response.data;
                this.toolInstances = instances.sort((a, b) => b.id - a.id);
            } catch (error) {
                console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
                this.toolInstances = [];
            } finally {
                this.isLoadingDetails = false;
            }
        },

        async getToolHistory(tool) {
            this.isLoadingHistory = true;

            try {
                const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
                const history = response.data.results || response.data;
                this.toolHistory = history.sort((a, b) =>
                    new Date(b.data_wydania) - new Date(a.data_wydania)
                );
            } catch (error) {
                console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
                this.toolHistory = [];
            } finally {
                this.isLoadingHistory = false;
            }
        },

        filterByPodkategoria(tools) {
            return tools.filter(tool => {
                return tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId;
            });
        },

        filterByKategoria(tools) {
            return tools.filter(tool => {
                if (!tool.podkategoria) return false;

                const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
                if (!kategoria) return false;

                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
            });
        },

        filterBySearchQuery(tools) {
            const query = this.searchQuery.trim().toLowerCase();

            return tools.filter(tool => {
                const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
                const kategoriaNazwa = this.getKategoriaNazwa(tool);
                const podkategoriaNazwa = this.getPodkategoriaNazwa(tool);
                const opisNazwa = tool.opis.toLowerCase();

                return kategoriaNazwa.includes(query) ||
                       podkategoriaNazwa.includes(query) ||
                       opisNazwa.includes(query) ||
                       catalogNumber.includes(query);
            });
        },

        getKategoriaNazwa(tool) {
            if (!tool.podkategoria || !tool.podkategoria.kategoria_nazwa) {
                return '';
            }
            return tool.podkategoria.kategoria_nazwa.toLowerCase();
        },

        getPodkategoriaNazwa(tool) {
            if (!tool.podkategoria) {
                return '';
            }
            return tool.podkategoria.nazwa.toLowerCase();
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

                const year = date.getFullYear();
                const month = this.padNumber(date.getMonth() + 1);
                const day = this.padNumber(date.getDate());
                const hours = this.padNumber(date.getHours());
                const minutes = this.padNumber(date.getMinutes());

                return `${year}-${month}-${day} [${hours}:${minutes}]`;
            } catch (e) {
                console.error("Błąd formatowania daty:", dateString, e);
                return 'Błąd daty';
            }
        },

        padNumber(num) {
            return num.toString().padStart(2, '0');
        },

        getInstanceStatusClass(stan) {
            const statusMap = {
                'nowe': 'success',
                'uzywane': 'primary',
                'uszkodzone': 'danger',
                'uszkodzone_regeneracja': 'warning'
            };
            return statusMap[stan] || 'secondary';
        },

        getInstanceStatusLabel(stan) {
            const labelMap = {
                'nowe': 'Nowe',
                'uzywane': 'Używane',
                'uszkodzone': 'Uszkodzone',
                'uszkodzone_regeneracja': 'Uszkodzone do regeneracji'
            };
            return labelMap[stan] || stan;
        },

        showIssueModal(instance) {
            this.issueData.instance = instance;
            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
            this.issueData.pracownik_id = null;
            this.error = '';

            if (this.modals.issueModal) {
                this.modals.issueModal.show();
            } else {
                console.error("Modal 'issueModal' not initialized!");
            }
        },

        async issueTool() {
            if (!this.issueData.pracownik_id) {
                this.error = "Wybierz pracownika.";
                return;
            }

            this.error = '';

            try {
                await axios.post(`${API_URL}/historia/wydanie/`, {
                    egzemplarz_id: this.issueData.instance.id,
                    maszyna_id: this.issueData.machine_id,
                    pracownik_id: this.issueData.pracownik_id
                });

                if (this.modals.issueModal) {
                    this.modals.issueModal.hide();
                }

                await this.fetchInitialData();

                if (this.selectedToolForDetails) {
                    await this.getToolInstances(this.selectedToolForDetails);
                    await this.getToolHistory(this.selectedToolForDetails);
                }
            } catch (error) {
                console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
                this.error = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
            }
        },

        showReturnModal(usageId) {
            this.usageToReturnId = usageId;
            this.returnStatus = 'uzywane';

            if (this.modals.returnModal) {
                this.modals.returnModal.show();
            } else {
                console.error("Modal 'returnModal' not initialized!");
            }
        },

        async confirmReturnTool() {
            try {
                await axios.post(`${API_URL}/historia/${this.usageToReturnId}/zwrot/`, {
                    stan_po_zwrocie: this.returnStatus
                });

                if (this.modals.returnModal) {
                    this.modals.returnModal.hide();
                }

                await this.fetchInitialData();

                if (this.selectedToolForDetails) {
                    await this.getToolInstances(this.selectedToolForDetails);
                    await this.getToolHistory(this.selectedToolForDetails);
                }
            } catch (error) {
                console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
                alert("Wystąpił błąd podczas zwracania narzędzia.");
            }
        },

        openToolModal(tool = null) {
            this.isEditMode = !!tool;
            this.toolImagePreview = null;
            this.toolImageFile = null;
            this.toolValidationError = '';

            if (this.isEditMode) {
                this.currentTool = {
                    ...tool,
                    podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
                    domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
                    opakowanie: tool.opakowanie || 'szt',
                    ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1
                };
                if (tool.obraz) {
                    this.toolImagePreview = tool.obraz;
                }
            } else {
                this.currentTool = {
                    podkategoria_id: null,
                    opis: '',
                    numer_katalogowy: '',
                    domyslna_lokalizacja_id: null,
                    obraz: null,
                    opakowanie: 'szt',
                    ilosc_w_opakowaniu: 1
                };
            }

            if (this.modals.toolModal) {
                this.modals.toolModal.show();
            } else {
                console.error("Modal 'toolModal' not initialized!");
            }
        },

        onOpakowanieChange() {
            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
                this.currentTool.ilosc_w_opakowaniu = 2;
            } else if (this.currentTool.opakowanie === 'szt') {
                this.currentTool.ilosc_w_opakowaniu = 1;
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
            this.toolValidationError = '';

            // Walidacja
            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
                this.toolValidationError = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
                return;
            }

            const formData = new FormData();
            formData.append('opis', this.currentTool.opis);
            formData.append('opakowanie', this.currentTool.opakowanie || 'szt');
            formData.append('ilosc_w_opakowaniu', this.currentTool.ilosc_w_opakowaniu || 1);

            if (this.currentTool.podkategoria_id) {
                formData.append('podkategoria_id', this.currentTool.podkategoria_id);
            }

            if (this.currentTool.numer_katalogowy) {
                formData.append('numer_katalogowy', this.currentTool.numer_katalogowy);
            }

            if (this.currentTool.domyslna_lokalizacja_id) {
                formData.append('domyslna_lokalizacja_id', this.currentTool.domyslna_lokalizacja_id);
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
                this.toolValidationError = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
            }
        },

        openInstanceModal(mode, instance = null) {
            this.instanceModal.mode = mode;
            this.instanceModal.errorMessage = '';

            if (mode === 'add') {
                this.setupAddInstanceMode();
            } else {
                this.setupEditInstanceMode(instance);
            }

            if (this.instanceModal.instance) {
                this.instanceModal.instance.show();
            } else {
                console.error("Modal 'instanceModal' not initialized!");
            }
        },

        setupAddInstanceMode() {
            this.instanceModal.title = 'Dodaj nowy egzemplarz';
            this.instanceModal.currentInstance = {
                id: null,
                narzedzie_typ_id: this.selectedToolForDetails.id,
                stan: 'nowe',
                lokalizacja_id: null,
                faktura_zakupu_id: null,
                zamowienie_id: null,
                ilosc: 1
            };

            // Priorytet 1: Domyślna lokalizacja z typu narzędzia
            if (this.selectedToolForDetails.domyslna_lokalizacja) {
                this.instanceModal.currentInstance.lokalizacja_id = this.selectedToolForDetails.domyslna_lokalizacja.id;
            }
            // Priorytet 2: Lokalizacja ostatniego egzemplarza
            else if (Array.isArray(this.toolInstances) && this.toolInstances.length > 0) {
                const lastInstance = this.toolInstances[0];
                if (lastInstance && lastInstance.lokalizacja) {
                    this.instanceModal.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
                }
            }
        },

        setupEditInstanceMode(instance) {
            this.instanceModal.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
            this.instanceModal.currentInstance = {
                ...instance,
                lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
                faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
                zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
                ilosc: 1
            };
        },

        async saveInstance() {
            this.isSavingInstance = true;
            this.instanceModal.errorMessage = '';

            const method = this.instanceModal.mode === 'add' ? 'post' : 'patch';
            const url = this.instanceModal.mode === 'add' ?
                `${API_URL}/egzemplarze/` :
                `${API_URL}/egzemplarze/${this.instanceModal.currentInstance.id}/`;

            const payload = {
                stan: this.instanceModal.currentInstance.stan,
                lokalizacja_id: this.instanceModal.currentInstance.lokalizacja_id,
                narzedzie_typ_id: this.instanceModal.currentInstance.narzedzie_typ_id,
                faktura_zakupu_id: this.instanceModal.currentInstance.faktura_zakupu_id,
                zamowienie_id: this.instanceModal.currentInstance.zamowienie_id
            };

            const ilosc = this.instanceModal.currentInstance.ilosc;

            if (this.instanceModal.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
                this.instanceModal.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
                this.isSavingInstance = false;
                return;
            }

            try {
                if (this.instanceModal.mode === 'add' && ilosc > 1) {
                    await this.createMultipleInstances(url, payload, ilosc);
                } else {
                    await this.createOrUpdateInstance(method, url, payload);
                }

                if (this.instanceModal.instance) {
                    this.instanceModal.instance.hide();
                }

                if (this.selectedToolForDetails) {
                    await this.getToolInstances(this.selectedToolForDetails);
                }

                await this.fetchInitialData();

            } catch (error) {
                this.handleSaveInstanceError(error, ilosc);
            } finally {
                this.isSavingInstance = false;
            }
        },

        async createMultipleInstances(url, payload, ilosc) {
            const requests = [];
            for (let i = 0; i < ilosc; i++) {
                requests.push(axios.post(url, payload));
            }
            const responses = await Promise.all(requests);
            console.log(`Pomyślnie dodano ${responses.length} egzemplarzy.`);
        },

        async createOrUpdateInstance(method, url, payload) {
            await axios({ method, url, data: payload });
            const action = this.instanceModal.mode === 'add' ? 'dodano' : 'zaktualizowano';
            console.log(`Pomyślnie ${action} egzemplarz.`);
        },

        handleSaveInstanceError(error, ilosc) {
            console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);

            let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';

            if (error.response?.data) {
                if (typeof error.response.data === 'object') {
                    errorMsg = Object.entries(error.response.data)
                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
                        .join('; ');
                } else if (Array.isArray(error.response.data) && ilosc > 1) {
                    const firstError = error.response.data[0];
                    errorMsg = `Błąd przy dodawaniu seryjnym: ${JSON.stringify(firstError)}`;
                } else {
                    errorMsg = `Błąd: ${error.response.data}`;
                }
            } else if (error.message) {
                const prefix = ilosc > 1 ? 'podczas dodawania seryjnego' : '';
                errorMsg = `Wystąpił błąd sieci lub serwera ${prefix}: ${error.message}.`;
            }

            this.instanceModal.errorMessage = errorMsg;
        },

        openDeleteInstanceModal(instance) {
            this.instanceToDelete = instance;

            const toolName = instance.narzedzie_typ.podkategoria ?
                `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}` :
                instance.narzedzie_typ.opis;

            if (instance.stan === 'uszkodzone') {
                this.deleteModalMessage = `Ten egzemplarz (<strong>${toolName}</strong>) jest oznaczony jako uszkodzony. Zostanie przeniesiony do archiwum. Czy chcesz kontynuować?`;
            } else {
                this.deleteModalMessage = `Czy na pewno chcesz trwale usunąć egzemplarz: <strong>${toolName}</strong>?`;
            }

            if (this.modals.deleteInstanceModal) {
                this.modals.deleteInstanceModal.show();
            } else {
                console.error("Modal 'deleteInstanceModal' not initialized!");
            }
        },

        async confirmDeleteInstance() {
            if (!this.instanceToDelete) {
                return;
            }

            try {
                await axios.delete(`${API_URL}/egzemplarze/${this.instanceToDelete.id}/`);

                if (this.modals.deleteInstanceModal) {
                    this.modals.deleteInstanceModal.hide();
                }

                if (this.selectedToolForDetails) {
                    await this.getToolInstances(this.selectedToolForDetails);
                }

                await this.fetchInitialData();
                this.instanceToDelete = null;
            } catch (error) {
                console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);

                if (this.modals.deleteInstanceModal) {
                    this.modals.deleteInstanceModal.hide();
                }

                alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
            }
        },
    }
}).mount('#app');

































///**
// * Panel Magazyniera - Frontend
// * Zarządzanie narzędziami CNC
// */
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//
//    data() {
//        return {
//            tools: [],
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            pracownicy: [],
//            faktury: [],
//            zamowienia: [],
//            usagesInUse: [],
//            toolInstances: [],
//            toolHistory: [],
//            locations: [],
//
//            selectedKategoriaId: null,
//            selectedPodkategoriaId: null,
//            selectedToolForDetails: null,
//            selectedMaszynaFilter: null,
//
//            activeTab: 'details',
//            isLoadingDetails: false,
//            isLoadingHistory: false,
//            isEditMode: false,
//            isSavingInstance: false,
//
//            error: '',
//            issueData: {
//                machine_id: null,
//                instance: null,
//                pracownik_id: null
//            },
//            currentTool: {},
//            returnStatus: 'uzywane',
//            usageToReturnId: null,
//            modals: {},
//            searchQuery: '',
//            toolValidationError: '',
//
//            instanceModal: {
//                instance: null,
//                title: '',
//                mode: 'add',
//                currentInstance: {
//                    id: null,
//                    narzedzie_typ_id: null,
//                    stan: 'nowe',
//                    lokalizacja_id: null,
//                    faktura_zakupu_id: null,
//                    zamowienie_id: null,
//                    ilosc: 1
//                },
//                errorMessage: '',
//            },
//
//            instanceToDelete: null,
//            deleteModalMessage: '',
//
//            toolImagePreview: null,
//            toolImageFile: null,
//        };
//    },
//
//    computed: {
//        filteredTools() {
//            let filtered = this.tools;
//
//            if (this.selectedPodkategoriaId) {
//                filtered = this.filterByPodkategoria(filtered);
//            } else if (this.selectedKategoriaId) {
//                filtered = this.filterByKategoria(filtered);
//            }
//
//            if (this.searchQuery.trim() !== '') {
//                filtered = this.filterBySearchQuery(filtered);
//            }
//
//            return filtered;
//        },
//
//        inUseInstanceIds() {
//            return new Set(this.usagesInUse.map(usage => usage.egzemplarz.id));
//        },
//
//        filteredPodkategorie() {
//            if (!this.selectedKategoriaId) {
//                return [];
//            }
//
//            const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kategoria ? kategoria.podkategorie : [];
//        },
//
//        unsettledInvoices() {
//            return this.faktury
//                .filter(f => !f.rozliczone)
//                .sort((a, b) => new Date(b.data_wystawienia) - new Date(a.data_wystawienia));
//        },
//
//        sortedLocations() {
//            return [...this.locations].sort((a, b) => {
//                if (a.szafa < b.szafa) return -1;
//                if (a.szafa > b.szafa) return 1;
//
//                const kolumnaA = parseInt(a.kolumna) || 0;
//                const kolumnaB = parseInt(b.kolumna) || 0;
//                if (kolumnaA < kolumnaB) return -1;
//                if (kolumnaA > kolumnaB) return 1;
//
//                const polkaA = parseInt(a.polka) || 0;
//                const polkaB = parseInt(b.polka) || 0;
//                return polkaA - polkaB;
//            });
//        },
//
//        filteredUsagesInUse() {
//            if (!this.selectedMaszynaFilter) {
//                return this.usagesInUse;
//            }
//
//            return this.usagesInUse.filter(usage => {
//                return usage.maszyna && usage.maszyna.id === this.selectedMaszynaFilter;
//            });
//        }
//    },
//
//    async mounted() {
//        this.initModals();
//        await this.fetchInitialData();
//    },
//
//    methods: {
//        initModals() {
//            const modalRefs = ['issueModal', 'returnModal', 'toolModal', 'instanceModal', 'deleteInstanceModal'];
//
//            modalRefs.forEach(ref => {
//                if (this.$refs[ref]) {
//                    const modalInstance = new bootstrap.Modal(this.$refs[ref]);
//
//                    if (ref === 'instanceModal') {
//                        this.instanceModal.instance = modalInstance;
//                    } else {
//                        this.modals[ref] = modalInstance;
//                    }
//                } else {
//                    console.warn(`Modal ref "${ref}" not found during init.`);
//                }
//            });
//        },
//
//        async fetchInitialData() {
//            this.isLoading = true;
//
//            try {
//                const responses = await this.fetchAllApiData();
//                this.assignFetchedData(responses);
//            } catch (error) {
//                this.handleFetchError(error);
//            } finally {
//                this.isLoading = false;
//            }
//        },
//
//        async fetchAllApiData() {
//            const [
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            ] = await Promise.all([
//                axios.get(`${API_URL}/narzedzia/`),
//                axios.get(`${API_URL}/kategorie/`),
//                axios.get(`${API_URL}/maszyny/`),
//                axios.get(`${API_URL}/historia/?w_uzyciu=true`),
//                axios.get(`${API_URL}/lokalizacje/`),
//                axios.get(`${API_URL}/podkategorie/`),
//                axios.get(`${API_URL}/pracownicy/`),
//                axios.get(`${API_URL}/faktury/`),
//                axios.get(`${API_URL}/zamowienia/`)
//            ]);
//
//            return {
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            };
//        },
//
//        assignFetchedData(responses) {
//            this.tools = responses.toolsRes.data.results || responses.toolsRes.data;
//            this.kategorie = responses.categoriesRes.data;
//            this.machines = responses.machinesRes.data;
//            this.usagesInUse = responses.usagesRes.data.results || responses.usagesRes.data;
//            this.locations = responses.locationsRes.data;
//            this.podkategorie = responses.podkategorieRes.data;
//            this.pracownicy = responses.pracownicyRes.data.results || responses.pracownicyRes.data;
//            this.faktury = responses.fakturyRes.data.results || responses.fakturyRes.data;
//            this.zamowienia = responses.zamowieniaRes.data.results || responses.zamowieniaRes.data;
//        },
//
//        handleFetchError(error) {
//            console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
//            alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
//        },
//
//        onKategoriaChange() {
//            this.selectedPodkategoriaId = null;
//        },
//
//        async selectTool(tool) {
//            if (this.selectedToolForDetails && this.selectedToolForDetails.id === tool.id) {
//                this.selectedToolForDetails = null;
//                this.toolInstances = [];
//                this.toolHistory = [];
//                return;
//            }
//
//            this.selectedToolForDetails = tool;
//            this.activeTab = 'details';
//
//            await this.getToolInstances(tool);
//            await this.getToolHistory(tool);
//        },
//
//        async getToolInstances(tool) {
//            this.isLoadingDetails = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
//                const instances = response.data.results || response.data;
//                this.toolInstances = instances.sort((a, b) => b.id - a.id);
//            } catch (error) {
//                console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
//                this.toolInstances = [];
//            } finally {
//                this.isLoadingDetails = false;
//            }
//        },
//
//        async getToolHistory(tool) {
//            this.isLoadingHistory = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
//                const history = response.data.results || response.data;
//                this.toolHistory = history.sort((a, b) =>
//                    new Date(b.data_wydania) - new Date(a.data_wydania)
//                );
//            } catch (error) {
//                console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
//                this.toolHistory = [];
//            } finally {
//                this.isLoadingHistory = false;
//            }
//        },
//
//        filterByPodkategoria(tools) {
//            return tools.filter(tool => {
//                return tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId;
//            });
//        },
//
//        filterByKategoria(tools) {
//            return tools.filter(tool => {
//                if (!tool.podkategoria) return false;
//
//                const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                if (!kategoria) return false;
//
//                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
//            });
//        },
//
//        filterBySearchQuery(tools) {
//            const query = this.searchQuery.trim().toLowerCase();
//
//            return tools.filter(tool => {
//                const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
//                const kategoriaNazwa = this.getKategoriaNazwa(tool);
//                const podkategoriaNazwa = this.getPodkategoriaNazwa(tool);
//                const opisNazwa = tool.opis.toLowerCase();
//
//                return kategoriaNazwa.includes(query) ||
//                       podkategoriaNazwa.includes(query) ||
//                       opisNazwa.includes(query) ||
//                       catalogNumber.includes(query);
//            });
//        },
//
//        getKategoriaNazwa(tool) {
//            if (!tool.podkategoria || !tool.podkategoria.kategoria_nazwa) {
//                return '';
//            }
//            return tool.podkategoria.kategoria_nazwa.toLowerCase();
//        },
//
//        getPodkategoriaNazwa(tool) {
//            if (!tool.podkategoria) {
//                return '';
//            }
//            return tool.podkategoria.nazwa.toLowerCase();
//        },
//
//        formatCustomDate(dateString) {
//            if (!dateString) {
//                return '';
//            }
//
//            try {
//                const date = new Date(dateString);
//
//                if (isNaN(date.getTime())) {
//                    return 'Nieprawidłowa data';
//                }
//
//                const year = date.getFullYear();
//                const month = this.padNumber(date.getMonth() + 1);
//                const day = this.padNumber(date.getDate());
//                const hours = this.padNumber(date.getHours());
//                const minutes = this.padNumber(date.getMinutes());
//
//                return `${year}-${month}-${day} [${hours}:${minutes}]`;
//            } catch (e) {
//                console.error("Błąd formatowania daty:", dateString, e);
//                return 'Błąd daty';
//            }
//        },
//
//        padNumber(num) {
//            return num.toString().padStart(2, '0');
//        },
//
//        getInstanceStatusClass(stan) {
//            const statusMap = {
//                'nowe': 'success',
//                'uzywane': 'primary',
//                'uszkodzone': 'danger',
//                'uszkodzone_regeneracja': 'warning'
//            };
//            return statusMap[stan] || 'secondary';
//        },
//
//        showIssueModal(instance) {
//            this.issueData.instance = instance;
//            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
//            this.issueData.pracownik_id = null;
//            this.error = '';
//
//            if (this.modals.issueModal) {
//                this.modals.issueModal.show();
//            } else {
//                console.error("Modal 'issueModal' not initialized!");
//            }
//        },
//
//        async issueTool() {
//            if (!this.issueData.pracownik_id) {
//                this.error = "Wybierz pracownika.";
//                return;
//            }
//
//            this.error = '';
//
//            try {
//                await axios.post(`${API_URL}/historia/wydanie/`, {
//                    egzemplarz_id: this.issueData.instance.id,
//                    maszyna_id: this.issueData.machine_id,
//                    pracownik_id: this.issueData.pracownik_id
//                });
//
//                if (this.modals.issueModal) {
//                    this.modals.issueModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                    await this.getToolHistory(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
//                this.error = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
//            }
//        },
//
//        showReturnModal(usageId) {
//            this.usageToReturnId = usageId;
//            this.returnStatus = 'uzywane';
//
//            if (this.modals.returnModal) {
//                this.modals.returnModal.show();
//            } else {
//                console.error("Modal 'returnModal' not initialized!");
//            }
//        },
//
//        async confirmReturnTool() {
//            try {
//                await axios.post(`${API_URL}/historia/${this.usageToReturnId}/zwrot/`, {
//                    stan_po_zwrocie: this.returnStatus
//                });
//
//                if (this.modals.returnModal) {
//                    this.modals.returnModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                    await this.getToolHistory(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
//                alert("Wystąpił błąd podczas zwracania narzędzia.");
//            }
//        },
//
//        openToolModal(tool = null) {
//            this.isEditMode = !!tool;
//            this.toolImagePreview = null;
//            this.toolImageFile = null;
//            this.toolValidationError = '';
//
//            if (this.isEditMode) {
//                this.currentTool = {
//                    ...tool,
//                    podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
//                    domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
//                    opakowanie: tool.opakowanie || 'szt',
//                    ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1
//                };
//                if (tool.obraz) {
//                    this.toolImagePreview = tool.obraz;
//                }
//            } else {
//                this.currentTool = {
//                    podkategoria_id: null,
//                    opis: '',
//                    numer_katalogowy: '',
//                    domyslna_lokalizacja_id: null,
//                    obraz: null,
//                    opakowanie: 'szt',
//                    ilosc_w_opakowaniu: 1
//                };
//            }
//
//            if (this.modals.toolModal) {
//                this.modals.toolModal.show();
//            } else {
//                console.error("Modal 'toolModal' not initialized!");
//            }
//        },
//
//        onOpakowanieChange() {
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.currentTool.ilosc_w_opakowaniu = 2;
//            } else if (this.currentTool.opakowanie === 'szt') {
//                this.currentTool.ilosc_w_opakowaniu = 1;
//            }
//        },
//
//        handleToolImageUpload(event) {
//            const file = event.target.files[0];
//
//            if (!file) {
//                this.toolImageFile = null;
//                this.toolImagePreview = (this.isEditMode && this.currentTool.obraz) ?
//                    this.currentTool.obraz : null;
//                return;
//            }
//
//            this.toolImageFile = file;
//            this.toolImagePreview = URL.createObjectURL(file);
//        },
//
//        async saveTool() {
//            this.toolValidationError = '';
//
//            // Walidacja
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.toolValidationError = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
//                return;
//            }
//
//            const formData = new FormData();
//            formData.append('opis', this.currentTool.opis);
//            formData.append('opakowanie', this.currentTool.opakowanie || 'szt');
//            formData.append('ilosc_w_opakowaniu', this.currentTool.ilosc_w_opakowaniu || 1);
//
//            if (this.currentTool.podkategoria_id) {
//                formData.append('podkategoria_id', this.currentTool.podkategoria_id);
//            }
//
//            if (this.currentTool.numer_katalogowy) {
//                formData.append('numer_katalogowy', this.currentTool.numer_katalogowy);
//            }
//
//            if (this.currentTool.domyslna_lokalizacja_id) {
//                formData.append('domyslna_lokalizacja_id', this.currentTool.domyslna_lokalizacja_id);
//            }
//
//            if (this.toolImageFile) {
//                formData.append('obraz', this.toolImageFile);
//            }
//
//            const method = this.isEditMode ? 'patch' : 'post';
//            const url = this.isEditMode ?
//                `${API_URL}/narzedzia/${this.currentTool.id}/` :
//                `${API_URL}/narzedzia/`;
//
//            try {
//                await axios({
//                    method: method,
//                    url: url,
//                    data: formData,
//                    headers: { 'Content-Type': 'multipart/form-data' }
//                });
//
//                if (this.modals.toolModal) {
//                    this.modals.toolModal.hide();
//                }
//
//                await this.fetchInitialData();
//            } catch (error) {
//                console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
//                this.toolValidationError = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
//            }
//        },
//
//        openInstanceModal(mode, instance = null) {
//            this.instanceModal.mode = mode;
//            this.instanceModal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.setupAddInstanceMode();
//            } else {
//                this.setupEditInstanceMode(instance);
//            }
//
//            if (this.instanceModal.instance) {
//                this.instanceModal.instance.show();
//            } else {
//                console.error("Modal 'instanceModal' not initialized!");
//            }
//        },
//
//        setupAddInstanceMode() {
//            this.instanceModal.title = 'Dodaj nowy egzemplarz';
//            this.instanceModal.currentInstance = {
//                id: null,
//                narzedzie_typ_id: this.selectedToolForDetails.id,
//                stan: 'nowe',
//                lokalizacja_id: null,
//                faktura_zakupu_id: null,
//                zamowienie_id: null,
//                ilosc: 1
//            };
//
//            // Priorytet 1: Domyślna lokalizacja z typu narzędzia
//            if (this.selectedToolForDetails.domyslna_lokalizacja) {
//                this.instanceModal.currentInstance.lokalizacja_id = this.selectedToolForDetails.domyslna_lokalizacja.id;
//            }
//            // Priorytet 2: Lokalizacja ostatniego egzemplarza
//            else if (Array.isArray(this.toolInstances) && this.toolInstances.length > 0) {
//                const lastInstance = this.toolInstances[0];
//                if (lastInstance && lastInstance.lokalizacja) {
//                    this.instanceModal.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
//                }
//            }
//        },
//
//        setupEditInstanceMode(instance) {
//            this.instanceModal.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
//            this.instanceModal.currentInstance = {
//                ...instance,
//                lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
//                faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
//                zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
//                ilosc: 1
//            };
//        },
//
//        async saveInstance() {
//            this.isSavingInstance = true;
//            this.instanceModal.errorMessage = '';
//
//            const method = this.instanceModal.mode === 'add' ? 'post' : 'patch';
//            const url = this.instanceModal.mode === 'add' ?
//                `${API_URL}/egzemplarze/` :
//                `${API_URL}/egzemplarze/${this.instanceModal.currentInstance.id}/`;
//
//            const payload = {
//                stan: this.instanceModal.currentInstance.stan,
//                lokalizacja_id: this.instanceModal.currentInstance.lokalizacja_id,
//                narzedzie_typ_id: this.instanceModal.currentInstance.narzedzie_typ_id,
//                faktura_zakupu_id: this.instanceModal.currentInstance.faktura_zakupu_id,
//                zamowienie_id: this.instanceModal.currentInstance.zamowienie_id
//            };
//
//            const ilosc = this.instanceModal.currentInstance.ilosc;
//
//            if (this.instanceModal.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
//                this.instanceModal.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
//                this.isSavingInstance = false;
//                return;
//            }
//
//            try {
//                if (this.instanceModal.mode === 'add' && ilosc > 1) {
//                    await this.createMultipleInstances(url, payload, ilosc);
//                } else {
//                    await this.createOrUpdateInstance(method, url, payload);
//                }
//
//                if (this.instanceModal.instance) {
//                    this.instanceModal.instance.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//
//            } catch (error) {
//                this.handleSaveInstanceError(error, ilosc);
//            } finally {
//                this.isSavingInstance = false;
//            }
//        },
//
//        async createMultipleInstances(url, payload, ilosc) {
//            const requests = [];
//            for (let i = 0; i < ilosc; i++) {
//                requests.push(axios.post(url, payload));
//            }
//            const responses = await Promise.all(requests);
//            console.log(`Pomyślnie dodano ${responses.length} egzemplarzy.`);
//        },
//
//        async createOrUpdateInstance(method, url, payload) {
//            await axios({ method, url, data: payload });
//            const action = this.instanceModal.mode === 'add' ? 'dodano' : 'zaktualizowano';
//            console.log(`Pomyślnie ${action} egzemplarz.`);
//        },
//
//        handleSaveInstanceError(error, ilosc) {
//            console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);
//
//            let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';
//
//            if (error.response?.data) {
//                if (typeof error.response.data === 'object') {
//                    errorMsg = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                } else if (Array.isArray(error.response.data) && ilosc > 1) {
//                    const firstError = error.response.data[0];
//                    errorMsg = `Błąd przy dodawaniu seryjnym: ${JSON.stringify(firstError)}`;
//                } else {
//                    errorMsg = `Błąd: ${error.response.data}`;
//                }
//            } else if (error.message) {
//                const prefix = ilosc > 1 ? 'podczas dodawania seryjnego' : '';
//                errorMsg = `Wystąpił błąd sieci lub serwera ${prefix}: ${error.message}.`;
//            }
//
//            this.instanceModal.errorMessage = errorMsg;
//        },
//
//        openDeleteInstanceModal(instance) {
//            this.instanceToDelete = instance;
//
//            const toolName = instance.narzedzie_typ.podkategoria ?
//                `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}` :
//                instance.narzedzie_typ.opis;
//
//            if (instance.stan === 'uszkodzone') {
//                this.deleteModalMessage = `Ten egzemplarz (<strong>${toolName}</strong>) jest oznaczony jako uszkodzony. Zostanie przeniesiony do archiwum. Czy chcesz kontynuować?`;
//            } else {
//                this.deleteModalMessage = `Czy na pewno chcesz trwale usunąć egzemplarz: <strong>${toolName}</strong>?`;
//            }
//
//            if (this.modals.deleteInstanceModal) {
//                this.modals.deleteInstanceModal.show();
//            } else {
//                console.error("Modal 'deleteInstanceModal' not initialized!");
//            }
//        },
//
//        async confirmDeleteInstance() {
//            if (!this.instanceToDelete) {
//                return;
//            }
//
//            try {
//                await axios.delete(`${API_URL}/egzemplarze/${this.instanceToDelete.id}/`);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//                this.instanceToDelete = null;
//            } catch (error) {
//                console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
//            }
//        },
//    }
//}).mount('#app');
//
//

































///**
// * Panel Magazyniera - Frontend
// * Zarządzanie narzędziami CNC
// */
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//
//    data() {
//        return {
//            tools: [],
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            pracownicy: [],
//            faktury: [],
//            zamowienia: [],
//            usagesInUse: [],
//            toolInstances: [],
//            toolHistory: [],
//            locations: [],
//
//            selectedKategoriaId: null,
//            selectedPodkategoriaId: null,
//            selectedToolForDetails: null,
//            selectedMaszynaFilter: null,
//
//            activeTab: 'details',
//            isLoadingDetails: false,
//            isLoadingHistory: false,
//            isEditMode: false,
//            isSavingInstance: false,
//
//            error: '',
//            issueData: {
//                machine_id: null,
//                instance: null,
//                pracownik_id: null
//            },
//            currentTool: {},
//            returnStatus: 'uzywane',
//            usageToReturnId: null,
//            modals: {},
//            searchQuery: '',
//            toolValidationError: '',
//
//            instanceModal: {
//                instance: null,
//                title: '',
//                mode: 'add',
//                currentInstance: {
//                    id: null,
//                    narzedzie_typ_id: null,
//                    stan: 'nowe',
//                    lokalizacja_id: null,
//                    faktura_zakupu_id: null,
//                    zamowienie_id: null,
//                    ilosc: 1
//                },
//                errorMessage: '',
//            },
//
//            instanceToDelete: null,
//            deleteModalMessage: '',
//
//            toolImagePreview: null,
//            toolImageFile: null,
//        };
//    },
//
//    computed: {
//        filteredTools() {
//            let filtered = this.tools;
//
//            if (this.selectedPodkategoriaId) {
//                filtered = this.filterByPodkategoria(filtered);
//            } else if (this.selectedKategoriaId) {
//                filtered = this.filterByKategoria(filtered);
//            }
//
//            if (this.searchQuery.trim() !== '') {
//                filtered = this.filterBySearchQuery(filtered);
//            }
//
//            return filtered;
//        },
//
//        inUseInstanceIds() {
//            return new Set(this.usagesInUse.map(usage => usage.egzemplarz.id));
//        },
//
//        filteredPodkategorie() {
//            if (!this.selectedKategoriaId) {
//                return [];
//            }
//
//            const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kategoria ? kategoria.podkategorie : [];
//        },
//
//        unsettledInvoices() {
//            return this.faktury
//                .filter(f => !f.rozliczone)
//                .sort((a, b) => new Date(b.data_wystawienia) - new Date(a.data_wystawienia));
//        },
//
//        sortedLocations() {
//            return [...this.locations].sort((a, b) => {
//                if (a.szafa < b.szafa) return -1;
//                if (a.szafa > b.szafa) return 1;
//
//                const kolumnaA = parseInt(a.kolumna) || 0;
//                const kolumnaB = parseInt(b.kolumna) || 0;
//                if (kolumnaA < kolumnaB) return -1;
//                if (kolumnaA > kolumnaB) return 1;
//
//                const polkaA = parseInt(a.polka) || 0;
//                const polkaB = parseInt(b.polka) || 0;
//                return polkaA - polkaB;
//            });
//        },
//
//        filteredUsagesInUse() {
//            if (!this.selectedMaszynaFilter) {
//                return this.usagesInUse;
//            }
//
//            return this.usagesInUse.filter(usage => {
//                return usage.maszyna && usage.maszyna.id === this.selectedMaszynaFilter;
//            });
//        }
//    },
//
//    async mounted() {
//        this.initModals();
//        await this.fetchInitialData();
//    },
//
//    methods: {
//        initModals() {
//            const modalRefs = ['issueModal', 'returnModal', 'toolModal', 'instanceModal', 'deleteInstanceModal'];
//
//            modalRefs.forEach(ref => {
//                if (this.$refs[ref]) {
//                    const modalInstance = new bootstrap.Modal(this.$refs[ref]);
//
//                    if (ref === 'instanceModal') {
//                        this.instanceModal.instance = modalInstance;
//                    } else {
//                        this.modals[ref] = modalInstance;
//                    }
//                } else {
//                    console.warn(`Modal ref "${ref}" not found during init.`);
//                }
//            });
//        },
//
//        async fetchInitialData() {
//            this.isLoading = true;
//
//            try {
//                const responses = await this.fetchAllApiData();
//                this.assignFetchedData(responses);
//            } catch (error) {
//                this.handleFetchError(error);
//            } finally {
//                this.isLoading = false;
//            }
//        },
//
//        async fetchAllApiData() {
//            const [
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            ] = await Promise.all([
//                axios.get(`${API_URL}/narzedzia/`),
//                axios.get(`${API_URL}/kategorie/`),
//                axios.get(`${API_URL}/maszyny/`),
//                axios.get(`${API_URL}/historia/?w_uzyciu=true`),
//                axios.get(`${API_URL}/lokalizacje/`),
//                axios.get(`${API_URL}/podkategorie/`),
//                axios.get(`${API_URL}/pracownicy/`),
//                axios.get(`${API_URL}/faktury/`),
//                axios.get(`${API_URL}/zamowienia/`)
//            ]);
//
//            return {
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            };
//        },
//
//        assignFetchedData(responses) {
//            this.tools = responses.toolsRes.data.results || responses.toolsRes.data;
//            this.kategorie = responses.categoriesRes.data;
//            this.machines = responses.machinesRes.data;
//            this.usagesInUse = responses.usagesRes.data.results || responses.usagesRes.data;
//            this.locations = responses.locationsRes.data;
//            this.podkategorie = responses.podkategorieRes.data;
//            this.pracownicy = responses.pracownicyRes.data.results || responses.pracownicyRes.data;
//            this.faktury = responses.fakturyRes.data.results || responses.fakturyRes.data;
//            this.zamowienia = responses.zamowieniaRes.data.results || responses.zamowieniaRes.data;
//        },
//
//        handleFetchError(error) {
//            console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
//            alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
//        },
//
//        onKategoriaChange() {
//            this.selectedPodkategoriaId = null;
//        },
//
//        async selectTool(tool) {
//            if (this.selectedToolForDetails && this.selectedToolForDetails.id === tool.id) {
//                this.selectedToolForDetails = null;
//                this.toolInstances = [];
//                this.toolHistory = [];
//                return;
//            }
//
//            this.selectedToolForDetails = tool;
//            this.activeTab = 'details';
//
//            await this.getToolInstances(tool);
//            await this.getToolHistory(tool);
//        },
//
//        async getToolInstances(tool) {
//            this.isLoadingDetails = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
//                const instances = response.data.results || response.data;
//                this.toolInstances = instances.sort((a, b) => b.id - a.id);
//            } catch (error) {
//                console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
//                this.toolInstances = [];
//            } finally {
//                this.isLoadingDetails = false;
//            }
//        },
//
//        async getToolHistory(tool) {
//            this.isLoadingHistory = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
//                const history = response.data.results || response.data;
//                this.toolHistory = history.sort((a, b) =>
//                    new Date(b.data_wydania) - new Date(a.data_wydania)
//                );
//            } catch (error) {
//                console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
//                this.toolHistory = [];
//            } finally {
//                this.isLoadingHistory = false;
//            }
//        },
//
//        filterByPodkategoria(tools) {
//            return tools.filter(tool => {
//                return tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId;
//            });
//        },
//
//        filterByKategoria(tools) {
//            return tools.filter(tool => {
//                if (!tool.podkategoria) return false;
//
//                const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                if (!kategoria) return false;
//
//                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
//            });
//        },
//
//        filterBySearchQuery(tools) {
//            const query = this.searchQuery.trim().toLowerCase();
//
//            return tools.filter(tool => {
//                const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
//                const kategoriaNazwa = this.getKategoriaNazwa(tool);
//                const podkategoriaNazwa = this.getPodkategoriaNazwa(tool);
//                const opisNazwa = tool.opis.toLowerCase();
//
//                return kategoriaNazwa.includes(query) ||
//                       podkategoriaNazwa.includes(query) ||
//                       opisNazwa.includes(query) ||
//                       catalogNumber.includes(query);
//            });
//        },
//
//        getKategoriaNazwa(tool) {
//            if (!tool.podkategoria || !tool.podkategoria.kategoria_nazwa) {
//                return '';
//            }
//            return tool.podkategoria.kategoria_nazwa.toLowerCase();
//        },
//
//        getPodkategoriaNazwa(tool) {
//            if (!tool.podkategoria) {
//                return '';
//            }
//            return tool.podkategoria.nazwa.toLowerCase();
//        },
//
//        formatCustomDate(dateString) {
//            if (!dateString) {
//                return '';
//            }
//
//            try {
//                const date = new Date(dateString);
//
//                if (isNaN(date.getTime())) {
//                    return 'Nieprawidłowa data';
//                }
//
//                const year = date.getFullYear();
//                const month = this.padNumber(date.getMonth() + 1);
//                const day = this.padNumber(date.getDate());
//                const hours = this.padNumber(date.getHours());
//                const minutes = this.padNumber(date.getMinutes());
//
//                return `${year}-${month}-${day} [${hours}:${minutes}]`;
//            } catch (e) {
//                console.error("Błąd formatowania daty:", dateString, e);
//                return 'Błąd daty';
//            }
//        },
//
//        padNumber(num) {
//            return num.toString().padStart(2, '0');
//        },
//
//        getInstanceStatusClass(stan) {
//            const statusMap = {
//                'nowe': 'success',
//                'uzywane': 'primary',
//                'uszkodzone': 'danger'
//            };
//            return statusMap[stan] || 'secondary';
//        },
//
//        showIssueModal(instance) {
//            this.issueData.instance = instance;
//            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
//            this.issueData.pracownik_id = null;
//            this.error = '';
//
//            if (this.modals.issueModal) {
//                this.modals.issueModal.show();
//            } else {
//                console.error("Modal 'issueModal' not initialized!");
//            }
//        },
//
//        async issueTool() {
//            if (!this.issueData.pracownik_id) {
//                this.error = "Wybierz pracownika.";
//                return;
//            }
//
//            this.error = '';
//
//            try {
//                await axios.post(`${API_URL}/historia/wydanie/`, {
//                    egzemplarz_id: this.issueData.instance.id,
//                    maszyna_id: this.issueData.machine_id,
//                    pracownik_id: this.issueData.pracownik_id
//                });
//
//                if (this.modals.issueModal) {
//                    this.modals.issueModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                    await this.getToolHistory(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
//                this.error = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
//            }
//        },
//
//        showReturnModal(usageId) {
//            this.usageToReturnId = usageId;
//            this.returnStatus = 'uzywane';
//
//            if (this.modals.returnModal) {
//                this.modals.returnModal.show();
//            } else {
//                console.error("Modal 'returnModal' not initialized!");
//            }
//        },
//
//        async confirmReturnTool() {
//            try {
//                await axios.post(`${API_URL}/historia/${this.usageToReturnId}/zwrot/`, {
//                    stan_po_zwrocie: this.returnStatus
//                });
//
//                if (this.modals.returnModal) {
//                    this.modals.returnModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                    await this.getToolHistory(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
//                alert("Wystąpił błąd podczas zwracania narzędzia.");
//            }
//        },
//
//        openToolModal(tool = null) {
//            this.isEditMode = !!tool;
//            this.toolImagePreview = null;
//            this.toolImageFile = null;
//            this.toolValidationError = '';
//
//            if (this.isEditMode) {
//                this.currentTool = {
//                    ...tool,
//                    podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
//                    domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
//                    opakowanie: tool.opakowanie || 'szt',
//                    ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1
//                };
//                if (tool.obraz) {
//                    this.toolImagePreview = tool.obraz;
//                }
//            } else {
//                this.currentTool = {
//                    podkategoria_id: null,
//                    opis: '',
//                    numer_katalogowy: '',
//                    domyslna_lokalizacja_id: null,
//                    obraz: null,
//                    opakowanie: 'szt',
//                    ilosc_w_opakowaniu: 1
//                };
//            }
//
//            if (this.modals.toolModal) {
//                this.modals.toolModal.show();
//            } else {
//                console.error("Modal 'toolModal' not initialized!");
//            }
//        },
//
//        onOpakowanieChange() {
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.currentTool.ilosc_w_opakowaniu = 2;
//            } else if (this.currentTool.opakowanie === 'szt') {
//                this.currentTool.ilosc_w_opakowaniu = 1;
//            }
//        },
//
//        handleToolImageUpload(event) {
//            const file = event.target.files[0];
//
//            if (!file) {
//                this.toolImageFile = null;
//                this.toolImagePreview = (this.isEditMode && this.currentTool.obraz) ?
//                    this.currentTool.obraz : null;
//                return;
//            }
//
//            this.toolImageFile = file;
//            this.toolImagePreview = URL.createObjectURL(file);
//        },
//
//        async saveTool() {
//            this.toolValidationError = '';
//
//            // Walidacja
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.toolValidationError = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
//                return;
//            }
//
//            const formData = new FormData();
//            formData.append('opis', this.currentTool.opis);
//            formData.append('opakowanie', this.currentTool.opakowanie || 'szt');
//            formData.append('ilosc_w_opakowaniu', this.currentTool.ilosc_w_opakowaniu || 1);
//
//            if (this.currentTool.podkategoria_id) {
//                formData.append('podkategoria_id', this.currentTool.podkategoria_id);
//            }
//
//            if (this.currentTool.numer_katalogowy) {
//                formData.append('numer_katalogowy', this.currentTool.numer_katalogowy);
//            }
//
//            if (this.currentTool.domyslna_lokalizacja_id) {
//                formData.append('domyslna_lokalizacja_id', this.currentTool.domyslna_lokalizacja_id);
//            }
//
//            if (this.toolImageFile) {
//                formData.append('obraz', this.toolImageFile);
//            }
//
//            const method = this.isEditMode ? 'patch' : 'post';
//            const url = this.isEditMode ?
//                `${API_URL}/narzedzia/${this.currentTool.id}/` :
//                `${API_URL}/narzedzia/`;
//
//            try {
//                await axios({
//                    method: method,
//                    url: url,
//                    data: formData,
//                    headers: { 'Content-Type': 'multipart/form-data' }
//                });
//
//                if (this.modals.toolModal) {
//                    this.modals.toolModal.hide();
//                }
//
//                await this.fetchInitialData();
//            } catch (error) {
//                console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
//                this.toolValidationError = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
//            }
//        },
//
//        openInstanceModal(mode, instance = null) {
//            this.instanceModal.mode = mode;
//            this.instanceModal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.setupAddInstanceMode();
//            } else {
//                this.setupEditInstanceMode(instance);
//            }
//
//            if (this.instanceModal.instance) {
//                this.instanceModal.instance.show();
//            } else {
//                console.error("Modal 'instanceModal' not initialized!");
//            }
//        },
//
//        setupAddInstanceMode() {
//            this.instanceModal.title = 'Dodaj nowy egzemplarz';
//            this.instanceModal.currentInstance = {
//                id: null,
//                narzedzie_typ_id: this.selectedToolForDetails.id,
//                stan: 'nowe',
//                lokalizacja_id: null,
//                faktura_zakupu_id: null,
//                zamowienie_id: null,
//                ilosc: 1
//            };
//
//            // Priorytet 1: Domyślna lokalizacja z typu narzędzia
//            if (this.selectedToolForDetails.domyslna_lokalizacja) {
//                this.instanceModal.currentInstance.lokalizacja_id = this.selectedToolForDetails.domyslna_lokalizacja.id;
//            }
//            // Priorytet 2: Lokalizacja ostatniego egzemplarza
//            else if (Array.isArray(this.toolInstances) && this.toolInstances.length > 0) {
//                const lastInstance = this.toolInstances[0];
//                if (lastInstance && lastInstance.lokalizacja) {
//                    this.instanceModal.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
//                }
//            }
//        },
//
//        setupEditInstanceMode(instance) {
//            this.instanceModal.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
//            this.instanceModal.currentInstance = {
//                ...instance,
//                lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
//                faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
//                zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
//                ilosc: 1
//            };
//        },
//
//        async saveInstance() {
//            this.isSavingInstance = true;
//            this.instanceModal.errorMessage = '';
//
//            const method = this.instanceModal.mode === 'add' ? 'post' : 'patch';
//            const url = this.instanceModal.mode === 'add' ?
//                `${API_URL}/egzemplarze/` :
//                `${API_URL}/egzemplarze/${this.instanceModal.currentInstance.id}/`;
//
//            const payload = {
//                stan: this.instanceModal.currentInstance.stan,
//                lokalizacja_id: this.instanceModal.currentInstance.lokalizacja_id,
//                narzedzie_typ_id: this.instanceModal.currentInstance.narzedzie_typ_id,
//                faktura_zakupu_id: this.instanceModal.currentInstance.faktura_zakupu_id,
//                zamowienie_id: this.instanceModal.currentInstance.zamowienie_id
//            };
//
//            const ilosc = this.instanceModal.currentInstance.ilosc;
//
//            if (this.instanceModal.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
//                this.instanceModal.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
//                this.isSavingInstance = false;
//                return;
//            }
//
//            try {
//                if (this.instanceModal.mode === 'add' && ilosc > 1) {
//                    await this.createMultipleInstances(url, payload, ilosc);
//                } else {
//                    await this.createOrUpdateInstance(method, url, payload);
//                }
//
//                if (this.instanceModal.instance) {
//                    this.instanceModal.instance.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//
//            } catch (error) {
//                this.handleSaveInstanceError(error, ilosc);
//            } finally {
//                this.isSavingInstance = false;
//            }
//        },
//
//        async createMultipleInstances(url, payload, ilosc) {
//            const requests = [];
//            for (let i = 0; i < ilosc; i++) {
//                requests.push(axios.post(url, payload));
//            }
//            const responses = await Promise.all(requests);
//            console.log(`Pomyślnie dodano ${responses.length} egzemplarzy.`);
//        },
//
//        async createOrUpdateInstance(method, url, payload) {
//            await axios({ method, url, data: payload });
//            const action = this.instanceModal.mode === 'add' ? 'dodano' : 'zaktualizowano';
//            console.log(`Pomyślnie ${action} egzemplarz.`);
//        },
//
//        handleSaveInstanceError(error, ilosc) {
//            console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);
//
//            let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';
//
//            if (error.response?.data) {
//                if (typeof error.response.data === 'object') {
//                    errorMsg = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                } else if (Array.isArray(error.response.data) && ilosc > 1) {
//                    const firstError = error.response.data[0];
//                    errorMsg = `Błąd przy dodawaniu seryjnym: ${JSON.stringify(firstError)}`;
//                } else {
//                    errorMsg = `Błąd: ${error.response.data}`;
//                }
//            } else if (error.message) {
//                const prefix = ilosc > 1 ? 'podczas dodawania seryjnego' : '';
//                errorMsg = `Wystąpił błąd sieci lub serwera ${prefix}: ${error.message}.`;
//            }
//
//            this.instanceModal.errorMessage = errorMsg;
//        },
//
//        openDeleteInstanceModal(instance) {
//            this.instanceToDelete = instance;
//
//            const toolName = instance.narzedzie_typ.podkategoria ?
//                `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}` :
//                instance.narzedzie_typ.opis;
//
//            if (instance.stan === 'uszkodzone') {
//                this.deleteModalMessage = `Ten egzemplarz (<strong>${toolName}</strong>) jest oznaczony jako uszkodzony. Zostanie przeniesiony do archiwum. Czy chcesz kontynuować?`;
//            } else {
//                this.deleteModalMessage = `Czy na pewno chcesz trwale usunąć egzemplarz: <strong>${toolName}</strong>?`;
//            }
//
//            if (this.modals.deleteInstanceModal) {
//                this.modals.deleteInstanceModal.show();
//            } else {
//                console.error("Modal 'deleteInstanceModal' not initialized!");
//            }
//        },
//
//        async confirmDeleteInstance() {
//            if (!this.instanceToDelete) {
//                return;
//            }
//
//            try {
//                await axios.delete(`${API_URL}/egzemplarze/${this.instanceToDelete.id}/`);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//                this.instanceToDelete = null;
//            } catch (error) {
//                console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
//            }
//        },
//    }
//}).mount('#app');
//
//




























































///**
// * Panel Magazyniera - Frontend
// * Zarządzanie narzędziami CNC
// */
//
//const { createApp } = Vue;
//const API_URL = '/api';
//
//axios.defaults.xsrfCookieName = 'csrftoken';
//axios.defaults.xsrfHeaderName = 'X-CSRFToken';
//
//createApp({
//    delimiters: ['[[', ']]'],
//
//    data() {
//        return {
//            tools: [],
//            kategorie: [],
//            podkategorie: [],
//            machines: [],
//            pracownicy: [],
//            faktury: [],
//            zamowienia: [],
//            usagesInUse: [],
//            toolInstances: [],
//            toolHistory: [],
//            locations: [],
//
//            selectedKategoriaId: null,
//            selectedPodkategoriaId: null,
//            selectedToolForDetails: null,
//            selectedMaszynaFilter: null,
//
//            activeTab: 'details',
//            isLoadingDetails: false,
//            isLoadingHistory: false,
//            isEditMode: false,
//            isSavingInstance: false,
//
//            error: '',
//            issueData: {
//                machine_id: null,
//                instance: null,
//                pracownik_id: null
//            },
//            currentTool: {},
//            returnStatus: 'uzywane',
//            usageToReturnId: null,
//            modals: {},
//            searchQuery: '',
//            toolValidationError: '',
//
//            instanceModal: {
//                instance: null,
//                title: '',
//                mode: 'add',
//                currentInstance: {
//                    id: null,
//                    narzedzie_typ_id: null,
//                    stan: 'nowe',
//                    lokalizacja_id: null,
//                    faktura_zakupu_id: null,
//                    zamowienie_id: null,
//                    ilosc: 1
//                },
//                errorMessage: '',
//            },
//
//            instanceToDelete: null,
//            deleteModalMessage: '',
//
//            toolImagePreview: null,
//            toolImageFile: null,
//        };
//    },
//
//    computed: {
//        filteredTools() {
//            let filtered = this.tools;
//
//            if (this.selectedPodkategoriaId) {
//                filtered = this.filterByPodkategoria(filtered);
//            } else if (this.selectedKategoriaId) {
//                filtered = this.filterByKategoria(filtered);
//            }
//
//            if (this.searchQuery.trim() !== '') {
//                filtered = this.filterBySearchQuery(filtered);
//            }
//
//            return filtered;
//        },
//
//        inUseInstanceIds() {
//            return new Set(this.usagesInUse.map(usage => usage.egzemplarz.id));
//        },
//
//        filteredPodkategorie() {
//            if (!this.selectedKategoriaId) {
//                return [];
//            }
//
//            const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//            return kategoria ? kategoria.podkategorie : [];
//        },
//
//        unsettledInvoices() {
//            return this.faktury
//                .filter(f => !f.rozliczone)
//                .sort((a, b) => new Date(b.data_wystawienia) - new Date(a.data_wystawienia));
//        },
//
//        sortedLocations() {
//            return [...this.locations].sort((a, b) => {
//                if (a.szafa < b.szafa) return -1;
//                if (a.szafa > b.szafa) return 1;
//
//                const kolumnaA = parseInt(a.kolumna) || 0;
//                const kolumnaB = parseInt(b.kolumna) || 0;
//                if (kolumnaA < kolumnaB) return -1;
//                if (kolumnaA > kolumnaB) return 1;
//
//                const polkaA = parseInt(a.polka) || 0;
//                const polkaB = parseInt(b.polka) || 0;
//                return polkaA - polkaB;
//            });
//        },
//
//        filteredUsagesInUse() {
//            if (!this.selectedMaszynaFilter) {
//                return this.usagesInUse;
//            }
//
//            return this.usagesInUse.filter(usage => {
//                return usage.maszyna && usage.maszyna.id === this.selectedMaszynaFilter;
//            });
//        }
//    },
//
//    async mounted() {
//        this.initModals();
//        await this.fetchInitialData();
//    },
//
//    methods: {
//        initModals() {
//            const modalRefs = ['issueModal', 'returnModal', 'toolModal', 'instanceModal', 'deleteInstanceModal'];
//
//            modalRefs.forEach(ref => {
//                if (this.$refs[ref]) {
//                    const modalInstance = new bootstrap.Modal(this.$refs[ref]);
//
//                    if (ref === 'instanceModal') {
//                        this.instanceModal.instance = modalInstance;
//                    } else {
//                        this.modals[ref] = modalInstance;
//                    }
//                } else {
//                    console.warn(`Modal ref "${ref}" not found during init.`);
//                }
//            });
//        },
//
//        async fetchInitialData() {
//            this.isLoading = true;
//
//            try {
//                const responses = await this.fetchAllApiData();
//                this.assignFetchedData(responses);
//            } catch (error) {
//                this.handleFetchError(error);
//            } finally {
//                this.isLoading = false;
//            }
//        },
//
//        async fetchAllApiData() {
//            const [
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            ] = await Promise.all([
//                axios.get(`${API_URL}/narzedzia/`),
//                axios.get(`${API_URL}/kategorie/`),
//                axios.get(`${API_URL}/maszyny/`),
//                axios.get(`${API_URL}/historia/?w_uzyciu=true`),
//                axios.get(`${API_URL}/lokalizacje/`),
//                axios.get(`${API_URL}/podkategorie/`),
//                axios.get(`${API_URL}/pracownicy/`),
//                axios.get(`${API_URL}/faktury/`),
//                axios.get(`${API_URL}/zamowienia/`)
//            ]);
//
//            return {
//                toolsRes,
//                categoriesRes,
//                machinesRes,
//                usagesRes,
//                locationsRes,
//                podkategorieRes,
//                pracownicyRes,
//                fakturyRes,
//                zamowieniaRes
//            };
//        },
//
//        assignFetchedData(responses) {
//            this.tools = responses.toolsRes.data.results || responses.toolsRes.data;
//            this.kategorie = responses.categoriesRes.data;
//            this.machines = responses.machinesRes.data;
//            this.usagesInUse = responses.usagesRes.data.results || responses.usagesRes.data;
//            this.locations = responses.locationsRes.data;
//            this.podkategorie = responses.podkategorieRes.data;
//            this.pracownicy = responses.pracownicyRes.data.results || responses.pracownicyRes.data;
//            this.faktury = responses.fakturyRes.data.results || responses.fakturyRes.data;
//            this.zamowienia = responses.zamowieniaRes.data.results || responses.zamowieniaRes.data;
//        },
//
//        handleFetchError(error) {
//            console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
//            alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
//        },
//
//        onKategoriaChange() {
//            this.selectedPodkategoriaId = null;
//        },
//
//        async selectTool(tool) {
//            if (this.selectedToolForDetails && this.selectedToolForDetails.id === tool.id) {
//                this.selectedToolForDetails = null;
//                this.toolInstances = [];
//                this.toolHistory = [];
//                return;
//            }
//
//            this.selectedToolForDetails = tool;
//            this.activeTab = 'details';
//
//            await this.getToolInstances(tool);
//            await this.getToolHistory(tool);
//        },
//
//        async getToolInstances(tool) {
//            this.isLoadingDetails = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
//                const instances = response.data.results || response.data;
//                this.toolInstances = instances.sort((a, b) => b.id - a.id);
//            } catch (error) {
//                console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
//                this.toolInstances = [];
//            } finally {
//                this.isLoadingDetails = false;
//            }
//        },
//
//        async getToolHistory(tool) {
//            this.isLoadingHistory = true;
//
//            try {
//                const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
//                const history = response.data.results || response.data;
//                this.toolHistory = history.sort((a, b) =>
//                    new Date(b.data_wydania) - new Date(a.data_wydania)
//                );
//            } catch (error) {
//                console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
//                this.toolHistory = [];
//            } finally {
//                this.isLoadingHistory = false;
//            }
//        },
//
//        filterByPodkategoria(tools) {
//            return tools.filter(tool => {
//                return tool.podkategoria && tool.podkategoria.id === this.selectedPodkategoriaId;
//            });
//        },
//
//        filterByKategoria(tools) {
//            return tools.filter(tool => {
//                if (!tool.podkategoria) return false;
//
//                const kategoria = this.kategorie.find(k => k.id === this.selectedKategoriaId);
//                if (!kategoria) return false;
//
//                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
//            });
//        },
//
//        filterBySearchQuery(tools) {
//            const query = this.searchQuery.trim().toLowerCase();
//
//            return tools.filter(tool => {
//                const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
//                const kategoriaNazwa = this.getKategoriaNazwa(tool);
//                const podkategoriaNazwa = this.getPodkategoriaNazwa(tool);
//                const opisNazwa = tool.opis.toLowerCase();
//
//                return kategoriaNazwa.includes(query) ||
//                       podkategoriaNazwa.includes(query) ||
//                       opisNazwa.includes(query) ||
//                       catalogNumber.includes(query);
//            });
//        },
//
//        getKategoriaNazwa(tool) {
//            if (!tool.podkategoria || !tool.podkategoria.kategoria_nazwa) {
//                return '';
//            }
//            return tool.podkategoria.kategoria_nazwa.toLowerCase();
//        },
//
//        getPodkategoriaNazwa(tool) {
//            if (!tool.podkategoria) {
//                return '';
//            }
//            return tool.podkategoria.nazwa.toLowerCase();
//        },
//
//        formatCustomDate(dateString) {
//            if (!dateString) {
//                return '';
//            }
//
//            try {
//                const date = new Date(dateString);
//
//                if (isNaN(date.getTime())) {
//                    return 'Nieprawidłowa data';
//                }
//
//                const year = date.getFullYear();
//                const month = this.padNumber(date.getMonth() + 1);
//                const day = this.padNumber(date.getDate());
//                const hours = this.padNumber(date.getHours());
//                const minutes = this.padNumber(date.getMinutes());
//
//                return `${year}-${month}-${day} [${hours}:${minutes}]`;
//            } catch (e) {
//                console.error("Błąd formatowania daty:", dateString, e);
//                return 'Błąd daty';
//            }
//        },
//
//        padNumber(num) {
//            return num.toString().padStart(2, '0');
//        },
//
//        getInstanceStatusClass(stan) {
//            const statusMap = {
//                'nowe': 'success',
//                'uzywane': 'primary',
//                'uszkodzone': 'danger'
//            };
//            return statusMap[stan] || 'secondary';
//        },
//
//        showIssueModal(instance) {
//            this.issueData.instance = instance;
//            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
//            this.issueData.pracownik_id = null;
//            this.error = '';
//
//            if (this.modals.issueModal) {
//                this.modals.issueModal.show();
//            } else {
//                console.error("Modal 'issueModal' not initialized!");
//            }
//        },
//
//        async issueTool() {
//            if (!this.issueData.pracownik_id) {
//                this.error = "Wybierz pracownika.";
//                return;
//            }
//
//            this.error = '';
//
//            try {
//                await axios.post(`${API_URL}/historia/wydanie/`, {
//                    egzemplarz_id: this.issueData.instance.id,
//                    maszyna_id: this.issueData.machine_id,
//                    pracownik_id: this.issueData.pracownik_id
//                });
//
//                if (this.modals.issueModal) {
//                    this.modals.issueModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
//                this.error = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
//            }
//        },
//
//        showReturnModal(usageId) {
//            this.usageToReturnId = usageId;
//            this.returnStatus = 'uzywane';
//
//            if (this.modals.returnModal) {
//                this.modals.returnModal.show();
//            } else {
//                console.error("Modal 'returnModal' not initialized!");
//            }
//        },
//
//        async confirmReturnTool() {
//            try {
//                await axios.post(`${API_URL}/historia/${this.usageToReturnId}/zwrot/`, {
//                    stan_po_zwrocie: this.returnStatus
//                });
//
//                if (this.modals.returnModal) {
//                    this.modals.returnModal.hide();
//                }
//
//                await this.fetchInitialData();
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//            } catch (error) {
//                console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
//                alert("Wystąpił błąd podczas zwracania narzędzia.");
//            }
//        },
//
//        openToolModal(tool = null) {
//            this.isEditMode = !!tool;
//            this.toolImagePreview = null;
//            this.toolImageFile = null;
//            this.toolValidationError = '';
//
//            if (this.isEditMode) {
//                this.currentTool = {
//                    ...tool,
//                    podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
//                    domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
//                    opakowanie: tool.opakowanie || 'szt',
//                    ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1
//                };
//                if (tool.obraz) {
//                    this.toolImagePreview = tool.obraz;
//                }
//            } else {
//                this.currentTool = {
//                    podkategoria_id: null,
//                    opis: '',
//                    numer_katalogowy: '',
//                    domyslna_lokalizacja_id: null,
//                    obraz: null,
//                    opakowanie: 'szt',
//                    ilosc_w_opakowaniu: 1
//                };
//            }
//
//            if (this.modals.toolModal) {
//                this.modals.toolModal.show();
//            } else {
//                console.error("Modal 'toolModal' not initialized!");
//            }
//        },
//
//        onOpakowanieChange() {
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.currentTool.ilosc_w_opakowaniu = 2;
//            } else if (this.currentTool.opakowanie === 'szt') {
//                this.currentTool.ilosc_w_opakowaniu = 1;
//            }
//        },
//
//        handleToolImageUpload(event) {
//            const file = event.target.files[0];
//
//            if (!file) {
//                this.toolImageFile = null;
//                this.toolImagePreview = (this.isEditMode && this.currentTool.obraz) ?
//                    this.currentTool.obraz : null;
//                return;
//            }
//
//            this.toolImageFile = file;
//            this.toolImagePreview = URL.createObjectURL(file);
//        },
//
//        async saveTool() {
//            this.toolValidationError = '';
//
//            // Walidacja
//            if (this.currentTool.opakowanie === 'kompl' && this.currentTool.ilosc_w_opakowaniu <= 1) {
//                this.toolValidationError = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
//                return;
//            }
//
//            const formData = new FormData();
//            formData.append('opis', this.currentTool.opis);
//            formData.append('opakowanie', this.currentTool.opakowanie || 'szt');
//            formData.append('ilosc_w_opakowaniu', this.currentTool.ilosc_w_opakowaniu || 1);
//
//            if (this.currentTool.podkategoria_id) {
//                formData.append('podkategoria_id', this.currentTool.podkategoria_id);
//            }
//
//            if (this.currentTool.numer_katalogowy) {
//                formData.append('numer_katalogowy', this.currentTool.numer_katalogowy);
//            }
//
//            if (this.currentTool.domyslna_lokalizacja_id) {
//                formData.append('domyslna_lokalizacja_id', this.currentTool.domyslna_lokalizacja_id);
//            }
//
//            if (this.toolImageFile) {
//                formData.append('obraz', this.toolImageFile);
//            }
//
//            const method = this.isEditMode ? 'patch' : 'post';
//            const url = this.isEditMode ?
//                `${API_URL}/narzedzia/${this.currentTool.id}/` :
//                `${API_URL}/narzedzia/`;
//
//            try {
//                await axios({
//                    method: method,
//                    url: url,
//                    data: formData,
//                    headers: { 'Content-Type': 'multipart/form-data' }
//                });
//
//                if (this.modals.toolModal) {
//                    this.modals.toolModal.hide();
//                }
//
//                await this.fetchInitialData();
//            } catch (error) {
//                console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
//                this.toolValidationError = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
//            }
//        },
//
//        openInstanceModal(mode, instance = null) {
//            this.instanceModal.mode = mode;
//            this.instanceModal.errorMessage = '';
//
//            if (mode === 'add') {
//                this.setupAddInstanceMode();
//            } else {
//                this.setupEditInstanceMode(instance);
//            }
//
//            if (this.instanceModal.instance) {
//                this.instanceModal.instance.show();
//            } else {
//                console.error("Modal 'instanceModal' not initialized!");
//            }
//        },
//
//        setupAddInstanceMode() {
//            this.instanceModal.title = 'Dodaj nowy egzemplarz';
//            this.instanceModal.currentInstance = {
//                id: null,
//                narzedzie_typ_id: this.selectedToolForDetails.id,
//                stan: 'nowe',
//                lokalizacja_id: null,
//                faktura_zakupu_id: null,
//                zamowienie_id: null,
//                ilosc: 1
//            };
//
//            // Priorytet 1: Domyślna lokalizacja z typu narzędzia
//            if (this.selectedToolForDetails.domyslna_lokalizacja) {
//                this.instanceModal.currentInstance.lokalizacja_id = this.selectedToolForDetails.domyslna_lokalizacja.id;
//            }
//            // Priorytet 2: Lokalizacja ostatniego egzemplarza
//            else if (Array.isArray(this.toolInstances) && this.toolInstances.length > 0) {
//                const lastInstance = this.toolInstances[0];
//                if (lastInstance && lastInstance.lokalizacja) {
//                    this.instanceModal.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
//                }
//            }
//        },
//
//        setupEditInstanceMode(instance) {
//            this.instanceModal.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
//            this.instanceModal.currentInstance = {
//                ...instance,
//                lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
//                faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
//                zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
//                ilosc: 1
//            };
//        },
//
//        async saveInstance() {
//            this.isSavingInstance = true;
//            this.instanceModal.errorMessage = '';
//
//            const method = this.instanceModal.mode === 'add' ? 'post' : 'patch';
//            const url = this.instanceModal.mode === 'add' ?
//                `${API_URL}/egzemplarze/` :
//                `${API_URL}/egzemplarze/${this.instanceModal.currentInstance.id}/`;
//
//            const payload = {
//                stan: this.instanceModal.currentInstance.stan,
//                lokalizacja_id: this.instanceModal.currentInstance.lokalizacja_id,
//                narzedzie_typ_id: this.instanceModal.currentInstance.narzedzie_typ_id,
//                faktura_zakupu_id: this.instanceModal.currentInstance.faktura_zakupu_id,
//                zamowienie_id: this.instanceModal.currentInstance.zamowienie_id
//            };
//
//            const ilosc = this.instanceModal.currentInstance.ilosc;
//
//            if (this.instanceModal.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
//                this.instanceModal.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
//                this.isSavingInstance = false;
//                return;
//            }
//
//            try {
//                if (this.instanceModal.mode === 'add' && ilosc > 1) {
//                    await this.createMultipleInstances(url, payload, ilosc);
//                } else {
//                    await this.createOrUpdateInstance(method, url, payload);
//                }
//
//                if (this.instanceModal.instance) {
//                    this.instanceModal.instance.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//
//            } catch (error) {
//                this.handleSaveInstanceError(error, ilosc);
//            } finally {
//                this.isSavingInstance = false;
//            }
//        },
//
//        async createMultipleInstances(url, payload, ilosc) {
//            const requests = [];
//            for (let i = 0; i < ilosc; i++) {
//                requests.push(axios.post(url, payload));
//            }
//            const responses = await Promise.all(requests);
//            console.log(`Pomyślnie dodano ${responses.length} egzemplarzy.`);
//        },
//
//        async createOrUpdateInstance(method, url, payload) {
//            await axios({ method, url, data: payload });
//            const action = this.instanceModal.mode === 'add' ? 'dodano' : 'zaktualizowano';
//            console.log(`Pomyślnie ${action} egzemplarz.`);
//        },
//
//        handleSaveInstanceError(error, ilosc) {
//            console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);
//
//            let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';
//
//            if (error.response?.data) {
//                if (typeof error.response.data === 'object') {
//                    errorMsg = Object.entries(error.response.data)
//                        .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
//                        .join('; ');
//                } else if (Array.isArray(error.response.data) && ilosc > 1) {
//                    const firstError = error.response.data[0];
//                    errorMsg = `Błąd przy dodawaniu seryjnym: ${JSON.stringify(firstError)}`;
//                } else {
//                    errorMsg = `Błąd: ${error.response.data}`;
//                }
//            } else if (error.message) {
//                const prefix = ilosc > 1 ? 'podczas dodawania seryjnego' : '';
//                errorMsg = `Wystąpił błąd sieci lub serwera ${prefix}: ${error.message}.`;
//            }
//
//            this.instanceModal.errorMessage = errorMsg;
//        },
//
//        openDeleteInstanceModal(instance) {
//            this.instanceToDelete = instance;
//
//            const toolName = instance.narzedzie_typ.podkategoria ?
//                `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}` :
//                instance.narzedzie_typ.opis;
//
//            if (instance.stan === 'uszkodzone') {
//                this.deleteModalMessage = `Ten egzemplarz (<strong>${toolName}</strong>) jest oznaczony jako uszkodzony. Zostanie przeniesiony do archiwum. Czy chcesz kontynuować?`;
//            } else {
//                this.deleteModalMessage = `Czy na pewno chcesz trwale usunąć egzemplarz: <strong>${toolName}</strong>?`;
//            }
//
//            if (this.modals.deleteInstanceModal) {
//                this.modals.deleteInstanceModal.show();
//            } else {
//                console.error("Modal 'deleteInstanceModal' not initialized!");
//            }
//        },
//
//        async confirmDeleteInstance() {
//            if (!this.instanceToDelete) {
//                return;
//            }
//
//            try {
//                await axios.delete(`${API_URL}/egzemplarze/${this.instanceToDelete.id}/`);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                if (this.selectedToolForDetails) {
//                    await this.getToolInstances(this.selectedToolForDetails);
//                }
//
//                await this.fetchInitialData();
//                this.instanceToDelete = null;
//            } catch (error) {
//                console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);
//
//                if (this.modals.deleteInstanceModal) {
//                    this.modals.deleteInstanceModal.hide();
//                }
//
//                alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
//            }
//        },
//    }
//}).mount('#app');
//

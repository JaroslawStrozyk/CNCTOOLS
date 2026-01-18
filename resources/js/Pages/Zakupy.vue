<template>
    <div class="zakupy-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">ZAKUPY</h2>
            <div class="header-buttons">
                <a :href="urls.ustawienia" class="btn btn-secondary">
                    <i class="pi pi-cog"></i> Ustawienia
                </a>
                <a :href="urls.zamowienia" class="btn btn-success">
                    <i class="pi pi-file"></i> Zamówienia
                </a>
                <a :href="urls.magazyn" class="btn btn-primary">
                    <i class="pi pi-building"></i> Magazyn
                </a>
                <div class="dropdown-wrapper">
                    <button class="user-dropdown-btn" @click="toggleUserMenu">
                        <i class="pi pi-user"></i>
                        {{ auth.user.first_name }} {{ auth.user.last_name }}
                        <i class="pi pi-chevron-down"></i>
                    </button>
                    <Menu ref="userMenu" id="user_menu" :model="userMenuItems" :popup="true" />
                </div>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="app-main">
            <!-- Górna tabela - Lista narzędzi -->
            <div class="tools-panel">
                <div class="panel-header">
                    <div class="search-box">
                        <input type="text" v-model="searchQuery" placeholder="Szukaj..." class="form-control search-input" />
                    </div>
                    <h3 class="panel-title">Lista narzędzi</h3>
                    <div class="filter-box">
                        <Dropdown
                            v-model="selectedKategoriaId"
                            :options="kategorieOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Wszystkie kategorie"
                            @change="onKategoriaChange"
                            class="filter-dropdown"
                        />
                        <Dropdown
                            v-model="selectedPodkategoriaId"
                            :options="filteredPodkategorieOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Wszystkie podkategorie"
                            :disabled="!selectedKategoriaId"
                            class="filter-dropdown"
                        />
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredTools"
                        :scrollable="true"
                        scrollHeight="flex"
                        selectionMode="single"
                        v-model:selection="selectedTool"
                        @row-select="onToolSelect"
                        @row-unselect="onToolUnselect"
                        dataKey="id"
                        class="tools-table"
                    >
                        <Column header="" style="width: 15px;">
                            <template #body="{ data }">
                                <div :class="getStatusClass(data)" class="status-indicator"></div>
                            </template>
                        </Column>
                        <Column header="Kategoria / Podkategoria">
                            <template #body="{ data }">
                                <span v-if="data.podkategoria">
                                    <strong>{{ data.podkategoria.kategoria.nazwa }}</strong> / {{ data.podkategoria.nazwa }}
                                </span>
                                <span v-else class="text-muted">Brak kategorii</span>
                            </template>
                        </Column>
                        <Column field="opis" header="Opis" />
                        <Column field="numer_katalogowy" header="Nr katalogowy" />
                        <Column header="Ilość całkowita" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <strong>{{ data.calkowita_ilosc }}</strong>
                            </template>
                        </Column>
                        <Column header="Limit minimalny" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                {{ data.stan_minimalny !== undefined ? data.stan_minimalny : 0 }}
                            </template>
                        </Column>
                        <Column header="Limit maksymalny" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                {{ data.stan_maksymalny !== undefined ? data.stan_maksymalny : 10 }}
                            </template>
                        </Column>
                        <Column header="" style="width: 100px; text-align: center;">
                            <template #header>
                                <Button icon="pi pi-plus" class="p-button-success p-button-sm" @click.stop="openToolModal()" title="Dodaj nowy typ narzędzia" />
                            </template>
                            <template #body="{ data }">
                                <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click.stop="openToolModal(data)" title="Edytuj typ narzędzia" />
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Dolna część - Zamówienia -->
            <div class="orders-panel">
                <TabView>
                    <TabPanel>
                        <template #header>
                            <span>Zamówienia</span>
                            <Badge v-if="selectedTool" :value="selectedTool.opis" severity="secondary" class="ml-2" />
                        </template>
                        <div class="tab-content-wrapper">
                            <div v-if="isLoadingOrders" class="loading-spinner">
                                <ProgressSpinner />
                                <span class="ml-2">Ładowanie zamówień...</span>
                            </div>
                            <div v-else-if="!selectedTool" class="empty-state">
                                Wybierz narzędzie, aby zobaczyć powiązane zamówienia.
                            </div>
                            <div v-else-if="!orders || orders.length === 0" class="empty-state">
                                Brak zamówień powiązanych z tym narzędziem.
                            </div>
                            <DataTable v-else :value="orders" :scrollable="true" scrollHeight="flex">
                                <Column header="Numer">
                                    <template #body="{ data }">
                                        <strong>{{ data.numer }}</strong>
                                    </template>
                                </Column>
                                <Column header="Dostawca">
                                    <template #body="{ data }">
                                        {{ data.dostawca?.nazwa_firmy || 'Brak dostawcy' }}
                                    </template>
                                </Column>
                                <Column header="Data utworzenia">
                                    <template #body="{ data }">
                                        {{ formatDateOnly(data.data_utworzenia) }}
                                    </template>
                                </Column>
                                <Column header="Status">
                                    <template #body="{ data }">
                                        <Tag :severity="getOrderStatusSeverity(data.status)" :value="getStatusLabel(data.status)" />
                                    </template>
                                </Column>
                                <Column header="Zrealizowane">
                                    <template #body="{ data }">
                                        <Tag v-if="data.status === 'completed'" severity="success" value="Tak" icon="pi pi-check-circle" />
                                        <Tag v-else-if="data.status === 'partially_received'" severity="warning" value="Częściowo" icon="pi pi-clock" />
                                        <Tag v-else severity="secondary" value="Nie" icon="pi pi-times-circle" />
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </TabPanel>
                </TabView>
            </div>
        </main>

        <!-- Modal: Edytuj/Dodaj typ narzędzia -->
        <Dialog v-model:visible="toolModalVisible" :header="isEditMode ? 'Edytuj typ narzędzia' : 'Dodaj nowy typ narzędzia'" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Kategoria / Podkategoria</label>
                    <Dropdown
                        v-model="currentTool.podkategoria_id"
                        :options="podkategorieGroupedOptions"
                        optionLabel="label"
                        optionValue="value"
                        optionGroupLabel="label"
                        optionGroupChildren="items"
                        placeholder="Brak (Główne)"
                    />
                </div>
                <div class="field">
                    <label>Opis / Specyfikacja</label>
                    <InputText v-model="currentTool.opis" />
                </div>
                <div class="field">
                    <label>Numer katalogowy (opcjonalnie)</label>
                    <InputText v-model="currentTool.numer_katalogowy" />
                </div>
                <div class="field">
                    <label>Limit minimalny</label>
                    <InputNumber v-model="currentTool.stan_minimalny" :min="0" />
                </div>
                <div class="field">
                    <label>Limit maksymalny</label>
                    <InputNumber v-model="currentTool.stan_maksymalny" :min="0" />
                </div>
                <div class="field">
                    <label>Obraz narzędzia</label>
                    <input type="file" @change="handleToolImageUpload" accept="image/*" class="p-inputtext" />
                </div>
                <div v-if="toolImagePreview" class="field text-center">
                    <p>Podgląd:</p>
                    <img :src="toolImagePreview" class="tool-image-preview" alt="Podgląd obrazka" />
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="toolModalVisible = false" />
                <Button :label="isEditMode ? 'Zapisz zmiany' : 'Dodaj typ'" icon="pi pi-check" @click="saveTool" />
            </template>
        </Dialog>

        <!-- Modal: O programie -->
        <Dialog v-model:visible="aboutModalVisible" header="O programie" :modal="true" :style="{ width: '450px' }">
            <div class="about-content">
                <div class="about-header">
                    <img :src="logoImage" alt="CNC Tools Logo" class="about-logo" />
                    <h4><strong>CNC Tools</strong></h4>
                    <p class="text-muted">System zarządzania narzędziami CNC</p>
                </div>
                <table class="about-table">
                    <tbody>
                        <tr>
                            <td class="label"><i class="pi pi-code"></i> Wersja:</td>
                            <td><strong>{{ infoProgram.WERSJA }}</strong></td>
                        </tr>
                        <tr>
                            <td class="label"><i class="pi pi-calendar"></i> Data modyfikacji:</td>
                            <td>{{ infoProgram.MODYFIKACJA }}</td>
                        </tr>
                        <tr>
                            <td class="label"><i class="pi pi-building"></i> Firma:</td>
                            <td>{{ infoProgram.FIRMA }}</td>
                        </tr>
                        <tr>
                            <td class="label"><i class="pi pi-user"></i> Autor:</td>
                            <td>{{ infoProgram.AUTOR }}</td>
                        </tr>
                        <tr>
                            <td class="label"><i class="pi pi-envelope"></i> Email:</td>
                            <td><a :href="infoProgram.EMAIL">{{ infoProgram.NEMAIL }}</a></td>
                        </tr>
                        <tr>
                            <td class="label"><i class="pi pi-phone"></i> Telefon:</td>
                            <td>{{ infoProgram.TEL }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <template #footer>
                <small class="text-muted">© {{ infoProgram.FIRMA }} 2025</small>
                <Button label="Zamknij" @click="aboutModalVisible = false" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';

// PrimeVue Components
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Dialog from 'primevue/dialog';
import Badge from 'primevue/badge';
import Tag from 'primevue/tag';
import Menu from 'primevue/menu';
import ProgressSpinner from 'primevue/progressspinner';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { firstName: '', lastName: '', username: '' }
        })
    },
    urls: {
        type: Object,
        default: () => ({
            ustawienia: '/ustawienia/',
            zamowienia: '/zamowienia/',
            magazyn: '/magazyn-inertia/',
            logout: '/logout/'
        })
    },
    infoProgram: {
        type: Object,
        default: () => ({})
    }
});

// Data
const tools = ref([]);
const kategorie = ref([]);
const orders = ref([]);

const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedTool = ref(null);
const searchQuery = ref('');
const isLoadingOrders = ref(false);

// Modals
const toolModalVisible = ref(false);
const aboutModalVisible = ref(false);
const isEditMode = ref(false);
const currentTool = ref({});
const toolImagePreview = ref(null);
const toolImageFile = ref(null);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
    {
        label: 'O programie',
        icon: 'pi pi-info-circle',
        command: () => { aboutModalVisible.value = true; }
    },
    { separator: true },
    {
        label: 'Wyjście',
        icon: 'pi pi-sign-out',
        command: () => { window.location.href = props.urls.logout; }
    }
]);

// Computed
const filteredTools = computed(() => {
    let filtered = [...tools.value];

    if (selectedPodkategoriaId.value) {
        filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.id === selectedPodkategoriaId.value);
    } else if (selectedKategoriaId.value) {
        filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.kategoria.id === selectedKategoriaId.value);
    }

    if (searchQuery.value.trim() !== '') {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(tool => {
            const catalogNumber = tool.numer_katalogowy || '';
            const kategoriaNazwa = tool.podkategoria ? tool.podkategoria.kategoria.nazwa.toLowerCase() : '';
            const podkategoriaNazwa = tool.podkategoria ? tool.podkategoria.nazwa.toLowerCase() : '';
            return kategoriaNazwa.includes(query) ||
                   podkategoriaNazwa.includes(query) ||
                   tool.opis.toLowerCase().includes(query) ||
                   catalogNumber.toLowerCase().includes(query);
        });
    }

    // Sortowanie
    return filtered.sort((a, b) => {
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
});

const kategorieOptions = computed(() => {
    return [
        { label: 'Wszystkie kategorie', value: null },
        ...kategorie.value.map(k => ({ label: k.nazwa, value: k.id }))
    ];
});

const filteredPodkategorieOptions = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return [
        { label: 'Wszystkie podkategorie', value: null },
        ...kategoria.podkategorie.map(p => ({ label: p.nazwa, value: p.id }))
    ];
});

const podkategorieGroupedOptions = computed(() => {
    return kategorie.value.map(kategoria => ({
        label: kategoria.nazwa,
        items: kategoria.podkategorie.map(p => ({
            label: `${kategoria.nazwa} / ${p.nazwa}`,
            value: p.id
        }))
    }));
});

// Methods
const toggleUserMenu = (event) => {
    userMenu.value.toggle(event);
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const getStatusClass = (tool) => {
    const iloscCalkowita = tool.calkowita_ilosc;
    const limitMin = tool.stan_minimalny !== undefined ? tool.stan_minimalny : 0;
    const limitMax = tool.stan_maksymalny !== undefined ? tool.stan_maksymalny : 10;

    if (iloscCalkowita >= limitMax) {
        return 'status-green';
    } else if (iloscCalkowita > limitMin && iloscCalkowita < limitMax) {
        return 'status-orange';
    } else {
        return 'status-red';
    }
};

const formatDateOnly = (dateString) => {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '-';
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    } catch (e) {
        return '-';
    }
};

const getStatusLabel = (status) => {
    const labels = {
        'draft': 'Szkic',
        'verified': 'Zweryfikowane',
        'sent': 'Wysłane',
        'partially_received': 'Częściowo zrealizowane',
        'completed': 'Zrealizowane'
    };
    return labels[status] || status;
};

const getOrderStatusSeverity = (status) => {
    const map = {
        'draft': 'secondary',
        'verified': 'info',
        'sent': 'primary',
        'partially_received': 'warning',
        'completed': 'success'
    };
    return map[status] || 'secondary';
};

const onToolSelect = async (event) => {
    const tool = event.data;
    await getToolOrders(tool);
};

const onToolUnselect = () => {
    orders.value = [];
};

const getToolOrders = async (tool) => {
    if (!tool || !tool.id) {
        orders.value = [];
        return;
    }

    isLoadingOrders.value = true;
    orders.value = [];

    try {
        const response = await axios.get(`${API_URL}/zamowienia/?narzedzie_id=${tool.id}`);
        let results = response.data.results || response.data;
        if (!Array.isArray(results)) results = [];
        orders.value = results.sort((a, b) => new Date(b.data_utworzenia) - new Date(a.data_utworzenia));
    } catch (error) {
        console.error(`Błąd ładowania zamówień:`, error.response?.data || error.message);
        orders.value = [];
    } finally {
        isLoadingOrders.value = false;
    }
};

const openToolModal = (tool = null) => {
    isEditMode.value = !!tool;
    toolImagePreview.value = null;
    toolImageFile.value = null;

    if (isEditMode.value) {
        currentTool.value = {
            ...tool,
            podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null
        };
        if (tool.obraz) {
            toolImagePreview.value = tool.obraz;
        }
    } else {
        currentTool.value = {
            podkategoria_id: null,
            opis: '',
            numer_katalogowy: '',
            stan_minimalny: 0,
            stan_maksymalny: 10,
            obraz: null
        };
    }

    toolModalVisible.value = true;
};

const handleToolImageUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
        toolImageFile.value = null;
        toolImagePreview.value = (isEditMode.value && currentTool.value.obraz) ? currentTool.value.obraz : null;
        return;
    }
    toolImageFile.value = file;
    toolImagePreview.value = URL.createObjectURL(file);
};

const saveTool = async () => {
    const formData = new FormData();
    formData.append('opis', currentTool.value.opis);
    formData.append('stan_minimalny', currentTool.value.stan_minimalny !== undefined ? currentTool.value.stan_minimalny : 0);
    formData.append('stan_maksymalny', currentTool.value.stan_maksymalny !== undefined ? currentTool.value.stan_maksymalny : 10);

    if (currentTool.value.podkategoria_id) {
        formData.append('podkategoria_id', currentTool.value.podkategoria_id);
    }
    if (currentTool.value.numer_katalogowy) {
        formData.append('numer_katalogowy', currentTool.value.numer_katalogowy);
    }
    if (toolImageFile.value) {
        formData.append('obraz', toolImageFile.value);
    }

    const method = isEditMode.value ? 'patch' : 'post';
    const url = isEditMode.value ? `${API_URL}/narzedzia/${currentTool.value.id}/` : `${API_URL}/narzedzia/`;

    try {
        await axios({ method, url, data: formData, headers: { 'Content-Type': 'multipart/form-data' } });
        toolModalVisible.value = false;
        await fetchInitialData();
    } catch (error) {
        console.error("Błąd zapisu:", error.response?.data || error.message);
        alert('Wystąpił błąd podczas zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message));
    }
};

const fetchInitialData = async () => {
    try {
        const [toolsRes, categoriesRes] = await Promise.all([
            axios.get(`${API_URL}/narzedzia-zakupy/`),
            axios.get(`${API_URL}/kategorie/`)
        ]);
        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;
    } catch (error) {
        console.error("Błąd ładowania danych:", error.response?.data || error.message);
    }
};

onMounted(() => {
    fetchInitialData();
});
</script>

<style scoped>
.zakupy-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
}

.header-buttons a {
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

.app-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 24px;
    gap: 16px;
    min-height: 0;
}

.tools-panel, .orders-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    min-height: 0;
}

.search-box { display: flex; align-items: center; }
.filter-box { display: flex; gap: 8px; }
.filter-dropdown { min-width: 180px; }
.panel-body { flex: 1; overflow: auto; min-height: 0; background: #212529; }

.status-indicator { width: 12px; height: 100%; min-height: 20px; border-radius: 2px; }
.status-green { background-color: #198754; }
.status-orange { background-color: #d97706; }
.status-red { background-color: #dc3545; }

:deep(.p-tabview) { height: 100%; display: flex; flex-direction: column; }
:deep(.p-tabview-panels) { flex: 1; min-height: 0; }
:deep(.p-tabview-panel) { height: 100%; }
.tab-content-wrapper { height: 100%; display: flex; flex-direction: column; }

.tool-image-preview { max-width: 150px; border-radius: 8px; border: 1px solid var(--dark-border); }
.about-content { text-align: center; }
.about-header { margin-bottom: 24px; }
.about-logo { width: 80px; height: 80px; }
.about-table { width: 100%; text-align: left; }
.about-table td { padding: 8px 0; color: var(--dark-text-primary); }
.about-table .label { text-align: right; color: var(--dark-text-muted); padding-right: 16px; width: 40%; }
</style>

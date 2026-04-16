<template>
    <div class="zakupy-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">ZAKUPY</h2>
            <div class="header-buttons">
                <button class="btn btn-info" @click="openHelp" title="Pomoc — przewodnik po module">
                    <i class="pi pi-question-circle"></i> Pomoc
                </button>
                <div class="dropdown-wrapper">
                    <button class="btn btn-success" @click="toggleDzialaniaMenu">
                        <i class="pi pi-th-large"></i> Działania
                        <i class="pi pi-chevron-down" style="margin-left: 4px; font-size: 0.75rem;"></i>
                    </button>
                    <Menu ref="dzialaniaMenu" id="dzialania_menu" :model="dzialaniaMenuItems" :popup="true" />
                </div>
                <div class="dropdown-wrapper">
                    <button class="btn btn-primary" @click="toggleMiejscaMenu">
                        <i class="pi pi-building"></i> Miejsca
                        <i class="pi pi-chevron-down" style="margin-left: 4px; font-size: 0.75rem;"></i>
                    </button>
                    <Menu ref="miejscaMenu" id="miejsca_menu" :model="miejscaMenuItems" :popup="true" />
                </div>
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
                        <input type="text" v-model="searchInput" placeholder="Szukaj..." class="form-control search-input" />
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
                        :loading="isLoadingTools"
                        :scrollable="true"
                        scrollHeight="flex"
                        tableLayout="fixed"
                        :virtualScrollerOptions="{ itemSize: 36 }"
                        selectionMode="single"
                        v-model:selection="selectedTool"
                        @row-select="onToolSelect"
                        @row-unselect="onToolUnselect"
                        dataKey="id"
                        class="tools-table"
                    >
                        <Column header="" style="width: 15px;">
                            <template #body="{ data }">
                                <div :class="data.reczna_kontrola ? 'status-blue' : getStatusClass(data)" class="status-indicator"></div>
                            </template>
                        </Column>
                        <Column header="Kategoria / Podkategoria" style="width: 330px;">
                            <template #body="{ data }">
                                <span v-if="data.podkategoria">
                                    <strong>{{ data.podkategoria.kategoria.nazwa }}</strong> / {{ data.podkategoria.nazwa }}
                                </span>
                                <span v-else class="text-muted">Brak kategorii</span>
                            </template>
                        </Column>
                        <Column field="opis" header="Opis" />
                        <Column field="numer_katalogowy" header="Nr katalogowy" style="width: 200px;" />
                        <Column header="Ilość całkowita" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <strong :class="{ 'zero-value': data.calkowita_ilosc === 0 }">{{ data.calkowita_ilosc }}</strong>
                            </template>
                        </Column>
                        <Column header="Limit minimalny" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': (data.stan_minimalny || 0) === 0 }">{{ data.stan_minimalny !== undefined ? data.stan_minimalny : 0 }}</span>
                            </template>
                        </Column>
                        <Column header="Limit maksymalny" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': (data.stan_maksymalny || 0) === 0 }">{{ data.stan_maksymalny !== undefined ? data.stan_maksymalny : 10 }}</span>
                            </template>
                        </Column>
                        <Column header="Kontrola" style="width: 90px; text-align: center;">
                            <template #body="{ data }">
                                <Tag v-if="data.reczna_kontrola" value="Ręczna" severity="secondary" class="control-reczna" />
                                <span v-else class="control-auto">Auto</span>
                            </template>
                        </Column>
                        <Column header="Ręczne dodanie" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <span v-if="data.reczna_kontrola" :class="{ 'zero-value': (data.reczne_dodanie || 0) === 0 }">
                                    <strong>{{ data.reczne_dodanie || 0 }}</strong>
                                </span>
                                <span v-else class="text-muted">-</span>
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
                                <Column header="Cena jedn." style="width: 150px; text-align: right;">
                                    <template #body="{ data }">
                                        <span :class="{ 'text-muted': isCenaZero(getPozycjaCena(data)) }">
                                            {{ formatCenaPLN(getPozycjaCena(data)) }}
                                        </span>
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
                    <InputNumber v-model="currentTool.stan_maksymalny" :min="0" :disabled="currentTool.reczna_kontrola" />
                </div>
                <div class="field">
                    <div class="checkbox-row">
                        <Checkbox v-model="currentTool.reczna_kontrola" :binary="true" inputId="reczna_kontrola" />
                        <label for="reczna_kontrola" class="checkbox-label">Ręczna kontrola zamówień</label>
                    </div>
                </div>
                <div v-if="currentTool.reczna_kontrola" class="field">
                    <label>Ręczne dodanie (ilość do zamówienia)</label>
                    <InputNumber v-model="currentTool.reczne_dodanie" :min="0" />
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
                <div class="about-footer">
                    <small class="copyright">© {{ infoProgram.FIRMA }} 2025</small>
                    <Button label="Zamknij" class="btn-modal-secondary" @click="aboutModalVisible = false" />
                </div>
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
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
import Checkbox from 'primevue/checkbox';
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
            magazyn: '/magazyn/',
            zapotrzebowania: '/zapotrzebowania/',
            realizacja: '/realizacja/',
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
const searchInput = ref('');
const searchQuery = ref('');
let searchDebounceTimer = null;
watch(searchInput, (val) => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => { searchQuery.value = val; }, 250);
});
const isLoadingTools = ref(true);
const isLoadingOrders = ref(false);

// Modals
const toolModalVisible = ref(false);
const aboutModalVisible = ref(false);
const isEditMode = ref(false);
const currentTool = ref({});
const toolImagePreview = ref(null);
const toolImageFile = ref(null);

// Menu Działania
const dzialaniaMenu = ref(null);
const dzialaniaMenuItems = ref([
    { label: 'Zapotrzebowania', icon: 'pi pi-inbox', command: () => { window.location.href = props.urls.zapotrzebowania + '?from=zakupy'; } },
    { label: 'Zamówienia', icon: 'pi pi-file', command: () => { window.location.href = props.urls.zamowienia; } },
    { label: 'Realizacje', icon: 'pi pi-box', visible: false, command: () => { window.location.href = props.urls.realizacja; } }
]);

// Pomoc — otwiera w nowym oknie typu popup (działa też w trybie PWA)
const openHelp = () => {
    const url = props.urls.pomoc_zakupy || '/pomoc/zakupy/';
    const features = 'noopener,noreferrer,width=1100,height=860,resizable=yes,scrollbars=yes';
    window.open(url, 'pomoc-zakupy', features);
};
const toggleDzialaniaMenu = (event) => { dzialaniaMenu.value.toggle(event); };

// Menu Miejsca
const miejscaMenu = ref(null);
const miejscaMenuItems = ref([
    { label: 'Magazyn', icon: 'pi pi-building', command: () => { window.location.href = props.urls.magazyn; } }
]);
const toggleMiejscaMenu = (event) => { miejscaMenu.value.toggle(event); };

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
    {
        label: 'Ustawienia',
        icon: 'pi pi-cog',
        command: () => { window.location.href = props.urls.ustawienia + '?from=zakupy'; }
    },
    { separator: true },
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

// Zwraca cenę jednostkową pozycji zamówienia odpowiadającej zaznaczonemu narzędziu
const getPozycjaCena = (zamowienie) => {
    if (!selectedTool.value || !zamowienie?.pozycje) return null;
    const pozycja = zamowienie.pozycje.find(p => p.narzedzie_typ?.id === selectedTool.value.id);
    return pozycja?.cena_jednostkowa;
};

// Format waluty PL — np. "0,00 zł", "12,50 zł"
const formatCenaPLN = (cena) => {
    const num = Number(cena);
    if (cena == null || cena === '' || isNaN(num)) return '0,00 zł';
    return num.toFixed(2).replace('.', ',') + ' zł';
};

// True gdy cena jest zerowa lub brak — używane do szarego oznaczenia w tabeli
const isCenaZero = (cena) => {
    const num = Number(cena);
    return cena == null || cena === '' || isNaN(num) || num === 0;
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
            reczna_kontrola: false,
            reczne_dodanie: 0,
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
    formData.append('reczna_kontrola', currentTool.value.reczna_kontrola ? 'true' : 'false');
    formData.append('reczne_dodanie', currentTool.value.reczne_dodanie || 0);

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
    } finally {
        isLoadingTools.value = false;
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
.status-blue { background-color: #0d6efd; }

.zero-value { color: #6c757d !important; }
.control-auto { color: #6c757d; font-size: 0.85rem; border: 1px solid #495057; border-radius: 4px; padding: 2px 8px; }
.control-reczna :deep(.p-tag-value) { color: #5bc0de !important; }

.checkbox-row { display: flex; align-items: center; gap: 8px; }
.checkbox-label { margin: 0; cursor: pointer; }

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

.about-footer { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.about-footer .copyright { color: #6c757d !important; font-size: 0.85rem; }
</style>

<style>
/* Menu Działania / Miejsca — globalny styl (nie scoped) */
#dzialania_menu,
#miejsca_menu {
    min-width: 180px !important;
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
    padding: 6px 0 !important;
}
#dzialania_menu_list,
#miejsca_menu_list {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}
#dzialania_menu_list li,
#miejsca_menu_list li {
    margin: 0 !important;
    padding: 0 !important;
}
#dzialania_menu_list li > div,
#miejsca_menu_list li > div {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    transition: background-color 0.15s !important;
}
#dzialania_menu_list li > div:hover,
#miejsca_menu_list li > div:hover {
    background-color: #3d444d !important;
}
#dzialania_menu_list li > div > a,
#dzialania_menu_list li > div > div,
#miejsca_menu_list li > div > a,
#miejsca_menu_list li > div > div {
    display: flex !important;
    align-items: center !important;
    padding: 10px 16px !important;
    gap: 10px !important;
    text-decoration: none !important;
    cursor: pointer !important;
}
#dzialania_menu_list li > div span[class*="icon"],
#dzialania_menu_list li > div i,
#dzialania_menu_list li > div .pi,
#miejsca_menu_list li > div span[class*="icon"],
#miejsca_menu_list li > div i,
#miejsca_menu_list li > div .pi {
    color: #adb5bd !important;
    font-size: 1rem !important;
}
#dzialania_menu_list li > div span:not([class*="icon"]):not(.pi),
#miejsca_menu_list li > div span:not([class*="icon"]):not(.pi) {
    color: #dee2e6 !important;
    font-size: 14px !important;
}
</style>

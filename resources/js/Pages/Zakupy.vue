<template>
    <div class="zakupy-app" :class="{ 'light-theme': isLightTheme }">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">ZAKUPY</h2>
            <div class="header-buttons">
                <button class="btn btn-info" @click="openHelp" title="Pomoc — przewodnik po module">
                    <i class="pi pi-question-circle"></i> Pomoc
                </button>
                <button class="btn btn-success" @click="goToZapotrzebowania">
                    <i class="pi pi-inbox"></i> Zapotrzebowania
                </button>
                <button class="btn btn-success" @click="goToZamowienia">
                    <i class="pi pi-file"></i> Zamówienia
                </button>
                <button class="btn btn-primary" @click="goToMagazyn">
                    <i class="pi pi-building"></i> Magazyn
                </button>
                <!-- Toggle motywu jasnego — ukryty, kod zachowany na przyszłość.
                     Aby aktywować: zmień v-if="false" na v-if="true" + przywróć odczyt z localStorage w onMounted. -->
                <button v-if="false" class="btn-theme-toggle" @click="toggleTheme" :title="isLightTheme ? 'Przełącz na motyw ciemny' : 'Przełącz na motyw jasny'">
                    <i :class="isLightTheme ? 'pi pi-moon' : 'pi pi-sun'"></i>
                </button>
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
                        <Column header="Cena jednostkowa" style="width: 130px; text-align: right;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': isCenaZero(data.cena_jednostkowa) }">
                                    {{ formatCenaPLN(data.cena_jednostkowa) }}
                                </span>
                            </template>
                        </Column>
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
                            <Badge v-if="selectedTool" :value="`  ${selectedTool.opis}  `" severity="secondary" class="ml-2" />
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
                    <label>Cena jednostkowa</label>
                    <InputNumber
                        v-model="currentTool.cena_jednostkowa"
                        mode="decimal"
                        :minFractionDigits="2"
                        :maxFractionDigits="2"
                        :min="0"
                        suffix=" zł"
                    />
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
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

// Pomoc — otwiera w nowym oknie typu popup (działa też w trybie PWA)
const openHelp = () => {
    const url = props.urls.pomoc_zakupy || '/pomoc/zakupy/';
    const features = 'noopener,noreferrer,width=1100,height=860,resizable=yes,scrollbars=yes';
    window.open(url, 'pomoc-zakupy', features);
};

const goToZapotrzebowania = () => { window.location.href = props.urls.zapotrzebowania + '?from=zakupy'; };
const goToZamowienia = () => { window.location.href = props.urls.zamowienia; };
const goToMagazyn = () => { window.location.href = props.urls.magazyn; };

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
        'draft': 'Wersja robocza',
        'pending_approval': 'Oczekuje na zatwierdzenie',
        'verified': 'Zatwierdzone',
        'sent': 'Wysłane',
        'partially_received': 'Częściowo odebrane',
        'completed': 'Zrealizowane'
    };
    return labels[status] || status;
};

const getOrderStatusSeverity = (status) => {
    const map = {
        'draft': 'secondary',
        'pending_approval': 'warning',
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
            cena_jednostkowa: null,
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
    // cena_jednostkowa zawsze wysyłana — pusty string → DRF interpretuje jako None (DecimalField null=True)
    formData.append(
        'cena_jednostkowa',
        currentTool.value.cena_jednostkowa != null && currentTool.value.cena_jednostkowa !== ''
            ? currentTool.value.cena_jednostkowa
            : ''
    );
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

// === Light/dark theme toggle (eksperyment ZACHOWANY na przyszłość, obecnie WYŁĄCZONY) ===
// Aby aktywować: (a) zmień v-if="false" na v-if="true" w buttonie .btn-theme-toggle (template),
// (b) w onMounted przywróć odczyt z localStorage (zakomentowana linia poniżej).
// Style light theme zostają w drugim <style> bloku na końcu pliku.
const THEME_STORAGE_KEY = 'zakupy-theme';
const isLightTheme = ref(false);

const toggleTheme = () => { isLightTheme.value = !isLightTheme.value; };

watch(isLightTheme, (val) => {
    localStorage.setItem(THEME_STORAGE_KEY, val ? 'light' : 'dark');
    document.body.classList.toggle('zakupy-light-active', val);
});

onMounted(() => {
    fetchInitialData();
    // Eksperyment wyłączony — jednorazowe wyczyszczenie zapamiętanej preferencji usera,
    // by powrót do dark był wymuszony nawet jeśli wcześniej miał ustawiony light.
    localStorage.removeItem(THEME_STORAGE_KEY);
    document.body.classList.remove('zakupy-light-active');
    // Aby przywrócić eksperyment — odkomentuj poniższe i zakomentuj 2 linie wyżej:
    // isLightTheme.value = localStorage.getItem(THEME_STORAGE_KEY) === 'light';
    // document.body.classList.toggle('zakupy-light-active', isLightTheme.value);
});

onBeforeUnmount(() => {
    document.body.classList.remove('zakupy-light-active');
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

/* === Theme toggle button (działa w obu motywach) === */
.btn-theme-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    margin-right: 4px;
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 4px;
    color: #ffc107;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.15s ease-in-out;
}
.btn-theme-toggle:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.4);
}
</style>

<!-- ============================================
     MOTYW JASNY DLA ZAKUPY.VUE — gotowy, OBECNIE WYŁĄCZONY (zatwierdzony 2026-05-27)
     ============================================
     Status: kompletny, przetestowany, do aktywacji w przyszłości.

     Mechanizm: klasa .light-theme na .zakupy-app + body.zakupy-light-active (dla
     portali PrimeVue: Dialog, Dropdown panel, Menu popup). Wszystkie reguły mają
     !important — bije globalny dark-theme.css i primevue-theme-dark.css.

     Aby aktywować (3 zmiany w tym pliku):
       1. <template> — button .btn-theme-toggle: v-if="false" → v-if="true"
       2. <script>  — onMounted: zakomentuj 2 linie removeItem+remove,
                      odkomentuj 2 linie isLightTheme=... i classList.toggle
       3. (opcjonalnie) usuń ten komentarz i przywróć poprzedni "EKSPERYMENTALNY"

     Pokrycie: header, panele (Lista narzędzi + Zamówienia), DataTable (incl. virtual
     scroller wrappers), TabView, Dropdown trigger + panel (z grupami), Tag, Badge,
     Modal Dialog (labels, inputs, checkbox, file input), scrollbary (bez czarnego
     obrysu Chromium), ikony przycisków PrimeVue.

     Paleta: tło aplikacji #f6f8fa, panele #ffffff, akcent #0d6efd (Bootstrap primary),
     tekst #212529, border #dee2e6. Cienie multi-layer Material-style.
     ============================================ -->
<style>
/* === CSS variables override === */
.zakupy-app.light-theme {
    --dark-bg-primary: #f6f8fa;
    --dark-bg-secondary: #ffffff;
    --dark-bg-tertiary: #f1f3f5;
    --dark-bg-card: #ffffff;
    --dark-bg-hover: #eef1f4;
    --dark-border: #dee2e6;
    --dark-text-primary: #212529;
    --dark-text-secondary: #495057;
    --dark-text-muted: #6c757d;
    background-color: #f6f8fa;
    color: #212529;
}

/* === Nagłówek strony === */
.zakupy-app.light-theme .app-header {
    background: linear-gradient(to bottom, #ffffff, #e9ecef) !important;
    color: #212529 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12), 0 1px 0 rgba(0, 0, 0, 0.08) !important;
}
.zakupy-app.light-theme .header-title {
    color: #0d6efd !important;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.6);
}

/* Theme toggle w trybie jasnym */
.zakupy-app.light-theme .btn-theme-toggle {
    border-color: #ced4da;
    color: #495057;
}
.zakupy-app.light-theme .btn-theme-toggle:hover {
    background-color: #f1f3f5;
    border-color: #adb5bd;
}

/* === Panele (główne karty) — wyraźny cień dla głębi === */
.zakupy-app.light-theme .tools-panel,
.zakupy-app.light-theme .orders-panel {
    background: #ffffff !important;
    border: 1px solid #e5e9ed !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08) !important;
}
.zakupy-app.light-theme .panel-header {
    background: #f8f9fa;
    box-shadow: inset 0 -1px 0 #dee2e6;
}
.zakupy-app.light-theme .panel-title {
    color: #0d6efd;
}
.zakupy-app.light-theme .panel-body {
    background: #ffffff;
}

/* === Inputs / Forms (z !important — dark-theme.css:214 ma !important) === */
.zakupy-app.light-theme .form-control,
.zakupy-app.light-theme .search-input {
    background-color: #ffffff !important;
    color: #212529 !important;
    border: 1px solid #ced4da !important;
}
.zakupy-app.light-theme .form-control:focus,
.zakupy-app.light-theme .search-input:focus {
    background-color: #ffffff !important;
    color: #212529 !important;
    border-color: #86b7fe !important;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.2) !important;
}
.zakupy-app.light-theme .form-control::placeholder,
.zakupy-app.light-theme .search-input::placeholder {
    color: #6c757d !important;
}

/* === Przyciski .btn — zachowują kolory, mocniejszy cień dla widoczności na białym === */
.zakupy-app.light-theme .btn {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.18), 0 1px 2px rgba(0, 0, 0, 0.12) !important;
}
.zakupy-app.light-theme .btn:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.22), 0 2px 4px rgba(0, 0, 0, 0.14) !important;
}
.zakupy-app.light-theme .btn:active {
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
}
.zakupy-app.light-theme .user-dropdown-btn {
    box-shadow: 0 1px 3px rgba(220, 53, 69, 0.35), 0 1px 2px rgba(0, 0, 0, 0.1) !important;
}
.zakupy-app.light-theme .user-dropdown-btn:hover {
    box-shadow: 0 2px 6px rgba(220, 53, 69, 0.4), 0 2px 4px rgba(0, 0, 0, 0.12) !important;
}

/* === Status indicator i etykiety pomocnicze === */
.zakupy-app.light-theme .zero-value { color: #adb5bd !important; }
.zakupy-app.light-theme .control-auto {
    color: #6c757d;
    border-color: #dee2e6;
    background-color: #f8f9fa;
}

/* === PrimeVue DataTable — pokrycie wszystkich wrapperów + wierszy === */
.zakupy-app.light-theme .p-datatable,
.zakupy-app.light-theme .p-datatable-wrapper,
.zakupy-app.light-theme .p-virtualscroller,
.zakupy-app.light-theme .p-virtualscroller-content,
.zakupy-app.light-theme .p-datatable-table {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #212529 !important;
}
.zakupy-app.light-theme .p-datatable .p-datatable-thead > tr > th {
    background: linear-gradient(to bottom, #ffffff, #f1f3f5) !important;
    color: #212529 !important;
    border-bottom: 1px solid #dee2e6 !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}
/* Wiersze tabeli — super-specyficzność (html body) + tło na tr ORAZ td (td może maskować tr) */
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr,
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr > td {
    background: #ffffff !important;
    background-color: #ffffff !important;
    background-image: none !important;
    color: #212529 !important;
}
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr:nth-child(even),
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr:nth-child(even) > td {
    background: #fafbfc !important;
    background-color: #fafbfc !important;
}
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr > td {
    border-bottom: 1px solid #eef1f4 !important;
}
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr:hover,
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr:hover > td {
    background: #eef5ff !important;
    background-color: #eef5ff !important;
}
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr.p-highlight,
html body.zakupy-light-active .p-datatable .p-datatable-tbody > tr.p-highlight > td {
    background: #cfe2ff !important;
    background-color: #cfe2ff !important;
    color: #084298 !important;
}
.zakupy-app.light-theme .p-datatable .p-sortable-column:hover {
    background: #eef1f4 !important;
    color: #212529 !important;
}
.zakupy-app.light-theme .p-datatable .p-sortable-column.p-highlight {
    background: linear-gradient(to bottom, #ffffff, #e7f1ff) !important;
    color: #0d6efd !important;
}
.zakupy-app.light-theme .p-datatable .p-sortable-column .p-sortable-column-icon {
    color: #6c757d !important;
}
.zakupy-app.light-theme .p-datatable-loading-overlay {
    background: rgba(255, 255, 255, 0.7) !important;
}
.zakupy-app.light-theme .p-datatable-loading-icon,
.zakupy-app.light-theme .p-datatable-loading-icon svg {
    color: #0d6efd !important;
    fill: #0d6efd !important;
}

/* === PrimeVue Tag (severity badges) === */
.zakupy-app.light-theme .p-tag.p-tag-secondary { background: #e9ecef; color: #495057; }
.zakupy-app.light-theme .p-tag.p-tag-info { background: #cff4fc; color: #055160; }
.zakupy-app.light-theme .p-tag.p-tag-primary { background: #cfe2ff; color: #084298; }
.zakupy-app.light-theme .p-tag.p-tag-success { background: #d1e7dd; color: #0a3622; }
.zakupy-app.light-theme .p-tag.p-tag-warning { background: #fff3cd; color: #664d03; }
.zakupy-app.light-theme .p-tag.p-tag-danger { background: #f8d7da; color: #58151c; }

/* === PrimeVue Badge (opis wybranego narzędzia w nagłówku tabu) ===
   Flex-center bije line-height:1.5rem z PrimeVue (wcześniej tekst spadał na baseline) */
.zakupy-app.light-theme .p-badge.p-badge-secondary {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    height: auto !important;
    background: #fff3cd !important;
    color: #664d03 !important;
    border: 1px solid #ffe69c !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    border-radius: 4px !important;
}

/* === Ikony przycisków PrimeVue (success/secondary/primary/danger) — białe === */
.zakupy-app.light-theme .p-button.p-button-success,
.zakupy-app.light-theme .p-button.p-button-secondary,
.zakupy-app.light-theme .p-button.p-button-primary,
.zakupy-app.light-theme .p-button.p-button-danger,
.zakupy-app.light-theme .p-button.p-button-help {
    color: #ffffff !important;
}
.zakupy-app.light-theme .p-button.p-button-success .p-button-icon,
.zakupy-app.light-theme .p-button.p-button-secondary .p-button-icon,
.zakupy-app.light-theme .p-button.p-button-primary .p-button-icon,
.zakupy-app.light-theme .p-button.p-button-danger .p-button-icon,
.zakupy-app.light-theme .p-button.p-button-help .p-button-icon {
    color: #ffffff !important;
}

/* === PrimeVue TabView (z !important — wrapper .p-tabview-nav-container ma gradient) === */
.zakupy-app.light-theme .p-tabview {
    background: transparent !important;
}
.zakupy-app.light-theme .p-tabview-nav-container {
    background: linear-gradient(to bottom, #ffffff, #f1f3f5) !important;
    box-shadow: inset 0 -1px 0 #dee2e6, 0 1px 2px rgba(0, 0, 0, 0.04) !important;
}
.zakupy-app.light-theme .p-tabview-nav {
    background: transparent !important;
    border: none !important;
}
.zakupy-app.light-theme .p-tabview-nav li .p-tabview-nav-link {
    background: transparent !important;
    color: #495057 !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
}
.zakupy-app.light-theme .p-tabview-nav li .p-tabview-nav-link:hover {
    background: rgba(13, 110, 253, 0.06) !important;
    color: #0d6efd !important;
}
.zakupy-app.light-theme .p-tabview-nav li.p-highlight .p-tabview-nav-link {
    background: rgba(13, 110, 253, 0.08) !important;
    color: #0d6efd !important;
    border-bottom-color: #0d6efd !important;
}
.zakupy-app.light-theme .p-tabview-panels {
    background: #ffffff !important;
    color: #212529 !important;
}

/* === PrimeVue Dropdown trigger (z !important — dark-theme.css:559 ma !important) === */
.zakupy-app.light-theme .p-dropdown {
    background: #ffffff !important;
    border: 1px solid #ced4da !important;
    color: #212529 !important;
}
.zakupy-app.light-theme .p-dropdown:not(.p-disabled):hover {
    border-color: #86b7fe !important;
}
.zakupy-app.light-theme .p-dropdown:not(.p-disabled).p-focus {
    border-color: #86b7fe !important;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.2) !important;
}
.zakupy-app.light-theme .p-dropdown .p-dropdown-label {
    color: #212529 !important;
}
.zakupy-app.light-theme .p-dropdown .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
}
.zakupy-app.light-theme .p-dropdown .p-dropdown-trigger {
    color: #6c757d !important;
}
.zakupy-app.light-theme .p-dropdown.p-disabled {
    background: #e9ecef !important;
    color: #adb5bd !important;
}

/* === PrimeVue InputText (wewnętrzny span Dropdownu też ma .p-inputtext) === */
.zakupy-app.light-theme .p-inputtext,
.zakupy-app.light-theme .p-dropdown-label.p-inputtext {
    background: #ffffff !important;
    border-color: #ced4da !important;
    color: #212529 !important;
}
.zakupy-app.light-theme .p-inputtext:focus {
    border-color: #86b7fe !important;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.2) !important;
}
.zakupy-app.light-theme .p-inputtext.p-placeholder,
.zakupy-app.light-theme .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
    background: #ffffff !important;
}
/* W disabled dropdownie label trzyma się dropdownu (.p-dropdown.p-disabled .p-dropdown-label) */
.zakupy-app.light-theme .p-dropdown.p-disabled .p-dropdown-label {
    background: #e9ecef !important;
    color: #adb5bd !important;
}

/* === PrimeVue InputNumber / Checkbox === */
.zakupy-app.light-theme .p-inputnumber-input {
    background: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
}
.zakupy-app.light-theme .p-checkbox .p-checkbox-box {
    background: #ffffff;
    border: 1px solid #ced4da;
}
.zakupy-app.light-theme .p-checkbox .p-checkbox-box.p-highlight {
    background: #0d6efd;
    border-color: #0d6efd;
}

/* ============================================
   PORTALE PrimeVue (renderowane do <body>)
   Wymagają body.zakupy-light-active
   ============================================ */

/* Dropdown panel (lista wyboru) — pełen zestaw wrapperów */
body.zakupy-light-active .p-dropdown-panel,
body.zakupy-light-active .p-dropdown-items-wrapper,
body.zakupy-light-active .p-dropdown-items {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #212529 !important;
}
body.zakupy-light-active .p-dropdown-panel {
    border: 1px solid #dee2e6 !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
}
body.zakupy-light-active .p-dropdown-panel .p-dropdown-item {
    color: #212529 !important;
    background: transparent !important;
}
body.zakupy-light-active .p-dropdown-panel .p-dropdown-item:hover {
    background: #eef5ff !important;
    color: #084298 !important;
}
body.zakupy-light-active .p-dropdown-panel .p-dropdown-item.p-highlight {
    background: #cfe2ff !important;
    color: #084298 !important;
}
/* Nagłówek grupy (np. "ĆWIERĆ FREZY") — jasnoszare tło, niebieski font */
body.zakupy-light-active .p-dropdown-item-group {
    background: #f1f3f5 !important;
    color: #0d6efd !important;
    font-weight: 700 !important;
    border-top: 1px solid #dee2e6 !important;
    border-bottom: 1px solid #dee2e6 !important;
}
body.zakupy-light-active .p-dropdown-header {
    background: #f8f9fa !important;
    border-bottom: 1px solid #dee2e6 !important;
}
body.zakupy-light-active .p-dropdown-header .p-dropdown-filter {
    background: #ffffff !important;
    border: 1px solid #ced4da !important;
    color: #212529 !important;
}

/* === SCROLLBARY (light) — bez czarnego obrysu z Chromium ===
   background-clip: padding-box + border transparent = thumb bez ramki
   border: 0 / box-shadow: none na thumb usuwa inset shadow przeglądarki
   scrollbar-corner: jednolite jasne tło zamiast domyślnego ciemnego */

/* Scrollbar w portalach (Dropdown panel, Menu popup, Dialog content) */
body.zakupy-light-active .p-dropdown-items-wrapper::-webkit-scrollbar,
body.zakupy-light-active .p-menu::-webkit-scrollbar,
body.zakupy-light-active .p-dialog-content::-webkit-scrollbar {
    width: 10px;
    height: 10px;
    background: #f1f3f5;
}
body.zakupy-light-active .p-dropdown-items-wrapper::-webkit-scrollbar-track,
body.zakupy-light-active .p-menu::-webkit-scrollbar-track,
body.zakupy-light-active .p-dialog-content::-webkit-scrollbar-track {
    background: #f1f3f5;
    border: 0;
    box-shadow: none;
}
body.zakupy-light-active .p-dropdown-items-wrapper::-webkit-scrollbar-thumb,
body.zakupy-light-active .p-menu::-webkit-scrollbar-thumb,
body.zakupy-light-active .p-dialog-content::-webkit-scrollbar-thumb {
    background-color: #ced4da;
    background-clip: padding-box;
    border: 2px solid transparent;
    border-radius: 7px;
    box-shadow: none;
    outline: none;
}
body.zakupy-light-active .p-dropdown-items-wrapper::-webkit-scrollbar-thumb:hover,
body.zakupy-light-active .p-menu::-webkit-scrollbar-thumb:hover,
body.zakupy-light-active .p-dialog-content::-webkit-scrollbar-thumb:hover {
    background-color: #adb5bd;
}
body.zakupy-light-active .p-dropdown-items-wrapper::-webkit-scrollbar-corner,
body.zakupy-light-active .p-menu::-webkit-scrollbar-corner,
body.zakupy-light-active .p-dialog-content::-webkit-scrollbar-corner {
    background: #f1f3f5;
}

/* Scrollbar wewnątrz .zakupy-app (DataTable, panele) */
.zakupy-app.light-theme ::-webkit-scrollbar {
    background: #f1f3f5;
}
.zakupy-app.light-theme ::-webkit-scrollbar-track {
    background: #f1f3f5;
    border: 0;
    box-shadow: none;
}
.zakupy-app.light-theme ::-webkit-scrollbar-thumb {
    background-color: #ced4da;
    background-clip: padding-box;
    border: 2px solid transparent;
    border-radius: 7px;
    box-shadow: none;
    outline: none;
}
.zakupy-app.light-theme ::-webkit-scrollbar-thumb:hover {
    background-color: #adb5bd;
}
.zakupy-app.light-theme ::-webkit-scrollbar-corner {
    background: #f1f3f5;
}

/* Dialog (modale Edytuj/Dodaj + about) */
body.zakupy-light-active .p-dialog-mask {
    background: rgba(0, 0, 0, 0.4);
}
body.zakupy-light-active .p-dialog {
    background: #ffffff !important;
    color: #212529 !important;
    border: 1px solid #dee2e6 !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15) !important;
}
body.zakupy-light-active .p-dialog .p-dialog-header {
    background: #f8f9fa !important;
    color: #212529 !important;
    border-bottom: 1px solid #dee2e6 !important;
}
body.zakupy-light-active .p-dialog .p-dialog-content {
    background: #ffffff !important;
    color: #212529 !important;
}
body.zakupy-light-active .p-dialog .p-dialog-footer {
    background: #ffffff !important;
    border-top: 1px solid #dee2e6 !important;
}
body.zakupy-light-active .p-dialog .p-dialog-header-icon {
    color: #495057 !important;
}
body.zakupy-light-active .p-dialog .p-dialog-header-icon:hover {
    background: #e9ecef !important;
}

/* === Wnętrze modalu Dialog — labels, inputs, dropdowns ===
   Dialog jest portalem (poza .zakupy-app), więc light variables tam nie sięgają.
   Reguły muszą startować od body.zakupy-light-active. */

/* Etykiety pól (.field label używa var(--dark-text-primary) → globalne ciemne tło + jasny font = nieczytelne na białym) */
body.zakupy-light-active .p-dialog .field label,
body.zakupy-light-active .p-dialog label,
body.zakupy-light-active .p-dialog .checkbox-label {
    color: #212529 !important;
    font-weight: 500 !important;
}

/* Pola tekstowe i numeryczne w modalu */
body.zakupy-light-active .p-dialog .p-inputtext,
body.zakupy-light-active .p-dialog .p-inputnumber-input,
body.zakupy-light-active .p-dialog .p-inputtextarea,
body.zakupy-light-active .p-dialog .form-control {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #ced4da !important;
    color: #212529 !important;
}
body.zakupy-light-active .p-dialog .p-inputtext:focus,
body.zakupy-light-active .p-dialog .p-inputnumber-input:focus,
body.zakupy-light-active .p-dialog .p-inputtextarea:focus,
body.zakupy-light-active .p-dialog .form-control:focus {
    border-color: #86b7fe !important;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.2) !important;
}
body.zakupy-light-active .p-dialog .p-inputtext::placeholder,
body.zakupy-light-active .p-dialog .form-control::placeholder {
    color: #6c757d !important;
}

/* Native button "Wybierz plik" w <input type="file"> — pseudo-element przeglądarki */
body.zakupy-light-active .p-dialog input[type="file"]::file-selector-button {
    background: #e9ecef !important;
    color: #0d6efd !important;
    border: 1px solid #ced4da !important;
    border-radius: 4px !important;
    padding: 4px 12px !important;
    margin-right: 10px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
}
body.zakupy-light-active .p-dialog input[type="file"]::file-selector-button:hover {
    background: #dee2e6 !important;
    color: #0a58ca !important;
}

/* Dropdown trigger wewnątrz modalu (np. wybór podkategorii) */
body.zakupy-light-active .p-dialog .p-dropdown {
    background: #ffffff !important;
    border: 1px solid #ced4da !important;
    color: #212529 !important;
}
body.zakupy-light-active .p-dialog .p-dropdown .p-dropdown-label {
    background: #ffffff !important;
    color: #212529 !important;
}
body.zakupy-light-active .p-dialog .p-dropdown .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
}
body.zakupy-light-active .p-dialog .p-dropdown .p-dropdown-trigger {
    color: #6c757d !important;
}
body.zakupy-light-active .p-dialog .p-dropdown.p-disabled,
body.zakupy-light-active .p-dialog .p-dropdown.p-disabled .p-dropdown-label {
    background: #e9ecef !important;
    color: #adb5bd !important;
}

/* Checkbox w modalu */
body.zakupy-light-active .p-dialog .p-checkbox .p-checkbox-box {
    background: #ffffff !important;
    border: 1px solid #ced4da !important;
}
body.zakupy-light-active .p-dialog .p-checkbox .p-checkbox-box.p-highlight {
    background: #0d6efd !important;
    border-color: #0d6efd !important;
}
body.zakupy-light-active .p-dialog .p-checkbox .p-checkbox-box .p-checkbox-icon {
    color: #ffffff !important;
}

/* About modal — pola w tabeli (label / value) */
body.zakupy-light-active .p-dialog .about-table td {
    color: #212529 !important;
}
body.zakupy-light-active .p-dialog .about-table .label {
    color: #6c757d !important;
}
body.zakupy-light-active .p-dialog .about-footer .copyright {
    color: #6c757d !important;
}

/* User menu popup */
body.zakupy-light-active .p-menu.p-menu-overlay {
    background: #ffffff !important;
    border: 1px solid #dee2e6 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}
body.zakupy-light-active .p-menu .p-menuitem-link {
    color: #212529 !important;
}
body.zakupy-light-active .p-menu .p-menuitem-link:hover {
    background: #f1f3f5 !important;
}
body.zakupy-light-active .p-menu .p-menuitem-link .p-menuitem-icon,
body.zakupy-light-active .p-menu .p-menuitem-link .p-menuitem-text {
    color: #212529 !important;
}
body.zakupy-light-active .p-menu .p-menu-separator {
    border-color: #dee2e6 !important;
}
</style>


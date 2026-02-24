<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">PRODUKCJA</h2>
            <div class="header-user-name">
                {{ auth.user.first_name }} {{ auth.user.last_name }}
            </div>
            <div class="header-buttons">
                <button
                    v-if="auth.isProdukcjaMagazyn"
                    class="btn-narzedzia"
                    @click="openNarzedziaModal"
                    title="Narzędzia"
                >
                    <i class="pi pi-wrench"></i>
                    Narzędzia
                </button>
                <button class="btn-exit" @click="logout">
                    <i class="pi pi-sign-out"></i>
                    Wyjście
                </button>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="magazyn-main">
            <!-- Górna tabela - Lista narzędzi -->
            <div class="tools-panel">
                <div class="panel-header">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="searchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">Lista typów narzędzi</h3>
                    <div class="filter-box">
                        <select
                            v-model="selectedKategoriaId"
                            @change="onKategoriaChange"
                            class="form-select filter-select"
                        >
                            <option :value="null">Wszystkie kategorie</option>
                            <option v-for="kat in kategorie" :key="kat.id" :value="kat.id">
                                {{ kat.nazwa }}
                            </option>
                        </select>
                        <select
                            v-model="selectedPodkategoriaId"
                            :disabled="!selectedKategoriaId"
                            class="form-select filter-select"
                        >
                            <option :value="null">Wszystkie podkategorie</option>
                            <option v-for="pod in filteredPodkategorie" :key="pod.id" :value="pod.id">
                                {{ pod.nazwa }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredTools"
                        :loading="isLoadingTools"
                        :scrollable="true"
                        scrollHeight="flex"
                        selectionMode="single"
                        v-model:selection="selectedToolForDetails"
                        dataKey="id"
                        class="tools-table"
                        :rowClass="rowClass"
                    >
                        <Column field="kategoria" header="Kategoria / Podkategoria">
                            <template #body="{ data }">
                                <span v-if="data.podkategoria">
                                    <strong>{{ data.podkategoria.kategoria_nazwa }}</strong> / {{ data.podkategoria.nazwa }}
                                </span>
                                <span v-else class="text-muted">Brak kategorii</span>
                            </template>
                        </Column>
                        <Column field="opis" header="Opis / Specyfikacja" />
                        <Column field="numer_katalogowy" header="Nr katalogowy">
                            <template #body="{ data }">
                                {{ data.numer_katalogowy || 'Brak' }}
                            </template>
                        </Column>
                        <Column field="ilosc_nowych" header="Nowe" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': data.ilosc_nowych === 0 }">{{ data.ilosc_nowych }}</span>
                            </template>
                        </Column>
                        <Column field="ilosc_uzywanych_dostepnych" header="Używane" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': data.ilosc_uzywanych_dostepnych === 0 }">{{ data.ilosc_uzywanych_dostepnych }}</span>
                            </template>
                        </Column>
                        <Column field="ilosc_w_uzyciu" header="W użyciu" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <button
                                    v-if="data.ilosc_w_uzyciu > 0"
                                    class="usage-btn"
                                    @click.stop="openUsageModal(data)"
                                >{{ data.ilosc_w_uzyciu }}</button>
                                <span v-else class="zero-value">0</span>
                            </template>
                        </Column>
                        <Column field="calkowita_ilosc" header="Razem" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <strong :class="{ 'zero-value': data.calkowita_ilosc === 0 }">{{ data.calkowita_ilosc }}</strong>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Dolna część - Zakładki -->
            <div class="details-panel">
                <TabView v-model:activeIndex="activeTabIndex">
                    <TabPanel>
                        <template #header>
                            <span>Moje narzędzia w użyciu</span>
                            <Badge :value="myUsagesInUse.length" style="background-color: #8B4513;" class="ml-2" />
                        </template>
                        <div class="tab-content-wrapper">
                            <div class="details-content">
                                <div class="instances-table">
                                    <DataTable :value="myUsagesInUse" :scrollable="true" scrollHeight="flex" class="instances-datatable">
                                        <Column header="Narzędzie">
                                            <template #body="{ data }">
                                                <span v-if="data.egzemplarz.narzedzie_typ.podkategoria">
                                                    <strong>{{ data.egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa }}</strong> /
                                                    {{ data.egzemplarz.narzedzie_typ.podkategoria.nazwa }} -
                                                </span>
                                                {{ data.egzemplarz.narzedzie_typ.opis }}
                                            </template>
                                        </Column>
                                        <Column header="Maszyna">
                                            <template #body="{ data }">
                                                {{ data.maszyna?.nazwa || 'Brak' }}
                                            </template>
                                        </Column>
                                        <Column header="Data pobrania">
                                            <template #body="{ data }">
                                                {{ formatCustomDate(data.data_wydania) }}
                                            </template>
                                        </Column>
                                        <template #empty>
                                            <div class="empty-state">Brak narzędzi w użyciu.</div>
                                        </template>
                                    </DataTable>
                                </div>
                                <div class="tool-image-panel">
                                    <img
                                        v-if="selectedToolForDetails && selectedToolForDetails.obraz"
                                        :src="selectedToolForDetails.obraz"
                                        class="tool-image"
                                        alt="Obrazek narzędzia"
                                    />
                                    <img
                                        v-else
                                        :src="defaultToolImage"
                                        class="tool-image"
                                        alt="Domyślny obrazek narzędzia"
                                    />
                                </div>
                            </div>
                        </div>
                    </TabPanel>
                </TabView>
            </div>
        </main>

        <!-- Modal: Narzędzia w użyciu -->
        <Dialog
            v-model:visible="showUsageModal"
            :header="selectedToolForUsage ? `Narzędzia w użyciu: ${selectedToolForUsage.opis}` : 'Narzędzia w użyciu'"
            :style="{ width: '70vw' }"
            :modal="true"
            class="usage-modal"
        >
            <DataTable :value="usagesForSelectedTool" :scrollable="true" scrollHeight="400px" class="usage-datatable">
                <Column header="Narzędzie">
                    <template #body="{ data }">
                        <span v-if="data.egzemplarz.narzedzie_typ.podkategoria">
                            <strong>{{ data.egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa }}</strong> /
                            {{ data.egzemplarz.narzedzie_typ.podkategoria.nazwa }} -
                        </span>
                        {{ data.egzemplarz.narzedzie_typ.opis }}
                    </template>
                </Column>
                <Column header="Maszyna">
                    <template #body="{ data }">
                        {{ data.maszyna?.nazwa || 'Brak' }}
                    </template>
                </Column>
                <Column header="Pracownik">
                    <template #body="{ data }">
                        {{ data.pracownik ? `${data.pracownik.nazwisko} ${data.pracownik.imie}` : 'Brak' }}
                    </template>
                </Column>
                <Column header="Data pobrania">
                    <template #body="{ data }">
                        {{ formatCustomDate(data.data_wydania) }}
                    </template>
                </Column>
                <template #empty>
                    <div class="empty-state">Brak narzędzi w użyciu.</div>
                </template>
            </DataTable>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import defaultToolImage from '@images/cnc.png';

// PrimeVue Components
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Badge from 'primevue/badge';
import Dialog from 'primevue/dialog';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { id: null, first_name: '', last_name: '', username: '' },
            isLogistyka: false,
            isProdukcjaMagazyn: false
        })
    },
    urls: {
        type: Object,
        default: () => ({
            logout: '/logout/'
        })
    },
    autoLogoutMinutes: {
        type: Number,
        default: 0
    }
});

// Data
const tools = ref([]);
const kategorie = ref([]);
const usagesInUse = ref([]);
const isLoadingTools = ref(true);

const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedToolForDetails = ref(null);
const searchQuery = ref('');
const activeTabIndex = ref(0);

// Modal "W użyciu"
const showUsageModal = ref(false);
const selectedToolForUsage = ref(null);

// Logout
const logout = () => {
    window.location.href = props.urls.logout;
};

// Auto-wylogowanie po bezczynności
let idleTimer = null;
const idleEvents = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'];

const resetIdleTimer = () => {
    if (!props.autoLogoutMinutes) return;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        logout();
    }, props.autoLogoutMinutes * 60 * 1000);
};

const startIdleWatch = () => {
    if (!props.autoLogoutMinutes) return;
    idleEvents.forEach(ev => window.addEventListener(ev, resetIdleTimer));
    resetIdleTimer();
};

const stopIdleWatch = () => {
    clearTimeout(idleTimer);
    idleEvents.forEach(ev => window.removeEventListener(ev, resetIdleTimer));
};

// Narzędzia (dla grupy produkcja-magazyn) - przekierowanie do magazynu w trybie ograniczonym
const openNarzedziaModal = () => {
    window.location.href = '/magazyn/?tryb=produkcja';
};

// Computed
const filteredTools = computed(() => {
    let filtered = tools.value;

    if (selectedPodkategoriaId.value) {
        filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.id === selectedPodkategoriaId.value);
    } else if (selectedKategoriaId.value) {
        const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
        if (kategoria) {
            filtered = filtered.filter(tool => {
                if (!tool.podkategoria) return false;
                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
            });
        }
    }

    if (searchQuery.value.trim() !== '') {
        const query = searchQuery.value.trim().toLowerCase();
        filtered = filtered.filter(tool => {
            const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
            const kategoriaNazwa = tool.podkategoria?.kategoria_nazwa?.toLowerCase() || '';
            const podkategoriaNazwa = tool.podkategoria?.nazwa?.toLowerCase() || '';
            const opisNazwa = tool.opis.toLowerCase();

            return kategoriaNazwa.includes(query) ||
                   podkategoriaNazwa.includes(query) ||
                   opisNazwa.includes(query) ||
                   catalogNumber.includes(query);
        });
    }

    return filtered;
});

// Filtrowane podkategorie dla native select
const filteredPodkategorie = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return kategoria.podkategorie || [];
});

// Narzędzia w użyciu tylko przez zalogowanego użytkownika
const myUsagesInUse = computed(() => {
    const firstName = props.auth.user.first_name?.toLowerCase() || '';
    const lastName = props.auth.user.last_name?.toLowerCase() || '';
    if (!firstName && !lastName) return [];
    return usagesInUse.value.filter(usage => {
        const pracownikImie = (usage.pracownik?.imie || '').toLowerCase();
        const pracownikNazwisko = (usage.pracownik?.nazwisko || '').toLowerCase();
        return pracownikImie === firstName && pracownikNazwisko === lastName;
    });
});

// Narzędzia w użyciu dla wybranego typu narzędzia (modal)
const usagesForSelectedTool = computed(() => {
    if (!selectedToolForUsage.value) return [];
    return usagesInUse.value.filter(usage =>
        usage.egzemplarz?.narzedzie_typ?.id === selectedToolForUsage.value.id
    );
});

// Methods
const rowClass = (data) => {
    return selectedToolForDetails.value && selectedToolForDetails.value.id === data.id ? 'selected-row' : '';
};

const formatCustomDate = (dateString) => {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Nieprawidłowa data';
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} [${hours}:${minutes}]`;
    } catch (e) {
        console.error("Błąd formatowania daty:", dateString, e);
        return 'Błąd daty';
    }
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const openUsageModal = (tool) => {
    if (tool.ilosc_w_uzyciu > 0) {
        selectedToolForUsage.value = tool;
        showUsageModal.value = true;
    }
};

const fetchInitialData = async () => {
    try {
        const [toolsRes, categoriesRes, usagesRes] = await Promise.all([
            axios.get(`${API_URL}/narzedzia/`),
            axios.get(`${API_URL}/kategorie/`),
            axios.get(`${API_URL}/historia/?w_uzyciu=true`)
        ]);

        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;
        usagesInUse.value = usagesRes.data.results || usagesRes.data;
    } catch (error) {
        console.error("Błąd ładowania danych:", error.response?.data || error.message);
    } finally {
        isLoadingTools.value = false;
    }
};

onMounted(() => {
    fetchInitialData();
    startIdleWatch();
});

onUnmounted(() => {
    stopIdleWatch();
});
</script>

<style scoped>
/* === CIEMNY MOTYW - ZMIENNE BOOTSTRAP 5 DARK === */
:root {
    --dark-bg-primary: #212529;
    --dark-bg-secondary: #2b3035;
    --dark-bg-tertiary: #343a40;
    --dark-bg-card: #2d3238;
    --dark-bg-hover: #3d444d;
    --dark-border: #495057;
    --dark-text-primary: #dee2e6;
    --dark-text-secondary: #adb5bd;
    --dark-text-muted: #6c757d;
    --dark-accent: #0d6efd;
}

/* === LAYOUT GŁÓWNY === */
.magazyn-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
    overflow: hidden;
}

/* === NAGŁÓWEK === */
.magazyn-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: linear-gradient(to bottom, #343a40, #212529);
    color: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    flex-shrink: 0;
    z-index: 10;
}

.header-title {
    margin: 0;
    color: #ffc107;
    font-weight: bold;
    font-size: 1.5rem;
}

.header-buttons {
    display: flex;
    gap: 5px;
    align-items: center;
}

.header-user-name {
    flex: 1;
    text-align: center;
    color: #e9ecef;
    font-size: 1rem;
    font-weight: 500;
}

.btn-narzedzia {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #17a2b8;
    background-color: #17a2b8;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}

.btn-narzedzia:hover {
    background-color: #138496;
    border-color: #117a8b;
}

.btn-exit {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid transparent;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
    background-color: #dc3545;
    border-color: #dc3545;
    color: #fff;
}

.btn-exit:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

/* === GŁÓWNA ZAWARTOŚĆ === */
.magazyn-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 24px 10px 24px;
    gap: 16px;
    min-height: 0;
    overflow: hidden;
}

/* === PANEL NARZĘDZI (GÓRNY) === */
.tools-panel {
    flex: 0 0 45%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    border: none;
    min-height: 0;
    overflow: hidden;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 6px 6px 0 0;
    flex-shrink: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.panel-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffc107;
}

.search-box {
    display: flex;
    align-items: center;
}

/* Bootstrap-like form controls - ciemny motyw */
.form-control {
    display: block;
    padding: 6px 12px;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-tertiary);
    background-clip: padding-box;
    border: 1px solid var(--dark-border);
    border-radius: 4px;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.form-control:focus {
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-secondary);
    border-color: var(--dark-accent);
    outline: 0;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}

.form-control::placeholder {
    color: var(--dark-text-muted);
}

.form-select {
    display: block;
    padding: 6px 32px 6px 12px;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-tertiary);
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23adb5bd' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 8px center;
    background-size: 16px 12px;
    border: 1px solid var(--dark-border);
    border-radius: 4px;
    appearance: none;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.form-select:focus {
    border-color: var(--dark-accent);
    outline: 0;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}

.form-select:disabled {
    background-color: var(--dark-bg-primary);
    opacity: 0.65;
    cursor: not-allowed;
}

/* Wyróżnienie pól wyszukiwania */
.search-input {
    width: 180px;
    background-color: #495057 !important;
    border: 2px solid #6c757d !important;
    color: #fff !important;
}

.search-input:focus {
    background-color: #4a5258 !important;
    border-color: #ffc107 !important;
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3) !important;
}

.search-input::placeholder {
    color: #adb5bd;
}

.filter-box {
    display: flex;
    gap: 8px;
}

/* Wyróżnienie dropdownów filtrów */
.filter-select {
    min-width: 180px;
    background-color: #495057 !important;
    border: 2px solid #6c757d !important;
    color: #fff !important;
}

.filter-select:focus {
    background-color: #4a5258 !important;
    border-color: #ffc107 !important;
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3) !important;
}

.filter-select:not(:disabled):hover {
    border-color: #adb5bd;
}

/* Stylowanie opcji w native select */
.filter-select option,
.form-select option {
    background-color: #343a40;
    color: #dee2e6;
    padding: 8px 12px;
}

.filter-select option:checked,
.form-select option:checked {
    background-color: #4a3728;
    color: #fff;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
}

/* === TABELE PRIMEVUE === */
:deep(.p-datatable) {
    font-size: 0.9rem;
    background: transparent;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
    background: linear-gradient(to bottom, #4a5258, #3d444d) !important;
    color: #fff !important;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: none;
    letter-spacing: 0;
    border-bottom: none !important;
    white-space: nowrap;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

:deep(.p-datatable .p-datatable-tbody > tr) {
    background-color: var(--dark-bg-card) !important;
    color: var(--dark-text-primary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:nth-child(even)) {
    background-color: var(--dark-bg-secondary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
    padding: 8px 12px;
    border-bottom: 1px solid var(--dark-border) !important;
    vertical-align: middle;
    color: var(--dark-text-primary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
    background-color: var(--dark-bg-hover) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr.p-highlight),
:deep(.p-datatable .p-datatable-tbody > tr.p-highlight > td) {
    background-color: #4a3728 !important;
    color: #fff !important;
}

:deep(.selected-row),
:deep(.selected-row td) {
    background-color: #4a3728 !important;
    color: #fff !important;
}

/* Sticky header dla tabel */
:deep(.p-datatable-scrollable .p-datatable-thead) {
    position: sticky;
    top: 0;
    z-index: 1;
}

/* === PANEL SZCZEGÓŁÓW (DOLNY) === */
.details-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 6px;
    border: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

/* === ZAKŁADKI (TABS) === */
:deep(.p-tabview) {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: transparent;
    border-radius: 0;
}

:deep(.p-tabview-nav-container) {
    flex-shrink: 0;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

:deep(.p-tabview-nav) {
    background: transparent;
    border: none;
    padding: 0 8px;
}

:deep(.p-tabview-nav li) {
    margin-right: 4px;
}

:deep(.p-tabview-nav li .p-tabview-nav-link) {
    border: none;
    border-bottom: 3px solid transparent;
    background: transparent;
    color: #adb5bd;
    padding: 12px 16px;
    font-weight: 500;
    border-radius: 0;
    margin-bottom: 0;
    transition: all 0.2s ease;
}

:deep(.p-tabview-nav li .p-tabview-nav-link:hover) {
    background: rgba(255, 255, 255, 0.1);
    border-color: transparent;
    color: #fff;
}

:deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
    border-bottom-color: #ffc107;
    color: #ffc107;
    background: rgba(255, 193, 7, 0.1);
}

:deep(.p-tabview-panels) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    padding: 0;
    background: #212529;
}

:deep(.p-tabview-panel) {
    height: 100%;
    padding: 0;
}

/* Badge w nagłówku zakładki */
:deep(.p-tabview-nav-link .p-badge) {
    margin-left: 8px;
    font-size: 0.75rem;
    vertical-align: middle;
}

.tab-content-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* === SZCZEGÓŁY NARZĘDZIA === */
.details-content {
    display: flex;
    height: 100%;
    overflow: hidden;
}

.instances-table {
    flex: 1;
    overflow: auto;
    min-width: 0;
}

.instances-datatable {
    height: 100%;
}

.tool-image-panel {
    width: 30%;
    min-width: 200px;
    max-width: 400px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-left: 1px solid #495057;
    background: linear-gradient(to right, #2d3238, #343a40);
    padding: 16px;
    flex-shrink: 0;
    overflow: hidden;
}

.tool-image {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
}

/* === STANY === */
.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    color: #6c757d;
    text-align: center;
    flex: 1;
}

/* === UTILITY === */
.text-muted {
    color: #6c757d;
}

.ml-2 {
    margin-left: 8px;
}

/* === WARTOŚĆ ZEROWA W TABELI === */
.zero-value {
    color: #6c757d !important;
}

/* === MINIATUROWY BUTTON W KOLUMNIE "W UŻYCIU" === */
.usage-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    height: 24px;
    padding: 2px 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #dee2e6;
    background-color: #495057;
    border: 1px solid #6c757d;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.usage-btn:hover {
    background-color: #5a6268;
    border-color: #adb5bd;
    color: #fff;
}

/* === MODAL NARZĘDZIA W UŻYCIU === */
:deep(.usage-modal .p-dialog-header) {
    background: linear-gradient(to bottom, #3d444d, #343a40);
    color: #ffc107;
    border-bottom: 1px solid #495057;
}

:deep(.usage-modal .p-dialog-content) {
    background-color: #212529;
    padding: 16px;
}

:deep(.usage-modal .p-dialog-footer) {
    background-color: #2d3238;
    border-top: 1px solid #495057;
}

/* === SCROLLBAR - CIEMNY MOTYW === */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--dark-bg-primary);
}

::-webkit-scrollbar-thumb {
    background: var(--dark-border);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: #4d555d;
}

</style>

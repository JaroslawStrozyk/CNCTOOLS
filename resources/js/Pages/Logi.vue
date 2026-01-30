<template>
    <div class="logi-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">LOGI SYSTEMOWE</h2>
            <div class="header-buttons">
                <a :href="urls.magazyn" class="btn btn-danger">
                    <i class="pi pi-arrow-left"></i> Wróć
                </a>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="app-main">
            <TabView>
                <!-- Logi bieżące (dzisiaj) -->
                <TabPanel header="Logi bieżące">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Logi z dzisiaj</h3>
                            <div class="header-actions">
                                <span class="auto-refresh-status" :class="{ active: autoRefreshEnabled }">
                                    <i class="pi pi-sync" :class="{ 'pi-spin': autoRefreshEnabled }"></i>
                                    Auto-odświeżanie: {{ autoRefreshEnabled ? 'ON' : 'OFF' }}
                                </span>
                                <button
                                    class="btn"
                                    :class="autoRefreshEnabled ? 'btn-warning' : 'btn-success'"
                                    @click="autoRefreshEnabled = !autoRefreshEnabled"
                                >
                                    <i :class="autoRefreshEnabled ? 'pi pi-pause' : 'pi pi-play'"></i>
                                    {{ autoRefreshEnabled ? 'Zatrzymaj' : 'Wznów' }}
                                </button>
                            </div>
                        </div>
                        <div class="panel-body">
                            <div v-if="logiLoading" class="loading-state">
                                <ProgressSpinner />
                                <p>Ładowanie logów...</p>
                            </div>
                            <div v-else-if="logiBiezace.length === 0" class="empty-state">
                                <i class="pi pi-inbox"></i>
                                <p>Brak logów z dzisiaj</p>
                            </div>
                            <DataTable
                                v-else
                                :value="logiBiezace"
                                :scrollable="true"
                                scrollHeight="flex"
                                :paginator="true"
                                :rows="50"
                                :rowsPerPageOptions="[25, 50, 100]"
                                class="logi-table"
                            >
                                <Column field="data" header="Data" style="width: 120px;">
                                    <template #body="{ data }">
                                        <span class="log-date">{{ formatDate(data.timestamp) }}</span>
                                    </template>
                                </Column>
                                <Column field="godzina" header="Godzina" style="width: 100px;">
                                    <template #body="{ data }">
                                        <span class="log-time">{{ formatTime(data.timestamp) }}</span>
                                    </template>
                                </Column>
                                <Column field="status" header="Status" style="width: 110px;">
                                    <template #body="{ data }">
                                        <Tag :severity="getStatusSeverity(data.status)" :value="data.status" />
                                    </template>
                                </Column>
                                <Column field="osoba" header="Osoba zalogowana" style="width: 180px;">
                                    <template #body="{ data }">
                                        <span class="log-user">{{ data.osoba || '-' }}</span>
                                    </template>
                                </Column>
                                <Column field="operacja" header="Operacja">
                                    <template #body="{ data }">
                                        <span class="log-operation">{{ data.operacja }}</span>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>
                </TabPanel>

                <!-- Archiwum logów (pliki) -->
                <TabPanel header="Archiwum">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Archiwum logów</h3>
                        </div>
                        <div class="panel-body archiwum-layout">
                            <!-- Lista plików -->
                            <div class="archiwum-files">
                                <div class="section-header">
                                    <h5>Pliki logów</h5>
                                </div>
                                <div v-if="archiwumLoading" class="loading-state small">
                                    <ProgressSpinner />
                                </div>
                                <div v-else-if="plikiLogow.length === 0" class="empty-state small">
                                    <p>Brak plików archiwalnych</p>
                                </div>
                                <Listbox
                                    v-else
                                    v-model="selectedPlik"
                                    :options="plikiLogow"
                                    optionLabel="nazwa"
                                    class="files-list"
                                    @change="onPlikSelect"
                                >
                                    <template #option="{ option }">
                                        <div class="file-item">
                                            <i class="pi pi-file"></i>
                                            <div class="file-info">
                                                <span class="file-name">{{ option.nazwa }}</span>
                                                <span class="file-size">{{ formatFileSize(option.rozmiar) }}</span>
                                            </div>
                                        </div>
                                    </template>
                                </Listbox>
                            </div>

                            <!-- Podgląd zawartości pliku (identyczna tabela jak bieżące) -->
                            <div class="archiwum-content">
                                <div class="section-header">
                                    <h5>{{ selectedPlik ? `Zawartość: ${selectedPlik.nazwa}` : 'Wybierz plik z listy' }}</h5>
                                </div>
                                <div v-if="!selectedPlik" class="empty-state">
                                    <i class="pi pi-file"></i>
                                    <p>Wybierz plik z listy, aby zobaczyć jego zawartość</p>
                                </div>
                                <div v-else-if="plikLoading" class="loading-state">
                                    <ProgressSpinner />
                                    <p>Ładowanie zawartości...</p>
                                </div>
                                <div v-else-if="logiArchiwum.length === 0" class="empty-state">
                                    <i class="pi pi-inbox"></i>
                                    <p>Plik jest pusty</p>
                                </div>
                                <DataTable
                                    v-else
                                    :value="logiArchiwum"
                                    :scrollable="true"
                                    scrollHeight="flex"
                                    :paginator="true"
                                    :rows="50"
                                    :rowsPerPageOptions="[25, 50, 100]"
                                    class="logi-table"
                                >
                                    <Column field="data" header="Data" style="width: 120px;">
                                        <template #body="{ data }">
                                            <span class="log-date">{{ formatDate(data.timestamp) }}</span>
                                        </template>
                                    </Column>
                                    <Column field="godzina" header="Godzina" style="width: 100px;">
                                        <template #body="{ data }">
                                            <span class="log-time">{{ formatTime(data.timestamp) }}</span>
                                        </template>
                                    </Column>
                                    <Column field="status" header="Status" style="width: 110px;">
                                        <template #body="{ data }">
                                            <Tag :severity="getStatusSeverity(data.status)" :value="data.status" />
                                        </template>
                                    </Column>
                                    <Column field="osoba" header="Osoba zalogowana" style="width: 180px;">
                                        <template #body="{ data }">
                                            <span class="log-user">{{ data.osoba || '-' }}</span>
                                        </template>
                                    </Column>
                                    <Column field="operacja" header="Operacja">
                                        <template #body="{ data }">
                                            <span class="log-operation">{{ data.operacja }}</span>
                                        </template>
                                    </Column>
                                </DataTable>
                            </div>
                        </div>
                    </div>
                </TabPanel>
            </TabView>
        </main>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';

import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Tag from 'primevue/tag';
import Listbox from 'primevue/listbox';
import ProgressSpinner from 'primevue/progressspinner';

const API_URL = '/api';

// Interwał automatycznego odświeżania (5 sekund)
const REFRESH_INTERVAL = 5000;
let refreshTimer = null;

const props = defineProps({
    urls: {
        type: Object,
        default: () => ({
            magazyn: '/magazyn/'
        })
    }
});

// Logi bieżące
const logiBiezace = ref([]);
const logiLoading = ref(false);
const autoRefreshEnabled = ref(true);

// Archiwum
const plikiLogow = ref([]);
const selectedPlik = ref(null);
const logiArchiwum = ref([]);
const archiwumLoading = ref(false);
const plikLoading = ref(false);

// Methods - formatowanie daty i czasu
const formatDate = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
};

const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('pl-PL', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
};

const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
};

const getStatusSeverity = (status) => {
    const severities = {
        'DEBUG': 'secondary',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'danger',
        'CRITICAL': 'danger',
        'OK': 'success',
        'SUCCESS': 'success'
    };
    return severities[status?.toUpperCase()] || 'secondary';
};

// Automatyczne odświeżanie
const startAutoRefresh = () => {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => {
        if (autoRefreshEnabled.value) {
            refreshLogiSilent();
        }
    }, REFRESH_INTERVAL);
};

const stopAutoRefresh = () => {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
};

// Ciche odświeżanie (bez loadera)
const refreshLogiSilent = async () => {
    try {
        const response = await axios.get(`${API_URL}/logi/biezace/`);
        logiBiezace.value = response.data || [];
    } catch (error) {
        console.error('Błąd odświeżania logów:', error);
    }
};

const refreshLogi = async () => {
    logiLoading.value = true;
    try {
        const response = await axios.get(`${API_URL}/logi/biezace/`);
        logiBiezace.value = response.data || [];
    } catch (error) {
        console.error('Błąd ładowania logów:', error);
        logiBiezace.value = [];
    } finally {
        logiLoading.value = false;
    }
};

const refreshArchiwum = async () => {
    archiwumLoading.value = true;
    try {
        const response = await axios.get(`${API_URL}/logi/pliki/`);
        plikiLogow.value = response.data || [];
    } catch (error) {
        console.error('Błąd ładowania listy plików:', error);
        plikiLogow.value = [];
    } finally {
        archiwumLoading.value = false;
    }
};

const onPlikSelect = async (event) => {
    if (!event.value) {
        logiArchiwum.value = [];
        return;
    }

    plikLoading.value = true;
    try {
        const response = await axios.get(`${API_URL}/logi/pliki/${event.value.nazwa}/`);
        logiArchiwum.value = response.data || [];
    } catch (error) {
        console.error('Błąd ładowania zawartości pliku:', error);
        logiArchiwum.value = [];
    } finally {
        plikLoading.value = false;
    }
};

onMounted(async () => {
    await Promise.all([
        refreshLogi(),
        refreshArchiwum()
    ]);
    // Uruchom automatyczne odświeżanie
    startAutoRefresh();
});

onUnmounted(() => {
    // Zatrzymaj automatyczne odświeżanie przy opuszczeniu strony
    stopAutoRefresh();
});
</script>

<style scoped>
/* === ZMIENNE === */
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
}

/* === LAYOUT === */
.logi-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
    overflow: hidden;
}

.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: linear-gradient(to bottom, #343a40, #212529);
    color: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    flex-shrink: 0;
}

.header-title {
    margin: 0;
    color: #ffc107;
    font-weight: bold;
    font-size: 1.5rem;
}

.header-buttons {
    display: flex;
    gap: 8px;
}

.app-main {
    flex: 1;
    padding: 24px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

/* === TABS === */
:deep(.p-tabview) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

:deep(.p-tabview-panels) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

:deep(.p-tabview-panel) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

/* === PANEL === */
.settings-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 8px 8px 0 0;
    flex-shrink: 0;
}

.panel-header h3 {
    margin: 0;
    color: #ffc107;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
    padding: 16px;
}

.header-actions {
    display: flex;
    gap: 8px;
}

/* === BUTTONS === */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    text-decoration: none;
}

.btn-danger {
    background-color: #dc3545;
    border-color: #dc3545;
    color: #fff;
}
.btn-danger:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

.btn-secondary {
    background-color: #6c757d;
    border-color: #6c757d;
    color: #fff;
}
.btn-secondary:hover {
    background-color: #5c636a;
    border-color: #565e64;
}

.btn-success {
    background-color: #198754;
    border-color: #198754;
    color: #fff;
}
.btn-success:hover {
    background-color: #157347;
    border-color: #146c43;
}

.btn-warning {
    background-color: #ffc107;
    border-color: #ffc107;
    color: #212529;
}
.btn-warning:hover {
    background-color: #ffca2c;
    border-color: #ffc720;
}

/* === AUTO REFRESH STATUS === */
.auto-refresh-status {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background-color: rgba(108, 117, 125, 0.3);
    border-radius: 4px;
    font-size: 13px;
    color: #adb5bd;
}

.auto-refresh-status.active {
    background-color: rgba(25, 135, 84, 0.2);
    color: #28a745;
}

.auto-refresh-status i {
    font-size: 14px;
}

/* === LOGI TABLE === */
.logi-table {
    font-size: 0.85rem;
}

.log-date {
    font-family: monospace;
    color: #adb5bd;
    font-weight: 500;
}

.log-time {
    font-family: monospace;
    color: #ffc107;
    font-weight: 500;
}

.log-user {
    color: #17a2b8;
    font-weight: 500;
}

.log-operation {
    color: #dee2e6;
}

/* === ARCHIWUM LAYOUT === */
.archiwum-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 20px;
    height: 100%;
}

.archiwum-files {
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.archiwum-content {
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

.section-header {
    margin-bottom: 12px;
}

.section-header h5 {
    margin: 0;
    color: #adb5bd;
    font-size: 0.9rem;
    font-weight: 600;
}

/* === FILES LIST === */
.files-list {
    flex: 1;
    overflow: auto;
}

:deep(.files-list .p-listbox) {
    background: var(--dark-bg-secondary);
    border-color: var(--dark-border);
}

:deep(.files-list .p-listbox-item) {
    padding: 10px 12px;
}

.file-item {
    display: flex;
    align-items: center;
    gap: 10px;
}

.file-item i {
    color: #ffc107;
    font-size: 1.2rem;
}

.file-info {
    display: flex;
    flex-direction: column;
}

.file-name {
    color: #dee2e6;
    font-weight: 500;
}

.file-size {
    color: #6c757d;
    font-size: 0.8rem;
}

/* === STATES === */
.loading-state, .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #6c757d;
    text-align: center;
}

.loading-state.small, .empty-state.small {
    padding: 20px;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state p {
    margin: 0;
    font-size: 14px;
}

/* === DATATABLE DARK THEME === */
:deep(.p-datatable) {
    background: transparent;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
    background: linear-gradient(to bottom, #4a5258, #3d444d) !important;
    color: #fff !important;
    border-bottom: none !important;
}

:deep(.p-datatable .p-datatable-tbody > tr) {
    background-color: var(--dark-bg-card) !important;
    color: var(--dark-text-primary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:nth-child(even)) {
    background-color: var(--dark-bg-secondary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
    border-bottom: 1px solid var(--dark-border) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
    background-color: var(--dark-bg-hover) !important;
}

/* === PAGINATOR DARK === */
:deep(.p-paginator) {
    background: var(--dark-bg-tertiary) !important;
    border: none !important;
}

:deep(.p-paginator .p-paginator-pages .p-paginator-page) {
    color: var(--dark-text-primary) !important;
}

:deep(.p-paginator .p-paginator-pages .p-paginator-page.p-highlight) {
    background: #6f42c1 !important;
    color: #fff !important;
}
</style>

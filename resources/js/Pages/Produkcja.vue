<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">PRODUKCJA</h2>
            <div class="header-user-name">
                {{ auth.user.first_name }} {{ auth.user.last_name }}
            </div>
            <div class="header-buttons">
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
                        :scrollable="true"
                        scrollHeight="flex"
                        selectionMode="single"
                        v-model:selection="selectedToolForDetails"
                        @row-select="onToolSelect"
                        @row-unselect="onToolUnselect"
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
                                <span :class="{ 'zero-value': data.ilosc_w_uzyciu === 0 }">{{ data.ilosc_w_uzyciu }}</span>
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

        <!-- Modal: Wydaj narzędzie -->
        <Dialog v-model:visible="issueModalVisible" header="Pobierz egzemplarz" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Narzędzie</label>
                    <InputText :value="issueData.instance ? issueData.instance.narzedzie_typ.opis : ''" disabled />
                </div>
                <div class="field">
                    <label for="machine">Wybierz maszynę</label>
                    <Dropdown
                        id="machine"
                        v-model="issueData.machine_id"
                        :options="machines"
                        optionLabel="nazwa"
                        optionValue="id"
                        placeholder="Wybierz maszynę"
                    />
                </div>
                <div class="field">
                    <label for="employee">Wybierz pracownika</label>
                    <Dropdown
                        id="employee"
                        v-model="issueData.pracownik_id"
                        :options="pracownicy"
                        optionLabel="fullName"
                        optionValue="id"
                        placeholder="-- Wybierz --"
                        :filter="true"
                    />
                </div>
                <Message v-if="issueError" severity="error" :closable="false">{{ issueError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="issueModalVisible = false" />
                <Button label="Pobierz" icon="pi pi-check" @click="issueTool" />
            </template>
        </Dialog>

        <!-- Modal: Zwróć narzędzie -->
        <Dialog v-model:visible="returnModalVisible" header="Zwrot narzędzia" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Pracownik zwracający</label>
                    <Dropdown
                        v-model="returnPracownikId"
                        :options="pracownicy"
                        optionLabel="fullName"
                        optionValue="id"
                        placeholder="Wybierz pracownika"
                        :filter="true"
                    />
                </div>
                <div class="field">
                    <label>W jakim stanie technicznym zwracasz narzędzie?</label>
                    <div class="return-status-options">
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUzywane" value="uzywane" />
                            <label for="stanUzywane">Dobrym (jako używane)</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzone" value="uszkodzone" />
                            <label for="stanUszkodzone">Uszkodzonym</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzoneRegen" value="uszkodzone_regeneracja" />
                            <label for="stanUszkodzoneRegen">Uszkodzonym do regeneracji</label>
                        </div>
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="returnModalVisible = false" />
                <Button label="Potwierdź zwrot" icon="pi pi-check" class="p-button-success" @click="confirmReturnTool" />
            </template>
        </Dialog>

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
                    <label>Domyślna lokalizacja (opcjonalnie)</label>
                    <Dropdown
                        v-model="currentTool.domyslna_lokalizacja_id"
                        :options="locationOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Brak --"
                    />
                </div>
                <div class="field">
                    <label>Opakowanie</label>
                    <Dropdown
                        v-model="currentTool.opakowanie"
                        :options="opakowanieOptions"
                        optionLabel="label"
                        optionValue="value"
                        @change="onOpakowanieChange"
                    />
                </div>
                <div class="field">
                    <label>Ilość w opakowaniu</label>
                    <InputNumber v-model="currentTool.ilosc_w_opakowaniu" :min="currentTool.opakowanie === 'kompl' ? 2 : 1" />
                </div>
                <Message v-if="toolValidationError" severity="error" :closable="false">{{ toolValidationError }}</Message>
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
                <Button :label="isEditMode ? 'Zapisz' : 'Dodaj'" icon="pi pi-check" @click="saveTool" />
            </template>
        </Dialog>

        <!-- Modal: Edytuj/Dodaj egzemplarz -->
        <Dialog v-model:visible="instanceModalVisible" :header="instanceModal.title" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <Message v-if="instanceModal.errorMessage" severity="error" :closable="false">{{ instanceModal.errorMessage }}</Message>
                <div class="field">
                    <label>Typ Narzędzia</label>
                    <InputText :value="selectedToolForDetails ? selectedToolForDetails.opis : ''" disabled />
                </div>
                <div class="field">
                    <label>Stan Techniczny</label>
                    <Dropdown
                        v-model="instanceModal.currentInstance.stan"
                        :options="stanOptions"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>
                <div class="field">
                    <label>Lokalizacja</label>
                    <Dropdown
                        v-model="instanceModal.currentInstance.lokalizacja_id"
                        :options="locationOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Wybierz lokalizację --"
                    />
                </div>
                <template v-if="instanceModal.mode === 'add'">
                    <div class="field">
                        <label>Zamówienie (opcjonalne)</label>
                        <Dropdown
                            v-model="instanceModal.currentInstance.zamowienie_id"
                            :options="zamowieniaOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="-- Brak --"
                        />
                    </div>
                    <div class="field">
                        <label>Ilość</label>
                        <InputNumber v-model="instanceModal.currentInstance.ilosc" :min="1" />
                    </div>
                </template>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="instanceModalVisible = false" :disabled="isSavingInstance" />
                <Button v-if="!isSavingInstance" label="Zapisz" icon="pi pi-check" @click="saveInstance" />
                <Button v-else label="Zapisywanie..." icon="pi pi-spin pi-spinner" disabled />
            </template>
        </Dialog>

        <!-- Modal: Potwierdź usunięcie -->
        <Dialog v-model:visible="deleteInstanceModalVisible" header="Potwierdź usunięcie" :modal="true" :style="{ width: '450px' }">
            <div v-html="deleteModalMessage"></div>
            <p class="text-danger mt-3">Tej operacji nie można cofnąć.</p>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteInstanceModalVisible = false" />
                <Button label="Tak, usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteInstance" />
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
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';
import defaultToolImage from '@images/cnc.png';

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
import Message from 'primevue/message';
import RadioButton from 'primevue/radiobutton';
import ProgressSpinner from 'primevue/progressspinner';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { id: null, first_name: '', last_name: '', username: '' },
            isLogistyka: false
        })
    },
    urls: {
        type: Object,
        default: () => ({
            ustawienia: '/ustawienia/',
            zwroty: '/zwroty/',
            zamowienia: '/zamowienia/',
            zakupy: '/zakupy/',
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
const podkategorie = ref([]);
const machines = ref([]);
const pracownicy = ref([]);
const faktury = ref([]);
const zamowienia = ref([]);
const usagesInUse = ref([]);
const toolInstances = ref([]);
const toolHistory = ref([]);
const locations = ref([]);

const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedToolForDetails = ref(null);
const searchQuery = ref('');

const activeTabIndex = ref(0);
const isLoadingDetails = ref(false);
const isLoadingHistory = ref(false);
const isEditMode = ref(false);
const isSavingInstance = ref(false);

const issueError = ref('');
const toolValidationError = ref('');

// Modals visibility
const issueModalVisible = ref(false);
const returnModalVisible = ref(false);
const toolModalVisible = ref(false);
const instanceModalVisible = ref(false);
const deleteInstanceModalVisible = ref(false);
const aboutModalVisible = ref(false);

// Modal data
const issueData = ref({
    machine_id: null,
    instance: null,
    pracownik_id: null
});

const currentTool = ref({});
const returnStatus = ref('uzywane');
const returnPracownikId = ref(null);
const usageToReturnId = ref(null);

const instanceModal = ref({
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
    errorMessage: ''
});

const instanceToDelete = ref(null);
const deleteModalMessage = ref('');

const toolImagePreview = ref(null);
const toolImageFile = ref(null);

// Logout
const logout = () => {
    window.location.href = props.urls.logout;
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

const inUseInstanceIds = computed(() => {
    return new Set(usagesInUse.value.map(usage => usage.egzemplarz.id));
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

// Filtrowane podkategorie dla native select (używane w panel-header)
const filteredPodkategorie = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return kategoria.podkategorie || [];
});

const kategorieOptions = computed(() => {
    return [
        { label: 'Wszystkie kategorie', value: null },
        ...kategorie.value.map(k => ({ label: k.nazwa, value: k.id }))
    ];
});

const sortedLocations = computed(() => {
    return [...locations.value].sort((a, b) => {
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
});

const locationOptions = computed(() => {
    return [
        { label: '-- Brak --', value: null },
        ...sortedLocations.value.map(loc => ({
            label: `${loc.szafa} / ${loc.kolumna} / ${loc.polka}`,
            value: loc.id
        }))
    ];
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

const machineOptions = computed(() => {
    return [
        { label: 'Wszystkie maszyny', value: null },
        ...machines.value.map(m => ({ label: m.nazwa, value: m.id }))
    ];
});

const zamowieniaOptions = computed(() => {
    return [
        { label: '-- Brak --', value: null },
        ...zamowienia.value.map(z => ({
            label: `${z.numer} - ${z.dostawca?.nazwa_firmy || 'Brak dostawcy'}`,
            value: z.id
        }))
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

// Static options
const opakowanieOptions = [
    { label: 'Sztuka', value: 'szt' },
    { label: 'Komplet', value: 'kompl' }
];

const stanOptions = [
    { label: 'Nowe', value: 'nowe' },
    { label: 'Używane', value: 'uzywane' },
    { label: 'Uszkodzone', value: 'uszkodzone' },
    { label: 'Uszkodzone do regeneracji', value: 'uszkodzone_regeneracja' }
];

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

const getInstanceStatusSeverity = (stan) => {
    const map = {
        'nowe': 'success',
        'uzywane': 'info',
        'uszkodzone': 'danger',
        'uszkodzone_regeneracja': 'warning'
    };
    return map[stan] || 'secondary';
};

const getInstanceStatusLabel = (stan) => {
    const map = {
        'nowe': 'Nowe',
        'uzywane': 'Używane',
        'uszkodzone': 'Uszkodzone',
        'uszkodzone_regeneracja': 'Uszkodzone do regeneracji'
    };
    return map[stan] || stan;
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const onToolSelect = async (event) => {
    const tool = event.data;
    activeTabIndex.value = 0;
    await getToolInstances(tool);
    await getToolHistory(tool);
};

const onToolUnselect = () => {
    toolInstances.value = [];
    toolHistory.value = [];
};

const getToolInstances = async (tool) => {
    isLoadingDetails.value = true;
    try {
        const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
        const instances = response.data.results || response.data;
        toolInstances.value = instances.sort((a, b) => b.id - a.id);
    } catch (error) {
        console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
        toolInstances.value = [];
    } finally {
        isLoadingDetails.value = false;
    }
};

const getToolHistory = async (tool) => {
    isLoadingHistory.value = true;
    try {
        const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
        const history = response.data.results || response.data;
        toolHistory.value = history.sort((a, b) => new Date(b.data_wydania) - new Date(a.data_wydania));
    } catch (error) {
        console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
        toolHistory.value = [];
    } finally {
        isLoadingHistory.value = false;
    }
};

const showIssueModal = (instance) => {
    issueData.value.instance = instance;
    issueData.value.machine_id = machines.value.length > 0 ? machines.value[0].id : null;
    issueData.value.pracownik_id = null;
    issueError.value = '';
    issueModalVisible.value = true;
};

const issueTool = async () => {
    if (!issueData.value.pracownik_id) {
        issueError.value = "Wybierz pracownika.";
        return;
    }

    issueError.value = '';

    try {
        await axios.post(`${API_URL}/historia/wydanie/`, {
            egzemplarz_id: issueData.value.instance.id,
            maszyna_id: issueData.value.machine_id,
            pracownik_id: issueData.value.pracownik_id
        });

        issueModalVisible.value = false;
        await fetchInitialData();

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
            await getToolHistory(selectedToolForDetails.value);
        }
    } catch (error) {
        console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
        issueError.value = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
    }
};

const showReturnModal = (usageId) => {
    usageToReturnId.value = usageId;
    returnStatus.value = 'uzywane';

    const usage = usagesInUse.value.find(u => u.id === usageId);
    if (usage && usage.pracownik) {
        returnPracownikId.value = usage.pracownik.id;
    } else {
        returnPracownikId.value = null;
    }

    returnModalVisible.value = true;
};

const confirmReturnTool = async () => {
    try {
        await axios.post(`${API_URL}/historia/${usageToReturnId.value}/zwrot/`, {
            stan_po_zwrocie: returnStatus.value,
            pracownik_zwracajacy_id: returnPracownikId.value
        });

        returnModalVisible.value = false;
        await fetchInitialData();

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
            await getToolHistory(selectedToolForDetails.value);
        }
    } catch (error) {
        console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
        alert("Wystąpił błąd podczas zwracania narzędzia.");
    }
};

const openToolModal = (tool = null) => {
    isEditMode.value = !!tool;
    toolImagePreview.value = null;
    toolImageFile.value = null;
    toolValidationError.value = '';

    if (isEditMode.value) {
        currentTool.value = {
            ...tool,
            podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
            domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
            opakowanie: tool.opakowanie || 'szt',
            ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1
        };
        if (tool.obraz) {
            toolImagePreview.value = tool.obraz;
        }
    } else {
        currentTool.value = {
            podkategoria_id: null,
            opis: '',
            numer_katalogowy: '',
            domyslna_lokalizacja_id: null,
            obraz: null,
            opakowanie: 'szt',
            ilosc_w_opakowaniu: 1
        };
    }

    toolModalVisible.value = true;
};

const onOpakowanieChange = () => {
    if (currentTool.value.opakowanie === 'kompl' && currentTool.value.ilosc_w_opakowaniu <= 1) {
        currentTool.value.ilosc_w_opakowaniu = 2;
    } else if (currentTool.value.opakowanie === 'szt') {
        currentTool.value.ilosc_w_opakowaniu = 1;
    }
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
    toolValidationError.value = '';

    if (currentTool.value.opakowanie === 'kompl' && currentTool.value.ilosc_w_opakowaniu <= 1) {
        toolValidationError.value = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
        return;
    }

    const formData = new FormData();
    formData.append('opis', currentTool.value.opis);
    formData.append('opakowanie', currentTool.value.opakowanie || 'szt');
    formData.append('ilosc_w_opakowaniu', currentTool.value.ilosc_w_opakowaniu || 1);

    if (currentTool.value.podkategoria_id) {
        formData.append('podkategoria_id', currentTool.value.podkategoria_id);
    }

    if (currentTool.value.numer_katalogowy) {
        formData.append('numer_katalogowy', currentTool.value.numer_katalogowy);
    }

    if (currentTool.value.domyslna_lokalizacja_id) {
        formData.append('domyslna_lokalizacja_id', currentTool.value.domyslna_lokalizacja_id);
    }

    if (toolImageFile.value) {
        formData.append('obraz', toolImageFile.value);
    }

    const method = isEditMode.value ? 'patch' : 'post';
    const url = isEditMode.value ? `${API_URL}/narzedzia/${currentTool.value.id}/` : `${API_URL}/narzedzia/`;

    try {
        await axios({
            method: method,
            url: url,
            data: formData,
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        toolModalVisible.value = false;
        await fetchInitialData();
    } catch (error) {
        console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
        toolValidationError.value = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
    }
};

const openInstanceModal = (mode, instance = null) => {
    instanceModal.value.mode = mode;
    instanceModal.value.errorMessage = '';

    if (mode === 'add') {
        instanceModal.value.title = 'Dodaj nowy egzemplarz';
        instanceModal.value.currentInstance = {
            id: null,
            narzedzie_typ_id: selectedToolForDetails.value.id,
            stan: 'nowe',
            lokalizacja_id: null,
            faktura_zakupu_id: null,
            zamowienie_id: null,
            ilosc: 1
        };

        if (selectedToolForDetails.value.domyslna_lokalizacja) {
            instanceModal.value.currentInstance.lokalizacja_id = selectedToolForDetails.value.domyslna_lokalizacja.id;
        } else if (Array.isArray(toolInstances.value) && toolInstances.value.length > 0) {
            const lastInstance = toolInstances.value[0];
            if (lastInstance && lastInstance.lokalizacja) {
                instanceModal.value.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
            }
        }
    } else {
        instanceModal.value.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
        instanceModal.value.currentInstance = {
            ...instance,
            lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
            faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
            zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
            ilosc: 1
        };
    }

    instanceModalVisible.value = true;
};

const saveInstance = async () => {
    isSavingInstance.value = true;
    instanceModal.value.errorMessage = '';

    const method = instanceModal.value.mode === 'add' ? 'post' : 'patch';
    const url = instanceModal.value.mode === 'add'
        ? `${API_URL}/egzemplarze/`
        : `${API_URL}/egzemplarze/${instanceModal.value.currentInstance.id}/`;

    const payload = {
        stan: instanceModal.value.currentInstance.stan,
        lokalizacja_id: instanceModal.value.currentInstance.lokalizacja_id,
        narzedzie_typ_id: instanceModal.value.currentInstance.narzedzie_typ_id,
        faktura_zakupu_id: instanceModal.value.currentInstance.faktura_zakupu_id,
        zamowienie_id: instanceModal.value.currentInstance.zamowienie_id
    };

    const ilosc = instanceModal.value.currentInstance.ilosc;

    if (instanceModal.value.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
        instanceModal.value.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
        isSavingInstance.value = false;
        return;
    }

    try {
        if (instanceModal.value.mode === 'add' && ilosc > 1) {
            const requests = [];
            for (let i = 0; i < ilosc; i++) {
                requests.push(axios.post(url, payload));
            }
            await Promise.all(requests);
        } else {
            await axios({ method, url, data: payload });
        }

        instanceModalVisible.value = false;

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
        }

        await fetchInitialData();
    } catch (error) {
        console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);

        let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';

        if (error.response?.data) {
            if (typeof error.response.data === 'object') {
                errorMsg = Object.entries(error.response.data)
                    .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
                    .join('; ');
            } else {
                errorMsg = `Błąd: ${error.response.data}`;
            }
        } else if (error.message) {
            errorMsg = `Wystąpił błąd sieci lub serwera: ${error.message}.`;
        }

        instanceModal.value.errorMessage = errorMsg;
    } finally {
        isSavingInstance.value = false;
    }
};

const openDeleteInstanceModal = (instance) => {
    instanceToDelete.value = instance;

    const toolName = instance.narzedzie_typ.podkategoria
        ? `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}`
        : instance.narzedzie_typ.opis;

    if (instance.stan === 'uszkodzone') {
        deleteModalMessage.value = `Ten egzemplarz (<strong>${toolName}</strong>) jest oznaczony jako uszkodzony. Zostanie przeniesiony do archiwum. Czy chcesz kontynuować?`;
    } else {
        deleteModalMessage.value = `Czy na pewno chcesz trwale usunąć egzemplarz: <strong>${toolName}</strong>?`;
    }

    deleteInstanceModalVisible.value = true;
};

const confirmDeleteInstance = async () => {
    if (!instanceToDelete.value) return;

    try {
        await axios.delete(`${API_URL}/egzemplarze/${instanceToDelete.value.id}/`);

        deleteInstanceModalVisible.value = false;

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
        }

        await fetchInitialData();
        instanceToDelete.value = null;
    } catch (error) {
        console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);
        deleteInstanceModalVisible.value = false;
        alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
    }
};

const fetchInitialData = async () => {
    try {
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

        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;
        machines.value = machinesRes.data;
        usagesInUse.value = usagesRes.data.results || usagesRes.data;
        locations.value = locationsRes.data;
        podkategorie.value = podkategorieRes.data;

        // Dodaj fullName do pracowników dla dropdown
        const pracownicyData = pracownicyRes.data.results || pracownicyRes.data;
        pracownicy.value = pracownicyData.map(p => ({
            ...p,
            fullName: `${p.nazwisko} ${p.imie}`
        }));

        faktury.value = fakturyRes.data.results || fakturyRes.data;
        zamowienia.value = zamowieniaRes.data.results || zamowieniaRes.data;
    } catch (error) {
        console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
        alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
    }
};

onMounted(() => {
    fetchInitialData();
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
    --dark-accent-hover: #0b5ed7;
    --dark-success: #198754;
    --dark-danger: #dc3545;
    --dark-warning: #ffc107;
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

/* === PRZYCISKI BOOTSTRAP-STYLE === */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    border: 1px solid transparent;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}

.btn-secondary {
    background-color: #6c757d;
    border-color: #6c757d;
    color: #fff;
}
.btn-secondary:hover {
    background-color: #5c636a;
    border-color: #565e64;
    color: #fff;
}

.btn-zwroty {
    background-color: #8B4513;
    border-color: #8B4513;
    color: #fff;
}
.btn-zwroty:hover {
    background-color: #7a3d11;
    border-color: #6d360f;
    color: #fff;
}

.btn-success {
    background-color: #198754;
    border-color: #198754;
    color: #fff;
}
.btn-success:hover {
    background-color: #157347;
    border-color: #146c43;
    color: #fff;
}

.btn-primary {
    background-color: #0d6efd;
    border-color: #0d6efd;
    color: #fff;
}
.btn-primary:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
    color: #fff;
}

.btn-danger {
    background-color: #dc3545;
    border-color: #dc3545;
    color: #fff;
}
.btn-danger:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
    color: #fff;
}

.btn-dark {
    background-color: #212529;
    border-color: #212529;
    color: #fff;
}
.btn-dark:hover {
    background-color: #1c1f23;
    border-color: #1a1e21;
    color: #fff;
}

.btn-sm {
    padding: 4px 8px;
    font-size: 0.875rem;
}

.btn-sm .pi {
    font-size: 0.875rem;
}

.header-buttons a {
    text-decoration: none;
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

/* === PANEL NARZĘDZI (GÓRNY) - STYL JAK NAGŁÓWEK === */
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

/* === TABELE PRIMEVUE - STYL JAK NAGŁÓWEK === */
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

/* === PANEL SZCZEGÓŁÓW (DOLNY) - STYL JAK NAGŁÓWEK === */
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

/* === ZAKŁADKI (TABS) - STYL JAK NAGŁÓWEK === */
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
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

/* Tab badge styling */
.tab-badge {
    display: inline-block;
    margin-left: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 500;
    background-color: #6c757d;
    color: white;
    border-radius: 4px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
}

/* Button group inline */
.btn-group-inline {
    display: inline-flex;
    gap: 4px;
    white-space: nowrap;
}

/* === STANY === */
.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    flex: 1;
}

.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    color: #6c757d;
    text-align: center;
    flex: 1;
}

/* === FORMULARZE (MODAL) - CIEMNY MOTYW === */
.field {
    margin-bottom: 16px;
}

.field label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: var(--dark-text-primary);
}

:deep(.field .p-inputtext),
:deep(.field .p-dropdown),
:deep(.field .p-inputnumber),
:deep(.field .p-password) {
    width: 100%;
}

.return-status-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.field-radiobutton {
    display: flex;
    align-items: center;
    gap: 8px;
}

.field-radiobutton label {
    margin-bottom: 0;
    font-weight: normal;
    cursor: pointer;
}

.tool-image-preview {
    max-width: 150px;
    border-radius: 8px;
    margin-top: 10px;
}

/* === O PROGRAMIE - CIEMNY MOTYW === */
.about-content {
    text-align: center;
    color: var(--dark-text-primary);
}

.about-header {
    margin-bottom: 24px;
}

.about-logo {
    width: 80px;
    height: 80px;
}

.about-table {
    width: 100%;
    text-align: left;
    color: var(--dark-text-primary);
}

.about-table td {
    padding: 8px 0;
}

.about-table .label {
    text-align: right;
    color: var(--dark-text-muted);
    padding-right: 16px;
    width: 40%;
}

/* === PRZYCISKI === */
:deep(.p-button-sm) {
    padding: 6px 10px;
    font-size: 0.875rem;
}

:deep(.p-button-sm .p-button-icon) {
    font-size: 0.875rem;
}

/* === TAGI/BADGE === */
:deep(.p-tag) {
    font-size: 0.8rem;
    padding: 4px 8px;
}

/* === UTILITY === */
.text-muted {
    color: #6c757d;
}

.text-danger {
    color: #dc3545;
}

.text-center {
    text-align: center;
}

.ml-2 {
    margin-left: 8px;
}

.mr-1 {
    margin-right: 4px;
}

.mt-3 {
    margin-top: 16px;
}

/* === WARTOŚĆ ZEROWA W TABELI === */
.zero-value {
    color: #6c757d !important;
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

<!-- Style dla menu popup (bez scoped - menu jest renderowane jako portal) - CIEMNY MOTYW -->
<style>
#user_menu {
    min-width: 180px !important;
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.5) !important;
    padding: 6px 0 !important;
}

#user_menu_list {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}

#user_menu_list li {
    margin: 0 !important;
    padding: 0 !important;
}

#user_menu_list li > div {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    transition: background-color 0.15s !important;
}

#user_menu_list li > div:hover {
    background-color: #3d444d !important;
}

#user_menu_list li > div > a,
#user_menu_list li > div > div {
    display: flex !important;
    align-items: center !important;
    padding: 10px 16px !important;
    color: #dee2e6 !important;
    text-decoration: none !important;
    gap: 10px !important;
    cursor: pointer !important;
}

#user_menu_list li > div span[class*="icon"],
#user_menu_list li > div i,
#user_menu_list li > div .pi {
    color: #adb5bd !important;
    font-size: 1rem !important;
}

#user_menu_list li > div span:not([class*="icon"]):not(.pi) {
    color: #dee2e6 !important;
    font-size: 14px !important;
}

#user_menu li[data-pc-section="separator"] {
    border: none !important;
    border-top: 1px solid #495057 !important;
    margin: 6px 0 !important;
    padding: 0 !important;
    height: 0 !important;
}

/* === MODALE PRIMEVUE - KOMPLETNY CIEMNY MOTYW === */

/* Overlay/Backdrop */
.p-dialog-mask {
    background-color: rgba(0, 0, 0, 0.6) !important;
    backdrop-filter: blur(2px);
}

/* Główny kontener dialogu */
.p-dialog {
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 8px !important;
    color: #dee2e6 !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
    overflow: hidden;
}

/* Nagłówek dialogu */
.p-dialog .p-dialog-header {
    background: linear-gradient(to bottom, #3d444d, #343a40) !important;
    border-bottom: 1px solid #495057 !important;
    color: #fff !important;
    padding: 16px 20px !important;
}

.p-dialog .p-dialog-header .p-dialog-title {
    color: #ffc107 !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
}

/* Przycisk zamknięcia */
.p-dialog .p-dialog-header-icons {
    display: flex;
    gap: 4px;
}

.p-dialog .p-dialog-header-icon {
    background: transparent !important;
    border: none !important;
    color: #adb5bd !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 4px !important;
    transition: all 0.15s ease !important;
}

.p-dialog .p-dialog-header-icon:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #fff !important;
}

.p-dialog .p-dialog-header-icon:focus {
    box-shadow: none !important;
}

/* Zawartość dialogu */
.p-dialog .p-dialog-content {
    background: #2d3238 !important;
    color: #dee2e6 !important;
    padding: 20px !important;
}

/* Stopka dialogu */
.p-dialog .p-dialog-footer {
    background: linear-gradient(to bottom, #343a40, #2d3238) !important;
    border-top: 1px solid #495057 !important;
    padding: 12px 20px !important;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}

/* Etykiety w formularzach */
.p-dialog .field label {
    color: #dee2e6 !important;
    font-weight: 500;
    margin-bottom: 8px;
    display: block;
}

/* RadioButton w dialogach */
.p-radiobutton .p-radiobutton-box {
    background: #343a40 !important;
    border-color: #6c757d !important;
    width: 20px !important;
    height: 20px !important;
}

.p-radiobutton .p-radiobutton-box:hover {
    border-color: #adb5bd !important;
}

.p-radiobutton .p-radiobutton-box.p-highlight {
    background: #0d6efd !important;
    border-color: #0d6efd !important;
}

.p-radiobutton .p-radiobutton-box .p-radiobutton-icon {
    background: #fff !important;
}

/* Message w dialogach */
.p-dialog .p-message {
    margin: 0 0 16px 0 !important;
    border-radius: 6px !important;
}

.p-dialog .p-message.p-message-error {
    background: rgba(220, 38, 38, 0.15) !important;
    border: 1px solid rgba(220, 38, 38, 0.4) !important;
    color: #f87171 !important;
}

.p-dialog .p-message .p-message-wrapper {
    padding: 12px 16px !important;
}

.p-dialog .p-message .p-message-text {
    color: #f87171 !important;
}

/* InputText disabled w dialogach */
.p-dialog .p-inputtext:disabled,
.p-dialog .p-inputtext[disabled] {
    background: #212529 !important;
    color: #6c757d !important;
    opacity: 0.8 !important;
    cursor: not-allowed !important;
}

/* Tekst danger w dialogach */
.p-dialog .text-danger {
    color: #f87171 !important;
    font-weight: 500;
}

/* Podgląd obrazu w dialogach */
.p-dialog .tool-image-preview {
    max-width: 150px;
    border-radius: 8px;
    margin-top: 10px;
    border: 1px solid #495057;
}

/* Input file w dialogach */
.p-dialog input[type="file"] {
    background: #343a40 !important;
    border: 1px solid #495057 !important;
    border-radius: 4px !important;
    color: #dee2e6 !important;
    padding: 8px !important;
    width: 100% !important;
}

.p-dialog input[type="file"]::file-selector-button {
    background: #495057 !important;
    border: none !important;
    border-radius: 4px !important;
    color: #fff !important;
    padding: 6px 12px !important;
    margin-right: 10px !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
}

.p-dialog input[type="file"]::file-selector-button:hover {
    background: #5c636a !important;
}

/* About modal specjalne style */
.p-dialog .about-content {
    text-align: center;
}

.p-dialog .about-header h4 {
    color: #ffc107 !important;
    margin: 10px 0 5px 0;
}

.p-dialog .about-header p {
    color: #adb5bd !important;
}

.p-dialog .about-table {
    margin-top: 20px;
}

.p-dialog .about-table td {
    padding: 8px 0;
    color: #dee2e6;
}

.p-dialog .about-table .label {
    color: #adb5bd !important;
}

.p-dialog .about-table a {
    color: #0d6efd !important;
    text-decoration: none;
}

.p-dialog .about-table a:hover {
    color: #3d8bfd !important;
    text-decoration: underline;
}

/* About modal footer */
.about-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.about-footer .copyright {
    color: #6c757d !important;
    font-size: 0.85rem;
}

/* === PRZYCISKI W MODALACH - STYL JAK W GŁÓWNYM OKNIE === */

/* Przycisk główny (niebieski) */
.p-dialog .p-button:not(.p-button-text):not(.p-button-secondary):not(.p-button-success):not(.p-button-danger):not(.btn-modal-secondary) {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button:not(.p-button-text):not(.p-button-secondary):not(.p-button-success):not(.p-button-danger):not(.btn-modal-secondary):hover {
    background-color: #0b5ed7 !important;
    border-color: #0a58ca !important;
}

/* Przycisk tekstowy (Anuluj) */
.p-dialog .p-button.p-button-text {
    background: transparent !important;
    border: 1px solid #6c757d !important;
    color: #adb5bd !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
}

.p-dialog .p-button.p-button-text:hover {
    background: rgba(108, 117, 125, 0.2) !important;
    border-color: #adb5bd !important;
    color: #dee2e6 !important;
}

/* Przycisk secondary (szary) */
.p-dialog .p-button.btn-modal-secondary,
.p-dialog .p-button.p-button-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-secondary:hover,
.p-dialog .p-button.p-button-secondary:hover {
    background-color: #5c636a !important;
    border-color: #565e64 !important;
}

/* Przycisk success (zielony) */
.p-dialog .p-button.p-button-success {
    background-color: #198754 !important;
    border-color: #198754 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.p-button-success:hover {
    background-color: #157347 !important;
    border-color: #146c43 !important;
}

/* Przycisk danger (czerwony) */
.p-dialog .p-button.p-button-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.p-button-danger:hover {
    background-color: #bb2d3b !important;
    border-color: #b02a37 !important;
}

/* === UJEDNOLICONA WYSOKOŚĆ PÓL W MODALACH === */
.p-dialog .p-inputtext,
.p-dialog .p-dropdown,
.p-dialog .p-inputnumber,
.p-dialog .p-inputnumber-input {
    height: 40px !important;
    min-height: 40px !important;
}

.p-dialog .p-dropdown .p-dropdown-label {
    padding: 8px 12px !important;
    line-height: 1.5 !important;
}

.p-dialog .p-inputtext {
    padding: 8px 12px !important;
    line-height: 1.5 !important;
}

.p-dialog .p-inputnumber {
    width: 100% !important;
}

.p-dialog .p-inputnumber-input {
    padding: 8px 12px !important;
    width: 100% !important;
}

/* PrimeVue Dropdown/Select - Bootstrap 5 Dark */
.p-dropdown {
    background: #343a40 !important;
    border: 1px solid #495057 !important;
    border-radius: 4px !important;
    color: #dee2e6 !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.p-dropdown:hover {
    border-color: #6c757d !important;
}

.p-dropdown:focus,
.p-dropdown.p-focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
}

.p-dropdown .p-dropdown-label {
    color: #dee2e6 !important;
    padding: 8px 12px !important;
}

.p-dropdown .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
}

.p-dropdown .p-dropdown-trigger {
    background: transparent !important;
    color: #adb5bd !important;
    width: 40px !important;
}

.p-dropdown-panel {
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
    margin-top: 2px !important;
}

.p-dropdown-header {
    background: #343a40 !important;
    border-bottom: 1px solid #495057 !important;
    padding: 10px !important;
}

.p-dropdown-header .p-dropdown-filter {
    background: #495057 !important;
    border-color: #6c757d !important;
    color: #fff !important;
}

.p-dropdown-items-wrapper {
    background: #2d3238 !important;
    max-height: 300px !important;
}

.p-dropdown-items {
    padding: 4px 0 !important;
}

.p-dropdown-item {
    color: #dee2e6 !important;
    padding: 10px 16px !important;
    transition: background 0.15s ease !important;
}

.p-dropdown-item:hover {
    background: #3d444d !important;
}

.p-dropdown-item.p-highlight {
    background: #4a3728 !important;
    color: #fff !important;
}

.p-dropdown-item-group {
    background: #343a40 !important;
    color: #ffc107 !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
}

/* Dropdown empty message */
.p-dropdown-empty-message {
    color: #6c757d !important;
    padding: 10px 16px !important;
}

/* PrimeVue InputText - Bootstrap 5 Dark */
.p-inputtext {
    background: #343a40 !important;
    border-color: #495057 !important;
    color: #dee2e6 !important;
}

.p-inputtext:focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
}

/* PrimeVue InputNumber - Bootstrap 5 Dark */
.p-inputnumber-input {
    background: #343a40 !important;
    border-color: #495057 !important;
    color: #dee2e6 !important;
}

/* === PRZYCISKI PRIMEVUE - BOOTSTRAP COLORS === */
.p-button {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    font-weight: 500 !important;
}

.p-button.p-button-success {
    background-color: #198754 !important;
    border-color: #198754 !important;
}
.p-button.p-button-success:hover {
    background-color: #157347 !important;
    border-color: #146c43 !important;
}

.p-button.p-button-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
}
.p-button.p-button-secondary:hover {
    background-color: #5c636a !important;
    border-color: #565e64 !important;
}

.p-button.p-button-primary {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
}
.p-button.p-button-primary:hover {
    background-color: #0b5ed7 !important;
    border-color: #0a58ca !important;
}

.p-button.p-button-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
}
.p-button.p-button-danger:hover {
    background-color: #bb2d3b !important;
    border-color: #b02a37 !important;
}

.p-button.p-button-sm {
    padding: 0.4rem 0.65rem !important;
    font-size: 0.875rem !important;
}

/* Tag/Badge colors */
.p-tag.p-tag-success {
    background-color: #198754 !important;
}
.p-tag.p-tag-danger {
    background-color: #dc3545 !important;
}
.p-tag.p-tag-warning {
    background-color: #ffc107 !important;
    color: #000 !important;
}
.p-tag.p-tag-info {
    background-color: #0dcaf0 !important;
    color: #000 !important;
}
.p-tag.p-tag-secondary {
    background-color: #6c757d !important;
}
</style>

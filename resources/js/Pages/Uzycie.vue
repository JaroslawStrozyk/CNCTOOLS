<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">NARZĘDZIA W UŻYCIU</h2>
            <!-- Tryb produkcja - imię na środku (poza header-buttons) -->
            <div v-if="trybProdukcja" class="header-user-name-prod">
                {{ auth.user.first_name }} {{ auth.user.last_name }}
            </div>
            <div class="header-buttons">
                <!-- Pełny tryb magazynu -->
                <template v-if="!trybProdukcja">
                    <button class="btn btn-success" @click="goToMagazyn" title="Wróć do Magazynu">
                        <i class="pi pi-arrow-left"></i> Magazyn
                    </button>
                    <div class="dropdown-wrapper">
                        <button class="user-dropdown-btn" @click="toggleUserMenu">
                            <i class="pi pi-user"></i>
                            {{ auth.user.first_name }} {{ auth.user.last_name }}
                            <i class="pi pi-chevron-down"></i>
                        </button>
                        <Menu ref="userMenu" id="user_menu" :model="userMenuItems" :popup="true" />
                    </div>
                </template>
                <!-- Tryb produkcja - buttony po prawej -->
                <template v-else>
                    <button class="btn-narzedzia-prod" @click="goToMagazyn">
                        <i class="pi pi-arrow-left"></i>
                        Wróć do Narzędzi
                    </button>
                    <button class="btn-exit-prod" @click="logout">
                        <i class="pi pi-sign-out"></i>
                        Wyjście
                    </button>
                </template>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="magazyn-main">
            <div class="usage-panel">
                <div class="in-use-header">
                    <input
                        type="text"
                        v-model="searchInput"
                        placeholder="Szukaj..."
                        class="form-control search-input"
                    />
                    <h3 class="panel-title">
                        Narzędzia aktualnie w użyciu
                        <Badge :value="usagesInUse.length" style="background-color: #8B4513;" class="ml-2" />
                    </h3>
                    <div class="filter-row">
                        <label>Filtruj po maszynie:</label>
                        <select
                            v-model="selectedMaszynaFilter"
                            class="form-select filter-select"
                            style="width: 220px;"
                        >
                            <option :value="null">Wszystkie maszyny</option>
                            <option v-for="m in machines" :key="m.id" :value="m.id">
                                {{ m.nazwa }}
                            </option>
                        </select>
                        <label>Filtruj po narzędziu:</label>
                        <select
                            v-model="selectedNarzedzieFilter"
                            class="form-select filter-select"
                            style="width: 220px;"
                        >
                            <option :value="null">Wszystkie narzędzia</option>
                            <option v-for="n in narzedzieFilterOptions" :key="n.id" :value="n.id">
                                {{ n.label }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="panel-body">
                    <!-- Wirtualny scroller: renderowane są tylko widoczne wiersze (lista bywa >1000 pozycji).
                         Wymaga stałej wysokości wiersza — stąd tableLayout="fixed" i nowrap w komórkach. -->
                    <DataTable
                        :value="filteredUsagesInUse"
                        :loading="isLoadingUsages"
                        :scrollable="true"
                        scrollHeight="flex"
                        tableLayout="fixed"
                        :virtualScrollerOptions="{ itemSize: 38 }"
                        dataKey="id"
                        class="usage-datatable"
                    >
                        <Column header="Narzędzie">
                            <template #body="{ data }">
                                <span v-if="data._kategoria"><strong>{{ data._kategoria }}</strong> / {{ data._podkategoria }} - </span>{{ data._opis }}
                            </template>
                        </Column>
                        <Column header="Maszyna" style="width: 180px;">
                            <template #body="{ data }">
                                {{ data._maszynaNazwa }}
                            </template>
                        </Column>
                        <Column header="Pracownik" style="width: 200px;">
                            <template #body="{ data }">
                                {{ data._pracownikNazwa }}
                            </template>
                        </Column>
                        <Column header="Data pobrania" style="width: 190px;">
                            <template #body="{ data }">
                                <span v-html="data._dataWydania"></span>
                            </template>
                        </Column>
                        <Column header="Oznaczenie" style="width: 160px;">
                            <template #body="{ data }">
                                {{ data._oznaczenie }}
                            </template>
                        </Column>
                        <Column header="Opakowanie" style="width: 160px;">
                            <template #body="{ data }">
                                <span v-html="data._opakowanie"></span>
                            </template>
                        </Column>
                        <Column field="nr_zlecenia" header="Nr zlecenia" style="width: 140px;" />
                        <Column v-if="!trybProdukcja" header="Akcje" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <Button icon="pi pi-undo" class="p-button-success p-button-sm" @click="showReturnModal(data.id)" title="Zwróć" />
                            </template>
                        </Column>
                        <template #empty>
                            <div class="empty-state">Brak narzędzi w użyciu.</div>
                        </template>
                    </DataTable>
                </div>
            </div>
        </main>

        <!-- Modal: Zwróć narzędzie -->
        <Dialog v-model:visible="returnModalVisible" header="Zwrot narzędzia" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <!-- Info o zwracanym egzemplarzu -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz">
                    <label>Narzędzie</label>
                    <InputText :value="returnData.usage.egzemplarz.narzedzie_typ?.opis || ''" disabled />
                    <small class="text-muted">
                        {{ returnData.usage.egzemplarz.ilosc_w_komplecie }} szt.
                        <template v-if="returnData.usage.egzemplarz.jednostka === 'kompl'"> <span class="hint-text">(komplet)</span></template>
                    </small>
                </div>
                <div class="field">
                    <label>Pracownik zwracający <span class="required-mark">*</span></label>
                    <Dropdown
                        v-model="returnPracownikId"
                        :options="pracownicy"
                        optionLabel="fullName"
                        optionValue="id"
                        placeholder="Wybierz pracownika"
                        :filter="true"
                    />
                </div>
                <!-- Wybór typu zwrotu - tylko gdy egzemplarz ma więcej niż 1 szt -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz && returnData.usage.egzemplarz.ilosc_w_komplecie > 1">
                    <label>Ile zwracasz?</label>
                    <Dropdown
                        v-model="returnData.typZwrotu"
                        :options="typZwrotuOptions"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>
                <!-- Ilość sztuk do zwrotu -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz && returnData.usage.egzemplarz.ilosc_w_komplecie > 1 && returnData.typZwrotu === 'czesc'">
                    <label>Ilość sztuk do zwrotu</label>
                    <InputNumber
                        v-model="returnData.iloscSztuk"
                        :min="1"
                        :max="returnData.usage.egzemplarz.ilosc_w_komplecie - 1"
                    />
                    <small class="text-muted">
                        Pozostanie w użyciu: {{ returnData.usage.egzemplarz.ilosc_w_komplecie - returnData.iloscSztuk }} szt.
                    </small>
                </div>
                <div class="field">
                    <label>W jakim stanie technicznym zwracasz narzędzie?</label>
                    <div class="return-status-options">
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanNowe" value="nowe" />
                            <label for="stanNowe">Nowym <span class="hint-text">(nie używane)</span></label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUzywane" value="uzywane" />
                            <label for="stanUzywane">Dobrym <span class="hint-text">(jako używane)</span></label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzone" value="uszkodzone" />
                            <label for="stanUszkodzone">Uszkodzonym</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzoneRegen" value="uszkodzone_regeneracja" />
                            <label for="stanUszkodzoneRegen">Zużytym</label>
                        </div>
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="returnModalVisible = false" />
                <Button label="Potwierdź zwrot" icon="pi pi-check" class="p-button-success" @click="confirmReturnTool" />
            </template>
        </Dialog>

        <!-- Modal: Karta uszkodzenia -->
        <Dialog v-model:visible="kartaUszkodzeniaModalVisible" header="Karta uszkodzenia" :modal="true" :style="{ width: '1100px' }">
            <div class="p-fluid">
                <div class="karta-row">
                    <div class="field">
                        <label>Nr karty</label>
                        <InputText :value="kartaUszkodzenia.numer_karty" disabled class="karta-numer" />
                    </div>
                    <div class="field">
                        <label>Data wystawienia</label>
                        <InputText :value="kartaUszkodzenia.data_wystawienia" disabled />
                    </div>
                </div>
                <div class="karta-row">
                    <div class="field">
                        <label>Maszyna</label>
                        <InputText :value="kartaUszkodzenia.maszyna" disabled />
                    </div>
                    <div class="field">
                        <label>Uszkodzone narzędzie</label>
                        <InputText :value="kartaUszkodzenia.narzedzie" disabled />
                    </div>
                </div>
                <div class="karta-row">
                    <div class="field">
                        <label>Kto zgłasza uszkodzenie?</label>
                        <Dropdown
                            v-model="kartaUszkodzenia.typ_zglaszajacego"
                            :options="typZglaszajacegoOptions"
                            optionLabel="label"
                            optionValue="value"
                            @change="onTypZglaszajacegoChange"
                        />
                    </div>
                    <div class="field">
                        <label>Nazwisko zgłaszającego</label>
                        <InputText v-model="kartaUszkodzenia.nazwisko_zglaszajacego" disabled />
                    </div>
                </div>
                <div class="field">
                    <label>Przyczyna uszkodzenia</label>
                    <Textarea
                        v-model="kartaUszkodzenia.przyczyna_uszkodzenia"
                        rows="3"
                        :autoResize="false"
                        class="karta-textarea"
                    />
                </div>
                <div class="field">
                    <label>Uwagi</label>
                    <Textarea
                        v-model="kartaUszkodzenia.uwagi"
                        rows="3"
                        :autoResize="false"
                        class="karta-textarea"
                    />
                </div>
                <div class="field">
                    <label>Stracony czas na maszynach</label>
                    <InputText v-model="kartaUszkodzenia.stracony_czas" />
                </div>
                <Message v-if="kartaUszkodzeniaError" severity="error" :closable="false">{{ kartaUszkodzeniaError }}</Message>
            </div>
            <template #footer>
                <Button class="p-button-text" @click="anulujKarteUszkodzenia">
                    <i class="pi pi-arrow-left mr-2"></i> Wróć
                </Button>
                <Button class="p-button-danger" @click="zatwierdzKarteUszkodzenia">
                    <i class="pi pi-check mr-2"></i> Zatwierdź kartę
                </Button>
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
import { ref, shallowRef, computed, watch, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';

// PrimeVue Components
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Badge from 'primevue/badge';
import Message from 'primevue/message';
import Menu from 'primevue/menu';
import RadioButton from 'primevue/radiobutton';
import Textarea from 'primevue/textarea';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { first_name: '', last_name: '', username: '' },
            isLogistyka: false,
            isAdministrator: false
        })
    },
    urls: {
        type: Object,
        default: () => ({
            magazyn: '/magazyn/',
            ustawienia: '/ustawienia/',
            logout: '/logout/'
        })
    },
    infoProgram: {
        type: Object,
        default: () => ({})
    },
    trybProdukcja: {
        type: Boolean,
        default: false
    },
    autoLogoutMinutes: {
        type: Number,
        default: 0
    }
});

// Data
// shallowRef: lista bywa >1000 pozycji — nie ma potrzeby robić jej głęboko reaktywną
// (rekordy są tylko czytane, a podmieniamy zawsze całą tablicę).
const usagesInUse = shallowRef([]);
const machines = shallowRef([]);
const pracownicy = shallowRef([]);
const selectedMaszynaFilter = ref(null);
const selectedNarzedzieFilter = ref(null);
const isLoadingUsages = ref(true);

// Wyszukiwarka z debounce — bez tego każdy znak przefiltrowałby i przerysował całą tabelę.
const searchInput = ref('');
const inUseSearchQuery = ref('');
let searchDebounceTimer = null;
watch(searchInput, (val) => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => { inUseSearchQuery.value = val; }, 250);
});

// Modals visibility
const returnModalVisible = ref(false);
const kartaUszkodzeniaModalVisible = ref(false);
const aboutModalVisible = ref(false);

// Zwrot narzędzia
const returnStatus = ref('uzywane');
const returnPracownikId = ref(null);
const usageToReturnId = ref(null);
const returnData = ref({
    usage: null,           // Pełne dane o wydaniu
    typZwrotu: 'calosc',   // 'calosc' lub 'czesc'
    iloscSztuk: 1          // Ilość zwracanych sztuk przy częściowym zwrocie
});

// Opcje dla typu zwrotu
const typZwrotuOptions = [
    { label: 'Całość', value: 'calosc' },
    { label: 'Tylko część', value: 'czesc' }
];

// Karta uszkodzenia
const kartaUszkodzenia = ref({
    numer_karty: '',
    data_wystawienia: '',
    maszyna: '',
    narzedzie: '',
    typ_zglaszajacego: 'pobierajacy',
    nazwisko_zglaszajacego: '',
    przyczyna_uszkodzenia: '',
    uwagi: '',
    stracony_czas: ''
});
const kartaUszkodzeniaError = ref('');

// Opcje dla typu zgłaszającego
const typZglaszajacegoOptions = [
    { label: 'Osoba pobierająca', value: 'pobierajacy' },
    { label: 'Osoba zwracająca', value: 'zwracajacy' }
];

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
    {
        label: 'Ustawienia',
        icon: 'pi pi-cog',
        command: () => { window.location.href = (props.urls.ustawienia || '/ustawienia/') + '?from=magazyn'; }
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

const toggleUserMenu = (event) => {
    userMenu.value.toggle(event);
};

// Powrót na stronę Magazynu (w trybie produkcja zachowujemy parametr trybu)
const goToMagazyn = () => {
    const base = props.urls.magazyn || '/magazyn/';
    window.location.href = props.trybProdukcja ? `${base}?tryb=produkcja` : base;
};

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

// Computed
// Lista unikalnych par "Kategoria / Podkategoria" obecnych w tabeli.
// Klucz unikalności: id podkategorii (każda podkategoria należy do jednej kategorii).
const narzedzieFilterOptions = computed(() => {
    const map = new Map();
    for (const usage of usagesInUse.value) {
        if (!usage._podkategoriaId || map.has(usage._podkategoriaId)) continue;
        const label = usage._kategoria && usage._podkategoria
            ? `${usage._kategoria} / ${usage._podkategoria}`
            : (usage._kategoria || usage._podkategoria);
        if (!label) continue;
        map.set(usage._podkategoriaId, { id: usage._podkategoriaId, label });
    }
    return Array.from(map.values()).sort((a, b) => a.label.localeCompare(b.label, 'pl'));
});

// Filtrowanie po gotowych polach wyliczonych raz przy pobraniu danych (patrz przygotujUsages) —
// jeden przebieg po tablicy, bez sklejania stringów i schodzenia w zagnieżdżone obiekty.
const filteredUsagesInUse = computed(() => {
    const maszynaId = selectedMaszynaFilter.value;
    const podkategoriaId = selectedNarzedzieFilter.value;
    const query = inUseSearchQuery.value.trim().toLowerCase();

    if (!maszynaId && !podkategoriaId && !query) return usagesInUse.value;

    return usagesInUse.value.filter(usage => (
        (!maszynaId || usage._maszynaId === maszynaId) &&
        (!podkategoriaId || usage._podkategoriaId === podkategoriaId) &&
        (!query || usage._search.includes(query))
    ));
});

// Methods
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
        return `${year}-${month}-${day} <span class="date-time">[${hours}:${minutes}]</span>`;
    } catch (e) {
        console.error("Błąd formatowania daty:", dateString, e);
        return 'Błąd daty';
    }
};

// Jednorazowe spłaszczenie rekordu: wszystko, co tabela wyświetla i po czym filtrujemy,
// liczymy raz po pobraniu danych. Dzięki temu render wiersza i filtr są czystym odczytem pól.
const przygotujUsages = (rows) => rows.map(usage => {
    const egz = usage.egzemplarz;
    const nt = egz?.narzedzie_typ;
    const podk = nt?.podkategoria;
    const kategoria = podk?.kategoria?.nazwa || '';
    const podkategoria = podk?.nazwa || '';
    const opis = nt?.opis || '';
    const pracownikNazwa = usage.pracownik
        ? `${usage.pracownik.nazwisko} ${usage.pracownik.imie}`
        : 'Brak';
    const oznaczenie = egz?.oznaczenie || '';

    let opakowanie;
    if (egz?.jednostka === 'kompl') {
        opakowanie = `Komplet <span class="hint-text">(${egz.ilosc_w_komplecie} szt.)</span>`;
    } else if (nt?.opakowanie === 'kompl') {
        opakowanie = `${egz.ilosc_w_komplecie} z kompletu`;
    } else {
        opakowanie = 'Sztuka';
    }

    return {
        ...usage,
        _kategoria: kategoria,
        _podkategoria: podkategoria,
        _podkategoriaId: podk?.id ?? null,
        _opis: opis,
        _maszynaId: usage.maszyna?.id ?? null,
        _maszynaNazwa: usage.maszyna?.nazwa || 'Brak',
        _pracownikNazwa: pracownikNazwa,
        _oznaczenie: oznaczenie,
        _opakowanie: opakowanie,
        _dataWydania: formatCustomDate(usage.data_wydania),
        _search: `${kategoria} ${podkategoria} ${opis} ${pracownikNazwa} ${usage.nr_zlecenia || ''} ${oznaczenie}`.toLowerCase(),
    };
});

const showReturnModal = async (usageId) => {
    // Lista pracowników jest potrzebna dopiero tutaj — na starcie strony jej nie czekamy.
    await ensurePracownicy();
    usageToReturnId.value = usageId;
    returnStatus.value = 'uzywane';

    const usage = usagesInUse.value.find(u => u.id === usageId);

    // Zapisz pełne dane o wydaniu do returnData
    returnData.value.usage = usage;
    returnData.value.typZwrotu = 'calosc';
    returnData.value.iloscSztuk = 1;

    if (usage && usage.pracownik) {
        returnPracownikId.value = usage.pracownik.id;
    } else {
        returnPracownikId.value = null;
    }

    returnModalVisible.value = true;
};

const confirmReturnTool = async () => {
    const usage = returnData.value.usage;
    const isPartialReturn = usage && usage.egzemplarz &&
        usage.egzemplarz.ilosc_w_komplecie > 1 &&
        returnData.value.typZwrotu === 'czesc';

    // Walidacja częściowego zwrotu
    if (isPartialReturn) {
        const iloscSztuk = returnData.value.iloscSztuk;
        const maxSztuk = usage.egzemplarz.ilosc_w_komplecie - 1;
        if (!Number.isInteger(iloscSztuk) || iloscSztuk < 1 || iloscSztuk > maxSztuk) {
            alert(`Ilość sztuk musi być liczbą od 1 do ${maxSztuk}.`);
            return;
        }
    }

    // Jeśli stan to 'uszkodzone', otwórz modal karty uszkodzenia
    if (returnStatus.value === 'uszkodzone') {
        otworzKarteUszkodzenia();
        return;
    }

    // Dla innych stanów (w tym uszkodzone_regeneracja) - bezpośredni zwrot
    await wykonajZwrot();
};

// Otwiera modal karty uszkodzenia z wypełnionymi danymi
const otworzKarteUszkodzenia = async () => {
    const usage = returnData.value.usage;
    const today = new Date();
    const formattedDate = `${String(today.getDate()).padStart(2, '0')}.${String(today.getMonth() + 1).padStart(2, '0')}.${today.getFullYear()}`;

    // Pobierz nazwisko pracownika pobierającego
    const pracownikPobierajacy = usage?.pracownik;
    const nazwiskoPobierajacy = pracownikPobierajacy
        ? `${pracownikPobierajacy.nazwisko} ${pracownikPobierajacy.imie}`
        : '';

    // Pobierz nazwisko pracownika zwracającego
    const pracownikZwracajacyObj = pracownicy.value.find(p => p.id === returnPracownikId.value);
    const nazwiskoZwracajacy = pracownikZwracajacyObj
        ? `${pracownikZwracajacyObj.nazwisko} ${pracownikZwracajacyObj.imie}`
        : '';

    // Pobierz następny numer karty z backendu
    let numerKarty = `${today.getFullYear()}/1`;
    try {
        const response = await axios.get(`${API_URL}/uszkodzenia/nastepny_numer_karty/`);
        numerKarty = response.data.numer_karty;
    } catch (error) {
        console.warn('Nie udało się pobrać numeru karty z backendu:', error);
    }

    kartaUszkodzenia.value = {
        numer_karty: numerKarty,
        data_wystawienia: formattedDate,
        maszyna: usage?.maszyna?.nazwa || 'Brak',
        narzedzie: usage?.egzemplarz?.narzedzie_typ?.opis || '',
        typ_zglaszajacego: 'pobierajacy',
        nazwisko_zglaszajacego: nazwiskoPobierajacy,
        przyczyna_uszkodzenia: '',
        uwagi: '',
        stracony_czas: '',
        // Dodatkowe dane do późniejszego użycia
        _nazwisko_pobierajacy: nazwiskoPobierajacy,
        _nazwisko_zwracajacy: nazwiskoZwracajacy
    };
    kartaUszkodzeniaError.value = '';

    returnModalVisible.value = false;
    kartaUszkodzeniaModalVisible.value = true;
};

// Zmiana typu zgłaszającego - aktualizuje nazwisko
const onTypZglaszajacegoChange = (event) => {
    const val = event?.value ?? kartaUszkodzenia.value.typ_zglaszajacego;
    kartaUszkodzenia.value.nazwisko_zglaszajacego = val === 'pobierajacy'
        ? kartaUszkodzenia.value._nazwisko_pobierajacy
        : kartaUszkodzenia.value._nazwisko_zwracajacy;
};

// Anuluj kartę i wróć do modalu zwrotu
const anulujKarteUszkodzenia = () => {
    kartaUszkodzeniaModalVisible.value = false;
    returnModalVisible.value = true;
};

// Zatwierdź kartę uszkodzenia i wykonaj zwrot
const zatwierdzKarteUszkodzenia = async () => {
    kartaUszkodzeniaError.value = '';

    // Wykonaj zwrot z danymi karty uszkodzenia
    await wykonajZwrot({
        przyczyna_uszkodzenia: kartaUszkodzenia.value.przyczyna_uszkodzenia,
        uwagi: kartaUszkodzenia.value.uwagi,
        stracony_czas: kartaUszkodzenia.value.stracony_czas,
        typ_zglaszajacego: kartaUszkodzenia.value.typ_zglaszajacego,
        nazwisko_zglaszajacego: kartaUszkodzenia.value.nazwisko_zglaszajacego
    });

    kartaUszkodzeniaModalVisible.value = false;
};

// Wykonuje faktyczny zwrot narzędzia
const wykonajZwrot = async (kartaData = null) => {
    const usage = returnData.value.usage;
    const isPartialReturn = usage && usage.egzemplarz &&
        usage.egzemplarz.ilosc_w_komplecie > 1 &&
        returnData.value.typZwrotu === 'czesc';

    try {
        const payload = {
            stan_po_zwrocie: returnStatus.value,
            pracownik_zwracajacy_id: returnPracownikId.value
        };

        // Dodaj info o częściowym zwrocie
        if (isPartialReturn) {
            payload.czesciowy_zwrot = true;
            payload.ilosc_sztuk = returnData.value.iloscSztuk;
        }

        // Dodaj dane karty uszkodzenia jeśli są
        if (kartaData) {
            payload.karta_uszkodzenia = kartaData;
        }

        await axios.post(`${API_URL}/historia/${usageToReturnId.value}/zwrot/`, payload);

        returnModalVisible.value = false;
        await fetchUsages();
    } catch (error) {
        console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
        alert(error.response?.data?.error || "Wystąpił błąd podczas zwracania narzędzia.");
    }
};

const fetchUsages = async () => {
    isLoadingUsages.value = true;
    try {
        const res = await axios.get(`${API_URL}/historia/?w_uzyciu=true&light=true`);
        usagesInUse.value = przygotujUsages(res.data.results || res.data);
    } catch (error) {
        console.error("Błąd ładowania narzędzi w użyciu:", error.response?.data || error.message);
    } finally {
        isLoadingUsages.value = false;
    }
};

const fetchMachines = async () => {
    try {
        const res = await axios.get(`${API_URL}/maszyny/`);
        machines.value = res.data;
    } catch (error) {
        console.error("Błąd ładowania maszyn:", error.response?.data || error.message);
    }
};

// Pracownicy — ładowani leniwie (potrzebni wyłącznie w modalu zwrotu).
// Jedno zapytanie na sesję strony; równoległe wywołania współdzielą to samo żądanie.
let pracownicyPromise = null;
const ensurePracownicy = () => {
    if (!pracownicyPromise) {
        pracownicyPromise = axios.get(`${API_URL}/pracownicy/`)
            .then(res => {
                // Dodaj fullName do pracowników dla dropdown
                // (...) = tylko karta (stara tabela, brak konta użytkownika)
                // Fallback: jeśli Pracownik.nazwisko/imie puste, użyj danych z User
                const pracownicyData = res.data.results || res.data;
                pracownicy.value = pracownicyData.map(p => {
                    const nazwisko = p.nazwisko || p.user?.last_name || '';
                    const imie = p.imie || p.user?.first_name || '';
                    return {
                        ...p,
                        fullName: p.user
                            ? `${nazwisko} ${imie}`.trim() || p.user.username
                            : `${nazwisko} ${imie} ...`.trim()
                    };
                });
            })
            .catch(error => {
                console.error("Błąd ładowania pracowników:", error.response?.data || error.message);
                pracownicyPromise = null;  // pozwól spróbować ponownie przy kolejnym zwrocie
            });
    }
    return pracownicyPromise;
};

// Niezależne zapytania — tabela renderuje się, gdy dotrą jej własne dane,
// bez czekania na listę maszyn (filtr) i pracowników (modal zwrotu).
const fetchData = () => {
    fetchUsages();
    fetchMachines();
};

onMounted(() => {
    fetchData();
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

/* User dropdown button */
.dropdown-wrapper {
    position: relative;
}

.user-dropdown-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    background-color: #dc3545;
    color: white;
    border: 1px solid #dc3545;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: background-color 0.2s;
}

.user-dropdown-btn:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

/* === TRYB PRODUKCJA - NAGŁÓWEK === */
.header-user-name-prod {
    flex: 1;
    text-align: center;
    color: #e9ecef;
    font-size: 1rem;
    font-weight: 500;
}

.btn-narzedzia-prod {
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
    text-decoration: none;
}

.btn-narzedzia-prod:hover {
    background-color: #138496;
    border-color: #117a8b;
    color: #fff;
}

.btn-exit-prod {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #dc3545;
    background-color: #dc3545;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}

.btn-exit-prod:hover {
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

/* === PANEL "W UŻYCIU" - STYL JAK PANEL NARZĘDZI W MAGAZYNIE === */
.usage-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    border: none;
    min-height: 0;
    overflow: hidden;
}

.panel-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffc107;
    white-space: nowrap;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
}

/* === NAGŁÓWEK "W UŻYCIU" - STYL JAK PANEL === */
.in-use-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 6px 6px 0 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    flex-shrink: 0;
}

.in-use-header .search-input {
    width: 180px;
}

.filter-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-row label {
    margin: 0;
    font-weight: 500;
    color: #dee2e6;
    white-space: nowrap;
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

/* Sticky header dla tabel */
:deep(.p-datatable-scrollable .p-datatable-thead) {
    position: sticky;
    top: 0;
    z-index: 1;
}

/* Wirtualny scroller wymaga wierszy o stałej wysokości (itemSize: 38) —
   stąd sztywna wysokość i brak zawijania w komórkach. */
.usage-datatable :deep(.p-datatable-tbody > tr) {
    height: 38px;
}

.usage-datatable :deep(.p-datatable-tbody > tr > td) {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
:deep(.field .p-inputnumber) {
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

/* === KARTA USZKODZENIA === */
.karta-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.karta-row .field {
    flex: 1;
    margin-bottom: 0;
}

.karta-numer {
    font-weight: bold !important;
    color: #ffc107 !important;
    background-color: #3d444d !important;
}

:deep(.karta-textarea.p-inputtextarea) {
    height: 76px !important;
    min-height: 76px !important;
    resize: none;
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

/* === UTILITY === */
.text-muted {
    color: #6c757d;
}

:deep(.date-time) {
    color: #7a8a9a;
}

.required-mark {
    color: #5a6570;
    font-size: 0.85em;
}

.hint-text {
    color: #888;
}

.ml-2 {
    margin-left: 8px;
}

.mr-2 {
    margin-right: 8px;
}
</style>

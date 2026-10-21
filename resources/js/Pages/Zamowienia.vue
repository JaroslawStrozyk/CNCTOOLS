<template>
    <div class="zamowienia-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">ZAMÓWIENIA</h2>
            <div class="header-buttons">
                <button class="btn btn-info" @click="openHelp" title="Pomoc — przewodnik po module">
                    <i class="pi pi-question-circle"></i> Pomoc
                </button>
                <button v-if="canGenerateOrders" class="btn btn-success" @click="generujAutomatyczne">
                    <i class="pi pi-sparkles"></i> Generuj nowe
                </button>
                <button v-if="!auth?.isMagazyn && draftZamowienia.length > 0" class="btn btn-success" @click="openApprovalModal">
                    <i class="pi pi-send"></i> Wyślij do zatwierdzenia
                </button>
                <button class="btn btn-primary" @click="goToMagazyn">
                    <i class="pi pi-building"></i> Magazyn
                </button>
                <button v-if="auth?.isLogistyka" class="btn btn-primary" @click="goToZakupy">
                    <i class="pi pi-truck"></i> Zakupy
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
            <div class="orders-panel">
                <div class="panel-header">
                    <h3 class="panel-title">Lista zamówień</h3>
                    <!-- Licznik zalegających + przełącznik filtra. Widoczny tylko gdy jest co pokazać;
                         po domknięciu wszystkich zamówień znika razem z filtrem. -->
                    <Button
                        v-if="zamowieniaDoDomkniecia.length > 0 || tylkoDoDomkniecia"
                        class="p-button-sm btn-do-domkniecia"
                        :class="{ 'filtr-aktywny': tylkoDoDomkniecia }"
                        icon="pi pi-exclamation-triangle"
                        :label="`${zamowieniaDoDomkniecia.length} do domknięcia`"
                        :title="tylkoDoDomkniecia ? 'Pokaż wszystkie zamówienia' : `Pokaż tylko zamówienia wiszące ponad ${DNI_DO_DOMKNIECIA} dni`"
                        @click="tylkoDoDomkniecia = !tylkoDoDomkniecia"
                    />
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="searchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable :value="sortedZamowienia" :loading="isLoading" :scrollable="true" scrollHeight="flex" dataKey="id" :rowClass="rowClass"
                        :paginator="true" :rows="pageSize" :rowsPerPageOptions="rowsPerPageOptions" :paginatorTemplate="paginatorTemplate">
                        <Column header="Numer">
                            <template #body="{ data }">
                                <i
                                    v-if="wymagaDomkniecia(data)"
                                    class="pi pi-exclamation-triangle ikona-domkniecia"
                                    :title="tytulDomkniecia(data)"
                                ></i>
                                <a href="#" @click.prevent="otworzZamowienie(data)" class="order-link">
                                    <strong>{{ data.numer }}</strong>
                                </a>
                                <Tag v-if="auth?.isLogistyka && data.nr_oferty_dostawcy" :value="data.nr_oferty_dostawcy" severity="info" class="ml-2" />
                            </template>
                        </Column>
                        <Column header="Dostawca">
                            <template #body="{ data }">
                                {{ data.dostawca?.nazwa_firmy || '-' }}
                            </template>
                        </Column>
                        <Column header="Data utworzenia">
                            <template #body="{ data }">
                                {{ formatDate(data.data_utworzenia) }}
                            </template>
                        </Column>
                        <Column header="Data wysłania">
                            <template #body="{ data }">
                                {{ data.data_wyslania ? formatDate(data.data_wyslania) : '-' }}
                            </template>
                        </Column>
                        <Column header="Status">
                            <template #body="{ data }">
                                <Tag :severity="getStatusSeverity(data.status)" :value="getStatusLabel(data.status)" :class="getStatusTagClass(data.status)" />
                            </template>
                        </Column>
                        <Column header="Pozycje" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                {{ data.pozycje?.length || 0 }}
                            </template>
                        </Column>
                        <Column header="Uwagi" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <Button v-if="data.uwagi" icon="pi pi-comment" class="p-button-text p-button-secondary p-button-sm" @click="showUwagi(data)" />
                            </template>
                        </Column>
                        <Column header="Akcje" style="width: 240px; text-align: center;">
                            <template #body="{ data }">
                                <div style="display: flex; gap: 4px; justify-content: center; flex-wrap: nowrap;">
                                    <Button v-if="data.status === 'verified'" icon="pi pi-envelope" class="p-button-success p-button-sm" @click="openEmailConfirmModal(data)" title="Wyślij e-mail do dostawcy" />
                                    <Button v-if="data.status === 'pending_approval'" icon="pi pi-check" class="p-button-success p-button-sm" @click="zatwierdzZamowienie(data)" title="Zatwierdź zamówienie" />
                                    <Button v-if="data.status === 'pending_approval'" icon="pi pi-undo" class="p-button-secondary p-button-sm" @click="cofnijDoRoboczej(data)" title="Cofnij do wersji roboczej" />
                                    <Button v-if="data.status === 'sent'" icon="pi pi-box" class="p-button-info p-button-sm" @click="otworzZamowienie(data)" title="Rozpocznij realizację" />
                                    <Button v-if="data.status === 'sent' && !isMagazynierView" icon="pi pi-undo" class="p-button-warning p-button-sm" @click="openCofnijDoZatwierdzoneModal(data)" title="Cofnij do 'Zatwierdzone' (zmiana dostawcy)" />
                                    <Button v-if="data.status === 'partially_received'" icon="pi pi-box" class="p-button-warning p-button-sm" @click="otworzZamowienie(data)" title="Kontynuuj realizację" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-truck" class="p-button-help p-button-sm" @click="openZmienDostawceModal(data)" title="Zmień dostawcę" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="otworzZamowienie(data)" title="Edytuj pozycje" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteConfirmModal(data)" title="Usuń" />
                                </div>
                            </template>
                        </Column>
                        <template #empty>
                            <div class="empty-state">Brak zamówień</div>
                        </template>
                    </DataTable>
                </div>
            </div>
        </main>

        <!-- Modal: Zamówienie (szczegóły + edycja + realizacja) -->
        <ZamowienieModal
            v-model:visible="zamowienieDetaleVisible"
            :zamowienieId="zamowienieDetaleId"
            :auth="auth"
            :formatDate="formatDate"
            :getStatusLabel="getStatusLabel"
            :getStatusSeverity="getStatusSeverity"
            :getStatusTagClass="getStatusTagClass"
            @zmieniono="fetchInitialData"
            @wynik="pokazWynikRealizacji"
        />

        <!-- Modal: Dodaj/Edytuj zamówienie -->
        <Dialog v-model:visible="zamowienieModalVisible" :header="zamowienieModal.title" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <Message v-if="zamowienieModal.errorMessage" severity="error" :closable="false">{{ zamowienieModal.errorMessage }}</Message>
                <div class="field">
                    <label>Numer zamówienia</label>
                    <InputText v-model="zamowienieModal.currentItem.numer" />
                </div>
                <div class="field">
                    <label>Dostawca</label>
                    <Dropdown
                        v-model="zamowienieModal.currentItem.dostawca_id"
                        :options="dostawcyOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Wybierz dostawcę --"
                    />
                </div>
                <div v-if="auth?.isLogistyka" class="field">
                    <label>Nr oferty dostawcy</label>
                    <InputText v-model="zamowienieModal.currentItem.nr_oferty_dostawcy" />
                </div>
                <div class="field">
                    <label>Uwagi</label>
                    <Textarea v-model="zamowienieModal.currentItem.uwagi" rows="3" />
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="zamowienieModalVisible = false" />
                <Button label="Zapisz" icon="pi pi-check" @click="saveZamowienie" :loading="isSaving" />
            </template>
        </Dialog>

        <!-- Modal: Uwagi -->
        <Dialog v-model:visible="uwagiModalVisible" header="Uwagi do zamówienia" :modal="true" :style="{ width: '450px' }">
            <p><strong>Numer zamówienia:</strong> {{ selectedUwagiZamowienie?.numer }}</p>
            <Divider />
            <p>{{ selectedUwagiZamowienie?.uwagi }}</p>
            <template #footer>
                <Button label="Zamknij" @click="uwagiModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie wysyłki email -->
        <Dialog v-model:visible="emailConfirmModalVisible" header="Potwierdzenie wysyłki e-mail" :modal="true" :style="{ width: '450px' }">
            <Message v-if="zamowieniaTestowe" severity="warn" :closable="false" style="margin-bottom: 15px;">
                <strong>TRYB TESTOWY</strong> — email zostanie wysłany na adres testowy zamiast do dostawcy!
            </Message>
            <p style="margin-bottom: 15px;">Czy na pewno chcesz wysłać to zamówienie e-mailem {{ zamowieniaTestowe ? '(testowo)' : 'do dostawcy' }}?</p>
            <Message severity="info" :closable="false">
                <strong>Numer zamówienia:</strong> {{ selectedEmailZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedEmailZamowienie?.dostawca?.nazwa_firmy }}<br>
                <strong>Email:</strong> {{ zamowieniaTestowe ? emailTestAddress + ' (testowy)' : (selectedEmailZamowienie?.email_docelowy || 'brak') }}
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="emailConfirmModalVisible = false" />
                <Button label="Wyślij e-mail" icon="pi pi-send" class="p-button-success" @click="confirmWyslijEmail" :loading="isSendingEmail" />
            </template>
        </Dialog>

        <!-- Modal: Wynik wysyłki email -->
        <Dialog v-model:visible="emailResultModalVisible" :header="emailResult.success ? 'Sukces' : 'Błąd'" :modal="true" :style="{ width: '400px' }">
            <Message :severity="emailResult.success ? 'success' : 'error'" :closable="false">{{ emailResult.message }}</Message>
            <template #footer>
                <Button label="Zamknij" @click="emailResultModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Zmiana dostawcy -->
        <Dialog v-model:visible="zmienDostawceModalVisible" header="Zmiana dostawcy" :modal="true" :style="{ width: '520px' }">
            <div v-if="selectedZmienDostawceZamowienie" class="p-fluid">
                <p>
                    <strong>Zamówienie:</strong> {{ selectedZmienDostawceZamowienie.numer }}<br>
                    <strong>Aktualny dostawca:</strong> {{ selectedZmienDostawceZamowienie.dostawca?.nazwa_firmy }}
                </p>
                <div class="field">
                    <label>Nowy dostawca</label>
                    <Dropdown
                        v-model="nowyDostawcaId"
                        :options="dostawcyZmianaOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Wybierz dostawcę"
                        filter
                    />
                </div>
                <Message v-if="nowyDostawcaInfo" severity="info" :closable="false">
                    <strong>Email nowego dostawcy:</strong> {{ nowyDostawcaInfo.email || '(brak — uzupełnij w kartotece)' }}<br>
                    Email zamówienia zostanie zaktualizowany do tego adresu.
                </Message>
                <Message v-if="zmienDostawceError" severity="error" :closable="false">{{ zmienDostawceError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="zmienDostawceModalVisible = false" />
                <Button label="Zmień dostawcę" icon="pi pi-check" class="p-button-success" @click="confirmZmienDostawce" :loading="isZmianaDostawcy" :disabled="!nowyDostawcaId" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie cofnięcia z "Wysłane" do "Zatwierdzone" -->
        <Dialog v-model:visible="cofnijDoZatwierdzoneModalVisible" header="Cofnięcie do 'Zatwierdzone'" :modal="true" :style="{ width: '500px' }">
            <p>Czy na pewno chcesz cofnąć zamówienie do statusu <strong>„Zatwierdzone”</strong>?</p>
            <Message severity="warn" :closable="false">
                <strong>Numer:</strong> {{ selectedCofnijZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedCofnijZamowienie?.dostawca?.nazwa_firmy }}<br>
                Po cofnięciu będziesz mógł zmienić dostawcę / pozycje i wysłać zamówienie ponownie.<br>
                Data wysłania zostanie zresetowana.
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="cofnijDoZatwierdzoneModalVisible = false" />
                <Button label="Cofnij do 'Zatwierdzone'" icon="pi pi-undo" class="p-button-warning" @click="confirmCofnijDoZatwierdzone" :loading="isCofajacDoZatwierdzone" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie usunięcia -->
        <Dialog v-model:visible="deleteConfirmModalVisible" header="Potwierdzenie usunięcia" :modal="true" :style="{ width: '450px' }">
            <p>Czy na pewno chcesz usunąć to zamówienie?</p>
            <Message severity="error" :closable="false">
                <strong>Numer zamówienia:</strong> {{ selectedDeleteZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedDeleteZamowienie?.dostawca?.nazwa_firmy }}<br>
                <strong>Uwaga:</strong> Ta operacja jest nieodwracalna!
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteConfirmModalVisible = false" />
                <Button label="Usuń zamówienie" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteZamowienie" :loading="isDeleting" />
            </template>
        </Dialog>

        <!-- Modal: Wynik realizacji -->
        <Dialog v-model:visible="realizacjaResultModalVisible" :header="realizacjaResult.success ? 'Przyjęcie potwierdzone' : 'Błąd'" :modal="true" :style="{ width: '650px' }">
            <Message :severity="realizacjaResult.success ? 'success' : 'error'" :closable="false">{{ realizacjaResult.message }}</Message>
            <DataTable v-if="realizacjaResult.success && realizacjaResult.egzemplarze.length > 0" :value="realizacjaResult.egzemplarze" class="p-datatable-sm mt-3">
                <Column field="narzedzie" header="Narzędzie" />
                <Column header="Ilość" style="width: 80px; text-align: center;">
                    <template #body="{ data }"><strong>{{ data.ilosc }}</strong></template>
                </Column>
                <Column field="lokalizacja" header="Lokalizacja" style="width: 150px;" />
            </DataTable>
            <template #footer>
                <Button label="Zamknij" @click="realizacjaResultModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Wyślij do zatwierdzenia -->
        <Dialog v-model:visible="approvalModalVisible" header="Wyślij zamówienia do zatwierdzenia" :modal="true" :style="{ width: '750px' }">
            <Message severity="info" :closable="false" style="margin-bottom: 15px;">
                Wybierz zamówienia, które chcesz wysłać do szefa do zatwierdzenia. Zostanie wysłany zbiorczy email z listą wszystkich pozycji i sumą.
            </Message>
            <Message v-if="!emailSzef" severity="warn" :closable="false" style="margin-bottom: 15px;">
                <strong>Brak adresu email szefa!</strong> Skonfiguruj go w Ustawienia → Poczta (EMAIL_SZEF).
            </Message>
            <DataTable :value="draftZamowienia" v-model:selection="selectedApprovalZamowienia" dataKey="id" class="p-datatable-sm">
                <Column selectionMode="multiple" style="width: 50px;" />
                <Column field="numer" header="Numer" style="width: 140px;">
                    <template #body="{ data }"><strong>{{ data.numer }}</strong></template>
                </Column>
                <Column header="Dostawca">
                    <template #body="{ data }">{{ data.dostawca?.nazwa_firmy || '-' }}</template>
                </Column>
                <Column header="Pozycji" style="width: 80px; text-align: center;">
                    <template #body="{ data }">{{ data.pozycje?.length || 0 }}</template>
                </Column>
                <Column header="Wartość" style="width: 120px; text-align: right;">
                    <template #body="{ data }"><strong>{{ data.wartosc_zamowienia }} zł</strong></template>
                </Column>
            </DataTable>
            <div v-if="selectedApprovalZamowienia.length > 0" class="approval-summary">
                <strong>Wybrano: {{ selectedApprovalZamowienia.length }} zamówień</strong>
                <span class="approval-total">Łączna wartość: <strong>{{ approvalTotal }} zł</strong></span>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="approvalModalVisible = false" />
                <Button label="Wyślij do zatwierdzenia" icon="pi pi-send" class="p-button-warning" @click="confirmSendApproval" :loading="isSendingApproval" :disabled="selectedApprovalZamowienia.length === 0 || !emailSzef" />
            </template>
        </Dialog>

        <!-- Modal: Wynik wysyłki do zatwierdzenia -->
        <Dialog v-model:visible="approvalResultModalVisible" :header="approvalResult.success ? 'Sukces' : 'Błąd'" :modal="true" :style="{ width: '400px' }">
            <Message :severity="approvalResult.success ? 'success' : 'error'" :closable="false">{{ approvalResult.message }}</Message>
            <template #footer>
                <Button label="Zamknij" @click="approvalResultModalVisible = false" />
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
                        <tr><td class="label"><i class="pi pi-code"></i> Wersja:</td><td><strong>{{ infoProgram.WERSJA }}</strong></td></tr>
                        <tr><td class="label"><i class="pi pi-calendar"></i> Data modyfikacji:</td><td>{{ infoProgram.MODYFIKACJA }}</td></tr>
                        <tr><td class="label"><i class="pi pi-building"></i> Firma:</td><td>{{ infoProgram.FIRMA }}</td></tr>
                        <tr><td class="label"><i class="pi pi-user"></i> Autor:</td><td>{{ infoProgram.AUTOR }}</td></tr>
                        <tr><td class="label"><i class="pi pi-envelope"></i> Email:</td><td><a :href="infoProgram.EMAIL">{{ infoProgram.NEMAIL }}</a></td></tr>
                        <tr><td class="label"><i class="pi pi-phone"></i> Telefon:</td><td>{{ infoProgram.TEL }}</td></tr>
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

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Menu from 'primevue/menu';
import Divider from 'primevue/divider';
import { usePaginacja } from '../paginacja';
import ZamowienieModal from '../Components/ZamowienieModal.vue';

const { pageSize, rowsPerPageOptions, paginatorTemplate } = usePaginacja();

const API_URL = '/api';

const props = defineProps({
    auth: { type: Object, default: () => ({ user: { firstName: '', lastName: '' }, isLogistyka: false }) },
    urls: { type: Object, default: () => ({ ustawienia: '/ustawienia/', realizacja: '/realizacja/', magazyn: '/magazyn-inertia/', zakupy: '/zakupy-inertia/', logout: '/logout/' }) },
    infoProgram: { type: Object, default: () => ({}) },
    canGenerateOrders: { type: Boolean, default: false }
});

// Data
const zamowienia = ref([]);
const isLoading = ref(false);
const dostawcy = ref([]);
const selectedUwagiZamowienie = ref(null);
const selectedEmailZamowienie = ref(null);
const selectedDeleteZamowienie = ref(null);

const isSaving = ref(false);
const isSendingEmail = ref(false);
const isDeleting = ref(false);
const isSendingApproval = ref(false);

const emailResult = ref({ success: false, message: '' });
const emailSzef = ref('');
const realizacjaResult = ref({ success: false, message: '', egzemplarze: [] });
const zamowieniaTestowe = ref(false);
const emailTestAddress = ref('');

// Modals
const zamowienieModalVisible = ref(false);
const uwagiModalVisible = ref(false);
const emailConfirmModalVisible = ref(false);
const emailResultModalVisible = ref(false);
const deleteConfirmModalVisible = ref(false);
const realizacjaResultModalVisible = ref(false);
const aboutModalVisible = ref(false);
const approvalModalVisible = ref(false);
const approvalResultModalVisible = ref(false);
const approvalResult = ref({ success: false, message: '' });
const selectedApprovalZamowienia = ref([]);

const zamowienieModal = ref({ title: '', mode: 'add', currentItem: {}, errorMessage: '' });

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
    { label: 'Ustawienia', icon: 'pi pi-cog', command: () => { window.location.href = props.urls.ustawienia + '?from=zakupy'; } },
    { separator: true },
    { label: 'O programie', icon: 'pi pi-info-circle', command: () => { aboutModalVisible.value = true; } },
    { separator: true },
    { label: 'Wyjście', icon: 'pi pi-sign-out', command: () => { window.location.href = props.urls.logout; } }
]);

// Pomoc — otwiera w nowym oknie typu popup (działa też w trybie PWA)
const openHelp = () => {
    const url = props.urls.pomoc_zamowienia || '/pomoc/zamowienia/';
    const features = 'noopener,noreferrer,width=1100,height=860,resizable=yes,scrollbars=yes';
    window.open(url, 'pomoc-zamowienia', features);
};

// Wyszukiwanie
const searchQuery = ref('');

// Nawigacja
const goToMagazyn = () => { window.location.href = props.urls.magazyn; };
const goToZakupy = () => { window.location.href = props.urls.zakupy; };

// Computed
const dostawcyOptions = computed(() => [
    { label: '-- Wybierz dostawcę --', value: null },
    ...dostawcy.value.map(d => ({ label: d.nazwa_firmy, value: d.id }))
]);

const statusLabels = {
    'draft': 'Wersja robocza',
    'pending_approval': 'Oczekuje na zatwierdzenie',
    'verified': 'Zatwierdzone',
    'sent': 'Wysłane',
    'partially_received': 'Częściowo odebrane',
    'completed': 'Zrealizowane'
};

// Methods
const toggleUserMenu = (event) => userMenu.value.toggle(event);

const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d} ${h}:${min}`;
};

const getStatusLabel = (status) => statusLabels[status] || status;

const getStatusSeverity = (status) => {
    const map = { 'draft': 'secondary', 'pending_approval': 'warning', 'verified': 'info', 'sent': 'primary', 'partially_received': 'warning', 'completed': 'success' };
    return map[status] || 'secondary';
};

// Status 'partially_received' — Tag musi mieć identyczny kolor jak p-button-warning (pomarańczowy).
// Klasa .tag-status-orange w dark-theme.css ma !important żeby pokonać override .p-tag-warning
const getStatusTagClass = (status) => {
    return status === 'partially_received' ? 'tag-status-orange' : '';
};

// Wspólny modal zamówienia — klik w numer, „Edytuj pozycje” i „Realizacja” otwierają to samo okno
const zamowienieDetaleVisible = ref(false);
const zamowienieDetaleId = ref(null);
const otworzZamowienie = (zamowienie) => {
    zamowienieDetaleId.value = zamowienie.id;
    zamowienieDetaleVisible.value = true;
};
const pokazWynikRealizacji = (wynik) => {
    realizacjaResult.value = wynik;
    realizacjaResultModalVisible.value = true;
};

const showUwagi = (zamowienie) => {
    selectedUwagiZamowienie.value = zamowienie;
    uwagiModalVisible.value = true;
};

const openEmailConfirmModal = (zamowienie) => {
    selectedEmailZamowienie.value = zamowienie;
    emailConfirmModalVisible.value = true;
};

const confirmWyslijEmail = async () => {
    isSendingEmail.value = true;
    try {
        await axios.post(`${API_URL}/zamowienia/${selectedEmailZamowienie.value.id}/wyslij-email/`);
        emailConfirmModalVisible.value = false;
        emailResult.value = { success: true, message: 'Email został wysłany pomyślnie!' };
        emailResultModalVisible.value = true;
        await fetchZamowienia();
    } catch (error) {
        emailConfirmModalVisible.value = false;
        emailResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd podczas wysyłki email' };
        emailResultModalVisible.value = true;
    } finally {
        isSendingEmail.value = false;
    }
};

const openDeleteConfirmModal = (zamowienie) => {
    selectedDeleteZamowienie.value = zamowienie;
    deleteConfirmModalVisible.value = true;
};

const confirmDeleteZamowienie = async () => {
    isDeleting.value = true;
    try {
        await axios.delete(`${API_URL}/zamowienia/${selectedDeleteZamowienie.value.id}/`);
        deleteConfirmModalVisible.value = false;
        await fetchZamowienia();
    } catch (error) {
        deleteConfirmModalVisible.value = false;
        emailResult.value = { success: false, message: 'Wystąpił błąd: ' + (error.response?.data?.error || error.message) };
        emailResultModalVisible.value = true;
    } finally {
        isDeleting.value = false;
        selectedDeleteZamowienie.value = null;
    }
};

const openZamowienieModal = (mode, zamowienie = null) => {
    zamowienieModal.value.mode = mode;
    zamowienieModal.value.errorMessage = '';
    if (mode === 'add') {
        zamowienieModal.value.title = 'Nowe zamówienie';
        zamowienieModal.value.currentItem = { numer: generateZamowienieNumer(), dostawca_id: null, nr_oferty_dostawcy: '', uwagi: '' };
    } else {
        zamowienieModal.value.title = 'Edytuj zamówienie';
        zamowienieModal.value.currentItem = { ...zamowienie, dostawca_id: zamowienie.dostawca?.id };
    }
    zamowienieModalVisible.value = true;
};

const generateZamowienieNumer = () => {
    const date = new Date();
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const r = Math.floor(Math.random() * 1000);
    return `ZAM/${y}/${m}/${r}`;
};

const saveZamowienie = async () => {
    isSaving.value = true;
    zamowienieModal.value.errorMessage = '';

    if (!zamowienieModal.value.currentItem.numer || !zamowienieModal.value.currentItem.dostawca_id) {
        zamowienieModal.value.errorMessage = 'Numer zamówienia i dostawca są wymagane.';
        isSaving.value = false;
        return;
    }

    const method = zamowienieModal.value.mode === 'add' ? 'post' : 'patch';
    const url = zamowienieModal.value.mode === 'add' ? `${API_URL}/zamowienia/` : `${API_URL}/zamowienia/${zamowienieModal.value.currentItem.id}/`;

    try {
        await axios({ method, url, data: zamowienieModal.value.currentItem });
        zamowienieModalVisible.value = false;
        await fetchInitialData();
    } catch (error) {
        zamowienieModal.value.errorMessage = 'Błąd zapisu: ' + (error.response?.data?.detail || error.message);
    } finally {
        isSaving.value = false;
    }
};

// Widok "czystego" magazyniera (magazyn bez logistyki) — ograniczona lista i akcje
const isMagazynierView = computed(() => props.auth?.isMagazyn && !props.auth?.isLogistyka);

// --- Zamówienia "do domknięcia" ---------------------------------------------
// Zamówienie wysłane do dostawcy, które po DNI_DO_DOMKNIECIA dniach nadal nie jest
// w całości odebrane, najczęściej już nie zostanie zrealizowane — dostawca nie
// dosłał resztówki. Taki rekord wisi na liście w nieskończoność, bo status
// zmienia się na 'completed' dopiero po przyjęciu WSZYSTKICH pozycji.
// Sygnalizujemy go, żeby logistyk odpisał brakujące pozycje przy realizacji
// (pozycja wraca wtedy do generatora, a zamówienie się domyka).
// Liczymy od daty UTWORZENIA — data wysłania bywa o kilkanaście dni późniejsza,
// a zaleganie zaczyna się w momencie wygenerowania zamówienia.
const DNI_DO_DOMKNIECIA = 30;
const STATUSY_DO_DOMKNIECIA = ['sent', 'partially_received'];

const wiekZamowieniaDni = (z) => {
    if (!z?.data_utworzenia) return 0;
    const utworzone = new Date(z.data_utworzenia);
    if (Number.isNaN(utworzone.getTime())) return 0;
    return Math.floor((Date.now() - utworzone.getTime()) / 86400000);
};

const wymagaDomkniecia = (z) =>
    STATUSY_DO_DOMKNIECIA.includes(z?.status) && wiekZamowieniaDni(z) > DNI_DO_DOMKNIECIA;

const tytulDomkniecia = (z) =>
    `Wisi ${wiekZamowieniaDni(z)} dni — rozważ odpisanie brakujących pozycji przy realizacji`;

// Przełącznik "pokaż tylko do domknięcia" (filtr listy)
const tylkoDoDomkniecia = ref(false);

// Klasa wiersza — podświetlenie zalegających zamówień
const rowClass = (z) => (wymagaDomkniecia(z) ? 'row-do-domkniecia' : '');

// Computed — filtrowanie po wyszukiwarce (Numer, Dostawca, Data utworzenia, Data wysłania)
const filteredZamowienia = computed(() => {
    // Magazynier widzi zamówienia 'sent' (do realizacji), 'partially_received'
    // (częściowo odebrane — realizacja w toku) i 'completed' (historia)
    let base = isMagazynierView.value
        ? zamowienia.value.filter(z => ['sent', 'partially_received', 'completed'].includes(z.status))
        : zamowienia.value;
    if (tylkoDoDomkniecia.value) base = base.filter(wymagaDomkniecia);
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return base;
    return base.filter(z => {
        const numer = (z.numer || '').toLowerCase();
        const dostawca = (z.dostawca?.nazwa_firmy || '').toLowerCase();
        const dataUtw = z.data_utworzenia ? formatDate(z.data_utworzenia).toLowerCase() : '';
        const dataWysl = z.data_wyslania ? formatDate(z.data_wyslania).toLowerCase() : '';
        return numer.includes(q) || dostawca.includes(q) || dataUtw.includes(q) || dataWysl.includes(q);
    });
});

// Computed — sortowanie listy: niezrealizowane/w trakcie zawsze na górze, w obrębie grupy numer malejąco
const sortedZamowienia = computed(() => {
    return [...filteredZamowienia.value].sort((a, b) => {
        const aDone = a.status === 'completed' ? 1 : 0;
        const bDone = b.status === 'completed' ? 1 : 0;
        if (aDone !== bDone) return aDone - bDone;
        return (b.numer || '').localeCompare(a.numer || '');
    });
});

// Licznik zalegających — liczony z listy widocznej dla danej roli, ale PRZED filtrem
// "tylko do domknięcia" i wyszukiwarką, żeby nie zerował się przy zawężaniu widoku.
const zamowieniaDoDomkniecia = computed(() => {
    const base = isMagazynierView.value
        ? zamowienia.value.filter(z => ['sent', 'partially_received', 'completed'].includes(z.status))
        : zamowienia.value;
    return base.filter(wymagaDomkniecia);
});

// Computed — filtrowane zamówienia
const draftZamowienia = computed(() => zamowienia.value.filter(z => z.status === 'draft'));
const approvalTotal = computed(() => {
    return selectedApprovalZamowienia.value.reduce((sum, z) => sum + parseFloat(z.wartosc_zamowienia || 0), 0).toFixed(2);
});

// Zatwierdzanie
const openApprovalModal = () => {
    selectedApprovalZamowienia.value = [...draftZamowienia.value];
    approvalModalVisible.value = true;
};

const confirmSendApproval = async () => {
    isSendingApproval.value = true;
    try {
        const ids = selectedApprovalZamowienia.value.map(z => z.id);
        const res = await axios.post(`${API_URL}/zamowienia/wyslij-do-zatwierdzenia/`, { zamowienie_ids: ids });
        approvalModalVisible.value = false;
        approvalResult.value = { success: true, message: res.data.message };
        approvalResultModalVisible.value = true;
        await fetchInitialData();
    } catch (error) {
        approvalModalVisible.value = false;
        approvalResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd' };
        approvalResultModalVisible.value = true;
    } finally {
        isSendingApproval.value = false;
    }
};

const zatwierdzZamowienie = async (zamowienie) => {
    try {
        const res = await axios.post(`${API_URL}/zamowienia/zatwierdz/`, { zamowienie_ids: [zamowienie.id] });
        approvalResult.value = { success: true, message: res.data.message };
        approvalResultModalVisible.value = true;
        await fetchInitialData();
    } catch (error) {
        approvalResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd' };
        approvalResultModalVisible.value = true;
    }
};

const cofnijDoRoboczej = async (zamowienie) => {
    try {
        await axios.post(`${API_URL}/zamowienia/cofnij-do-roboczej/`, { zamowienie_id: zamowienie.id });
        await fetchInitialData();
    } catch (error) {
        alert('Błąd: ' + (error.response?.data?.error || error.message));
    }
};

// Zmiana dostawcy zamówienia
const zmienDostawceModalVisible = ref(false);
const selectedZmienDostawceZamowienie = ref(null);
const nowyDostawcaId = ref(null);
const isZmianaDostawcy = ref(false);
const zmienDostawceError = ref('');

const dostawcyZmianaOptions = computed(() => {
    const aktualnyId = selectedZmienDostawceZamowienie.value?.dostawca?.id;
    return dostawcy.value
        .filter(d => d.id !== aktualnyId)
        .map(d => ({ label: d.nazwa_firmy + (d.email ? ` — ${d.email}` : ''), value: d.id }));
});

const nowyDostawcaInfo = computed(() => {
    if (!nowyDostawcaId.value) return null;
    return dostawcy.value.find(d => d.id === nowyDostawcaId.value) || null;
});

const openZmienDostawceModal = (zamowienie) => {
    selectedZmienDostawceZamowienie.value = zamowienie;
    nowyDostawcaId.value = null;
    zmienDostawceError.value = '';
    zmienDostawceModalVisible.value = true;
};

const confirmZmienDostawce = async () => {
    if (!selectedZmienDostawceZamowienie.value || !nowyDostawcaId.value) return;
    isZmianaDostawcy.value = true;
    zmienDostawceError.value = '';
    try {
        await axios.post(`${API_URL}/zamowienia/zmien-dostawce/`, {
            zamowienie_id: selectedZmienDostawceZamowienie.value.id,
            dostawca_id: nowyDostawcaId.value,
        });
        zmienDostawceModalVisible.value = false;
        selectedZmienDostawceZamowienie.value = null;
        nowyDostawcaId.value = null;
        await fetchInitialData();
    } catch (error) {
        zmienDostawceError.value = error.response?.data?.error || error.message;
    } finally {
        isZmianaDostawcy.value = false;
    }
};

// Cofnięcie z "Wysłane" do "Zatwierdzone" — dla przypadku zmiany dostawcy
const cofnijDoZatwierdzoneModalVisible = ref(false);
const selectedCofnijZamowienie = ref(null);
const isCofajacDoZatwierdzone = ref(false);

const openCofnijDoZatwierdzoneModal = (zamowienie) => {
    selectedCofnijZamowienie.value = zamowienie;
    cofnijDoZatwierdzoneModalVisible.value = true;
};

const confirmCofnijDoZatwierdzone = async () => {
    if (!selectedCofnijZamowienie.value) return;
    isCofajacDoZatwierdzone.value = true;
    try {
        await axios.post(`${API_URL}/zamowienia/cofnij-do-zatwierdzone/`, {
            zamowienie_id: selectedCofnijZamowienie.value.id
        });
        cofnijDoZatwierdzoneModalVisible.value = false;
        selectedCofnijZamowienie.value = null;
        await fetchInitialData();
    } catch (error) {
        alert('Błąd: ' + (error.response?.data?.error || error.message));
    } finally {
        isCofajacDoZatwierdzone.value = false;
    }
};
const generujAutomatyczne = () => {
    window.location.href = props.urls.generator || '/generator/';
};

const fetchZamowienia = async () => {
    try {
        const res = await axios.get(`${API_URL}/zamowienia/`);
        zamowienia.value = res.data.results || res.data;
    } catch (error) {
        console.error("Błąd ładowania zamówień:", error);
    }
};

const fetchInitialData = async () => {
    isLoading.value = true;
    try {
        const [zamRes, dosRes, emailRes] = await Promise.all([
            axios.get(`${API_URL}/zamowienia/`),
            axios.get(`${API_URL}/dostawcy/`),
            axios.get('/api/email/config/')
        ]);
        zamowienia.value = zamRes.data.results || zamRes.data;
        dostawcy.value = dosRes.data;
        zamowieniaTestowe.value = emailRes.data.zamowienia_testowe || false;
        emailTestAddress.value = emailRes.data.email_test_address || '';
        emailSzef.value = emailRes.data.email_szef || '';
    } catch (error) {
        console.error("Błąd ładowania danych:", error);
    } finally {
        isLoading.value = false;
    }
};

onMounted(() => fetchInitialData());
</script>

<style scoped>
.zamowienia-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
}

.app-main {
    flex: 1;
    padding: 16px 24px;
    min-height: 0;
}

.orders-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.approval-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    margin-top: 12px;
    background: rgba(253, 126, 20, 0.1);
    border-radius: 6px;
    border: 1px solid rgba(253, 126, 20, 0.3);
}

.approval-total {
    font-size: 1.1em;
    color: #fd7e14;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
    background: #212529;
}

.order-link {
    color: #ffc107;
    text-decoration: none;
}

.order-link:hover {
    text-decoration: underline;
    color: #ffda6a;
}

.about-content { text-align: center; }
.about-header { margin-bottom: 24px; }
.about-logo { width: 80px; height: 80px; }
.about-table { width: 100%; text-align: left; }
.about-table td { padding: 8px 0; color: var(--dark-text-primary); }
.about-table .label { text-align: right; color: var(--dark-text-muted); padding-right: 16px; width: 40%; }
.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }

.text-muted { color: #868e96; }

/* --- Zamówienia zalegające ("do domknięcia", ponad 30 dni) ---------------- */
/* Bursztyn, nie czerwień — to sygnał "zrób z tym porządek", nie błąd krytyczny.
   Podświetlenie wiersza musi mieć !important, bo PrimeVue maluje tło wierszy
   własnymi regułami o wyższej specyficzności (także na hover i w paskach zebra). */
:deep(.row-do-domkniecia > td) {
    background-color: rgba(217, 119, 6, 0.14) !important;
}

:deep(.row-do-domkniecia:hover > td) {
    background-color: rgba(217, 119, 6, 0.22) !important;
}

.ikona-domkniecia {
    color: #d97706;
    margin-right: 6px;
    cursor: help;
}

/* margin-left:auto dosuwa przycisk do wyszukiwarki po prawej — bez tego
   .panel-header (justify-content: space-between) rozrzuciłby trzy elementy równomiernie */
.btn-do-domkniecia {
    margin-left: auto;
    margin-right: 12px;
    white-space: nowrap;
    background: transparent;
    border: 1px solid rgba(217, 119, 6, 0.6);
    color: #d97706;
}

.btn-do-domkniecia:hover {
    background: rgba(217, 119, 6, 0.15);
    border-color: #d97706;
    color: #d97706;
}

/* Filtr włączony — pełne wypełnienie, żeby było widać, że lista jest zawężona */
.btn-do-domkniecia.filtr-aktywny {
    background: #d97706;
    border-color: #d97706;
    color: #fff;
}
</style>

<template>
    <div class="generator-app">
        <header class="app-header">
            <h2 class="header-title"><span class="yellow">Generator Zamówień</span></h2>
            <div class="header-buttons">
                <button class="btn btn-success" @click="zamowienieGotowe" style="margin-right: 50px;">
                    <i class="pi pi-check"></i> Zamówienie gotowe
                </button>
                <a :href="urls.zamowienia" class="btn btn-danger">
                    <i class="pi pi-sign-out"></i> Wyjście
                </a>
            </div>
        </header>

        <main class="app-main">
            <div class="generator-panel">
                <div class="panel-header">
                    <h3>Narzędzia do zamówienia</h3>
                    <span class="text-muted">Pozycji do zamówienia: <strong>{{ toolsToOrder.length }}</strong></span>
                    <Button icon="pi pi-plus" class="p-button-success p-button-sm btn-add-manual" @click="openAddModal" title="Dodaj ręcznie" />
                </div>
                <div class="panel-body">
                    <div v-if="isLoading" class="loading-spinner">
                        <ProgressSpinner />
                        <p>Ładowanie danych...</p>
                    </div>
                    <div v-else-if="toolsToOrder.length === 0" class="empty-state success">
                        <i class="pi pi-check-circle" style="font-size: 3rem; color: #198754; margin-right: 0.5rem;"></i>
                        <h5>Wszystkie narzędzia są na odpowiednim poziomie - Nie ma nic do zamówienia.</h5>
                    </div>
                    <DataTable v-else :value="toolsToOrder" :scrollable="true" scrollHeight="flex"
                               v-model:selection="selectedTools" dataKey="id">
                        <Column selectionMode="multiple" headerStyle="width: 3rem" :exportable="false" />
                        <Column field="dostawca_nazwa" header="Dostawca">
                            <template #body="{ data }">{{ data.dostawca_nazwa || '-' }}</template>
                        </Column>
                        <Column field="element" header="Element" />
                        <Column field="numer_katalogowy" header="Nr Katalogowy">
                            <template #body="{ data }">{{ data.numer_katalogowy || '-' }}</template>
                        </Column>
                        <Column header="Ilość" style="width: 80px;">
                            <template #body="{ data }"><strong>{{ data.ilosc_do_zamowienia }}</strong></template>
                        </Column>
                        <Column field="rodzaj" header="Rodzaj" />
                        <Column header="Cena jednostkowa" style="width: 130px;">
                            <template #body="{ data }">{{ data.cena_jednostkowa ? data.cena_jednostkowa.toFixed(2) + ' zł' : '-' }}</template>
                        </Column>
                        <Column header="Źródło" style="width: 160px;">
                            <template #body="{ data }">
                                <span :class="'zrodlo-' + data.zrodlo">{{ data.zrodlo_label || '-' }}</span>
                            </template>
                        </Column>
                        <Column style="width: 170px; text-align: center;">
                            <template #header>
                                <Button icon="pi pi-trash" label="Kas. seryjne"
                                        class="p-button-danger p-button-sm btn-bulk-delete"
                                        :disabled="selectedTools.length === 0"
                                        @click="openBulkDeleteModal" title="Usuń zaznaczone pozycje" />
                            </template>
                            <template #body="{ data }">
                                <div style="display: flex; gap: 4px; justify-content: center;">
                                    <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="openEditModal(data)" title="Edytuj" />
                                    <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteModal(data)" title="Usuń" />
                                </div>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Nieprzypisane pozycje zapotrzebowań -->
            <div v-if="nieprzypisanePozycje.length > 0" class="nieprzypisane-panel">
                <div class="panel-header" style="background: linear-gradient(to bottom, #8B4513, #5C2D0E);">
                    <h3 style="margin: 0; color: #ffc107;">
                        Pozycje zapotrzebowań bez powiązanego narzędzia
                        <span style="font-size: 0.8rem; font-weight: 400; color: #adb5bd; margin-left: 10px;">(wymagają ręcznego przetworzenia)</span>
                    </h3>
                </div>
                <div class="panel-body" style="max-height: 300px; overflow: auto;">
                    <DataTable :value="nieprzypisanePozycje" class="p-datatable-sm">
                        <Column field="zapotrzebowanie_numer" header="Zapotrzebowanie" style="width: 140px;" />
                        <Column field="technolog" header="Technolog" style="width: 160px;" />
                        <Column field="kategoria_nazwa" header="Kategoria" />
                        <Column field="specyfikacja" header="Specyfikacja" />
                        <Column field="numer_katalogowy" header="Nr katalogowy" style="width: 130px;" />
                        <Column field="ilosc" header="Ilość" style="width: 70px; text-align: center;">
                            <template #body="{ data }"><strong>{{ data.ilosc }}</strong></template>
                        </Column>
                        <Column field="uwagi" header="Uwagi" />
                        <Column header="" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <div style="display: flex; gap: 4px; justify-content: center;">
                                    <Button icon="pi pi-link" class="p-button-success p-button-sm" @click="openAssignModal(data)" title="Przypisz narzędzie" />
                                    <Button icon="pi pi-times" class="p-button-danger p-button-sm" @click="openRejectModal(data)" title="Odrzuć pozycję" />
                                </div>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>
        </main>

        <!-- Modal Przypisywania narzędzia do pozycji zapotrzebowania -->
        <Dialog v-model:visible="assignModalVisible" header="Przypisz narzędzie do pozycji zapotrzebowania" :modal="true" :style="{ width: '550px' }">
            <div class="p-fluid" v-if="assignItem">
                <div class="field">
                    <label><strong>Zapotrzebowanie:</strong></label>
                    <p class="text-muted">{{ assignItem.zapotrzebowanie_numer }} — {{ assignItem.technolog }}</p>
                </div>
                <div class="field">
                    <label><strong>Specyfikacja technologa:</strong></label>
                    <p class="text-muted">{{ assignItem.specyfikacja }}</p>
                    <p v-if="assignItem.uwagi" class="text-muted small">Uwagi: {{ assignItem.uwagi }}</p>
                </div>
                <div class="field">
                    <label>Kategoria</label>
                    <Dropdown v-model="assignForm.kategoria_id" :options="kategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz kategorię" @change="onAssignKategoriaChange" />
                </div>
                <div class="field">
                    <label>Podkategoria</label>
                    <Dropdown v-model="assignForm.podkategoria_id" :options="assignPodkategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz podkategorię" :disabled="!assignForm.kategoria_id" @change="onAssignPodkategoriaChange" />
                </div>
                <div class="field">
                    <label>Narzędzie</label>
                    <Dropdown v-model="assignForm.narzedzie_id" :options="assignNarzedziaOptions" optionLabel="label" optionValue="value" placeholder="Wybierz narzędzie" :disabled="!assignForm.podkategoria_id" filter />
                </div>
                <Message v-if="assignError" severity="error" :closable="false">{{ assignError }}</Message>
                <Message severity="info" :closable="false">
                    Brak pasującego narzędzia? Najpierw dodaj je w <strong>Zakupach</strong>, potem wróć tutaj.
                </Message>
            </div>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="assignModalVisible = false" />
                <Button label="Przypisz" class="p-button-success" @click="confirmAssign" :loading="isAssigning" />
            </template>
        </Dialog>

        <!-- Modal Odrzucania pozycji zapotrzebowania -->
        <Dialog v-model:visible="rejectModalVisible" header="Odrzucić pozycję zapotrzebowania?" :modal="true" :style="{ width: '450px' }">
            <div v-if="rejectItem">
                <p>Czy na pewno odrzucić pozycję <strong>{{ rejectItem.specyfikacja }}</strong>?</p>
                <p class="small text-muted">Od: {{ rejectItem.technolog }} ({{ rejectItem.zapotrzebowanie_numer }})</p>
                <p class="small text-muted">Pozycja zniknie z listy bez trafiania do zamówienia.</p>
            </div>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="rejectModalVisible = false" />
                <Button label="Odrzuć" class="p-button-danger" @click="confirmReject" :loading="isRejecting" />
            </template>
        </Dialog>

        <!-- Modal Edycji -->
        <Dialog v-model:visible="editModalVisible" header="Edytuj pozycję zamówienia" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <div class="field"><label><strong>Narzędzie:</strong></label><p class="text-muted">{{ editForm.element }}</p></div>
                <div class="field"><label>Dostawca</label><Dropdown v-model="editForm.dostawca_id" :options="dostawcyOptions" optionLabel="label" optionValue="value" placeholder="Brak" /></div>
                <div class="field"><label>Nr Katalogowy</label><InputText v-model="editForm.numer_katalogowy" /></div>
                <div class="field"><label>Ilość</label><InputNumber v-model="editForm.ilosc_do_zamowienia" :min="1" /></div>
                <div class="field"><label>Cena jednostkowa (zł)</label><InputNumber v-model="editForm.cena_jednostkowa" :minFractionDigits="2" :maxFractionDigits="2" :min="0" /></div>
                <Message v-if="editError" severity="error" :closable="false">{{ editError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="editModalVisible = false" />
                <Button label="Zapisz zmiany" @click="saveEdit" :loading="isSaving" />
            </template>
        </Dialog>

        <!-- Modal Usuwania -->
        <Dialog v-model:visible="deleteModalVisible" header="Potwierdzenie usunięcia" :modal="true" :style="{ width: '400px' }">
            <p>Czy na pewno chcesz usunąć tę pozycję z listy zamówień?</p>
            <p class="text-muted"><strong>{{ deleteItem?.element }}</strong></p>
            <p class="small text-muted">Uwaga: Zostanie ustawiony limit maksymalny równy aktualnemu stanowi.</p>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="deleteModalVisible = false" />
                <Button label="Usuń" class="p-button-danger" @click="confirmDelete" :loading="isDeleting" />
            </template>
        </Dialog>

        <!-- Modal Masowego Usuwania -->
        <Dialog v-model:visible="bulkDeleteModalVisible" header="Potwierdzenie masowego usunięcia" :modal="true" :style="{ width: '420px' }">
            <p>Czy na pewno chcesz usunąć zaznaczone pozycje z listy zamówień?</p>
            <Message severity="warn" :closable="false"><strong>Liczba pozycji do usunięcia: {{ selectedTools.length }}</strong></Message>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="bulkDeleteModalVisible = false" />
                <Button :label="`Usuń zaznaczone (${selectedTools.length})`" class="p-button-danger" @click="confirmBulkDelete" :loading="isBulkDeleting" />
            </template>
        </Dialog>

        <!-- Modal Potwierdzenia Generowania -->
        <Dialog v-model:visible="confirmOrderModalVisible" header="Potwierdzenie generowania zamówień" :modal="true" :style="{ width: '450px' }">
            <Message severity="info" :closable="false"><strong>Liczba pozycji do zamówienia: {{ toolsToOrder.length }}</strong></Message>
            <p>Czy na pewno chcesz wygenerować zamówienia?</p>
            <Message severity="warn" :closable="false"><strong>Uwaga:</strong> Generator zostanie wyczyszczony po utworzeniu zamówień.</Message>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="confirmOrderModalVisible = false" />
                <Button label="Generuj zamówienia" icon="pi pi-check" class="p-button-success" @click="confirmZamowienieGotowe" :loading="isGenerating" />
            </template>
        </Dialog>

        <!-- Modal Dodawania -->
        <Dialog v-model:visible="addModalVisible" header="Dodaj ręcznie pozycję do zamówienia" :modal="true" :style="{ width: '560px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Tryb dodawania</label>
                    <div style="display: flex; gap: 8px;">
                        <Button
                            label="Z listy narzędzi"
                            icon="pi pi-list"
                            :severity="addForm.tryb === 'istniejace' ? 'secondary' : 'info'"
                            :outlined="addForm.tryb !== 'istniejace'"
                            style="flex: 1;"
                            @click="setTryb('istniejace')"
                        />
                        <Button
                            label="Nowe narzędzie"
                            icon="pi pi-plus-circle"
                            :severity="addForm.tryb === 'nowe' ? 'secondary' : 'info'"
                            :outlined="addForm.tryb !== 'nowe'"
                            style="flex: 1;"
                            @click="setTryb('nowe')"
                        />
                    </div>
                </div>

                <!-- TRYB: istniejące — najpierw wyszukiwarka narzędzia, potem podgląd + dostawca -->
                <template v-if="addForm.tryb === 'istniejace'">
                    <div class="field">
                        <label>Narzędzie</label>
                        <Dropdown v-model="addForm.narzedzie_id" :options="allNarzedziaOptions" optionLabel="label" optionValue="value"
                                  placeholder="Wyszukaj narzędzie..." filter filterPlaceholder="Szukaj po nazwie lub nr katalogowym"
                                  @change="onNarzedzieChange" />
                    </div>
                    <div class="p-grid" style="display: flex; gap: 12px;">
                        <div class="field" style="flex: 1;">
                            <label>Kategoria</label>
                            <InputText :modelValue="selectedNarzedzie ? (selectedNarzedzie.kategoria_nazwa || '-') : ''" disabled placeholder="—" />
                        </div>
                        <div class="field" style="flex: 1;">
                            <label>Podkategoria</label>
                            <InputText :modelValue="selectedNarzedzie ? (selectedNarzedzie.podkategoria?.nazwa || '-') : ''" disabled placeholder="—" />
                        </div>
                    </div>
                    <div class="field"><label>Dostawca</label><Dropdown v-model="addForm.dostawca_id" :options="dostawcyOptions" optionLabel="label" optionValue="value" placeholder="Brak" /></div>
                </template>

                <!-- TRYB: nowe — dostawca + kaskada kategoria/podkategoria + pola nowego narzędzia -->
                <template v-else>
                    <div class="field"><label>Dostawca</label><Dropdown v-model="addForm.dostawca_id" :options="dostawcyOptions" optionLabel="label" optionValue="value" placeholder="Brak" /></div>

                    <!-- Kategoria: istniejąca lub nowa -->
                    <div class="field">
                        <label>Kategoria</label>
                        <div class="p-inputgroup" v-if="!addForm.nowa_kategoria">
                            <Dropdown v-model="addForm.kategoria_id" :options="kategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz kategorię" @change="onKategoriaChange" />
                            <Button icon="pi pi-plus" class="p-button-secondary" title="Nowa kategoria" @click="toggleNowaKategoria(true)" />
                        </div>
                        <div class="p-inputgroup" v-else>
                            <InputText v-model="addForm.nowa_kategoria_nazwa" placeholder="Nazwa nowej kategorii" />
                            <Button icon="pi pi-times" class="p-button-secondary" title="Wybierz z listy" @click="toggleNowaKategoria(false)" />
                        </div>
                    </div>

                    <!-- Podkategoria: istniejąca lub nowa -->
                    <div class="field">
                        <label>Podkategoria</label>
                        <div class="p-inputgroup" v-if="!addForm.nowa_podkategoria">
                            <Dropdown v-model="addForm.podkategoria_id" :options="filteredPodkategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz podkategorię" :disabled="!addForm.kategoria_id && !addForm.nowa_kategoria" @change="onPodkategoriaChange" />
                            <Button icon="pi pi-plus" class="p-button-secondary" title="Nowa podkategoria" @click="toggleNowaPodkategoria(true)" />
                        </div>
                        <div class="p-inputgroup" v-else>
                            <InputText v-model="addForm.nowa_podkategoria_nazwa" placeholder="Nazwa nowej podkategorii" />
                            <Button icon="pi pi-times" class="p-button-secondary" title="Wybierz z listy" @click="toggleNowaPodkategoria(false)" :disabled="addForm.nowa_kategoria" />
                        </div>
                    </div>

                    <div class="field"><label>Opis / nazwa narzędzia *</label><InputText v-model="addForm.opis" placeholder="Np. Frez węglikowy 10mm" /></div>
                    <div class="field"><label>Numer katalogowy</label><InputText v-model="addForm.numer_katalogowy" placeholder="Opcjonalnie" /></div>
                    <div class="p-grid" style="display: flex; gap: 12px;">
                        <div class="field" style="flex: 1;">
                            <label>Jednostka zakupu</label>
                            <Dropdown v-model="addForm.opakowanie" :options="opakowanieOptions" optionLabel="label" optionValue="value" />
                        </div>
                        <div class="field" style="flex: 1;">
                            <label>Ilość w opakowaniu</label>
                            <InputNumber v-model="addForm.ilosc_w_opakowaniu" :min="1" />
                        </div>
                    </div>
                    <div class="p-grid" style="display: flex; gap: 12px;">
                        <div class="field" style="flex: 1;">
                            <label>Stan minimalny</label>
                            <InputNumber v-model="addForm.stan_minimalny" :min="0" />
                        </div>
                        <div class="field" style="flex: 1;">
                            <label>Stan maksymalny</label>
                            <InputNumber v-model="addForm.stan_maksymalny" :min="0" />
                        </div>
                    </div>
                </template>

                <div class="field"><label>Ilość do zamówienia <span v-if="selectedNarzedzie" class="text-muted">({{ selectedNarzedzie.opakowanie === 'kompl' ? 'komplety' : 'sztuki' }})</span></label><InputNumber v-model="addForm.ilosc_do_zamowienia" :min="1" /></div>
                <div class="field"><label>Cena jednostkowa (zł)</label><InputNumber v-model="addForm.cena_jednostkowa" :minFractionDigits="2" :maxFractionDigits="2" :min="0" /></div>
                <Message v-if="addError" severity="error" :closable="false">{{ addError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" class="p-button-text" @click="addModalVisible = false" />
                <Button label="Dodaj" class="p-button-success" @click="saveAdd" :loading="isAdding" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Message from 'primevue/message';
import ProgressSpinner from 'primevue/progressspinner';

const API_URL = '/api';

const props = defineProps({
    urls: { type: Object, default: () => ({ zamowienia: '/zamowienia-inertia/' }) }
});

const toolsToOrder = ref([]);
const nieprzypisanePozycje = ref([]);
const dostawcy = ref([]);
const kategorie = ref([]);
const narzedzia = ref([]);

const isLoading = ref(true);
const isSaving = ref(false);
const isDeleting = ref(false);
const isBulkDeleting = ref(false);
const isAdding = ref(false);
const isGenerating = ref(false);

const editModalVisible = ref(false);
const deleteModalVisible = ref(false);
const bulkDeleteModalVisible = ref(false);
const selectedTools = ref([]);
const addModalVisible = ref(false);
const confirmOrderModalVisible = ref(false);

const editForm = ref({ id: null, element: '', dostawca_id: null, numer_katalogowy: '', ilosc_do_zamowienia: 1, cena_jednostkowa: 0 });
const editError = ref('');
const deleteItem = ref(null);
const defaultAddForm = () => ({
    tryb: 'istniejace',
    dostawca_id: null,
    kategoria_id: null,
    podkategoria_id: null,
    narzedzie_id: null,
    nowa_kategoria: false,
    nowa_kategoria_nazwa: '',
    nowa_podkategoria: false,
    nowa_podkategoria_nazwa: '',
    opis: '',
    numer_katalogowy: '',
    opakowanie: 'szt',
    ilosc_w_opakowaniu: 1,
    stan_minimalny: 0,
    stan_maksymalny: 0,
    ilosc_do_zamowienia: 1,
    cena_jednostkowa: 0,
});
const addForm = ref(defaultAddForm());
const addError = ref('');
const selectedNarzedzie = ref(null);

const opakowanieOptions = [
    { label: 'Sztuka', value: 'szt' },
    { label: 'Komplet', value: 'kompl' },
];

// Stan przypisywania nieprzypisanych pozycji zapotrzebowania
const assignModalVisible = ref(false);
const assignItem = ref(null);
const assignForm = ref({ kategoria_id: null, podkategoria_id: null, narzedzie_id: null });
const assignError = ref('');
const isAssigning = ref(false);

const rejectModalVisible = ref(false);
const rejectItem = ref(null);
const isRejecting = ref(false);

const dostawcyOptions = computed(() => [{ label: 'Brak', value: null }, ...dostawcy.value.map(d => ({ label: d.nazwa_firmy, value: d.id }))]);
const kategorieOptions = computed(() => [{ label: 'Wybierz kategorię', value: null }, ...kategorie.value.map(k => ({ label: k.nazwa, value: k.id }))]);
const filteredPodkategorieOptions = computed(() => {
    if (!addForm.value.kategoria_id) return [];
    const kat = kategorie.value.find(k => k.id === addForm.value.kategoria_id);
    return kat ? [{ label: 'Wybierz podkategorię', value: null }, ...kat.podkategorie.map(p => ({ label: p.nazwa, value: p.id }))] : [];
});
const filteredNarzedziaOptions = computed(() => {
    if (!addForm.value.podkategoria_id) return [];
    return [{ label: 'Wybierz narzędzie', value: null }, ...narzedzia.value.filter(n => n.podkategoria?.id === addForm.value.podkategoria_id).map(n => ({ label: `${n.opis} ${n.numer_katalogowy ? '(' + n.numer_katalogowy + ')' : ''}`, value: n.id }))];
});
// Wszystkie narzędzia — dla wyszukiwarki w trybie "Z listy narzędzi" (kolejność: najpierw narzędzie)
const allNarzedziaOptions = computed(() => narzedzia.value.map(n => {
    const kat = n.kategoria_nazwa || '';
    const podkat = n.podkategoria?.nazwa || '';
    const sciezka = [kat, podkat].filter(Boolean).join(' / ');
    return {
        label: `${sciezka ? sciezka + ' — ' : ''}${n.opis}${n.numer_katalogowy ? ' (' + n.numer_katalogowy + ')' : ''}`,
        value: n.id,
    };
}));

const assignPodkategorieOptions = computed(() => {
    if (!assignForm.value.kategoria_id) return [];
    const kat = kategorie.value.find(k => k.id === assignForm.value.kategoria_id);
    return kat ? [{ label: 'Wybierz podkategorię', value: null }, ...kat.podkategorie.map(p => ({ label: p.nazwa, value: p.id }))] : [];
});
const assignNarzedziaOptions = computed(() => {
    if (!assignForm.value.podkategoria_id) return [];
    return [{ label: 'Wybierz narzędzie', value: null }, ...narzedzia.value.filter(n => n.podkategoria?.id === assignForm.value.podkategoria_id).map(n => ({ label: `${n.opis}${n.numer_katalogowy ? ' (' + n.numer_katalogowy + ')' : ''}`, value: n.id }))];
});

const onKategoriaChange = () => { addForm.value.podkategoria_id = null; addForm.value.narzedzie_id = null; selectedNarzedzie.value = null; };
const onPodkategoriaChange = () => { addForm.value.narzedzie_id = null; selectedNarzedzie.value = null; };
const onNarzedzieChange = () => {
    const n = addForm.value.narzedzie_id ? narzedzia.value.find(x => x.id === addForm.value.narzedzie_id) : null;
    selectedNarzedzie.value = n;
    // Tryb "Z listy narzędzi": po wyborze narzędzia auto-uzupełnij dostawcę i cenę (edytowalne)
    if (n && addForm.value.tryb === 'istniejace') {
        // ostatni_dostawca_id jest write_only w API — w payloadzie jest tylko zagnieżdżony ostatni_dostawca
        addForm.value.dostawca_id = n.ostatni_dostawca?.id ?? null;
        addForm.value.cena_jednostkowa = n.cena_jednostkowa != null ? Number(n.cena_jednostkowa) : 0;
    }
};

// Przełączenie trybu dodawania — reset pól zależnych od trybu, by stany się nie mieszały
const setTryb = (tryb) => {
    if (addForm.value.tryb === tryb) return;
    addForm.value.tryb = tryb;
    addForm.value.narzedzie_id = null;
    addForm.value.kategoria_id = null;
    addForm.value.podkategoria_id = null;
    addForm.value.dostawca_id = null;
    addForm.value.cena_jednostkowa = 0;
    addForm.value.nowa_kategoria = false;
    addForm.value.nowa_podkategoria = false;
    addForm.value.nowa_kategoria_nazwa = '';
    addForm.value.nowa_podkategoria_nazwa = '';
    selectedNarzedzie.value = null;
};

const toggleNowaKategoria = (val) => {
    addForm.value.nowa_kategoria = val;
    addForm.value.kategoria_id = null;
    addForm.value.nowa_kategoria_nazwa = val ? addForm.value.nowa_kategoria_nazwa : '';
    // Nowa kategoria wymusza też nową podkategorię
    if (val) {
        addForm.value.nowa_podkategoria = true;
        addForm.value.podkategoria_id = null;
    }
};
const toggleNowaPodkategoria = (val) => {
    addForm.value.nowa_podkategoria = val;
    addForm.value.podkategoria_id = null;
    addForm.value.nowa_podkategoria_nazwa = val ? addForm.value.nowa_podkategoria_nazwa : '';
};

const openAddModal = () => { addForm.value = defaultAddForm(); selectedNarzedzie.value = null; addError.value = ''; addModalVisible.value = true; };

// Przełączenie trybu — resetuj flagi "nowa kategoria/podkategoria" żeby UI był spójny
watch(() => addForm.value.tryb, (nowy) => {
    if (nowy === 'istniejace') {
        addForm.value.nowa_kategoria = false;
        addForm.value.nowa_kategoria_nazwa = '';
        addForm.value.nowa_podkategoria = false;
        addForm.value.nowa_podkategoria_nazwa = '';
    }
});
const openEditModal = (tool) => { editForm.value = { id: tool.id, element: tool.element, dostawca_id: tool.dostawca_id, numer_katalogowy: tool.numer_katalogowy || '', ilosc_do_zamowienia: tool.ilosc_do_zamowienia, cena_jednostkowa: tool.cena_jednostkowa || 0 }; editError.value = ''; editModalVisible.value = true; };
const openDeleteModal = (tool) => { deleteItem.value = tool; deleteModalVisible.value = true; };

const saveAdd = async () => {
    isAdding.value = true; addError.value = '';
    const f = addForm.value;

    // Walidacja po stronie klienta
    if (f.tryb === 'istniejace') {
        if (!f.narzedzie_id) { addError.value = 'Wybierz narzędzie'; isAdding.value = false; return; }
    } else {
        if (!f.opis || !f.opis.trim()) { addError.value = 'Podaj opis narzędzia'; isAdding.value = false; return; }
        if (!f.kategoria_id && !(f.nowa_kategoria && f.nowa_kategoria_nazwa.trim())) {
            addError.value = 'Wybierz kategorię lub podaj nazwę nowej'; isAdding.value = false; return;
        }
        if (!f.podkategoria_id && !(f.nowa_podkategoria && f.nowa_podkategoria_nazwa.trim())) {
            addError.value = 'Wybierz podkategorię lub podaj nazwę nowej'; isAdding.value = false; return;
        }
        if (f.opakowanie === 'kompl' && (f.ilosc_w_opakowaniu || 0) <= 1) {
            addError.value = 'Dla opakowania "Komplet" ilość w opakowaniu musi być > 1'; isAdding.value = false; return;
        }
    }

    // Zbuduj payload
    const payload = {
        tryb: f.tryb,
        dostawca_id: f.dostawca_id,
        ilosc_do_zamowienia: f.ilosc_do_zamowienia,
        cena_jednostkowa: f.cena_jednostkowa,
    };
    if (f.tryb === 'istniejace') {
        payload.narzedzie_id = f.narzedzie_id;
    } else {
        payload.kategoria_id = f.nowa_kategoria ? null : f.kategoria_id;
        payload.nowa_kategoria_nazwa = f.nowa_kategoria ? f.nowa_kategoria_nazwa.trim() : '';
        payload.podkategoria_id = f.nowa_podkategoria ? null : f.podkategoria_id;
        payload.nowa_podkategoria_nazwa = f.nowa_podkategoria ? f.nowa_podkategoria_nazwa.trim() : '';
        payload.opis = f.opis.trim();
        payload.numer_katalogowy = f.numer_katalogowy;
        payload.opakowanie = f.opakowanie;
        payload.ilosc_w_opakowaniu = f.ilosc_w_opakowaniu;
        payload.stan_minimalny = f.stan_minimalny;
        payload.stan_maksymalny = f.stan_maksymalny;
    }

    try {
        await axios.post(`${API_URL}/generator-zamowien/add/`, payload);
        addModalVisible.value = false;
        // Odśwież słowniki, bo mogły powstać nowe kategoria/podkategoria/narzędzie
        if (f.tryb === 'nowe') {
            const [katRes, narRes] = await Promise.all([
                axios.get(`${API_URL}/kategorie/`),
                axios.get(`${API_URL}/narzedzia/`),
            ]);
            kategorie.value = katRes.data;
            narzedzia.value = narRes.data.results || narRes.data;
        }
        await fetchToolsToOrder();
    }
    catch (error) { addError.value = error.response?.data?.error || 'Błąd dodawania'; }
    finally { isAdding.value = false; }
};

const saveEdit = async () => {
    isSaving.value = true; editError.value = '';
    try { await axios.patch(`${API_URL}/generator-zamowien/${editForm.value.id}/update/`, editForm.value); editModalVisible.value = false; await fetchToolsToOrder(); }
    catch (error) { editError.value = error.response?.data?.error || 'Błąd zapisu'; }
    finally { isSaving.value = false; }
};

const confirmDelete = async () => {
    if (!deleteItem.value) return;
    isDeleting.value = true;
    try {
        await axios.delete(`${API_URL}/generator-zamowien/${deleteItem.value.id}/delete/`);
        // Lokalne usunięcie - bez refetchu, żeby pozycja nie wróciła od razu z GET.
        // Wróci dopiero przy ponownym wejściu w generator (nowa sesja).
        toolsToOrder.value = toolsToOrder.value.filter(t => t.id !== deleteItem.value.id);
        deleteModalVisible.value = false;
    }
    catch (error) { alert('Błąd: ' + (error.response?.data?.error || error.message)); }
    finally { isDeleting.value = false; deleteItem.value = null; }
};

const openBulkDeleteModal = () => { if (selectedTools.value.length > 0) bulkDeleteModalVisible.value = true; };

const confirmBulkDelete = async () => {
    if (selectedTools.value.length === 0) return;
    isBulkDeleting.value = true;
    const ids = selectedTools.value.map(t => t.id);
    try {
        await axios.post(`${API_URL}/generator-zamowien/bulk-delete/`, { narzedzie_ids: ids });
        // Lokalne usunięcie - bez refetchu, żeby pozycje nie wróciły od razu z GET.
        const idsSet = new Set(ids);
        toolsToOrder.value = toolsToOrder.value.filter(t => !idsSet.has(t.id));
        selectedTools.value = [];
        bulkDeleteModalVisible.value = false;
    }
    catch (error) { alert('Błąd: ' + (error.response?.data?.error || error.message)); }
    finally { isBulkDeleting.value = false; }
};

const openAssignModal = (item) => {
    assignItem.value = item;
    assignForm.value = { kategoria_id: null, podkategoria_id: null, narzedzie_id: null };
    assignError.value = '';
    assignModalVisible.value = true;
};
const onAssignKategoriaChange = () => { assignForm.value.podkategoria_id = null; assignForm.value.narzedzie_id = null; };
const onAssignPodkategoriaChange = () => { assignForm.value.narzedzie_id = null; };

const confirmAssign = async () => {
    if (!assignItem.value) return;
    if (!assignForm.value.narzedzie_id) {
        assignError.value = 'Wybierz narzędzie';
        return;
    }
    isAssigning.value = true;
    assignError.value = '';
    try {
        await axios.post(`${API_URL}/generator-zamowien/przypisz-pozycje/${assignItem.value.id}/`, {
            narzedzie_id: assignForm.value.narzedzie_id
        });
        assignModalVisible.value = false;
        await fetchToolsToOrder();
    } catch (error) {
        assignError.value = error.response?.data?.error || 'Błąd przypisywania';
    } finally {
        isAssigning.value = false;
    }
};

const openRejectModal = (item) => {
    rejectItem.value = item;
    rejectModalVisible.value = true;
};

const confirmReject = async () => {
    if (!rejectItem.value) return;
    isRejecting.value = true;
    try {
        await axios.delete(`${API_URL}/generator-zamowien/odrzuc-pozycje/${rejectItem.value.id}/`);
        rejectModalVisible.value = false;
        rejectItem.value = null;
        await fetchToolsToOrder();
    } catch (error) {
        alert('Błąd: ' + (error.response?.data?.error || error.message));
    } finally {
        isRejecting.value = false;
    }
};

const zamowienieGotowe = () => { if (toolsToOrder.value.length === 0) { alert('Brak pozycji w generatorze!'); return; } confirmOrderModalVisible.value = true; };

const confirmZamowienieGotowe = async () => {
    isGenerating.value = true;
    try { const response = await axios.post(`${API_URL}/generator-zamowien/gotowe/`); if (response.data.success) { confirmOrderModalVisible.value = false; window.location.href = props.urls.zamowienia; } }
    catch (error) { alert('Błąd: ' + (error.response?.data?.error || error.message)); }
    finally { isGenerating.value = false; }
};

const fetchToolsToOrder = async () => {
    isLoading.value = true;
    try {
        const res = await axios.get(`${API_URL}/generator-zamowien/`);
        toolsToOrder.value = res.data.pozycje || [];
        nieprzypisanePozycje.value = res.data.nieprzypisane || [];
    }
    catch (error) { alert('Błąd ładowania danych.'); }
    finally { isLoading.value = false; }
};

onMounted(async () => {
    const [dosRes, katRes, narRes] = await Promise.all([axios.get(`${API_URL}/dostawcy/`), axios.get(`${API_URL}/kategorie/`), axios.get(`${API_URL}/narzedzia/`)]);
    dostawcy.value = dosRes.data;
    kategorie.value = katRes.data;
    narzedzia.value = narRes.data.results || narRes.data;
    await fetchToolsToOrder();
});
</script>

<style scoped>
.generator-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
}
.header-title { margin: 0; font-weight: bold; color: #fff; }
.header-title .yellow { color: #ffc107; }
.header-buttons a {
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 4px;
}
.app-main {
    flex: 1;
    padding: 16px 24px;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.generator-panel {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}
.panel-header { display: flex; align-items: center; padding: 12px 16px; }
.panel-header h3 { margin: 0; color: #ffc107; }
.panel-header .text-muted { margin-left: auto; }
.panel-header .btn-add-manual { margin-left: 30px; }
.btn-bulk-delete { width: auto !important; min-width: 8rem !important; padding: 0.3rem 0.6rem; white-space: nowrap; gap: 0.35rem; }
.btn-bulk-delete :deep(.p-button-label) { display: inline-block !important; visibility: visible !important; width: auto !important; font-size: 0.8rem; font-weight: 600; }
.btn-bulk-delete :deep(.p-button-icon) { font-size: 0.8rem; }
.panel-body { flex: 1; overflow: auto; min-height: 0; background: #212529; }
.empty-state.success { color: #75b798; }
.empty-state.success i { color: #198754 !important; }
.small { font-size: 0.85rem; }

:deep(.p-datatable .p-datatable-tbody > tr > td) {
    padding: 4px 12px;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
    padding: 6px 12px;
    height: 50px;
}

.nieprzypisane-panel {
    flex-shrink: 0;
    max-height: 40%;
    display: flex;
    flex-direction: column;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.zrodlo-auto { color: #4dabf7; font-size: 0.85rem; }
.zrodlo-reczne { color: #ffc107; font-size: 0.85rem; }
.zrodlo-zapotrzebowanie { color: #69db7c; font-size: 0.85rem; font-weight: 600; }

:deep(.p-button.p-button-sm) {
    width: 32px;
    height: 32px;
    padding: 0;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

</style>

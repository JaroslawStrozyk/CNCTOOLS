<template>
    <div class="generator-app">
        <header class="app-header">
            <h2 class="header-title">CNC MILLING: <span class="yellow">Generator Zamówień</span></h2>
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
                </div>
                <div class="panel-body">
                    <div v-if="isLoading" class="loading-spinner">
                        <ProgressSpinner />
                        <p>Ładowanie danych...</p>
                    </div>
                    <div v-else-if="toolsToOrder.length === 0" class="empty-state success">
                        <i class="pi pi-check-circle" style="font-size: 3rem; color: #198754;"></i>
                        <h5>Wszystkie narzędzia są na odpowiednim poziomie</h5>
                        <p>Nie ma nic do zamówienia.</p>
                    </div>
                    <DataTable v-else :value="toolsToOrder" :scrollable="true" scrollHeight="flex">
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
                        <Column header="" style="width: 120px; text-align: center;">
                            <template #header>
                                <Button icon="pi pi-plus" class="p-button-success p-button-sm" @click="openAddModal" title="Dodaj ręcznie" />
                            </template>
                            <template #body="{ data }">
                                <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm mr-1" @click="openEditModal(data)" title="Edytuj" />
                                <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteModal(data)" title="Usuń" />
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>
        </main>

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
        <Dialog v-model:visible="addModalVisible" header="Dodaj ręcznie pozycję do zamówienia" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <div class="field"><label>Dostawca</label><Dropdown v-model="addForm.dostawca_id" :options="dostawcyOptions" optionLabel="label" optionValue="value" placeholder="Brak" /></div>
                <div class="field"><label>Kategoria</label><Dropdown v-model="addForm.kategoria_id" :options="kategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz kategorię" @change="onKategoriaChange" /></div>
                <div class="field"><label>Podkategoria</label><Dropdown v-model="addForm.podkategoria_id" :options="filteredPodkategorieOptions" optionLabel="label" optionValue="value" placeholder="Wybierz podkategorię" :disabled="!addForm.kategoria_id" @change="onPodkategoriaChange" /></div>
                <div class="field"><label>Narzędzie</label><Dropdown v-model="addForm.narzedzie_id" :options="filteredNarzedziaOptions" optionLabel="label" optionValue="value" placeholder="Wybierz narzędzie" :disabled="!addForm.podkategoria_id" @change="onNarzedzieChange" /></div>
                <div class="field"><label>Ilość <span v-if="selectedNarzedzie" class="text-muted">({{ selectedNarzedzie.opakowanie === 'kompl' ? 'komplety' : 'sztuki' }})</span></label><InputNumber v-model="addForm.ilosc_do_zamowienia" :min="1" /></div>
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
import { ref, computed, onMounted } from 'vue';
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
const dostawcy = ref([]);
const kategorie = ref([]);
const narzedzia = ref([]);

const isLoading = ref(true);
const isSaving = ref(false);
const isDeleting = ref(false);
const isAdding = ref(false);
const isGenerating = ref(false);

const editModalVisible = ref(false);
const deleteModalVisible = ref(false);
const addModalVisible = ref(false);
const confirmOrderModalVisible = ref(false);

const editForm = ref({ id: null, element: '', dostawca_id: null, numer_katalogowy: '', ilosc_do_zamowienia: 1, cena_jednostkowa: 0 });
const editError = ref('');
const deleteItem = ref(null);
const addForm = ref({ dostawca_id: null, kategoria_id: null, podkategoria_id: null, narzedzie_id: null, ilosc_do_zamowienia: 1, cena_jednostkowa: 0 });
const addError = ref('');
const selectedNarzedzie = ref(null);

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

const onKategoriaChange = () => { addForm.value.podkategoria_id = null; addForm.value.narzedzie_id = null; selectedNarzedzie.value = null; };
const onPodkategoriaChange = () => { addForm.value.narzedzie_id = null; selectedNarzedzie.value = null; };
const onNarzedzieChange = () => { selectedNarzedzie.value = addForm.value.narzedzie_id ? narzedzia.value.find(n => n.id === addForm.value.narzedzie_id) : null; };

const openAddModal = () => { addForm.value = { dostawca_id: null, kategoria_id: null, podkategoria_id: null, narzedzie_id: null, ilosc_do_zamowienia: 1, cena_jednostkowa: 0 }; selectedNarzedzie.value = null; addError.value = ''; addModalVisible.value = true; };
const openEditModal = (tool) => { editForm.value = { id: tool.id, element: tool.element, dostawca_id: tool.dostawca_id, numer_katalogowy: tool.numer_katalogowy || '', ilosc_do_zamowienia: tool.ilosc_do_zamowienia, cena_jednostkowa: tool.cena_jednostkowa || 0 }; editError.value = ''; editModalVisible.value = true; };
const openDeleteModal = (tool) => { deleteItem.value = tool; deleteModalVisible.value = true; };

const saveAdd = async () => {
    isAdding.value = true; addError.value = '';
    if (!addForm.value.narzedzie_id) { addError.value = 'Wybierz narzędzie'; isAdding.value = false; return; }
    try { await axios.post(`${API_URL}/generator-zamowien/add/`, addForm.value); addModalVisible.value = false; await fetchToolsToOrder(); }
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
    try { await axios.delete(`${API_URL}/generator-zamowien/${deleteItem.value.id}/delete/`); deleteModalVisible.value = false; await fetchToolsToOrder(); }
    catch (error) { alert('Błąd: ' + (error.response?.data?.error || error.message)); }
    finally { isDeleting.value = false; deleteItem.value = null; }
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
    try { const res = await axios.get(`${API_URL}/generator-zamowien/`); toolsToOrder.value = res.data; }
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
.app-main { flex: 1; padding: 16px 24px; min-height: 0; }
.generator-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}
.panel-header h3 { margin: 0; color: #ffc107; }
.panel-body { flex: 1; overflow: auto; min-height: 0; background: #212529; }
.empty-state.success { color: #75b798; }
.empty-state.success i { color: #198754 !important; }
.small { font-size: 0.85rem; }
</style>

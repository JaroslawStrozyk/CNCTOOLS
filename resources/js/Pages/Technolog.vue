<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">TECHNOLOGIA</h2>
            <div class="header-user-name">
                {{ auth.user.first_name }} {{ auth.user.last_name }}
            </div>
            <div class="header-buttons">
                <button
                    class="btn-history"
                    @click="openHistoriaModal"
                    title="Historia zamówień"
                >
                    <i class="pi pi-history"></i>
                    Historia
                </button>
                <button
                    class="btn-demand-card"
                    :disabled="isKoszykEmpty"
                    @click="openKoszykModal"
                    title="Zamówienie"
                >
                    <i class="pi pi-shopping-cart"></i>
                    Zamówienie
                    <span v-if="koszykCount > 0" class="badge">{{ koszykCount }}</span>
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
                        :paginator="true"
                        :rows="pageSize"
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
                                <span v-if="data.numer_katalogowy">{{ data.numer_katalogowy }}</span>
                                <span v-else class="text-muted">-</span>
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
                        <Column header="" style="width: 50px; text-align: center;">
                            <template #body="{ data }">
                                <button class="btn-preview" @click.stop="openPreviewModal(data)" title="Podgląd">
                                    <i class="pi pi-image"></i>
                                </button>
                            </template>
                        </Column>
                        <Column style="width: 50px; text-align: center;">
                            <template #header>
                                <button class="btn-new-demand" @click="openKartaModal(null)" title="Nowa karta zapotrzebowania">
                                    <i class="pi pi-plus"></i>
                                </button>
                            </template>
                            <template #body="{ data }">
                                <button class="btn-demand-card-row" @click.stop="openKartaModal(data)" title="Karta zapotrzebowania">
                                    <i class="pi pi-file-plus"></i>
                                </button>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

        </main>

        <!-- Modal: Historia zamówień -->
        <Dialog
            v-model:visible="historiaModalVisible"
            header="Historia zamówień"
            :modal="true"
            :style="{ width: '95vw', maxWidth: '95vw', minWidth: '1400px' }"
            class="historia-modal"
        >
            <div class="historia-content">
                <!-- Przełącznik: Moje / Wszystkie -->
                <div class="historia-toolbar">
                    <div class="historia-toggle">
                        <button
                            :class="['toggle-btn', { active: !historiaShowAll }]"
                            @click="historiaShowAll = false; fetchHistoria()"
                        >
                            <i class="pi pi-user"></i>
                            Moje zamówienia
                        </button>
                        <button
                            :class="['toggle-btn', { active: historiaShowAll }]"
                            @click="historiaShowAll = true; fetchHistoria()"
                        >
                            <i class="pi pi-users"></i>
                            Wszystkich technologów
                        </button>
                    </div>
                    <div class="historia-info">
                        <i class="pi pi-info-circle"></i>
                        Historia z ostatnich 6 miesięcy
                    </div>
                </div>

                <!-- Tabela historii -->
                <DataTable
                    :value="historiaZamowien"
                    :scrollable="true"
                    scrollHeight="calc(80vh - 180px)"
                    dataKey="id"
                    class="historia-table"
                    v-model:expandedRows="expandedHistoriaRows"
                    :loading="historiaLoading"
                >
                    <Column expander style="width: 50px" />
                    <Column header="Nr zamówienia" style="width: 140px;">
                        <template #body="{ data }">
                            <strong class="numer-zamowienia">ZAM-{{ String(data.id).padStart(4, '0') }}</strong>
                        </template>
                    </Column>
                    <Column header="Technolog" style="width: 180px;" v-if="historiaShowAll">
                        <template #body="{ data }">
                            {{ data.technolog ? `${data.technolog.first_name} ${data.technolog.last_name}` : '-' }}
                        </template>
                    </Column>
                    <Column header="Data wysłania" style="width: 150px;">
                        <template #body="{ data }">
                            {{ data.data_wyslania ? formatDate(data.data_wyslania) : '-' }}
                        </template>
                    </Column>
                    <Column header="Status" style="width: 130px;">
                        <template #body="{ data }">
                            <span :class="['status-badge', `status-${data.status}`]">
                                {{ data.status_display }}
                            </span>
                        </template>
                    </Column>
                    <Column header="Data realizacji" style="width: 150px;">
                        <template #body="{ data }">
                            {{ data.data_realizacji ? formatDate(data.data_realizacji) : '-' }}
                        </template>
                    </Column>
                    <Column header="Pozycji" style="width: 80px; text-align: center;">
                        <template #body="{ data }">
                            <span class="pozycje-count">{{ data.pozycje_count }}</span>
                        </template>
                    </Column>
                    <Column header="Akcje" style="width: 80px; text-align: center;">
                        <template #body="{ data }">
                            <button class="btn-pdf-small" @click="openHistoriaPdf(data)" title="Podgląd PDF">
                                <i class="pi pi-file-pdf"></i>
                            </button>
                        </template>
                    </Column>

                    <!-- Rozwinięte pozycje -->
                    <template #expansion="{ data }">
                        <div class="historia-pozycje">
                            <h4>Pozycje zamówienia</h4>
                            <DataTable :value="data.pozycje" class="pozycje-subtable">
                                <Column field="nr_klienta" header="Nr klienta" style="width: 100px;">
                                    <template #body="{ data: poz }">{{ poz.nr_klienta || '-' }}</template>
                                </Column>
                                <Column field="nr_zlecenia" header="Nr zlecenia" style="width: 100px;">
                                    <template #body="{ data: poz }">{{ poz.nr_zlecenia || '-' }}</template>
                                </Column>
                                <Column field="kategoria_nazwa" header="Kategoria" style="width: 120px;">
                                    <template #body="{ data: poz }">{{ poz.kategoria_nazwa || '-' }}</template>
                                </Column>
                                <Column field="podkategoria_nazwa" header="Podkategoria" style="width: 120px;">
                                    <template #body="{ data: poz }">{{ poz.podkategoria_nazwa || '-' }}</template>
                                </Column>
                                <Column field="specyfikacja" header="Specyfikacja">
                                    <template #body="{ data: poz }">{{ poz.specyfikacja || '-' }}</template>
                                </Column>
                                <Column field="numer_katalogowy" header="Nr kat." style="width: 130px;">
                                    <template #body="{ data: poz }">{{ poz.numer_katalogowy || '-' }}</template>
                                </Column>
                                <Column field="ilosc" header="Ilość" style="width: 70px; text-align: center;">
                                    <template #body="{ data: poz }">
                                        <strong>{{ poz.ilosc }}</strong>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </template>

                    <template #empty>
                        <div class="empty-historia">
                            <i class="pi pi-inbox"></i>
                            <p>Brak zamówień w historii</p>
                        </div>
                    </template>
                </DataTable>
            </div>
            <template #footer>
                <Button label="Zamknij" class="btn-modal-secondary" @click="historiaModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Podgląd narzędzia -->
        <Dialog v-model:visible="previewModalVisible" :header="previewTool ? previewTool.opis : 'Podgląd'" :modal="true" :style="{ width: '500px' }">
            <div class="preview-content">
                <img
                    v-if="previewTool && previewTool.obraz"
                    :src="previewTool.obraz"
                    class="preview-image"
                    alt="Obrazek narzędzia"
                />
                <img
                    v-else
                    :src="defaultToolImage"
                    class="preview-image"
                    alt="Domyślny obrazek narzędzia"
                />
            </div>
            <template #footer>
                <Button label="Zamknij" class="btn-modal-secondary" @click="previewModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Karta zapotrzebowania -->
        <Dialog
            v-model:visible="kartaModalVisible"
            :header="kartaModalTitle"
            :modal="true"
            :style="{ width: '600px' }"
        >
            <div class="karta-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>Nr klienta</label>
                        <input type="text" v-model="kartaForm.nr_klienta" class="form-control" placeholder="Np. K-001" />
                    </div>
                    <div class="form-group">
                        <label>Nr zlecenia <span class="required">*</span></label>
                        <input
                            type="text"
                            v-model="kartaForm.nr_zlecenia"
                            class="form-control"
                            :class="{ 'is-invalid': nrZleceniaError }"
                            placeholder="Np. 26-0396 lub 26-004M"
                            maxlength="7"
                            required
                        />
                        <small v-if="nrZleceniaError" class="invalid-feedback">{{ nrZleceniaError }}</small>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Kategoria</label>
                        <Dropdown
                            v-model="kartaForm.kategoria_id"
                            :options="kartaKategorieOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Wybierz kategorię"
                            :disabled="kartaForm.narzedzie_typ_id !== null"
                            @change="onKartaKategoriaChange"
                            class="karta-dropdown"
                            :class="{ 'disabled-field': kartaForm.narzedzie_typ_id !== null }"
                        />
                    </div>
                    <div class="form-group">
                        <label>Podkategoria</label>
                        <Dropdown
                            v-model="kartaForm.podkategoria_id"
                            :options="kartaPodkategorieOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Wybierz podkategorię"
                            :disabled="kartaForm.narzedzie_typ_id !== null || !kartaForm.kategoria_id"
                            class="karta-dropdown"
                            :class="{ 'disabled-field': kartaForm.narzedzie_typ_id !== null || !kartaForm.kategoria_id }"
                        />
                    </div>
                </div>

                <div class="form-group full-width">
                    <label>Specyfikacja / Opis</label>
                    <textarea
                        v-model="kartaForm.specyfikacja"
                        class="form-control"
                        rows="2"
                        :disabled="kartaForm.narzedzie_typ_id !== null"
                        :class="{ 'disabled-field': kartaForm.narzedzie_typ_id !== null }"
                    ></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Nr katalogowy</label>
                        <input
                            type="text"
                            v-model="kartaForm.numer_katalogowy"
                            class="form-control"
                            :disabled="kartaForm.narzedzie_typ_id !== null"
                            :class="{ 'disabled-field': kartaForm.narzedzie_typ_id !== null }"
                        />
                    </div>
                    <div class="form-group">
                        <label>Ilość *</label>
                        <input type="number" v-model.number="kartaForm.ilosc" class="form-control" min="1" />
                    </div>
                </div>

                <div class="form-group full-width">
                    <label>Uwagi</label>
                    <textarea v-model="kartaForm.uwagi" class="form-control" rows="2" placeholder="Dodatkowe uwagi..."></textarea>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" class="btn-modal-secondary" @click="closeKartaModal" />
                <Button
                    :label="kartaMode === 'add' ? 'Dodaj do zamówienia' : 'Zapisz zmiany'"
                    class="btn-modal-primary"
                    @click="saveKartaForm"
                    :disabled="!kartaForm.ilosc || kartaForm.ilosc < 1 || !!nrZleceniaError"
                />
            </template>
        </Dialog>

        <!-- Modal: Koszyk (Zamówienie) -->
        <Dialog
            v-model:visible="koszykModalVisible"
            header="Zamówienie"
            :modal="true"
            :style="{ width: '1300px' }"
        >
            <div class="koszyk-content">
                <!-- Nagłówek zamówienia -->
                <div class="zamowienie-header">
                    <div class="zamowienie-header-item">
                        <span class="label">Nr zamówienia:</span>
                        <span class="value">{{ numerZamowienia }}</span>
                    </div>
                    <div class="zamowienie-header-item">
                        <span class="label">Dział:</span>
                        <span class="value">{{ dzialUzytkownika }}</span>
                    </div>
                    <div class="zamowienie-header-item">
                        <span class="label">Imię i Nazwisko:</span>
                        <span class="value">{{ pelneImieNazwisko }}</span>
                    </div>
                </div>
                <DataTable
                    :value="pozycjeKoszyka"
                    :scrollable="true"
                    scrollHeight="400px"
                    dataKey="id"
                    class="koszyk-table"
                >
                    <Column field="nr_klienta" header="Nr klienta" style="width: 100px;">
                        <template #body="{ data }">
                            {{ data.nr_klienta || '-' }}
                        </template>
                    </Column>
                    <Column field="nr_zlecenia" header="Nr zlecenia" style="width: 100px;">
                        <template #body="{ data }">
                            {{ data.nr_zlecenia || '-' }}
                        </template>
                    </Column>
                    <Column header="Kategoria" style="width: 120px;">
                        <template #body="{ data }">
                            {{ data.kategoria_nazwa || '-' }}
                        </template>
                    </Column>
                    <Column header="Podkategoria" style="width: 120px;">
                        <template #body="{ data }">
                            {{ data.podkategoria_nazwa || '-' }}
                        </template>
                    </Column>
                    <Column field="specyfikacja" header="Specyfikacja">
                        <template #body="{ data }">
                            {{ data.specyfikacja || '-' }}
                        </template>
                    </Column>
                    <Column field="numer_katalogowy" header="Nr kat." style="width: 150px; white-space: nowrap;">
                        <template #body="{ data }">
                            {{ data.numer_katalogowy || '-' }}
                        </template>
                    </Column>
                    <Column field="ilosc" header="Ilość" style="width: 70px; text-align: center;">
                        <template #body="{ data }">
                            <strong>{{ data.ilosc }}</strong>
                        </template>
                    </Column>
                    <Column header="Akcje" style="width: 100px; text-align: center;">
                        <template #body="{ data }">
                            <button class="btn-edit-row" @click="editPozycja(data)" title="Edytuj">
                                <i class="pi pi-pencil"></i>
                            </button>
                            <button class="btn-delete-row" @click="deletePozycja(data)" title="Usuń">
                                <i class="pi pi-trash"></i>
                            </button>
                        </template>
                    </Column>
                </DataTable>
            </div>
            <template #footer>
                <div class="koszyk-footer">
                    <div class="koszyk-summary">
                        <span>Pozycji: <strong>{{ koszykCount }}</strong></span>
                    </div>
                    <div class="koszyk-actions">
                        <Button label="Zamknij" class="btn-modal-secondary" @click="koszykModalVisible = false" />
                        <Button label="PDF" class="btn-modal-info" @click="openPdfPreview" :disabled="isKoszykEmpty" />
                        <Button label="Wyślij" class="btn-modal-success" @click="wyslijZamowienie" :disabled="isKoszykEmpty" />
                    </div>
                </div>
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie usunięcia -->
        <Dialog
            v-model:visible="confirmDeleteVisible"
            header="Potwierdzenie usunięcia"
            :modal="true"
            :style="{ width: '400px' }"
        >
            <div class="confirm-delete-content">
                <i class="pi pi-exclamation-triangle confirm-icon"></i>
                <p>Czy na pewno chcesz usunąć tę pozycję?</p>
                <p class="confirm-details" v-if="pozycjaToDelete">
                    <strong>{{ pozycjaToDelete.specyfikacja || 'Brak specyfikacji' }}</strong>
                </p>
            </div>
            <template #footer>
                <Button label="Anuluj" class="btn-modal-secondary" @click="cancelDelete" />
                <Button label="Usuń" class="btn-modal-danger" @click="confirmDelete" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie wysłania -->
        <Dialog
            v-model:visible="confirmSendVisible"
            header="Potwierdzenie wysłania"
            :modal="true"
            :style="{ width: '450px' }"
        >
            <div class="confirm-send-content">
                <i class="pi pi-send confirm-icon send-icon"></i>
                <p>Czy na pewno chcesz wysłać zapotrzebowanie?</p>
                <p class="confirm-warning">Po wysłaniu nie będzie można go edytować.</p>
                <div class="confirm-summary">
                    <span>Numer: <strong>{{ numerZamowienia }}</strong></span>
                    <span>Pozycji: <strong>{{ koszykCount }}</strong></span>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" class="btn-modal-secondary" @click="confirmSendVisible = false" />
                <Button label="Wyślij" class="btn-modal-success" @click="confirmSend" :loading="isSending" />
            </template>
        </Dialog>

        <!-- Modal: Sukces wysłania -->
        <Dialog
            v-model:visible="successSendVisible"
            header="Wysłano pomyślnie"
            :modal="true"
            :style="{ width: '400px' }"
            :closable="false"
        >
            <div class="success-send-content">
                <i class="pi pi-check-circle success-icon"></i>
                <p>Zapotrzebowanie zostało wysłane!</p>
                <p class="success-details">Numer: <strong>{{ lastSentNumer }}</strong></p>
            </div>
            <template #footer>
                <Button label="OK" class="btn-modal-primary" @click="closeSuccessSend" />
            </template>
        </Dialog>

        <!-- Modal: Podgląd PDF -->
        <Dialog
            v-model:visible="pdfPreviewVisible"
            header="Podgląd dokumentu PDF"
            :modal="true"
            :style="{ width: '90vw', maxWidth: '1200px' }"
            :contentStyle="{ padding: '0', overflow: 'hidden' }"
            @hide="closePdfPreview"
        >
            <div class="pdf-preview-container">
                <iframe
                    id="pdf-preview-iframe"
                    :src="pdfPreviewUrl"
                    class="pdf-iframe"
                ></iframe>
            </div>
            <template #footer>
                <Button label="Zamknij" class="btn-modal-secondary" @click="closePdfPreview" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import defaultToolImage from '@images/cnc.png';

// PrimeVue Components
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Dropdown from 'primevue/dropdown';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { first_name: '', last_name: '', username: '', grupa: '' },
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
            zapotrzebowania: '/zapotrzebowania/',
            logout: '/logout/'
        })
    },
    pageSize: {
        type: Number,
        default: 50
    }
});

// Data
const tools = ref([]);
const kategorie = ref([]);
const isLoadingTools = ref(true);

const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedToolForDetails = ref(null);
const searchQuery = ref('');

// Koszyk (zapotrzebowanie w statusie draft)
const koszyk = ref(null);
const pozycjeKoszyka = ref([]);

// Modals visibility
const previewModalVisible = ref(false);
const previewTool = ref(null);

// PDF Preview
const pdfPreviewVisible = ref(false);
const pdfPreviewUrl = ref('');
const kartaModalVisible = ref(false);
const koszykModalVisible = ref(false);

// Historia zamówień
const historiaModalVisible = ref(false);
const historiaZamowien = ref([]);
const historiaShowAll = ref(false);
const historiaLoading = ref(false);
const expandedHistoriaRows = ref([]);

// Formularz karty zapotrzebowania
const kartaForm = ref({
    narzedzie_typ_id: null,
    kategoria_id: null,
    podkategoria_id: null,
    specyfikacja: '',
    numer_katalogowy: '',
    nr_klienta: '',
    nr_zlecenia: '',
    ilosc: 1,
    uwagi: ''
});
const kartaMode = ref('add');
const editingPozycjaId = ref(null);
const returnToKoszyk = ref(false);

// Walidacja "Nr zlecenia" — format: 2 cyfry + "-" + 3 cyfry + 1 znak alfanumeryczny
// Przykłady poprawne: "26-0396", "26-004M"
const NR_ZLECENIA_REGEX = /^\d{2}-\d{3}[A-Za-z0-9]$/;
const nrZleceniaError = computed(() => {
    const v = (kartaForm.value.nr_zlecenia || '').trim();
    if (!v) return 'Nr zlecenia jest wymagany.';
    if (!NR_ZLECENIA_REGEX.test(v)) return 'Format: 2 cyfry, "-", 3 cyfry, 1 znak (np. 26-0396 lub 26-004M).';
    return '';
});

// Modal potwierdzenia usunięcia
const confirmDeleteVisible = ref(false);
const pozycjaToDelete = ref(null);

// Wysyłanie zamówienia
const confirmSendVisible = ref(false);
const successSendVisible = ref(false);
const isSending = ref(false);
const lastSentNumer = ref('');

// Computed
const koszykCount = computed(() => pozycjeKoszyka.value.length);
const isKoszykEmpty = computed(() => koszykCount.value === 0);

// Numer zamówienia w formacie ZAM-RRRR-NNNN
const numerZamowienia = computed(() => {
    if (!koszyk.value || !koszyk.value.id) return '-';
    const rok = new Date().getFullYear();
    const numer = String(koszyk.value.id).padStart(4, '0');
    return `ZAM-${rok}-${numer}`;
});

// Pełne imię i nazwisko użytkownika
const pelneImieNazwisko = computed(() => {
    const firstName = props.auth.user.first_name || '';
    const lastName = props.auth.user.last_name || '';
    return `${firstName} ${lastName}`.trim() || props.auth.user.username;
});

// Dział (grupa) użytkownika - wielkimi literami
const dzialUzytkownika = computed(() => {
    const grupa = props.auth.user.grupa || '-';
    return grupa.toUpperCase();
});

const kartaModalTitle = computed(() => {
    if (kartaMode.value === 'edit') {
        return 'Edycja pozycji';
    }
    if (kartaForm.value.narzedzie_typ_id !== null) {
        return 'Karta zapotrzebowania';
    }
    return 'Nowa karta zapotrzebowania';
});

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

// Filtrowane podkategorie dla native select (używane w panel-header)
const filteredPodkategorie = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return kategoria.podkategorie || [];
});

// Methods

// Kontekst wejścia — jeśli user przyszedł z Zapotrzebowania, "Wyjście" wraca tam zamiast wylogowywać
const entryFromParam = new URLSearchParams(window.location.search).get('from');
const entryOriginParam = new URLSearchParams(window.location.search).get('origin');

const logout = () => {
    if (entryFromParam === 'zapotrzebowania') {
        const base = props.urls.zapotrzebowania || '/zapotrzebowania/';
        const qs = entryOriginParam ? `?from=${encodeURIComponent(entryOriginParam)}` : '';
        window.location.href = base + qs;
        return;
    }
    window.location.href = props.urls.logout;
};

const openPreviewModal = (tool) => {
    previewTool.value = tool;
    previewModalVisible.value = true;
};

const rowClass = (data) => {
    return selectedToolForDetails.value && selectedToolForDetails.value.id === data.id ? 'selected-row' : '';
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const onToolSelect = () => {
    // Zarezerwowane dla przyszłej funkcjonalności
};

const onToolUnselect = () => {
    // Zarezerwowane dla przyszłej funkcjonalności
};

// === KOSZYK METHODS ===

const resetKartaForm = () => {
    kartaForm.value = {
        narzedzie_typ_id: null,
        kategoria_id: null,
        podkategoria_id: null,
        specyfikacja: '',
        numer_katalogowy: '',
        nr_klienta: '',
        nr_zlecenia: '',
        ilosc: 1,
        uwagi: ''
    };
    kartaMode.value = 'add';
    editingPozycjaId.value = null;
    returnToKoszyk.value = false;
};

const kartaKategorieOptions = computed(() => [
    { label: 'Brak', value: null },
    ...kategorie.value.map(k => ({ label: k.nazwa, value: k.id })),
]);

const kartaPodkategorieOptions = computed(() => {
    if (!kartaForm.value.kategoria_id) return [];
    const kat = kategorie.value.find(k => k.id === kartaForm.value.kategoria_id);
    return (kat?.podkategorie || []).map(p => ({ label: p.nazwa, value: p.id }));
});

const onKartaKategoriaChange = () => {
    kartaForm.value.podkategoria_id = null;
};

const openKartaModal = (tool) => {
    resetKartaForm();

    if (tool) {
        // Otwieranie z wiersza - wypełnij pola i zablokuj
        kartaForm.value.narzedzie_typ_id = tool.id;
        kartaForm.value.specyfikacja = tool.opis || '';
        kartaForm.value.numer_katalogowy = tool.numer_katalogowy || '';
        if (tool.podkategoria) {
            kartaForm.value.podkategoria_id = tool.podkategoria.id;
            const kat = kategorie.value.find(k =>
                k.podkategorie?.some(p => p.id === tool.podkategoria.id)
            );
            kartaForm.value.kategoria_id = kat?.id || null;
        }
    }
    // Jeśli tool = null, otwieramy pustą kartę (nowa ręczna pozycja)

    kartaModalVisible.value = true;
};

const openKoszykModal = () => {
    koszykModalVisible.value = true;
};

const closeKartaModal = () => {
    kartaModalVisible.value = false;

    // Wróć do koszyka jeśli edytowaliśmy z koszyka
    if (returnToKoszyk.value) {
        koszykModalVisible.value = true;
    }

    resetKartaForm();
};

const saveKartaForm = async () => {
    if (!koszyk.value) {
        alert('Błąd: Brak aktywnego koszyka');
        return;
    }
    if (nrZleceniaError.value) {
        alert(nrZleceniaError.value);
        return;
    }

    try {
        const kat = kategorie.value.find(k => k.id === kartaForm.value.kategoria_id);
        const pod = kat?.podkategorie?.find(p => p.id === kartaForm.value.podkategoria_id);
        const payload = {
            zapotrzebowanie: koszyk.value.id,
            narzedzie_typ_id: kartaForm.value.narzedzie_typ_id,
            kategoria_nazwa: kat?.nazwa || '',
            podkategoria_nazwa: pod?.nazwa || '',
            specyfikacja: kartaForm.value.specyfikacja,
            numer_katalogowy: kartaForm.value.numer_katalogowy,
            nr_klienta: kartaForm.value.nr_klienta,
            nr_zlecenia: kartaForm.value.nr_zlecenia,
            ilosc: kartaForm.value.ilosc,
            uwagi: kartaForm.value.uwagi
        };

        if (kartaMode.value === 'edit' && editingPozycjaId.value) {
            // Aktualizacja istniejącej pozycji
            await axios.patch(`${API_URL}/pozycje-zapotrzebowan/${editingPozycjaId.value}/`, payload);
        } else {
            // Dodanie nowej pozycji
            await axios.post(`${API_URL}/pozycje-zapotrzebowan/`, payload);
        }

        // Odśwież koszyk
        await fetchKoszyk();
        kartaModalVisible.value = false;

        // Wróć do koszyka jeśli edytowaliśmy z koszyka
        if (returnToKoszyk.value) {
            koszykModalVisible.value = true;
        }

        resetKartaForm();
    } catch (error) {
        console.error('Błąd zapisywania pozycji:', error.response?.data || error.message);
        alert('Błąd podczas zapisywania pozycji');
    }
};

const editPozycja = (pozycja) => {
    kartaMode.value = 'edit';
    editingPozycjaId.value = pozycja.id;
    returnToKoszyk.value = true;

    const kat = kategorie.value.find(k => k.nazwa === pozycja.kategoria_nazwa);
    const pod = kat?.podkategorie?.find(p => p.nazwa === pozycja.podkategoria_nazwa);
    kartaForm.value = {
        narzedzie_typ_id: pozycja.narzedzie_typ?.id || null,
        kategoria_id: kat?.id || null,
        podkategoria_id: pod?.id || null,
        specyfikacja: pozycja.specyfikacja || '',
        numer_katalogowy: pozycja.numer_katalogowy || '',
        nr_klienta: pozycja.nr_klienta || '',
        nr_zlecenia: pozycja.nr_zlecenia || '',
        ilosc: pozycja.ilosc || 1,
        uwagi: pozycja.uwagi || ''
    };

    koszykModalVisible.value = false;
    kartaModalVisible.value = true;
};

const deletePozycja = (pozycja) => {
    pozycjaToDelete.value = pozycja;
    confirmDeleteVisible.value = true;
};

const confirmDelete = async () => {
    if (!pozycjaToDelete.value) return;

    try {
        await axios.delete(`${API_URL}/pozycje-zapotrzebowan/${pozycjaToDelete.value.id}/`);
        await fetchKoszyk();
    } catch (error) {
        console.error('Błąd usuwania pozycji:', error.response?.data || error.message);
        alert('Błąd podczas usuwania pozycji');
    } finally {
        confirmDeleteVisible.value = false;
        pozycjaToDelete.value = null;
    }
};

const cancelDelete = () => {
    confirmDeleteVisible.value = false;
    pozycjaToDelete.value = null;
};

const openPdfPreview = async () => {
    if (!koszyk.value) return;

    try {
        const response = await axios.get(`${API_URL}/zapotrzebowania/${koszyk.value.id}/pdf/`, {
            responseType: 'blob'
        });

        // Zwolnij poprzedni URL jeśli istnieje
        if (pdfPreviewUrl.value) {
            window.URL.revokeObjectURL(pdfPreviewUrl.value);
        }

        pdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        pdfPreviewVisible.value = true;
    } catch (error) {
        console.error('Błąd generowania PDF:', error.response?.data || error.message);
        alert('Błąd podczas generowania PDF');
    }
};

const printPdf = () => {
    const iframe = document.getElementById('pdf-preview-iframe');
    if (iframe) {
        iframe.contentWindow.print();
    }
};

const downloadPdf = () => {
    if (!pdfPreviewUrl.value || !koszyk.value) return;

    const link = document.createElement('a');
    link.href = pdfPreviewUrl.value;
    link.setAttribute('download', `ZAM-${String(koszyk.value.id).padStart(4, '0')}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
};

const closePdfPreview = () => {
    pdfPreviewVisible.value = false;
    if (pdfPreviewUrl.value) {
        window.URL.revokeObjectURL(pdfPreviewUrl.value);
        pdfPreviewUrl.value = '';
    }
};

const wyslijZamowienie = () => {
    if (!koszyk.value) return;
    confirmSendVisible.value = true;
};

const confirmSend = async () => {
    if (!koszyk.value) return;

    isSending.value = true;
    try {
        await axios.post(`${API_URL}/zapotrzebowania/${koszyk.value.id}/wyslij/`);

        // Zapisz numer wysłanego zamówienia
        lastSentNumer.value = `ZAM-${String(koszyk.value.id).padStart(4, '0')}`;

        // Zamknij modalne
        confirmSendVisible.value = false;
        koszykModalVisible.value = false;

        // Pokaż sukces
        successSendVisible.value = true;

        // Pobierz nowy koszyk (stary został wysłany)
        await fetchKoszyk();
    } catch (error) {
        console.error('Błąd wysyłania:', error.response?.data || error.message);
        confirmSendVisible.value = false;
        // Wyświetl błąd w formie alertu (tymczasowo)
        alert(error.response?.data?.error || 'Błąd podczas wysyłania zapotrzebowania');
    } finally {
        isSending.value = false;
    }
};

const closeSuccessSend = () => {
    successSendVisible.value = false;
};

// === HISTORIA METHODS ===

const openHistoriaModal = () => {
    historiaModalVisible.value = true;
    fetchHistoria();
};

const fetchHistoria = async () => {
    historiaLoading.value = true;
    expandedHistoriaRows.value = [];
    try {
        const params = historiaShowAll.value ? '?all=true' : '';
        const response = await axios.get(`${API_URL}/zapotrzebowania/historia/${params}`);
        historiaZamowien.value = response.data;
    } catch (error) {
        console.error('Błąd pobierania historii:', error.response?.data || error.message);
        historiaZamowien.value = [];
    } finally {
        historiaLoading.value = false;
    }
};

const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
};

const openHistoriaPdf = async (zamowienie) => {
    try {
        const response = await axios.get(`${API_URL}/zapotrzebowania/${zamowienie.id}/pdf/`, {
            responseType: 'blob'
        });

        // Zwolnij poprzedni URL jeśli istnieje
        if (pdfPreviewUrl.value) {
            window.URL.revokeObjectURL(pdfPreviewUrl.value);
        }

        pdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        pdfPreviewVisible.value = true;
    } catch (error) {
        console.error('Błąd generowania PDF:', error.response?.data || error.message);
        alert('Błąd podczas generowania PDF');
    }
};

const fetchKoszyk = async () => {
    try {
        const response = await axios.get(`${API_URL}/zapotrzebowania/moj_koszyk/`);
        koszyk.value = response.data;
        pozycjeKoszyka.value = response.data.pozycje || [];
    } catch (error) {
        console.error('Błąd pobierania koszyka:', error.response?.data || error.message);
    }
};

const fetchInitialData = async () => {
    try {
        const [toolsRes, categoriesRes] = await Promise.all([
            axios.get(`${API_URL}/narzedzia/`),
            axios.get(`${API_URL}/kategorie/`)
        ]);

        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;

        // Pobierz koszyk
        await fetchKoszyk();
    } catch (error) {
        console.error("Błąd ładowania danych początkowych:", error.response?.data || error.message);
        alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
    } finally {
        isLoadingTools.value = false;
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

.header-user-name {
    flex: 1;
    text-align: center;
    color: #dee2e6;
    font-size: 1.1rem;
    font-weight: 500;
}

.header-buttons {
    display: flex;
    gap: 10px;
    align-items: center;
}

.btn-preview {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #17a2b8;
    background-color: #17a2b8;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-preview:hover {
    background-color: #138496;
    border-color: #117a8b;
}

.btn-history {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #6f42c1;
    background-color: #6f42c1;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}
.btn-history:hover {
    background-color: #5a32a3;
    border-color: #4e2a8e;
}

.btn-demand-card {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #28a745;
    background-color: #28a745;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
    position: relative;
}
.btn-demand-card:hover:not(:disabled) {
    background-color: #218838;
    border-color: #1e7e34;
}

.btn-demand-card:disabled {
    background-color: #6c757d;
    border-color: #6c757d;
    cursor: not-allowed;
    opacity: 0.65;
}

.btn-demand-card .badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background-color: #dc3545;
    color: #fff;
    font-size: 11px;
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 10px;
    min-width: 18px;
    text-align: center;
}

.btn-new-demand {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #28a745;
    background-color: #28a745;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-new-demand:hover {
    background-color: #218838;
    border-color: #1e7e34;
}

.btn-demand-card-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #28a745;
    background-color: #28a745;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-demand-card-row:hover {
    background-color: #218838;
    border-color: #1e7e34;
}

.btn-edit-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 12px;
    border: 1px solid #17a2b8;
    background-color: #17a2b8;
    color: #fff;
    cursor: pointer;
    margin-right: 4px;
    transition: all 0.15s ease-in-out;
}
.btn-edit-row:hover {
    background-color: #138496;
    border-color: #117a8b;
}

.btn-delete-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 12px;
    border: 1px solid #dc3545;
    background-color: #dc3545;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-delete-row:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

.preview-content {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background-color: #1f2937;
    border-radius: 6px;
}

.preview-image {
    max-width: 100%;
    max-height: 400px;
    object-fit: contain;
    border-radius: 4px;
}

.btn-exit {
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
.btn-exit:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

/* === GŁÓWNA ZAWARTOŚĆ === */
.magazyn-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 24px 15px 24px;
    gap: 0;
    min-height: 0;
    overflow: hidden;
}

/* === PANEL NARZĘDZI (GÓRNY) === */
.tools-panel {
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

.form-control:disabled,
.form-control.disabled-field {
    background-color: #1a1d20 !important;
    color: #6c757d !important;
    cursor: not-allowed;
    opacity: 0.7;
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

/* === KARTA FORM === */
.karta-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.form-row {
    display: flex;
    gap: 16px;
}

.form-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.form-group.full-width {
    width: 100%;
}

.form-group label {
    font-size: 13px;
    font-weight: 500;
    color: #adb5bd;
}

.form-group textarea {
    resize: vertical;
    min-height: 60px;
}

/* === KOSZYK CONTENT === */
.koszyk-content {
    min-height: 200px;
}

/* Nagłówek zamówienia */
.zamowienie-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    margin-bottom: 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 6px;
    border: 1px solid #495057;
}

.zamowienie-header-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.zamowienie-header-item .label {
    font-size: 11px;
    color: #adb5bd;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.zamowienie-header-item .value {
    font-size: 15px;
    font-weight: 600;
    color: #ffc107;
}

.koszyk-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.koszyk-summary {
    color: #adb5bd;
    font-size: 14px;
}

.koszyk-actions {
    display: flex;
    gap: 8px;
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

/* Walidacja Nr zlecenia */
.required { color: #dc3545; font-weight: bold; }
.form-control.is-invalid {
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 0.15rem rgba(220, 53, 69, 0.18);
}
.invalid-feedback {
    display: block;
    margin-top: 4px;
    font-size: 0.78rem;
    color: #f87171;
}
</style>

<!-- Style dla modali PrimeVue - CIEMNY MOTYW -->
<style>
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

/* === DROPDOWN W KARCIE ZAPOTRZEBOWANIA - CIEMNY MOTYW === */
.p-dialog .karta-dropdown {
    width: 100%;
    background-color: #343a40 !important;
    border: 1px solid #495057 !important;
    border-radius: 4px !important;
    color: #dee2e6 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
}

.p-dialog .karta-dropdown .p-dropdown-label {
    color: #dee2e6 !important;
    padding: 6px 12px !important;
    font-size: 14px !important;
}

.p-dialog .karta-dropdown .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
}

.p-dialog .karta-dropdown .p-dropdown-trigger {
    color: #adb5bd !important;
}

.p-dialog .karta-dropdown:not(.p-disabled):hover {
    border-color: #6c757d !important;
}

.p-dialog .karta-dropdown:not(.p-disabled).p-focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25) !important;
}

.p-dialog .karta-dropdown.p-disabled,
.p-dialog .karta-dropdown.disabled-field {
    background-color: #1a1d20 !important;
    opacity: 0.7;
    cursor: not-allowed;
}

.p-dialog .karta-dropdown.p-disabled .p-dropdown-label,
.p-dialog .karta-dropdown.disabled-field .p-dropdown-label {
    color: #6c757d !important;
}

.p-dialog .karta-dropdown .p-dropdown-clear-icon {
    color: #adb5bd !important;
    right: 36px;
}

/* Panel (rozwijana lista) - ciemny motyw */
.p-dropdown-panel {
    background-color: #2d3238 !important;
    border: 1px solid #495057 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}

.p-dropdown-panel .p-dropdown-items .p-dropdown-item {
    color: #dee2e6 !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
}

.p-dropdown-panel .p-dropdown-items .p-dropdown-item:hover {
    background-color: #3d444d !important;
    color: #fff !important;
}

.p-dropdown-panel .p-dropdown-items .p-dropdown-item.p-highlight {
    background-color: #4a3728 !important;
    color: #fff !important;
}

/* === PRZYCISKI W MODALACH === */
.p-dialog .p-button.btn-modal-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-secondary:hover {
    background-color: #5c636a !important;
    border-color: #565e64 !important;
}

.p-dialog .p-button.btn-modal-primary {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-primary:hover {
    background-color: #0b5ed7 !important;
    border-color: #0a58ca !important;
}

.p-dialog .p-button.btn-modal-primary:disabled {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    opacity: 0.65;
    cursor: not-allowed;
}

.p-dialog .p-button.btn-modal-success {
    background-color: #198754 !important;
    border-color: #198754 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-success:hover {
    background-color: #157347 !important;
    border-color: #146c43 !important;
}

.p-dialog .p-button.btn-modal-success:disabled {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    opacity: 0.65;
    cursor: not-allowed;
}

.p-dialog .p-button.btn-modal-info {
    background-color: #17a2b8 !important;
    border-color: #17a2b8 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-info:hover {
    background-color: #138496 !important;
    border-color: #117a8b !important;
}

.p-dialog .p-button.btn-modal-info:disabled {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    opacity: 0.65;
    cursor: not-allowed;
}

.p-dialog .p-button.btn-modal-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-danger:hover {
    background-color: #bb2d3b !important;
    border-color: #b02a37 !important;
}

/* Styl dla modalu potwierdzenia usunięcia */
.confirm-delete-content {
    text-align: center;
    padding: 10px 0;
}

.confirm-delete-content .confirm-icon {
    font-size: 3rem;
    color: #ffc107;
    margin-bottom: 15px;
    display: block;
}

.confirm-delete-content p {
    margin: 0 0 10px 0;
    color: #dee2e6;
}

.confirm-delete-content .confirm-details {
    color: #adb5bd;
    font-size: 0.9rem;
}

/* === POTWIERDZENIE WYSŁANIA === */
.confirm-send-content {
    text-align: center;
    padding: 10px 0;
}

.confirm-send-content .confirm-icon {
    font-size: 3rem;
    margin-bottom: 15px;
    display: block;
}

.confirm-send-content .send-icon {
    color: #198754;
}

.confirm-send-content p {
    margin: 0 0 10px 0;
    color: #dee2e6;
}

.confirm-send-content .confirm-warning {
    color: #ffc107;
    font-size: 0.9rem;
    font-style: italic;
}

.confirm-send-content .confirm-summary {
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-top: 15px;
    padding: 10px;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    color: #adb5bd;
}

/* === SUKCES WYSŁANIA === */
.success-send-content {
    text-align: center;
    padding: 20px 0;
}

.success-send-content .success-icon {
    font-size: 4rem;
    color: #198754;
    margin-bottom: 15px;
    display: block;
}

.success-send-content p {
    margin: 0 0 10px 0;
    color: #dee2e6;
    font-size: 1.1rem;
}

.success-send-content .success-details {
    color: #adb5bd;
    font-size: 0.95rem;
}

/* === PODGLĄD PDF === */
.pdf-preview-container {
    width: 100%;
    height: 70vh;
    min-height: 500px;
    background-color: #1a1d21;
}

.pdf-iframe {
    width: 100%;
    height: 100%;
    border: none;
}

.pdf-preview-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.pdf-preview-actions .p-button {
    display: flex;
    align-items: center;
}

/* === MODAL HISTORIA ZAMÓWIEŃ === */

/* Responsywny rozmiar modalu */
.historia-modal.p-dialog {
    width: 95vw !important;
    max-width: 95vw !important;
    min-width: min(1400px, 95vw) !important;
    max-height: 90vh !important;
}

.historia-modal .p-dialog-content {
    min-height: 760px;
    height: calc(85vh - 120px);
    overflow: hidden;
}

.historia-content {
    min-height: 700px;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.historia-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 6px;
    border: 1px solid #495057;
    flex-shrink: 0;
}

/* DataTable wypełnia resztę przestrzeni */
.historia-content .historia-table {
    flex: 1;
    min-height: 0;
}

.historia-content .p-datatable-wrapper {
    height: 100% !important;
}

.historia-toggle {
    display: flex;
    gap: 4px;
    background-color: #2d3238;
    padding: 4px;
    border-radius: 6px;
}

.historia-toggle .toggle-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    background-color: transparent;
    color: #adb5bd;
}

.historia-toggle .toggle-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #dee2e6;
}

.historia-toggle .toggle-btn.active {
    background-color: #6f42c1;
    color: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.historia-info {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #adb5bd;
    font-size: 13px;
}

.historia-info i {
    color: #ffc107;
}

/* Tabela historii */
.historia-table .numer-zamowienia {
    color: #ffc107;
    font-family: monospace;
    font-size: 14px;
}

.historia-table .status-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
}

.historia-table .status-submitted {
    background-color: rgba(23, 162, 184, 0.2);
    color: #17a2b8;
    border: 1px solid rgba(23, 162, 184, 0.4);
}

.historia-table .status-completed {
    background-color: rgba(25, 135, 84, 0.2);
    color: #28a745;
    border: 1px solid rgba(25, 135, 84, 0.4);
}

.historia-table .status-ordered {
    background-color: rgba(13, 110, 253, 0.2);
    color: #4dabf7;
    border: 1px solid rgba(13, 110, 253, 0.4);
}

.historia-table .status-cancelled {
    background-color: rgba(220, 53, 69, 0.2);
    color: #dc3545;
    border: 1px solid rgba(220, 53, 69, 0.4);
}

.historia-table .pozycje-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    height: 24px;
    padding: 0 8px;
    background-color: #495057;
    color: #dee2e6;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.btn-pdf-small {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #dc3545;
    background-color: #dc3545;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}

.btn-pdf-small:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

/* Rozwinięte pozycje */
.historia-pozycje {
    padding: 16px 20px;
    background-color: #1a1d21;
    border-radius: 6px;
    margin: 8px 0;
}

.historia-pozycje h4 {
    margin: 0 0 12px 0;
    color: #adb5bd;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.pozycje-subtable {
    font-size: 13px;
}

.p-datatable .pozycje-subtable .p-datatable-thead > tr > th {
    background-color: #2d3238 !important;
    padding: 8px 10px !important;
    font-size: 12px !important;
}

.p-datatable .pozycje-subtable .p-datatable-tbody > tr > td {
    padding: 6px 10px !important;
    background-color: #252a30 !important;
}

.p-datatable .pozycje-subtable .p-datatable-tbody > tr:nth-child(even) > td {
    background-color: #1f2428 !important;
}

/* Empty state */
.empty-historia {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: #6c757d;
}

.empty-historia i {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-historia p {
    font-size: 16px;
    margin: 0;
}

/* Expander button */
.p-datatable .p-row-toggler {
    color: #adb5bd !important;
}

.p-datatable .p-row-toggler:hover {
    color: #ffc107 !important;
    background-color: rgba(255, 193, 7, 0.1) !important;
}

</style>

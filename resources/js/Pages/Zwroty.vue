<template>
  <div class="zwroty-page">
    <!-- Header -->
    <header class="app-header">
      <h2 class="header-title">ZWROTY</h2>
      <div class="header-buttons">
        <a :href="urls.magazyn" class="btn btn-primary">
          <i class="pi pi-warehouse"></i> Magazyn
        </a>
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

    <!-- Main content -->
    <main class="main-content">
      <div class="card">
        <div class="card-content">
          <TabView v-model:activeIndex="activeTab">
            <TabPanel>
              <template #header>
                <i class="pi pi-exclamation-triangle mr-2"></i>
                <span>Uszkodzone elementy</span>
                <Badge :value="filteredDamagesUszkodzone.length" severity="danger" class="ml-2" />
              </template>
            <ProgressSpinner v-if="isLoading" class="loading-spinner" />
            <div v-else-if="damagesUszkodzone.length === 0" class="empty-state">
              <i class="pi pi-check-circle success-icon"></i>
              <p class="empty-title">Brak uszkodzonych elementów</p>
            </div>
            <template v-else>
              <!-- Pole wyszukiwania -->
              <div class="search-bar">
                <div class="search-wrapper">
                  <i class="pi pi-search search-icon" />
                  <InputText v-model="searchQuery" placeholder="Szukaj..." class="search-input" />
                </div>
                <Button v-if="searchQuery" icon="pi pi-times" class="p-button-secondary p-button-sm" @click="searchQuery = ''" title="Wyczyść" />
                <div class="search-bar-spacer"></div>
                <Button icon="pi pi-file-pdf" class="p-button-sm btn-pdf" @click="openPdfListPreview" title="Drukuj listę" />
              </div>
              <DataTable
                :value="filteredDamagesUszkodzone"
                responsiveLayout="scroll"
                class="damages-table"
                stripedRows
                scrollable
                scrollHeight="flex"
              >
                <Column header="Nr karty" style="width: 100px;">
                  <template #body="{ data }">
                    <strong v-if="data.numer_karty" class="karta-numer">{{ data.numer_karty }}</strong>
                    <span v-else>-</span>
                  </template>
                </Column>
                <Column header="Data uszkodzenia">
                  <template #body="{ data }">
                    {{ formatCustomDate(data.data_uszkodzenia) }}
                  </template>
                </Column>
                <Column header="Ostatnia maszyna">
                  <template #body="{ data }">
                    {{ data.maszyna_uszkodzenia || '-' }}
                  </template>
                </Column>
                <Column header="Zgłaszający">
                  <template #body="{ data }">
                    {{ data.nazwisko_zglaszajacego || formatPracownik(data.ostatni_pracownik) }}
                  </template>
                </Column>
                <Column header="Narzędzie">
                  <template #body="{ data }">
                    {{ data.kategoria_narzedzia }}: {{ data.opis_narzedzia }}
                  </template>
                </Column>
                <Column header="Nr kat.">
                  <template #body="{ data }">
                    {{ data.numer_katalogowy || '-' }}
                  </template>
                </Column>
                <Column header="Przyczyna uszkodzenia">
                  <template #body="{ data }">
                    {{ data.przyczyna_uszkodzenia || '-' }}
                  </template>
                </Column>
                <Column header="Stracony czas">
                  <template #body="{ data }">
                    {{ data.stracony_czas || '-' }}
                  </template>
                </Column>
                <Column header="Uwagi">
                  <template #body="{ data }">
                    {{ data.opis_uszkodzenia || '-' }}
                  </template>
                </Column>
                <Column header="Akcje" style="width: 140px; text-align: center;">
                  <template #body="{ data }">
                    <div class="btn-group-inline">
                      <Button icon="pi pi-file-pdf" class="p-button-sm btn-pdf" @click="openPdfPreview(data)" title="Drukuj" />
                      <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="openEditModal(data)" title="Edytuj" />
                      <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteModal(data)" title="Usuń" />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </template>
            </TabPanel>

            <TabPanel>
              <template #header>
                <i class="pi pi-refresh mr-2"></i>
                <span>Uszkodzone do regeneracji</span>
                <Badge :value="filteredDamagesRegeneracja.length" style="background-color: #8B4513;" class="ml-2" />
              </template>
              <ProgressSpinner v-if="isLoading" class="loading-spinner" />
              <div v-else-if="damagesRegeneracja.length === 0" class="empty-state">
                <i class="pi pi-check-circle success-icon"></i>
                <p class="empty-title">Brak elementów do regeneracji</p>
              </div>
              <template v-else>
                <!-- Pole wyszukiwania -->
                <div class="search-bar">
                  <div class="search-wrapper">
                    <i class="pi pi-search search-icon" />
                    <InputText v-model="searchQueryRegen" placeholder="Szukaj..." class="search-input" />
                  </div>
                  <Button v-if="searchQueryRegen" icon="pi pi-times" class="p-button-secondary p-button-sm" @click="searchQueryRegen = ''" title="Wyczyść" />
                  <div class="search-bar-spacer"></div>
                  <Button icon="pi pi-file-pdf" class="p-button-sm btn-pdf" @click="openPdfListPreviewRegen" title="Drukuj listę" />
                </div>
                <DataTable
                  :value="filteredDamagesRegeneracja"
                  responsiveLayout="scroll"
                  class="damages-table"
                  stripedRows
                  scrollable
                  scrollHeight="flex"
                >
                  <Column header="Nr karty" style="width: 100px;">
                    <template #body="{ data }">
                      <strong v-if="data.numer_karty" class="karta-numer-regen">{{ data.numer_karty }}</strong>
                      <span v-else>-</span>
                    </template>
                  </Column>
                  <Column header="Data uszkodzenia">
                    <template #body="{ data }">
                      {{ formatCustomDate(data.data_uszkodzenia) }}
                    </template>
                  </Column>
                  <Column header="Ostatnia maszyna">
                    <template #body="{ data }">
                      {{ data.maszyna_uszkodzenia || '-' }}
                    </template>
                  </Column>
                  <Column header="Ostatni użytkownik">
                    <template #body="{ data }">
                      {{ formatPracownik(data.ostatni_pracownik) }}
                    </template>
                  </Column>
                  <Column header="Narzędzie">
                    <template #body="{ data }">
                      {{ data.kategoria_narzedzia }}: {{ data.opis_narzedzia }}
                    </template>
                  </Column>
                  <Column header="Nr kat.">
                    <template #body="{ data }">
                      {{ data.numer_katalogowy || '-' }}
                    </template>
                  </Column>
                  <Column header="Ostatnia lokalizacja">
                    <template #body="{ data }">
                      {{ data.ostatnia_lokalizacja || '-' }}
                    </template>
                  </Column>
                  <Column header="Opis uszkodzenia">
                    <template #body="{ data }">
                      {{ data.opis_uszkodzenia || '-' }}
                    </template>
                  </Column>
                  <Column header="Akcje" style="width: 140px; text-align: center;">
                    <template #body="{ data }">
                      <div class="btn-group-inline">
                        <Button icon="pi pi-file-pdf" class="p-button-sm btn-pdf" @click="openPdfPreview(data)" title="Drukuj" />
                        <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="openEditModal(data)" title="Edytuj" />
                        <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteModal(data)" title="Usuń" />
                      </div>
                    </template>
                  </Column>
                </DataTable>
              </template>
            </TabPanel>
          </TabView>
        </div>
      </div>
    </main>

    <!-- Modal: Edycja uszkodzenia -->
    <Dialog v-model:visible="editModalVisible" header="Edytuj uszkodzenie" :modal="true" :style="{ width: '600px' }">
      <div class="p-fluid" v-if="editData">
        <div class="field">
          <label>Narzędzie</label>
          <InputText :value="`${editData.kategoria_narzedzia}: ${editData.opis_narzedzia}`" disabled />
        </div>
        <div class="field">
          <label>Nr karty</label>
          <InputText :value="editData.numer_karty || '-'" disabled />
        </div>
        <div class="field">
          <label>Zgłaszający</label>
          <InputText v-model="editData.nazwisko_zglaszajacego" />
        </div>
        <div class="field">
          <label>Przyczyna uszkodzenia</label>
          <Textarea v-model="editData.przyczyna_uszkodzenia" rows="3" />
        </div>
        <div class="field">
          <label>Stracony czas</label>
          <InputText v-model="editData.stracony_czas" />
        </div>
        <div class="field">
          <label>Uwagi</label>
          <Textarea v-model="editData.opis_uszkodzenia" rows="3" />
        </div>
      </div>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="editModalVisible = false" />
        <Button label="Zapisz" icon="pi pi-check" @click="saveEdit" :loading="isSaving" />
      </template>
    </Dialog>

    <!-- Modal: Potwierdzenie usunięcia -->
    <Dialog v-model:visible="deleteModalVisible" header="Potwierdź usunięcie" :modal="true" :style="{ width: '450px' }">
      <div v-if="deleteData">
        <p>Czy na pewno chcesz usunąć wpis uszkodzenia:</p>
        <p><strong>{{ deleteData.kategoria_narzedzia }}: {{ deleteData.opis_narzedzia }}</strong></p>
        <p v-if="deleteData.numer_karty">Nr karty: <strong class="karta-numer">{{ deleteData.numer_karty }}</strong></p>
      </div>
      <p class="text-danger mt-3">Tej operacji nie można cofnąć.</p>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteModalVisible = false" />
        <Button label="Tak, usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDelete" :loading="isDeleting" />
      </template>
    </Dialog>

    <!-- Modal: Podgląd PDF -->
    <Dialog
      v-model:visible="pdfPreviewVisible"
      header="Podgląd karty uszkodzenia"
      :modal="true"
      :style="{ width: '90vw', maxWidth: '1000px' }"
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
        <Button label="Zamknij" icon="pi pi-times" class="p-button-secondary" @click="closePdfPreview" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Badge from 'primevue/badge';
import ProgressSpinner from 'primevue/progressspinner';
import Menu from 'primevue/menu';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

const API_URL = '/api';

const props = defineProps({
  auth: Object,
  urls: Object,
  infoProgram: Object
});

// State
const damages = ref([]);
const isLoading = ref(false);
const activeTab = ref(0);
const searchQuery = ref('');
const searchQueryRegen = ref('');

// Modal edycji
const editModalVisible = ref(false);
const editData = ref(null);
const isSaving = ref(false);

// Modal usuwania
const deleteModalVisible = ref(false);
const deleteData = ref(null);
const isDeleting = ref(false);

// Modal PDF
const pdfPreviewVisible = ref(false);
const pdfPreviewUrl = ref('');
const currentPdfData = ref(null);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
  { label: 'Wyloguj', icon: 'pi pi-sign-out', command: () => { window.location.href = props.urls?.logout || '/logout/'; } }
]);

const toggleUserMenu = (event) => {
  userMenu.value.toggle(event);
};

// Computed
const damagesUszkodzone = computed(() => {
  return damages.value.filter(d => d.stan_egzemplarza === 'Uszkodzone');
});

const filteredDamagesUszkodzone = computed(() => {
  if (!searchQuery.value.trim()) {
    return damagesUszkodzone.value;
  }
  const query = searchQuery.value.toLowerCase().trim();
  return damagesUszkodzone.value.filter(d => {
    const searchFields = [
      d.numer_karty || '',
      formatCustomDate(d.data_uszkodzenia) || '',
      d.maszyna_uszkodzenia || '',
      d.nazwisko_zglaszajacego || formatPracownik(d.ostatni_pracownik) || '',
      `${d.kategoria_narzedzia}: ${d.opis_narzedzia}` || '',
      d.numer_katalogowy || '',
      d.przyczyna_uszkodzenia || '',
      d.stracony_czas || '',
      d.opis_uszkodzenia || ''
    ];
    return searchFields.some(field => field.toLowerCase().includes(query));
  });
});

const damagesRegeneracja = computed(() => {
  return damages.value.filter(d => d.stan_egzemplarza === 'Uszkodzone do regeneracji');
});

const filteredDamagesRegeneracja = computed(() => {
  if (!searchQueryRegen.value.trim()) {
    return damagesRegeneracja.value;
  }
  const query = searchQueryRegen.value.toLowerCase().trim();
  return damagesRegeneracja.value.filter(d => {
    const searchFields = [
      d.numer_karty || '',
      formatCustomDate(d.data_uszkodzenia) || '',
      d.maszyna_uszkodzenia || '',
      formatPracownik(d.ostatni_pracownik) || '',
      `${d.kategoria_narzedzia}: ${d.opis_narzedzia}` || '',
      d.numer_katalogowy || '',
      d.ostatnia_lokalizacja || '',
      d.opis_uszkodzenia || ''
    ];
    return searchFields.some(field => field.toLowerCase().includes(query));
  });
});

// Methods
const fetchDamages = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get(`${API_URL}/uszkodzenia/`);
    damages.value = response.data.results || response.data;
  } catch (error) {
    console.error('Błąd pobierania uszkodzeń:', error);
  } finally {
    isLoading.value = false;
  }
};

const formatCustomDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${day}.${month}.${year} ${hours}:${minutes}`;
};

const formatPracownik = (pracownik) => {
  if (!pracownik) return '-';
  return `${pracownik.nazwisko} ${pracownik.imie}`;
};

// Funkcje modalu edycji
const openEditModal = (damage) => {
  editData.value = { ...damage };
  editModalVisible.value = true;
};

const saveEdit = async () => {
  if (!editData.value) return;
  isSaving.value = true;
  try {
    await axios.patch(`${API_URL}/uszkodzenia/${editData.value.id}/`, {
      nazwisko_zglaszajacego: editData.value.nazwisko_zglaszajacego,
      przyczyna_uszkodzenia: editData.value.przyczyna_uszkodzenia,
      stracony_czas: editData.value.stracony_czas,
      opis_uszkodzenia: editData.value.opis_uszkodzenia
    });
    editModalVisible.value = false;
    await fetchDamages();
  } catch (error) {
    console.error('Błąd zapisu:', error);
    alert('Nie udało się zapisać zmian.');
  } finally {
    isSaving.value = false;
  }
};

// Funkcje modalu usuwania
const openDeleteModal = (damage) => {
  deleteData.value = damage;
  deleteModalVisible.value = true;
};

const confirmDelete = async () => {
  if (!deleteData.value) return;
  isDeleting.value = true;
  try {
    await axios.delete(`${API_URL}/uszkodzenia/${deleteData.value.id}/`);
    deleteModalVisible.value = false;
    await fetchDamages();
  } catch (error) {
    console.error('Błąd usuwania:', error);
    alert('Nie udało się usunąć wpisu.');
  } finally {
    isDeleting.value = false;
  }
};

// Funkcje PDF
const openPdfPreview = async (damage) => {
  currentPdfData.value = damage;
  try {
    const response = await axios.get(`${API_URL}/uszkodzenia/${damage.id}/pdf/`, {
      responseType: 'blob'
    });

    if (pdfPreviewUrl.value) {
      window.URL.revokeObjectURL(pdfPreviewUrl.value);
    }

    pdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    pdfPreviewVisible.value = true;
  } catch (error) {
    console.error('Błąd generowania PDF:', error);
    alert('Błąd podczas generowania PDF');
  }
};

const printPdf = () => {
  const iframe = document.getElementById('pdf-preview-iframe');
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.print();
  }
};

const downloadPdf = () => {
  if (!pdfPreviewUrl.value || !currentPdfData.value) return;
  const link = document.createElement('a');
  link.href = pdfPreviewUrl.value;

  let filename;
  const today = new Date().toISOString().split('T')[0];
  if (currentPdfData.value.type === 'lista') {
    filename = `Lista_uszkodzen_${today}.pdf`;
  } else if (currentPdfData.value.type === 'lista_regen') {
    filename = `Lista_do_regeneracji_${today}.pdf`;
  } else if (currentPdfData.value.numer_karty) {
    filename = `Karta_uszkodzenia_${currentPdfData.value.numer_karty.replace('/', '-')}.pdf`;
  } else {
    filename = `Karta_uszkodzenia_${currentPdfData.value.id}.pdf`;
  }

  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const closePdfPreview = () => {
  pdfPreviewVisible.value = false;
  if (pdfPreviewUrl.value) {
    window.URL.revokeObjectURL(pdfPreviewUrl.value);
    pdfPreviewUrl.value = '';
  }
  currentPdfData.value = null;
};

// Zbiorcze PDF listy uszkodzeń
const openPdfListPreview = async () => {
  try {
    // Pobierz ID z przefiltrowanej listy
    const ids = filteredDamagesUszkodzone.value.map(d => d.id);

    if (ids.length === 0) {
      alert('Brak elementów do wydruku.');
      return;
    }

    const response = await axios.post(`${API_URL}/uszkodzenia/pdf_lista/`, { ids, typ: 'uszkodzone' }, {
      responseType: 'blob'
    });

    if (pdfPreviewUrl.value) {
      window.URL.revokeObjectURL(pdfPreviewUrl.value);
    }

    pdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    currentPdfData.value = { type: 'lista', count: ids.length };
    pdfPreviewVisible.value = true;
  } catch (error) {
    console.error('Błąd generowania zbiorczego PDF:', error);
    alert('Błąd podczas generowania zbiorczego PDF');
  }
};

// Zbiorcze PDF listy do regeneracji
const openPdfListPreviewRegen = async () => {
  try {
    const ids = filteredDamagesRegeneracja.value.map(d => d.id);

    if (ids.length === 0) {
      alert('Brak elementów do wydruku.');
      return;
    }

    const response = await axios.post(`${API_URL}/uszkodzenia/pdf_lista/`, { ids, typ: 'regeneracja' }, {
      responseType: 'blob'
    });

    if (pdfPreviewUrl.value) {
      window.URL.revokeObjectURL(pdfPreviewUrl.value);
    }

    pdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    currentPdfData.value = { type: 'lista_regen', count: ids.length };
    pdfPreviewVisible.value = true;
  } catch (error) {
    console.error('Błąd generowania zbiorczego PDF:', error);
    alert('Błąd podczas generowania zbiorczego PDF');
  }
};

onMounted(() => {
  fetchDamages();
});
</script>

<style scoped>
.zwroty-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--dark-bg-primary);
  color: var(--dark-text-primary);
}

.main-content {
  flex: 1;
  padding: 1.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card {
  background: linear-gradient(to bottom, #343a40, #212529);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.empty-state { text-align: center; padding: 3rem; color: var(--dark-text-muted); }
.success-icon { font-size: 3rem; color: #198754; margin-bottom: 1rem; display: block; }
.empty-title { font-size: 1.25rem; margin: 0; }

/* TabView styling */
:deep(.p-tabview) {
    background: transparent;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

:deep(.p-tabview-nav-container) {
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

:deep(.p-tabview-nav li .p-tabview-nav-link:focus) {
    box-shadow: none;
}

:deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
    border-bottom-color: #ffc107;
    color: #ffc107;
    background: rgba(255, 193, 7, 0.1);
}

:deep(.p-tabview-panels) {
    padding: 0;
    background: #212529;
    flex: 1;
    overflow: auto;
}

:deep(.p-tabview-panel) {
    padding: 0;
}

/* Badge w nagłówku zakładki */
:deep(.p-tabview-nav-link .p-badge) {
    margin-left: 8px;
    font-size: 0.75rem;
}

/* Utility classes */
.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }

/* Numer karty uszkodzenia */
.karta-numer {
  color: #ffc107;
}

/* Numer karty regeneracji - brązowy */
.karta-numer-regen {
  color: #cd853f;
}

/* Pole wyszukiwania */
.search-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #2b3035;
  border-bottom: 1px solid #495057;
}

.search-wrapper {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #adb5bd;
  z-index: 1;
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 38px;
  padding: 0.5rem 0.75rem 0.5rem 2.5rem;
  background: #343a40;
  border: 1px solid #495057;
  color: #dee2e6;
  font-size: 1rem;
  border-radius: 4px;
}

.search-input:focus {
  border-color: #ffc107;
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.25);
}

.search-bar-spacer {
  flex: 1;
}

/* Button PDF - fioletowy */
:deep(.btn-pdf) {
  background: #6f42c1 !important;
  border-color: #6f42c1 !important;
  color: #fff !important;
}

:deep(.btn-pdf:hover) {
  background: #5a32a3 !important;
  border-color: #5a32a3 !important;
}

/* Grupa buttonów w tabeli */
.btn-group-inline {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* Style modali */
:deep(.p-dialog) {
  background: #2b3035;
  border: 1px solid #495057;
}

:deep(.p-dialog .p-dialog-header) {
  background: #343a40;
  color: #dee2e6;
  border-bottom: 1px solid #495057;
}

:deep(.p-dialog .p-dialog-content) {
  background: #2b3035;
  color: #dee2e6;
}

:deep(.p-dialog .p-dialog-footer) {
  background: #343a40;
  border-top: 1px solid #495057;
}

.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  margin-bottom: 0.5rem;
  color: #adb5bd;
  font-weight: 500;
}

:deep(.field .p-inputtext),
:deep(.field .p-inputtextarea) {
  width: 100%;
  background: #343a40;
  border: 1px solid #495057;
  color: #dee2e6;
}

:deep(.field .p-inputtext:disabled) {
  background: #212529;
  color: #6c757d;
}

.text-danger {
  color: #dc3545;
}

.mt-3 {
  margin-top: 1rem;
}

/* Podgląd PDF */
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
</style>

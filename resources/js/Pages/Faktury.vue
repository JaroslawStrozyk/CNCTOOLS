<template>
  <div class="faktury-page">
    <!-- Header -->
    <header class="app-header">
      <h2 class="header-title">FAKTURY</h2>
      <div class="header-buttons">
        <a :href="urls.ustawienia" class="btn btn-secondary">
          <i class="pi pi-cog"></i> Ustawienia
        </a>
        <a :href="urls.zamowienia" class="btn btn-success">
          <i class="pi pi-file"></i> Zamówienia
        </a>
        <a :href="urls.magazyn" class="btn btn-primary">
          <i class="pi pi-warehouse"></i> Magazyn
        </a>
        <a :href="urls.zakupy" class="btn btn-info">
          <i class="pi pi-truck"></i> Zakupy
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
        <div class="card-header">
          <h3>Zarządzaj Fakturami</h3>
          <Button
            icon="pi pi-plus"
            label="Dodaj nową"
            @click="openModal('add')"
          />
        </div>
        <div class="card-body">
          <ProgressSpinner v-if="isLoading" class="loading-spinner" />
          <div v-else>
            <DataTable
              :value="faktury"
              responsiveLayout="scroll"
              class="faktury-table"
              stripedRows
            >
              <template #empty>
                <div class="empty-message">Brak faktur.</div>
              </template>
              <Column field="numer_faktury" header="Numer faktury" />
              <Column field="data_wystawienia" header="Data wystawienia" />
              <Column header="Dostawca">
                <template #body="{ data }">
                  {{ data.dostawca?.nazwa_firmy }}
                </template>
              </Column>
              <Column header="Rozliczona" class="center-column">
                <template #body="{ data }">
                  <i v-if="data.rozliczone" class="pi pi-check-circle text-success"></i>
                  <i v-else class="pi pi-times-circle text-danger"></i>
                </template>
              </Column>
              <Column header="Plik" class="center-column">
                <template #body="{ data }">
                  <a
                    v-if="data.plik"
                    :href="data.plik"
                    target="_blank"
                    class="file-link"
                    title="Otwórz plik"
                  >
                    <i class="pi pi-file-pdf"></i>
                  </a>
                  <span v-else class="no-file">-</span>
                </template>
              </Column>
              <Column header="Akcje" class="actions-column">
                <template #body="{ data }">
                  <div class="action-buttons">
                    <Button
                      icon="pi pi-pencil"
                      severity="secondary"
                      size="small"
                      @click="openModal('edit', data)"
                    />
                    <Button
                      icon="pi pi-trash"
                      severity="danger"
                      size="small"
                      @click="showDeleteModal(data.id)"
                    />
                  </div>
                </template>
              </Column>
            </DataTable>

            <!-- Pagination -->
            <Paginator
              v-if="pagination.totalPages > 1"
              :rows="pagination.pageSize"
              :totalRecords="pagination.count"
              :first="(pagination.currentPage - 1) * pagination.pageSize"
              @page="onPageChange"
              class="faktury-paginator"
            />
          </div>
        </div>
      </div>
    </main>

    <!-- Modal dodawania/edycji -->
    <Dialog
      v-model:visible="modalVisible"
      :header="modal.title"
      :style="{ width: '500px' }"
      modal
    >
      <Message v-if="modal.errorMessage" severity="error" :closable="false">
        {{ modal.errorMessage }}
      </Message>

      <div class="form-field">
        <label class="required-label">Numer faktury</label>
        <InputText v-model="modal.currentItem.numer_faktury" class="w-full" />
      </div>

      <div class="form-field">
        <label class="required-label">Data wystawienia</label>
        <Calendar
          v-model="modal.currentItem.data_wystawienia_date"
          dateFormat="yy-mm-dd"
          class="w-full"
        />
      </div>

      <div class="form-field">
        <label class="required-label">Dostawca</label>
        <Dropdown
          v-model="modal.currentItem.dostawca_id"
          :options="dostawcy"
          optionLabel="nazwa_firmy"
          optionValue="id"
          placeholder="-- Wybierz dostawcę --"
          class="w-full"
        >
          <template #option="{ option }">
            {{ option.nazwa_firmy }} ({{ option.kod_dostawcy }})
          </template>
        </Dropdown>
      </div>

      <div class="form-field">
        <label>Plik faktury (PDF, obraz)</label>
        <input
          type="file"
          ref="fileInput"
          @change="handleFileUpload"
          accept=".pdf,image/*"
          class="file-input"
        />
        <small v-if="modal.mode === 'edit' && modal.currentItem.plik" class="current-file">
          Obecny plik:
          <a :href="modal.currentItem.plik" target="_blank">
            {{ getFileName(modal.currentItem.plik) }}
          </a>.
          Wybierz nowy, aby zastąpić.
        </small>
      </div>

      <div class="form-field checkbox-field">
        <Checkbox
          v-model="modal.currentItem.rozliczone"
          :binary="true"
          inputId="rozliczoneCheck"
        />
        <label for="rozliczoneCheck">Faktura rozliczona</label>
      </div>

      <template #footer>
        <Button
          label="Anuluj"
          severity="secondary"
          @click="modalVisible = false"
          :disabled="isSaving"
        />
        <Button
          v-if="!isSaving"
          label="Zapisz"
          @click="saveItem"
        />
        <Button
          v-else
          label="Zapisywanie..."
          :loading="true"
          disabled
        />
      </template>
    </Dialog>

    <!-- Modal usuwania -->
    <Dialog
      v-model:visible="deleteModalVisible"
      header="Potwierdź usunięcie"
      :style="{ width: '450px' }"
      modal
    >
      <p>Czy na pewno chcesz trwale usunąć tę fakturę?</p>
      <p class="text-danger">Tej operacji nie można cofnąć.</p>
      <p class="text-warning">Upewnij się, że żadne egzemplarze narzędzi nie są powiązane z tą fakturą przed usunięciem.</p>

      <template #footer>
        <Button label="Anuluj" severity="secondary" @click="deleteModalVisible = false" />
        <Button label="Tak, usuń" severity="danger" @click="confirmDeleteItem" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Calendar from 'primevue/calendar';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';
import Message from 'primevue/message';
import Paginator from 'primevue/paginator';
import ProgressSpinner from 'primevue/progressspinner';
import Menu from 'primevue/menu';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

const API_URL = '/api';
const baseUrl = `${API_URL}/faktury/`;

const props = defineProps({
  auth: Object,
  urls: Object,
  infoProgram: Object
});

// State
const faktury = ref([]);
const dostawcy = ref([]);
const isLoading = ref(false);
const isSaving = ref(false);

// Modal state
const modalVisible = ref(false);
const modal = ref({
  mode: 'add',
  title: '',
  currentItem: {},
  fileToUpload: null,
  errorMessage: ''
});

// Delete modal state
const deleteModalVisible = ref(false);
const idToDelete = ref(null);

// Pagination
const pagination = ref({
  count: 0,
  next: null,
  previous: null,
  currentPage: 1,
  totalPages: 1,
  pageSize: 100
});

// File input ref
const fileInput = ref(null);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
  { label: 'Wyloguj', icon: 'pi pi-sign-out', command: () => { window.location.href = props.urls?.logout || '/logout/'; } }
]);

const toggleUserMenu = (event) => {
  userMenu.value.toggle(event);
};

// Methods
const fetchDostawcy = async () => {
  try {
    const response = await axios.get(`${API_URL}/dostawcy/`);
    dostawcy.value = response.data;
  } catch (error) {
    console.error("Błąd podczas pobierania dostawców:", error);
    alert("Nie udało się pobrać listy dostawców.");
  }
};

const fetchFaktury = async (url = baseUrl, page = 1) => {
  isLoading.value = true;
  try {
    const urlObj = new URL(url, window.location.origin);
    urlObj.searchParams.set('page', page);
    urlObj.searchParams.set('page_size', pagination.value.pageSize);

    const response = await axios.get(urlObj.toString());
    faktury.value = response.data.results;
    updatePagination(response.data, page);
  } catch (error) {
    console.error("Błąd podczas pobierania faktur:", error);
    alert("Nie udało się pobrać listy faktur.");
  } finally {
    isLoading.value = false;
  }
};

const updatePagination = (data, currentPage) => {
  pagination.value.count = data.count;
  pagination.value.next = data.next;
  pagination.value.previous = data.previous;
  pagination.value.totalPages = Math.ceil(data.count / pagination.value.pageSize);
  pagination.value.currentPage = currentPage;
};

const onPageChange = (event) => {
  const page = event.page + 1;
  fetchFaktury(baseUrl, page);
};

const getInitialItem = () => ({
  numer_faktury: '',
  data_wystawienia_date: new Date(),
  dostawca_id: null,
  plik: null,
  rozliczone: false
});

const openModal = (mode, item = null) => {
  modal.value.mode = mode;
  modal.value.errorMessage = '';
  modal.value.fileToUpload = null;

  if (fileInput.value) {
    fileInput.value.value = '';
  }

  if (mode === 'add') {
    modal.value.title = 'Dodaj nową fakturę';
    modal.value.currentItem = getInitialItem();
  } else {
    modal.value.title = 'Edytuj fakturę';
    modal.value.currentItem = {
      ...item,
      dostawca_id: item.dostawca ? item.dostawca.id : null,
      data_wystawienia_date: item.data_wystawienia ? new Date(item.data_wystawienia) : new Date()
    };
  }
  modalVisible.value = true;
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  modal.value.fileToUpload = file || null;
};

const formatDateForApi = (date) => {
  if (!date) return '';
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const saveItem = async () => {
  isSaving.value = true;
  modal.value.errorMessage = '';

  const item = modal.value.currentItem;
  const dataWystawienia = formatDateForApi(item.data_wystawienia_date);

  if (!item.numer_faktury || !dataWystawienia || !item.dostawca_id) {
    modal.value.errorMessage = 'Pola: Numer faktury, Data wystawienia i Dostawca są wymagane.';
    isSaving.value = false;
    return;
  }

  const formData = new FormData();
  formData.append('numer_faktury', item.numer_faktury);
  formData.append('data_wystawienia', dataWystawienia);
  formData.append('dostawca_id', item.dostawca_id);
  formData.append('rozliczone', item.rozliczone);

  if (modal.value.fileToUpload) {
    formData.append('plik', modal.value.fileToUpload);
  }

  const method = modal.value.mode === 'add' ? 'post' : 'patch';
  const url = modal.value.mode === 'add' ? baseUrl : `${baseUrl}${item.id}/`;

  try {
    await axios({
      method: method,
      url: url,
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    modalVisible.value = false;
    await fetchFaktury(baseUrl, pagination.value.currentPage);
  } catch (error) {
    console.error("Błąd zapisu faktury:", error.response?.data);
    if (error.response?.data) {
      if (typeof error.response.data === 'object') {
        modal.value.errorMessage = Object.entries(error.response.data)
          .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
          .join('; ');
      } else {
        modal.value.errorMessage = error.response.data;
      }
    } else {
      modal.value.errorMessage = 'Wystąpił nieznany błąd podczas zapisu.';
    }
  } finally {
    isSaving.value = false;
  }
};

const showDeleteModal = (id) => {
  idToDelete.value = id;
  deleteModalVisible.value = true;
};

const confirmDeleteItem = async () => {
  if (!idToDelete.value) return;
  try {
    await axios.delete(`${baseUrl}${idToDelete.value}/`);
    deleteModalVisible.value = false;

    if (faktury.value.length === 1 && pagination.value.currentPage > 1) {
      await fetchFaktury(baseUrl, pagination.value.currentPage - 1);
    } else {
      await fetchFaktury(baseUrl, pagination.value.currentPage);
    }
  } catch (error) {
    console.error("Błąd usuwania faktury:", error);
    deleteModalVisible.value = false;
    alert('Nie można usunąć faktury. Sprawdź, czy nie jest powiązana z egzemplarzami narzędzi.');
  }
};

const getFileName = (url) => {
  if (!url) return '';
  return url.split('/').pop();
};

onMounted(async () => {
  await fetchDostawcy();
  await fetchFaktury();
});
</script>

<style scoped>
.faktury-page {
  min-height: 100vh;
  background-color: var(--dark-bg-primary);
  color: var(--dark-text-primary);
}

.main-content { padding: 1.5rem; }

.card {
  background: linear-gradient(to bottom, #343a40, #212529);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(to bottom, #3d444d, #343a40);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.card-header h3 { margin: 0; font-size: 1.25rem; color: #ffc107; }
.card-body { padding: 1.5rem; background: #212529; }
.empty-message { text-align: center; padding: 2rem; color: var(--dark-text-muted); }
.center-column { text-align: center; }
.actions-column { text-align: right; }
.action-buttons { display: flex; gap: 0.25rem; justify-content: flex-end; }
.file-link { color: #0d6efd; text-decoration: none; }
.file-link:hover { text-decoration: underline; color: #3d8bfd; }
.no-file { color: var(--dark-text-muted); }

.form-field { margin-bottom: 1rem; }
.form-field label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--dark-text-primary); }
.required-label::after { content: " *"; color: #dc3545; }
.w-full { width: 100%; }
.file-input { width: 100%; padding: 0.5rem; border: 1px solid var(--dark-border); border-radius: 4px; background: var(--dark-bg-tertiary); color: var(--dark-text-primary); }
.current-file { display: block; margin-top: 0.5rem; color: var(--dark-text-muted); }
.current-file a { color: #0d6efd; }
.checkbox-field { display: flex; align-items: center; gap: 0.5rem; }
.checkbox-field label { margin-bottom: 0; }
.faktury-paginator { margin-top: 1rem; justify-content: center; }
</style>

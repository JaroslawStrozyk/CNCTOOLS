<template>
  <div class="realizacja-page">
    <!-- Header -->
    <div class="header-bar">
      <h2 class="header-title"><span class="yellow-text">REALIZACJE ZAMÓWIEŃ</span></h2>
      <div class="header-buttons">
        <a :href="urls?.magazyn || '/magazyn/'" class="btn btn-danger">
          <i class="pi pi-arrow-left"></i> Wróć
        </a>
        <div class="dropdown-wrapper">
          <button class="user-dropdown-btn" @click="toggleUserMenu">
            <i class="pi pi-user"></i>
            {{ userName }}
            <i class="pi pi-chevron-down"></i>
          </button>
          <Menu ref="userMenu" :model="userMenuItems" :popup="true" />
        </div>
      </div>
    </div>

    <!-- Main content -->
    <main class="main-content">
      <div class="card">
        <div class="card-header">
          <h3>Lista realizacji do przyjęcia</h3>
        </div>
        <div class="card-body">
          <DataTable
            :value="realizacje"
            responsiveLayout="scroll"
            class="realizacje-table"
          >
            <template #empty>
              <div class="empty-message">Brak realizacji do przyjęcia</div>
            </template>
            <Column field="zamowienie.numer" header="Numer zamówienia">
              <template #body="{ data }">
                <strong class="order-number">{{ data.zamowienie?.numer }}</strong>
              </template>
            </Column>
            <Column field="zamowienie.dostawca.nazwa_firmy" header="Dostawca" />
            <Column header="Data utworzenia">
              <template #body="{ data }">
                {{ formatDate(data.data_realizacji) }}
              </template>
            </Column>
            <Column header="Pozycje">
              <template #body="{ data }">
                {{ data.pozycje?.length || 0 }}
              </template>
            </Column>
            <Column header="Akcje" class="actions-column">
              <template #body="{ data }">
                <div class="action-buttons">
                  <template v-if="!isRealizacjaZakonczona(data)">
                    <Button
                      icon="pi pi-inbox"
                      label="Przyjmij"
                      severity="info"
                      size="small"
                      class="shadow-btn"
                      @click="openPrzyjmijModal(data)"
                    />
                    <Button
                      icon="pi pi-trash"
                      severity="danger"
                      size="small"
                      class="shadow-btn"
                      @click="openDeleteModal(data)"
                    />
                  </template>
                  <Tag v-else value="Przyjęto" severity="success" />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </main>

    <!-- Modal przyjęcia towaru -->
    <Dialog
      v-model:visible="przyjmijDialogVisible"
      header="Przyjęcie towaru"
      :style="{ width: '900px' }"
      modal
      :closable="true"
    >
      <template #header>
        <div class="dialog-header-content">
          <i class="pi pi-inbox dialog-icon"></i>
          <span>Przyjęcie towaru - {{ selectedRealizacja?.zamowienie?.numer }}</span>
        </div>
      </template>

      <div v-if="selectedRealizacja" class="supplier-info">
        <p><strong>Dostawca:</strong> {{ selectedRealizacja.zamowienie?.dostawca?.nazwa_firmy }}</p>
      </div>

      <DataTable :value="selectedPozycje" class="przyjmij-table">
        <Column header="Przyjmij" class="checkbox-column">
          <template #body="{ data }">
            <Checkbox v-model="data.przyjmij" :binary="true" />
          </template>
        </Column>
        <Column field="pozycja_zamowienia.narzedzie_opis" header="Narzędzie" />
        <Column field="pozycja_zamowienia.numer_katalogowy" header="Nr katalogowy" />
        <Column header="Zamówiono" class="center-column">
          <template #body="{ data }">
            <strong>{{ data.pozycja_zamowienia?.ilosc_zamowiona }}</strong>
          </template>
        </Column>
        <Column header="Przyjęto" class="center-column">
          <template #body="{ data }">
            <InputNumber
              v-if="data.przyjmij"
              v-model="data.ilosc_przyjeta_input"
              :min="1"
              :max="data.pozycja_zamowienia?.ilosc_zamowiona"
              inputClass="quantity-input"
            />
            <span v-else>-</span>
          </template>
        </Column>
        <Column header="Lokalizacja">
          <template #body="{ data }">
            <span v-if="data.lokalizacja">
              {{ data.lokalizacja.szafa }}/{{ data.lokalizacja.polka }}/{{ data.lokalizacja.kolumna }}
            </span>
            <span v-else class="no-location">Brak domyślnej</span>
          </template>
        </Column>
      </DataTable>

      <Message v-if="przyjmijError" severity="error" class="error-message">
        {{ przyjmijError }}
      </Message>

      <template #footer>
        <Button label="Anuluj" severity="secondary" @click="przyjmijDialogVisible = false" />
        <Button
          label="Zatwierdź przyjęcie"
          icon="pi pi-check"
          severity="success"
          :loading="isPrzyjecieLoading"
          @click="zatwierdzPrzyjecie"
        />
      </template>
    </Dialog>

    <!-- Modal wyniku przyjęcia -->
    <Dialog
      v-model:visible="wynikDialogVisible"
      header="Przyjęcie potwierdzone"
      :style="{ width: '600px' }"
      modal
    >
      <template #header>
        <div class="dialog-header-success">
          <i class="pi pi-check-circle dialog-icon"></i>
          <span>Przyjęcie potwierdzone</span>
        </div>
      </template>

      <Message severity="success" :closable="false">
        <strong>Utworzono egzemplarze w magazynie:</strong>
      </Message>

      <DataTable :value="utworzoneEgzemplarze" class="wynik-table">
        <Column field="narzedzie" header="Narzędzie" />
        <Column header="Ilość" class="center-column">
          <template #body="{ data }">
            <strong>{{ data.ilosc }}</strong>
          </template>
        </Column>
        <Column field="lokalizacja" header="Lokalizacja" />
      </DataTable>

      <template #footer>
        <Button label="Zamknij" severity="secondary" @click="wynikDialogVisible = false" />
      </template>
    </Dialog>

    <!-- Modal usuwania -->
    <Dialog
      v-model:visible="deleteDialogVisible"
      header="Potwierdzenie usunięcia"
      :style="{ width: '450px' }"
      modal
    >
      <template #header>
        <div class="dialog-header-danger">
          <i class="pi pi-trash dialog-icon"></i>
          <span>Potwierdzenie usunięcia</span>
        </div>
      </template>

      <p>Czy na pewno chcesz usunąć tę realizację?</p>

      <Message severity="warn" :closable="false">
        <div class="delete-info">
          <p><strong>Numer zamówienia:</strong> {{ selectedDeleteRealizacja?.zamowienie?.numer }}</p>
          <p><strong>Dostawca:</strong> {{ selectedDeleteRealizacja?.zamowienie?.dostawca?.nazwa_firmy }}</p>
          <p><strong>Liczba pozycji:</strong> {{ selectedDeleteRealizacja?.pozycje?.length }}</p>
        </div>
      </Message>

      <template #footer>
        <Button label="Anuluj" severity="secondary" @click="deleteDialogVisible = false" />
        <Button
          label="Usuń"
          icon="pi pi-trash"
          severity="danger"
          :loading="isDeleting"
          @click="confirmDelete"
        />
      </template>
    </Dialog>

    <!-- Modal O programie -->
    <Dialog
      v-model:visible="aboutDialogVisible"
      header="O programie"
      :style="{ width: '450px' }"
      modal
    >
      <template #header>
        <div class="dialog-header-content">
          <i class="pi pi-info-circle dialog-icon"></i>
          <span>O programie</span>
        </div>
      </template>

      <div class="about-content">
        <div class="about-logo">
          <img :src="logoImage" alt="CNC Tools Logo" />
          <h4>CNC Tools</h4>
          <p class="subtitle">System zarządzania narzędziami CNC</p>
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
        <small class="copyright">© {{ infoProgram.FIRMA }} 2025</small>
        <Button label="Zamknij" severity="secondary" @click="aboutDialogVisible = false" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Menu from 'primevue/menu';
import Checkbox from 'primevue/checkbox';
import InputNumber from 'primevue/inputnumber';
import Message from 'primevue/message';
import Tag from 'primevue/tag';
import logoImage from '@images/cnc-logo.png';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

const API_URL = '/api';

const props = defineProps({
  auth: Object,
  urls: Object,
  infoProgram: Object
});

// State
const realizacje = ref([]);
const selectedRealizacja = ref(null);
const selectedPozycje = ref([]);
const selectedDeleteRealizacja = ref(null);
const isPrzyjecieLoading = ref(false);
const isDeleting = ref(false);
const przyjmijError = ref('');
const utworzoneEgzemplarze = ref([]);

// Dialog visibility
const przyjmijDialogVisible = ref(false);
const wynikDialogVisible = ref(false);
const deleteDialogVisible = ref(false);
const aboutDialogVisible = ref(false);

// User menu
const userMenu = ref(null);
const userName = computed(() => {
  if (props.auth?.user) {
    return `${props.auth.user.first_name} ${props.auth.user.last_name}`;
  }
  return 'Użytkownik';
});

const userMenuItems = ref([
  {
    label: 'O programie',
    icon: 'pi pi-info-circle',
    command: () => { aboutDialogVisible.value = true; }
  },
  { separator: true },
  {
    label: 'Wyjście',
    icon: 'pi pi-sign-out',
    command: () => { window.location.href = props.urls?.logout || '/logout/'; }
  }
]);

const toggleUserMenu = (event) => {
  userMenu.value.toggle(event);
};

// Methods
const fetchRealizacje = async () => {
  try {
    const response = await axios.get(`${API_URL}/realizacje/`);
    realizacje.value = response.data.results || response.data;
  } catch (error) {
    console.error("Błąd ładowania realizacji:", error);
  }
};

const openPrzyjmijModal = (realizacja) => {
  selectedRealizacja.value = realizacja;
  przyjmijError.value = '';

  selectedPozycje.value = realizacja.pozycje.map(poz => ({
    ...poz,
    przyjmij: false,
    ilosc_przyjeta_input: poz.pozycja_zamowienia?.ilosc_zamowiona || 0
  }));

  przyjmijDialogVisible.value = true;
};

const zatwierdzPrzyjecie = async () => {
  przyjmijError.value = '';

  const zaznaczone = selectedPozycje.value.filter(p => p.przyjmij);
  if (zaznaczone.length === 0) {
    przyjmijError.value = 'Zaznacz przynajmniej jedną pozycję do przyjęcia';
    return;
  }

  for (const poz of zaznaczone) {
    if (!poz.ilosc_przyjeta_input || poz.ilosc_przyjeta_input <= 0) {
      przyjmijError.value = 'Wszystkie zaznaczone pozycje muszą mieć ilość > 0';
      return;
    }
  }

  isPrzyjecieLoading.value = true;

  try {
    const pozycje_dane = zaznaczone.map(poz => ({
      id: poz.id,
      ilosc_przyjeta: poz.ilosc_przyjeta_input
    }));

    const response = await axios.post(
      `${API_URL}/realizacje/${selectedRealizacja.value.id}/zatwierdz/`,
      { pozycje: pozycje_dane }
    );

    if (response.data.success) {
      utworzoneEgzemplarze.value = response.data.utworzone_egzemplarze;
      przyjmijDialogVisible.value = false;
      wynikDialogVisible.value = true;
      await fetchRealizacje();
    }
  } catch (error) {
    console.error("Błąd zatwierdzania przyjęcia:", error);
    przyjmijError.value = error.response?.data?.error || 'Wystąpił błąd podczas zatwierdzania';
  } finally {
    isPrzyjecieLoading.value = false;
  }
};

const isRealizacjaZakonczona = (realizacja) => {
  if (!realizacja.pozycje || realizacja.pozycje.length === 0) {
    return false;
  }
  return realizacja.pozycje.every(poz => poz.ilosc_przyjeta > 0);
};

const openDeleteModal = (realizacja) => {
  selectedDeleteRealizacja.value = realizacja;
  deleteDialogVisible.value = true;
};

const confirmDelete = async () => {
  isDeleting.value = true;

  try {
    await axios.delete(`${API_URL}/realizacje/${selectedDeleteRealizacja.value.id}/`);
    deleteDialogVisible.value = false;
    await fetchRealizacje();
  } catch (error) {
    console.error("Błąd usuwania realizacji:", error);
    alert('Wystąpił błąd podczas usuwania realizacji');
  } finally {
    isDeleting.value = false;
  }
};

const goBack = () => {
  window.location.href = props.urls?.zamowienia || '/zamowienia-inertia/';
};

const formatDate = (dateString) => {
  if (!dateString) return '';

  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

onMounted(() => {
  fetchRealizacje();
});
</script>

<style scoped>
.realizacja-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--dark-bg-primary);
  color: var(--dark-text-primary);
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(to bottom, #343a40, #212529);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.header-title { margin: 0; font-weight: bold; color: white; }
.yellow-text { color: #ffc107; }
.header-actions { display: flex; gap: 0.5rem; align-items: center; }
.shadow-btn { box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.user-dropdown { position: relative; }

.main-content { flex: 1; padding: 1.5rem; overflow: auto; }

.card {
  background: linear-gradient(to bottom, #343a40, #212529);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  padding: 1rem 1.5rem;
  background: linear-gradient(to bottom, #3d444d, #343a40);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.card-header h3 { margin: 0; font-size: 1.25rem; color: #ffc107; }
.card-body { flex: 1; overflow: auto; padding: 0; background: #212529; }
.empty-message { text-align: center; padding: 2rem; color: var(--dark-text-muted); }
.order-number { color: #ffc107; }
.action-buttons { display: flex; gap: 0.5rem; justify-content: center; }
.actions-column { text-align: center; }

.dialog-header-content, .dialog-header-success, .dialog-header-danger { display: flex; align-items: center; gap: 0.5rem; }
.dialog-icon { font-size: 1.25rem; }
.dialog-header-success { color: #198754; }
.dialog-header-danger { color: #dc3545; }

.supplier-info { margin-bottom: 1rem; padding: 0.5rem; background: var(--dark-bg-tertiary); border-radius: 4px; }
.supplier-info p { margin: 0; }

.checkbox-column { width: 80px; text-align: center; }
.center-column { text-align: center; }
:deep(.quantity-input) { width: 80px; text-align: center; }
.no-location { color: var(--dark-text-muted); }
.error-message { margin-top: 1rem; }
.delete-info p { margin: 0.25rem 0; }

.about-content { text-align: center; }
.about-logo { margin-bottom: 1.5rem; }
.about-logo img { width: 80px; height: 80px; }
.about-logo h4 { margin: 1rem 0 0.25rem; font-weight: bold; color: #ffc107; }
.about-logo .subtitle { color: var(--dark-text-muted); margin: 0; }
.about-table { width: 100%; text-align: left; }
.about-table td { padding: 0.5rem; color: var(--dark-text-primary); }
.about-table .label { text-align: right; color: var(--dark-text-muted); width: 45%; }
.about-table .label i { margin-right: 0.5rem; }
.copyright { color: var(--dark-text-muted); margin-right: auto; }
</style>

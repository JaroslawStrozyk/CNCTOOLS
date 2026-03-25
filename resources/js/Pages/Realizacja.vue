<template>
  <div class="realizacja-page">
    <!-- Header -->
    <div class="header-bar">
      <h2 class="header-title"><span class="yellow-text">REALIZACJE ZAMÓWIEŃ</span></h2>
      <div class="header-buttons">
        <a :href="backUrl" class="btn btn-danger">
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
          <h3>Lista realizacji</h3>
        </div>
        <div class="card-body">
          <DataTable
            :value="realizacje"
            responsiveLayout="scroll"
            class="realizacje-table"
          >
            <template #empty>
              <div class="empty-message">Brak realizacji</div>
            </template>
            <Column field="zamowienie.numer" header="Numer zamówienia">
              <template #body="{ data }">
                <strong class="order-number">{{ data.zamowienie?.numer }}</strong>
              </template>
            </Column>
            <Column field="zamowienie.dostawca.nazwa_firmy" header="Dostawca" />
            <Column header="Data realizacji">
              <template #body="{ data }">
                {{ formatDate(data.data_realizacji) }}
              </template>
            </Column>
            <Column header="Pozycje" style="width: 80px; text-align: center;">
              <template #body="{ data }">
                {{ data.pozycje?.length || 0 }}
              </template>
            </Column>
            <Column header="Status" style="width: 160px; text-align: center;">
              <template #body="{ data }">
                <Tag v-if="isRealizacjaZakonczona(data)" value="Zrealizowane" severity="success" />
                <Tag v-else-if="hasCzesciowaPrzyjecie(data)" value="Częściowo" severity="warning" />
                <Tag v-else value="Oczekuje" severity="info" />
              </template>
            </Column>
            <Column header="Szczegóły" style="width: 100px; text-align: center;">
              <template #body="{ data }">
                <Button
                  icon="pi pi-eye"
                  severity="secondary"
                  size="small"
                  class="shadow-btn"
                  @click="openSzczegolyModal(data)"
                  title="Pokaż szczegóły"
                />
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </main>

    <!-- Modal szczegółów realizacji -->
    <Dialog
      v-model:visible="szczegolyDialogVisible"
      :style="{ width: '950px' }"
      modal
    >
      <template #header>
        <div class="dialog-header-content">
          <i class="pi pi-list dialog-icon"></i>
          <span>Szczegóły realizacji — {{ selectedRealizacja?.zamowienie?.numer }}</span>
        </div>
      </template>

      <div v-if="selectedRealizacja" class="szczegoly-info">
        <div class="info-grid">
          <p><strong>Dostawca:</strong> {{ selectedRealizacja.zamowienie?.dostawca?.nazwa_firmy }}</p>
          <p><strong>Data realizacji:</strong> {{ formatDate(selectedRealizacja.data_realizacji) }}</p>
          <p><strong>Status:</strong>
            <Tag v-if="isRealizacjaZakonczona(selectedRealizacja)" value="Zrealizowane" severity="success" />
            <Tag v-else-if="hasCzesciowaPrzyjecie(selectedRealizacja)" value="Częściowo zrealizowane" severity="warning" />
            <Tag v-else value="Oczekuje na przyjęcie" severity="info" />
          </p>
        </div>
      </div>

      <DataTable :value="selectedRealizacja?.pozycje || []" class="p-datatable-sm">
        <Column field="pozycja_zamowienia.narzedzie_opis" header="Narzędzie" />
        <Column field="pozycja_zamowienia.numer_katalogowy" header="Nr katalogowy" style="width: 140px;" />
        <Column header="Zamówiono" style="width: 100px; text-align: center;">
          <template #body="{ data }">
            <strong>{{ data.pozycja_zamowienia?.ilosc_zamowiona }}</strong>
          </template>
        </Column>
        <Column header="Przyjęto" style="width: 100px; text-align: center;">
          <template #body="{ data }">
            <span :class="przyjeteClass(data)">{{ data.ilosc_przyjeta || 0 }}</span>
          </template>
        </Column>
        <Column header="Lokalizacja" style="width: 140px;">
          <template #body="{ data }">
            <span v-if="data.lokalizacja">
              {{ data.lokalizacja.szafa }}/{{ data.lokalizacja.polka }}/{{ data.lokalizacja.kolumna }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </Column>
        <Column header="Status" style="width: 120px; text-align: center;">
          <template #body="{ data }">
            <Tag v-if="data.ilosc_przyjeta >= (data.pozycja_zamowienia?.ilosc_zamowiona || 0)" value="OK" severity="success" />
            <Tag v-else-if="data.ilosc_przyjeta > 0" value="Częściowo" severity="warning" />
            <Tag v-else value="Brak" severity="secondary" />
          </template>
        </Column>
      </DataTable>

      <div v-if="selectedRealizacja?.uwagi" class="uwagi-section">
        <strong>Uwagi:</strong> {{ selectedRealizacja.uwagi }}
      </div>

      <template #footer>
        <Button label="Zamknij" severity="secondary" @click="szczegolyDialogVisible = false" />
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

// Powrót na podstawie grupy użytkownika
const backUrl = computed(() => {
  const grupa = props.auth?.user?.grupa || '';
  if (grupa === 'logistyka') return props.urls?.zakupy || '/zakupy/';
  if (grupa === 'kierownik') return props.urls?.kierownik || '/kierownik/';
  // magazyn, produkcja-magazyn, administrator, brak grupy → magazyn
  return props.urls?.magazyn || '/magazyn/';
});

// State
const realizacje = ref([]);
const selectedRealizacja = ref(null);

// Dialog visibility
const szczegolyDialogVisible = ref(false);
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

const openSzczegolyModal = (realizacja) => {
  selectedRealizacja.value = realizacja;
  szczegolyDialogVisible.value = true;
};

const isRealizacjaZakonczona = (realizacja) => {
  if (!realizacja.pozycje || realizacja.pozycje.length === 0) return false;
  return realizacja.pozycje.every(poz =>
    poz.ilosc_przyjeta >= (poz.pozycja_zamowienia?.ilosc_zamowiona || 0)
  );
};

const hasCzesciowaPrzyjecie = (realizacja) => {
  if (!realizacja.pozycje || realizacja.pozycje.length === 0) return false;
  return realizacja.pozycje.some(poz => poz.ilosc_przyjeta > 0);
};

const przyjeteClass = (poz) => {
  const przyjeto = poz.ilosc_przyjeta || 0;
  const zamowiono = poz.pozycja_zamowienia?.ilosc_zamowiona || 0;
  if (przyjeto >= zamowiono) return 'text-green';
  if (przyjeto > 0) return 'text-orange';
  return '';
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
.shadow-btn { box-shadow: 0 2px 4px rgba(0,0,0,0.3); }

.header-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.header-buttons a {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
}

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

.dialog-header-content { display: flex; align-items: center; gap: 0.5rem; }
.dialog-icon { font-size: 1.25rem; }

.szczegoly-info {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.info-grid { display: flex; gap: 24px; flex-wrap: wrap; }
.info-grid p { margin: 0; display: flex; align-items: center; gap: 8px; }

.text-green { color: #69db7c; font-weight: 600; }
.text-orange { color: #ffa94d; font-weight: 600; }
.text-muted { color: #868e96; }

.uwagi-section {
  margin-top: 16px;
  padding: 10px 14px;
  background: rgba(255, 193, 7, 0.1);
  border-radius: 4px;
  border-left: 3px solid #ffc107;
}

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

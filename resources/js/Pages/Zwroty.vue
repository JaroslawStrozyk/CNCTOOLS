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
                <Badge :value="damagesUszkodzone.length" severity="danger" class="ml-2" />
              </template>
            <ProgressSpinner v-if="isLoading" class="loading-spinner" />
            <div v-else-if="damagesUszkodzone.length === 0" class="empty-state">
              <i class="pi pi-check-circle success-icon"></i>
              <p class="empty-title">Brak uszkodzonych elementów</p>
            </div>
            <DataTable
              v-else
              :value="damagesUszkodzone"
              responsiveLayout="scroll"
              class="damages-table"
              stripedRows
            >
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
            </DataTable>
            </TabPanel>

            <TabPanel>
              <template #header>
                <i class="pi pi-refresh mr-2"></i>
                <span>Uszkodzone do regeneracji</span>
                <Badge :value="damagesRegeneracja.length" style="background-color: #8B4513;" class="ml-2" />
              </template>
              <ProgressSpinner v-if="isLoading" class="loading-spinner" />
              <div v-else-if="damagesRegeneracja.length === 0" class="empty-state">
                <i class="pi pi-check-circle success-icon"></i>
                <p class="empty-title">Brak elementów do regeneracji</p>
              </div>
              <DataTable
                v-else
                :value="damagesRegeneracja"
                responsiveLayout="scroll"
                class="damages-table"
                stripedRows
              >
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
              </DataTable>
            </TabPanel>
          </TabView>
        </div>
      </div>
    </main>
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

const damagesRegeneracja = computed(() => {
  return damages.value.filter(d => d.stan_egzemplarza === 'Uszkodzone do regeneracji');
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
</style>

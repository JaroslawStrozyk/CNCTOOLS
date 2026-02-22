<template>
  <div class="zapotrzebowania-page">
    <!-- Header -->
    <header class="app-header">
      <h2 class="header-title">ZAPOTRZEBOWANIA</h2>
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
          <div v-if="isLoadingZapotrzebowania" class="loading-spinner">
            <ProgressSpinner />
          </div>
          <div v-else-if="zapotrzebowania.length === 0" class="empty-state">
            <i class="pi pi-check-circle success-icon"></i>
            <p class="empty-title">Brak wysłanych zapotrzebowań do realizacji</p>
          </div>
          <DataTable
            v-else
            :value="zapotrzebowania"
            :scrollable="true"
            scrollHeight="flex"
            v-model:expandedRows="expandedZapotrzebowania"
            dataKey="id"
            stripedRows
          >
            <Column :expander="true" style="width: 40px;" />
            <Column header="Numer">
              <template #body="{ data }">
                <strong>ZAM-{{ String(data.id).padStart(4, '0') }}</strong>
              </template>
            </Column>
            <Column header="Technolog">
              <template #body="{ data }">
                {{ data.technolog ? `${data.technolog.first_name} ${data.technolog.last_name}` : 'Nieznany' }}
              </template>
            </Column>
            <Column header="Data wysłania">
              <template #body="{ data }">
                <span v-html="formatCustomDate(data.data_wyslania)"></span>
              </template>
            </Column>
            <Column header="Pozycji" style="width: 80px; text-align: center;">
              <template #body="{ data }">
                <Badge :value="data.pozycje_count" />
              </template>
            </Column>
            <Column header="Akcje" style="width: 100px; text-align: center;">
              <template #body="{ data }">
                <Button
                  icon="pi pi-check"
                  class="p-button-success p-button-sm"
                  @click="zrealizujZapotrzebowanie(data.id)"
                  title="Zrealizuj zapotrzebowanie"
                />
              </template>
            </Column>
            <template #expansion="slotProps">
              <div class="expansion-content">
                <h5>Pozycje zapotrzebowania ZAM-{{ String(slotProps.data.id).padStart(4, '0') }}</h5>
                <DataTable :value="slotProps.data.pozycje" class="expansion-table">
                  <Column field="nr_klienta" header="Nr klienta">
                    <template #body="{ data }">{{ data.nr_klienta || '-' }}</template>
                  </Column>
                  <Column field="nr_zlecenia" header="Nr zlecenia">
                    <template #body="{ data }">{{ data.nr_zlecenia || '-' }}</template>
                  </Column>
                  <Column header="Kategoria">
                    <template #body="{ data }">
                      {{ data.kategoria_nazwa || '-' }} / {{ data.podkategoria_nazwa || '-' }}
                    </template>
                  </Column>
                  <Column field="specyfikacja" header="Specyfikacja">
                    <template #body="{ data }">{{ data.specyfikacja || '-' }}</template>
                  </Column>
                  <Column field="numer_katalogowy" header="Nr katalogowy">
                    <template #body="{ data }">{{ data.numer_katalogowy || '-' }}</template>
                  </Column>
                  <Column field="ilosc" header="Ilość" style="width: 60px; text-align: center;" />
                  <Column field="uwagi" header="Uwagi">
                    <template #body="{ data }">{{ data.uwagi || '-' }}</template>
                  </Column>
                </DataTable>
              </div>
            </template>
            <template #empty>
              <div class="empty-state">Brak wysłanych zapotrzebowań do realizacji.</div>
            </template>
          </DataTable>
        </div>
      </div>
    </main>

    <!-- Modal: O programie -->
    <Dialog v-model:visible="aboutModalVisible" header="O programie" :modal="true" :style="{ width: '450px' }">
      <div class="about-content">
        <div class="about-header">
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
          <small class="copyright">&copy; {{ infoProgram.FIRMA }} 2025</small>
          <Button label="Zamknij" class="btn-modal-secondary" @click="aboutModalVisible = false" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Badge from 'primevue/badge';
import ProgressSpinner from 'primevue/progressspinner';
import Menu from 'primevue/menu';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

const API_URL = '/api';

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
  }
});

// State
const zapotrzebowania = ref([]);
const expandedZapotrzebowania = ref([]);
const isLoadingZapotrzebowania = ref(false);
const aboutModalVisible = ref(false);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
  {
    label: 'Ustawienia',
    icon: 'pi pi-cog',
    command: () => { window.location.href = props.urls.ustawienia; }
  },
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

const fetchZapotrzebowania = async () => {
  isLoadingZapotrzebowania.value = true;
  try {
    const response = await axios.get(`${API_URL}/zapotrzebowania/lista_dla_magazynu/`);
    zapotrzebowania.value = response.data;
  } catch (error) {
    console.error("Błąd pobierania zapotrzebowań:", error.response?.data || error.message);
  } finally {
    isLoadingZapotrzebowania.value = false;
  }
};

const zrealizujZapotrzebowanie = async (id) => {
  if (!confirm('Czy na pewno chcesz oznaczyć to zapotrzebowanie jako zrealizowane?')) {
    return;
  }
  try {
    await axios.post(`${API_URL}/zapotrzebowania/${id}/zrealizuj/`);
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd realizacji zapotrzebowania:", error.response?.data || error.message);
    alert('Nie udało się zrealizować zapotrzebowania: ' + (error.response?.data?.error || error.message));
  }
};

onMounted(() => {
  fetchZapotrzebowania();
});
</script>

<style scoped>
.zapotrzebowania-page {
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
  padding: 0;
}

.empty-state { text-align: center; padding: 3rem; color: var(--dark-text-muted); }
.success-icon { font-size: 3rem; color: #198754; margin-bottom: 1rem; display: block; }
.empty-title { font-size: 1.25rem; margin: 0; }

.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 3rem;
}

/* === EXPANSION === */
.expansion-content {
  padding: 16px;
  background: rgba(52, 58, 64, 0.5);
  border-radius: 6px;
  margin: 8px 0;
}

.expansion-content h5 {
  color: var(--dark-text-primary);
  margin-bottom: 12px;
  font-size: 0.95rem;
}

.expansion-table {
  font-size: 0.85rem;
}

:deep(.expansion-table .p-datatable-tbody > tr > td) {
  padding: 6px 8px;
  background: transparent;
}

:deep(.expansion-table .p-datatable-thead > tr > th) {
  padding: 8px;
  background: var(--dark-bg-tertiary);
  font-size: 0.8rem;
}

/* About modal */
.about-content {
  text-align: center;
}

.about-header {
  margin-bottom: 1.5rem;
}

.about-header h4 {
  margin: 0.5rem 0 0.25rem;
  color: #ffc107;
}

.about-header .text-muted {
  color: #adb5bd;
  margin: 0;
}

.about-table {
  width: 100%;
  text-align: left;
}

.about-table td {
  padding: 6px 8px;
  color: #dee2e6;
}

.about-table td.label {
  color: #adb5bd;
  white-space: nowrap;
  width: 160px;
}

.about-table a {
  color: #ffc107;
  text-decoration: none;
}

.about-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.copyright {
  color: #6c757d;
}
</style>

<!-- Style dla menu popup (bez scoped - menu jest renderowane jako portal) -->
<style>
#user_menu {
  min-width: 180px !important;
  background: #2d3238 !important;
  border: 1px solid #495057 !important;
  border-radius: 6px !important;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.5) !important;
  padding: 6px 0 !important;
}

#user_menu_list {
  padding: 0 !important;
  margin: 0 !important;
  list-style: none !important;
}

#user_menu_list li {
  margin: 0 !important;
  padding: 0 !important;
}

#user_menu_list li > div {
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  border-radius: 0 !important;
  cursor: pointer !important;
  transition: background-color 0.15s !important;
}

#user_menu_list li > div:hover {
  background-color: #3d444d !important;
}

#user_menu_list li > div > a,
#user_menu_list li > div > div {
  display: flex !important;
  align-items: center !important;
  padding: 10px 16px !important;
  color: #dee2e6 !important;
  text-decoration: none !important;
  gap: 10px !important;
  cursor: pointer !important;
}

#user_menu_list li > div span[class*="icon"],
#user_menu_list li > div i,
#user_menu_list li > div .pi {
  color: #adb5bd !important;
  font-size: 1rem !important;
}

#user_menu_list li > div span:not([class*="icon"]):not(.pi) {
  color: #dee2e6 !important;
  font-size: 14px !important;
}

#user_menu li[data-pc-section="separator"] {
  border: none !important;
  border-top: 1px solid #495057 !important;
  margin: 6px 0 !important;
  padding: 0 !important;
  height: 0 !important;
}

/* === MODALE PRIMEVUE - CIEMNY MOTYW === */
.p-dialog-mask {
  background-color: rgba(0, 0, 0, 0.6) !important;
  backdrop-filter: blur(2px);
}

.p-dialog {
  background: #2d3238 !important;
  border: 1px solid #495057 !important;
  border-radius: 8px !important;
  color: #dee2e6 !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
  overflow: hidden;
}

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

.p-dialog .p-dialog-content {
  background: #2d3238 !important;
  color: #dee2e6 !important;
  padding: 20px !important;
}

.p-dialog .p-dialog-footer {
  background: #343a40 !important;
  border-top: 1px solid #495057 !important;
  padding: 12px 20px !important;
}

.btn-modal-secondary {
  background: #6c757d !important;
  border-color: #6c757d !important;
  color: #fff !important;
}

.btn-modal-secondary:hover {
  background: #5c636a !important;
  border-color: #565e64 !important;
}
</style>

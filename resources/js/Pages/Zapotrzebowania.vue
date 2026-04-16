<template>
  <div class="zapotrzebowania-page">
    <!-- Header -->
    <header class="app-header">
      <h2 class="header-title">ZAPOTRZEBOWANIA</h2>
      <div class="header-buttons">
        <a v-if="canAddZapotrzebowanie" :href="addUrl" class="btn btn-success" title="Dodaj zapotrzebowanie">
          <i class="pi pi-plus"></i> Dodaj
        </a>
        <a :href="backUrl" class="btn btn-primary">
          <i :class="backIcon"></i> {{ backLabel }}
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
          <DataTable
            :value="zapotrzebowania"
            :loading="isLoadingZapotrzebowania"
            :scrollable="true"
            scrollHeight="flex"
            v-model:expandedRows="expandedZapotrzebowania"
            dataKey="id"
            stripedRows
            :rowClass="rowClassZap"
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
            <Column header="Status" style="width: 140px; text-align: center;">
              <template #body="{ data }">
                <Tag v-if="data.status === 'ordered'" value="W zamówieniu" severity="info" icon="pi pi-shopping-cart" />
                <Tag v-else-if="data.status === 'completed'" value="Zatwierdzone" severity="success" icon="pi pi-check" />
                <Tag v-else value="Nowe" severity="warning" icon="pi pi-clock" />
              </template>
            </Column>
            <Column header="Pozycji" style="width: 80px; text-align: center;">
              <template #body="{ data }">
                <Badge :value="data.pozycje_count" />
              </template>
            </Column>
            <Column header="Akcje" style="width: 160px; text-align: center;">
              <template #body="{ data }">
                <div class="btn-group-inline">
                  <template v-if="data.status === 'submitted'">
                    <Button
                      icon="pi pi-check"
                      class="p-button-success p-button-sm"
                      @click="openRealizujModal(data)"
                      title="Zatwierdź zapotrzebowanie"
                    />
                    <Button
                      icon="pi pi-trash"
                      class="p-button-danger p-button-sm"
                      @click="usunZapotrzebowanie(data)"
                      title="Usuń zapotrzebowanie"
                    />
                  </template>
                  <template v-else>
                    <Button
                      icon="pi pi-undo"
                      class="p-button-warning p-button-sm"
                      @click="cofnijZapotrzebowanie(data)"
                      title="Cofnij zatwierdzenie"
                      :loading="cofanieId === data.id"
                    />
                  </template>
                </div>
              </template>
            </Column>
            <template #expansion="slotProps">
              <div class="expansion-content">
                <h5>Pozycje zapotrzebowania ZAM-{{ String(slotProps.data.id).padStart(4, '0') }}</h5>
                <DataTable :value="slotProps.data.pozycje" class="expansion-table" dataKey="id">
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
                  <Column header="Ilość" style="width: 80px; text-align: center;">
                    <template #body="{ data }">
                      <strong>{{ data.ilosc }}</strong>
                    </template>
                  </Column>
                  <Column field="uwagi" header="Uwagi">
                    <template #body="{ data }">{{ data.uwagi || '-' }}</template>
                  </Column>
                  <Column header="" style="width: 50px; text-align: center;">
                    <template #body="{ data }">
                      <i v-if="data.w_zamowieniu" class="pi pi-shopping-cart" style="color: #4dabf7;" title="W zamówieniu"></i>
                    </template>
                  </Column>
                  <Column v-if="slotProps.data.status === 'submitted'" header="Akcje" style="width: 100px; text-align: center;">
                    <template #body="{ data: pozycja }">
                      <div class="btn-group-inline">
                        <Button
                          icon="pi pi-pencil"
                          class="p-button-secondary p-button-sm"
                          @click="openEditPozycja(pozycja, slotProps.data)"
                          title="Edytuj pozycję"
                        />
                        <Button
                          icon="pi pi-trash"
                          class="p-button-danger p-button-sm"
                          @click="usunPozycje(pozycja, slotProps.data)"
                          title="Usuń pozycję"
                        />
                      </div>
                    </template>
                  </Column>
                </DataTable>
              </div>
            </template>
            <template #empty>
              <div class="empty-state">
                <i class="pi pi-check-circle success-icon"></i>
                <p class="empty-title">Brak zapotrzebowań</p>
              </div>
            </template>
          </DataTable>
        </div>
      </div>
    </main>

    <!-- Modal: Edycja pozycji -->
    <Dialog v-model:visible="editModalVisible" header="Edytuj pozycję zapotrzebowania" :modal="true" :style="{ width: '550px' }">
      <div class="p-fluid" v-if="editData">
        <div class="field">
          <label>Kategoria</label>
          <Dropdown
            v-model="editData.selectedKategoriaId"
            :options="kategorieOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Wybierz kategorię"
            filter
            :filterPlaceholder="'Szukaj...'"
            showClear
            @change="onEditKategoriaChange"
          />
        </div>
        <div class="field">
          <label>Podkategoria</label>
          <Dropdown
            v-model="editData.selectedPodkategoriaId"
            :options="editPodkategorieOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Wybierz podkategorię"
            filter
            :filterPlaceholder="'Szukaj...'"
            showClear
            :disabled="!editData.selectedKategoriaId"
            @change="onEditPodkategoriaChange"
          />
        </div>
        <div class="field">
          <label>Specyfikacja</label>
          <InputText v-model="editData.specyfikacja" />
        </div>
        <div class="field">
          <label>Nr katalogowy</label>
          <InputText v-model="editData.numer_katalogowy" />
        </div>
        <div class="field-row">
          <div class="field">
            <label>Nr klienta</label>
            <InputText v-model="editData.nr_klienta" />
          </div>
          <div class="field">
            <label>Nr zlecenia</label>
            <InputText v-model="editData.nr_zlecenia" />
          </div>
        </div>
        <div class="field">
          <label>Ilość</label>
          <InputNumber v-model="editData.ilosc" :min="1" showButtons />
        </div>
        <div class="field">
          <label>Uwagi</label>
          <Textarea v-model="editData.uwagi" rows="3" />
        </div>
      </div>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="editModalVisible = false" />
        <Button label="Zapisz" icon="pi pi-check" @click="saveEditPozycja" :loading="isSaving" />
      </template>
    </Dialog>

    <!-- Modal: Potwierdzenie realizacji -->
    <Dialog v-model:visible="realizujModalVisible" header="Zatwierdź zapotrzebowanie" :modal="true" :style="{ width: '500px' }">
      <div v-if="realizujData">
        <p>Czy na pewno zatwierdzić zapotrzebowanie:</p>
        <p class="confirm-numer">ZAM-{{ String(realizujData.id).padStart(4, '0') }}</p>
        <p>Technolog: <strong>{{ realizujData.technolog ? `${realizujData.technolog.first_name} ${realizujData.technolog.last_name}` : 'Nieznany' }}</strong></p>
        <p>Liczba pozycji: <strong>{{ realizujData.pozycje_count || realizujData.pozycje?.length || 0 }}</strong></p>
        <p class="confirm-info">
          <i class="pi pi-info-circle"></i>
          Pozycje zostaną oznaczone jako gotowe do zamówienia i będą widoczne w generatorze zamówień.
        </p>
      </div>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="realizujModalVisible = false" />
        <Button label="Zatwierdź" icon="pi pi-check" class="p-button-success" @click="confirmRealizuj" :loading="realizowanieId === realizujData?.id" />
      </template>
    </Dialog>

    <!-- Modal: Potwierdzenie usunięcia zapotrzebowania -->
    <Dialog v-model:visible="deleteZapModalVisible" header="Usuń zapotrzebowanie" :modal="true" :style="{ width: '450px' }">
      <div v-if="deleteZapData">
        <p>Czy na pewno usunąć zapotrzebowanie:</p>
        <p class="confirm-numer">ZAM-{{ String(deleteZapData.id).padStart(4, '0') }}</p>
        <p class="confirm-info" style="background: rgba(220, 53, 69, 0.15); border-color: rgba(220, 53, 69, 0.3); color: #ea868f;">
          <i class="pi pi-exclamation-triangle"></i>
          Tej operacji nie można cofnąć. Wszystkie pozycje zapotrzebowania zostaną usunięte.
        </p>
      </div>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteZapModalVisible = false" />
        <Button label="Usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteZap" :loading="isDeletingZap" />
      </template>
    </Dialog>

    <!-- Modal: Potwierdzenie usunięcia pozycji -->
    <Dialog v-model:visible="deletePozModalVisible" header="Usuń pozycję" :modal="true" :style="{ width: '450px' }">
      <div v-if="deletePozData">
        <p>Czy na pewno usunąć pozycję:</p>
        <p class="confirm-numer">{{ deletePozData.specyfikacja || deletePozData.numer_katalogowy || `ID: ${deletePozData.id}` }}</p>
      </div>
      <template #footer>
        <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deletePozModalVisible = false" />
        <Button label="Usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDeletePoz" :loading="isDeletingPoz" />
      </template>
    </Dialog>

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
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Badge from 'primevue/badge';
import Tag from 'primevue/tag';
import Menu from 'primevue/menu';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';

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
      zakupy: '/zakupy/',
      ustawienia: '/ustawienia/',
      zapotrzebowania: '/zapotrzebowania/',
      technologia: '/technologia/',
      logout: '/logout/'
    })
  },
  infoProgram: {
    type: Object,
    default: () => ({})
  }
});

// Powrót — skąd przyszedł użytkownik
const fromParam = new URLSearchParams(window.location.search).get('from');
const backUrl = fromParam === 'zakupy' ? (props.urls.zakupy || '/zakupy/') : (props.urls.magazyn || '/magazyn/');
const backLabel = fromParam === 'zakupy' ? 'Zakupy' : 'Magazyn';
const backIcon = fromParam === 'zakupy' ? 'pi pi-truck' : 'pi pi-warehouse';

// "Dodaj" — tylko dla grup administrator / logistyka / magazyn (NIE technologia)
const canAddZapotrzebowanie = computed(() => {
  const grupa = props.auth.user.grupa;
  return ['administrator', 'logistyka', 'magazyn'].includes(grupa);
});

const addUrl = computed(() => {
  const base = props.urls.technologia || '/technologia/';
  const params = new URLSearchParams();
  params.set('from', 'zapotrzebowania');
  if (fromParam) {
    params.set('origin', fromParam);
  }
  return `${base}?${params.toString()}`;
});

// State
const zapotrzebowania = ref([]);
const expandedZapotrzebowania = ref([]);
const isLoadingZapotrzebowania = ref(true);
const aboutModalVisible = ref(false);
const realizowanieId = ref(null);
const cofanieId = ref(null);

// Modal realizacji
const realizujModalVisible = ref(false);
const realizujData = ref(null);

// Edycja pozycji
const editModalVisible = ref(false);
const editData = ref(null);
const editParentZap = ref(null);
const isSaving = ref(false);

// Kategorie/podkategorie
const kategorie = ref([]);

// Usuwanie — modale
const deleteZapModalVisible = ref(false);
const deleteZapData = ref(null);
const isDeletingZap = ref(false);
const deletePozModalVisible = ref(false);
const deletePozData = ref(null);
const deletePozParent = ref(null);
const isDeletingPoz = ref(false);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
  {
    label: 'Ustawienia',
    icon: 'pi pi-cog',
    command: () => { window.location.href = props.urls.ustawienia + '?from=zapotrzebowania' + (fromParam ? '&origin=' + fromParam : ''); }
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

const rowClassZap = (data) => {
  return data.status === 'completed' ? 'row-completed' : '';
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

// Realizacja — modal
const openRealizujModal = (zap) => {
  realizujData.value = zap;
  realizujModalVisible.value = true;
};

const confirmRealizuj = async () => {
  if (!realizujData.value) return;
  realizowanieId.value = realizujData.value.id;
  try {
    await axios.post(`${API_URL}/zapotrzebowania/${realizujData.value.id}/zrealizuj/`);
    realizujModalVisible.value = false;
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd zatwierdzania:", error.response?.data || error.message);
    alert('Nie udało się zatwierdzić zapotrzebowania: ' + (error.response?.data?.error || error.message));
  } finally {
    realizowanieId.value = null;
  }
};

// Cofnij zatwierdzenie
const cofnijZapotrzebowanie = async (zap) => {
  cofanieId.value = zap.id;
  try {
    await axios.post(`${API_URL}/zapotrzebowania/${zap.id}/cofnij/`);
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd cofania:", error.response?.data || error.message);
    alert('Nie udało się cofnąć zatwierdzenia: ' + (error.response?.data?.error || error.message));
  } finally {
    cofanieId.value = null;
  }
};

const usunZapotrzebowanie = (zap) => {
  deleteZapData.value = zap;
  deleteZapModalVisible.value = true;
};

const confirmDeleteZap = async () => {
  if (!deleteZapData.value) return;
  isDeletingZap.value = true;
  try {
    await axios.delete(`${API_URL}/zapotrzebowania/${deleteZapData.value.id}/`);
    deleteZapModalVisible.value = false;
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd usuwania zapotrzebowania:", error.response?.data || error.message);
    alert('Nie udało się usunąć zapotrzebowania: ' + (error.response?.data?.error || error.message));
  } finally {
    isDeletingZap.value = false;
  }
};

// Kategorie — computed options
const kategorieOptions = computed(() => {
  return kategorie.value.map(k => ({ label: k.nazwa, value: k.id }));
});

const editPodkategorieOptions = computed(() => {
  if (!editData.value?.selectedKategoriaId) return [];
  const kat = kategorie.value.find(k => k.id === editData.value.selectedKategoriaId);
  if (!kat) return [];
  return (kat.podkategorie || []).map(p => ({ label: p.nazwa, value: p.id }));
});

const onEditKategoriaChange = () => {
  if (!editData.value) return;
  editData.value.selectedPodkategoriaId = null;
  editData.value.podkategoria_nazwa = '';
  // Ustaw nazwę kategorii
  const kat = kategorie.value.find(k => k.id === editData.value.selectedKategoriaId);
  editData.value.kategoria_nazwa = kat ? kat.nazwa : '';
};

const onEditPodkategoriaChange = () => {
  if (!editData.value) return;
  const kat = kategorie.value.find(k => k.id === editData.value.selectedKategoriaId);
  if (kat) {
    const pod = (kat.podkategorie || []).find(p => p.id === editData.value.selectedPodkategoriaId);
    editData.value.podkategoria_nazwa = pod ? pod.nazwa : '';
  }
};

const fetchKategorie = async () => {
  try {
    const response = await axios.get(`${API_URL}/kategorie/`);
    kategorie.value = response.data;
  } catch (error) {
    console.error("Błąd ładowania kategorii:", error.response?.data || error.message);
  }
};

// Edycja pozycji
const openEditPozycja = (pozycja, parentZap) => {
  const data = { ...pozycja };
  // Dopasuj kategoria/podkategoria do ID na podstawie nazw
  let katId = null;
  let podId = null;
  if (pozycja.kategoria_nazwa) {
    const kat = kategorie.value.find(k => k.nazwa === pozycja.kategoria_nazwa);
    if (kat) {
      katId = kat.id;
      if (pozycja.podkategoria_nazwa) {
        const pod = (kat.podkategorie || []).find(p => p.nazwa === pozycja.podkategoria_nazwa);
        if (pod) podId = pod.id;
      }
    }
  }
  data.selectedKategoriaId = katId;
  data.selectedPodkategoriaId = podId;
  editData.value = data;
  editParentZap.value = parentZap;
  editModalVisible.value = true;
};

const saveEditPozycja = async () => {
  if (!editData.value) return;
  isSaving.value = true;
  try {
    await axios.patch(`${API_URL}/pozycje-zapotrzebowan/${editData.value.id}/`, {
      kategoria_nazwa: editData.value.kategoria_nazwa,
      podkategoria_nazwa: editData.value.podkategoria_nazwa,
      specyfikacja: editData.value.specyfikacja,
      numer_katalogowy: editData.value.numer_katalogowy,
      nr_klienta: editData.value.nr_klienta,
      nr_zlecenia: editData.value.nr_zlecenia,
      ilosc: editData.value.ilosc,
      uwagi: editData.value.uwagi
    });
    editModalVisible.value = false;
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd zapisu pozycji:", error.response?.data || error.message);
    alert('Nie udało się zapisać zmian.');
  } finally {
    isSaving.value = false;
  }
};

const usunPozycje = (pozycja, parentZap) => {
  deletePozData.value = pozycja;
  deletePozParent.value = parentZap;
  deletePozModalVisible.value = true;
};

const confirmDeletePoz = async () => {
  if (!deletePozData.value) return;
  isDeletingPoz.value = true;
  try {
    await axios.delete(`${API_URL}/pozycje-zapotrzebowan/${deletePozData.value.id}/`);
    deletePozModalVisible.value = false;
    await fetchZapotrzebowania();
  } catch (error) {
    console.error("Błąd usuwania pozycji:", error.response?.data || error.message);
    alert('Nie udało się usunąć pozycji.');
  } finally {
    isDeletingPoz.value = false;
  }
};

onMounted(() => {
  fetchZapotrzebowania();
  fetchKategorie();
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

/* === BUTTONY INLINE === */
.btn-group-inline {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* === WIERSZ ZATWIERDZONY === */
:deep(.row-completed) {
  opacity: 0.7;
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

/* === MODAL EDYCJI === */
.field {
  margin-bottom: 1rem;
}

.field label {
  display: block;
  margin-bottom: 0.5rem;
  color: #adb5bd;
  font-weight: 500;
}

.field-row {
  display: flex;
  gap: 1rem;
}

.field-row .field {
  flex: 1;
}

:deep(.field .p-inputtext),
:deep(.field .p-inputtextarea),
:deep(.field .p-inputnumber) {
  width: 100%;
}

:deep(.field .p-inputtext),
:deep(.field .p-inputtextarea),
:deep(.field .p-inputnumber-input) {
  background: #343a40;
  border: 1px solid #495057;
  color: #dee2e6;
}

:deep(.field .p-inputtext:disabled) {
  background: #212529;
  color: #6c757d;
}

:deep(.field .p-inputnumber-button) {
  background: #495057;
  border-color: #495057;
  color: #dee2e6;
}

:deep(.field .p-inputnumber-button:hover) {
  background: #5c636a;
  border-color: #5c636a;
}

/* === MODAL POTWIERDZENIA === */
.confirm-numer {
  font-size: 1.3rem;
  font-weight: 700;
  color: #ffc107;
  margin: 8px 0;
}

.confirm-info {
  margin-top: 16px;
  padding: 10px 14px;
  background: rgba(25, 135, 84, 0.15);
  border: 1px solid rgba(25, 135, 84, 0.3);
  border-radius: 6px;
  color: #75b798;
  font-size: 0.9rem;
}

.confirm-info i {
  margin-right: 6px;
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

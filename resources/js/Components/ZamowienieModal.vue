<template>
    <!--
        Wspólny modal zamówienia — zastępuje dawne „Szczegóły zamówienia” (klik w numer)
        i „Realizację / Kontynuuj realizację” (przycisk 📦). Zakres zależy od statusu:
          draft / pending_approval / verified → edycja ilości i cen, usuwanie pozycji
          sent / partially_received          → przyjęcie i odpisanie towaru + edycja cen
          completed                          → tylko odczyt (z historią przyjęć)
        Magazynier (bez logistyki) nie edytuje cen.
    -->
    <Dialog :visible="visible" @update:visible="zamknij" :header="tytul" :modal="true"
            :style="{ width: '1800px', maxWidth: '96vw' }">
        <div v-if="isLoading" class="loading-state">
            <i class="pi pi-spin pi-spinner" style="font-size: 2rem;"></i>
            <p>Ładowanie danych zamówienia...</p>
        </div>

        <div v-else-if="zamowienie" class="order-details">
            <div class="details-grid">
                <div class="details-left">
                    <p><strong>Dostawca:</strong> {{ zamowienie.dostawca?.nazwa_firmy }}</p>
                    <p><strong>Data utworzenia:</strong> {{ formatDate(zamowienie.data_utworzenia) }}</p>
                    <p><strong>Data wysłania:</strong> {{ zamowienie.data_wyslania ? formatDate(zamowienie.data_wyslania) : 'Nie wysłano' }}</p>
                </div>
                <div class="details-right">
                    <p><strong>Status:</strong> <Tag :severity="getStatusSeverity(zamowienie.status)" :value="getStatusLabel(zamowienie.status)" :class="getStatusTagClass(zamowienie.status)" /></p>
                    <p><strong>Wartość:</strong> {{ wartoscZamowienia }} zł</p>
                    <p><strong>Email:</strong> {{ zamowienie.email_docelowy || 'brak' }}</p>
                    <p v-if="auth?.isLogistyka" style="margin-top: 5px;">
                        <strong>Nr oferty dostawcy:</strong>
                        <InputText v-if="edycjaPozycji" v-model="zamowienie.nr_oferty_dostawcy" style="width: 240px; margin-left: 8px;" />
                        <span v-else>{{ zamowienie.nr_oferty_dostawcy || 'brak' }}</span>
                    </p>
                </div>
            </div>

            <div class="pozycje-header mt-4 mb-3">
                <h6>Pozycje zamówienia:</h6>
                <label v-if="trybRealizacji" class="select-all-label">
                    <Checkbox v-model="zaznaczWszystkie" :binary="true" @change="toggleSelectAll" />
                    <span>Zaznacz wszystkie (pełna realizacja)</span>
                </label>
            </div>

            <DataTable :value="pozycje" :scrollable="true" scrollHeight="400px" class="p-datatable-sm" dataKey="id">
                <Column field="kategoria_nazwa" header="Kategoria" />
                <Column field="podkategoria_nazwa" header="Podkategoria" />
                <Column field="narzedzie_opis" header="Narzędzie" />
                <Column field="numer_katalogowy" header="Nr katalogowy" />
                <Column header="Zamówiono" style="width: 100px; text-align: center;">
                    <template #body="{ data }">
                        <InputNumber v-if="edycjaPozycji" v-model="data.ilosc_zamowiona" :min="1"
                                     :inputStyle="{ width: '60px', textAlign: 'center' }" />
                        <strong v-else>{{ data.ilosc_zamowiona }}</strong>
                    </template>
                </Column>
                <Column header="Jednostka" style="width: 120px;">
                    <template #body="{ data }">
                        {{ data.jednostka === 'kompl' ? `kompl. (${data.ilosc_w_komplecie} szt.)` : 'szt.' }}
                    </template>
                </Column>
                <Column v-if="pokazStanRealizacji" header="Przyjęto" style="width: 130px; text-align: center;">
                    <template #body="{ data }">
                        <div v-if="trybRealizacji && data.ilosc_pozostala > 0 && !data.odpisz">
                            <InputNumber v-model="data.ilosc_do_przyjecia" :min="0"
                                         inputClass="qty-input" :inputStyle="{ width: '70px', textAlign: 'center' }" />
                            <div v-if="data.ilosc_przyjeta > 0" class="text-muted" style="font-size: 0.72rem; margin-top: 2px;">już przyjęto: {{ data.ilosc_przyjeta }}</div>
                            <div v-if="data.ilosc_do_przyjecia > data.ilosc_pozostala" class="text-orange" style="font-size: 0.72rem; margin-top: 2px;">
                                nadwyżka +{{ data.ilosc_do_przyjecia - data.ilosc_pozostala }}
                            </div>
                        </div>
                        <span v-else-if="data.ilosc_pozostala === 0" class="text-green">
                            {{ data.ilosc_przyjeta }} ✓
                            <span v-if="data.ilosc_przyjeta > data.ilosc_zamowiona" class="text-orange" title="Przyjęto więcej niż zamówiono">(+{{ data.ilosc_przyjeta - data.ilosc_zamowiona }})</span>
                        </span>
                        <span v-else-if="!trybRealizacji">{{ data.ilosc_przyjeta }}</span>
                        <span v-else class="text-muted">-</span>
                    </template>
                </Column>
                <Column v-if="pokazStanRealizacji" header="Pozostało" style="width: 90px; text-align: center;">
                    <template #body="{ data }">
                        <span :class="{ 'text-orange': data.ilosc_pozostala > 0, 'text-green': data.ilosc_pozostala === 0 }">
                            {{ data.ilosc_pozostala }}
                        </span>
                    </template>
                </Column>
                <Column v-if="trybRealizacji" header="Odpisz" style="width: 80px; text-align: center;">
                    <template #body="{ data }">
                        <Checkbox v-if="data.ilosc_pozostala > 0" v-model="data.odpisz" :binary="true"
                                  @change="onOdpiszToggle(data)" title="Skasuj pozycję z zamówienia (wróci do generatora)" />
                        <span v-else class="text-muted">-</span>
                    </template>
                </Column>
                <Column header="Cena jedn." style="width: 120px; text-align: right;">
                    <template #body="{ data }">
                        <InputNumber v-if="edycjaCeny" v-model="data.cena_jednostkowa" :minFractionDigits="2" :maxFractionDigits="2"
                                     :min="0" :inputStyle="{ width: '80px', textAlign: 'right' }" />
                        <span v-else>{{ Number(data.cena_jednostkowa || 0).toFixed(2) }} zł</span>
                    </template>
                </Column>
                <Column header="Wartość" style="width: 110px;">
                    <template #body="{ data }">
                        <strong>{{ wartoscPozycji(data).toFixed(2) }} zł</strong>
                    </template>
                </Column>
                <Column v-if="pokazStanRealizacji" header="Lokalizacja" style="width: 140px;">
                    <template #body="{ data }">
                        <span v-if="data.lokalizacja">{{ data.lokalizacja.szafa }}/{{ data.lokalizacja.polka }}/{{ data.lokalizacja.kolumna }}</span>
                        <span v-else class="text-muted">Brak domyślnej</span>
                    </template>
                </Column>
                <Column v-if="usuwaniePozycji" header="" style="width: 60px; text-align: center;">
                    <template #body="{ data }">
                        <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="deletePozycja(data)" title="Usuń pozycję" />
                    </template>
                </Column>
            </DataTable>

            <Message v-if="blad" severity="error" :closable="false" class="mt-3">{{ blad }}</Message>

            <Message v-if="zamowienie.uwagi" severity="info" :closable="false" class="mt-3">
                <strong>Uwagi:</strong> {{ zamowienie.uwagi }}
            </Message>

            <div v-if="zamowienie.powiazane_zapotrzebowania?.length > 0" class="mt-4">
                <h6 class="mb-3">Powiązane zapotrzebowania:</h6>
                <DataTable :value="zamowienie.powiazane_zapotrzebowania" class="p-datatable-sm">
                    <Column field="numer" header="Numer" style="width: 120px;">
                        <template #body="{ data }"><strong style="color: #69db7c;">{{ data.numer }}</strong></template>
                    </Column>
                    <Column field="technolog" header="Technolog" />
                    <Column field="data_wyslania" header="Data wysłania" style="width: 130px;">
                        <template #body="{ data }">{{ data.data_wyslania || '-' }}</template>
                    </Column>
                    <Column field="status" header="Status" style="width: 130px;" />
                </DataTable>
            </div>
        </div>

        <template #footer>
            <Button :label="trybRealizacji ? 'Anuluj' : 'Zamknij'" icon="pi pi-times" class="p-button-text" @click="onAnuluj" />
            <Button v-if="moznaZapisac" label="Zapisz zmiany" icon="pi pi-save" class="p-button-success"
                    @click="zapiszZmiany" :loading="isSaving" :disabled="isLoading || isRealizujLoading" />
            <Button v-if="trybRealizacji" label="Zatwierdź przyjęcie" icon="pi pi-check" class="p-button-warning"
                    @click="confirmRealizuj()" :loading="isRealizujLoading" :disabled="isLoading || isSaving || !hasSelectedPozycje" />
        </template>
    </Dialog>

    <!-- Potwierdzenie przyjęcia ponad zamówioną ilość (chroni przed literówką) -->
    <Dialog v-model:visible="nadwyzkaVisible" header="Przyjęcie ponad zamówioną ilość" :modal="true" :style="{ width: '560px' }">
        <p>Dla poniższych pozycji przyjmujesz więcej, niż pozostało do przyjęcia:</p>
        <DataTable :value="nadwyzki" class="p-datatable-sm">
            <Column field="narzedzie_opis" header="Narzędzie" />
            <Column header="Pozostało" style="width: 90px; text-align: center;">
                <template #body="{ data }">{{ data.ilosc_pozostala }}</template>
            </Column>
            <Column header="Przyjmujesz" style="width: 100px; text-align: center;">
                <template #body="{ data }"><strong>{{ data.ilosc_do_przyjecia }}</strong></template>
            </Column>
            <Column header="Nadwyżka" style="width: 90px; text-align: center;">
                <template #body="{ data }"><span class="text-orange">+{{ data.ilosc_do_przyjecia - data.ilosc_pozostala }}</span></template>
            </Column>
        </DataTable>
        <p class="text-muted mt-3">Nadwyżka trafi na stan magazynu. Zamówiona ilość i wartość zamówienia pozostają bez zmian.</p>
        <template #footer>
            <Button label="Popraw ilości" icon="pi pi-pencil" class="p-button-text" @click="nadwyzkaVisible = false" />
            <Button label="Przyjmij z nadwyżką" icon="pi pi-check" class="p-button-warning" @click="potwierdzNadwyzke" />
        </template>
    </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Checkbox from 'primevue/checkbox';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Message from 'primevue/message';

const API_URL = '/api';

const STATUSY_EDYCJI = ['draft', 'pending_approval', 'verified'];
const STATUSY_USUWANIA = ['draft', 'pending_approval'];
const STATUSY_REALIZACJI = ['sent', 'partially_received'];

const props = defineProps({
    visible: { type: Boolean, default: false },
    zamowienieId: { type: Number, default: null },
    auth: { type: Object, default: () => ({}) },
    // Pomocnicze z Zamowienia.vue — jedno źródło etykiet i kolorów statusów
    formatDate: { type: Function, required: true },
    getStatusLabel: { type: Function, required: true },
    getStatusSeverity: { type: Function, required: true },
    getStatusTagClass: { type: Function, required: true },
});

// zmieniono — rodzic odświeża listę; wynik — rodzic pokazuje modal wyniku realizacji
const emit = defineEmits(['update:visible', 'zmieniono', 'wynik']);

const zamowienie = ref(null);
const pozycje = ref([]);
const isLoading = ref(false);
const isSaving = ref(false);
const isRealizujLoading = ref(false);
const zaznaczWszystkie = ref(false);
const blad = ref('');
const nadwyzkaVisible = ref(false);
const nadwyzki = ref([]);

const status = computed(() => zamowienie.value?.status);
const isMagazynierView = computed(() => props.auth?.isMagazyn && !props.auth?.isLogistyka);
const edycjaPozycji = computed(() => STATUSY_EDYCJI.includes(status.value));
const usuwaniePozycji = computed(() => STATUSY_USUWANIA.includes(status.value));
const trybRealizacji = computed(() => STATUSY_REALIZACJI.includes(status.value));
const pokazStanRealizacji = computed(() => trybRealizacji.value || status.value === 'completed');
const edycjaCeny = computed(() => !!status.value && status.value !== 'completed' && !isMagazynierView.value);
const moznaZapisac = computed(() => edycjaPozycji.value || edycjaCeny.value);

const tytul = computed(() => {
    if (!zamowienie.value) return 'Zamówienie';
    if (status.value === 'partially_received') return `Zamówienie ${zamowienie.value.numer} — kontynuacja realizacji`;
    if (status.value === 'sent') return `Zamówienie ${zamowienie.value.numer} — przyjęcie towaru`;
    return `Zamówienie ${zamowienie.value.numer}`;
});

// Wartość pozycji: cena jest za sztukę, więc dla kompletów mnożymy przez ilość sztuk w komplecie
const wartoscPozycji = (p) => {
    const mnoznik = p.jednostka === 'kompl' ? (p.ilosc_w_komplecie || 1) : 1;
    return p.ilosc_zamowiona * mnoznik * (p.cena_jednostkowa || 0);
};
const wartoscZamowienia = computed(() => pozycje.value.reduce((sum, p) => sum + wartoscPozycji(p), 0).toFixed(2));

const hasSelectedPozycje = computed(() =>
    pozycje.value.some(p => p.ilosc_pozostala > 0 && (p.odpisz || p.ilosc_do_przyjecia > 0))
);

// Pozycje z niezapisaną zmianą ceny/ilości (porównanie z wartościami z serwera)
const zmienionePozycje = () => pozycje.value.filter(p =>
    Number(p.cena_jednostkowa || 0) !== p._cena_org || p.ilosc_zamowiona !== p._ilosc_org
);

const zaladuj = async () => {
    if (!props.zamowienieId) return;
    isLoading.value = true;
    blad.value = '';
    zaznaczWszystkie.value = false;
    try {
        const res = await axios.get(`${API_URL}/zamowienia/${props.zamowienieId}/`);
        const zam = res.data;
        // Stan realizacji (przyjęto/pozostało/lokalizacja) — tylko gdy ma sens
        let stan = {};
        if (STATUSY_REALIZACJI.includes(zam.status) || zam.status === 'completed') {
            const stanRes = await axios.get(`${API_URL}/zamowienia/${zam.id}/stan_realizacji/`);
            stan = Object.fromEntries(stanRes.data.pozycje.map(s => [s.pozycja_zamowienia_id, s]));
        }
        zamowienie.value = zam;
        pozycje.value = (zam.pozycje || []).map(p => ({
            ...p,
            ilosc_przyjeta: stan[p.id]?.ilosc_przyjeta ?? 0,
            ilosc_pozostala: stan[p.id]?.ilosc_pozostala ?? p.ilosc_zamowiona,
            lokalizacja: stan[p.id]?.lokalizacja ?? null,
            odpisz: false,
            ilosc_do_przyjecia: 0,  // "ile przyjąć teraz" — domyślnie 0, magazynier wpisuje ręcznie
            cena_jednostkowa: Number(p.cena_jednostkowa || 0),
            _cena_org: Number(p.cena_jednostkowa || 0),
            _ilosc_org: p.ilosc_zamowiona,
        }));
    } catch (error) {
        if (error.response?.status === 404) {
            // Zamówienie zniknęło (np. usunięto ostatnią pozycję) — zamknij
            emit('zmieniono');
            emit('update:visible', false);
            return;
        }
        blad.value = 'Błąd ładowania danych: ' + (error.response?.data?.error || error.message);
    } finally {
        isLoading.value = false;
    }
};

watch(() => [props.visible, props.zamowienieId], ([widoczny]) => {
    if (widoczny) zaladuj();
    else { zamowienie.value = null; pozycje.value = []; }
}, { immediate: true });

const zamknij = () => emit('update:visible', false);

const zapiszPozycje = async () => {
    for (const poz of zmienionePozycje()) {
        const payload = { cena_jednostkowa: poz.cena_jednostkowa || 0 };
        if (edycjaPozycji.value) payload.ilosc_zamowiona = poz.ilosc_zamowiona;
        await axios.patch(`${API_URL}/pozycje-zamowien/${poz.id}/`, payload);
        poz._cena_org = Number(poz.cena_jednostkowa || 0);
        poz._ilosc_org = poz.ilosc_zamowiona;
    }
};

const zapiszZmiany = async () => {
    isSaving.value = true;
    blad.value = '';
    try {
        await zapiszPozycje();
        if (props.auth?.isLogistyka && edycjaPozycji.value) {
            await axios.patch(`${API_URL}/zamowienia/${zamowienie.value.id}/`, {
                nr_oferty_dostawcy: zamowienie.value.nr_oferty_dostawcy || ''
            });
        }
        emit('zmieniono');
        zamknij();
    } catch (error) {
        blad.value = 'Błąd zapisu: ' + (error.response?.data?.detail || error.message);
    } finally {
        isSaving.value = false;
    }
};

const deletePozycja = async (pozycja) => {
    try {
        await axios.delete(`${API_URL}/pozycje-zamowien/${pozycja.id}/`);
        emit('zmieniono');
        await zaladuj();
    } catch (error) {
        blad.value = 'Błąd usuwania: ' + (error.response?.data?.detail || error.message);
    }
};

const onAnuluj = async () => {
    // Skrót do przeliczenia statusu: "Zaznacz wszystkie" + "Anuluj" → backend
    // ponownie liczy status zamówienia (bezpiecznie, bez ruszania pozycji).
    if (trybRealizacji.value && zaznaczWszystkie.value) {
        try {
            const res = await axios.post(`${API_URL}/zamowienia/${zamowienie.value.id}/przelicz_status/`);
            zamknij();
            emit('wynik', { success: res.data.success, message: res.data.message, egzemplarze: [] });
            if (res.data.changed) emit('zmieniono');
        } catch (error) {
            blad.value = error.response?.data?.error || 'Błąd przeliczania statusu';
        }
        return;
    }
    zamknij();
};

const onOdpiszToggle = (poz) => {
    // Odpisanie i przyjęcie wykluczają się — przy odpisaniu zeruj ilość do przyjęcia
    if (poz.odpisz) poz.ilosc_do_przyjecia = 0;
};

const toggleSelectAll = () => {
    const val = zaznaczWszystkie.value;
    pozycje.value.forEach(poz => {
        if (poz.ilosc_pozostala > 0) {
            if (val) {
                poz.odpisz = false;
                poz.ilosc_do_przyjecia = poz.ilosc_pozostala;  // pełna realizacja
            } else {
                poz.ilosc_do_przyjecia = 0;
            }
        }
    });
};

const potwierdzNadwyzke = () => {
    nadwyzkaVisible.value = false;
    confirmRealizuj(true);
};

const confirmRealizuj = async (nadwyzkaPotwierdzona = false) => {
    blad.value = '';

    const zaznaczone = pozycje.value.filter(p => p.ilosc_do_przyjecia > 0 && !p.odpisz && p.ilosc_pozostala > 0);
    const odpisane = pozycje.value.filter(p => p.odpisz && p.ilosc_pozostala > 0);

    if (zaznaczone.length === 0 && odpisane.length === 0) {
        blad.value = 'Wpisz ilość do przyjęcia lub zaznacz pozycję do odpisania.';
        return;
    }
    // Przyjęcie ponad pozostałą ilość (dostawca przysłał więcej) — tylko po potwierdzeniu
    const ponad = zaznaczone.filter(p => p.ilosc_do_przyjecia > p.ilosc_pozostala);
    if (ponad.length > 0 && nadwyzkaPotwierdzona !== true) {
        nadwyzki.value = ponad;
        nadwyzkaVisible.value = true;
        return;
    }

    isRealizujLoading.value = true;
    try {
        // Niezapisane zmiany cen nie mogą przepaść przy przyjęciu — zapisz je najpierw
        if (edycjaCeny.value) await zapiszPozycje();

        const response = await axios.post(`${API_URL}/zamowienia/${zamowienie.value.id}/realizuj/`, {
            pozycje: zaznaczone.map(poz => ({ pozycja_zamowienia_id: poz.id, ilosc_przyjeta: poz.ilosc_do_przyjecia })),
            pozycje_do_odpisania: odpisane.map(p => p.id),
            nadwyzka_potwierdzona: ponad.length > 0,
        });
        if (response.data.success) {
            zamknij();
            emit('wynik', {
                success: true,
                message: response.data.message,
                egzemplarze: response.data.utworzone_egzemplarze || [],
            });
            emit('zmieniono');
        }
    } catch (error) {
        blad.value = error.response?.data?.error || 'Wystąpił błąd podczas realizacji.';
    } finally {
        isRealizujLoading.value = false;
    }
};
</script>

<style scoped>
.order-details .details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.pozycje-header {
    display: flex;
    align-items: center;
    gap: 24px;
}
.pozycje-header h6 { margin: 0; }

.select-all-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 14px;
}

.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: var(--dark-text-muted);
}

.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }
.mb-3 { margin-bottom: 16px; }

.text-green { color: #69db7c; font-weight: 600; }
.text-orange { color: #ffa94d; font-weight: 600; }
.text-muted { color: #868e96; }

:deep(.qty-input) { width: 70px !important; text-align: center; }
</style>

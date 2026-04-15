<template>
    <div class="zamowienia-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">ZAMÓWIENIA</h2>
            <div class="header-buttons">
                <button class="btn btn-info" @click="openHelp" title="Pomoc — przewodnik po module">
                    <i class="pi pi-question-circle"></i> Pomoc
                </button>
                <div v-if="dzialaniaMenuItems.length > 0" class="dropdown-wrapper">
                    <button class="btn btn-success" @click="toggleDzialaniaMenu">
                        <i class="pi pi-th-large"></i> Działania
                        <i class="pi pi-chevron-down" style="margin-left: 4px; font-size: 0.75rem;"></i>
                    </button>
                    <Menu ref="dzialaniaMenu" id="dzialania_menu" :model="dzialaniaMenuItems" :popup="true" />
                </div>
                <div class="dropdown-wrapper">
                    <button class="btn btn-primary" @click="toggleMiejscaMenu">
                        <i class="pi pi-building"></i> Miejsca
                        <i class="pi pi-chevron-down" style="margin-left: 4px; font-size: 0.75rem;"></i>
                    </button>
                    <Menu ref="miejscaMenu" id="miejsca_menu" :model="miejscaMenuItems" :popup="true" />
                </div>
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

        <!-- Główna zawartość -->
        <main class="app-main">
            <div class="orders-panel">
                <div class="panel-header">
                    <h3 class="panel-title">Lista zamówień</h3>
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="searchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable :value="sortedZamowienia" :scrollable="true" scrollHeight="flex" dataKey="id">
                        <Column header="Numer">
                            <template #body="{ data }">
                                <a href="#" @click.prevent="selectZamowienie(data)" class="order-link">
                                    <strong>{{ data.numer }}</strong>
                                </a>
                            </template>
                        </Column>
                        <Column header="Dostawca">
                            <template #body="{ data }">
                                {{ data.dostawca?.nazwa_firmy || '-' }}
                            </template>
                        </Column>
                        <Column header="Data utworzenia">
                            <template #body="{ data }">
                                {{ formatDate(data.data_utworzenia) }}
                            </template>
                        </Column>
                        <Column header="Data wysłania">
                            <template #body="{ data }">
                                {{ data.data_wyslania ? formatDate(data.data_wyslania) : '-' }}
                            </template>
                        </Column>
                        <Column header="Status">
                            <template #body="{ data }">
                                <Tag :severity="getStatusSeverity(data.status)" :value="getStatusLabel(data.status)" :class="getStatusTagClass(data.status)" />
                            </template>
                        </Column>
                        <Column header="Pozycje" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                {{ data.pozycje?.length || 0 }}
                            </template>
                        </Column>
                        <Column header="Uwagi" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <Button v-if="data.uwagi" icon="pi pi-comment" class="p-button-text p-button-secondary p-button-sm" @click="showUwagi(data)" />
                            </template>
                        </Column>
                        <Column header="Akcje" style="width: 240px; text-align: center;">
                            <template #body="{ data }">
                                <div style="display: flex; gap: 4px; justify-content: center; flex-wrap: nowrap;">
                                    <Button v-if="data.status === 'verified'" icon="pi pi-envelope" class="p-button-success p-button-sm" @click="openEmailConfirmModal(data)" title="Wyślij e-mail do dostawcy" />
                                    <Button v-if="data.status === 'pending_approval'" icon="pi pi-check" class="p-button-success p-button-sm" @click="zatwierdzZamowienie(data)" title="Zatwierdź zamówienie" />
                                    <Button v-if="data.status === 'pending_approval'" icon="pi pi-undo" class="p-button-secondary p-button-sm" @click="cofnijDoRoboczej(data)" title="Cofnij do wersji roboczej" />
                                    <Button v-if="data.status === 'sent'" icon="pi pi-box" class="p-button-info p-button-sm" @click="rozpocznijRealizacje(data)" title="Rozpocznij realizację" />
                                    <Button v-if="data.status === 'sent'" icon="pi pi-undo" class="p-button-warning p-button-sm" @click="openCofnijDoZatwierdzoneModal(data)" title="Cofnij do 'Zatwierdzone' (zmiana dostawcy)" />
                                    <Button v-if="data.status === 'partially_received'" icon="pi pi-box" class="p-button-warning p-button-sm" @click="rozpocznijRealizacje(data)" title="Kontynuuj realizację" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-truck" class="p-button-help p-button-sm" @click="openZmienDostawceModal(data)" title="Zmień dostawcę" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="selectZamowienie(data)" title="Edytuj pozycje" />
                                    <Button v-if="['draft', 'pending_approval', 'verified'].includes(data.status)" icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteConfirmModal(data)" title="Usuń" />
                                </div>
                            </template>
                        </Column>
                        <template #empty>
                            <div class="empty-state">Brak zamówień</div>
                        </template>
                    </DataTable>
                </div>
            </div>
        </main>

        <!-- Modal: Szczegóły zamówienia -->
        <Dialog v-model:visible="detailsModalVisible" header="Szczegóły zamówienia" :modal="true" :style="{ width: '1800px' }">
            <div v-if="selectedZamowienie" class="order-details">
                <div class="details-grid">
                    <div class="details-left">
                        <p><strong>Dostawca:</strong> {{ selectedZamowienie.dostawca?.nazwa_firmy }}</p>
                        <p><strong>Data utworzenia:</strong> {{ formatDate(selectedZamowienie.data_utworzenia) }}</p>
                        <p><strong>Data wysłania:</strong> {{ selectedZamowienie.data_wyslania ? formatDate(selectedZamowienie.data_wyslania) : 'Nie wysłano' }}</p>
                    </div>
                    <div class="details-right">
                        <p><strong>Status:</strong> <Tag :severity="getStatusSeverity(selectedZamowienie.status)" :value="getStatusLabel(selectedZamowienie.status)" :class="getStatusTagClass(selectedZamowienie.status)" /></p>
                        <p><strong>Wartość:</strong> {{ obliczonaWartoscZamowienia }} zł</p>
                        <p><strong>Email:</strong> {{ selectedZamowienie.email_docelowy || 'brak' }}</p>
                    </div>
                </div>

                <h6 class="mt-4 mb-3">Pozycje zamówienia:</h6>
                <DataTable :value="selectedZamowienie.pozycje" :scrollable="true" scrollHeight="300px" class="p-datatable-sm">
                    <Column field="kategoria_nazwa" header="Kategoria" />
                    <Column field="podkategoria_nazwa" header="Podkategoria" />
                    <Column field="narzedzie_opis" header="Narzędzie" />
                    <Column field="numer_katalogowy" header="Nr katalogowy" />
                    <Column header="Ilość" style="width: 100px;">
                        <template #body="{ data }">
                            <InputNumber
                                v-if="canEditPozycje"
                                v-model="data.ilosc_zamowiona"
                                :min="1"
                                :inputStyle="{ width: '60px', textAlign: 'center' }"
                            />
                            <span v-else>{{ data.ilosc_zamowiona }}</span>
                        </template>
                    </Column>
                    <Column header="Jednostka" style="width: 120px;">
                        <template #body="{ data }">
                            {{ data.jednostka === 'kompl' ? `kompl. (${data.ilosc_w_komplecie} szt.)` : 'szt.' }}
                        </template>
                    </Column>
                    <Column header="Cena jedn." style="width: 120px;">
                        <template #body="{ data }">
                            <InputNumber
                                v-model="data.cena_jednostkowa"
                                :minFractionDigits="2"
                                :maxFractionDigits="2"
                                :min="0"
                                :inputStyle="{ width: '80px', textAlign: 'right' }"
                            />
                        </template>
                    </Column>
                    <Column header="Wartość" style="width: 110px;">
                        <template #body="{ data }">
                            <strong>{{ (data.ilosc_zamowiona * (data.cena_jednostkowa || 0)).toFixed(2) }} zł</strong>
                        </template>
                    </Column>
                    <Column v-if="canDeletePozycja" header="" style="width: 60px; text-align: center;">
                        <template #body="{ data }">
                            <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="deletePozycja(data)" title="Usuń pozycję" />
                        </template>
                    </Column>
                </DataTable>

                <Message v-if="selectedZamowienie.uwagi" severity="info" :closable="false" class="mt-3">
                    <strong>Uwagi:</strong> {{ selectedZamowienie.uwagi }}
                </Message>

                <div v-if="selectedZamowienie.powiazane_zapotrzebowania && selectedZamowienie.powiazane_zapotrzebowania.length > 0" class="mt-4">
                    <h6 class="mb-3">Powiązane zapotrzebowania:</h6>
                    <DataTable :value="selectedZamowienie.powiazane_zapotrzebowania" class="p-datatable-sm">
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
                <Button label="Zapisz zmiany" icon="pi pi-save" class="p-button-success" @click="saveAllPozycje" :loading="isSavingPozycje" />
                <Button label="Zamknij" @click="closeDetails" />
            </template>
        </Dialog>

        <!-- Modal: Dodaj/Edytuj zamówienie -->
        <Dialog v-model:visible="zamowienieModalVisible" :header="zamowienieModal.title" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <Message v-if="zamowienieModal.errorMessage" severity="error" :closable="false">{{ zamowienieModal.errorMessage }}</Message>
                <div class="field">
                    <label>Numer zamówienia</label>
                    <InputText v-model="zamowienieModal.currentItem.numer" />
                </div>
                <div class="field">
                    <label>Dostawca</label>
                    <Dropdown
                        v-model="zamowienieModal.currentItem.dostawca_id"
                        :options="dostawcyOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Wybierz dostawcę --"
                    />
                </div>
                <div class="field">
                    <label>Uwagi</label>
                    <Textarea v-model="zamowienieModal.currentItem.uwagi" rows="3" />
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="zamowienieModalVisible = false" />
                <Button label="Zapisz" icon="pi pi-check" @click="saveZamowienie" :loading="isSaving" />
            </template>
        </Dialog>

        <!-- Modal: Uwagi -->
        <Dialog v-model:visible="uwagiModalVisible" header="Uwagi do zamówienia" :modal="true" :style="{ width: '450px' }">
            <p><strong>Numer zamówienia:</strong> {{ selectedUwagiZamowienie?.numer }}</p>
            <Divider />
            <p>{{ selectedUwagiZamowienie?.uwagi }}</p>
            <template #footer>
                <Button label="Zamknij" @click="uwagiModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie wysyłki email -->
        <Dialog v-model:visible="emailConfirmModalVisible" header="Potwierdzenie wysyłki e-mail" :modal="true" :style="{ width: '450px' }">
            <Message v-if="zamowieniaTestowe" severity="warn" :closable="false" style="margin-bottom: 15px;">
                <strong>TRYB TESTOWY</strong> — email zostanie wysłany na adres testowy zamiast do dostawcy!
            </Message>
            <p style="margin-bottom: 15px;">Czy na pewno chcesz wysłać to zamówienie e-mailem {{ zamowieniaTestowe ? '(testowo)' : 'do dostawcy' }}?</p>
            <Message severity="info" :closable="false">
                <strong>Numer zamówienia:</strong> {{ selectedEmailZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedEmailZamowienie?.dostawca?.nazwa_firmy }}<br>
                <strong>Email:</strong> {{ zamowieniaTestowe ? emailTestAddress + ' (testowy)' : (selectedEmailZamowienie?.email_docelowy || 'brak') }}
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="emailConfirmModalVisible = false" />
                <Button label="Wyślij e-mail" icon="pi pi-send" class="p-button-success" @click="confirmWyslijEmail" :loading="isSendingEmail" />
            </template>
        </Dialog>

        <!-- Modal: Wynik wysyłki email -->
        <Dialog v-model:visible="emailResultModalVisible" :header="emailResult.success ? 'Sukces' : 'Błąd'" :modal="true" :style="{ width: '400px' }">
            <Message :severity="emailResult.success ? 'success' : 'error'" :closable="false">{{ emailResult.message }}</Message>
            <template #footer>
                <Button label="Zamknij" @click="emailResultModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Zmiana dostawcy -->
        <Dialog v-model:visible="zmienDostawceModalVisible" header="Zmiana dostawcy" :modal="true" :style="{ width: '520px' }">
            <div v-if="selectedZmienDostawceZamowienie" class="p-fluid">
                <p>
                    <strong>Zamówienie:</strong> {{ selectedZmienDostawceZamowienie.numer }}<br>
                    <strong>Aktualny dostawca:</strong> {{ selectedZmienDostawceZamowienie.dostawca?.nazwa_firmy }}
                </p>
                <div class="field">
                    <label>Nowy dostawca</label>
                    <Dropdown
                        v-model="nowyDostawcaId"
                        :options="dostawcyZmianaOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Wybierz dostawcę"
                        filter
                    />
                </div>
                <Message v-if="nowyDostawcaInfo" severity="info" :closable="false">
                    <strong>Email nowego dostawcy:</strong> {{ nowyDostawcaInfo.email || '(brak — uzupełnij w kartotece)' }}<br>
                    Email zamówienia zostanie zaktualizowany do tego adresu.
                </Message>
                <Message v-if="zmienDostawceError" severity="error" :closable="false">{{ zmienDostawceError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="zmienDostawceModalVisible = false" />
                <Button label="Zmień dostawcę" icon="pi pi-check" class="p-button-success" @click="confirmZmienDostawce" :loading="isZmianaDostawcy" :disabled="!nowyDostawcaId" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie cofnięcia z "Wysłane" do "Zatwierdzone" -->
        <Dialog v-model:visible="cofnijDoZatwierdzoneModalVisible" header="Cofnięcie do 'Zatwierdzone'" :modal="true" :style="{ width: '500px' }">
            <p>Czy na pewno chcesz cofnąć zamówienie do statusu <strong>„Zatwierdzone”</strong>?</p>
            <Message severity="warn" :closable="false">
                <strong>Numer:</strong> {{ selectedCofnijZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedCofnijZamowienie?.dostawca?.nazwa_firmy }}<br>
                Po cofnięciu będziesz mógł zmienić dostawcę / pozycje i wysłać zamówienie ponownie.<br>
                Data wysłania zostanie zresetowana.
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="cofnijDoZatwierdzoneModalVisible = false" />
                <Button label="Cofnij do 'Zatwierdzone'" icon="pi pi-undo" class="p-button-warning" @click="confirmCofnijDoZatwierdzone" :loading="isCofajacDoZatwierdzone" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdzenie usunięcia -->
        <Dialog v-model:visible="deleteConfirmModalVisible" header="Potwierdzenie usunięcia" :modal="true" :style="{ width: '450px' }">
            <p>Czy na pewno chcesz usunąć to zamówienie?</p>
            <Message severity="error" :closable="false">
                <strong>Numer zamówienia:</strong> {{ selectedDeleteZamowienie?.numer }}<br>
                <strong>Dostawca:</strong> {{ selectedDeleteZamowienie?.dostawca?.nazwa_firmy }}<br>
                <strong>Uwaga:</strong> Ta operacja jest nieodwracalna!
            </Message>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteConfirmModalVisible = false" />
                <Button label="Usuń zamówienie" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteZamowienie" :loading="isDeleting" />
            </template>
        </Dialog>

        <!-- Modal: Realizacja zamówienia (częściowa/pełna) -->
        <Dialog v-model:visible="realizacjaConfirmModalVisible" :header="realizacjaModalTitle" :modal="true" :style="{ width: '1100px' }">
            <div v-if="selectedRealizacjaZamowienie" class="realizacja-modal-content">
                <div class="realizacja-info-bar">
                    <span><strong>Zamówienie:</strong> {{ selectedRealizacjaZamowienie.numer }}</span>
                    <span><strong>Dostawca:</strong> {{ selectedRealizacjaZamowienie.dostawca?.nazwa_firmy }}</span>
                    <span><Tag :severity="getStatusSeverity(selectedRealizacjaZamowienie.status)" :value="getStatusLabel(selectedRealizacjaZamowienie.status)" :class="getStatusTagClass(selectedRealizacjaZamowienie.status)" /></span>
                </div>

                <div v-if="isLoadingRealizacja" class="loading-state">
                    <i class="pi pi-spin pi-spinner" style="font-size: 2rem;"></i>
                    <p>Ładowanie danych realizacji...</p>
                </div>

                <div v-else>
                    <div class="realizacja-toolbar">
                        <label class="select-all-label">
                            <Checkbox v-model="realizacjaSelectAll" :binary="true" @change="toggleSelectAll" />
                            <span>Zaznacz wszystkie (pełna realizacja)</span>
                        </label>
                    </div>

                    <DataTable :value="realizacjaPozycje" class="p-datatable-sm realizacja-table" :scrollable="true" scrollHeight="400px">
                        <Column header="" style="width: 50px; text-align: center;">
                            <template #body="{ data }">
                                <Checkbox v-model="data.przyjmij" :binary="true" :disabled="data.ilosc_pozostala <= 0" />
                            </template>
                        </Column>
                        <Column field="narzedzie_opis" header="Narzędzie" />
                        <Column field="numer_katalogowy" header="Nr katalogowy" style="width: 140px;" />
                        <Column header="Zamówiono" style="width: 100px; text-align: center;">
                            <template #body="{ data }">
                                <strong>{{ data.ilosc_zamowiona }}</strong>
                                <span class="unit-label">{{ data.jednostka === 'kompl' ? 'kompl.' : 'szt.' }}</span>
                            </template>
                        </Column>
                        <Column header="Przyjęto" style="width: 90px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'text-green': data.ilosc_przyjeta > 0 }">{{ data.ilosc_przyjeta }}</span>
                            </template>
                        </Column>
                        <Column header="Pozostało" style="width: 90px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'text-orange': data.ilosc_pozostala > 0, 'text-green': data.ilosc_pozostala === 0 }">
                                    {{ data.ilosc_pozostala }}
                                </span>
                            </template>
                        </Column>
                        <Column header="Do przyjęcia" style="width: 120px; text-align: center;">
                            <template #body="{ data }">
                                <InputNumber
                                    v-if="data.przyjmij && data.ilosc_pozostala > 0"
                                    v-model="data.ilosc_do_przyjecia"
                                    :min="1"
                                    :max="data.ilosc_pozostala"
                                    inputClass="qty-input"
                                    :inputStyle="{ width: '70px', textAlign: 'center' }"
                                />
                                <Tag v-else-if="data.ilosc_pozostala === 0" value="OK" severity="success" />
                                <span v-else>-</span>
                            </template>
                        </Column>
                        <Column header="Cena jedn." style="width: 120px; text-align: right;">
                            <template #body="{ data }">
                                <span>{{ Number(data.cena_jednostkowa || 0).toFixed(2) }} zł</span>
                            </template>
                        </Column>
                        <Column header="Lokalizacja" style="width: 140px;">
                            <template #body="{ data }">
                                <span v-if="data.lokalizacja">
                                    {{ data.lokalizacja.szafa }}/{{ data.lokalizacja.polka }}/{{ data.lokalizacja.kolumna }}
                                </span>
                                <span v-else class="text-muted">Brak domyślnej</span>
                            </template>
                        </Column>
                    </DataTable>

                    <Message v-if="realizacjaError" severity="error" :closable="false" class="mt-3">{{ realizacjaError }}</Message>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="realizacjaConfirmModalVisible = false" />
                <Button
                    label="Zatwierdź przyjęcie"
                    icon="pi pi-check"
                    class="p-button-success"
                    @click="confirmRealizuj"
                    :loading="isRealizujLoading"
                    :disabled="isLoadingRealizacja || !hasSelectedPozycje"
                />
            </template>
        </Dialog>

        <!-- Modal: Wynik realizacji -->
        <Dialog v-model:visible="realizacjaResultModalVisible" :header="realizacjaResult.success ? 'Przyjęcie potwierdzone' : 'Błąd'" :modal="true" :style="{ width: '650px' }">
            <Message :severity="realizacjaResult.success ? 'success' : 'error'" :closable="false">{{ realizacjaResult.message }}</Message>
            <DataTable v-if="realizacjaResult.success && realizacjaResult.egzemplarze.length > 0" :value="realizacjaResult.egzemplarze" class="p-datatable-sm mt-3">
                <Column field="narzedzie" header="Narzędzie" />
                <Column header="Ilość" style="width: 80px; text-align: center;">
                    <template #body="{ data }"><strong>{{ data.ilosc }}</strong></template>
                </Column>
                <Column field="lokalizacja" header="Lokalizacja" style="width: 150px;" />
            </DataTable>
            <template #footer>
                <Button label="Zamknij" @click="realizacjaResultModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Wyślij do zatwierdzenia -->
        <Dialog v-model:visible="approvalModalVisible" header="Wyślij zamówienia do zatwierdzenia" :modal="true" :style="{ width: '750px' }">
            <Message severity="info" :closable="false" style="margin-bottom: 15px;">
                Wybierz zamówienia, które chcesz wysłać do szefa do zatwierdzenia. Zostanie wysłany zbiorczy email z listą wszystkich pozycji i sumą.
            </Message>
            <Message v-if="!emailSzef" severity="warn" :closable="false" style="margin-bottom: 15px;">
                <strong>Brak adresu email szefa!</strong> Skonfiguruj go w Ustawienia → Poczta (EMAIL_SZEF).
            </Message>
            <DataTable :value="draftZamowienia" v-model:selection="selectedApprovalZamowienia" dataKey="id" class="p-datatable-sm">
                <Column selectionMode="multiple" style="width: 50px;" />
                <Column field="numer" header="Numer" style="width: 140px;">
                    <template #body="{ data }"><strong>{{ data.numer }}</strong></template>
                </Column>
                <Column header="Dostawca">
                    <template #body="{ data }">{{ data.dostawca?.nazwa_firmy || '-' }}</template>
                </Column>
                <Column header="Pozycji" style="width: 80px; text-align: center;">
                    <template #body="{ data }">{{ data.pozycje?.length || 0 }}</template>
                </Column>
                <Column header="Wartość" style="width: 120px; text-align: right;">
                    <template #body="{ data }"><strong>{{ data.wartosc_zamowienia }} zł</strong></template>
                </Column>
            </DataTable>
            <div v-if="selectedApprovalZamowienia.length > 0" class="approval-summary">
                <strong>Wybrano: {{ selectedApprovalZamowienia.length }} zamówień</strong>
                <span class="approval-total">Łączna wartość: <strong>{{ approvalTotal }} zł</strong></span>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="approvalModalVisible = false" />
                <Button label="Wyślij do zatwierdzenia" icon="pi pi-send" class="p-button-warning" @click="confirmSendApproval" :loading="isSendingApproval" :disabled="selectedApprovalZamowienia.length === 0 || !emailSzef" />
            </template>
        </Dialog>

        <!-- Modal: Wynik wysyłki do zatwierdzenia -->
        <Dialog v-model:visible="approvalResultModalVisible" :header="approvalResult.success ? 'Sukces' : 'Błąd'" :modal="true" :style="{ width: '400px' }">
            <Message :severity="approvalResult.success ? 'success' : 'error'" :closable="false">{{ approvalResult.message }}</Message>
            <template #footer>
                <Button label="Zamknij" @click="approvalResultModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: O programie -->
        <Dialog v-model:visible="aboutModalVisible" header="O programie" :modal="true" :style="{ width: '450px' }">
            <div class="about-content">
                <div class="about-header">
                    <img :src="logoImage" alt="CNC Tools Logo" class="about-logo" />
                    <h4><strong>CNC Tools</strong></h4>
                    <p class="text-muted">System zarządzania narzędziami CNC</p>
                </div>
                <table class="about-table">
                    <tbody>
                        <tr><td class="label"><i class="pi pi-code"></i> Wersja:</td><td><strong>{{ infoProgram.WERSJA }}</strong></td></tr>
                        <tr><td class="label"><i class="pi pi-calendar"></i> Data modyfikacji:</td><td>{{ infoProgram.MODYFIKACJA }}</td></tr>
                        <tr><td class="label"><i class="pi pi-building"></i> Firma:</td><td>{{ infoProgram.FIRMA }}</td></tr>
                        <tr><td class="label"><i class="pi pi-user"></i> Autor:</td><td>{{ infoProgram.AUTOR }}</td></tr>
                        <tr><td class="label"><i class="pi pi-envelope"></i> Email:</td><td><a :href="infoProgram.EMAIL">{{ infoProgram.NEMAIL }}</a></td></tr>
                        <tr><td class="label"><i class="pi pi-phone"></i> Telefon:</td><td>{{ infoProgram.TEL }}</td></tr>
                    </tbody>
                </table>
            </div>
            <template #footer>
                <small class="text-muted">© {{ infoProgram.FIRMA }} 2025</small>
                <Button label="Zamknij" @click="aboutModalVisible = false" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';
import Checkbox from 'primevue/checkbox';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Menu from 'primevue/menu';
import Divider from 'primevue/divider';

const API_URL = '/api';

const props = defineProps({
    auth: { type: Object, default: () => ({ user: { firstName: '', lastName: '' }, isLogistyka: false }) },
    urls: { type: Object, default: () => ({ ustawienia: '/ustawienia/', realizacja: '/realizacja/', magazyn: '/magazyn-inertia/', zakupy: '/zakupy-inertia/', logout: '/logout/' }) },
    infoProgram: { type: Object, default: () => ({}) },
    canGenerateOrders: { type: Boolean, default: false }
});

// Data
const zamowienia = ref([]);
const dostawcy = ref([]);
const selectedZamowienie = ref(null);
const selectedUwagiZamowienie = ref(null);
const selectedEmailZamowienie = ref(null);
const selectedDeleteZamowienie = ref(null);
const selectedRealizacjaZamowienie = ref(null);

const isSaving = ref(false);
const isSendingEmail = ref(false);
const isDeleting = ref(false);
const isSendingApproval = ref(false);
const isSavingPozycje = ref(false);

const emailResult = ref({ success: false, message: '' });
const emailSzef = ref('');
const realizacjaResult = ref({ success: false, message: '', egzemplarze: [] });
const realizacjaPozycje = ref([]);
const realizacjaSelectAll = ref(false);
const realizacjaError = ref('');
const isLoadingRealizacja = ref(false);
const isRealizujLoading = ref(false);
const zamowieniaTestowe = ref(false);
const emailTestAddress = ref('');

// Modals
const detailsModalVisible = ref(false);
const zamowienieModalVisible = ref(false);
const uwagiModalVisible = ref(false);
const emailConfirmModalVisible = ref(false);
const emailResultModalVisible = ref(false);
const deleteConfirmModalVisible = ref(false);
const realizacjaConfirmModalVisible = ref(false);
const realizacjaResultModalVisible = ref(false);
const aboutModalVisible = ref(false);
const approvalModalVisible = ref(false);
const approvalResultModalVisible = ref(false);
const approvalResult = ref({ success: false, message: '' });
const selectedApprovalZamowienia = ref([]);

const zamowienieModal = ref({ title: '', mode: 'add', currentItem: {}, errorMessage: '' });

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
    { label: 'Ustawienia', icon: 'pi pi-cog', command: () => { window.location.href = props.urls.ustawienia + '?from=zakupy'; } },
    { separator: true },
    { label: 'O programie', icon: 'pi pi-info-circle', command: () => { aboutModalVisible.value = true; } },
    { separator: true },
    { label: 'Wyjście', icon: 'pi pi-sign-out', command: () => { window.location.href = props.urls.logout; } }
]);

// Pomoc — otwiera w nowym oknie typu popup (działa też w trybie PWA)
const openHelp = () => {
    const url = props.urls.pomoc_zamowienia || '/pomoc/zamowienia/';
    const features = 'noopener,noreferrer,width=1100,height=860,resizable=yes,scrollbars=yes';
    window.open(url, 'pomoc-zamowienia', features);
};

// Menu Działania
const dzialaniaMenu = ref(null);
const dzialaniaMenuItems = computed(() => {
    const items = [];
    if (props.canGenerateOrders) {
        items.push({ label: 'Generuj nowe', icon: 'pi pi-sparkles', command: () => generujAutomatyczne() });
    }
    if (draftZamowienia.value.length > 0) {
        items.push({ label: 'Wyślij do zatwierdzenia', icon: 'pi pi-send', command: () => openApprovalModal() });
    }
    return items;
});
const toggleDzialaniaMenu = (event) => { dzialaniaMenu.value.toggle(event); };

// Wyszukiwanie
const searchQuery = ref('');

// Menu Miejsca
const miejscaMenu = ref(null);
const miejscaMenuItems = computed(() => {
    const items = [
        { label: 'Magazyn', icon: 'pi pi-building', command: () => { window.location.href = props.urls.magazyn; } }
    ];
    if (props.auth?.isLogistyka) {
        items.push({ label: 'Zakupy', icon: 'pi pi-truck', command: () => { window.location.href = props.urls.zakupy; } });
    }
    return items;
});
const toggleMiejscaMenu = (event) => { miejscaMenu.value.toggle(event); };

// Computed
const dostawcyOptions = computed(() => [
    { label: '-- Wybierz dostawcę --', value: null },
    ...dostawcy.value.map(d => ({ label: d.nazwa_firmy, value: d.id }))
]);

const statusLabels = {
    'draft': 'Wersja robocza',
    'pending_approval': 'Oczekuje na zatwierdzenie',
    'verified': 'Zatwierdzone',
    'sent': 'Wysłane',
    'partially_received': 'Częściowo odebrane',
    'completed': 'Zrealizowane'
};

// Methods
const toggleUserMenu = (event) => userMenu.value.toggle(event);

const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const h = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d} ${h}:${min}`;
};

const getStatusLabel = (status) => statusLabels[status] || status;

const getStatusSeverity = (status) => {
    const map = { 'draft': 'secondary', 'pending_approval': 'warning', 'verified': 'info', 'sent': 'primary', 'partially_received': 'warning', 'completed': 'success' };
    return map[status] || 'secondary';
};

// Status 'partially_received' — Tag musi mieć identyczny kolor jak p-button-warning (pomarańczowy).
// Klasa .tag-status-orange w dark-theme.css ma !important żeby pokonać override .p-tag-warning
const getStatusTagClass = (status) => {
    return status === 'partially_received' ? 'tag-status-orange' : '';
};

const selectZamowienie = (zamowienie) => {
    selectedZamowienie.value = zamowienie;
    detailsModalVisible.value = true;
};

const showUwagi = (zamowienie) => {
    selectedUwagiZamowienie.value = zamowienie;
    uwagiModalVisible.value = true;
};

const openEmailConfirmModal = (zamowienie) => {
    selectedEmailZamowienie.value = zamowienie;
    emailConfirmModalVisible.value = true;
};

const confirmWyslijEmail = async () => {
    isSendingEmail.value = true;
    try {
        await axios.post(`${API_URL}/zamowienia/${selectedEmailZamowienie.value.id}/wyslij-email/`);
        emailConfirmModalVisible.value = false;
        emailResult.value = { success: true, message: 'Email został wysłany pomyślnie!' };
        emailResultModalVisible.value = true;
        await fetchZamowienia();
    } catch (error) {
        emailConfirmModalVisible.value = false;
        emailResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd podczas wysyłki email' };
        emailResultModalVisible.value = true;
    } finally {
        isSendingEmail.value = false;
    }
};

const openDeleteConfirmModal = (zamowienie) => {
    selectedDeleteZamowienie.value = zamowienie;
    deleteConfirmModalVisible.value = true;
};

const confirmDeleteZamowienie = async () => {
    isDeleting.value = true;
    try {
        await axios.delete(`${API_URL}/zamowienia/${selectedDeleteZamowienie.value.id}/`);
        deleteConfirmModalVisible.value = false;
        await fetchZamowienia();
    } catch (error) {
        deleteConfirmModalVisible.value = false;
        emailResult.value = { success: false, message: 'Wystąpił błąd: ' + (error.response?.data?.error || error.message) };
        emailResultModalVisible.value = true;
    } finally {
        isDeleting.value = false;
        selectedDeleteZamowienie.value = null;
    }
};

const openZamowienieModal = (mode, zamowienie = null) => {
    zamowienieModal.value.mode = mode;
    zamowienieModal.value.errorMessage = '';
    if (mode === 'add') {
        zamowienieModal.value.title = 'Nowe zamówienie';
        zamowienieModal.value.currentItem = { numer: generateZamowienieNumer(), dostawca_id: null, uwagi: '' };
    } else {
        zamowienieModal.value.title = 'Edytuj zamówienie';
        zamowienieModal.value.currentItem = { ...zamowienie, dostawca_id: zamowienie.dostawca?.id };
    }
    zamowienieModalVisible.value = true;
};

const generateZamowienieNumer = () => {
    const date = new Date();
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const r = Math.floor(Math.random() * 1000);
    return `ZAM/${y}/${m}/${r}`;
};

const saveZamowienie = async () => {
    isSaving.value = true;
    zamowienieModal.value.errorMessage = '';

    if (!zamowienieModal.value.currentItem.numer || !zamowienieModal.value.currentItem.dostawca_id) {
        zamowienieModal.value.errorMessage = 'Numer zamówienia i dostawca są wymagane.';
        isSaving.value = false;
        return;
    }

    const method = zamowienieModal.value.mode === 'add' ? 'post' : 'patch';
    const url = zamowienieModal.value.mode === 'add' ? `${API_URL}/zamowienia/` : `${API_URL}/zamowienia/${zamowienieModal.value.currentItem.id}/`;

    try {
        await axios({ method, url, data: zamowienieModal.value.currentItem });
        zamowienieModalVisible.value = false;
        await fetchInitialData();
    } catch (error) {
        zamowienieModal.value.errorMessage = 'Błąd zapisu: ' + (error.response?.data?.detail || error.message);
    } finally {
        isSaving.value = false;
    }
};

// Computed — filtrowanie po wyszukiwarce (Numer, Dostawca, Data utworzenia, Data wysłania)
const filteredZamowienia = computed(() => {
    const q = searchQuery.value.trim().toLowerCase();
    if (!q) return zamowienia.value;
    return zamowienia.value.filter(z => {
        const numer = (z.numer || '').toLowerCase();
        const dostawca = (z.dostawca?.nazwa_firmy || '').toLowerCase();
        const dataUtw = z.data_utworzenia ? formatDate(z.data_utworzenia).toLowerCase() : '';
        const dataWysl = z.data_wyslania ? formatDate(z.data_wyslania).toLowerCase() : '';
        return numer.includes(q) || dostawca.includes(q) || dataUtw.includes(q) || dataWysl.includes(q);
    });
});

// Computed — sortowanie listy: niezrealizowane/w trakcie zawsze na górze, w obrębie grupy numer malejąco
const sortedZamowienia = computed(() => {
    return [...filteredZamowienia.value].sort((a, b) => {
        const aDone = a.status === 'completed' ? 1 : 0;
        const bDone = b.status === 'completed' ? 1 : 0;
        if (aDone !== bDone) return aDone - bDone;
        return (b.numer || '').localeCompare(a.numer || '');
    });
});

// Computed — filtrowane zamówienia
const draftZamowienia = computed(() => zamowienia.value.filter(z => z.status === 'draft'));
const canEditPozycje = computed(() => {
    if (!selectedZamowienie.value) return false;
    return ['draft', 'pending_approval', 'verified'].includes(selectedZamowienie.value.status);
});
const canDeletePozycja = computed(() => {
    if (!selectedZamowienie.value) return false;
    return ['draft', 'pending_approval'].includes(selectedZamowienie.value.status);
});
const obliczonaWartoscZamowienia = computed(() => {
    if (!selectedZamowienie.value?.pozycje) return '0.00';
    return selectedZamowienie.value.pozycje
        .reduce((sum, p) => sum + p.ilosc_zamowiona * (p.cena_jednostkowa || 0), 0)
        .toFixed(2);
});
const approvalTotal = computed(() => {
    return selectedApprovalZamowienia.value.reduce((sum, z) => sum + parseFloat(z.wartosc_zamowienia || 0), 0).toFixed(2);
});

// Zatwierdzanie
const openApprovalModal = () => {
    selectedApprovalZamowienia.value = [...draftZamowienia.value];
    approvalModalVisible.value = true;
};

const confirmSendApproval = async () => {
    isSendingApproval.value = true;
    try {
        const ids = selectedApprovalZamowienia.value.map(z => z.id);
        const res = await axios.post(`${API_URL}/zamowienia/wyslij-do-zatwierdzenia/`, { zamowienie_ids: ids });
        approvalModalVisible.value = false;
        approvalResult.value = { success: true, message: res.data.message };
        approvalResultModalVisible.value = true;
        await fetchInitialData();
    } catch (error) {
        approvalModalVisible.value = false;
        approvalResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd' };
        approvalResultModalVisible.value = true;
    } finally {
        isSendingApproval.value = false;
    }
};

const zatwierdzZamowienie = async (zamowienie) => {
    try {
        const res = await axios.post(`${API_URL}/zamowienia/zatwierdz/`, { zamowienie_ids: [zamowienie.id] });
        approvalResult.value = { success: true, message: res.data.message };
        approvalResultModalVisible.value = true;
        await fetchInitialData();
    } catch (error) {
        approvalResult.value = { success: false, message: error.response?.data?.error || 'Wystąpił błąd' };
        approvalResultModalVisible.value = true;
    }
};

const cofnijDoRoboczej = async (zamowienie) => {
    try {
        await axios.post(`${API_URL}/zamowienia/cofnij-do-roboczej/`, { zamowienie_id: zamowienie.id });
        await fetchInitialData();
    } catch (error) {
        alert('Błąd: ' + (error.response?.data?.error || error.message));
    }
};

// Zmiana dostawcy zamówienia
const zmienDostawceModalVisible = ref(false);
const selectedZmienDostawceZamowienie = ref(null);
const nowyDostawcaId = ref(null);
const isZmianaDostawcy = ref(false);
const zmienDostawceError = ref('');

const dostawcyZmianaOptions = computed(() => {
    const aktualnyId = selectedZmienDostawceZamowienie.value?.dostawca?.id;
    return dostawcy.value
        .filter(d => d.id !== aktualnyId)
        .map(d => ({ label: d.nazwa_firmy + (d.email ? ` — ${d.email}` : ''), value: d.id }));
});

const nowyDostawcaInfo = computed(() => {
    if (!nowyDostawcaId.value) return null;
    return dostawcy.value.find(d => d.id === nowyDostawcaId.value) || null;
});

const openZmienDostawceModal = (zamowienie) => {
    selectedZmienDostawceZamowienie.value = zamowienie;
    nowyDostawcaId.value = null;
    zmienDostawceError.value = '';
    zmienDostawceModalVisible.value = true;
};

const confirmZmienDostawce = async () => {
    if (!selectedZmienDostawceZamowienie.value || !nowyDostawcaId.value) return;
    isZmianaDostawcy.value = true;
    zmienDostawceError.value = '';
    try {
        await axios.post(`${API_URL}/zamowienia/zmien-dostawce/`, {
            zamowienie_id: selectedZmienDostawceZamowienie.value.id,
            dostawca_id: nowyDostawcaId.value,
        });
        zmienDostawceModalVisible.value = false;
        selectedZmienDostawceZamowienie.value = null;
        nowyDostawcaId.value = null;
        await fetchInitialData();
    } catch (error) {
        zmienDostawceError.value = error.response?.data?.error || error.message;
    } finally {
        isZmianaDostawcy.value = false;
    }
};

// Cofnięcie z "Wysłane" do "Zatwierdzone" — dla przypadku zmiany dostawcy
const cofnijDoZatwierdzoneModalVisible = ref(false);
const selectedCofnijZamowienie = ref(null);
const isCofajacDoZatwierdzone = ref(false);

const openCofnijDoZatwierdzoneModal = (zamowienie) => {
    selectedCofnijZamowienie.value = zamowienie;
    cofnijDoZatwierdzoneModalVisible.value = true;
};

const confirmCofnijDoZatwierdzone = async () => {
    if (!selectedCofnijZamowienie.value) return;
    isCofajacDoZatwierdzone.value = true;
    try {
        await axios.post(`${API_URL}/zamowienia/cofnij-do-zatwierdzone/`, {
            zamowienie_id: selectedCofnijZamowienie.value.id
        });
        cofnijDoZatwierdzoneModalVisible.value = false;
        selectedCofnijZamowienie.value = null;
        await fetchInitialData();
    } catch (error) {
        alert('Błąd: ' + (error.response?.data?.error || error.message));
    } finally {
        isCofajacDoZatwierdzone.value = false;
    }
};

// Edycja pozycji zamówienia
const updatePozycja = async (pozycja) => {
    try {
        await axios.patch(`${API_URL}/pozycje-zamowien/${pozycja.id}/`, {
            ilosc_zamowiona: pozycja.ilosc_zamowiona
        });
        await refreshSelectedZamowienie();
    } catch (error) {
        alert('Błąd aktualizacji: ' + (error.response?.data?.detail || error.message));
    }
};

const saveAllPozycje = async () => {
    if (!selectedZamowienie.value) return;
    isSavingPozycje.value = true;
    const editIlosc = canEditPozycje.value;
    try {
        for (const poz of selectedZamowienie.value.pozycje) {
            const payload = { cena_jednostkowa: poz.cena_jednostkowa || 0 };
            if (editIlosc) payload.ilosc_zamowiona = poz.ilosc_zamowiona;
            await axios.patch(`${API_URL}/pozycje-zamowien/${poz.id}/`, payload);
        }
        await fetchInitialData();
        closeDetails();
    } catch (error) {
        alert('Błąd zapisu: ' + (error.response?.data?.detail || error.message));
    } finally {
        isSavingPozycje.value = false;
    }
};

const closeDetails = () => {
    detailsModalVisible.value = false;
    selectedZamowienie.value = null;
    setTimeout(() => fetchInitialData(), 500);
};

const deletePozycja = async (pozycja) => {
    try {
        await axios.delete(`${API_URL}/pozycje-zamowien/${pozycja.id}/`);
        await refreshSelectedZamowienie();
    } catch (error) {
        alert('Błąd usuwania: ' + (error.response?.data?.detail || error.message));
    }
};

const refreshSelectedZamowienie = async () => {
    if (!selectedZamowienie.value) return;
    await fetchInitialData();
    const updated = zamowienia.value.find(z => z.id === selectedZamowienie.value.id);
    if (updated) {
        selectedZamowienie.value = updated;
    } else {
        detailsModalVisible.value = false;
    }
};

const generujAutomatyczne = () => {
    window.location.href = props.urls.generator || '/generator/';
};

const realizacjaModalTitle = computed(() => {
    if (!selectedRealizacjaZamowienie.value) return 'Realizacja zamówienia';
    return selectedRealizacjaZamowienie.value.status === 'partially_received'
        ? 'Kontynuuj realizację zamówienia'
        : 'Realizacja zamówienia — przyjęcie towaru';
});

const hasSelectedPozycje = computed(() => {
    return realizacjaPozycje.value.some(p => p.przyjmij && p.ilosc_pozostala > 0);
});

const rozpocznijRealizacje = async (zamowienie) => {
    selectedRealizacjaZamowienie.value = zamowienie;
    realizacjaError.value = '';
    realizacjaSelectAll.value = false;
    realizacjaPozycje.value = [];
    isLoadingRealizacja.value = true;
    realizacjaConfirmModalVisible.value = true;

    try {
        const res = await axios.get(`${API_URL}/zamowienia/${zamowienie.id}/stan_realizacji/`);
        realizacjaPozycje.value = res.data.pozycje.map(poz => ({
            ...poz,
            przyjmij: false,
            ilosc_do_przyjecia: poz.ilosc_pozostala,
        }));
    } catch (error) {
        realizacjaError.value = 'Błąd ładowania danych: ' + (error.response?.data?.error || error.message);
    } finally {
        isLoadingRealizacja.value = false;
    }
};

const toggleSelectAll = () => {
    const val = realizacjaSelectAll.value;
    realizacjaPozycje.value.forEach(poz => {
        if (poz.ilosc_pozostala > 0) {
            poz.przyjmij = val;
            if (val) poz.ilosc_do_przyjecia = poz.ilosc_pozostala;
        }
    });
};

const confirmRealizuj = async () => {
    realizacjaError.value = '';

    const zaznaczone = realizacjaPozycje.value.filter(p => p.przyjmij && p.ilosc_pozostala > 0);
    if (zaznaczone.length === 0) {
        realizacjaError.value = 'Zaznacz przynajmniej jedną pozycję do przyjęcia.';
        return;
    }

    for (const poz of zaznaczone) {
        if (!poz.ilosc_do_przyjecia || poz.ilosc_do_przyjecia <= 0) {
            realizacjaError.value = 'Wszystkie zaznaczone pozycje muszą mieć ilość > 0.';
            return;
        }
        if (poz.ilosc_do_przyjecia > poz.ilosc_pozostala) {
            realizacjaError.value = `Ilość do przyjęcia nie może przekroczyć pozostałej (${poz.narzedzie_opis}).`;
            return;
        }
    }

    isRealizujLoading.value = true;

    try {
        const pozycje_dane = zaznaczone.map(poz => ({
            pozycja_zamowienia_id: poz.pozycja_zamowienia_id,
            ilosc_przyjeta: poz.ilosc_do_przyjecia,
        }));

        const response = await axios.post(
            `${API_URL}/zamowienia/${selectedRealizacjaZamowienie.value.id}/realizuj/`,
            { pozycje: pozycje_dane }
        );

        if (response.data.success) {
            realizacjaConfirmModalVisible.value = false;
            realizacjaResult.value = {
                success: true,
                message: response.data.message,
                egzemplarze: response.data.utworzone_egzemplarze || [],
            };
            realizacjaResultModalVisible.value = true;
            await fetchInitialData();
        }
    } catch (error) {
        realizacjaError.value = error.response?.data?.error || 'Wystąpił błąd podczas realizacji.';
    } finally {
        isRealizujLoading.value = false;
    }
};

const fetchZamowienia = async () => {
    try {
        const res = await axios.get(`${API_URL}/zamowienia/`);
        zamowienia.value = res.data.results || res.data;
    } catch (error) {
        console.error("Błąd ładowania zamówień:", error);
    }
};

const fetchInitialData = async () => {
    try {
        const [zamRes, dosRes, emailRes] = await Promise.all([
            axios.get(`${API_URL}/zamowienia/`),
            axios.get(`${API_URL}/dostawcy/`),
            axios.get('/api/email/config/')
        ]);
        zamowienia.value = zamRes.data.results || zamRes.data;
        dostawcy.value = dosRes.data;
        zamowieniaTestowe.value = emailRes.data.zamowienia_testowe || false;
        emailTestAddress.value = emailRes.data.email_test_address || '';
        emailSzef.value = emailRes.data.email_szef || '';
    } catch (error) {
        console.error("Błąd ładowania danych:", error);
    }
};

onMounted(() => fetchInitialData());
</script>

<style scoped>
.zamowienia-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
}

.app-main {
    flex: 1;
    padding: 16px 24px;
    min-height: 0;
}

.orders-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.approval-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    margin-top: 12px;
    background: rgba(253, 126, 20, 0.1);
    border-radius: 6px;
    border: 1px solid rgba(253, 126, 20, 0.3);
}

.approval-total {
    font-size: 1.1em;
    color: #fd7e14;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
    background: #212529;
}

.order-link {
    color: #ffc107;
    text-decoration: none;
}

.order-link:hover {
    text-decoration: underline;
    color: #ffda6a;
}

.order-details .details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.about-content { text-align: center; }
.about-header { margin-bottom: 24px; }
.about-logo { width: 80px; height: 80px; }
.about-table { width: 100%; text-align: left; }
.about-table td { padding: 8px 0; color: var(--dark-text-primary); }
.about-table .label { text-align: right; color: var(--dark-text-muted); padding-right: 16px; width: 40%; }
.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }

.realizacja-modal-content { min-height: 200px; }

.realizacja-info-bar {
    display: flex;
    gap: 24px;
    align-items: center;
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.realizacja-toolbar {
    margin-bottom: 12px;
    padding: 8px 0;
}

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

.text-green { color: #69db7c; font-weight: 600; }
.text-orange { color: #ffa94d; font-weight: 600; }
.text-muted { color: #868e96; }
.unit-label { font-size: 0.8em; color: #868e96; margin-left: 4px; }

:deep(.qty-input) { width: 70px !important; text-align: center; }
</style>

<template>
    <div class="ustawienia-app">
        <!-- Nagłówek -->
        <header class="app-header">
            <h2 class="header-title">USTAWIENIA</h2>
            <div class="header-buttons">
                <a :href="backUrl" class="btn btn-danger">
                    <i class="pi pi-arrow-left"></i> Wróć
                </a>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="app-main">
            <TabView>
                <!-- Kategorie -->
                <TabPanel header="Kategorie">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Zarządzaj Kategoriami i Podkategoriami</h3>
                        </div>
                        <div class="panel-body categories-grid">
                            <div class="categories-left">
                                <div class="section-header">
                                    <h5>Kategorie Główne</h5>
                                    <button class="btn btn-primary" @click="openModal('kategoria', 'add')">
                                        <i class="pi pi-plus"></i> Dodaj
                                    </button>
                                </div>
                                <Listbox v-model="selectedKategoriaId" :options="kategorieOptions" optionLabel="label" optionValue="value" class="categories-list" @change="onKategoriaSelect">
                                    <template #option="{ option }">
                                        <div class="category-item">
                                            <span>
                                                {{ option.label }}
                                                <Badge :value="option.count" severity="secondary" />
                                                <span v-if="option.item.grupa_stanowiska" class="grupa-stanowiska-badge" :title="`Widoczna tylko dla stanowiska: ${option.item.grupa_stanowiska}`">{{ option.item.grupa_stanowiska }}</span>
                                            </span>
                                            <div class="category-actions" @click.stop>
                                                <button class="btn btn-secondary btn-icon" @click="openModal('kategoria', 'edit', option.item)" title="Edycja">
                                                    <i class="pi pi-pencil"></i>
                                                </button>
                                                <button class="btn btn-danger btn-icon" @click="showDeleteModal('kategoria', option.item.id)" title="Usuń">
                                                    <i class="pi pi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </template>
                                </Listbox>
                            </div>
                            <div class="categories-right">
                                <div v-if="!selectedKategoriaId" class="empty-state">
                                    Wybierz kategorię główną, aby zobaczyć podkategorie.
                                </div>
                                <div v-else>
                                    <div class="section-header">
                                        <h5>Podkategorie dla: <strong class="kategoria-nazwa-bright">{{ selectedKategoriaNazwa }}</strong></h5>
                                        <button class="btn btn-primary" @click="openModal('podkategoria', 'add')">
                                            <i class="pi pi-plus"></i> Dodaj
                                        </button>
                                    </div>
                                    <div v-if="podkategorie.length === 0" class="empty-state">Brak podkategorii.</div>
                                    <div v-else class="subcategories-list">
                                        <div v-for="item in podkategorie" :key="item.id" class="subcategory-item">
                                            <span>{{ item.nazwa }}</span>
                                            <div class="subcategory-actions">
                                                <button class="btn btn-secondary btn-icon" @click="openModal('podkategoria', 'edit', item)" title="Edycja">
                                                    <i class="pi pi-pencil"></i>
                                                </button>
                                                <button class="btn btn-danger btn-icon" @click="showDeleteModal('podkategoria', item.id)" title="Usuń">
                                                    <i class="pi pi-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </TabPanel>

                <!-- Maszyny -->
                <TabPanel header="Maszyny">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Zarządzaj Maszynami</h3>
                            <button class="btn btn-primary" @click="openModal('machine', 'add')">
                                <i class="pi pi-plus"></i> Dodaj nową
                            </button>
                        </div>
                        <div class="panel-body">
                            <DataTable :value="machines" :scrollable="true" scrollHeight="flex">
                                <Column field="nazwa" header="Nazwa" />
                                <Column header="Akcje" style="width: 120px; text-align: center;">
                                    <template #body="{ data }">
                                        <button class="btn btn-secondary btn-icon mr-1" @click="openModal('machine', 'edit', data)" title="Edycja">
                                            <i class="pi pi-pencil"></i>
                                        </button>
                                        <button class="btn btn-danger btn-icon" @click="showDeleteModal('machine', data.id)" title="Usuń">
                                            <i class="pi pi-trash"></i>
                                        </button>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>
                </TabPanel>

                <!-- Lokalizacje -->
                <TabPanel header="Lokalizacje">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Zarządzaj Lokalizacjami</h3>
                            <div class="header-actions">
                                <button class="btn btn-primary" @click="openModal('location', 'add')">
                                    <i class="pi pi-plus"></i> Dodaj nową
                                </button>
                                <button class="btn btn-success ml-2" @click="openBulkAddModal">
                                    <i class="pi pi-th-large"></i> Dodaj seryjnie
                                </button>
                            </div>
                        </div>
                        <div class="panel-body">
                            <DataTable :value="locations" :scrollable="true" scrollHeight="flex">
                                <Column field="szafa" header="Szafa" />
                                <Column field="polka" header="Półka" />
                                <Column field="kolumna" header="Kolumna" />
                                <Column header="Akcje" style="width: 120px; text-align: center;">
                                    <template #body="{ data }">
                                        <button class="btn btn-secondary btn-icon mr-1" @click="openModal('location', 'edit', data)" title="Edycja">
                                            <i class="pi pi-pencil"></i>
                                        </button>
                                        <button class="btn btn-danger btn-icon" @click="showDeleteModal('location', data.id)" title="Usuń">
                                            <i class="pi pi-trash"></i>
                                        </button>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>
                </TabPanel>

                <!-- Dostawcy -->
                <TabPanel header="Dostawcy">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Zarządzaj Dostawcami</h3>
                            <button class="btn btn-primary" @click="openModal('supplier', 'add')">
                                <i class="pi pi-plus"></i> Dodaj nowego
                            </button>
                        </div>
                        <div class="panel-body">
                            <DataTable :value="suppliers" :scrollable="true" scrollHeight="flex">
                                <Column field="kod_dostawcy" header="Kod" />
                                <Column field="nazwa_firmy" header="Nazwa Firmy" />
                                <Column field="nip" header="NIP" />
                                <Column field="adres" header="Adres" />
                                <Column field="telefon" header="Telefon" />
                                <Column field="email" header="Email" />
                                <Column header="Akcje" style="width: 120px; text-align: center;">
                                    <template #body="{ data }">
                                        <button class="btn btn-secondary btn-icon mr-1" @click="openModal('supplier', 'edit', data)" title="Edycja">
                                            <i class="pi pi-pencil"></i>
                                        </button>
                                        <button class="btn btn-danger btn-icon" @click="showDeleteModal('supplier', data.id)" title="Usuń">
                                            <i class="pi pi-trash"></i>
                                        </button>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>
                </TabPanel>

                <!-- Poczta -->
                <TabPanel header="Poczta">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Konfiguracja Poczty Email</h3>
                        </div>
                        <div class="panel-body">
                            <div v-if="emailLoading" class="loading-spinner">
                                <ProgressSpinner />
                                <p>Ładowanie konfiguracji...</p>
                            </div>
                            <div v-else>
                                <div class="email-config-table">
                                    <div class="config-row">
                                        <span class="config-label" style="color: #4dabf7;">Zamówienia testowe</span>
                                        <span class="config-value-inline">
                                            <button class="btn-toggle-testowe" :class="zamowieniaTestowe ? 'active' : ''" @click="openTestoweModal()">
                                                {{ zamowieniaTestowe ? 'TRUE' : 'FALSE' }}
                                            </button>
                                            <span class="text-muted" style="margin-left: 20px; font-size: 0.85rem;">Emaile z zamówieniami będą wysyłane na adres testowy zamiast do dostawcy</span>
                                        </span>
                                    </div>
                                    <div class="config-row"><span class="config-label">Serwer SMTP</span><span>{{ emailConfig.email_host }}</span></div>
                                    <div class="config-row"><span class="config-label">Port</span><span>{{ emailConfig.email_port }}</span></div>
                                    <div class="config-row"><span class="config-label">Użyj SSL</span><Tag :severity="emailConfig.email_use_ssl ? 'success' : 'secondary'" :value="emailConfig.email_use_ssl ? 'TAK' : 'NIE'" /></div>
                                    <div class="config-row"><span class="config-label">Użyj TLS</span><Tag :severity="emailConfig.email_use_tls ? 'success' : 'secondary'" :value="emailConfig.email_use_tls ? 'TAK' : 'NIE'" /></div>
                                    <div class="config-row"><span class="config-label">Konto email</span><span>{{ emailConfig.email_host_user }}</span></div>
                                    <div class="config-row"><span class="config-label">Email nadawcy</span><span>{{ emailConfig.default_from_email }}</span></div>
                                    <div class="config-row"><span class="config-label">Adres testowy</span><span>{{ emailConfig.email_test_address }}</span></div>
                                    <div class="config-row"><span class="config-label">Adres DW</span><span>{{ emailConfig.email_dw || '-' }}</span></div>
                                    <div class="config-row"><span class="config-label">Adres Szefa</span><span>{{ emailConfig.email_szef || '-' }}</span></div>
                                    <div class="config-row">
                                        <span class="config-label">Status SMTP</span>
                                        <Tag :severity="emailConfig.email_configured ? 'success' : 'danger'" :value="emailConfig.email_configured ? 'Skonfigurowane' : 'Brak konfiguracji'" :icon="emailConfig.email_configured ? 'pi pi-check' : 'pi pi-exclamation-triangle'" />
                                    </div>

                                    <!-- IMAP — kopia w Wysłane -->
                                    <div class="config-row" style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;">
                                        <span class="config-label" style="color: #4dabf7;">Kopia w Wysłane (IMAP)</span>
                                        <span></span>
                                    </div>
                                    <div class="config-row"><span class="config-label">Serwer IMAP</span><span>{{ emailConfig.imap_host || '-' }}</span></div>
                                    <div class="config-row"><span class="config-label">Port IMAP</span><span>{{ emailConfig.imap_port || '-' }}</span></div>
                                    <div class="config-row">
                                        <span class="config-label">Użyj SSL (IMAP)</span>
                                        <Tag :severity="emailConfig.imap_use_ssl ? 'success' : 'secondary'" :value="emailConfig.imap_use_ssl ? 'TAK' : 'NIE'" />
                                    </div>
                                    <div class="config-row"><span class="config-label">Folder Wysłane</span><span>{{ emailConfig.imap_sent_folder || '-' }}</span></div>
                                    <div class="config-row">
                                        <span class="config-label">Status IMAP</span>
                                        <Tag :severity="emailConfig.imap_configured ? 'success' : 'secondary'" :value="emailConfig.imap_configured ? 'Skonfigurowane' : 'Wyłączone'" :icon="emailConfig.imap_configured ? 'pi pi-check' : 'pi pi-minus'" />
                                    </div>
                                </div>

                                <Divider />

                                <div class="email-test-row">
                                    <button
                                        class="btn btn-primary"
                                        @click="sendTestEmail"
                                        :disabled="emailTestSending || !emailConfig.email_configured"
                                    >
                                        <i :class="emailTestSending ? 'pi pi-spin pi-spinner' : 'pi pi-send'"></i>
                                        {{ emailTestSending ? 'Wysyłanie...' : 'Test wysyłki' }}
                                    </button>
                                    <span class="text-muted email-test-info">Wyślij testowy email na adres: <strong>{{ emailConfig.email_test_address }}</strong></span>
                                </div>

                                <Message v-if="emailTestResult" :severity="emailTestResult.success ? 'success' : 'error'" :closable="false" class="mt-3">
                                    {{ emailTestResult.message }}
                                </Message>

                                <Message v-if="!emailConfig.email_configured" severity="warn" :closable="false" class="mt-3">
                                    Skonfiguruj konto email w pliku <code>settings.py</code> aby móc wysyłać wiadomości.
                                </Message>

                            </div>
                        </div>
                    </div>
                </TabPanel>

                <!-- Dokumenty -->
                <TabPanel header="Dokumenty">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Wzory dokumentów</h3>
                        </div>
                        <div class="panel-body">
                            <div class="documents-grid">
                                <!-- Karta zapotrzebowania -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-file-pdf document-icon"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Karta zapotrzebowania</h4>
                                        <p class="text-muted">Wzór dokumentu zamówienia narzędzi</p>
                                        <p class="document-version">Wersja: {{ infoProgram?.PDF_ZAPOTRZEBOWANIE_WERSJA || '-' }} | Data: {{ infoProgram?.PDF_ZAPOTRZEBOWANIE_DATA || '-' }}</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-download" class="p-button-info p-button-sm" @click="downloadDocumentTemplate('zapotrzebowanie')" />
                                        <Button label="Drukuj" icon="pi pi-print" class="p-button-secondary p-button-sm" @click="printDocumentTemplate('zapotrzebowanie')" />
                                    </div>
                                </div>

                                <!-- Karta uszkodzenia -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-file-pdf document-icon"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Karta uszkodzenia</h4>
                                        <p class="text-muted">Wzór dokumentu zgłoszenia uszkodzenia narzędzia</p>
                                        <p class="document-version">Wersja: {{ infoProgram?.PDF_USZKODZENIE_WERSJA || '-' }} | Data: {{ infoProgram?.PDF_USZKODZENIE_DATA || '-' }}</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-download" class="p-button-info p-button-sm" @click="downloadDocumentTemplate('uszkodzenie')" />
                                        <Button label="Drukuj" icon="pi pi-print" class="p-button-secondary p-button-sm" @click="printDocumentTemplate('uszkodzenie')" />
                                    </div>
                                </div>

                                <!-- Logi -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-file-pdf document-icon"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Raport logów</h4>
                                        <p class="text-muted">Wzór raportu z logów systemowych</p>
                                        <p class="document-version">Wersja: {{ infoProgram?.PDF_LOGI_WERSJA || '-' }} | Data: {{ infoProgram?.PDF_LOGI_DATA || '-' }}</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-download" class="p-button-info p-button-sm" @click="downloadDocumentTemplate('logi')" />
                                        <Button label="Drukuj" icon="pi pi-print" class="p-button-secondary p-button-sm" @click="printDocumentTemplate('logi')" />
                                    </div>
                                </div>

                                <!-- Lista uszkodzeń -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-file-pdf document-icon"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Lista uszkodzeń</h4>
                                        <p class="text-muted">Wzór listy uszkodzonych narzędzi</p>
                                        <p class="document-version">Wersja: {{ infoProgram?.PDF_LISTA_USZKODZEN_WERSJA || '-' }} | Data: {{ infoProgram?.PDF_LISTA_USZKODZEN_DATA || '-' }}</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-download" class="p-button-info p-button-sm" @click="downloadDocumentTemplate('lista_uszkodzen')" />
                                        <Button label="Drukuj" icon="pi pi-print" class="p-button-secondary p-button-sm" @click="printDocumentTemplate('lista_uszkodzen')" />
                                    </div>
                                </div>

                                <!-- Inwentura startowa -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-file-pdf document-icon"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Inwentura startowa</h4>
                                        <p class="text-muted">Wzór arkusza do przeprowadzenia inwentury magazynowej</p>
                                        <p class="document-version">Wersja: {{ infoProgram?.PDF_INWENTURA_WERSJA || '-' }} | Data: {{ infoProgram?.PDF_INWENTURA_DATA || '-' }}</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-download" class="p-button-info p-button-sm" @click="downloadDocumentTemplate('inwentura')" />
                                        <Button label="Drukuj" icon="pi pi-print" class="p-button-secondary p-button-sm" @click="printDocumentTemplate('inwentura')" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </TabPanel>

                <!-- Użytkownicy (tylko administrator + logistyka) -->
                <TabPanel header="Użytkownicy" v-if="canManageUsers">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Zarządzaj Użytkownikami</h3>
                            <button class="btn btn-primary" @click="openUserModal()">
                                <i class="pi pi-plus"></i> Dodaj użytkownika
                            </button>
                        </div>
                        <div class="panel-body">
                            <DataTable :value="users" :loading="isLoadingUsers" :scrollable="true" scrollHeight="flex" dataKey="id" :paginator="users.length > 25" :rows="25">
                                <Column field="username" header="Login" style="width: 160px;" />
                                <Column header="Imię i nazwisko" style="width: 220px;">
                                    <template #body="{ data }">
                                        {{ data.first_name }} {{ data.last_name }}
                                    </template>
                                </Column>
                                <Column field="email" header="Email" style="width: 220px;" />
                                <Column header="Karta" style="width: 140px;">
                                    <template #body="{ data }">
                                        <span v-if="data.karta">{{ data.karta }}</span>
                                        <span v-else class="text-muted">-</span>
                                    </template>
                                </Column>
                                <Column header="Grupy" style="min-width: 220px;">
                                    <template #body="{ data }">
                                        <Tag v-for="g in data.groups" :key="g.id" :value="g.name" class="group-tag" />
                                        <span v-if="!data.groups || !data.groups.length" class="text-muted">-</span>
                                    </template>
                                </Column>
                                <Column header="Pobieranie narzędzi" style="width: 130px; text-align: center;">
                                    <template #body="{ data }">
                                        <Tag v-if="data.pobieranie_narzedzi" value="Tak" severity="success" />
                                        <Tag v-else value="Nie" severity="secondary" />
                                    </template>
                                </Column>
                                <Column header="Aktywny" style="width: 90px; text-align: center;">
                                    <template #body="{ data }">
                                        <Tag v-if="data.is_active" value="Tak" severity="success" />
                                        <Tag v-else value="Nie" severity="danger" />
                                    </template>
                                </Column>
                                <Column header="Akcje" style="width: 130px; text-align: center;">
                                    <template #body="{ data }">
                                        <button class="btn btn-secondary btn-icon mr-1" @click="openUserModal(data)" title="Edytuj">
                                            <i class="pi pi-pencil"></i>
                                        </button>
                                        <button class="btn btn-danger btn-icon" @click="confirmDeleteUser(data)" title="Usuń">
                                            <i class="pi pi-trash"></i>
                                        </button>
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </div>
                </TabPanel>

                <!-- Eksporty -->
                <TabPanel header="Eksporty">
                    <div class="settings-panel">
                        <div class="panel-header">
                            <h3>Eksport danych</h3>
                        </div>
                        <div class="panel-body">
                            <div class="documents-grid">
                                <!-- Inwentura startowa -->
                                <div class="document-card">
                                    <div class="document-preview">
                                        <i class="pi pi-box document-icon" style="color: #198754;"></i>
                                    </div>
                                    <div class="document-info">
                                        <h4>Inwentura startowa</h4>
                                        <p class="text-muted">Pełny stan magazynowy na dzień wydruku - do przeprowadzenia inwentury</p>
                                        <p class="document-version">Generuje listę wszystkich narzędzi z ilościami i lokalizacjami</p>
                                    </div>
                                    <div class="document-actions">
                                        <Button label="PDF" icon="pi pi-file-pdf" class="p-button-danger p-button-sm" @click="downloadInwenturaPdf" :loading="inwenturaLoading.pdf" />
                                        <Button label="XLS" icon="pi pi-file-excel" class="p-button-success p-button-sm" @click="downloadInwenturaXls" :loading="inwenturaLoading.xls" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </TabPanel>
            </TabView>
        </main>

        <!-- Modal: Zamówienia testowe -->
        <Dialog v-model:visible="testoweModalVisible" header="Zamówienia testowe" :modal="true" :style="{ width: '450px' }">
            <div class="field" style="margin-bottom: 15px;">
                <label class="zamowienia-testowe-modal-label">
                    <input type="checkbox" v-model="testoweModalValue" style="width: 18px; height: 18px; cursor: pointer; accent-color: #ffc107;" />
                    <span style="margin-left: 10px;">Włącz tryb zamówień testowych</span>
                </label>
                <p class="text-muted" style="margin-top: 10px; font-size: 0.85rem;">
                    Gdy włączone, emaile z zamówieniami będą wysyłane na adres testowy
                    (<strong>{{ emailConfig.email_test_address }}</strong>) zamiast do dostawcy.
                </p>
            </div>
            <template #footer>
                <Button label="Zapisz" icon="pi pi-check" severity="danger" @click="saveTestoweModal" />
                <Button label="Anuluj" icon="pi pi-times" severity="secondary" @click="testoweModalVisible = false" />
            </template>
        </Dialog>

        <!-- Ukryty iframe do drukowania -->
        <iframe id="print-frame" style="display: none;"></iframe>

        <!-- Modal: Edycja/Dodawanie -->
        <Dialog v-model:visible="modalVisible" :header="modal.title" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <Message v-if="modal.errorMessage" severity="error" :closable="false">{{ modal.errorMessage }}</Message>

                <!-- Kategoria -->
                <template v-if="modal.type === 'kategoria'">
                    <div class="field">
                        <label>Nazwa Kategorii Głównej</label>
                        <InputText v-model="modal.currentItem.nazwa" />
                    </div>
                    <div class="field">
                        <label>
                            Grupa stanowiska
                            <small class="text-muted"> (opcjonalne — ogranicza widoczność dla tokarza/frezera/ślusarza)</small>
                        </label>
                        <Dropdown
                            v-model="modal.currentItem.grupa_stanowiska"
                            :options="grupyStanowiskOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Wybierz grupę"
                        />
                    </div>
                </template>

                <!-- Podkategoria -->
                <template v-if="modal.type === 'podkategoria'">
                    <div class="field">
                        <label>Kategoria Nadrzędna</label>
                        <Dropdown v-model="modal.currentItem.kategoria" :options="kategorieDropdownOptions" optionLabel="label" optionValue="value" :disabled="modal.mode === 'add'" />
                    </div>
                    <div class="field">
                        <label>Nazwa Podkategorii</label>
                        <InputText v-model="modal.currentItem.nazwa" />
                    </div>
                </template>

                <!-- Maszyna -->
                <template v-if="modal.type === 'machine'">
                    <div class="field">
                        <label>Nazwa</label>
                        <InputText v-model="modal.currentItem.nazwa" />
                    </div>
                </template>

                <!-- Lokalizacja -->
                <template v-if="modal.type === 'location'">
                    <div class="field"><label>Szafa</label><InputText v-model="modal.currentItem.szafa" /></div>
                    <div class="field"><label>Półka</label><InputText v-model="modal.currentItem.polka" /></div>
                    <div class="field"><label>Kolumna</label><InputText v-model="modal.currentItem.kolumna" /></div>
                </template>

                <!-- Dostawca -->
                <template v-if="modal.type === 'supplier'">
                    <div class="field"><label>Kod dostawcy</label><InputText v-model="modal.currentItem.kod_dostawcy" /></div>
                    <div class="field"><label>Nazwa firmy</label><InputText v-model="modal.currentItem.nazwa_firmy" /></div>
                    <div class="field"><label>NIP</label><InputText v-model="modal.currentItem.nip" /></div>
                    <div class="field"><label>Adres</label><Textarea v-model="modal.currentItem.adres" rows="2" /></div>
                    <div class="field"><label>Telefon</label><InputText v-model="modal.currentItem.telefon" /></div>
                    <div class="field"><label>Email</label><InputText v-model="modal.currentItem.email" /></div>
                </template>

            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="modalVisible = false" />
                <Button label="Zapisz" icon="pi pi-check" @click="saveItem" />
            </template>
        </Dialog>

        <!-- Modal: Usuwanie -->
        <Dialog v-model:visible="deleteModalVisible" header="Potwierdź usunięcie" :modal="true" :style="{ width: '450px' }">
            <p>{{ deleteModal.message }}</p>
            <p class="text-danger">Tej operacji nie można cofnąć.</p>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteModalVisible = false" />
                <Button label="Tak, usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteItem" />
            </template>
        </Dialog>

        <!-- Modal: Dodaj seryjnie -->
        <!-- Modal: Dodaj/Edytuj użytkownika -->
        <Dialog v-model:visible="userModalVisible" :header="isEditUserMode ? 'Edytuj użytkownika' : 'Dodaj użytkownika'" :modal="true" :style="{ width: '520px' }">
            <div class="p-fluid">
                <Message v-if="userModalError" severity="error" :closable="false">{{ userModalError }}</Message>
                <div class="field">
                    <label>Login <span class="required">*</span></label>
                    <InputText v-model="currentUser.username" :disabled="isEditUserMode" autocomplete="off" />
                </div>
                <div class="field-row">
                    <div class="field">
                        <label>Imię</label>
                        <InputText v-model="currentUser.first_name" autocomplete="off" />
                    </div>
                    <div class="field">
                        <label>Nazwisko</label>
                        <InputText v-model="currentUser.last_name" autocomplete="off" />
                    </div>
                </div>
                <div class="field">
                    <label>Email</label>
                    <InputText v-model="currentUser.email" autocomplete="off" />
                </div>
                <div class="field">
                    <label>
                        Hasło
                        <span v-if="!isEditUserMode" class="required">*</span>
                        <small v-else class="text-muted"> (puste = bez zmiany)</small>
                    </label>
                    <InputText v-model="currentUser.password" type="password" autocomplete="new-password" />
                </div>
                <div class="field">
                    <label>Grupa</label>
                    <Dropdown v-model="currentUser.group_id" :options="grupyDoWyboru" optionLabel="name" optionValue="id" placeholder="Wybierz grupę" class="user-group-dropdown" />
                </div>
                <div class="field">
                    <label>Karta RFID (opcjonalnie)</label>
                    <InputText v-model="currentUser.karta" placeholder="np. 1234567890" autocomplete="off" />
                </div>
                <div class="field">
                    <div class="checkbox-row">
                        <Checkbox v-model="currentUser.pobieranie_narzedzi" :binary="true" inputId="pobieranie_narzedzi" />
                        <label for="pobieranie_narzedzi" class="checkbox-label">Pobieranie narzędzi (widoczny na listach wyboru pracownika)</label>
                    </div>
                </div>
                <div class="field">
                    <div class="checkbox-row">
                        <Checkbox v-model="currentUser.is_active" :binary="true" inputId="is_active" />
                        <label for="is_active" class="checkbox-label">Aktywny (może się zalogować)</label>
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="userModalVisible = false" />
                <Button :label="isEditUserMode ? 'Zapisz zmiany' : 'Dodaj'" icon="pi pi-check" @click="saveUser" :loading="isSavingUser" />
            </template>
        </Dialog>

        <!-- Modal: Potwierdź usunięcie użytkownika -->
        <Dialog v-model:visible="deleteUserModalVisible" header="Potwierdź usunięcie" :modal="true" :style="{ width: '460px' }">
            <p v-if="userToDelete">
                Usunąć użytkownika
                <strong>{{ userToDelete.username }}</strong>
                ({{ userToDelete.first_name }} {{ userToDelete.last_name }})?
            </p>
            <p class="text-muted" style="font-size: 0.85rem;">
                Konto + powiązany rekord pracownika zostaną skasowane. Historia operacji zostaje (pracownik w niej jako "brak").
            </p>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteUserModalVisible = false" />
                <Button label="Usuń" icon="pi pi-trash" severity="danger" @click="deleteUserConfirmed" :loading="isDeletingUser" />
            </template>
        </Dialog>

        <Dialog v-model:visible="bulkAddModalVisible" header="Dodaj lokalizacje seryjnie" :modal="true" :style="{ width: '400px' }">
            <div class="p-fluid">
                <div class="field"><label>Nazwa/Numer szafy</label><InputText v-model="bulkAddData.szafa" placeholder="np. SZAFA-01" /></div>
                <div class="field"><label>Liczba półek (oś Y)</label><InputNumber v-model="bulkAddData.liczba_polek" :min="1" /></div>
                <div class="field"><label>Liczba kolumn (oś X)</label><InputNumber v-model="bulkAddData.liczba_kolumn" :min="1" /></div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="bulkAddModalVisible = false" />
                <Button label="Zatwierdź i stwórz" icon="pi pi-check" class="p-button-success" @click="saveBulkItems" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Textarea from 'primevue/textarea';
import Dropdown from 'primevue/dropdown';
import Listbox from 'primevue/listbox';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Dialog from 'primevue/dialog';
import Badge from 'primevue/badge';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Divider from 'primevue/divider';
import ProgressSpinner from 'primevue/progressspinner';
import Checkbox from 'primevue/checkbox';

const API_URL = '/api';

const props = defineProps({
    urls: { type: Object, default: () => ({ magazyn: '/magazyn-inertia/', zakupy: '/zakupy-inertia/' }) },
    infoProgram: { type: Object, default: () => ({}) },
    auth: { type: Object, default: () => ({ isAdministrator: false, isLogistyka: false, user: {} }) }
});

const canManageUsers = computed(() => !!(props.auth?.isAdministrator || props.auth?.isLogistyka));

// Oblicz URL powrotu na podstawie referrer lub parametru URL
const backUrl = computed(() => {
    // Sprawdź parametr URL
    const urlParams = new URLSearchParams(window.location.search);
    const fromParam = urlParams.get('from');
    if (fromParam === 'zakupy') return props.urls.zakupy;
    if (fromParam === 'magazyn') return props.urls.magazyn;
    if (fromParam === 'kierownik') return props.urls.kierownik;
    if (fromParam === 'zapotrzebowania') {
        const origin = urlParams.get('origin');
        return props.urls.zapotrzebowania + (origin ? '?from=' + origin : '');
    }

    // Sprawdź referrer
    const referrer = document.referrer;
    if (referrer.includes('zakupy')) return props.urls.zakupy;
    if (referrer.includes('kierownik')) return props.urls.kierownik;

    // Domyślnie wróć do magazynu
    return props.urls.magazyn;
});

// Data
const kategorie = ref([]);
const podkategorie = ref([]);
const machines = ref([]);
const locations = ref([]);
const suppliers = ref([]);

const selectedKategoriaId = ref(null);

const emailConfig = ref({});
const emailLoading = ref(false);
const emailTestSending = ref(false);
const emailTestResult = ref(null);
const zamowieniaTestowe = ref(false);
const testoweModalVisible = ref(false);
const testoweModalValue = ref(false);

// Inwentura
const inwenturaLoading = ref({ pdf: false, xls: false });

// Modals
const modalVisible = ref(false);
const deleteModalVisible = ref(false);
const bulkAddModalVisible = ref(false);

const modal = ref({ type: '', mode: 'add', title: '', currentItem: {}, errorMessage: '' });
const deleteModal = ref({ type: null, id: null, message: '' });
const bulkAddData = ref({ szafa: '', liczba_kolumn: 1, liczba_polek: 1 });

const endpoints = {
    kategoria: 'kategorie',
    podkategoria: 'podkategorie',
    machine: 'maszyny',
    location: 'lokalizacje',
    supplier: 'dostawcy'
};

// Computed
const kategorieOptions = computed(() => kategorie.value.map(k => ({
    label: k.nazwa,
    value: k.id,
    count: k.podkategorie?.length || 0,
    item: k
})));

const kategorieDropdownOptions = computed(() => kategorie.value.map(k => ({ label: k.nazwa, value: k.id })));

const selectedKategoriaNazwa = computed(() => {
    if (!selectedKategoriaId.value) return '';
    const kat = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    return kat ? kat.nazwa : '';
});

// Methods
const onKategoriaSelect = (event) => {
    if (event.value) {
        const kat = kategorie.value.find(k => k.id === event.value);
        podkategorie.value = kat ? kat.podkategorie : [];
    } else {
        podkategorie.value = [];
    }
};

const getInitialItem = (type) => {
    if (type === 'location') return { szafa: '', kolumna: '', polka: '' };
    if (type === 'supplier') return { kod_dostawcy: '', nazwa_firmy: '', nip: '', adres: '', telefon: '', email: '' };
    if (type === 'kategoria') return { nazwa: '', grupa_stanowiska: null };
    if (type === 'podkategoria') return { nazwa: '', kategoria: selectedKategoriaId.value };
    return { nazwa: '' };
};

const grupyStanowiskOptions = [
    { label: 'Brak', value: null },
    { label: 'tokarz', value: 'tokarz' },
    { label: 'frezer', value: 'frezer' },
    { label: 'ślusarz', value: 'ślusarz' },
];

const modalTitles = {
    kategoria: { add: 'Dodaj kategorię', edit: 'Edytuj kategorię' },
    podkategoria: { add: 'Dodaj podkategorię', edit: 'Edytuj podkategorię' },
    machine: { add: 'Dodaj maszynę', edit: 'Edytuj maszynę' },
    location: { add: 'Dodaj lokalizację', edit: 'Edytuj lokalizację' },
    supplier: { add: 'Dodaj dostawcę', edit: 'Edytuj dostawcę' }
};

const openModal = async (type, mode, item = null) => {
    modal.value.type = type;
    modal.value.mode = mode;
    modal.value.errorMessage = '';

    if (mode === 'add') {
        modal.value.title = modalTitles[type]?.add || `Dodaj ${type}`;
        modal.value.currentItem = getInitialItem(type);
    } else {
        modal.value.title = modalTitles[type]?.edit || `Edytuj ${type}`;
        if (type === 'podkategoria') {
            modal.value.currentItem = { ...item, kategoria: item.kategoria?.id || item.kategoria };
        } else {
            modal.value.currentItem = { ...item };
        }
    }
    modalVisible.value = true;
};

const saveItem = async () => {
    const endpoint = endpoints[modal.value.type];
    const method = modal.value.mode === 'add' ? 'post' : 'put';
    const url = modal.value.mode === 'add' ? `${API_URL}/${endpoint}/` : `${API_URL}/${endpoint}/${modal.value.currentItem.id}/`;

    let payload;
    if (modal.value.type === 'podkategoria') {
        payload = { nazwa: modal.value.currentItem.nazwa, kategoria_id: modal.value.currentItem.kategoria };
    } else {
        payload = modal.value.currentItem;
    }

    try {
        await axios({ method, url, data: payload });
        modalVisible.value = false;
        await fetchAllData();
        if (modal.value.type === 'podkategoria' && selectedKategoriaId.value) {
            const kat = kategorie.value.find(k => k.id === selectedKategoriaId.value);
            podkategorie.value = kat ? kat.podkategorie : [];
        }
    } catch (error) {
        console.error(`Błąd zapisu:`, error.response?.data);
        if (error.response?.data) {
            if (typeof error.response.data === 'object') {
                modal.value.errorMessage = Object.entries(error.response.data).map(([f, e]) => `${f}: ${Array.isArray(e) ? e.join(' ') : e}`).join('; ');
            } else {
                modal.value.errorMessage = error.response.data;
            }
        } else {
            modal.value.errorMessage = 'Wystąpił nieznany błąd.';
        }
    }
};

const showDeleteModal = (type, itemId) => {
    deleteModal.value.type = type;
    deleteModal.value.id = itemId;

    if (type === 'kategoria') {
        deleteModal.value.message = 'Czy na pewno chcesz trwale usunąć tę kategorię? Usunięcie kategorii głównej usunie również wszystkie jej podkategorie.';
    } else if (type === 'podkategoria') {
        deleteModal.value.message = 'Czy na pewno chcesz trwale usunąć tę podkategorię?';
    } else {
        deleteModal.value.message = 'Czy na pewno chcesz trwale usunąć ten element?';
    }

    deleteModalVisible.value = true;
};

const confirmDeleteItem = async () => {
    const endpoint = endpoints[deleteModal.value.type];
    try {
        await axios.delete(`${API_URL}/${endpoint}/${deleteModal.value.id}/`);
        deleteModalVisible.value = false;
        await fetchAllData();
    } catch (error) {
        console.error(`Błąd usuwania:`, error);
        deleteModalVisible.value = false;
        alert('Nie można usunąć elementu. Sprawdź, czy nie jest powiązany z innymi danymi.');
    }
};

const openBulkAddModal = () => {
    bulkAddData.value = { szafa: '', liczba_kolumn: 1, liczba_polek: 1 };
    bulkAddModalVisible.value = true;
};

const saveBulkItems = async () => {
    if (!bulkAddData.value.szafa || !bulkAddData.value.liczba_kolumn || !bulkAddData.value.liczba_polek) {
        alert('Wszystkie pola są wymagane.');
        return;
    }
    try {
        await axios.post(`${API_URL}/lokalizacje/dodaj_seryjnie/`, bulkAddData.value);
        bulkAddModalVisible.value = false;
        await fetchAllData();
    } catch (error) {
        console.error('Błąd:', error.response?.data);
        alert('Wystąpił błąd: ' + (error.response?.data?.error || 'Błąd serwera.'));
    }
};

const fetchEmailConfig = async () => {
    emailLoading.value = true;
    try {
        const response = await axios.get('/api/email/config/');
        emailConfig.value = response.data;
        zamowieniaTestowe.value = response.data.zamowienia_testowe || false;
    } catch (error) {
        console.error('Błąd ładowania konfiguracji email:', error);
    } finally {
        emailLoading.value = false;
    }
};

const openTestoweModal = () => {
    testoweModalValue.value = zamowieniaTestowe.value;
    testoweModalVisible.value = true;
};

const saveTestoweModal = async () => {
    try {
        await axios.post('/api/email/zamowienia-testowe/', {
            zamowienia_testowe: testoweModalValue.value
        });
        zamowieniaTestowe.value = testoweModalValue.value;
        testoweModalVisible.value = false;
    } catch (error) {
        console.error('Błąd zmiany trybu testowego:', error);
    }
};

const sendTestEmail = async () => {
    emailTestSending.value = true;
    emailTestResult.value = null;
    try {
        const response = await axios.post('/api/email/test/');
        emailTestResult.value = response.data;
    } catch (error) {
        emailTestResult.value = { success: false, message: error.response?.data?.message || 'Wystąpił błąd podczas wysyłki.' };
    } finally {
        emailTestSending.value = false;
    }
};

const fetchAllData = async () => {
    try {
        const [katRes, macRes, locRes, supRes] = await Promise.all([
            axios.get(`${API_URL}/kategorie/`),
            axios.get(`${API_URL}/maszyny/`),
            axios.get(`${API_URL}/lokalizacje/`),
            axios.get(`${API_URL}/dostawcy/`)
        ]);
        kategorie.value = (katRes.data || []).filter(item => item != null);
        machines.value = (macRes.data || []).filter(item => item != null);
        locations.value = (locRes.data || []).filter(item => item != null);
        suppliers.value = (supRes.data || []).filter(item => item != null);
    } catch (error) {
        console.error("Błąd ładowania danych:", error);
    }
};

// Computed dla infoProgram
const infoProgram = computed(() => props.infoProgram);

// Funkcje dokumentów
const downloadDocumentTemplate = async (type) => {
    try {
        const response = await axios.get(`${API_URL}/dokumenty/wzor/${type}/`, {
            responseType: 'blob'
        });

        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const link = document.createElement('a');
        link.href = url;

        const filenames = {
            'zapotrzebowanie': 'Wzor_Karta_zapotrzebowania.pdf',
            'uszkodzenie': 'Wzor_Karta_uszkodzenia.pdf',
            'logi': 'Wzor_Raport_logow.pdf',
            'lista_uszkodzen': 'Wzor_Lista_uszkodzen.pdf',
            'inwentura': 'Wzor_Inwentura_startowa.pdf'
        };
        link.setAttribute('download', filenames[type] || `Wzor_${type}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Błąd pobierania wzoru:', error);
        alert('Nie udało się pobrać wzoru dokumentu.');
    }
};

const printDocumentTemplate = async (type) => {
    try {
        const response = await axios.get(`${API_URL}/dokumenty/wzor/${type}/?print=1`, {
            responseType: 'blob'
        });

        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const printFrame = document.getElementById('print-frame');
        printFrame.src = url;

        printFrame.onload = () => {
            try {
                printFrame.contentWindow.print();
            } catch (e) {
                // Jeśli drukowanie z iframe nie działa, otwórz w nowym oknie
                window.open(url, '_blank');
            }
        };
    } catch (error) {
        console.error('Błąd drukowania wzoru:', error);
        alert('Nie udało się wydrukować wzoru dokumentu.');
    }
};

// Funkcje eksportu inwentury
const downloadInwenturaPdf = async () => {
    inwenturaLoading.value.pdf = true;
    try {
        const response = await axios.get(`${API_URL}/eksport/inwentura/pdf/`, {
            responseType: 'blob'
        });

        const today = new Date().toISOString().split('T')[0];
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Inwentura_${today}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Błąd pobierania inwentury PDF:', error);
        alert('Nie udało się wygenerować dokumentu PDF inwentury.');
    } finally {
        inwenturaLoading.value.pdf = false;
    }
};

const downloadInwenturaXls = async () => {
    inwenturaLoading.value.xls = true;
    try {
        const response = await axios.get(`${API_URL}/eksport/inwentura/xls/`, {
            responseType: 'blob'
        });

        const today = new Date().toISOString().split('T')[0];
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Inwentura_${today}.xlsx`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Błąd pobierania inwentury XLS:', error);
        alert('Nie udało się wygenerować pliku Excel inwentury.');
    } finally {
        inwenturaLoading.value.xls = false;
    }
};

// ============================================================================
// Użytkownicy — zakładka widoczna tylko dla administrator + logistyka
// ============================================================================
const users = ref([]);
const grupy = ref([]);
const isLoadingUsers = ref(false);
const userModalVisible = ref(false);
const isEditUserMode = ref(false);
const isSavingUser = ref(false);
const userModalError = ref('');
const currentUser = ref({});
const deleteUserModalVisible = ref(false);
const userToDelete = ref(null);
const isDeletingUser = ref(false);

const blankUser = () => ({
    id: null,
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    group_id: null,
    karta: '',
    pobieranie_narzedzi: true,
    is_active: true,
});

// Dropdown w modalu — bez grupy administrator (zarządzana tylko z /admin/)
const grupyDoWyboru = computed(() => grupy.value.filter(g => g.name !== 'administrator'));

const fetchUsersAndGroups = async () => {
    if (!canManageUsers.value) return;
    isLoadingUsers.value = true;
    try {
        const [usersRes, grupyRes] = await Promise.all([
            axios.get(`${API_URL}/zespol/`),
            axios.get(`${API_URL}/grupy/`),
        ]);
        users.value = usersRes.data.results || usersRes.data;
        grupy.value = grupyRes.data.results || grupyRes.data;
    } catch (error) {
        console.error('Błąd ładowania użytkowników:', error.response?.data || error.message);
    } finally {
        isLoadingUsers.value = false;
    }
};

const openUserModal = (user = null) => {
    userModalError.value = '';
    if (user) {
        isEditUserMode.value = true;
        // Jeśli user jest w wielu grupach (z legacy DB), bierzemy pierwszą non-administrator
        const firstNonAdmin = (user.groups || []).find(g => g.name !== 'administrator');
        currentUser.value = {
            id: user.id,
            username: user.username,
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            email: user.email || '',
            password: '',
            group_id: firstNonAdmin ? firstNonAdmin.id : null,
            karta: user.karta || '',
            pobieranie_narzedzi: user.pobieranie_narzedzi ?? true,
            is_active: user.is_active ?? true,
        };
    } else {
        isEditUserMode.value = false;
        currentUser.value = blankUser();
    }
    userModalVisible.value = true;
};

const saveUser = async () => {
    userModalError.value = '';
    const u = currentUser.value;
    if (!u.username || !u.username.trim()) {
        userModalError.value = 'Login jest wymagany.';
        return;
    }
    if (!isEditUserMode.value && (!u.password || u.password.length < 4)) {
        userModalError.value = 'Hasło wymagane przy tworzeniu konta (min. 4 znaki).';
        return;
    }
    isSavingUser.value = true;
    try {
        const payload = {
            username: u.username.trim(),
            first_name: u.first_name || '',
            last_name: u.last_name || '',
            email: u.email || '',
            is_active: !!u.is_active,
            group_ids: u.group_id ? [u.group_id] : [],
            karta: (u.karta || '').trim() || null,
            pobieranie_narzedzi: !!u.pobieranie_narzedzi,
        };
        if (u.password) payload.password = u.password;

        if (isEditUserMode.value) {
            await axios.patch(`${API_URL}/zespol/${u.id}/`, payload);
        } else {
            await axios.post(`${API_URL}/zespol/`, payload);
        }
        userModalVisible.value = false;
        await fetchUsersAndGroups();
    } catch (error) {
        const data = error.response?.data;
        if (data && typeof data === 'object') {
            userModalError.value = Object.entries(data)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
                .join(' • ');
        } else {
            userModalError.value = error.message || 'Błąd zapisu.';
        }
    } finally {
        isSavingUser.value = false;
    }
};

const confirmDeleteUser = (user) => {
    userToDelete.value = user;
    deleteUserModalVisible.value = true;
};

const deleteUserConfirmed = async () => {
    if (!userToDelete.value) return;
    isDeletingUser.value = true;
    try {
        await axios.delete(`${API_URL}/zespol/${userToDelete.value.id}/`);
        deleteUserModalVisible.value = false;
        userToDelete.value = null;
        await fetchUsersAndGroups();
    } catch (error) {
        alert('Błąd usunięcia: ' + (error.response?.data?.detail || error.message));
    } finally {
        isDeletingUser.value = false;
    }
};

onMounted(async () => {
    await fetchAllData();
    await fetchEmailConfig();
    await fetchUsersAndGroups();
});
</script>

<style scoped>
.ustawienia-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
    overflow: hidden;
}

.app-main {
    flex: 1;
    padding: 24px;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

/* TabView - pełna wysokość */
:deep(.p-tabview) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

:deep(.p-tabview-panels) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

:deep(.p-tabview-panel) {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

.settings-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.settings-panel .panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
}

/* DataTable scrollHeight auto */
:deep(.p-datatable-wrapper) {
    flex: 1;
    overflow: auto;
}

.panel-header h3 {
    margin: 0;
    color: #ffc107;
}

.header-actions {
    display: flex;
    gap: 8px;
}

.categories-grid {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 24px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.section-header h5 {
    margin: 0;
    color: #dee2e6;
}

.categories-list {
    width: 100%;
}

.category-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.category-actions, .subcategory-actions {
    display: flex;
    gap: 4px;
}

.subcategories-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.subcategory-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--dark-bg-tertiary);
    border-radius: 4px;
    color: var(--dark-text-primary);
}

.subcategory-item:hover {
    background: var(--dark-bg-hover);
}

.email-config-table {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.config-row {
    display: flex;
    padding: 8px 0;
    border-bottom: 1px solid var(--dark-border);
    color: var(--dark-text-primary);
}

.config-label {
    width: 200px;
    font-weight: 500;
    color: var(--dark-text-muted);
}

code {
    background: var(--dark-bg-tertiary);
    padding: 2px 6px;
    border-radius: 4px;
    color: #ffc107;
}

.email-test-row {
    display: flex;
    align-items: center;
    gap: 50px;
    margin-top: 15px;
}

.email-test-info {
    font-size: 14px;
}

.config-value-inline {
    display: flex;
    align-items: center;
}

.zamowienia-testowe-modal-label {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
    cursor: pointer;
    color: #e0e0e0;
    font-size: 1rem;
}

.zamowienia-testowe-modal-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: #ffc107;
}

.btn-toggle-testowe {
    padding: 4px 12px;
    border-radius: 4px;
    border: none;
    font-weight: 700;
    font-size: 0.8rem;
    cursor: pointer;
    background-color: #198754;
    color: #fff;
    transition: all 0.15s ease;
}

.btn-toggle-testowe.active {
    background-color: #dc3545;
}

/* Dokumenty */
.documents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    padding: 10px;
}

.document-card {
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border: 1px solid #495057;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    transition: transform 0.2s, box-shadow 0.2s;
}

.document-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.document-preview {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80px;
    background: #2b3035;
    border-radius: 6px;
}

.document-icon {
    font-size: 3rem;
    color: #dc3545;
}

.document-info h4 {
    margin: 0 0 8px 0;
    color: #fff;
    font-size: 1.1rem;
}

.document-info .text-muted {
    color: #adb5bd;
    font-size: 0.9rem;
    margin: 0 0 8px 0;
}

.document-version {
    font-size: 0.8rem;
    color: #6c757d;
    margin: 0;
}

.document-actions {
    display: flex;
    gap: 10px;
    margin-top: auto;
}

.document-actions .p-button {
    flex: 1;
}

/* Użytkownicy — modal */
.field-row { display: flex; gap: 12px; }
.field-row .field { flex: 1; }
.required { color: #dc3545; font-weight: bold; }
.checkbox-row { display: flex; align-items: center; gap: 8px; }
.checkbox-label { margin: 0; cursor: pointer; font-weight: normal; }

/* Użytkownicy — tabela */
.group-tag :deep(.p-tag-value),
.group-tag.p-tag {
    background-color: var(--dark-bg-hover, #3d444d) !important;
    color: var(--dark-text-primary, #dee2e6) !important;
    border: 1px solid var(--dark-border, #495057);
    margin-right: 4px;
    font-weight: 500;
}

/* Dropdown "Grupa" w modalu Użytkownika — szerokość pełna, spójność z resztą inputów */
.user-group-dropdown { width: 100%; }

/* Nazwa wybranej kategorii w nagłówku podkategorii — o 30% jaśniejsza */
.kategoria-nazwa-bright {
    filter: brightness(1.3);
}

/* Dyskretny badge "grupa_stanowiska" przy nazwie kategorii (tylko gdy ustawione) */
.grupa-stanowiska-badge {
    display: inline-block;
    margin-left: 6px;
    padding: 1px 7px;
    border-radius: 10px;
    font-size: 0.72rem;
    color: var(--dark-text-muted, #adb5bd);
    background-color: transparent;
    border: 1px solid var(--dark-border, #495057);
    font-style: italic;
    vertical-align: middle;
}
</style>

<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">{{ trybProdukcja ? 'NARZĘDZIA' : 'MAGAZYN' }}</h2>
            <!-- Tryb produkcja - imię na środku (poza header-buttons) -->
            <div v-if="trybProdukcja" class="header-user-name-prod">
                {{ auth.user.first_name }} {{ auth.user.last_name }}
            </div>
            <div class="header-buttons">
                <!-- Pełny tryb magazynu -->
                <template v-if="!trybProdukcja">
                    <a
                        v-if="auth.isAdministrator"
                        :href="urls.logi"
                        class="btn btn-logi"
                        title="Logi systemowe"
                    >
                        <i class="pi pi-list"></i> Logi
                    </a>
                    <div class="dropdown-wrapper">
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
                </template>
                <!-- Tryb produkcja - buttony po prawej -->
                <template v-else>
                    <a :href="urls.produkcja" class="btn-narzedzia-prod">
                        <i class="pi pi-arrow-left"></i>
                        Wróć do Produkcji
                    </a>
                    <button class="btn-exit-prod" @click="logout">
                        <i class="pi pi-sign-out"></i>
                        Wyjście
                    </button>
                </template>
            </div>
        </header>

        <!-- Główna zawartość -->
        <main class="magazyn-main">
            <!-- Górna tabela - Lista narzędzi -->
            <div class="tools-panel">
                <div class="panel-header">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="searchInput"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">Lista typów narzędzi</h3>
                    <div class="filter-box">
                        <select
                            v-model="selectedKategoriaId"
                            @change="onKategoriaChange"
                            class="form-select filter-select"
                        >
                            <option :value="null">Wszystkie kategorie</option>
                            <option v-for="kat in kategorie" :key="kat.id" :value="kat.id">
                                {{ kat.nazwa }}
                            </option>
                        </select>
                        <select
                            v-model="selectedPodkategoriaId"
                            :disabled="!selectedKategoriaId"
                            class="form-select filter-select"
                        >
                            <option :value="null">Wszystkie podkategorie</option>
                            <option v-for="pod in filteredPodkategorie" :key="pod.id" :value="pod.id">
                                {{ pod.nazwa }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredTools"
                        :loading="isLoadingTools"
                        :scrollable="true"
                        scrollHeight="flex"
                        tableLayout="fixed"
                        :virtualScrollerOptions="{ itemSize: 36 }"
                        selectionMode="single"
                        v-model:selection="selectedToolForDetails"
                        @row-select="onToolSelect"
                        @row-unselect="onToolUnselect"
                        dataKey="id"
                        class="tools-table"
                        :rowClass="rowClass"
                    >
                        <Column field="kategoria" header="Kategoria / Podkategoria">
                            <template #body="{ data }">
                                <span v-if="data.podkategoria">
                                    <strong>{{ data.podkategoria.kategoria_nazwa }}</strong> / {{ data.podkategoria.nazwa }}
                                </span>
                                <span v-else class="text-muted">Brak kategorii</span>
                            </template>
                        </Column>
                        <Column field="opis" header="Opis / Specyfikacja" />
                        <Column field="numer_katalogowy" header="Nr katalogowy">
                            <template #body="{ data }">
                                {{ data.numer_katalogowy || 'Brak' }}
                            </template>
                        </Column>
                        <Column field="ilosc_nowych" header="Nowe" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': data.ilosc_nowych === 0 }">{{ data.ilosc_nowych }}</span>
                            </template>
                        </Column>
                        <Column field="ilosc_uzywanych_dostepnych" header="Używane" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': data.ilosc_uzywanych_dostepnych === 0 }">{{ data.ilosc_uzywanych_dostepnych }}</span>
                            </template>
                        </Column>
                        <Column field="ilosc_w_uzyciu" header="W użyciu" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <span :class="{ 'zero-value': data.ilosc_w_uzyciu === 0 }">{{ data.ilosc_w_uzyciu }}</span>
                            </template>
                        </Column>
                        <Column field="calkowita_ilosc" header="Razem" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <strong :class="{ 'zero-value': data.calkowita_ilosc === 0 }">{{ data.calkowita_ilosc }}</strong>
                            </template>
                        </Column>
                        <Column v-if="!trybProdukcja" header="" style="width: 100px; text-align: center;">
                            <template #header>
                                <Button icon="pi pi-plus" class="p-button-success p-button-sm" @click.stop="openToolModal()" title="Dodaj nowy typ narzędzia" />
                            </template>
                            <template #body="{ data }">
                                <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click.stop="openToolModal(data)" title="Edytuj typ narzędzia" />
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Dolna część - Zakładki -->
            <div class="details-panel">
                <TabView v-model:activeIndex="activeTabIndex">
                    <TabPanel>
                        <template #header>
                            <span>Szczegóły</span>
                            <span v-if="selectedToolForDetails" class="tab-badge">&nbsp;&nbsp;{{ selectedToolForDetails.opis }}&nbsp;&nbsp;</span>
                        </template>
                        <div class="tab-content-wrapper">
                            <div v-if="isLoadingDetails" class="loading-spinner">
                                <ProgressSpinner />
                            </div>
                            <div v-else-if="!selectedToolForDetails" class="empty-state">
                                Kliknij na narzędzie w tabeli powyżej, aby zobaczyć jego egzemplarze.
                            </div>
                            <div v-else class="details-content">
                                <div class="instances-table">
                                    <DataTable :value="toolInstances" :scrollable="true" scrollHeight="flex" class="instances-datatable" :rowClass="instanceRowClass">
                                        <Column header="Lokalizacja">
                                            <template #body="{ data }">
                                                <span :title="data.faktura_zakupu ? `Faktura: ${data.faktura_zakupu.numer_faktury}` : ''">
                                                    {{ data.lokalizacja ? `${data.lokalizacja.szafa}/${data.lokalizacja.polka}/${data.lokalizacja.kolumna}` : 'Brak' }}
                                                </span>
                                            </template>
                                        </Column>
                                        <Column header="Data">
                                            <template #body="{ data }">
                                                <span v-html="formatCustomDate(data.data_modyfikacji)"></span>
                                            </template>
                                        </Column>
                                        <Column header="Oznaczenie">
                                            <template #body="{ data }">
                                                <div class="oznaczenie-cell">
                                                    <span>{{ data.oznaczenie || '' }}</span>
                                                    <Button
                                                        v-if="data.nowy_wpis && data.oznaczenie"
                                                        icon="pi pi-tag"
                                                        class="p-button-sm p-button-text etykieta-btn"
                                                        title="Pobierz etykietę PNG"
                                                        @click="downloadEtykieta(data)"
                                                    />
                                                </div>
                                            </template>
                                        </Column>
                                        <Column header="Opakowanie">
                                            <template #body="{ data }">
                                                <template v-if="data.jednostka === 'kompl'">Komplet ({{ data.ilosc_w_komplecie }} szt.)</template>
                                                <template v-else-if="data.narzedzie_typ && data.narzedzie_typ.opakowanie === 'kompl'">{{ data.ilosc_w_komplecie }} z kompletu</template>
                                                <template v-else>Sztuka</template>
                                            </template>
                                        </Column>
                                        <Column header="Stan">
                                            <template #body="{ data }">
                                                <Tag :severity="getInstanceStatusSeverity(data.stan)" :value="getInstanceStatusLabel(data.stan)" />
                                            </template>
                                        </Column>
                                        <Column header="Akcja" style="width: 80px; text-align: center;">
                                            <template #body="{ data }">
                                                <Button
                                                    v-if="data.stan === 'nowe' || data.stan === 'uzywane'"
                                                    icon="pi pi-download"
                                                    :class="inUseInstanceIds.has(data.id) ? 'p-button-secondary' : 'p-button-primary'"
                                                    class="p-button-sm"
                                                    :disabled="inUseInstanceIds.has(data.id)"
                                                    :title="inUseInstanceIds.has(data.id) ? 'Egzemplarz jest aktualnie w użyciu' : 'Pobierz ten egzemplarz'"
                                                    @click="showIssueModal(data)"
                                                />
                                            </template>
                                        </Column>
                                        <Column v-if="!trybProdukcja" style="width: 90px; text-align: center;">
                                            <template #header>
                                                <Button icon="pi pi-plus" class="p-button-success p-button-sm" @click="openInstanceModal('add')" title="Dodaj nowy egzemplarz" />
                                            </template>
                                            <template #body="{ data }">
                                                <div class="btn-group-inline">
                                                    <Button icon="pi pi-pencil" class="p-button-secondary p-button-sm" @click="openInstanceModal('edit', data)" title="Edytuj" />
                                                    <Button icon="pi pi-trash" class="p-button-danger p-button-sm" @click="openDeleteInstanceModal(data)" title="Usuń" />
                                                </div>
                                            </template>
                                        </Column>
                                        <template #empty>
                                            <div class="empty-state">Brak egzemplarzy dla tego typu narzędzia.</div>
                                        </template>
                                    </DataTable>
                                </div>
                                <div class="tool-image-panel">
                                    <img
                                        v-if="selectedToolForDetails.obraz"
                                        :src="selectedToolForDetails.obraz"
                                        class="tool-image"
                                        alt="Obrazek narzędzia"
                                    />
                                    <img
                                        v-else
                                        :src="defaultToolImage"
                                        class="tool-image"
                                        alt="Domyślny obrazek narzędzia"
                                    />
                                </div>
                            </div>
                        </div>
                    </TabPanel>

                    <TabPanel v-if="!trybProdukcja">
                        <template #header>
                            <span>Historia użycia</span>
                            <span v-if="selectedToolForDetails" class="tab-badge">&nbsp;&nbsp;{{ selectedToolForDetails.opis }}&nbsp;&nbsp;</span>
                        </template>
                        <div class="tab-content-wrapper">
                            <div v-if="isLoadingHistory" class="loading-spinner">
                                <ProgressSpinner />
                            </div>
                            <div v-else-if="!selectedToolForDetails" class="empty-state">
                                Kliknij na narzędzie w tabeli powyżej, aby zobaczyć jego historię.
                            </div>
                            <DataTable v-else :value="toolHistory" :scrollable="true" scrollHeight="flex">
                                <Column header="Pracownik">
                                    <template #body="{ data }">
                                        {{ data.pracownik ? `${data.pracownik.nazwisko} ${data.pracownik.imie}` : 'Brak' }}
                                    </template>
                                </Column>
                                <Column header="Maszyna">
                                    <template #body="{ data }">
                                        {{ data.maszyna?.nazwa || 'Brak' }}
                                    </template>
                                </Column>
                                <Column header="Data pobrania">
                                    <template #body="{ data }">
                                        <span v-html="formatCustomDate(data.data_wydania)"></span>
                                    </template>
                                </Column>
                                <Column header="Data zwrotu">
                                    <template #body="{ data }">
                                        <span v-if="data.data_zwrotu" v-html="formatCustomDate(data.data_zwrotu)"></span>
                                        <Tag v-else severity="danger" value="W użyciu" />
                                    </template>
                                </Column>
                                <Column header="Zwrócił">
                                    <template #body="{ data }">
                                        <span v-if="data.pracownik_zwracajacy">{{ data.pracownik_zwracajacy.nazwisko }} {{ data.pracownik_zwracajacy.imie }}</span>
                                        <span v-else-if="data.data_zwrotu">-</span>
                                    </template>
                                </Column>
                                <Column header="Stan">
                                    <template #body="{ data }">
                                        <Tag v-if="data.stan_po_zwrocie_display"
                                             :value="data.stan_po_zwrocie_display"
                                             :severity="getStanSeverity(data.stan_po_zwrocie)" />
                                        <span v-else-if="data.data_zwrotu">-</span>
                                    </template>
                                </Column>
                                <Column header="Opakowanie">
                                    <template #body="{ data }">
                                        <template v-if="data.egzemplarz?.jednostka === 'kompl'">Komplet ({{ data.egzemplarz.ilosc_w_komplecie }} szt.)</template>
                                        <template v-else-if="data.egzemplarz?.narzedzie_typ?.opakowanie === 'kompl'">{{ data.egzemplarz.ilosc_w_komplecie }} z kompletu</template>
                                        <template v-else>Sztuka</template>
                                    </template>
                                </Column>
                                <Column header="Oznaczenie">
                                    <template #body="{ data }">
                                        {{ data.egzemplarz?.oznaczenie }}
                                    </template>
                                </Column>
                                <Column field="nr_zlecenia" header="Nr zlecenia" />
                                <Column field="uwagi" header="Uwagi" />
                                <template #empty>
                                    <div class="empty-state">Brak historii użycia dla tego narzędzia.</div>
                                </template>
                            </DataTable>
                        </div>
                    </TabPanel>

                    <TabPanel>
                        <template #header>
                            <span>Narzędzia aktualnie w użyciu</span>
                            <Badge :value="usagesInUse.length" style="background-color: #8B4513;" class="ml-2" />
                        </template>
                        <div class="tab-content-wrapper">
                            <div class="in-use-header">
                                <input
                                    type="text"
                                    v-model="inUseSearchQuery"
                                    placeholder="Szukaj..."
                                    class="form-control search-input"
                                />
                                <div class="filter-row">
                                    <label>Filtruj po maszynie:</label>
                                    <select
                                        v-model="selectedMaszynaFilter"
                                        class="form-select filter-select"
                                    >
                                        <option :value="null">Wszystkie maszyny</option>
                                        <option v-for="m in machines" :key="m.id" :value="m.id">
                                            {{ m.nazwa }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <DataTable :value="filteredUsagesInUse" :scrollable="true" scrollHeight="flex">
                                <Column header="Narzędzie">
                                    <template #body="{ data }">
                                        <span v-if="data.egzemplarz.narzedzie_typ.podkategoria">
                                            <strong>{{ data.egzemplarz.narzedzie_typ.podkategoria.kategoria.nazwa }}</strong> /
                                            {{ data.egzemplarz.narzedzie_typ.podkategoria.nazwa }} -
                                        </span>
                                        {{ data.egzemplarz.narzedzie_typ.opis }}
                                    </template>
                                </Column>
                                <Column header="Maszyna">
                                    <template #body="{ data }">
                                        {{ data.maszyna?.nazwa || 'Brak' }}
                                    </template>
                                </Column>
                                <Column header="Pracownik">
                                    <template #body="{ data }">
                                        {{ data.pracownik ? `${data.pracownik.nazwisko} ${data.pracownik.imie}` : 'Brak' }}
                                    </template>
                                </Column>
                                <Column header="Data pobrania">
                                    <template #body="{ data }">
                                        <span v-html="formatCustomDate(data.data_wydania)"></span>
                                    </template>
                                </Column>
                                <Column header="Oznaczenie">
                                    <template #body="{ data }">
                                        {{ data.egzemplarz?.oznaczenie }}
                                    </template>
                                </Column>
                                <Column header="Opakowanie">
                                    <template #body="{ data }">
                                        <template v-if="data.egzemplarz?.jednostka === 'kompl'">Komplet ({{ data.egzemplarz.ilosc_w_komplecie }} szt.)</template>
                                        <template v-else-if="data.egzemplarz?.narzedzie_typ?.opakowanie === 'kompl'">{{ data.egzemplarz.ilosc_w_komplecie }} z kompletu</template>
                                        <template v-else>Sztuka</template>
                                    </template>
                                </Column>
                                <Column field="nr_zlecenia" header="Nr zlecenia" />
                                <Column v-if="!trybProdukcja" header="Akcje" style="width: 80px; text-align: center;">
                                    <template #body="{ data }">
                                        <Button icon="pi pi-undo" class="p-button-success p-button-sm" @click="showReturnModal(data.id)" title="Zwróć" />
                                    </template>
                                </Column>
                                <template #empty>
                                    <div class="empty-state">Brak narzędzi w użyciu.</div>
                                </template>
                            </DataTable>
                        </div>
                    </TabPanel>

                </TabView>
            </div>
        </main>

        <!-- Modal: Wydaj narzędzie -->
        <Dialog v-model:visible="issueModalVisible" header="Pobierz egzemplarz" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Narzędzie</label>
                    <InputText :value="issueData.instance ? issueData.instance.narzedzie_typ.opis : ''" disabled />
                </div>
                <!-- Info o egzemplarzu - czy komplet czy sztuki -->
                <div class="field" v-if="issueData.instance">
                    <small class="text-muted">
                        <template v-if="issueData.instance.narzedzie_typ && issueData.instance.narzedzie_typ.opakowanie === 'kompl'">
                            Komplet ({{ issueData.instance.ilosc_w_komplecie }} szt.)
                        </template>
                        <template v-else>
                            {{ issueData.instance.ilosc_w_komplecie }} szt.
                        </template>
                    </small>
                </div>
                <!-- Wybór typu wydania dla kompletów (tylko gdy narzędzie pozwala na wydawanie sztuk) -->
                <div class="field" v-if="issueData.instance && issueData.instance.narzedzie_typ && issueData.instance.narzedzie_typ.wydawanie_sztuk && issueData.instance.ilosc_w_komplecie > 1">
                    <label>Typ wydania</label>
                    <Dropdown
                        v-model="issueData.typWydania"
                        :options="typWydaniaOptions"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>
                <!-- Ilość sztuk do wydania -->
                <div class="field" v-if="issueData.instance && issueData.instance.narzedzie_typ && issueData.instance.narzedzie_typ.wydawanie_sztuk && issueData.instance.ilosc_w_komplecie > 1 && issueData.typWydania === 'sztuki'">
                    <label>Ilość sztuk do wydania</label>
                    <InputNumber
                        v-model="issueData.iloscSztuk"
                        :min="1"
                        :max="issueData.instance.ilosc_w_komplecie"
                    />
                    <small class="text-muted">
                        Pozostanie w magazynie: {{ issueData.instance.ilosc_w_komplecie - issueData.iloscSztuk }} szt.
                    </small>
                </div>
                <div class="field">
                    <label for="machine">Wybierz maszynę</label>
                    <Dropdown
                        id="machine"
                        v-model="issueData.machine_id"
                        :options="machines"
                        optionLabel="nazwa"
                        optionValue="id"
                        placeholder="Wybierz maszynę"
                    />
                </div>
                <div class="field">
                    <label for="employee">Wybierz pracownika <span class="required-mark">*</span></label>
                    <Dropdown
                        id="employee"
                        v-model="issueData.pracownik_id"
                        :options="pracownicy"
                        optionLabel="fullName"
                        optionValue="id"
                        placeholder="-- Wybierz --"
                        :filter="true"
                    />
                </div>
                <div class="field">
                    <label for="nr_zlecenia">Nr zlecenia</label>
                    <InputText id="nr_zlecenia" v-model="issueData.nr_zlecenia" placeholder="Nr zlecenia" />
                </div>
                <Message v-if="issueError" severity="error" :closable="false">{{ issueError }}</Message>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="issueModalVisible = false" />
                <Button label="Pobierz" icon="pi pi-check" @click="issueTool" />
            </template>
        </Dialog>

        <!-- Modal: Zwróć narzędzie -->
        <Dialog v-model:visible="returnModalVisible" header="Zwrot narzędzia" :modal="true" :style="{ width: '450px' }">
            <div class="p-fluid">
                <!-- Info o zwracanym egzemplarzu -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz">
                    <label>Narzędzie</label>
                    <InputText :value="returnData.usage.egzemplarz.narzedzie_typ?.opis || ''" disabled />
                    <small class="text-muted">
                        {{ returnData.usage.egzemplarz.ilosc_w_komplecie }} szt.
                        <template v-if="returnData.usage.egzemplarz.jednostka === 'kompl'"> (komplet)</template>
                    </small>
                </div>
                <div class="field">
                    <label>Pracownik zwracający <span class="required-mark">*</span></label>
                    <Dropdown
                        v-model="returnPracownikId"
                        :options="pracownicy"
                        optionLabel="fullName"
                        optionValue="id"
                        placeholder="Wybierz pracownika"
                        :filter="true"
                    />
                </div>
                <!-- Wybór typu zwrotu - tylko gdy egzemplarz ma więcej niż 1 szt -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz && returnData.usage.egzemplarz.ilosc_w_komplecie > 1">
                    <label>Ile zwracasz?</label>
                    <Dropdown
                        v-model="returnData.typZwrotu"
                        :options="typZwrotuOptions"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>
                <!-- Ilość sztuk do zwrotu -->
                <div class="field" v-if="returnData.usage && returnData.usage.egzemplarz && returnData.usage.egzemplarz.ilosc_w_komplecie > 1 && returnData.typZwrotu === 'czesc'">
                    <label>Ilość sztuk do zwrotu</label>
                    <InputNumber
                        v-model="returnData.iloscSztuk"
                        :min="1"
                        :max="returnData.usage.egzemplarz.ilosc_w_komplecie - 1"
                    />
                    <small class="text-muted">
                        Pozostanie w użyciu: {{ returnData.usage.egzemplarz.ilosc_w_komplecie - returnData.iloscSztuk }} szt.
                    </small>
                </div>
                <div class="field">
                    <label>W jakim stanie technicznym zwracasz narzędzie?</label>
                    <div class="return-status-options">
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanNowe" value="nowe" />
                            <label for="stanNowe">Nowym (nie używane)</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUzywane" value="uzywane" />
                            <label for="stanUzywane">Dobrym (jako używane)</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzone" value="uszkodzone" />
                            <label for="stanUszkodzone">Uszkodzonym</label>
                        </div>
                        <div class="field-radiobutton">
                            <RadioButton v-model="returnStatus" inputId="stanUszkodzoneRegen" value="uszkodzone_regeneracja" />
                            <label for="stanUszkodzoneRegen">Zużytym</label>
                        </div>
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="returnModalVisible = false" />
                <Button label="Potwierdź zwrot" icon="pi pi-check" class="p-button-success" @click="confirmReturnTool" />
            </template>
        </Dialog>

        <!-- Modal: Karta uszkodzenia -->
        <Dialog v-model:visible="kartaUszkodzeniaModalVisible" header="Karta uszkodzenia" :modal="true" :style="{ width: '1100px' }">
            <div class="p-fluid">
                <div class="karta-row">
                    <div class="field">
                        <label>Nr karty</label>
                        <InputText :value="kartaUszkodzenia.numer_karty" disabled class="karta-numer" />
                    </div>
                    <div class="field">
                        <label>Data wystawienia</label>
                        <InputText :value="kartaUszkodzenia.data_wystawienia" disabled />
                    </div>
                </div>
                <div class="karta-row">
                    <div class="field">
                        <label>Maszyna</label>
                        <InputText :value="kartaUszkodzenia.maszyna" disabled />
                    </div>
                    <div class="field">
                        <label>Uszkodzone narzędzie</label>
                        <InputText :value="kartaUszkodzenia.narzedzie" disabled />
                    </div>
                </div>
                <div class="karta-row">
                    <div class="field">
                        <label>Kto zgłasza uszkodzenie?</label>
                        <Dropdown
                            v-model="kartaUszkodzenia.typ_zglaszajacego"
                            :options="typZglaszajacegoOptions"
                            optionLabel="label"
                            optionValue="value"
                            @change="onTypZglaszajacegoChange"
                        />
                    </div>
                    <div class="field">
                        <label>Nazwisko zgłaszającego</label>
                        <InputText v-model="kartaUszkodzenia.nazwisko_zglaszajacego" disabled />
                    </div>
                </div>
                <div class="field">
                    <label>Przyczyna uszkodzenia</label>
                    <Textarea
                        v-model="kartaUszkodzenia.przyczyna_uszkodzenia"
                        rows="3"
                        :autoResize="false"
                        class="karta-textarea"
                    />
                </div>
                <div class="field">
                    <label>Uwagi</label>
                    <Textarea
                        v-model="kartaUszkodzenia.uwagi"
                        rows="3"
                        :autoResize="false"
                        class="karta-textarea"
                    />
                </div>
                <div class="field">
                    <label>Stracony czas na maszynach</label>
                    <InputText v-model="kartaUszkodzenia.stracony_czas" />
                </div>
                <Message v-if="kartaUszkodzeniaError" severity="error" :closable="false">{{ kartaUszkodzeniaError }}</Message>
            </div>
            <template #footer>
                <Button class="p-button-text" @click="anulujKarteUszkodzenia">
                    <i class="pi pi-arrow-left mr-2"></i> Wróć
                </Button>
                <Button class="p-button-danger" @click="zatwierdzKarteUszkodzenia">
                    <i class="pi pi-check mr-2"></i> Zatwierdź kartę
                </Button>
            </template>
        </Dialog>

        <!-- Modal: Edytuj/Dodaj typ narzędzia -->
        <Dialog v-model:visible="toolModalVisible" :header="isEditMode ? 'Edytuj typ narzędzia' : 'Dodaj nowy typ narzędzia'" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <div class="field">
                    <label>Kategoria / Podkategoria</label>
                    <Dropdown
                        v-model="currentTool.podkategoria_id"
                        :options="podkategorieGroupedOptions"
                        optionLabel="label"
                        optionValue="value"
                        optionGroupLabel="label"
                        optionGroupChildren="items"
                        placeholder="Brak (Główne)"
                    />
                </div>
                <div class="field">
                    <label>Opis / Specyfikacja <span class="required-mark">*</span></label>
                    <InputText v-model="currentTool.opis" />
                </div>
                <div class="field">
                    <label>Numer katalogowy</label>
                    <InputText v-model="currentTool.numer_katalogowy" />
                </div>
                <div class="field">
                    <label>Domyślna lokalizacja</label>
                    <Dropdown
                        v-model="currentTool.domyslna_lokalizacja_id"
                        :options="locationOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Brak --"
                        :filter="true"
                    />
                </div>

                <!-- Sekcja: ZAKUP -->
                <div class="modal-section">
                    <div class="modal-section-title">Zakup</div>
                    <div class="field">
                        <label>Jednostka zakupu</label>
                        <div class="radio-options-horizontal">
                            <div class="field-radiobutton">
                                <RadioButton v-model="currentTool.opakowanie" inputId="zakupSzt" value="szt" @change="onOpakowanieChange" />
                                <label for="zakupSzt">Sztuka</label>
                            </div>
                            <div class="field-radiobutton">
                                <RadioButton v-model="currentTool.opakowanie" inputId="zakupKompl" value="kompl" @change="onOpakowanieChange" />
                                <label for="zakupKompl">Komplet</label>
                            </div>
                        </div>
                    </div>
                    <div class="field" v-if="currentTool.opakowanie === 'kompl'">
                        <label>Ilość sztuk w komplecie</label>
                        <InputNumber v-model="currentTool.ilosc_w_opakowaniu" :min="2" suffix=" szt." />
                    </div>
                </div>

                <!-- Sekcja: WYDAWANIE (tylko dla kompletów) -->
                <div class="modal-section" v-if="currentTool.opakowanie === 'kompl'">
                    <div class="modal-section-title">Wydawanie</div>
                    <div class="field">
                        <label>Możliwość wydawania</label>
                        <div class="radio-options-vertical">
                            <div class="field-radiobutton">
                                <RadioButton v-model="currentTool.wydawanie_sztuk" inputId="wydawanieTylkoKompl" :value="false" />
                                <label for="wydawanieTylkoKompl">Tylko całe komplety</label>
                            </div>
                            <div class="field-radiobutton">
                                <RadioButton v-model="currentTool.wydawanie_sztuk" inputId="wydawanieKomplLubSzt" :value="true" />
                                <label for="wydawanieKomplLubSzt">Komplet lub pojedyncze sztuki</label>
                            </div>
                        </div>
                    </div>
                </div>

                <Message v-if="toolValidationError" severity="error" :closable="false">{{ toolValidationError }}</Message>
                <div class="field">
                    <label>Obraz narzędzia</label>
                    <input type="file" @change="handleToolImageUpload" accept="image/*" class="p-inputtext" />
                </div>
                <div v-if="toolImagePreview" class="field text-center">
                    <p>Podgląd:</p>
                    <img :src="toolImagePreview" class="tool-image-preview" alt="Podgląd obrazka" />
                </div>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="toolModalVisible = false" />
                <Button :label="isEditMode ? 'Zapisz' : 'Dodaj'" icon="pi pi-check" @click="saveTool" />
            </template>
        </Dialog>

        <!-- Modal: Edytuj/Dodaj egzemplarz -->
        <Dialog v-model:visible="instanceModalVisible" :header="instanceModal.title" :modal="true" :style="{ width: '500px' }">
            <div class="p-fluid">
                <Message v-if="instanceModal.errorMessage" severity="error" :closable="false">{{ instanceModal.errorMessage }}</Message>
                <div class="field">
                    <label>Typ Narzędzia</label>
                    <InputText :value="selectedToolForDetails ? selectedToolForDetails.opis : ''" disabled />
                </div>
                <div class="field">
                    <label>Stan Techniczny</label>
                    <Dropdown
                        v-model="instanceModal.currentInstance.stan"
                        :options="stanOptions"
                        optionLabel="label"
                        optionValue="value"
                    />
                </div>
                <div class="field">
                    <label>Lokalizacja</label>
                    <Dropdown
                        v-model="instanceModal.currentInstance.lokalizacja_id"
                        :options="locationOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="-- Wybierz lokalizację --"
                        :filter="true"
                        filterPlaceholder="Szukaj..."
                    />
                </div>
                <div class="field" v-if="!(instanceModal.mode === 'add' && selectedToolForDetails && selectedToolForDetails.opakowanie === 'szt')">
                    <label>Oznaczenie</label>
                    <InputText v-model="instanceModal.currentInstance.oznaczenie" placeholder="np. numer seryjny, partia" />
                </div>
                <template v-if="instanceModal.mode === 'add'">
                    <!-- Wybór typu dodawania dla narzędzi typu komplet (tylko gdy można wydawać sztuki) -->
                    <div class="field" v-if="selectedToolForDetails && selectedToolForDetails.opakowanie === 'kompl' && selectedToolForDetails.wydawanie_sztuk">
                        <label>Typ dodawania</label>
                        <Dropdown
                            v-model="instanceModal.currentInstance.typDodawania"
                            :options="typDodawaniaOptions"
                            optionLabel="label"
                            optionValue="value"
                        />
                        <small class="text-muted" v-if="instanceModal.currentInstance.typDodawania === 'komplet'">
                            Komplet zawiera {{ selectedToolForDetails.ilosc_w_opakowaniu }} szt.
                        </small>
                    </div>
                    <!-- Ilość luźnych sztuk -->
                    <div class="field" v-if="selectedToolForDetails && selectedToolForDetails.opakowanie === 'kompl' && selectedToolForDetails.wydawanie_sztuk && instanceModal.currentInstance.typDodawania === 'sztuki'">
                        <label>Ilość sztuk</label>
                        <InputNumber
                            v-model="instanceModal.currentInstance.iloscSztukLuznych"
                            :min="1"
                            :max="selectedToolForDetails.ilosc_w_opakowaniu - 1"
                        />
                        <small class="text-muted">
                            Wprowadź liczbę luźnych sztuk (maks. {{ selectedToolForDetails.ilosc_w_opakowaniu - 1 }})
                        </small>
                    </div>
                    <div class="field">
                        <label>Zamówienie</label>
                        <Dropdown
                            v-model="instanceModal.currentInstance.zamowienie_id"
                            :options="zamowieniaOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="-- Brak --"
                        />
                    </div>
                    <!-- Ilość kompletów/sztuk - ukryte dla luźnych sztuk, bo tam mamy osobne pole -->
                    <div class="field" v-if="!(selectedToolForDetails && selectedToolForDetails.opakowanie === 'kompl' && selectedToolForDetails.wydawanie_sztuk && instanceModal.currentInstance.typDodawania === 'sztuki')">
                        <label>Ilość {{ selectedToolForDetails && selectedToolForDetails.opakowanie === 'kompl' ? 'kompletów' : '' }}</label>
                        <InputNumber v-model="instanceModal.currentInstance.ilosc" :min="1" />
                        <small class="text-muted" v-if="selectedToolForDetails && selectedToolForDetails.opakowanie === 'kompl'">
                            Łącznie: {{ instanceModal.currentInstance.ilosc * selectedToolForDetails.ilosc_w_opakowaniu }} szt.
                        </small>
                    </div>
                </template>
            </div>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="instanceModalVisible = false" :disabled="isSavingInstance" />
                <Button v-if="!isSavingInstance" label="Zapisz" icon="pi pi-check" @click="saveInstance" />
                <Button v-else label="Zapisywanie..." icon="pi pi-spin pi-spinner" disabled />
            </template>
        </Dialog>

        <!-- Modal: Potwierdź usunięcie -->
        <Dialog v-model:visible="deleteInstanceModalVisible" header="Potwierdź usunięcie" :modal="true" :style="{ width: '450px' }">
            <div v-html="deleteModalMessage"></div>
            <p class="text-danger mt-3">Tej operacji nie można cofnąć.</p>
            <template #footer>
                <Button label="Anuluj" icon="pi pi-times" class="p-button-text" @click="deleteInstanceModalVisible = false" />
                <Button label="Tak, usuń" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteInstance" />
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
                    <small class="copyright">© {{ infoProgram.FIRMA }} 2025</small>
                    <Button label="Zamknij" class="btn-modal-secondary" @click="aboutModalVisible = false" />
                </div>
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';
import defaultToolImage from '@images/cnc.png';

// PrimeVue Components
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Dropdown from 'primevue/dropdown';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Dialog from 'primevue/dialog';
import Badge from 'primevue/badge';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Menu from 'primevue/menu';
import RadioButton from 'primevue/radiobutton';
import ProgressSpinner from 'primevue/progressspinner';
import Textarea from 'primevue/textarea';

const API_URL = '/api';

// Props from Inertia
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
            ustawienia: '/ustawienia/',
            zwroty: '/zwroty/',
            zamowienia: '/zamowienia/',
            zapotrzebowania: '/zapotrzebowania/',
            zakupy: '/zakupy/',
            logi: '/logi/',
            logout: '/logout/',
            produkcja: '/produkcja/'
        })
    },
    infoProgram: {
        type: Object,
        default: () => ({})
    },
    trybProdukcja: {
        type: Boolean,
        default: false
    },
    autoLogoutMinutes: {
        type: Number,
        default: 0
    }
});

// Data
const tools = ref([]);
const kategorie = ref([]);
const podkategorie = ref([]);
const machines = ref([]);
const pracownicy = ref([]);
const faktury = ref([]);
const zamowienia = ref([]);
const usagesInUse = ref([]);
const toolInstances = ref([]);
const toolHistory = ref([]);
const locations = ref([]);
const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedToolForDetails = ref(null);
const selectedMaszynaFilter = ref(null);
const inUseSearchQuery = ref('');
const searchInput = ref('');
const searchQuery = ref('');
let searchDebounceTimer = null;
watch(searchInput, (val) => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => { searchQuery.value = val; }, 250);
});

const activeTabIndex = ref(0);
const isLoadingTools = ref(true);
const isLoadingDetails = ref(false);
const isLoadingHistory = ref(false);
const isEditMode = ref(false);
const isSavingInstance = ref(false);

const issueError = ref('');
const toolValidationError = ref('');

// Modals visibility
const issueModalVisible = ref(false);
const returnModalVisible = ref(false);
const toolModalVisible = ref(false);
const instanceModalVisible = ref(false);
const deleteInstanceModalVisible = ref(false);
const aboutModalVisible = ref(false);
const kartaUszkodzeniaModalVisible = ref(false);

// Modal data
const issueData = ref({
    machine_id: null,
    instance: null,
    pracownik_id: null,
    typWydania: 'komplet',  // 'komplet' lub 'sztuki' - dla narzędzi typu komplet
    iloscSztuk: 1,          // ilość sztuk do wydania, gdy typWydania === 'sztuki'
    nr_zlecenia: ''
});

// Opcje dla typu wydania (komplet vs sztuki)
const typWydaniaOptions = [
    { label: 'Cały komplet', value: 'komplet' },
    { label: 'Wybrane sztuki', value: 'sztuki' }
];

const currentTool = ref({});
const returnStatus = ref('uzywane');
const returnPracownikId = ref(null);
const usageToReturnId = ref(null);
const returnData = ref({
    usage: null,           // Pełne dane o wydaniu
    typZwrotu: 'calosc',   // 'calosc' lub 'czesc'
    iloscSztuk: 1          // Ilość zwracanych sztuk przy częściowym zwrocie
});

// Opcje dla typu zwrotu
const typZwrotuOptions = [
    { label: 'Całość', value: 'calosc' },
    { label: 'Tylko część', value: 'czesc' }
];

// Karta uszkodzenia
const kartaUszkodzenia = ref({
    numer_karty: '',
    data_wystawienia: '',
    maszyna: '',
    narzedzie: '',
    typ_zglaszajacego: 'pobierajacy',
    nazwisko_zglaszajacego: '',
    przyczyna_uszkodzenia: '',
    uwagi: '',
    stracony_czas: ''
});
const kartaUszkodzeniaError = ref('');

// Opcje dla typu zgłaszającego
const typZglaszajacegoOptions = [
    { label: 'Osoba pobierająca', value: 'pobierajacy' },
    { label: 'Osoba zwracająca', value: 'zwracajacy' }
];

const instanceModal = ref({
    title: '',
    mode: 'add',
    currentInstance: {
        id: null,
        narzedzie_typ_id: null,
        stan: 'nowe',
        lokalizacja_id: null,
        faktura_zakupu_id: null,
        zamowienie_id: null,
        ilosc: 1,
        typDodawania: 'komplet',  // 'komplet' lub 'sztuki' - dla narzędzi typu komplet
        iloscSztukLuznych: 1      // ilość luźnych sztuk, gdy typDodawania === 'sztuki'
    },
    errorMessage: ''
});

// Opcje dla typu dodawania (komplet vs luźne sztuki)
const typDodawaniaOptions = [
    { label: 'Pełny komplet', value: 'komplet' },
    { label: 'Luźne sztuki', value: 'sztuki' }
];

const instanceToDelete = ref(null);
const deleteModalMessage = ref('');

const toolImagePreview = ref(null);
const toolImageFile = ref(null);

// User menu
const userMenu = ref(null);
const userMenuItems = ref([
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

// Menu Działania
const dzialaniaMenu = ref(null);
const dzialaniaMenuItems = ref([
    { label: 'Zapotrzebowania', icon: 'pi pi-inbox', command: () => { window.location.href = props.urls.zapotrzebowania; } },
    { label: 'Zamówienia', icon: 'pi pi-file', command: () => { window.location.href = props.urls.zamowienia; } },
    { label: 'Realizacje', icon: 'pi pi-box', command: () => { window.location.href = props.urls.realizacja; } }
]);
const toggleDzialaniaMenu = (event) => { dzialaniaMenu.value.toggle(event); };

// Menu Miejsca
const miejscaMenu = ref(null);
const miejscaMenuItems = ref([
    { label: 'Ustawienia', icon: 'pi pi-cog', command: () => { window.location.href = props.urls.ustawienia; } },
    { separator: true },
    { label: 'Zakupy', icon: 'pi pi-truck', command: () => { window.location.href = props.urls.zakupy; } },
    { label: 'Zwroty', icon: 'pi pi-undo', command: () => { window.location.href = props.urls.zwroty; } }
]);
const toggleMiejscaMenu = (event) => { miejscaMenu.value.toggle(event); };

// Logout (tryb produkcja)
const logout = () => {
    window.location.href = props.urls.logout;
};

// Auto-wylogowanie po bezczynności
let idleTimer = null;
const idleEvents = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'];

const resetIdleTimer = () => {
    if (!props.autoLogoutMinutes) return;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        logout();
    }, props.autoLogoutMinutes * 60 * 1000);
};

const startIdleWatch = () => {
    if (!props.autoLogoutMinutes) return;
    idleEvents.forEach(ev => window.addEventListener(ev, resetIdleTimer));
    resetIdleTimer();
};

const stopIdleWatch = () => {
    clearTimeout(idleTimer);
    idleEvents.forEach(ev => window.removeEventListener(ev, resetIdleTimer));
};

// Computed
const filteredTools = computed(() => {
    let filtered = tools.value;

    if (selectedPodkategoriaId.value) {
        filtered = filtered.filter(tool => tool.podkategoria && tool.podkategoria.id === selectedPodkategoriaId.value);
    } else if (selectedKategoriaId.value) {
        const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
        if (kategoria) {
            filtered = filtered.filter(tool => {
                if (!tool.podkategoria) return false;
                return kategoria.podkategorie.some(p => p.id === tool.podkategoria.id);
            });
        }
    }

    if (searchQuery.value.trim() !== '') {
        const query = searchQuery.value.trim().toLowerCase();
        filtered = filtered.filter(tool => {
            const catalogNumber = (tool.numer_katalogowy || '').toLowerCase();
            const kategoriaNazwa = tool.podkategoria?.kategoria_nazwa?.toLowerCase() || '';
            const podkategoriaNazwa = tool.podkategoria?.nazwa?.toLowerCase() || '';
            const opisNazwa = tool.opis.toLowerCase();

            return kategoriaNazwa.includes(query) ||
                   podkategoriaNazwa.includes(query) ||
                   opisNazwa.includes(query) ||
                   catalogNumber.includes(query);
        });
    }

    return filtered;
});

const inUseInstanceIds = computed(() => {
    return new Set(usagesInUse.value.map(usage => usage.egzemplarz.id));
});

const filteredPodkategorieOptions = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return [
        { label: 'Wszystkie podkategorie', value: null },
        ...kategoria.podkategorie.map(p => ({ label: p.nazwa, value: p.id }))
    ];
});

// Filtrowane podkategorie dla native select (używane w panel-header)
const filteredPodkategorie = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return kategoria.podkategorie || [];
});

const kategorieOptions = computed(() => {
    return [
        { label: 'Wszystkie kategorie', value: null },
        ...kategorie.value.map(k => ({ label: k.nazwa, value: k.id }))
    ];
});

const sortedLocations = computed(() => {
    return [...locations.value].sort((a, b) => {
        if (a.szafa < b.szafa) return -1;
        if (a.szafa > b.szafa) return 1;
        const kolumnaA = parseInt(a.kolumna) || 0;
        const kolumnaB = parseInt(b.kolumna) || 0;
        if (kolumnaA < kolumnaB) return -1;
        if (kolumnaA > kolumnaB) return 1;
        const polkaA = parseInt(a.polka) || 0;
        const polkaB = parseInt(b.polka) || 0;
        return polkaA - polkaB;
    });
});

const locationOptions = computed(() => {
    return [
        { label: '-- Brak --', value: null },
        ...sortedLocations.value.map(loc => ({
            label: `${loc.szafa} / ${loc.polka} / ${loc.kolumna}`,
            value: loc.id
        }))
    ];
});

const machineOptions = computed(() => {
    return [
        { label: 'Wszystkie maszyny', value: null },
        ...machines.value.map(m => ({ label: m.nazwa, value: m.id }))
    ];
});

const zamowieniaOptions = computed(() => {
    return [
        { label: '-- Brak --', value: null },
        ...zamowienia.value.map(z => ({
            label: `${z.numer} - ${z.dostawca?.nazwa_firmy || 'Brak dostawcy'}`,
            value: z.id
        }))
    ];
});

const podkategorieGroupedOptions = computed(() => {
    return kategorie.value.map(kategoria => ({
        label: kategoria.nazwa,
        items: kategoria.podkategorie.map(p => ({
            label: `${kategoria.nazwa} / ${p.nazwa}`,
            value: p.id
        }))
    }));
});

const filteredUsagesInUse = computed(() => {
    let filtered = usagesInUse.value;

    if (selectedMaszynaFilter.value) {
        filtered = filtered.filter(usage => usage.maszyna && usage.maszyna.id === selectedMaszynaFilter.value);
    }

    if (inUseSearchQuery.value.trim() !== '') {
        const query = inUseSearchQuery.value.toLowerCase().trim();
        filtered = filtered.filter(usage => {
            const narzedzie = usage.egzemplarz?.narzedzie_typ;
            let narzedzieTekst = '';
            if (narzedzie) {
                if (narzedzie.podkategoria) {
                    narzedzieTekst = `${narzedzie.podkategoria.kategoria?.nazwa || ''} ${narzedzie.podkategoria.nazwa || ''} ${narzedzie.opis || ''}`.toLowerCase();
                } else {
                    narzedzieTekst = (narzedzie.opis || '').toLowerCase();
                }
            }

            const pracownik = usage.pracownik;
            let pracownikTekst = '';
            if (pracownik) {
                pracownikTekst = `${pracownik.nazwisko || ''} ${pracownik.imie || ''}`.toLowerCase();
            }

            const zlecenieTekst = (usage.nr_zlecenia || '').toLowerCase();
            const oznaczenieTekst = (usage.egzemplarz?.oznaczenie || '').toLowerCase();

            return narzedzieTekst.includes(query) || pracownikTekst.includes(query) || zlecenieTekst.includes(query) || oznaczenieTekst.includes(query);
        });
    }

    return filtered;
});

// Static options
const opakowanieOptions = [
    { label: 'Sztuka', value: 'szt' },
    { label: 'Komplet', value: 'kompl' }
];

const stanOptions = [
    { label: 'Nowe', value: 'nowe' },
    { label: 'Używane', value: 'uzywane' },
    { label: 'Uszkodzone', value: 'uszkodzone' }
];

// Methods
const toggleUserMenu = (event) => {
    userMenu.value.toggle(event);
};

const rowClass = (data) => {
    return selectedToolForDetails.value && selectedToolForDetails.value.id === data.id ? 'selected-row' : '';
};

const instanceRowClass = (data) => {
    return data.nowy_wpis ? 'nowy-wpis-row' : '';
};

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

const getInstanceStatusSeverity = (stan) => {
    const map = {
        'nowe': 'success',
        'uzywane': 'info',
        'uszkodzone': 'danger',
        'uszkodzone_regeneracja': 'warning'
    };
    return map[stan] || 'secondary';
};

const getInstanceStatusLabel = (stan) => {
    const map = {
        'nowe': 'Nowe',
        'uzywane': 'Używane',
        'uszkodzone': 'Uszkodzone',
        'uszkodzone_regeneracja': 'Uszkodzone do regeneracji'
    };
    return map[stan] || stan;
};

const getStanSeverity = (stan) => {
    const map = {
        'nowe': 'success',
        'uzywane': 'info',
        'uszkodzone': 'danger',
        'uszkodzone_regeneracja': 'warning'
    };
    return map[stan] || 'secondary';
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const onToolSelect = async (event) => {
    const tool = event.data;
    activeTabIndex.value = 0;
    await getToolInstances(tool);
    await getToolHistory(tool);
};

const onToolUnselect = () => {
    toolInstances.value = [];
    toolHistory.value = [];
};

const getToolInstances = async (tool) => {
    isLoadingDetails.value = true;
    try {
        const response = await axios.get(`${API_URL}/egzemplarze/?narzedzie_typ_id=${tool.id}`);
        const instances = response.data.results || response.data;
        toolInstances.value = instances.sort((a, b) => b.id - a.id);
    } catch (error) {
        console.error("Błąd ładowania egzemplarzy:", error.response?.data || error.message);
        toolInstances.value = [];
    } finally {
        isLoadingDetails.value = false;
    }
};

const getToolHistory = async (tool) => {
    isLoadingHistory.value = true;
    try {
        const response = await axios.get(`${API_URL}/historia/?narzedzie_id=${tool.id}`);
        const history = response.data.results || response.data;
        toolHistory.value = history.sort((a, b) => new Date(b.data_wydania) - new Date(a.data_wydania));
    } catch (error) {
        console.error("Błąd ładowania historii narzędzia:", error.response?.data || error.message);
        toolHistory.value = [];
    } finally {
        isLoadingHistory.value = false;
    }
};

const showIssueModal = (instance) => {
    issueData.value.instance = instance;
    issueData.value.machine_id = machines.value.length > 0 ? machines.value[0].id : null;
    issueData.value.pracownik_id = null;
    issueData.value.typWydania = 'komplet';
    issueData.value.iloscSztuk = 1;
    issueError.value = '';
    issueModalVisible.value = true;
};

const issueTool = async () => {
    if (!issueData.value.pracownik_id) {
        issueError.value = "Wybierz pracownika.";
        return;
    }

    const instance = issueData.value.instance;
    const isPartialIssue = instance && instance.narzedzie_typ && instance.narzedzie_typ.wydawanie_sztuk && instance.ilosc_w_komplecie > 1 && issueData.value.typWydania === 'sztuki';

    // Walidacja ilości przy częściowym wydaniu
    if (isPartialIssue) {
        const iloscSztuk = issueData.value.iloscSztuk;
        const maxSztuk = instance.ilosc_w_komplecie;
        if (!Number.isInteger(iloscSztuk) || iloscSztuk < 1 || iloscSztuk > maxSztuk) {
            issueError.value = `Ilość sztuk musi być liczbą od 1 do ${maxSztuk}.`;
            return;
        }
    }

    issueError.value = '';

    try {
        const payload = {
            egzemplarz_id: instance.id,
            maszyna_id: issueData.value.machine_id,
            pracownik_id: issueData.value.pracownik_id,
            nr_zlecenia: issueData.value.nr_zlecenia || null
        };

        // Dodaj info o częściowym wydaniu
        if (isPartialIssue) {
            payload.czesciowe_wydanie = true;
            payload.ilosc_sztuk = issueData.value.iloscSztuk;
        }

        await axios.post(`${API_URL}/historia/wydanie/`, payload);

        issueModalVisible.value = false;
        await fetchInitialData();

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
            await getToolHistory(selectedToolForDetails.value);
        }
    } catch (error) {
        console.error("Błąd wydawania narzędzia:", error.response?.data || error.message);
        issueError.value = error.response?.data?.error || "Wystąpił nieznany błąd podczas wydawania.";
    }
};

const showReturnModal = (usageId) => {
    usageToReturnId.value = usageId;
    returnStatus.value = 'uzywane';

    const usage = usagesInUse.value.find(u => u.id === usageId);

    // Zapisz pełne dane o wydaniu do returnData
    returnData.value.usage = usage;
    returnData.value.typZwrotu = 'calosc';
    returnData.value.iloscSztuk = 1;

    if (usage && usage.pracownik) {
        returnPracownikId.value = usage.pracownik.id;
    } else {
        returnPracownikId.value = null;
    }

    returnModalVisible.value = true;
};

const confirmReturnTool = async () => {
    const usage = returnData.value.usage;
    const isPartialReturn = usage && usage.egzemplarz &&
        usage.egzemplarz.ilosc_w_komplecie > 1 &&
        returnData.value.typZwrotu === 'czesc';

    // Walidacja częściowego zwrotu
    if (isPartialReturn) {
        const iloscSztuk = returnData.value.iloscSztuk;
        const maxSztuk = usage.egzemplarz.ilosc_w_komplecie - 1;
        if (!Number.isInteger(iloscSztuk) || iloscSztuk < 1 || iloscSztuk > maxSztuk) {
            alert(`Ilość sztuk musi być liczbą od 1 do ${maxSztuk}.`);
            return;
        }
    }

    // Jeśli stan to 'uszkodzone', otwórz modal karty uszkodzenia
    if (returnStatus.value === 'uszkodzone') {
        otworzKarteUszkodzenia();
        return;
    }

    // Dla innych stanów (w tym uszkodzone_regeneracja) - bezpośredni zwrot
    await wykonajZwrot();
};

// Otwiera modal karty uszkodzenia z wypełnionymi danymi
const otworzKarteUszkodzenia = async () => {
    const usage = returnData.value.usage;
    const today = new Date();
    const formattedDate = `${String(today.getDate()).padStart(2, '0')}.${String(today.getMonth() + 1).padStart(2, '0')}.${today.getFullYear()}`;

    // Pobierz nazwisko pracownika pobierającego
    const pracownikPobierajacy = usage?.pracownik;
    const nazwiskoPobierajacy = pracownikPobierajacy
        ? `${pracownikPobierajacy.nazwisko} ${pracownikPobierajacy.imie}`
        : '';

    // Pobierz nazwisko pracownika zwracającego
    const pracownikZwracajacyObj = pracownicy.value.find(p => p.id === returnPracownikId.value);
    const nazwiskoZwracajacy = pracownikZwracajacyObj
        ? `${pracownikZwracajacyObj.nazwisko} ${pracownikZwracajacyObj.imie}`
        : '';

    // Pobierz następny numer karty z backendu
    let numerKarty = `${today.getFullYear()}/1`;
    try {
        const response = await axios.get(`${API_URL}/uszkodzenia/nastepny_numer_karty/`);
        numerKarty = response.data.numer_karty;
    } catch (error) {
        console.warn('Nie udało się pobrać numeru karty z backendu:', error);
    }

    kartaUszkodzenia.value = {
        numer_karty: numerKarty,
        data_wystawienia: formattedDate,
        maszyna: usage?.maszyna?.nazwa || 'Brak',
        narzedzie: usage?.egzemplarz?.narzedzie_typ?.opis || '',
        typ_zglaszajacego: 'pobierajacy',
        nazwisko_zglaszajacego: nazwiskoPobierajacy,
        przyczyna_uszkodzenia: '',
        uwagi: '',
        stracony_czas: '',
        // Dodatkowe dane do późniejszego użycia
        _nazwisko_pobierajacy: nazwiskoPobierajacy,
        _nazwisko_zwracajacy: nazwiskoZwracajacy
    };
    kartaUszkodzeniaError.value = '';

    returnModalVisible.value = false;
    kartaUszkodzeniaModalVisible.value = true;
};

// Zmiana typu zgłaszającego - aktualizuje nazwisko
const onTypZglaszajacegoChange = () => {
    if (kartaUszkodzenia.value.typ_zglaszajacego === 'pobierajacy') {
        kartaUszkodzenia.value.nazwisko_zglaszajacego = kartaUszkodzenia.value._nazwisko_pobierajacy;
    } else {
        kartaUszkodzenia.value.nazwisko_zglaszajacego = kartaUszkodzenia.value._nazwisko_zwracajacy;
    }
};

// Anuluj kartę i wróć do modalu zwrotu
const anulujKarteUszkodzenia = () => {
    kartaUszkodzeniaModalVisible.value = false;
    returnModalVisible.value = true;
};

// Zatwierdź kartę uszkodzenia i wykonaj zwrot
const zatwierdzKarteUszkodzenia = async () => {
    kartaUszkodzeniaError.value = '';

    // Wykonaj zwrot z danymi karty uszkodzenia
    await wykonajZwrot({
        przyczyna_uszkodzenia: kartaUszkodzenia.value.przyczyna_uszkodzenia,
        uwagi: kartaUszkodzenia.value.uwagi,
        stracony_czas: kartaUszkodzenia.value.stracony_czas,
        typ_zglaszajacego: kartaUszkodzenia.value.typ_zglaszajacego,
        nazwisko_zglaszajacego: kartaUszkodzenia.value.nazwisko_zglaszajacego
    });

    kartaUszkodzeniaModalVisible.value = false;
};

// Wykonuje faktyczny zwrot narzędzia
const wykonajZwrot = async (kartaData = null) => {
    const usage = returnData.value.usage;
    const isPartialReturn = usage && usage.egzemplarz &&
        usage.egzemplarz.ilosc_w_komplecie > 1 &&
        returnData.value.typZwrotu === 'czesc';

    try {
        const payload = {
            stan_po_zwrocie: returnStatus.value,
            pracownik_zwracajacy_id: returnPracownikId.value
        };

        // Dodaj info o częściowym zwrocie
        if (isPartialReturn) {
            payload.czesciowy_zwrot = true;
            payload.ilosc_sztuk = returnData.value.iloscSztuk;
        }

        // Dodaj dane karty uszkodzenia jeśli są
        if (kartaData) {
            payload.karta_uszkodzenia = kartaData;
        }

        await axios.post(`${API_URL}/historia/${usageToReturnId.value}/zwrot/`, payload);

        returnModalVisible.value = false;
        await fetchInitialData();

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
            await getToolHistory(selectedToolForDetails.value);
        }
    } catch (error) {
        console.error("Błąd zwracania narzędzia:", error.response?.data || error.message);
        alert(error.response?.data?.error || "Wystąpił błąd podczas zwracania narzędzia.");
    }
};

const openToolModal = (tool = null) => {
    isEditMode.value = !!tool;
    toolImagePreview.value = null;
    toolImageFile.value = null;
    toolValidationError.value = '';

    if (isEditMode.value) {
        currentTool.value = {
            ...tool,
            podkategoria_id: tool.podkategoria ? tool.podkategoria.id : null,
            domyslna_lokalizacja_id: tool.domyslna_lokalizacja ? tool.domyslna_lokalizacja.id : null,
            opakowanie: tool.opakowanie || 'szt',
            ilosc_w_opakowaniu: tool.ilosc_w_opakowaniu || 1,
            wydawanie_sztuk: tool.wydawanie_sztuk !== undefined ? tool.wydawanie_sztuk : false
        };
        if (tool.obraz) {
            toolImagePreview.value = tool.obraz;
        }
    } else {
        currentTool.value = {
            podkategoria_id: null,
            opis: '',
            numer_katalogowy: '',
            domyslna_lokalizacja_id: null,
            obraz: null,
            opakowanie: 'szt',
            ilosc_w_opakowaniu: 1,
            wydawanie_sztuk: false
        };
    }

    toolModalVisible.value = true;
};

const onOpakowanieChange = () => {
    if (currentTool.value.opakowanie === 'kompl' && currentTool.value.ilosc_w_opakowaniu <= 1) {
        currentTool.value.ilosc_w_opakowaniu = 2;
    } else if (currentTool.value.opakowanie === 'szt') {
        currentTool.value.ilosc_w_opakowaniu = 1;
    }
};

const handleToolImageUpload = (event) => {
    const file = event.target.files[0];

    if (!file) {
        toolImageFile.value = null;
        toolImagePreview.value = (isEditMode.value && currentTool.value.obraz) ? currentTool.value.obraz : null;
        return;
    }

    toolImageFile.value = file;
    toolImagePreview.value = URL.createObjectURL(file);
};

const saveTool = async () => {
    toolValidationError.value = '';

    if (currentTool.value.opakowanie === 'kompl' && currentTool.value.ilosc_w_opakowaniu <= 1) {
        toolValidationError.value = 'Dla opakowania "Komplet" ilość w opakowaniu musi być większa niż 1.';
        return;
    }

    const formData = new FormData();
    formData.append('opis', currentTool.value.opis);
    formData.append('opakowanie', currentTool.value.opakowanie || 'szt');
    formData.append('ilosc_w_opakowaniu', currentTool.value.ilosc_w_opakowaniu || 1);
    // Dla kompletów według wyboru użytkownika, dla sztuk pole nie ma znaczenia (domyślnie false)
    formData.append('wydawanie_sztuk', currentTool.value.wydawanie_sztuk || false);

    if (currentTool.value.podkategoria_id) {
        formData.append('podkategoria_id', currentTool.value.podkategoria_id);
    }

    if (currentTool.value.numer_katalogowy) {
        formData.append('numer_katalogowy', currentTool.value.numer_katalogowy);
    }

    if (currentTool.value.domyslna_lokalizacja_id) {
        formData.append('domyslna_lokalizacja_id', currentTool.value.domyslna_lokalizacja_id);
    }

    if (toolImageFile.value) {
        formData.append('obraz', toolImageFile.value);
    }

    const method = isEditMode.value ? 'patch' : 'post';
    const url = isEditMode.value ? `${API_URL}/narzedzia/${currentTool.value.id}/` : `${API_URL}/narzedzia/`;

    try {
        const response = await axios({
            method: method,
            url: url,
            data: formData,
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        toolModalVisible.value = false;
        const savedToolId = response.data?.id || selectedToolForDetails.value?.id;
        await fetchInitialData();

        // Odśwież selectedToolForDetails świeżymi danymi (w tym domyslna_lokalizacja)
        if (savedToolId) {
            const freshTool = tools.value.find(t => t.id === savedToolId);
            if (freshTool) {
                selectedToolForDetails.value = freshTool;
                await getToolInstances(freshTool);
            }
        }
    } catch (error) {
        console.error("Błąd zapisu typu narzędzia:", error.response?.data || error.message);
        toolValidationError.value = 'Wystąpił błąd zapisu narzędzia: ' + JSON.stringify(error.response?.data || error.message);
    }
};

const openInstanceModal = (mode, instance = null) => {
    instanceModal.value.mode = mode;
    instanceModal.value.errorMessage = '';

    if (mode === 'add') {
        instanceModal.value.title = 'Dodaj nowy egzemplarz';
        instanceModal.value.currentInstance = {
            id: null,
            narzedzie_typ_id: selectedToolForDetails.value.id,
            stan: 'nowe',
            lokalizacja_id: null,
            faktura_zakupu_id: null,
            zamowienie_id: null,
            oznaczenie: '',
            ilosc: 1,
            typDodawania: 'komplet',
            iloscSztukLuznych: 1
        };

        if (selectedToolForDetails.value.domyslna_lokalizacja) {
            instanceModal.value.currentInstance.lokalizacja_id = selectedToolForDetails.value.domyslna_lokalizacja.id;
        } else if (Array.isArray(toolInstances.value) && toolInstances.value.length > 0) {
            const lastInstance = toolInstances.value[0];
            if (lastInstance && lastInstance.lokalizacja) {
                instanceModal.value.currentInstance.lokalizacja_id = lastInstance.lokalizacja.id;
            }
        }
    } else {
        instanceModal.value.title = `Edytuj egzemplarz: ${instance.narzedzie_typ.opis}`;
        instanceModal.value.currentInstance = {
            ...instance,
            lokalizacja_id: instance.lokalizacja ? instance.lokalizacja.id : null,
            faktura_zakupu_id: instance.faktura_zakupu ? instance.faktura_zakupu.id : null,
            zamowienie_id: instance.zamowienie ? instance.zamowienie.id : null,
            ilosc: 1,
            typDodawania: 'komplet',
            iloscSztukLuznych: 1
        };
    }

    instanceModalVisible.value = true;
};

const saveInstance = async () => {
    isSavingInstance.value = true;
    instanceModal.value.errorMessage = '';

    const method = instanceModal.value.mode === 'add' ? 'post' : 'patch';
    const url = instanceModal.value.mode === 'add'
        ? `${API_URL}/egzemplarze/`
        : `${API_URL}/egzemplarze/${instanceModal.value.currentInstance.id}/`;

    const payload = {
        stan: instanceModal.value.currentInstance.stan,
        lokalizacja_id: instanceModal.value.currentInstance.lokalizacja_id,
        narzedzie_typ_id: instanceModal.value.currentInstance.narzedzie_typ_id,
        faktura_zakupu_id: instanceModal.value.currentInstance.faktura_zakupu_id,
        zamowienie_id: instanceModal.value.currentInstance.zamowienie_id,
        oznaczenie: instanceModal.value.currentInstance.oznaczenie || null
    };

    // Obsługa luźnych sztuk dla narzędzi typu komplet
    const isKompletTool = selectedToolForDetails.value && selectedToolForDetails.value.opakowanie === 'kompl';
    const isLuzneStuki = instanceModal.value.currentInstance.typDodawania === 'sztuki';

    if (instanceModal.value.mode === 'add' && isKompletTool && isLuzneStuki) {
        // Luźne sztuki - nadpisz jednostkę i ilość w komplecie
        payload.jednostka = 'szt';
        payload.ilosc_w_komplecie = instanceModal.value.currentInstance.iloscSztukLuznych;
    }

    const ilosc = instanceModal.value.currentInstance.ilosc;

    if (instanceModal.value.mode === 'add' && (!Number.isInteger(ilosc) || ilosc < 1)) {
        instanceModal.value.errorMessage = 'Ilość musi być liczbą całkowitą większą od 0.';
        isSavingInstance.value = false;
        return;
    }

    // Walidacja ilości luźnych sztuk
    if (instanceModal.value.mode === 'add' && isKompletTool && isLuzneStuki) {
        const iloscSztuk = instanceModal.value.currentInstance.iloscSztukLuznych;
        const maxSztuk = selectedToolForDetails.value.ilosc_w_opakowaniu - 1;
        if (!Number.isInteger(iloscSztuk) || iloscSztuk < 1 || iloscSztuk > maxSztuk) {
            instanceModal.value.errorMessage = `Ilość sztuk musi być liczbą od 1 do ${maxSztuk}.`;
            isSavingInstance.value = false;
            return;
        }
    }

    try {
        if (instanceModal.value.mode === 'add' && ilosc > 1) {
            for (let i = 0; i < ilosc; i++) {
                await axios.post(url, payload);
            }
        } else {
            await axios({ method, url, data: payload });
        }

        instanceModalVisible.value = false;

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
        }

        await fetchInitialData();
    } catch (error) {
        console.error("Błąd zapisu egzemplarza:", error.response?.data || error.message);

        let errorMsg = 'Wystąpił nieznany błąd podczas zapisu.';

        if (error.response?.data) {
            if (typeof error.response.data === 'object') {
                errorMsg = Object.entries(error.response.data)
                    .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(' ') : errors}`)
                    .join('; ');
            } else {
                errorMsg = `Błąd: ${error.response.data}`;
            }
        } else if (error.message) {
            errorMsg = `Wystąpił błąd sieci lub serwera: ${error.message}.`;
        }

        instanceModal.value.errorMessage = errorMsg;
    } finally {
        isSavingInstance.value = false;
    }
};

// Referencja do katalogu wybranego przez użytkownika (File System Access API)
let savedDirHandle = null;

const downloadEtykieta = async (instance) => {
    try {
        const response = await axios.get(`${API_URL}/egzemplarze/${instance.id}/etykieta/`, {
            responseType: 'blob'
        });

        const blob = new Blob([response.data], { type: 'application/dxf' });
        const fileName = `${instance.oznaczenie}.dxf`;
        let saved = false;

        // File System Access API — pozwala wybrać katalog i zapamiętuje go
        if (window.showSaveFilePicker) {
            try {
                const opts = {
                    suggestedName: fileName,
                    types: [{
                        description: 'Plik DXF',
                        accept: { 'application/dxf': ['.dxf'] }
                    }]
                };

                // Jeśli mamy zapamiętany katalog, użyj go jako startowego
                if (savedDirHandle) {
                    opts.startIn = savedDirHandle;
                }

                const fileHandle = await window.showSaveFilePicker(opts);

                // Zapamiętaj katalog nadrzędny (nie da się go pobrać bezpośrednio,
                // ale przeglądarka zapamiętuje ostatni wybór w showSaveFilePicker)
                savedDirHandle = fileHandle;

                const writable = await fileHandle.createWritable();
                await writable.write(blob);
                await writable.close();
                saved = true;
            } catch (err) {
                // Użytkownik anulował dialog — nie robimy nic
                if (err.name === 'AbortError') return;
                console.warn('File System Access API fallback:', err);
            }
        }

        // Fallback dla przeglądarek bez File System Access API
        if (!saved) {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        }

        // Po pobraniu — oznacz jako nie-nowy
        await axios.patch(`${API_URL}/egzemplarze/${instance.id}/`, { nowy_wpis: false });

        // Odśwież listę egzemplarzy
        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
        }
    } catch (error) {
        console.error('Błąd pobierania etykiety:', error);
    }
};

const openDeleteInstanceModal = (instance) => {
    instanceToDelete.value = instance;

    const toolName = instance.narzedzie_typ.podkategoria
        ? `${instance.narzedzie_typ.podkategoria.kategoria.nazwa} / ${instance.narzedzie_typ.podkategoria.nazwa} - ${instance.narzedzie_typ.opis}`
        : instance.narzedzie_typ.opis;

    deleteModalMessage.value = `Czy na pewno chcesz usunąć egzemplarz: <strong>${toolName}</strong>?`;

    deleteInstanceModalVisible.value = true;
};

const confirmDeleteInstance = async () => {
    if (!instanceToDelete.value) return;

    try {
        await axios.delete(`${API_URL}/egzemplarze/${instanceToDelete.value.id}/`);

        deleteInstanceModalVisible.value = false;

        if (selectedToolForDetails.value) {
            await getToolInstances(selectedToolForDetails.value);
        }

        await fetchInitialData();
        instanceToDelete.value = null;
    } catch (error) {
        console.error("Błąd usuwania egzemplarza:", error.response?.data || error.message);
        deleteInstanceModalVisible.value = false;
        alert('Nie można usunąć egzemplarza. Sprawdź, czy nie jest aktualnie w użyciu lub nie ma powiązanej historii.');
    }
};

const fetchInitialData = async () => {
    // Faza 1: dane krytyczne dla głównej tabeli narzędzi (wyświetl jak najszybciej)
    try {
        const [toolsRes, categoriesRes, podkategorieRes] = await Promise.all([
            axios.get(`${API_URL}/narzedzia/`),
            axios.get(`${API_URL}/kategorie/`),
            axios.get(`${API_URL}/podkategorie/`)
        ]);

        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;
        podkategorie.value = podkategorieRes.data;
        isLoadingTools.value = false;
    } catch (error) {
        console.error("Błąd ładowania danych głównych:", error.response?.data || error.message);
        isLoadingTools.value = false;
        alert("Wystąpił krytyczny błąd podczas ładowania danych aplikacji. Sprawdź konsolę przeglądarki.");
        return;
    }

    // Faza 2: dane pomocnicze (modale, zakładki, formularze) — w tle
    try {
        const [machinesRes, usagesRes, locationsRes, pracownicyRes, fakturyRes, zamowieniaRes] = await Promise.all([
            axios.get(`${API_URL}/maszyny/`),
            axios.get(`${API_URL}/historia/?w_uzyciu=true`),
            axios.get(`${API_URL}/lokalizacje/`),
            axios.get(`${API_URL}/pracownicy/`),
            axios.get(`${API_URL}/faktury/`),
            axios.get(`${API_URL}/zamowienia/`)
        ]);

        machines.value = machinesRes.data;
        usagesInUse.value = usagesRes.data.results || usagesRes.data;
        locations.value = locationsRes.data;

        // Dodaj fullName do pracowników dla dropdown
        // (...) = tylko karta (stara tabela, brak konta użytkownika)
        const pracownicyData = pracownicyRes.data.results || pracownicyRes.data;
        pracownicy.value = pracownicyData.map(p => ({
            ...p,
            fullName: p.user
                ? `${p.nazwisko} ${p.imie}`
                : `${p.nazwisko} ${p.imie} ...`
        }));

        faktury.value = fakturyRes.data.results || fakturyRes.data;
        zamowienia.value = zamowieniaRes.data.results || zamowieniaRes.data;
    } catch (error) {
        console.error("Błąd ładowania danych pomocniczych:", error.response?.data || error.message);
    }
};

onMounted(() => {
    fetchInitialData();
    startIdleWatch();
});

onUnmounted(() => {
    stopIdleWatch();
});
</script>

<style scoped>
/* === CIEMNY MOTYW - ZMIENNE BOOTSTRAP 5 DARK === */
:root {
    --dark-bg-primary: #212529;
    --dark-bg-secondary: #2b3035;
    --dark-bg-tertiary: #343a40;
    --dark-bg-card: #2d3238;
    --dark-bg-hover: #3d444d;
    --dark-border: #495057;
    --dark-text-primary: #dee2e6;
    --dark-text-secondary: #adb5bd;
    --dark-text-muted: #6c757d;
    --dark-accent: #0d6efd;
    --dark-accent-hover: #0b5ed7;
    --dark-success: #198754;
    --dark-danger: #dc3545;
    --dark-warning: #ffc107;
}

/* === LAYOUT GŁÓWNY === */
.magazyn-app {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--dark-bg-primary);
    color: var(--dark-text-primary);
    overflow: hidden;
}

/* === NAGŁÓWEK === */
.magazyn-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: linear-gradient(to bottom, #343a40, #212529);
    color: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    flex-shrink: 0;
    z-index: 10;
}

.header-title {
    margin: 0;
    color: #ffc107;
    font-weight: bold;
    font-size: 1.5rem;
}

.header-buttons {
    display: flex;
    gap: 5px;
    align-items: center;
}

/* === PRZYCISKI BOOTSTRAP-STYLE === */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    border: 1px solid transparent;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}

.btn-secondary {
    background-color: #6c757d;
    border-color: #6c757d;
    color: #fff;
}
.btn-secondary:hover {
    background-color: #5c636a;
    border-color: #565e64;
    color: #fff;
}

.btn-success {
    background-color: #198754;
    border-color: #198754;
    color: #fff;
}
.btn-success:hover {
    background-color: #157347;
    border-color: #146c43;
    color: #fff;
}

.btn-primary {
    background-color: #0d6efd;
    border-color: #0d6efd;
    color: #fff;
}
.btn-primary:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
    color: #fff;
}

.btn-logi {
    background-color: #6f42c1;
    border-color: #6f42c1;
    color: #fff;
}
.btn-logi:hover {
    background-color: #5a32a3;
    border-color: #4e2a8e;
    color: #fff;
}

.btn-danger {
    background-color: #dc3545;
    border-color: #dc3545;
    color: #fff;
}
.btn-danger:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
    color: #fff;
}

.btn-dark {
    background-color: #212529;
    border-color: #212529;
    color: #fff;
}
.btn-dark:hover {
    background-color: #1c1f23;
    border-color: #1a1e21;
    color: #fff;
}

.btn-sm {
    padding: 4px 8px;
    font-size: 0.875rem;
}

.btn-sm .pi {
    font-size: 0.875rem;
}

.header-buttons a {
    text-decoration: none;
}

/* User dropdown button */
.dropdown-wrapper {
    position: relative;
}

.user-dropdown-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    background-color: #dc3545;
    color: white;
    border: 1px solid #dc3545;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: background-color 0.2s;
}

.user-dropdown-btn:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

.user-name-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 500;
    color: #ffc107;
}

/* === TRYB PRODUKCJA - NAGŁÓWEK === */
.header-user-name-prod {
    flex: 1;
    text-align: center;
    color: #e9ecef;
    font-size: 1rem;
    font-weight: 500;
}

.header-buttons-prod {
    display: flex;
    gap: 5px;
    align-items: center;
}

.btn-narzedzia-prod {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #17a2b8;
    background-color: #17a2b8;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
    text-decoration: none;
}

.btn-narzedzia-prod:hover {
    background-color: #138496;
    border-color: #117a8b;
    color: #fff;
}

.btn-exit-prod {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    border: 1px solid #dc3545;
    background-color: #dc3545;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s ease-in-out;
}

.btn-exit-prod:hover {
    background-color: #bb2d3b;
    border-color: #b02a37;
}

/* === GŁÓWNA ZAWARTOŚĆ === */
.magazyn-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 24px 10px 24px;
    gap: 16px;
    min-height: 0;
    overflow: hidden;
}

/* === PANEL NARZĘDZI (GÓRNY) - STYL JAK NAGŁÓWEK === */
.tools-panel {
    flex: 0 0 45%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    border: none;
    min-height: 0;
    overflow: hidden;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    border-radius: 6px 6px 0 0;
    flex-shrink: 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.panel-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffc107;
}

.search-box {
    display: flex;
    align-items: center;
}

/* Bootstrap-like form controls - ciemny motyw */
.form-control {
    display: block;
    padding: 6px 12px;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-tertiary);
    background-clip: padding-box;
    border: 1px solid var(--dark-border);
    border-radius: 4px;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.form-control:focus {
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-secondary);
    border-color: var(--dark-accent);
    outline: 0;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}

.form-control::placeholder {
    color: var(--dark-text-muted);
}

.form-select {
    display: block;
    padding: 6px 32px 6px 12px;
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--dark-text-primary);
    background-color: var(--dark-bg-tertiary);
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23adb5bd' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 8px center;
    background-size: 16px 12px;
    border: 1px solid var(--dark-border);
    border-radius: 4px;
    appearance: none;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.form-select:focus {
    border-color: var(--dark-accent);
    outline: 0;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}

.form-select:disabled {
    background-color: var(--dark-bg-primary);
    opacity: 0.65;
    cursor: not-allowed;
}

/* Wyróżnienie pól wyszukiwania */
.search-input {
    width: 180px;
    background-color: #495057 !important;
    border: 2px solid #6c757d !important;
    color: #fff !important;
}

.search-input:focus {
    background-color: #4a5258 !important;
    border-color: #ffc107 !important;
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3) !important;
}

.search-input::placeholder {
    color: #adb5bd;
}

.filter-box {
    display: flex;
    gap: 8px;
}

/* Wyróżnienie dropdownów filtrów */
.filter-select {
    min-width: 180px;
    background-color: #495057 !important;
    border: 2px solid #6c757d !important;
    color: #fff !important;
}

.filter-select:focus {
    background-color: #4a5258 !important;
    border-color: #ffc107 !important;
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3) !important;
}

.filter-select:not(:disabled):hover {
    border-color: #adb5bd;
}

/* Stylowanie opcji w native select */
.filter-select option,
.form-select option {
    background-color: #343a40;
    color: #dee2e6;
    padding: 8px 12px;
}

.filter-select option:checked,
.form-select option:checked {
    background-color: #4a3728;
    color: #fff;
}

.panel-body {
    flex: 1;
    overflow: auto;
    min-height: 0;
}

/* === TABELE PRIMEVUE - STYL JAK NAGŁÓWEK === */
:deep(.p-datatable) {
    font-size: 0.9rem;
    background: transparent;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
    background: linear-gradient(to bottom, #4a5258, #3d444d) !important;
    color: #fff !important;
    padding: 10px 12px;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: none;
    letter-spacing: 0;
    border-bottom: none !important;
    white-space: nowrap;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

:deep(.p-datatable .p-datatable-tbody > tr) {
    background-color: var(--dark-bg-card) !important;
    color: var(--dark-text-primary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:nth-child(even)) {
    background-color: var(--dark-bg-secondary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr > td) {
    padding: 8px 12px;
    border-bottom: 1px solid var(--dark-border) !important;
    vertical-align: middle;
    color: var(--dark-text-primary) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr:hover) {
    background-color: var(--dark-bg-hover) !important;
}

:deep(.p-datatable .p-datatable-tbody > tr.p-highlight),
:deep(.p-datatable .p-datatable-tbody > tr.p-highlight > td) {
    background-color: #4a3728 !important;
    color: #fff !important;
}

:deep(.selected-row),
:deep(.selected-row td) {
    background-color: #4a3728 !important;
    color: #fff !important;
}

/* Nowy wpis - brązowe wyróżnienie (jak przycisk Zwroty) */
:deep(.nowy-wpis-row),
:deep(.nowy-wpis-row td) {
    background-color: #3b2510 !important;
    border-left: 3px solid #8B4513 !important;
}

.oznaczenie-cell {
    display: flex;
    align-items: center;
    gap: 6px;
}

.etykieta-btn {
    padding: 0.15rem 0.3rem !important;
    min-width: unset !important;
    color: #cd7f32 !important;
    flex-shrink: 0;
}

.etykieta-btn:hover {
    color: #ffc107 !important;
    background-color: rgba(139, 69, 19, 0.2) !important;
}

/* Sticky header dla tabel */
:deep(.p-datatable-scrollable .p-datatable-thead) {
    position: sticky;
    top: 0;
    z-index: 1;
}

/* === PANEL SZCZEGÓŁÓW (DOLNY) - STYL JAK NAGŁÓWEK === */
.details-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
    background: linear-gradient(to bottom, #343a40, #212529);
    border-radius: 6px;
    border: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

/* === ZAKŁADKI (TABS) - STYL JAK NAGŁÓWEK === */
:deep(.p-tabview) {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: transparent;
    border-radius: 0;
}

:deep(.p-tabview-nav-container) {
    flex-shrink: 0;
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

:deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
    border-bottom-color: #ffc107;
    color: #ffc107;
    background: rgba(255, 193, 7, 0.1);
}

:deep(.p-tabview-panels) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    padding: 0;
    background: #212529;
}

:deep(.p-tabview-panel) {
    height: 100%;
    padding: 0;
}

/* Badge w nagłówku zakładki */
:deep(.p-tabview-nav-link .p-badge) {
    margin-left: 8px;
    font-size: 0.75rem;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
}

.tab-content-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* === SZCZEGÓŁY NARZĘDZIA === */
.details-content {
    display: flex;
    height: 100%;
    overflow: hidden;
}

.instances-table {
    flex: 1;
    overflow: auto;
    min-width: 0;
}

.instances-datatable {
    height: 100%;
}

.tool-image-panel {
    width: 30%;
    min-width: 200px;
    max-width: 400px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-left: 1px solid #495057;
    background: linear-gradient(to right, #2d3238, #343a40);
    padding: 16px;
    flex-shrink: 0;
    overflow: hidden;
}

.tool-image {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    display: block;
}

/* Tab badge styling */
.tab-badge {
    display: inline-block;
    margin-left: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 500;
    background-color: #6c757d;
    color: white;
    border-radius: 4px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
}

/* Button group inline */
.btn-group-inline {
    display: inline-flex;
    gap: 4px;
    white-space: nowrap;
}

/* === NAGŁÓWEK "W UŻYCIU" - STYL JAK PANEL === */
.in-use-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: linear-gradient(to bottom, #3d444d, #343a40);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    flex-shrink: 0;
}

.in-use-header .search-input {
    width: 180px;
}

.filter-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-row label {
    margin: 0;
    font-weight: 500;
    color: #dee2e6;
    white-space: nowrap;
}

/* === STANY === */
.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    flex: 1;
}

.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
    color: #6c757d;
    text-align: center;
    flex: 1;
}

/* === FORMULARZE (MODAL) - CIEMNY MOTYW === */
.field {
    margin-bottom: 16px;
}

.field label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: var(--dark-text-primary);
}

:deep(.field .p-inputtext),
:deep(.field .p-dropdown),
:deep(.field .p-inputnumber),
:deep(.field .p-password) {
    width: 100%;
}

.return-status-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.field-radiobutton {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Sekcje w modalu */
.modal-section {
    margin: 20px 0;
    padding: 16px;
    background: rgba(52, 58, 64, 0.5);
    border: 1px solid var(--dark-border);
    border-radius: 6px;
}

.modal-section-title {
    font-weight: 600;
    color: #ffc107;
    margin-bottom: 12px;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.radio-options-horizontal {
    display: flex;
    gap: 24px;
}

.radio-options-vertical {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.field-radiobutton label {
    margin-bottom: 0;
    font-weight: normal;
    cursor: pointer;
}

.tool-image-preview {
    max-width: 150px;
    border-radius: 8px;
    margin-top: 10px;
}

/* === O PROGRAMIE - CIEMNY MOTYW === */
.about-content {
    text-align: center;
    color: var(--dark-text-primary);
}

.about-header {
    margin-bottom: 24px;
}

.about-logo {
    width: 80px;
    height: 80px;
}

.about-table {
    width: 100%;
    text-align: left;
    color: var(--dark-text-primary);
}

.about-table td {
    padding: 8px 0;
}

.about-table .label {
    text-align: right;
    color: var(--dark-text-muted);
    padding-right: 16px;
    width: 40%;
}

/* === PRZYCISKI === */
:deep(.p-button-sm) {
    padding: 6px 10px;
    font-size: 0.875rem;
}

:deep(.p-button-sm .p-button-icon) {
    font-size: 0.875rem;
}

/* === TAGI/BADGE === */
:deep(.p-tag) {
    font-size: 0.8rem;
    padding: 4px 8px;
}

/* === UTILITY === */
.text-muted {
    color: #6c757d;
}

:deep(.date-time) {
    color: #7a8a9a;
}

.required-mark {
    color: #5a6570;
    font-size: 0.85em;
}

.text-danger {
    color: #dc3545;
}

.text-center {
    text-align: center;
}

.ml-2 {
    margin-left: 8px;
}

.mr-1 {
    margin-right: 4px;
}

.mt-3 {
    margin-top: 16px;
}

/* === WARTOŚĆ ZEROWA W TABELI === */
.zero-value {
    color: #6c757d !important;
}

/* === KARTA USZKODZENIA === */
.karta-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.karta-row .field {
    flex: 1;
    margin-bottom: 0;
}

.karta-numer {
    font-weight: bold !important;
    color: #ffc107 !important;
    background-color: #3d444d !important;
}

:deep(.karta-textarea.p-inputtextarea) {
    height: 76px !important;
    min-height: 76px !important;
    resize: none;
}

</style>

<!-- Style dla menu popup (bez scoped - menu jest renderowane jako portal) - CIEMNY MOTYW -->
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

/* === MENU DZIAŁANIA === */
#dzialania_menu,
#miejsca_menu {
    min-width: 180px !important;
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.5) !important;
    padding: 6px 0 !important;
}

#dzialania_menu_list,
#miejsca_menu_list {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}

#dzialania_menu_list li,
#miejsca_menu_list li {
    margin: 0 !important;
    padding: 0 !important;
}

#dzialania_menu_list li > div,
#miejsca_menu_list li > div {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    transition: background-color 0.15s !important;
}

#dzialania_menu_list li > div:hover,
#miejsca_menu_list li > div:hover {
    background-color: #3d444d !important;
}

#dzialania_menu_list li > div > a,
#dzialania_menu_list li > div > div,
#miejsca_menu_list li > div > a,
#miejsca_menu_list li > div > div {
    display: flex !important;
    align-items: center !important;
    padding: 10px 16px !important;
    color: #dee2e6 !important;
    text-decoration: none !important;
    gap: 10px !important;
    cursor: pointer !important;
}

#dzialania_menu_list li > div span[class*="icon"],
#dzialania_menu_list li > div i,
#dzialania_menu_list li > div .pi,
#miejsca_menu_list li > div span[class*="icon"],
#miejsca_menu_list li > div i,
#miejsca_menu_list li > div .pi {
    color: #adb5bd !important;
    font-size: 1rem !important;
}

#dzialania_menu_list li > div span:not([class*="icon"]):not(.pi),
#miejsca_menu_list li > div span:not([class*="icon"]):not(.pi) {
    color: #dee2e6 !important;
    font-size: 14px !important;
}

/* === MODALE PRIMEVUE - KOMPLETNY CIEMNY MOTYW === */

/* Overlay/Backdrop */
.p-dialog-mask {
    background-color: rgba(0, 0, 0, 0.6) !important;
    backdrop-filter: blur(2px);
}

/* Główny kontener dialogu */
.p-dialog {
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 8px !important;
    color: #dee2e6 !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important;
    overflow: hidden;
}

/* Nagłówek dialogu */
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

/* Przycisk zamknięcia */
.p-dialog .p-dialog-header-icons {
    display: flex;
    gap: 4px;
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

.p-dialog .p-dialog-header-icon:focus {
    box-shadow: none !important;
}

/* Zawartość dialogu */
.p-dialog .p-dialog-content {
    background: #2d3238 !important;
    color: #dee2e6 !important;
    padding: 20px !important;
}

/* Stopka dialogu */
.p-dialog .p-dialog-footer {
    background: linear-gradient(to bottom, #343a40, #2d3238) !important;
    border-top: 1px solid #495057 !important;
    padding: 12px 20px !important;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}

/* Etykiety w formularzach */
.p-dialog .field label {
    color: #dee2e6 !important;
    font-weight: 500;
    margin-bottom: 8px;
    display: block;
}

/* RadioButton w dialogach */
.p-radiobutton .p-radiobutton-box {
    background: #343a40 !important;
    border-color: #6c757d !important;
    width: 20px !important;
    height: 20px !important;
}

.p-radiobutton .p-radiobutton-box:hover {
    border-color: #adb5bd !important;
}

.p-radiobutton .p-radiobutton-box.p-highlight {
    background: #0d6efd !important;
    border-color: #0d6efd !important;
}

.p-radiobutton .p-radiobutton-box .p-radiobutton-icon {
    background: #fff !important;
}

/* Message w dialogach */
.p-dialog .p-message {
    margin: 0 0 16px 0 !important;
    border-radius: 6px !important;
}

.p-dialog .p-message.p-message-error {
    background: rgba(220, 38, 38, 0.15) !important;
    border: 1px solid rgba(220, 38, 38, 0.4) !important;
    color: #f87171 !important;
}

.p-dialog .p-message .p-message-wrapper {
    padding: 12px 16px !important;
}

.p-dialog .p-message .p-message-text {
    color: #f87171 !important;
}

/* InputText disabled w dialogach */
.p-dialog .p-inputtext:disabled,
.p-dialog .p-inputtext[disabled] {
    background: #212529 !important;
    color: #6c757d !important;
    opacity: 0.8 !important;
    cursor: not-allowed !important;
}

/* Tekst danger w dialogach */
.p-dialog .text-danger {
    color: #f87171 !important;
    font-weight: 500;
}

/* Podgląd obrazu w dialogach */
.p-dialog .tool-image-preview {
    max-width: 150px;
    border-radius: 8px;
    margin-top: 10px;
    border: 1px solid #495057;
}

/* Input file w dialogach */
.p-dialog input[type="file"] {
    background: #343a40 !important;
    border: 1px solid #495057 !important;
    border-radius: 4px !important;
    color: #dee2e6 !important;
    padding: 8px !important;
    width: 100% !important;
}

.p-dialog input[type="file"]::file-selector-button {
    background: #495057 !important;
    border: none !important;
    border-radius: 4px !important;
    color: #fff !important;
    padding: 6px 12px !important;
    margin-right: 10px !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
}

.p-dialog input[type="file"]::file-selector-button:hover {
    background: #5c636a !important;
}

/* About modal specjalne style */
.p-dialog .about-content {
    text-align: center;
}

.p-dialog .about-header h4 {
    color: #ffc107 !important;
    margin: 10px 0 5px 0;
}

.p-dialog .about-header p {
    color: #adb5bd !important;
}

.p-dialog .about-table {
    margin-top: 20px;
}

.p-dialog .about-table td {
    padding: 8px 0;
    color: #dee2e6;
}

.p-dialog .about-table .label {
    color: #adb5bd !important;
}

.p-dialog .about-table a {
    color: #0d6efd !important;
    text-decoration: none;
}

.p-dialog .about-table a:hover {
    color: #3d8bfd !important;
    text-decoration: underline;
}

/* About modal footer */
.about-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.about-footer .copyright {
    color: #6c757d !important;
    font-size: 0.85rem;
}

/* === PRZYCISKI W MODALACH - STYL JAK W GŁÓWNYM OKNIE === */

/* Przycisk główny (niebieski) */
.p-dialog .p-button:not(.p-button-text):not(.p-button-secondary):not(.p-button-success):not(.p-button-danger):not(.btn-modal-secondary) {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button:not(.p-button-text):not(.p-button-secondary):not(.p-button-success):not(.p-button-danger):not(.btn-modal-secondary):hover {
    background-color: #0b5ed7 !important;
    border-color: #0a58ca !important;
}

/* Przycisk tekstowy (Anuluj) */
.p-dialog .p-button.p-button-text {
    background: transparent !important;
    border: 1px solid #6c757d !important;
    color: #adb5bd !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
}

.p-dialog .p-button.p-button-text:hover {
    background: rgba(108, 117, 125, 0.2) !important;
    border-color: #adb5bd !important;
    color: #dee2e6 !important;
}

/* Przycisk secondary (szary) */
.p-dialog .p-button.btn-modal-secondary,
.p-dialog .p-button.p-button-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.btn-modal-secondary:hover,
.p-dialog .p-button.p-button-secondary:hover {
    background-color: #5c636a !important;
    border-color: #565e64 !important;
}

/* Przycisk success (zielony) */
.p-dialog .p-button.p-button-success {
    background-color: #198754 !important;
    border-color: #198754 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.p-button-success:hover {
    background-color: #157347 !important;
    border-color: #146c43 !important;
}

/* Przycisk danger (czerwony) */
.p-dialog .p-button.p-button-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
    color: #fff !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}

.p-dialog .p-button.p-button-danger:hover {
    background-color: #bb2d3b !important;
    border-color: #b02a37 !important;
}

/* === UJEDNOLICONA WYSOKOŚĆ PÓL W MODALACH === */
.p-dialog .p-inputtext,
.p-dialog .p-dropdown,
.p-dialog .p-inputnumber,
.p-dialog .p-inputnumber-input {
    height: 40px !important;
    min-height: 40px !important;
}

.p-dialog .p-dropdown .p-dropdown-label {
    padding: 8px 12px !important;
    line-height: 1.5 !important;
}

.p-dialog .p-inputtext {
    padding: 8px 12px !important;
    line-height: 1.5 !important;
}

.p-dialog .p-inputnumber {
    width: 100% !important;
}

.p-dialog .p-inputnumber-input {
    padding: 8px 12px !important;
    width: 100% !important;
}

/* PrimeVue Dropdown/Select - Bootstrap 5 Dark */
.p-dropdown {
    background: #343a40 !important;
    border: 1px solid #495057 !important;
    border-radius: 4px !important;
    color: #dee2e6 !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.p-dropdown:hover {
    border-color: #6c757d !important;
}

.p-dropdown:focus,
.p-dropdown.p-focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
}

.p-dropdown .p-dropdown-label {
    color: #dee2e6 !important;
    padding: 8px 12px !important;
}

.p-dropdown .p-dropdown-label.p-placeholder {
    color: #6c757d !important;
}

.p-dropdown .p-dropdown-trigger {
    background: transparent !important;
    color: #adb5bd !important;
    width: 40px !important;
}

.p-dropdown-panel {
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
    margin-top: 2px !important;
}

.p-dropdown-header {
    background: #343a40 !important;
    border-bottom: 1px solid #495057 !important;
    padding: 10px !important;
}

.p-dropdown-header .p-dropdown-filter {
    background: #495057 !important;
    border: 1px solid #6c757d !important;
    border-radius: 4px !important;
    color: #fff !important;
    height: 38px !important;
    min-height: 38px !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
    width: 100% !important;
}

.p-dropdown-header .p-dropdown-filter:focus {
    border-color: #ffc107 !important;
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.3) !important;
    outline: none !important;
}

.p-dropdown-header .p-dropdown-filter::placeholder {
    color: #adb5bd !important;
}

.p-dropdown-items-wrapper {
    background: #2d3238 !important;
    max-height: 300px !important;
}

.p-dropdown-items {
    padding: 4px 0 !important;
}

.p-dropdown-item {
    color: #dee2e6 !important;
    padding: 10px 16px !important;
    transition: background 0.15s ease !important;
}

.p-dropdown-item:hover {
    background: #3d444d !important;
}

.p-dropdown-item.p-highlight {
    background: #4a3728 !important;
    color: #fff !important;
}

.p-dropdown-item-group {
    background: #343a40 !important;
    color: #ffc107 !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
}

/* Dropdown empty message */
.p-dropdown-empty-message {
    color: #6c757d !important;
    padding: 10px 16px !important;
}

/* PrimeVue InputText - Bootstrap 5 Dark */
.p-inputtext {
    background: #343a40 !important;
    border-color: #495057 !important;
    color: #dee2e6 !important;
}

.p-inputtext:focus {
    border-color: #0d6efd !important;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
}

/* PrimeVue InputNumber - Bootstrap 5 Dark */
.p-inputnumber-input {
    background: #343a40 !important;
    border-color: #495057 !important;
    color: #dee2e6 !important;
}

/* === PRZYCISKI PRIMEVUE - BOOTSTRAP COLORS === */
.p-button {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    font-weight: 500 !important;
    gap: 0.5rem;
}

.p-button.p-button-success {
    background-color: #198754 !important;
    border-color: #198754 !important;
}
.p-button.p-button-success:hover {
    background-color: #157347 !important;
    border-color: #146c43 !important;
}

.p-button.p-button-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
}
.p-button.p-button-secondary:hover {
    background-color: #5c636a !important;
    border-color: #565e64 !important;
}

.p-button.p-button-primary {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
}
.p-button.p-button-primary:hover {
    background-color: #0b5ed7 !important;
    border-color: #0a58ca !important;
}

.p-button.p-button-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
}
.p-button.p-button-danger:hover {
    background-color: #bb2d3b !important;
    border-color: #b02a37 !important;
}

.p-button.p-button-sm {
    padding: 0.4rem 0.65rem !important;
    font-size: 0.875rem !important;
}

/* Tag/Badge colors */
.p-tag.p-tag-success {
    background-color: #198754 !important;
}
.p-tag.p-tag-danger {
    background-color: #dc3545 !important;
}
.p-tag.p-tag-warning {
    background-color: #ffc107 !important;
    color: #000 !important;
}
.p-tag.p-tag-info {
    background-color: #0dcaf0 !important;
    color: #000 !important;
}
.p-tag.p-tag-secondary {
    background-color: #6c757d !important;
}

/* === SCROLLBAR - CIEMNY MOTYW === */
::-webkit-scrollbar {
    width: 10px;
    height: 14px;
}

::-webkit-scrollbar-track {
    background: #212529;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(to right, #4a5568, #5a6577, #4a5568);
    border-radius: 6px;
    border: 2px solid #212529;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to right, #5a6577, #6b7688, #5a6577);
}

/* === SCROLLBAR W TABELACH === */
.p-datatable .p-datatable-wrapper::-webkit-scrollbar {
    width: 10px;
    height: 14px;
}

.p-datatable .p-datatable-wrapper::-webkit-scrollbar-track {
    background: #212529;
}

.p-datatable .p-datatable-wrapper::-webkit-scrollbar-thumb {
    background: linear-gradient(to bottom, #5a6577, #4a5568);
    border-radius: 5px;
    border: 2px solid #212529;
}

.p-datatable .p-datatable-wrapper::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(to bottom, #6b7688, #5a6577);
}

.p-datatable .p-datatable-wrapper::-webkit-scrollbar-corner {
    background: #212529;
}

/* === TABELA - NAGŁÓWEK STICKY === */

/* Nagłówek sticky - przyklejony do góry podczas przewijania pionowego */
.p-datatable .p-datatable-thead {
    position: sticky !important;
    top: 0 !important;
    z-index: 3 !important;
}

.p-datatable .p-datatable-thead > tr > th {
    background: linear-gradient(to bottom, #3d444d, #343a40) !important;
    border-bottom: 2px solid #4a5568 !important;
}

/* Scrollbar poziomy - tylko pod body tabeli */
.p-datatable .p-datatable-table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
}

/* Ukryj scrollbar w headerze - pokaż tylko w udziale body */
.p-datatable .p-datatable-thead tr {
    display: table-row !important;
}

/* Body tabeli */
.p-datatable .p-datatable-tbody > tr > td {
    background: #2b3035 !important;
}
</style>

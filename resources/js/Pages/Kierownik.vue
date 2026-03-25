<template>
    <div class="magazyn-app">
        <!-- Nagłówek -->
        <header class="magazyn-header">
            <h2 class="header-title">PANEL KIEROWNIKA</h2>
            <div class="header-buttons">
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
        <main class="magazyn-main">
            <!-- Widok: Lista narzędzi -->
            <div v-if="currentView === 'lista'" class="tools-panel">
                <div class="panel-header">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="searchInput"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">Lista narzędzi</h3>
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
                        :paginator="true"
                        :rows="pageSize"
                        :scrollable="true"
                        scrollHeight="flex"
                        selectionMode="single"
                        v-model:selection="selectedTool"
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
                                <button
                                    v-if="data.ilosc_w_uzyciu > 0"
                                    class="usage-btn"
                                    @click.stop="openUsageModal(data)"
                                >{{ data.ilosc_w_uzyciu }}</button>
                                <span v-else class="zero-value">0</span>
                            </template>
                        </Column>
                        <Column field="calkowita_ilosc" header="Razem" style="width: 80px; text-align: center;">
                            <template #body="{ data }">
                                <strong :class="{ 'zero-value': data.calkowita_ilosc === 0 }">{{ data.calkowita_ilosc }}</strong>
                            </template>
                        </Column>
                        <Column header="" style="width: 90px; text-align: center;">
                            <template #body="{ data }">
                                <div style="display: flex; gap: 4px; justify-content: center;">
                                    <button class="btn-preview" @click.stop="openPreviewModal(data)" title="Podgląd">
                                        <i class="pi pi-image"></i>
                                    </button>
                                    <button class="btn-history" @click.stop="openHistoryModal(data)" title="Historia użycia">
                                        <i class="pi pi-history"></i>
                                    </button>
                                </div>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Widok: Narzędzia w użyciu -->
            <div v-if="currentView === 'w_uzyciu'" class="tools-panel">
                <div class="panel-header" style="height: 50px;">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="inUseSearchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">
                        Narzędzia w użyciu
                        <Badge :value="usagesInUse.length" style="background-color: #8B4513; margin-left: 8px;" />
                    </h3>
                    <div class="filter-box">
                        <select
                            v-model="selectedMaszynaFilter"
                            class="form-select filter-select"
                        >
                            <option :value="null">Wszystkie maszyny</option>
                            <option v-for="m in machines" :key="m.id" :value="m.id">
                                {{ m.nazwa }}
                            </option>
                        </select>
                        <button class="btn-chart" @click="openChartModal" title="Wykres">
                            <i class="pi pi-chart-bar"></i>
                        </button>
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredUsagesInUse"
                        :loading="isLoadingTools"
                        :scrollable="true"
                        scrollHeight="flex"
                        class="tools-table"
                    >
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
                        <template #empty>
                            <div class="empty-state">Brak narzędzi w użyciu.</div>
                        </template>
                    </DataTable>
                </div>
            </div>
            <!-- Widok: Uszkodzone elementy -->
            <div v-if="currentView === 'uszkodzone'" class="tools-panel">
                <div class="panel-header" style="height: 50px;">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="dmgSearchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">
                        Uszkodzone elementy
                        <Badge :value="filteredDamagesUszkodzone.length" severity="danger" style="margin-left: 8px;" />
                    </h3>
                    <div class="filter-box">
                        <button class="btn-pdf-header" @click="openDmgPdfList('uszkodzone')" title="Eksport PDF całej listy">
                            <i class="pi pi-file-pdf"></i>
                        </button>
                        <button class="btn-chart" @click="openDmgChartModal('uszkodzone')" title="Wykres">
                            <i class="pi pi-chart-bar"></i>
                        </button>
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredDamagesUszkodzone"
                        :loading="isLoadingDamages"
                        :scrollable="true"
                        scrollHeight="flex"
                        class="tools-table"
                        stripedRows
                    >
                        <Column header="Nr karty" style="width: 100px;">
                            <template #body="{ data }">
                                <strong v-if="data.numer_karty" class="karta-numer-dmg">{{ data.numer_karty }}</strong>
                                <span v-else>-</span>
                            </template>
                        </Column>
                        <Column header="Data uszkodzenia">
                            <template #body="{ data }">
                                <span v-html="formatCustomDate(data.data_uszkodzenia)"></span>
                            </template>
                        </Column>
                        <Column header="Ostatnia maszyna">
                            <template #body="{ data }">
                                {{ data.maszyna_uszkodzenia || '-' }}
                            </template>
                        </Column>
                        <Column header="Zgłaszający">
                            <template #body="{ data }">
                                {{ data.nazwisko_zglaszajacego || formatDmgPracownik(data.ostatni_pracownik) }}
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
                        <Column style="text-align: center;">
                            <template #header>
                                <div style="text-align: center; line-height: 1.3;">Stracony czas<br><span class="stracony-czas-unit">[godz.]</span></div>
                            </template>
                            <template #body="{ data }">
                                <span v-if="data.stracony_czas" class="stracony-czas-value">{{ formatMinutesToHours(data.stracony_czas) }}</span>
                                <span v-else class="stracony-czas-empty">?</span>
                            </template>
                        </Column>
                        <Column header="" style="width: 100px; text-align: center;">
                            <template #body="{ data }">
                                <button class="btn-details-row" @click="openDmgDetailModal(data)" title="Szczegóły">
                                    <i class="pi pi-info-circle"></i>
                                </button>
                                <button class="btn-pdf-row" @click="openDmgPdfSingle(data)" title="Eksport PDF">
                                    <i class="pi pi-file-pdf"></i>
                                </button>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>

            <!-- Widok: Zużyte -->
            <div v-if="currentView === 'zuzyte'" class="tools-panel">
                <div class="panel-header" style="height: 50px;">
                    <div class="search-box">
                        <input
                            type="text"
                            v-model="regenSearchQuery"
                            placeholder="Szukaj..."
                            class="form-control search-input"
                        />
                    </div>
                    <h3 class="panel-title">
                        Zużyte
                        <Badge :value="filteredDamagesRegeneracja.length" style="background-color: #8B4513; margin-left: 8px;" />
                    </h3>
                    <div class="filter-box">
                        <button class="btn-pdf-header" @click="openDmgPdfList('regeneracja')" title="Eksport PDF całej listy">
                            <i class="pi pi-file-pdf"></i>
                        </button>
                        <button class="btn-chart" @click="openDmgChartModal('zuzyte')" title="Wykres">
                            <i class="pi pi-chart-bar"></i>
                        </button>
                    </div>
                </div>
                <div class="panel-body">
                    <DataTable
                        :value="filteredDamagesRegeneracja"
                        :loading="isLoadingDamages"
                        :scrollable="true"
                        scrollHeight="flex"
                        class="tools-table"
                        stripedRows
                    >
                        <Column header="Nr karty" style="width: 100px;">
                            <template #body="{ data }">
                                <strong v-if="data.numer_karty" class="karta-numer-regen">{{ data.numer_karty }}</strong>
                                <span v-else>-</span>
                            </template>
                        </Column>
                        <Column header="Data uszkodzenia">
                            <template #body="{ data }">
                                <span v-html="formatCustomDate(data.data_uszkodzenia)"></span>
                            </template>
                        </Column>
                        <Column header="Ostatnia maszyna">
                            <template #body="{ data }">
                                {{ data.maszyna_uszkodzenia || '-' }}
                            </template>
                        </Column>
                        <Column header="Ostatni użytkownik">
                            <template #body="{ data }">
                                {{ formatDmgPracownik(data.ostatni_pracownik) }}
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
                        <Column header="" style="width: 50px; text-align: center;">
                            <template #body="{ data }">
                                <button class="btn-pdf-row" @click="openDmgPdfSingle(data)" title="Eksport PDF">
                                    <i class="pi pi-file-pdf"></i>
                                </button>
                            </template>
                        </Column>
                    </DataTable>
                </div>
            </div>
        </main>

        <!-- Modal: Podgląd PDF uszkodzenia -->
        <Dialog
            v-model:visible="dmgPdfPreviewVisible"
            header="Podgląd PDF"
            :modal="true"
            :style="{ width: '90vw', maxWidth: '1000px' }"
            :contentStyle="{ padding: '0', overflow: 'hidden' }"
            @hide="closeDmgPdfPreview"
        >
            <div class="pdf-preview-container">
                <iframe
                    id="dmg-pdf-preview-iframe"
                    :src="dmgPdfPreviewUrl"
                    class="pdf-iframe"
                ></iframe>
            </div>
            <template #footer>
                <Button label="Zamknij" icon="pi pi-times" class="btn-modal-secondary" @click="closeDmgPdfPreview" />
            </template>
        </Dialog>

        <!-- Modal: Wykres uszkodzeń/zużytych -->
        <Dialog
            v-model:visible="showDmgChartModal"
            :header="dmgChartType === 'uszkodzone' ? 'Wykres uszkodzonych elementów' : 'Wykres zużytych elementów'"
            :style="{ width: '70vw' }"
            :contentStyle="{ height: dmgChartContentHeight + 'px', maxHeight: '80vh', overflow: 'auto' }"
            :modal="true"
            class="usage-modal chart-modal"
        >
            <div class="chart-controls">
                <label>Grupuj wg:</label>
                <select v-model="dmgChartGroupBy" class="form-select chart-select">
                    <option value="maszyna">Maszyna</option>
                    <option value="osoba">{{ dmgChartType === 'uszkodzone' ? 'Zgłaszający' : 'Ostatni użytkownik' }}</option>
                </select>
            </div>
            <div class="chart-scroll-wrapper">
                <div class="chart-container" :style="{ height: dmgChartHeightPx + 'px' }">
                    <Chart v-if="dmgChartReady" :key="dmgChartKey" type="bar" :data="dmgChartData" :options="chartOptions" :height="dmgChartHeightPx" />
                </div>
            </div>
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

        <!-- Modal: Narzędzia w użyciu -->
        <Dialog
            v-model:visible="showUsageModal"
            :header="selectedToolForUsage ? `Narzędzia w użyciu: ${selectedToolForUsage.opis}` : 'Narzędzia w użyciu'"
            :style="{ width: '70vw' }"
            :modal="true"
            class="usage-modal"
        >
            <DataTable :value="usagesForSelectedTool" :scrollable="true" scrollHeight="400px" class="usage-datatable">
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
                <template #empty>
                    <div class="empty-state">Brak narzędzi w użyciu.</div>
                </template>
            </DataTable>
        </Dialog>

        <!-- Modal: Podgląd narzędzia -->
        <Dialog v-model:visible="previewModalVisible" :header="previewTool ? previewTool.opis : 'Podgląd'" :modal="true" :style="{ width: '500px' }">
            <div class="preview-content">
                <img
                    v-if="previewTool && previewTool.obraz"
                    :src="previewTool.obraz"
                    class="preview-image"
                    alt="Obrazek narzędzia"
                />
                <img
                    v-else
                    :src="defaultToolImage"
                    class="preview-image"
                    alt="Domyślny obrazek narzędzia"
                />
            </div>
            <template #footer>
                <Button label="Zamknij" class="btn-modal-secondary" @click="previewModalVisible = false" />
            </template>
        </Dialog>

        <!-- Modal: Historia użycia -->
        <Dialog
            v-model:visible="showHistoryModal"
            :header="selectedToolForHistory ? `Historia użycia: ${selectedToolForHistory.opis}` : 'Historia użycia'"
            :style="{ width: '80vw' }"
            :modal="true"
            class="usage-modal"
        >
            <div v-if="isLoadingHistory" class="loading-spinner">
                <ProgressSpinner />
            </div>
            <DataTable v-else :value="toolHistory" :scrollable="true" scrollHeight="400px" class="usage-datatable">
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
        </Dialog>

        <!-- Modal: Wykres -->
        <Dialog
            v-model:visible="showChartModal"
            header="Wykres narzędzi w użyciu"
            :style="{ width: '70vw' }"
            :contentStyle="{ height: chartContentHeight + 'px', maxHeight: '80vh', overflow: 'auto' }"
            :modal="true"
            class="usage-modal chart-modal"
        >
            <div class="chart-controls">
                <label>Grupuj wg:</label>
                <select v-model="chartGroupBy" class="form-select chart-select">
                    <option value="maszyna">Maszyna</option>
                    <option value="pracownik">Pracownik</option>
                </select>
            </div>
            <div class="chart-scroll-wrapper">
                <div class="chart-container" :style="{ height: chartHeightPx + 'px' }">
                    <Chart v-if="chartReady" :key="chartKey" type="bar" :data="chartData" :options="chartOptions" :height="chartHeightPx" />
                </div>
            </div>
        </Dialog>

        <!-- Modal: Szczegóły uszkodzenia -->
        <Dialog
            v-model:visible="dmgDetailModalVisible"
            header="Szczegóły uszkodzenia"
            :modal="true"
            :style="{ width: '1200px' }"
        >
            <div v-if="dmgDetailData" class="dmg-detail-grid">
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Nr karty:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.numer_karty || '-' }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Data uszkodzenia:</span>
                    <span class="dmg-detail-value" v-html="formatCustomDate(dmgDetailData.data_uszkodzenia)"></span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Ostatnia maszyna:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.maszyna_uszkodzenia || '-' }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Zgłaszający:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.nazwisko_zglaszajacego || formatDmgPracownik(dmgDetailData.ostatni_pracownik) }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Narzędzie:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.kategoria_narzedzia }}: {{ dmgDetailData.opis_narzedzia }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Nr katalogowy:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.numer_katalogowy || '-' }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Przyczyna uszkodzenia:</span>
                    <span class="dmg-detail-value">{{ dmgDetailData.przyczyna_uszkodzenia || '-' }}</span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Stracony czas:</span>
                    <span class="dmg-detail-value dmg-detail-value-inline">
                        <input type="number" v-model.number="dmgEditStracony" class="dmg-edit-input dmg-edit-input-short" min="0" />
                        <span class="dmg-edit-hint">wartość w minutach</span>
                    </span>
                </div>
                <div class="dmg-detail-row">
                    <span class="dmg-detail-label">Uwagi:</span>
                    <span class="dmg-detail-value">
                        <textarea v-model="dmgEditUwagi" class="dmg-edit-input dmg-edit-textarea" rows="3" placeholder="Uwagi..."></textarea>
                    </span>
                </div>
            </div>
            <template #footer>
                <Button label="Zapisz" icon="pi pi-check" severity="danger" @click="saveDmgDetail" :loading="dmgDetailSaving" :disabled="!dmgDetailChanged" />
                <Button label="Zamknij" icon="pi pi-times" severity="success" @click="dmgDetailModalVisible = false" />
            </template>
        </Dialog>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import axios from 'axios';
import logoImage from '@images/cnc-logo.png';
import defaultToolImage from '@images/cnc.png';

// PrimeVue Components
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Menu from 'primevue/menu';
import Tag from 'primevue/tag';
import ProgressSpinner from 'primevue/progressspinner';
import Badge from 'primevue/badge';
import Chart from 'primevue/chart';

const API_URL = '/api';

// Props from Inertia
const props = defineProps({
    auth: {
        type: Object,
        default: () => ({
            user: { first_name: '', last_name: '', username: '', grupa: '' }
        })
    },
    urls: {
        type: Object,
        default: () => ({
            logout: '/logout/'
        })
    },
    infoProgram: {
        type: Object,
        default: () => ({})
    },
    pageSize: {
        type: Number,
        default: 50
    }
});

// Data
const currentView = ref('lista');
const tools = ref([]);
const kategorie = ref([]);
const machines = ref([]);
const usagesInUse = ref([]);
const isLoadingTools = ref(true);

const selectedKategoriaId = ref(null);
const selectedPodkategoriaId = ref(null);
const selectedTool = ref(null);
const searchInput = ref('');
const searchQuery = ref('');
let searchDebounceTimer = null;
watch(searchInput, (val) => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => { searchQuery.value = val; }, 250);
});

// Narzędzia w użyciu - wyszukiwanie i filtr
const inUseSearchQuery = ref('');
const selectedMaszynaFilter = ref(null);

// Historia użycia
const toolHistory = ref([]);
const isLoadingHistory = ref(false);
const showHistoryModal = ref(false);
const selectedToolForHistory = ref(null);

// Wykres
const showChartModal = ref(false);
const chartGroupBy = ref('maszyna');
const chartKey = ref(0);
const chartReady = ref(false);

const chartData = computed(() => {
    const counts = {};
    const source = usagesInUse.value;

    if (chartGroupBy.value === 'maszyna') {
        source.forEach(usage => {
            const name = usage.maszyna?.nazwa || 'Brak';
            counts[name] = (counts[name] || 0) + 1;
        });
    } else {
        source.forEach(usage => {
            const name = usage.pracownik ? `${usage.pracownik.nazwisko} ${usage.pracownik.imie}` : 'Brak';
            counts[name] = (counts[name] || 0) + 1;
        });
    }

    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const labels = sorted.map(e => e[0]);
    const values = sorted.map(e => e[1]);

    const colors = [
        '#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1',
        '#0dcaf0', '#fd7e14', '#20c997', '#d63384', '#6610f2',
        '#adb5bd', '#495057', '#e35d6a', '#3d8bfd', '#75b798'
    ];
    const bgColors = labels.map((_, i) => colors[i % colors.length]);

    return {
        labels,
        datasets: [{
            label: chartGroupBy.value === 'maszyna' ? 'Narzędzia na maszynę' : 'Narzędzia na pracownika',
            data: values,
            backgroundColor: bgColors,
            borderColor: '#212529',
            borderWidth: 1,
            barThickness: 22
        }]
    };
});

const chartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: '#343a40',
            titleColor: '#ffc107',
            bodyColor: '#dee2e6'
        }
    },
    scales: {
        x: {
            ticks: { color: '#adb5bd', stepSize: 1 },
            grid: { color: '#495057' }
        },
        y: {
            ticks: { color: '#dee2e6', font: { size: 13 }, padding: 8 },
            grid: { color: '#495057' },
            afterFit: (axis) => { axis.width = 180; }
        }
    }
};

const chartHeightPx = computed(() => {
    const count = chartData.value.labels.length;
    return Math.max(300, count * 35 + 40);
});

const chartContentHeight = computed(() => {
    // wysokość wykresu + kontrolki + padding
    return chartHeightPx.value + 100;
});

watch(chartGroupBy, () => {
    chartReady.value = false;
    showChartModal.value = false;
    nextTick(() => {
        showChartModal.value = true;
        nextTick(() => {
            chartKey.value++;
            chartReady.value = true;
        });
    });
});

const openChartModal = () => {
    chartReady.value = false;
    showChartModal.value = true;
    nextTick(() => {
        chartKey.value++;
        chartReady.value = true;
    });
};

// Uszkodzenia / Zużyte
const damagesList = ref([]);
const isLoadingDamages = isLoadingTools;
const dmgSearchQuery = ref('');
const regenSearchQuery = ref('');
const dmgPdfPreviewVisible = ref(false);
const dmgPdfPreviewUrl = ref('');
const dmgDetailModalVisible = ref(false);
const dmgDetailData = ref(null);
const dmgEditStracony = ref('');
const dmgEditUwagi = ref('');
const dmgDetailSaving = ref(false);

const dmgDetailChanged = computed(() => {
    if (!dmgDetailData.value) return false;
    const origStracony = dmgDetailData.value.stracony_czas || null;
    const origUwagi = dmgDetailData.value.opis_uszkodzenia || '';
    return (dmgEditStracony.value || null) !== origStracony || dmgEditUwagi.value !== origUwagi;
});

const openDmgDetailModal = (damage) => {
    dmgDetailData.value = damage;
    dmgEditStracony.value = damage.stracony_czas || null;
    dmgEditUwagi.value = damage.opis_uszkodzenia || '';
    dmgDetailModalVisible.value = true;
};

const saveDmgDetail = async () => {
    if (!dmgDetailData.value) return;

    // Cicha walidacja stracony_czas — jeśli niepoprawna wartość, cofnij do oryginału
    let straconyValue = dmgEditStracony.value;
    if (straconyValue !== null && straconyValue !== '' && (!Number.isInteger(straconyValue) || straconyValue < 0)) {
        dmgEditStracony.value = dmgDetailData.value.stracony_czas || null;
        return;
    }

    dmgDetailSaving.value = true;
    try {
        await axios.patch(`${API_URL}/uszkodzenia/${dmgDetailData.value.id}/`, {
            stracony_czas: straconyValue || null,
            opis_uszkodzenia: dmgEditUwagi.value || ''
        });
        dmgDetailData.value.stracony_czas = straconyValue || null;
        dmgDetailData.value.opis_uszkodzenia = dmgEditUwagi.value || '';
        dmgDetailModalVisible.value = false;
    } catch (err) {
        console.error('Błąd zapisu uszkodzenia:', err);
    } finally {
        dmgDetailSaving.value = false;
    }
};

const damagesUszkodzone = computed(() => {
    return damagesList.value.filter(d => d.stan_egzemplarza === 'Uszkodzone');
});

const damagesRegeneracja = computed(() => {
    return damagesList.value.filter(d => d.stan_egzemplarza === 'Uszkodzone do regeneracji');
});

const filteredDamagesUszkodzone = computed(() => {
    if (!dmgSearchQuery.value.trim()) return damagesUszkodzone.value;
    const query = dmgSearchQuery.value.toLowerCase().trim();
    return damagesUszkodzone.value.filter(d => {
        return [
            d.numer_karty || '',
            d.maszyna_uszkodzenia || '',
            d.nazwisko_zglaszajacego || formatDmgPracownik(d.ostatni_pracownik) || '',
            `${d.kategoria_narzedzia}: ${d.opis_narzedzia}`,
            d.numer_katalogowy || '',
            d.przyczyna_uszkodzenia || '',
            d.stracony_czas || '',
            d.opis_uszkodzenia || ''
        ].some(f => f.toLowerCase().includes(query));
    });
});

const filteredDamagesRegeneracja = computed(() => {
    if (!regenSearchQuery.value.trim()) return damagesRegeneracja.value;
    const query = regenSearchQuery.value.toLowerCase().trim();
    return damagesRegeneracja.value.filter(d => {
        return [
            d.numer_karty || '',
            d.maszyna_uszkodzenia || '',
            formatDmgPracownik(d.ostatni_pracownik) || '',
            `${d.kategoria_narzedzia}: ${d.opis_narzedzia}`,
            d.numer_katalogowy || '',
            d.ostatnia_lokalizacja || '',
            d.opis_uszkodzenia || ''
        ].some(f => f.toLowerCase().includes(query));
    });
});

const formatDmgPracownik = (pracownik) => {
    if (!pracownik) return '-';
    return `${pracownik.nazwisko} ${pracownik.imie}`;
};

const openDmgPdfSingle = async (damage) => {
    try {
        const response = await axios.get(`${API_URL}/uszkodzenia/${damage.id}/pdf/`, {
            responseType: 'blob'
        });
        if (dmgPdfPreviewUrl.value) {
            window.URL.revokeObjectURL(dmgPdfPreviewUrl.value);
        }
        dmgPdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        dmgPdfPreviewVisible.value = true;
    } catch (error) {
        console.error('Błąd generowania PDF:', error);
        alert('Błąd podczas generowania PDF');
    }
};

const openDmgPdfList = async (typ) => {
    const items = typ === 'uszkodzone' ? filteredDamagesUszkodzone.value : filteredDamagesRegeneracja.value;
    const ids = items.map(d => d.id);
    if (ids.length === 0) {
        alert('Brak elementów do wydruku.');
        return;
    }
    try {
        const response = await axios.post(`${API_URL}/uszkodzenia/pdf_lista/`, { ids, typ }, {
            responseType: 'blob'
        });
        if (dmgPdfPreviewUrl.value) {
            window.URL.revokeObjectURL(dmgPdfPreviewUrl.value);
        }
        dmgPdfPreviewUrl.value = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        dmgPdfPreviewVisible.value = true;
    } catch (error) {
        console.error('Błąd generowania zbiorczego PDF:', error);
        alert('Błąd podczas generowania zbiorczego PDF');
    }
};

const closeDmgPdfPreview = () => {
    dmgPdfPreviewVisible.value = false;
    if (dmgPdfPreviewUrl.value) {
        window.URL.revokeObjectURL(dmgPdfPreviewUrl.value);
        dmgPdfPreviewUrl.value = '';
    }
};

// Wykres uszkodzeń/zużytych
const showDmgChartModal = ref(false);
const dmgChartType = ref('uszkodzone');
const dmgChartGroupBy = ref('maszyna');
const dmgChartKey = ref(0);
const dmgChartReady = ref(false);

const dmgChartData = computed(() => {
    const counts = {};
    const source = dmgChartType.value === 'uszkodzone' ? filteredDamagesUszkodzone.value : filteredDamagesRegeneracja.value;

    source.forEach(d => {
        let name;
        if (dmgChartGroupBy.value === 'maszyna') {
            name = d.maszyna_uszkodzenia || 'Brak';
        } else {
            if (dmgChartType.value === 'uszkodzone') {
                name = d.nazwisko_zglaszajacego || formatDmgPracownik(d.ostatni_pracownik);
            } else {
                name = formatDmgPracownik(d.ostatni_pracownik);
            }
        }
        counts[name] = (counts[name] || 0) + 1;
    });

    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const labels = sorted.map(e => e[0]);
    const values = sorted.map(e => e[1]);

    const colors = [
        '#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1',
        '#0dcaf0', '#fd7e14', '#20c997', '#d63384', '#6610f2',
        '#adb5bd', '#495057', '#e35d6a', '#3d8bfd', '#75b798'
    ];
    const bgColors = labels.map((_, i) => colors[i % colors.length]);

    return {
        labels,
        datasets: [{
            label: dmgChartGroupBy.value === 'maszyna' ? 'Wg maszyny' : (dmgChartType.value === 'uszkodzone' ? 'Wg zgłaszającego' : 'Wg użytkownika'),
            data: values,
            backgroundColor: bgColors,
            borderColor: '#212529',
            borderWidth: 1,
            barThickness: 22
        }]
    };
});

const dmgChartHeightPx = computed(() => {
    const count = dmgChartData.value.labels.length;
    return Math.max(300, count * 35 + 40);
});

const dmgChartContentHeight = computed(() => {
    return dmgChartHeightPx.value + 100;
});

watch(dmgChartGroupBy, () => {
    dmgChartReady.value = false;
    showDmgChartModal.value = false;
    nextTick(() => {
        showDmgChartModal.value = true;
        nextTick(() => {
            dmgChartKey.value++;
            dmgChartReady.value = true;
        });
    });
});

const openDmgChartModal = (typ) => {
    dmgChartType.value = typ;
    dmgChartReady.value = false;
    showDmgChartModal.value = true;
    nextTick(() => {
        dmgChartKey.value++;
        dmgChartReady.value = true;
    });
};

// Modals
const aboutModalVisible = ref(false);
const previewModalVisible = ref(false);
const previewTool = ref(null);
const showUsageModal = ref(false);
const selectedToolForUsage = ref(null);

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

const filteredPodkategorie = computed(() => {
    if (!selectedKategoriaId.value) return [];
    const kategoria = kategorie.value.find(k => k.id === selectedKategoriaId.value);
    if (!kategoria) return [];
    return kategoria.podkategorie || [];
});

// Narzędzia w użyciu dla wybranego typu narzędzia (modal)
const usagesForSelectedTool = computed(() => {
    if (!selectedToolForUsage.value) return [];
    return usagesInUse.value.filter(usage =>
        usage.egzemplarz?.narzedzie_typ?.id === selectedToolForUsage.value.id
    );
});

// Filtrowane narzędzia w użyciu
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
            const maszynaTekst = (usage.maszyna?.nazwa || '').toLowerCase();
            const pracownikTekst = usage.pracownik ? `${usage.pracownik.nazwisko || ''} ${usage.pracownik.imie || ''}`.toLowerCase() : '';
            const dataTekst = (usage.data_wydania || '').toLowerCase();
            const oznaczenieTekst = (usage.egzemplarz?.oznaczenie || '').toLowerCase();
            return narzedzieTekst.includes(query) || maszynaTekst.includes(query) || pracownikTekst.includes(query) || dataTekst.includes(query) || oznaczenieTekst.includes(query);
        });
    }

    return filtered;
});

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
const toggleUserMenu = (event) => { userMenu.value.toggle(event); };

// Menu Miejsca
const miejscaMenu = ref(null);
const miejscaMenuItems = ref([
    { label: 'Lista narzędzi', icon: 'pi pi-list', command: () => { currentView.value = 'lista'; } },
    { label: 'Narzędzia w użyciu', icon: 'pi pi-wrench', command: () => { currentView.value = 'w_uzyciu'; } },
    { separator: true },
    { label: 'Uszkodzone elementy', icon: 'pi pi-exclamation-triangle', command: () => { currentView.value = 'uszkodzone'; } },
    { label: 'Zużyte', icon: 'pi pi-refresh', command: () => { currentView.value = 'zuzyte'; } },
    { separator: true },
    { label: 'Lista realizacji', icon: 'pi pi-box', command: () => { window.location.href = props.urls.realizacja; } }
]);
const toggleMiejscaMenu = (event) => { miejscaMenu.value.toggle(event); };

const openHistoryModal = async (tool) => {
    selectedToolForHistory.value = tool;
    showHistoryModal.value = true;
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

const getStanSeverity = (stan) => {
    const map = {
        'nowe': 'success',
        'uzywane': 'info',
        'uszkodzone': 'danger',
        'uszkodzone_regeneracja': 'warning'
    };
    return map[stan] || 'secondary';
};

const openUsageModal = (tool) => {
    if (tool.ilosc_w_uzyciu > 0) {
        selectedToolForUsage.value = tool;
        showUsageModal.value = true;
    }
};

const formatMinutesToHours = (minutes) => {
    if (!minutes || minutes <= 0) return '-';
    return (minutes / 60).toFixed(2).replace('.', ',').replace(/0+$/, '').replace(/,$/, '');
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
        return `${year}-${month}-${day} <span style="color: #6c757d;">[${hours}:${minutes}]</span>`;
    } catch (e) {
        console.error("Błąd formatowania daty:", dateString, e);
        return 'Błąd daty';
    }
};

const openPreviewModal = (tool) => {
    previewTool.value = tool;
    previewModalVisible.value = true;
};

const rowClass = (data) => {
    return selectedTool.value && selectedTool.value.id === data.id ? 'selected-row' : '';
};

const onKategoriaChange = () => {
    selectedPodkategoriaId.value = null;
};

const onToolSelect = () => {};
const onToolUnselect = () => {};

const fetchInitialData = async () => {
    try {
        const [toolsRes, categoriesRes, usagesRes, machinesRes, damagesRes] = await Promise.all([
            axios.get(`${API_URL}/narzedzia/`),
            axios.get(`${API_URL}/kategorie/`),
            axios.get(`${API_URL}/historia/?w_uzyciu=true`),
            axios.get(`${API_URL}/maszyny/`),
            axios.get(`${API_URL}/uszkodzenia/`)
        ]);

        tools.value = toolsRes.data.results || toolsRes.data;
        kategorie.value = categoriesRes.data;
        usagesInUse.value = usagesRes.data.results || usagesRes.data;
        machines.value = machinesRes.data.results || machinesRes.data;
        damagesList.value = damagesRes.data.results || damagesRes.data;
    } catch (error) {
        console.error("Błąd ładowania danych:", error.response?.data || error.message);
    } finally {
        isLoadingTools.value = false;
    }
};

onMounted(() => {
    fetchInitialData();
});
</script>

<style scoped>
/* === CIEMNY MOTYW - ZMIENNE === */
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
    gap: 10px;
    align-items: center;
}

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

.btn.btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    background-color: #0d6efd;
    color: white;
    border: 1px solid #0d6efd;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: background-color 0.2s;
}

.btn.btn-primary:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
}

.btn-preview {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #17a2b8;
    background-color: #17a2b8;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-preview:hover {
    background-color: #138496;
    border-color: #117a8b;
}

.btn-history {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid #6f42c1;
    background-color: #6f42c1;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-history:hover {
    background-color: #5a32a3;
    border-color: #4e2d8e;
}

.loading-spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
}

.empty-state {
    text-align: center;
    padding: 20px;
    color: var(--dark-text-muted);
}

.in-use-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 0 12px 0;
}

.filter-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-row label {
    white-space: nowrap;
    color: var(--dark-text-secondary);
    font-size: 14px;
}

.btn-chart {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    padding: 0;
    border-radius: 4px;
    font-size: 1rem;
    border: 1px solid #198754;
    background-color: #198754;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
}
.btn-chart:hover {
    background-color: #157347;
    border-color: #146c43;
}

.chart-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}

.chart-controls label {
    color: #adb5bd;
    font-size: 14px;
    white-space: nowrap;
}

.chart-select {
    width: 180px;
    padding: 6px 32px 6px 12px;
    font-size: 14px;
    color: #dee2e6;
    background-color: #343a40;
    border: 1px solid #495057;
    border-radius: 4px;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23adb5bd' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 8px center;
    background-size: 16px 12px;
}

.chart-scroll-wrapper {
    border-radius: 6px;
    background-color: #1a1e23;
}

.chart-container {
    background-color: #1a1e23;
    padding: 16px;
    min-height: 300px;
}

.chart-container .p-chart {
    height: 100% !important;
}

.preview-content {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background-color: #1f2937;
    border-radius: 6px;
}

.preview-image {
    max-width: 100%;
    max-height: 400px;
    object-fit: contain;
    border-radius: 4px;
}

/* === GŁÓWNA ZAWARTOŚĆ === */
.magazyn-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 24px 15px 24px;
    gap: 0;
    min-height: 0;
    overflow: hidden;
}

/* === PANEL NARZĘDZI === */
.tools-panel {
    flex: 1;
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

/* === TABELE PRIMEVUE === */
:deep(.p-datatable) {
    font-size: 0.9rem;
    background: transparent;
}

:deep(.p-datatable .p-datatable-thead > tr > th) {
    background: linear-gradient(to bottom, #4a5258, #3d444d) !important;
    color: #fff !important;
    height: 50px;
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

:deep(.p-datatable-scrollable .p-datatable-thead) {
    position: sticky;
    top: 0;
    z-index: 1;
}

/* === O PROGRAMIE === */
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

/* === MINIATUROWY BUTTON W KOLUMNIE "W UŻYCIU" === */
.usage-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    height: 24px;
    padding: 2px 8px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #dee2e6;
    background-color: #495057;
    border: 1px solid #6c757d;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.usage-btn:hover {
    background-color: #5a6268;
    border-color: #adb5bd;
    color: #fff;
}

/* === MODAL NARZĘDZIA W UŻYCIU === */
:deep(.usage-modal .p-dialog-header) {
    background: linear-gradient(to bottom, #3d444d, #343a40);
    color: #ffc107;
    border-bottom: 1px solid #495057;
}

:deep(.usage-modal .p-dialog-content) {
    background-color: #212529;
    padding: 16px;
}

:deep(.usage-modal .p-dialog-footer) {
    background-color: #2d3238;
    border-top: 1px solid #495057;
}

/* === UTILITY === */
.text-muted { color: #6c757d; }
.zero-value { color: #6c757d !important; }

/* === USZKODZENIA — numery kart === */
.karta-numer-dmg {
    color: #ffc107;
}

.karta-numer-regen {
    color: #cd853f;
}

/* === BUTTON PDF w nagłówku panelu === */
.btn-pdf-header {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background-color: #6f42c1;
    border: 1px solid #6f42c1;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease;
    font-size: 1rem;
}

.btn-pdf-header:hover {
    background-color: #5a32a3;
    border-color: #5a32a3;
}

/* === BUTTON PDF w wierszu tabeli === */
.btn-pdf-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background-color: #6f42c1;
    border: 1px solid #6f42c1;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease;
    font-size: 0.85rem;
}

.btn-pdf-row:hover {
    background-color: #5a32a3;
    border-color: #5a32a3;
}

.stracony-czas-value {
    font-weight: 700;
    color: #e89a3c;
}

.stracony-czas-empty {
    color: #e53935;
}

.stracony-czas-unit {
    color: #e89a3c;
    font-size: 0.8rem;
    font-weight: 400;
}

.btn-details-row {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background-color: #0d6efd;
    border: 1px solid #0d6efd;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.15s ease;
    font-size: 0.85rem;
    margin-right: 4px;
}

.btn-details-row:hover {
    background-color: #0b5ed7;
    border-color: #0b5ed7;
}

/* === SZCZEGÓŁY USZKODZENIA === */
.dmg-detail-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.dmg-detail-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.dmg-detail-label {
    font-weight: 600;
    min-width: 195px;
    color: #adb5bd;
}

.dmg-detail-value {
    flex: 1;
    color: #e0e0e0;
}

.dmg-edit-input {
    width: 100%;
    background: #2b3035;
    border: 1px solid #495057;
    border-radius: 4px;
    color: #e0e0e0;
    padding: 6px 10px;
    font-size: 0.9rem;
    font-family: inherit;
    transition: border-color 0.15s ease;
}

.dmg-edit-input:focus {
    outline: none;
    border-color: #4dabf7;
}

.dmg-edit-input-short {
    max-width: 200px;
}

.dmg-edit-textarea {
    resize: vertical;
    min-height: 60px;
}

.dmg-detail-value-inline {
    display: flex;
    align-items: center;
}

.dmg-edit-hint {
    margin-left: 15px;
    color: #888;
    font-size: 0.85rem;
    white-space: nowrap;
}

/* === PODGLĄD PDF === */
.pdf-preview-container {
    width: 100%;
    height: 70vh;
    min-height: 500px;
    background-color: #1a1d21;
}

.pdf-iframe {
    width: 100%;
    height: 100%;
    border: none;
}

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--dark-bg-primary); }
::-webkit-scrollbar-thumb { background: var(--dark-border); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #4d555d; }
</style>

<!-- Style dla modali PrimeVue - CIEMNY MOTYW -->
<style>
.p-dialog-mask { background-color: rgba(0, 0, 0, 0.6) !important; backdrop-filter: blur(2px); }
.p-dialog { background: #2d3238 !important; border: 1px solid #495057 !important; border-radius: 8px !important; color: #dee2e6 !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important; overflow: hidden; }
.p-dialog .p-dialog-header { background: linear-gradient(to bottom, #3d444d, #343a40) !important; border-bottom: 1px solid #495057 !important; color: #fff !important; padding: 16px 20px !important; }
.p-dialog .p-dialog-header .p-dialog-title { color: #ffc107 !important; font-weight: 600 !important; font-size: 1.1rem !important; }
.p-dialog .p-dialog-header-icon { background: transparent !important; border: none !important; color: #adb5bd !important; width: 32px !important; height: 32px !important; border-radius: 4px !important; transition: all 0.15s ease !important; }
.p-dialog .p-dialog-header-icon:hover { background: rgba(255, 255, 255, 0.1) !important; color: #fff !important; }
.p-dialog .p-dialog-header-icon:focus { box-shadow: none !important; }
.p-dialog .p-dialog-content { background: #2d3238 !important; color: #dee2e6 !important; padding: 20px !important; }
.p-dialog .p-dialog-footer { background: linear-gradient(to bottom, #343a40, #2d3238) !important; border-top: 1px solid #495057 !important; padding: 12px 20px !important; display: flex; justify-content: flex-end; gap: 8px; }

.p-dialog .about-content { text-align: center; }
.p-dialog .about-header h4 { color: #ffc107 !important; margin: 10px 0 5px 0; }
.p-dialog .about-header p { color: #adb5bd !important; }
.p-dialog .about-table { margin-top: 20px; }
.p-dialog .about-table td { padding: 8px 0; color: #dee2e6; }
.p-dialog .about-table .label { color: #adb5bd !important; }
.p-dialog .about-table a { color: #0d6efd !important; text-decoration: none; }
.p-dialog .about-table a:hover { color: #3d8bfd !important; text-decoration: underline; }

.about-footer { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.about-footer .copyright { color: #6c757d !important; font-size: 0.85rem; }

.p-dialog .p-button.btn-modal-secondary { background-color: #6c757d !important; border-color: #6c757d !important; color: #fff !important; padding: 8px 16px !important; font-weight: 500 !important; border-radius: 4px !important; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important; }
.p-dialog .p-button.btn-modal-secondary:hover { background-color: #5c636a !important; border-color: #565e64 !important; }

/* === MENU USER === */
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

/* === MENU MIEJSCA === */
#miejsca_menu {
    min-width: 180px !important;
    background: #2d3238 !important;
    border: 1px solid #495057 !important;
    border-radius: 6px !important;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.5) !important;
    padding: 6px 0 !important;
}

#miejsca_menu_list {
    padding: 0 !important;
    margin: 0 !important;
    list-style: none !important;
}

#miejsca_menu_list li {
    margin: 0 !important;
    padding: 0 !important;
}

#miejsca_menu_list li > div {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    transition: background-color 0.15s !important;
}

#miejsca_menu_list li > div:hover {
    background-color: #3d444d !important;
}

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

#miejsca_menu_list li > div span[class*="icon"],
#miejsca_menu_list li > div i,
#miejsca_menu_list li > div .pi {
    color: #adb5bd !important;
    font-size: 1rem !important;
}

#miejsca_menu_list li > div span:not([class*="icon"]):not(.pi) {
    color: #dee2e6 !important;
    font-size: 14px !important;
}

/* === MODAL WYKRES === */
</style>

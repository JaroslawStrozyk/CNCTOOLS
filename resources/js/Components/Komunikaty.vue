<template>
    <Toast position="top-right" />
    <Dialog
        :visible="stan.widoczny"
        @update:visible="v => { if (!v) zamknijModal(false); }"
        :header="stan.naglowek"
        :modal="true"
        :closable="true"
        :style="{ width: '450px' }"
    >
        <div class="komunikat-tresc">
            <i :class="stan.rodzaj === 'potwierdzenie' ? 'pi pi-question-circle' : 'pi pi-exclamation-triangle'" class="komunikat-ikona"></i>
            <span>{{ stan.tresc }}</span>
        </div>
        <template #footer>
            <Button
                v-if="stan.rodzaj === 'potwierdzenie'"
                label="Anuluj"
                icon="pi pi-times"
                class="p-button-text"
                @click="zamknijModal(false)"
            />
            <Button
                :label="stan.przyciskTak"
                icon="pi pi-check"
                autofocus
                @click="zamknijModal(true)"
            />
        </template>
    </Dialog>
</template>

<script setup>
import Toast from 'primevue/toast';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import { stanModala as stan, zamknijModal } from '../komunikaty.js';
</script>

<style scoped>
.komunikat-tresc {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    white-space: pre-line;
}

.komunikat-ikona {
    font-size: 1.6rem;
    color: #f0ad4e;
    flex-shrink: 0;
}
</style>

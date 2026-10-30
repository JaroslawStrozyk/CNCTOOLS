// Wspólne komunikaty aplikacji — zamiennik alert()/confirm().
// - blad(): Toast błędu bez automatycznego znikania (błędy po akcjach na serwerze)
// - ostrzezenie(): modal z przyciskiem OK (warunek blokujący akcję)
// - potwierdz(): modal Tak/Nie, zwraca Promise<boolean>
// Komponent wyświetlający: Components/Komunikaty.vue (montowany raz w app.js).
import { reactive } from 'vue';
import ToastEventBus from 'primevue/toasteventbus';

export const stanModala = reactive({
    widoczny: false,
    rodzaj: 'ostrzezenie',  // 'ostrzezenie' | 'potwierdzenie'
    naglowek: '',
    tresc: '',
    przyciskTak: 'Tak',
    rozwiaz: null,
});

export const blad = (tresc, naglowek = 'Błąd') => {
    ToastEventBus.emit('add', { severity: 'error', summary: naglowek, detail: tresc });
};

export const sukces = (tresc, naglowek = 'Gotowe') => {
    ToastEventBus.emit('add', { severity: 'success', summary: naglowek, detail: tresc, life: 3000 });
};

const otworz = (rodzaj, tresc, naglowek, przyciskTak) => new Promise((resolve) => {
    // Poprzedni, niezamknięty modal traktujemy jako anulowany
    if (stanModala.rozwiaz) stanModala.rozwiaz(false);
    Object.assign(stanModala, { widoczny: true, rodzaj, tresc, naglowek, przyciskTak, rozwiaz: resolve });
});

export const ostrzezenie = (tresc, naglowek = 'Uwaga') =>
    otworz('ostrzezenie', tresc, naglowek, 'OK');

export const potwierdz = (tresc, { naglowek = 'Potwierdzenie', przyciskTak = 'Tak' } = {}) =>
    otworz('potwierdzenie', tresc, naglowek, przyciskTak);

export const zamknijModal = (wynik) => {
    const rozwiaz = stanModala.rozwiaz;
    stanModala.rozwiaz = null;
    stanModala.widoczny = false;
    if (rozwiaz) rozwiaz(wynik);
};

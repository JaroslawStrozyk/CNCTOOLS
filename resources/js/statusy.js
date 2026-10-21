// Jedno źródło etykiet i kolorów statusów we froncie.
// Zamówienia są źródłem prawdy: status zapotrzebowania przychodzi z backendu jako
// `status_efektywny` + `status_display` (liczone ze statusów powiązanych zamówień,
// TOOLS/statusy.py) — tu są tylko kolory do jego kodów.

// --- Zamówienie (Zamowienie.status) ---
export const ZAMOWIENIE_STATUS_ETYKIETY = {
    draft: 'Wersja robocza',
    pending_approval: 'Oczekuje na zatwierdzenie',
    verified: 'Zatwierdzone',
    sent: 'Wysłane',
    partially_received: 'Częściowo odebrane',
    completed: 'Zrealizowane',
};

const ZAMOWIENIE_STATUS_SEVERITY = {
    draft: 'secondary',
    pending_approval: 'warning',
    verified: 'info',
    sent: 'primary',
    partially_received: 'warning',
    completed: 'success',
};

export const etykietaStatusuZamowienia = (status) => ZAMOWIENIE_STATUS_ETYKIETY[status] || status;
export const severityStatusuZamowienia = (status) => ZAMOWIENIE_STATUS_SEVERITY[status] || 'secondary';
// 'partially_received' — Tag w kolorze p-button-warning (pomarańczowy); klasa w dark-theme.css ma !important
export const klasaStatusuZamowienia = (status) => (status === 'partially_received' ? 'tag-status-orange' : '');

// --- Zapotrzebowanie (kod efektywny z backendu) ---
const ZAPOTRZEBOWANIE_STATUS_SEVERITY = {
    draft: 'secondary',
    submitted: 'warning',
    approved: 'success',
    w_przygotowaniu: 'info',
    wyslane: 'info',
    ordered: 'info',
    czesciowo_odebrane: 'warning',
    completed: 'success',
    cancelled: 'danger',
};

export const severityStatusuZapotrzebowania = (kod) => ZAPOTRZEBOWANIE_STATUS_SEVERITY[kod] || 'secondary';

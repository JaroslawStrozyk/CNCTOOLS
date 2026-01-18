import '../css/app.css';
import { createApp, h } from 'vue';
import { createInertiaApp } from '@inertiajs/vue3';
import PrimeVue from 'primevue/config';
import axios from 'axios';

// Funkcja do pobierania aktualnego CSRF tokena
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

// Ustaw CSRF dla Inertia - dynamicznie przy każdym requeście
document.addEventListener('inertia:before', (event) => {
    const token = getCsrfToken();
    if (token && event.detail.visit.method !== 'get') {
        event.detail.visit.headers = {
            ...event.detail.visit.headers,
            'X-CSRFToken': token,
        };
    }
});

// Ustaw CSRF dla axios
axios.interceptors.request.use(config => {
    const token = getCsrfToken();
    if (token) {
        config.headers['X-CSRFToken'] = token;
    }
    return config;
});

createInertiaApp({
    resolve: name => {
        const pages = import.meta.glob('./Pages/**/*.vue', { eager: true });
        return pages[`./Pages/${name}.vue`];
    },
    setup({ el, App, props, plugin }) {
        createApp({ render: () => h(App, props) })
            .use(plugin)
            .use(PrimeVue)
            .mount(el);
    },
});
/**
 * Panel Odpady - Frontend
 * Zarządzanie uszkodzonymi narzędziami CNC
 */

const { createApp } = Vue;
const API_URL = '/api';

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            damages: [],
            isLoading: false,
        };
    },

    computed: {
        // Filtruj uszkodzone (stan: uszkodzone)
        damagesUszkodzone() {
            return this.damages.filter(d => d.stan_egzemplarza === 'Uszkodzone');
        },

        // Filtruj uszkodzone do regeneracji (stan: uszkodzone_regeneracja)
        damagesRegeneracja() {
            return this.damages.filter(d => d.stan_egzemplarza === 'Uszkodzone do regeneracji');
        }
    },

    async mounted() {
        await this.fetchDamages();
    },

    methods: {
        async fetchDamages() {
            this.isLoading = true;
            try {
                const response = await axios.get(`${API_URL}/uszkodzenia/`);
                this.damages = response.data.results || response.data;
            } catch (error) {
                console.error('Błąd pobierania uszkodzeń:', error);
            } finally {
                this.isLoading = false;
            }
        },

        formatCustomDate(dateString) {
            if (!dateString) return '-';
            const date = new Date(dateString);
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${day}.${month}.${year} ${hours}:${minutes}`;
        }
    }
}).mount('#app');
<template>
    <div class="login-container" :style="{ backgroundImage: `url(${tlo})` }">
        <div class="login-card">
            <!-- Admin button -->
            <a href="/admin/" class="admin-btn" title="Panel administracyjny">
                <i class="pi pi-cog"></i>
            </a>

            <div class="login-header">
                <img :src="logo" alt="CNC Logo" class="logo" />
                <h2>CNC Tools</h2>
                <p>System zarządzania narzędziami</p>
            </div>

            <!-- Card reading indicator -->
            <div v-if="isCardReading" class="card-reading-indicator">
                <i class="pi pi-id-card card-icon"></i>
                <span>Odczytywanie karty...</span>
            </div>

            <!-- Card login message -->
            <Message v-if="cardMessage" :severity="cardMessageType" :closable="false" class="card-message">
                {{ cardMessage }}
            </Message>

            <form @submit.prevent="submit">
                <div class="field">
                    <label for="username">Nazwa użytkownika</label>
                    <InputText
                        id="username"
                        v-model="form.username"
                        :class="{ 'p-invalid': form.errors.username }"
                        autofocus
                    />
                    <small v-if="form.errors.username" class="p-error">
                        {{ form.errors.username }}
                    </small>
                </div>

                <div class="field">
                    <label for="password">Hasło</label>
                    <Password
                        id="password"
                        v-model="form.password"
                        :feedback="false"
                        toggleMask
                        :class="{ 'p-invalid': form.errors.password }"
                    />
                    <small v-if="form.errors.password" class="p-error">
                        {{ form.errors.password }}
                    </small>
                </div>

                <Message v-if="form.errors.error" severity="error" :closable="false">
                    {{ form.errors.error }}
                </Message>

                <Button
                    type="submit"
                    label="Zaloguj"
                    :loading="form.processing"
                    class="w-full"
                />
            </form>

            <!-- Card login hint -->
            <div class="card-hint" :class="{ 'connected': wsConnected }">
                <i class="pi pi-id-card"></i>
                <span v-if="wsConnected">przyłóż kartę do czytnika</span>
                <span v-else>lub przyłóż kartę do czytnika</span>
                <span v-if="wsConnected" class="ws-status" title="Połączono z czytnikiem">●</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useForm } from '@inertiajs/vue3';
import axios from 'axios';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';
import Message from 'primevue/message';
import logo from '@images/cnc-logo.png';
import tlo from '@images/tlo.png';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

const props = defineProps({
    errors: {
        type: Object,
        default: () => ({})
    }
});

const form = useForm({
    username: '',
    password: '',
});

// Card reader state
const cardBuffer = ref('');
const cardTimeout = ref(null);
const isCardReading = ref(false);
const cardMessage = ref('');
const cardMessageType = ref('info');
const isCardProcessing = ref(false);
const lastKeyTime = ref(0);
const fastInputCount = ref(0);

// WebSocket state
const wsConnected = ref(false);
const wsReaderConnected = ref(false);
let ws = null;
let wsReconnectTimer = null;
const WS_URL = 'ws://localhost:2222';

// Card reader detection - HID readers act as keyboards
// Key insight: Card readers type VERY fast (<50ms between chars), humans can't type that fast
const handleCardInput = (event) => {
    const now = Date.now();
    const timeSinceLastKey = now - lastKeyTime.value;

    // Enter key = end of card read
    if (event.key === 'Enter') {
        if (cardBuffer.value.length === 10 && /^\d{10}$/.test(cardBuffer.value)) {
            event.preventDefault();
            event.stopPropagation();

            // Clear any text that got into input fields
            clearInputFields();

            loginByCard(cardBuffer.value);
        }
        resetCardState();
        return;
    }

    // Only process digits for card
    if (/^\d$/.test(event.key)) {
        // Detect fast input (card reader is < 50ms between chars)
        const isFastInput = timeSinceLastKey < 80;

        if (isFastInput || cardBuffer.value.length > 0) {
            fastInputCount.value++;
        }

        // If we detect fast input pattern, it's a card reader
        if (fastInputCount.value >= 2 || cardBuffer.value.length >= 2) {
            event.preventDefault();
            event.stopPropagation();

            // First time detecting card - clear any digits that got into inputs
            if (!isCardReading.value) {
                clearInputFields();
                // Also blur the active input to prevent further typing
                document.activeElement?.blur();
            }
            isCardReading.value = true;
        }

        // Clear previous timeout
        clearTimeout(cardTimeout.value);

        // First digit
        if (cardBuffer.value.length === 0) {
            lastKeyTime.value = now;
        }

        cardBuffer.value += event.key;
        lastKeyTime.value = now;

        // Reset if typing is too slow (human typing)
        cardTimeout.value = setTimeout(() => {
            resetCardState();
        }, 200);
    }
};

const resetCardState = () => {
    cardBuffer.value = '';
    isCardReading.value = false;
    fastInputCount.value = 0;
};

const clearInputFields = () => {
    // Clear username and password fields if card number got typed into them
    if (form.username && /^\d+$/.test(form.username)) {
        form.username = '';
    }
    if (form.password && /^\d+$/.test(form.password)) {
        form.password = '';
    }
};

const loginByCard = async (cardNumber) => {
    if (isCardProcessing.value) return;

    isCardProcessing.value = true;
    cardMessage.value = '';

    try {
        const response = await axios.post('/api/login-card/', {
            card_number: cardNumber
        });

        if (response.data.success) {
            cardMessageType.value = 'success';
            cardMessage.value = `Witaj, ${response.data.user.first_name}!`;

            // Redirect after short delay
            setTimeout(() => {
                window.location.href = response.data.redirect;
            }, 500);
        }
    } catch (error) {
        cardMessageType.value = 'error';
        cardMessage.value = error.response?.data?.error || 'Błąd logowania kartą';
        isCardProcessing.value = false;

        // Clear message after 5 seconds
        setTimeout(() => {
            cardMessage.value = '';
        }, 5000);
    }
};

// WebSocket connection
const connectWebSocket = () => {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('WebSocket connected to card reader daemon');
            wsConnected.value = true;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'status') {
                    wsReaderConnected.value = data.reader_connected;
                }
                else if (data.type === 'card') {
                    // Card received via WebSocket - login
                    console.log('Card received via WebSocket:', data.card_number);
                    loginByCard(data.card_number);
                }
            } catch (e) {
                console.error('WebSocket message parse error:', e);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            wsConnected.value = false;
            wsReaderConnected.value = false;

            // Reconnect after 3 seconds
            wsReconnectTimer = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
            // Silent error - daemon might not be running
            wsConnected.value = false;
        };

    } catch (e) {
        // WebSocket not supported or connection failed
        wsConnected.value = false;
    }
};

const disconnectWebSocket = () => {
    clearTimeout(wsReconnectTimer);
    if (ws) {
        ws.close();
        ws = null;
    }
};

onMounted(() => {
    // Keyboard fallback (when WebSocket daemon not running)
    window.addEventListener('keydown', handleCardInput, true);

    // Try WebSocket connection
    connectWebSocket();
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleCardInput, true);
    clearTimeout(cardTimeout.value);
    disconnectWebSocket();
});

const submit = () => {
    form.post('/login/', {
        onSuccess: () => {
            // Przekierowanie automatyczne
        },
    });
};
</script>

<style scoped>
.login-container {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    margin: 0;
    padding: 0;
    overflow: hidden;
}

.login-card {
    position: relative;
    background: rgba(31, 41, 55, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    width: 100%;
    max-width: 400px;
}

/* Admin button */
.admin-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(107, 114, 128, 0.3);
    border: 1px solid rgba(107, 114, 128, 0.4);
    border-radius: 6px;
    color: #6b7280;
    text-decoration: none;
    transition: all 0.2s ease;
    opacity: 0.6;
}

.admin-btn:hover {
    background: rgba(107, 114, 128, 0.5);
    border-color: rgba(156, 163, 175, 0.6);
    color: #9ca3af;
    opacity: 1;
}

.admin-btn i {
    font-size: 14px;
}

.login-header {
    text-align: center;
    margin-bottom: 30px;
}

.logo {
    width: 80px;
    height: 80px;
    margin-bottom: 20px;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
}

.login-header h2 {
    margin: 0 0 10px 0;
    color: #f9fafb;
    font-size: 28px;
}

.login-header p {
    margin: 0;
    color: #9ca3af;
    font-size: 14px;
}

.field {
    margin-bottom: 20px;
}

.field label {
    display: block;
    margin-bottom: 8px;
    color: #d1d5db;
    font-weight: 500;
}

/* Inputy */
.field :deep(.p-inputtext),
.field :deep(.p-password input) {
    width: 100%;
    height: 48px;
    font-size: 16px;
    padding: 0 14px;
    background-color: #374151 !important;
    border-color: #4b5563 !important;
    color: #f9fafb !important;
}

.field :deep(.p-inputtext:focus),
.field :deep(.p-password input:focus) {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2) !important;
}

.field :deep(.p-password) {
    width: 100%;
    position: relative;
}

/* Ikona oka (toggle password) */
.field :deep(.p-password .p-icon-field-right) {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
}

.field :deep(.p-password svg) {
    font-size: 18px;
    color: #9ca3af;
}

/* Button */
:deep(.p-button) {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border: none !important;
    transition: transform 0.2s, box-shadow 0.2s;
}

:deep(.p-button:hover) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

/* Message error */
:deep(.p-message) {
    margin-bottom: 16px;
    background-color: rgba(220, 38, 38, 0.15) !important;
    border-color: rgba(220, 38, 38, 0.3) !important;
}

:deep(.p-message .p-message-icon) {
    display: none !important;
}

.p-error {
    color: #f87171;
    font-size: 12px;
    display: block;
    margin-top: 4px;
}

/* Card reading indicator */
.card-reading-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 16px;
    margin-bottom: 20px;
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.4);
    border-radius: 8px;
    color: #93c5fd;
    animation: pulse 1.5s infinite;
}

.card-reading-indicator .card-icon {
    font-size: 24px;
    animation: cardScan 0.8s infinite alternate;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

@keyframes cardScan {
    0% { transform: scale(1); }
    100% { transform: scale(1.1); }
}

/* Card message */
.card-message {
    margin-bottom: 16px;
}

:deep(.card-message.p-message-success) {
    background-color: rgba(34, 197, 94, 0.15) !important;
    border-color: rgba(34, 197, 94, 0.3) !important;
}

:deep(.card-message.p-message-success .p-message-text) {
    color: #86efac !important;
}

/* Card hint */
.card-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    color: #6b7280;
    font-size: 13px;
}

.card-hint i {
    font-size: 18px;
    color: #9ca3af;
}

/* WebSocket connected state */
.card-hint.connected {
    color: #86efac;
}

.card-hint.connected i {
    color: #86efac;
}

.ws-status {
    color: #22c55e;
    font-size: 10px;
    animation: blink 2s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
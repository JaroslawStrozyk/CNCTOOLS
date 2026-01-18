<template>
    <div style="padding: 50px; text-align: center;">
        <h1>🎉 Inertia.js działa!</h1>
        <p>Message from backend: {{ message }}</p>
        <p>Zalogowany jako: <strong>{{ $page.props.auth?.user?.username || 'Guest' }}</strong></p>

        <div style="margin-top: 30px;">
            <Button label="Test PrimeVue" severity="success" class="mr-2" />
            <Button
                label="Wyloguj"
                severity="danger"
                icon="pi pi-sign-out"
                @click="logout"
            />
        </div>
    </div>
</template>

<script setup>
import Button from 'primevue/button';
import { router } from '@inertiajs/vue3';

defineProps({
    message: String
});

const logout = () => {
    router.visit('/logout/');
};
</script>

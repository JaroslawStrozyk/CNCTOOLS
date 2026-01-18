import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';

export default defineConfig(({ command }) => ({
    plugins: [vue()],
    root: resolve('./resources'),
    // Dev: '/' (Vite serwuje bezpośrednio), Build: '/static/dist/' (dla produkcji)
    base: command === 'serve' ? '/' : '/static/dist/',
    server: {
        host: '0.0.0.0',
        port: 5173,
        open: false,
        strictPort: true,
        origin: 'http://localhost:5173',  // Pełne URL-e do assetów w dev
        watch: {
            usePolling: true,
            disableGlobbing: false,
        },
        cors: true,
    },
    resolve: {
        extensions: ['.js', '.json', '.jsx', '.mjs', '.ts', '.tsx', '.vue'],
        alias: {
            '@': resolve('./resources/js'),
            '@images': resolve('./resources/images'),
            '@fonts': resolve('./resources/fonts'),
        },
    },
    build: {
        outDir: resolve('./static_dev/dist'),
        assetsDir: '',
        manifest: true,
        emptyOutDir: true,
        target: 'es2015',
        rollupOptions: {
            input: {
                main: resolve('./resources/js/app.js'),
            },
        },
    },
}));

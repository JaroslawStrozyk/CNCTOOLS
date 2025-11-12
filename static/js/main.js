// static/js/main.js

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Globalne konfiguracje Axios
axios.defaults.headers.common['X-CSRFToken'] = getCookie('csrftoken');
axios.defaults.headers.get['Cache-Control'] = 'no-cache';
axios.defaults.headers.get['Pragma'] = 'no-cache';
axios.defaults.headers.get['Expires'] = '0';

// Inicjalizacja aplikacji Vue
const { createApp } = Vue;

createApp({
    data() {
        return {
            tools: [],
            machines: [],
            usagesInUse: [],
            categories: [],
            selectedCategory: null,
            activeTab: 'inUse',
            selectedToolForHistory: null,
            toolHistory: [],
            isLoadingHistory: false,
            // Dane dla modali
            selectedTool: {},
            issueData: { tool_id: null, machine_id: null },
            error: '',
            issueModalInstance: null,
            returnModalInstance: null,
            usageIdToReturn: null,
            toolModalInstance: null,
            currentTool: {},
            isEditMode: false,
            // Nowe właściwości do zarządzania kategoriami
            addCategoryModalInstance: null,
            editCategoryModalInstance: null,
            newCategoryName: '',
            categoryToEdit: {},
        }
    },
    computed: {
        filteredTools() {
            if (!this.selectedCategory) {
                return this.tools;
            }
            return this.tools.filter(tool => tool.category.id === this.selectedCategory);
        }
    },
    methods: {
        // --- METODY POMOCNICZE ---
        formatCustomDate(isoDate) {
            if (!isoDate) return '';
            const date = new Date(isoDate);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day} [${hours}:${minutes}]`;
        },
        async fetchData() {
            try {
                const [toolsRes, machinesRes, usagesRes, categoriesRes] = await Promise.all([
                    axios.get('/api/tools/'),
                    axios.get('/api/machines/'),
                    axios.get('/api/usages/?status=in_use'),
                    axios.get('/api/categories/'),
                ]);
                this.tools = toolsRes.data;
                this.machines = machinesRes.data;
                this.usagesInUse = usagesRes.data;
                this.categories = categoriesRes.data;
            } catch (error) {
                console.error("Błąd podczas pobierania danych:", error);
            }
        },
        async getToolHistory(tool) {
            this.selectedToolForHistory = tool;
            this.isLoadingHistory = true;
            this.toolHistory = [];
            try {
                const response = await axios.get(`/api/usages/?tool=${tool.id}`);
                this.toolHistory = response.data;
            } catch (error) {
                console.error(`Błąd podczas pobierania historii dla narzędzia ${tool.id}:`, error);
            } finally {
                this.isLoadingHistory = false;
                this.activeTab = 'history';
            }
        },

        // --- METODY OBSŁUGI NARZĘDZI ---
        showIssueModal(tool) {
            this.selectedTool = tool;
            this.issueData.tool_id = tool.id;
            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
            this.error = '';
            this.issueModalInstance.show();
        },
        async issueTool() {
            if (!this.issueData.machine_id) {
                this.error = "Wybierz maszynę.";
                return;
            }
            try {
                await axios.post('/api/usages/', this.issueData);
                this.issueModalInstance.hide();
                await this.fetchData();
            } catch (error) {
                this.error = error.response?.data?.error || "Wystąpił nieznany błąd.";
                console.error("Błąd przy wydawaniu narzędzia:", error);
            }
        },
        showReturnModal(usageId) {
            this.usageIdToReturn = usageId;
            this.returnModalInstance.show();
        },
        async confirmReturnTool() {
            try {
                await axios.patch(`/api/usages/${this.usageIdToReturn}/`, { return_date: new Date().toISOString() });
                await this.fetchData();
            } catch (error) {
                alert("Wystąpił błąd podczas zwracania narzędzia.");
                console.error("Błąd przy zwracaniu narzędzia:", error);
            } finally {
                this.returnModalInstance.hide();
                this.usageIdToReturn = null;
            }
        },
        openToolModal(tool = null) {
            if (tool) {
                this.isEditMode = true;
                this.currentTool = { ...tool, category_id: tool.category.id };
            } else {
                this.isEditMode = false;
                this.currentTool = {
                    category_id: this.categories.length > 0 ? this.categories[0].id : null,
                    description: '',
                    catalog_number: '',
                    quantity_new: 0,
                    quantity_used_available: 0
                };
            }
            this.toolModalInstance.show();
        },
        async saveTool() {
            try {
                if (this.isEditMode) {
                    await axios.patch(`/api/tools/${this.currentTool.id}/`, this.currentTool);
                } else {
                    await axios.post('/api/tools/', this.currentTool);
                }
                this.toolModalInstance.hide();
                await this.fetchData();
            } catch (error) {
                console.error("Błąd podczas zapisywania narzędzia:", error);
                alert("Wystąpił błąd. Sprawdź konsolę, aby uzyskać więcej informacji.");
            }
        },

        // --- METODY OBSŁUGI KATEGORII ---
        openAddCategoryModal() {
            this.newCategoryName = '';
            this.addCategoryModalInstance.show();
        },
        async saveNewCategory() {
            if (!this.newCategoryName.trim()) {
                alert("Nazwa kategorii nie może być pusta.");
                return;
            }
            try {
                await axios.post('/api/categories/', { name: this.newCategoryName });
                this.addCategoryModalInstance.hide();
                await this.fetchData();
            } catch (error) {
                console.error("Błąd podczas dodawania kategorii:", error);
                alert("Wystąpił błąd. Możliwe, że kategoria o tej nazwie już istnieje.");
            }
        },
        openEditCategoryModal() {
            this.categoryToEdit = {};
            this.editCategoryModalInstance.show();
        },
        startEditingCategory(category) {
            this.categoryToEdit = { ...category };
        },
        cancelEditingCategory() {
            this.categoryToEdit = {};
        },
        async updateCategory() {
            if (!this.categoryToEdit.name.trim()) {
                alert("Nazwa kategorii nie może być pusta.");
                return;
            }
            try {
                await axios.patch(`/api/categories/${this.categoryToEdit.id}/`, { name: this.categoryToEdit.name });
                this.categoryToEdit = {};
                await this.fetchData();
            } catch (error) {
                console.error("Błąd podczas aktualizacji kategorii:", error);
                alert("Wystąpił błąd podczas zapisu.");
            }
        },
        async deleteCategory(categoryId) {
            if (confirm('Czy na pewno chcesz usunąć tę kategorię?\n\nUsunięcie kategorii jest możliwe tylko wtedy, gdy nie są do niej przypisane żadne narzędzia.')) {
                try {
                    await axios.delete(`/api/categories/${categoryId}/`);
                    await this.fetchData();
                } catch (error) {
                    console.error("Błąd podczas usuwania kategorii:", error);
                    alert("Nie można usunąć kategorii, ponieważ istnieją do niej przypisane narzędzia.");
                }
            }
        }
    },
    mounted() {
        this.fetchData();
        // Inicjalizacja wszystkich instancji modali
        this.issueModalInstance = new bootstrap.Modal(this.$refs.issueModal);
        this.returnModalInstance = new bootstrap.Modal(this.$refs.returnModal);
        this.toolModalInstance = new bootstrap.Modal(this.$refs.toolModal);
        this.addCategoryModalInstance = new bootstrap.Modal(this.$refs.addCategoryModal);
        this.editCategoryModalInstance = new bootstrap.Modal(this.$refs.editCategoryModal);
    }
}).mount('#app');
















//// static/js/main.js
//
//function getCookie(name) {
//    let cookieValue = null;
//    if (document.cookie && document.cookie !== '') {
//        const cookies = document.cookie.split(';');
//        for (let i = 0; i < cookies.length; i++) {
//            const cookie = cookies[i].trim();
//            if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                break;
//            }
//        }
//    }
//    return cookieValue;
//}
//
//axios.defaults.headers.common['X-CSRFToken'] = getCookie('csrftoken');
//axios.defaults.headers.get['Cache-Control'] = 'no-cache';
//axios.defaults.headers.get['Pragma'] = 'no-cache';
//axios.defaults.headers.get['Expires'] = '0';
//
//const { createApp } = Vue;
//
//createApp({
//    data() {
//        return {
//            tools: [],
//            machines: [],
//            usagesInUse: [],
//            categories: [],
//            selectedCategory: null,
//            activeTab: 'inUse',
//            selectedToolForHistory: null,
//            toolHistory: [],
//            isLoadingHistory: false,
//            selectedTool: {},
//            issueData: { tool_id: null, machine_id: null },
//            error: '',
//            issueModalInstance: null,
//            returnModalInstance: null,
//            usageIdToReturn: null,
//            // Nowe właściwości
//            toolModalInstance: null,
//            categoryModalInstance: null,
//            currentTool: {},
//            isEditMode: false,
//            newCategoryName: '',
//        }
//    },
//    computed: {
//        filteredTools() {
//            if (!this.selectedCategory) return this.tools;
//            return this.tools.filter(tool => tool.category.id === this.selectedCategory);
//        }
//    },
//    methods: {
//        formatCustomDate(isoDate) {
//            if (!isoDate) return '';
//            const date = new Date(isoDate);
//            const year = date.getFullYear();
//            const month = String(date.getMonth() + 1).padStart(2, '0');
//            const day = String(date.getDate()).padStart(2, '0');
//            const hours = String(date.getHours()).padStart(2, '0');
//            const minutes = String(date.getMinutes()).padStart(2, '0');
//            return `${year}-${month}-${day} [${hours}:${minutes}]`;
//        },
//        async fetchData() {
//            try {
//                const [toolsRes, machinesRes, usagesRes, categoriesRes] = await Promise.all([
//                    axios.get('/api/tools/'),
//                    axios.get('/api/machines/'),
//                    axios.get('/api/usages/?status=in_use'),
//                    axios.get('/api/categories/'),
//                ]);
//                this.tools = toolsRes.data;
//                this.machines = machinesRes.data;
//                this.usagesInUse = usagesRes.data;
//                this.categories = categoriesRes.data;
//            } catch (error) {
//                console.error("Błąd podczas pobierania danych:", error);
//            }
//        },
//        async getToolHistory(tool) {
//            this.selectedToolForHistory = tool;
//            this.isLoadingHistory = true;
//            this.toolHistory = [];
//            try {
//                const response = await axios.get(`/api/usages/?tool=${tool.id}`);
//                this.toolHistory = response.data;
//            } catch (error) {
//                console.error(`Błąd podczas pobierania historii dla narzędzia ${tool.id}:`, error);
//            } finally {
//                this.isLoadingHistory = false;
//                this.activeTab = 'history';
//            }
//        },
//        showIssueModal(tool) {
//            this.selectedTool = tool;
//            this.issueData.tool_id = tool.id;
//            this.issueData.machine_id = this.machines.length > 0 ? this.machines[0].id : null;
//            this.error = '';
//            this.issueModalInstance.show();
//        },
//        async issueTool() {
//            if (!this.issueData.machine_id) {
//                this.error = "Wybierz maszynę.";
//                return;
//            }
//            try {
//                await axios.post('/api/usages/', this.issueData);
//                this.issueModalInstance.hide();
//                await this.fetchData();
//            } catch (error) {
//                this.error = error.response?.data?.error || "Wystąpił nieznany błąd.";
//                console.error("Błąd przy wydawaniu narzędzia:", error);
//            }
//        },
//        showReturnModal(usageId) {
//            this.usageIdToReturn = usageId;
//            this.returnModalInstance.show();
//        },
//        async confirmReturnTool() {
//            try {
//                await axios.patch(`/api/usages/${this.usageIdToReturn}/`, { return_date: new Date().toISOString() });
//                await this.fetchData();
//            } catch (error) {
//                alert("Wystąpił błąd podczas zwracania narzędzia.");
//                console.error("Błąd przy zwracaniu narzędzia:", error);
//            } finally {
//                this.returnModalInstance.hide();
//                this.usageIdToReturn = null;
//            }
//        },
//        // Nowe metody
//        openToolModal(tool = null) {
//            if (tool) {
//                this.isEditMode = true;
//                this.currentTool = { ...tool, category_id: tool.category.id };
//            } else {
//                this.isEditMode = false;
//                this.currentTool = {
//                    category_id: this.categories.length > 0 ? this.categories[0].id : null,
//                    description: '',
//                    catalog_number: '',
//                    quantity_new: 0,
//                    quantity_used_available: 0
//                };
//            }
//            this.toolModalInstance.show();
//        },
//        async saveTool() {
//            try {
//                if (this.isEditMode) {
//                    await axios.patch(`/api/tools/${this.currentTool.id}/`, this.currentTool);
//                } else {
//                    await axios.post('/api/tools/', this.currentTool);
//                }
//                this.toolModalInstance.hide();
//                await this.fetchData();
//            } catch (error) {
//                console.error("Błąd podczas zapisywania narzędzia:", error);
//                alert("Wystąpił błąd. Sprawdź konsolę, aby uzyskać więcej informacji.");
//            }
//        },
//        openCategoryModal() {
//            this.newCategoryName = '';
//            this.categoryModalInstance.show();
//        },
//        async saveCategory() {
//            if (!this.newCategoryName.trim()) {
//                alert("Nazwa kategorii nie może być pusta.");
//                return;
//            }
//            try {
//                await axios.post('/api/categories/', { name: this.newCategoryName });
//                this.newCategoryName = '';
//                await this.fetchData();
//                // Opcjonalnie: można by zamknąć modal po sukcesie, ale zostawienie go otwartym
//                // pozwala na dodanie kilku kategorii pod rząd.
//            } catch (error) {
//                console.error("Błąd podczas dodawania kategorii:", error);
//                alert("Wystąpił błąd. Możliwe, że kategoria o tej nazwie już istnieje.");
//            }
//        }
//    },
//    mounted() {
//        this.fetchData();
//        this.issueModalInstance = new bootstrap.Modal(this.$refs.issueModal);
//        this.returnModalInstance = new bootstrap.Modal(this.$refs.returnModal);
//        this.toolModalInstance = new bootstrap.Modal(this.$refs.toolModal);
//        this.categoryModalInstance = new bootstrap.Modal(this.$refs.categoryModal);
//    }
//}).mount('#app');
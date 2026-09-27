import { usePage } from '@inertiajs/vue3';

// Wspólna paginacja tabel. Limit wierszy na stronę = globalne settings.PAGE_SIZE
// (przekazywane w propsie infoProgram przez get_info_program()).
const PAGINATOR_TEMPLATE = 'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown CurrentPageReport';

export function usePaginacja() {
    const pageSize = usePage().props.infoProgram?.PAGE_SIZE || 25;
    const rowsPerPageOptions = [...new Set([pageSize, 50, 100, 200])].sort((a, b) => a - b);
    return { pageSize, rowsPerPageOptions, paginatorTemplate: PAGINATOR_TEMPLATE };
}

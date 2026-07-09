/**
 * ASN.1 Web Decoder v3.0 - Búsqueda en tiempo real
 * Módulo de búsqueda inteligente
 */

// Configuración de búsqueda
const SearchConfig = {
    MIN_QUERY_LENGTH: 2,
    DEBOUNCE_DELAY: 300,
    MAX_RESULTS: 100
};

// Estado de búsqueda
let searchState = {
    query: '',
    results: [],
    activeFilters: {
        tag: true,
        hex: true,
        value: true
    }
};

// Debounce timer
let searchTimer = null;

/**
 * Inicializa el módulo de búsqueda
 */
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const filterTag = document.getElementById('filter-tag');
    const filterHex = document.getElementById('filter-hex');
    const filterValue = document.getElementById('filter-value');
    
    if (!searchInput) return;
    
    // Event listeners para filtros
    if (filterTag) {
        filterTag.addEventListener('change', (e) => {
            searchState.activeFilters.tag = e.target.checked;
            performSmartSearch();
        });
    }
    
    if (filterHex) {
        filterHex.addEventListener('change', (e) => {
            searchState.activeFilters.hex = e.target.checked;
            performSmartSearch();
        });
    }
    
    if (filterValue) {
        filterValue.addEventListener('change', (e) => {
            searchState.activeFilters.value = e.target.checked;
            performSmartSearch();
        });
    }
    
    // Event listener para input con debounce
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimer);
        
        searchTimer = setTimeout(() => {
            searchState.query = e.target.value.trim();
            performSmartSearch();
        }, SearchConfig.DEBOUNCE_DELAY);
    });
    
    // Atajo de teclado (Ctrl+F)
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    });
}

/**
 * Realiza búsqueda inteligente
 */
function performSmartSearch() {
    const { query, activeFilters } = searchState;
    
    // Limpiar resultados anteriores
    clearSearchHighlights();
    
    // Si no hay query, salir
    if (!query || query.length < SearchConfig.MIN_QUERY_LENGTH) {
        updateSearchResults(0);
        return;
    }
    
    // Buscar en el árbol
    const treeView = document.getElementById('tree-view');
    if (!treeView) return;
    
    const nodes = treeView.querySelectorAll('.tree-node');
    const results = [];
    
    nodes.forEach((node, index) => {
        if (results.length >= SearchConfig.MAX_RESULTS) return;
        
        const matchData = extractNodeData(node);
        const matches = searchInNode(matchData, query, activeFilters);
        
        if (matches) {
            results.push({ node, matchData, index });
            highlightNode(node, matches.type);
        }
    });
    
    searchState.results = results;
    updateSearchResults(results.length);
    
    console.log(`Búsqueda "${query}": ${results.length} resultados`);
}

/**
 * Extrae datos de un nodo para búsqueda
 */
function extractNodeData(node) {
    return {
        tag: node.querySelector('.tree-tag')?.textContent || '',
        class: node.querySelector('.tree-class')?.textContent || '',
        length: node.querySelector('.tree-length')?.textContent || '',
        value: node.querySelector('.tree-value')?.textContent || '',
        hex: node.querySelector('.tree-hex')?.textContent || '',
        fullText: node.textContent.toLowerCase()
    };
}

/**
 * Busca en los datos de un nodo
 */
function searchInNode(data, query, filters) {
    const queryLower = query.toLowerCase();
    const matches = [];
    
    // Búsqueda por tag
    if (filters.tag) {
        if (data.tag.toLowerCase().includes(queryLower)) {
            matches.push({ type: 'tag', field: 'tag' });
        }
    }
    
    // Búsqueda por hex
    if (filters.hex) {
        if (data.hex.toLowerCase().includes(queryLower)) {
            matches.push({ type: 'hex', field: 'hex' });
        }
    }
    
    // Búsqueda por valor
    if (filters.value) {
        if (data.value.toLowerCase().includes(queryLower)) {
            matches.push({ type: 'value', field: 'value' });
        }
    }
    
    return matches.length > 0 ? matches[0] : null;
}

/**
 * Resalta un nodo según el tipo de coincidencia
 */
function highlightNode(node, matchType) {
    // Remover clases previas
    node.classList.remove('search-highlight-tag', 'search-highlight-hex', 'search-highlight-value');
    
    // Agregar clase según tipo
    node.classList.add(`search-highlight-${matchType}`);
    
    // Scroll suave si es el primer resultado
    if (searchState.results.length === 1) {
        node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Limpia todos los resaltados de búsqueda
 */
function clearSearchHighlights() {
    const treeView = document.getElementById('tree-view');
    if (!treeView) return;
    
    const nodes = treeView.querySelectorAll('.tree-node');
    nodes.forEach(node => {
        node.classList.remove(
            'search-highlight-tag',
            'search-highlight-hex',
            'search-highlight-value',
            'error-highlight'
        );
    });
}

/**
 * Actualiza el contador de resultados
 */
function updateSearchResults(count) {
    let badge = document.getElementById('search-results-badge');
    
    if (!badge) {
        badge = document.createElement('span');
        badge.id = 'search-results-badge';
        badge.style.cssText = 'margin-left: 1rem; padding: 0.2rem 0.6rem; background: var(--accent); border-radius: 12px; font-size: 0.8rem;';
        
        const searchSection = document.querySelector('.search-container');
        if (searchSection && searchSection.querySelector('h2')) {
            searchSection.querySelector('h2').appendChild(badge);
        }
    }
    
    if (count > 0) {
        badge.textContent = `${count} encontrado${count !== 1 ? 's' : ''}`;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

/**
 * Navega al siguiente resultado de búsqueda
 */
function nextSearchResult() {
    if (searchState.results.length === 0) return;
    
    const currentIndex = searchState.currentIndex || -1;
    const nextIndex = (currentIndex + 1) % searchState.results.length;
    
    goToResult(nextIndex);
}

/**
 * Navega al resultado anterior
 */
function previousSearchResult() {
    if (searchState.results.length === 0) return;
    
    const currentIndex = searchState.currentIndex || 0;
    const prevIndex = (currentIndex - 1 + searchState.results.length) % searchState.results.length;
    
    goToResult(prevIndex);
}

/**
 * Va a un resultado específico
 */
function goToResult(index) {
    const result = searchState.results[index];
    if (!result) return;
    
    // Remover highlight del resultado anterior
    if (searchState.currentIndex !== undefined) {
        const prevResult = searchState.results[searchState.currentIndex];
        if (prevResult && prevResult.node) {
            prevResult.node.classList.remove('search-result-active');
        }
    }
    
    // Highlight del nuevo resultado
    result.node.classList.add('search-result-active');
    result.node.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    searchState.currentIndex = index;
    
    console.log(`Resultado ${index + 1} de ${searchState.results.length}`);
}

/**
 * Exporta funciones para uso global
 */
window.SearchModule = {
    init: initSearch,
    performSearch: performSmartSearch,
    nextResult: nextSearchResult,
    previousResult: previousSearchResult,
    clear: clearSearchHighlights
};

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSearch);
} else {
    initSearch();
}

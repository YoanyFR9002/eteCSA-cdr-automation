/**
 * ASN.1 Web Decoder v3.0 - Frontend Logic
 * Maneja decodificación, visualización y exportación
 */

// Estado global
let currentDecodedData = null;
let selectedFile = null;

// Elementos DOM principales
const elements = {
    hexData: document.getElementById('hex-data'),
    decodeBtn: document.getElementById('decode-btn'),
    pasteBtn: document.getElementById('paste-btn'),
    clearHexBtn: document.getElementById('clear-hex-btn'),
    loadSampleBtn: document.getElementById('load-sample-btn'),
    fileInput: document.getElementById('file-input'),
    dropZone: document.getElementById('drop-zone'),
    statsPanel: document.getElementById('stats-panel'),
    searchSection: document.getElementById('search-section'),
    resultsSection: document.getElementById('results-section'),
    errorsSection: document.getElementById('errors-section'),
    hexView: document.getElementById('hex-view'),
    treeView: document.getElementById('tree-view'),
    errorsList: document.getElementById('errors-list'),
    loadingOverlay: document.getElementById('loading-overlay'),
    searchInput: document.getElementById('search-input'),
    filterTag: document.getElementById('filter-tag'),
    filterHex: document.getElementById('filter-hex'),
    filterValue: document.getElementById('filter-value'),
    themeToggle: document.getElementById('theme-toggle')
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadTheme();
});

// Configurar event listeners
function setupEventListeners() {
    // Botón decodificar
    elements.decodeBtn.addEventListener('click', decodeData);
    
    // Pegar desde portapapeles
    elements.pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            elements.hexData.value = text;
        } catch (err) {
            alert('Error al pegar: ' + err);
        }
    });
    
    // Limpiar hex
    elements.clearHexBtn.addEventListener('click', () => {
        elements.hexData.value = '';
        resetResults();
    });
    
    // Cargar ejemplo
    elements.loadSampleBtn.addEventListener('click', loadSampleData);
    
    // File input
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Drop zone
    elements.dropZone.addEventListener('click', () => elements.fileInput.click());
    elements.dropZone.addEventListener('dragover', handleDragOver);
    elements.dropZone.addEventListener('dragleave', handleDragLeave);
    elements.dropZone.addEventListener('drop', handleDrop);
    
    // Export buttons
    document.getElementById('export-txt').addEventListener('click', () => exportData('txt'));
    document.getElementById('export-json').addEventListener('click', () => exportData('json'));
    document.getElementById('export-csv').addEventListener('click', () => exportData('csv'));
    document.getElementById('export-pcap').addEventListener('click', () => exportData('pcapng'));
    
    // Search
    elements.searchInput.addEventListener('input', performSearch);
    
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchTab);
    });
}

// Switch tabs
function switchTab(e) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    e.target.classList.add('active');
    const tabId = e.target.dataset.tab;
    document.getElementById(tabId).classList.add('active');
}

// Manejar drag over
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.add('dragover');
}

// Manejar drag leave
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.remove('dragover');
}

// Manejar drop
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Manejar selección de archivo
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Procesar archivo
async function processFile(file) {
    selectedFile = file;
    
    const reader = new FileReader();
    
    reader.onload = async (e) => {
        const arrayBuffer = e.target.result;
        const bytes = new Uint8Array(arrayBuffer);
        
        // Convertir a hex
        const hexString = Array.from(bytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join(' ')
            .toUpperCase();
        
        elements.hexData.value = hexString;
        
        // Auto-decode
        await decodeData();
    };
    
    reader.readAsArrayBuffer(file);
}

// Decodificar datos
async function decodeData() {
    const hexData = elements.hexData.value.trim();
    
    if (!hexData && !selectedFile) {
        alert('Por favor ingrese datos hex o seleccione un archivo');
        return;
    }
    
    showLoading(true);
    
    try {
        let response;
        
        if (selectedFile) {
            // Enviar archivo
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            response = await fetch('/api/decode', {
                method: 'POST',
                body: formData
            });
        } else {
            // Enviar hex
            response = await fetch('/api/decode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ hex_data: hexData })
            });
        }
        
        const result = await response.json();
        
        if (response.ok) {
            currentDecodedData = result;
            displayResults(result);
        } else {
            alert('Error: ' + (result.error || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Decode error:', error);
        alert('Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Mostrar resultados
function displayResults(result) {
    // Mostrar secciones
    elements.statsPanel.classList.remove('hidden');
    elements.searchSection.classList.remove('hidden');
    elements.resultsSection.classList.remove('hidden');
    
    // Mostrar estadísticas
    const stats = result.stats || {};
    document.getElementById('stat-size').textContent = formatBytes(stats.total_size || 0);
    document.getElementById('stat-records').textContent = stats.total_records || 0;
    document.getElementById('stat-octets').textContent = stats.total_octets || 0;
    document.getElementById('stat-time').textContent = (stats.decode_time_ms || 0).toFixed(2) + ' ms';
    document.getElementById('stat-encoding').textContent = stats.encoding_detected || 'N/A';
    
    const errorCount = (result.errors || []).length;
    document.getElementById('stat-errors').textContent = errorCount;
    
    // Mostrar vista hex
    displayHexView(result.data);
    
    // Mostrar árbol
    displayTreeView(result.data);
    
    // Mostrar errores
    displayErrors(result.errors || []);
}

// Mostrar vista hexadecimal
function displayHexView(data) {
    const hexLines = [];
    let offset = 0;
    
    data.forEach(item => {
        const hex = item.hex || '';
        if (hex) {
            const line = formatHexLine(hex, offset);
            hexLines.push(line);
            offset += Math.ceil(hex.length / 2);
        }
    });
    
    elements.hexView.innerHTML = hexLines.join('\n');
}

// Formatear línea hex
function formatHexLine(hex, offset) {
    const bytes = hex.match(/.{1,2}/g) || [];
    const ascii = bytes.map(b => {
        const code = parseInt(b, 16);
        return (code >= 32 && code <= 126) ? String.fromCharCode(code) : '.';
    }).join('');
    
    const hexPairs = bytes.join(' ');
    const offsetStr = offset.toString(16).padStart(8, '0').toUpperCase();
    
    return `<span class="hex-offset">${offsetStr}</span>  ${hexPairs.padEnd(47)}  |${ascii}|`;
}

// Mostrar árbol decodificado
function displayTreeView(data, container = elements.treeView, level = 0) {
    container.innerHTML = '';
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p>No hay datos para mostrar</p>';
        return;
    }
    
    data.forEach((item, index) => {
        const node = createTreeNode(item, level);
        container.appendChild(node);
    });
}

// Crear nodo de árbol
function createTreeNode(item, level) {
    const div = document.createElement('div');
    div.className = 'tree-node';
    
    const hasChildren = item.constructed && item.value && Array.isArray(item.value) && item.value.length > 0;
    
    if (hasChildren) {
        div.classList.add('has-children');
    }
    
    // Contenido del nodo
    const content = document.createElement('span');
    content.innerHTML = `
        <span class="tree-tag">${item.tag}</span>
        <span class="tree-class">(${item.tag_class})</span>
        <span class="tree-length">Len=${item.length}</span>
        ${!item.constructed ? `<span class="tree-value">${formatValue(item.value)}</span>` : ''}
        ${item.hex ? `<span class="tree-hex">[${item.hex.substring(0, 20)}${item.hex.length > 20 ? '...' : ''}]</span>` : ''}
    `;
    
    div.appendChild(content);
    
    // Click handler para expandir/colapsar
    div.addEventListener('click', (e) => {
        e.stopPropagation();
        
        if (hasChildren) {
            div.classList.toggle('expanded');
            
            const childrenContainer = div.querySelector('.tree-children');
            if (childrenContainer) {
                childrenContainer.style.display = 
                    childrenContainer.style.display === 'none' ? 'block' : 'none';
            }
        }
    });
    
    // Hijos
    if (hasChildren) {
        const childrenDiv = document.createElement('div');
        childrenDiv.className = 'tree-children';
        childrenDiv.style.display = 'none';
        
        item.value.forEach(child => {
            const childNode = createTreeNode(child, level + 1);
            childrenDiv.appendChild(childNode);
        });
        
        div.appendChild(childrenDiv);
    }
    
    return div;
}

// Formatear valor
function formatValue(value) {
    if (value === null) return 'NULL';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'string' && value.length > 50) {
        return value.substring(0, 50) + '...';
    }
    return value;
}

// Mostrar errores
function displayErrors(errors) {
    if (errors.length === 0) {
        elements.errorsSection.classList.add('hidden');
        return;
    }
    
    elements.errorsSection.classList.remove('hidden');
    elements.errorsList.innerHTML = '';
    
    errors.forEach(error => {
        const div = document.createElement('div');
        div.className = 'error-item';
        div.innerHTML = `
            <strong>Error en offset ${error.offset || 'N/A'}:</strong>
            ${error.error || 'Error desconocido'}
            ${error.hex_context ? `<br><small>Hex: ${error.hex_context}</small>` : ''}
        `;
        elements.errorsList.appendChild(div);
    });
}

// Búsqueda
function performSearch() {
    const query = elements.searchInput.value.toLowerCase().trim();
    
    if (!query || !currentDecodedData) {
        resetSearchHighlight();
        return;
    }
    
    const filterTag = elements.filterTag.checked;
    const filterHex = elements.filterHex.checked;
    const filterValue = elements.filterValue.checked;
    
    // Buscar en el árbol
    const nodes = elements.treeView.querySelectorAll('.tree-node');
    let matchCount = 0;
    
    nodes.forEach(node => {
        const text = node.textContent.toLowerCase();
        const tag = node.querySelector('.tree-tag')?.textContent.toLowerCase() || '';
        const hex = node.querySelector('.tree-hex')?.textContent.toLowerCase() || '';
        const value = node.querySelector('.tree-value')?.textContent.toLowerCase() || '';
        
        let matches = false;
        
        if (filterTag && tag.includes(query)) matches = true;
        if (filterHex && hex.includes(query)) matches = true;
        if (filterValue && value.includes(query)) matches = true;
        
        if (matches) {
            node.classList.add('error-highlight');
            matchCount++;
        } else {
            node.classList.remove('error-highlight');
        }
    });
    
    console.log(`Búsqueda: "${query}" - ${matchCount} coincidencias`);
}

// Resetear búsqueda
function resetSearchHighlight() {
    const nodes = elements.treeView.querySelectorAll('.tree-node');
    nodes.forEach(node => {
        node.classList.remove('error-highlight');
    });
}

// Exportar datos
async function exportData(format) {
    if (!currentDecodedData) {
        alert('No hay datos para exportar');
        return;
    }
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                decoded_data: currentDecodedData,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `asn1_export.${format}`;
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            const error = await response.json();
            alert('Error exportando: ' + error.error);
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Error de conexión: ' + error.message);
    }
}

// Resetear resultados
function resetResults() {
    currentDecodedData = null;
    selectedFile = null;
    
    elements.statsPanel.classList.add('hidden');
    elements.searchSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.errorsSection.classList.add('hidden');
    
    elements.hexView.innerHTML = '';
    elements.treeView.innerHTML = '';
    elements.errorsList.innerHTML = '';
}

// Cargar datos de ejemplo
function loadSampleData() {
    // Sample ASN.1 SEQUENCE con INTEGER y STRING
    const sample = '30 1A 02 01 42 0C 05 Hello 02 02 03 E8 0C 0B World Test';
    elements.hexData.value = sample;
}

// Mostrar loading
function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Toggle tema
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    document.body.classList.toggle('dark-theme');
    
    const isLight = document.body.classList.contains('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    elements.themeToggle.textContent = isLight ? '☀️' : '🌙';
}

// Cargar tema guardado
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
        elements.themeToggle.textContent = '☀️';
    }
}

// Utilidad: formatear bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Funciones globales para modales
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function showHelp() {
    document.getElementById('help-modal').classList.remove('hidden');
}

function showAbout() {
    alert('ASN.1 Web Decoder v3.0 Enterprise Edition\n\nDesarrollado para decodificación profesional de CDRs de telecomunicaciones.\n\nSoporta BER/DER/PER auto-detectado.');
}

// Cerrar modal al hacer click fuera
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.add('hidden');
    }
}

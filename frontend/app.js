// Global variables
let currentMachineId = 1;
let currentSiteId = null;
let currentObjectType = null; // 'site', 'machine', 'template'
let currentObjectId = null;
let currentObjectData = null;
let efficiencyChart = null;
let efficiencyData = [];

// API Base URL
const API_BASE = 'http://localhost:8000/api/v1';

// Application Version
const APP_VERSION = '2.4';

// Version: 2.0 - Templates System
// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    updateVersionIndicator();
});

// Function to automatically detect and display version
function updateVersionIndicator() {
    const versionIndicator = document.getElementById('versionIndicator');
    if (!versionIndicator) return;
    
    // Use the application version directly
    versionIndicator.textContent = `v${APP_VERSION}`;
}

function initializeApp() {
    initializeChart();
    initializeRatioAnalysisChart();
    setTheme('dark'); // Default theme
    loadMarketData();
    
    // Mettre à jour les données de marché toutes les 30 secondes
    setInterval(loadMarketData, 30000);
    
    // Attendre que les graphiques soient complètement initialisés avant de charger les sites
    setTimeout(() => {
        // Charger les sites et machines (sélectionnera automatiquement le premier site)
        loadSitesAndMachines(true);
    }, 200);
    
    // Initialize navigation handling
    initializeNavigation();
}

// Show welcome message when no object is selected
function showWelcomeMessage() {
    const selectedObjectCard = document.getElementById('selectedObjectCard');
    const selectedObjectTitle = document.getElementById('selectedObjectTitle');
    const selectedObjectInfo = document.getElementById('selectedObjectInfo');
    
    if (!selectedObjectCard || !selectedObjectTitle || !selectedObjectInfo) return;
    
    selectedObjectTitle.innerHTML = '<i class="fas fa-home"></i> Bienvenue';
    selectedObjectInfo.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="info-item">
                    <strong>📊 Bitcoin Backtesting</strong>
                    <p class="text-muted mb-2">Sélectionnez un site ou une machine dans la barre latérale pour commencer l'analyse.</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="info-item">
                    <strong>🎯 Fonctionnalités</strong>
                    <ul class="text-muted mb-0">
                        <li>Optimisation économique et technique</li>
                        <li>Analyse des courbes d'efficacité</li>
                        <li>Calculs de rentabilité</li>
                        <li>Gestion multi-machines</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    selectedObjectCard.style.display = 'block';
}

// Theme Management
function changeStyle(theme) {
    setTheme(theme);
    updateChartTheme();
    updateVersionIndicator(); // Update version indicator when theme changes
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function updateChartTheme() {
    if (efficiencyChart) {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#c9d1d9' : '#212529';
        const gridColor = isDark ? '#30363d' : '#dee2e6';
        
        const efficiencyChart = window.efficiencyChart;
        if (efficiencyChart) {
            efficiencyChart.options.plugins.legend.labels.color = textColor;
            efficiencyChart.options.scales.x.grid.color = gridColor;
            efficiencyChart.options.scales.y.grid.color = gridColor;
            efficiencyChart.options.scales.x.ticks.color = textColor;
            efficiencyChart.options.scales.y.ticks.color = textColor;
            efficiencyChart.update();
        }
    }
}

// Object Selection
function selectObject(objectType, objectId, objectData = null) {
    currentObjectType = objectType;
    currentObjectId = objectId;
    currentObjectData = objectData;
    
    // Update active object in UI
    document.querySelectorAll('.machine-item, .template-item, .site-header').forEach(item => {
        item.classList.remove('active');
    });
    
    // Hide backtest section when selecting objects
    document.getElementById('backtestSection').style.display = 'none';
    
    // Add active class to selected object
    if (event && event.target) {
        const target = event.target.closest('.machine-item, .template-item, .site-header');
        if (target) target.classList.add('active');
    } else {
        // For programmatic selection (no event), find the element by data attributes
        let selector = '';
        if (objectType === 'site') {
            selector = `.site-header[data-site-id="${objectId}"]`;
        } else if (objectType === 'machine') {
            selector = `.machine-item[data-machine-id="${objectId}"]`;
        } else if (objectType === 'template') {
            selector = `.template-item[data-template-id="${objectId}"]`;
        }
        
        if (selector) {
            const element = document.querySelector(selector);
            if (element) element.classList.add('active');
        }
    }
    
    // Update selected object info
    updateSelectedObjectInfo(objectType, objectId, objectData);
    
    // Load appropriate data based on object type
    if (objectType === 'machine' || objectType === 'template') {
        currentMachineId = objectId;
        
        // S'assurer que les graphiques sont bien initialisés avant de charger les données
        setTimeout(() => {
            loadEfficiencyData();
        }, 100);
        
        showEfficiencySection(true);
        
        // Masquer la synthèse du site
        const siteSummaryCard = document.getElementById('siteSummaryCard');
        if (siteSummaryCard) siteSummaryCard.style.display = 'none';
        
        // Masquer le bouton d'optimisation multi-machines
        const multiOptimalBtn = document.getElementById('multiOptimalBtn');
        if (multiOptimalBtn) multiOptimalBtn.style.display = 'none';
        
        // S'assurer que les sections de graphiques et d'optimisation sont visibles
        const chartsSection = document.getElementById('chartsSection');
        const optimizationSection = document.getElementById('optimizationSection');
        
        if (chartsSection) {
            chartsSection.style.display = 'flex';
        }
        if (optimizationSection) {
            optimizationSection.style.display = 'flex';
        }
        
        // Force Bootstrap grid recalculation
        window.dispatchEvent(new Event('resize'));
        
        
    } else if (objectType === 'site') {
        currentSiteId = objectId;
        
        // Charger les statistiques du site (machines, hashrate)
        loadSiteStatistics(objectId);
        
        // Charger la synthèse du site
        loadSiteSummary(objectId);
        
        // Mettre à jour les informations du site avec les données fraîches
        if (objectData) {
            updateSelectedObjectInfo(objectType, objectId, objectData);
        }
        
        // Masquer les sections de graphiques et d'optimisation pour les sites
        const chartsSection = document.getElementById('chartsSection');
        const optimizationSection = document.getElementById('optimizationSection');
        
        if (chartsSection) {
            chartsSection.style.display = 'none';
        }
        if (optimizationSection) {
            optimizationSection.style.display = 'none';
        }
        
        // Afficher les boutons d'optimisation multi-machines
        const multiOptimalBtn = document.getElementById('multiOptimalBtn');
        const manualRatioBtn = document.getElementById('manualRatioBtn');
        if (multiOptimalBtn) multiOptimalBtn.style.display = 'block';
        if (manualRatioBtn) manualRatioBtn.style.display = 'block';
    }
}

// Machine Selection (for backward compatibility)
function selectMachine(machineId) {
    selectObject('machine', machineId);
}

// Select machine from site summary table
async function selectMachineFromSummary(templateId, machineName) {
    try {
        // Récupérer les données du template
        const response = await fetch(`${API_BASE}/machine-templates/${templateId}`);
        if (!response.ok) {
            throw new Error('Failed to load machine template');
        }
        
        const template = await response.json();
        
        // Sélectionner la machine avec les données du template
        selectObject('template', templateId, template);
        
        // Afficher une notification
        showNotification(`Machine sélectionnée: ${machineName}`, 'success');
        
    } catch (error) {
        console.error('Error selecting machine from summary:', error);
        showNotification('Erreur lors de la sélection de la machine', 'error');
    }
}

// Update Selected Object Info
function updateSelectedObjectInfo(objectType, objectId, objectData) {
    const card = document.getElementById('selectedObjectCard');
    const title = document.getElementById('selectedObjectTitle');
    const info = document.getElementById('selectedObjectInfo');
    
    if (!card || !title || !info) return;
    
    card.style.display = 'block';
    
    switch (objectType) {
        case 'site':
            title.textContent = `Site: ${objectData?.name || 'Chargement...'}`;
            info.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="info-item">
                            <strong>Adresse:</strong> <span id="siteAddress">Chargement...</span>
                        </div>
                        <div class="info-item">
                            <strong>Électricité 1er palier:</strong> <span id="siteTier1Rate">Chargement...</span> $/kWh
                        </div>
                        <div class="info-item">
                            <strong>Électricité 2ème palier:</strong> <span id="siteTier2Rate">Chargement...</span> $/kWh
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="info-item">
                            <strong>Devise:</strong> <span id="siteCurrency">Chargement...</span>
                        </div>
                        <div class="info-item">
                            <strong>Machines:</strong> <span id="siteMachineCount">Chargement...</span>
                        </div>
                        <div class="info-item">
                            <strong>Hashrate total:</strong> <span id="siteTotalHashrate">Chargement...</span>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'machine':
        case 'template':
            const machineName = objectData?.model || 'Machine';
            const hashrate = objectData?.hashrate_nominal || '0';
            const power = objectData?.power_nominal || '0';
            const efficiency = objectData?.efficiency_base || '0';
            
            title.textContent = `Machine: ${machineName}`;
            info.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="info-item">
                            <strong>Modèle:</strong> ${machineName}
                        </div>
                        <div class="info-item">
                            <strong>Fabricant:</strong> ${objectData?.manufacturer || 'Non spécifié'}
                        </div>
                        <div class="info-item">
                            <strong>Hashrate nominal:</strong> ${hashrate} TH/s
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="info-item">
                            <strong>Puissance nominale:</strong> ${power}W
                        </div>
                        <div class="info-item">
                            <strong>Efficacité de base:</strong> ${efficiency} J/TH
                        </div>
                        <div class="info-item">
                            <strong>Prix:</strong> ${objectData?.price_cad ? `${objectData.price_cad} CAD` : 'Non spécifié'}
                        </div>
                    </div>
                </div>
            `;
            break;
            
        default:
            card.style.display = 'none';
            return;
    }
}

// Load Site Summary
async function loadSiteSummary(siteId) {
    try {
        const response = await fetch(`${API_BASE}/sites/${siteId}/summary`);
        if (!response.ok) {
            throw new Error('Failed to load site summary');
        }
        
        const summary = await response.json();
        updateSiteSummaryDisplay(summary);
        
    } catch (error) {
        console.error('Error loading site summary:', error);
        showNotification('Erreur lors du chargement de la synthèse du site', 'error');
    }
}



// Update Site Summary Display
function updateSiteSummaryDisplay(summary) {
    const card = document.getElementById('siteSummaryCard');
    const title = document.getElementById('siteSummaryTitle');
    const tbody = document.getElementById('siteSummaryTableBody');
    const tfoot = document.getElementById('siteSummaryTableFooter');
    
    if (!card || !title || !tbody || !tfoot) return;
    
    // Afficher la carte
    card.style.display = 'block';
    title.textContent = `Synthèse du Site: ${summary.site_name}`;
    
    // Afficher les boutons d'action seulement s'il y a des machines
    const multiOptimalBtn = document.getElementById('multiOptimalBtn');
    const globalOptimizationBtn = document.getElementById('globalOptimizationBtn');
    const manualRatioBtn = document.getElementById('manualRatioBtn');
    const nominalRatioBtn = document.getElementById('nominalRatioBtn');
    
    console.log('Boutons trouvés:', {
        multiOptimal: !!multiOptimalBtn,
        globalOptimization: !!globalOptimizationBtn,
        manualRatio: !!manualRatioBtn,
        nominalRatio: !!nominalRatioBtn
    });
    
    const machineCount = summary.machines.length;
    console.log('Nombre de machines dans le site:', machineCount);
    console.log('Machines:', summary.machines);
    
    if (machineCount === 0) {
        console.log('Aucune machine - masquage de tous les boutons');
        // Masquer tous les boutons s'il n'y a pas de machines
        if (multiOptimalBtn) {
            multiOptimalBtn.style.display = 'none';
            console.log('Bouton multiOptimal masqué');
        }
        if (globalOptimizationBtn) {
            globalOptimizationBtn.style.display = 'none';
            console.log('Bouton globalOptimization masqué');
        }
        if (manualRatioBtn) {
            manualRatioBtn.style.display = 'none';
            console.log('Bouton manualRatio masqué');
        }
        if (nominalRatioBtn) {
            nominalRatioBtn.style.display = 'none';
            console.log('Bouton nominalRatio masqué');
        }
    } else {
        console.log(`${machineCount} machine(s) - affichage des boutons`);
        // Afficher les boutons selon le nombre de machines
        if (multiOptimalBtn) multiOptimalBtn.style.display = 'inline-block';
        if (manualRatioBtn) manualRatioBtn.style.display = 'inline-block';
        if (nominalRatioBtn) nominalRatioBtn.style.display = 'inline-block';
        
        // Afficher l'optimisation globale seulement s'il y a plus d'une machine
        if (globalOptimizationBtn) {
            if (machineCount > 1) {
                globalOptimizationBtn.style.display = 'inline-block';
                globalOptimizationBtn.disabled = false;
                globalOptimizationBtn.title = `Optimisation globale pour ${machineCount} machines`;
            } else {
                globalOptimizationBtn.style.display = 'none';
            }
        }
    }
    
    // Vider le tableau
    tbody.innerHTML = '';
    tfoot.innerHTML = '';
    
    if (summary.machines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Aucune machine dans ce site</td></tr>';
        return;
    }
    
    // Remplir le tableau avec les machines
    summary.machines.forEach(machine => {
        // Déterminer l'affichage du ratio actuel
        let currentRatioDisplay = 'N/A';
        let currentRatioClass = '';
        
        if (machine.current_ratio !== null && machine.current_ratio !== undefined) {
            currentRatioDisplay = machine.current_ratio.toFixed(3);
            
            // Logique d'affichage des icônes multiples
            let icons = [];
            
            // Toujours l'icône nominal si ratio = 1.0
            if (machine.current_ratio === 1.0) {
                icons.push('<i class="fas fa-undo text-muted" title="Ratio nominal"></i>');
                currentRatioClass = 'text-muted';
            }
            
            // Si ratio actuel = ratio optimal calculé → Ajouter icône optimal
            if (machine.optimal_ratio && Math.abs(machine.current_ratio - machine.optimal_ratio) < 0.01) {
                icons.push('<i class="fas fa-cog text-info" title="Ratio optimal"></i>');
                if (machine.current_ratio !== 1.0) {
                    currentRatioClass = 'text-info';
                }
            }
            
            // Si ratio_type = 'optimal' ET ratio différent → Ajouter icône d'alerte
            if (machine.ratio_type === 'optimal' && 
                machine.optimal_ratio && 
                Math.abs(machine.current_ratio - machine.optimal_ratio) > 0.01) {
                icons.push('<i class="fas fa-exclamation-triangle text-warning" title="Ratio optimal a changé"></i>');
                currentRatioClass = 'text-warning';
            }
            
            // Si ratio_type = 'manual' et pas d'autres icônes
            if (machine.ratio_type === 'manual' && icons.length === 0) {
                icons.push('<i class="fas fa-hand-paper text-warning" title="Ratio manuel"></i>');
                currentRatioClass = 'text-warning';
            }
            
            // Ajouter les icônes au display
            currentRatioDisplay += ' ' + icons.join(' ');
        }
        
        const row = `
            <tr>
                <td>
                    <a href="#" class="machine-link" onclick="selectMachineFromSummary('${machine.template_id}', '${machine.name}')" title="Cliquer pour voir les détails de cette machine">
                        ${machine.name}
                        <i class="fas fa-external-link-alt ms-1" style="font-size: 0.8em; opacity: 0.7;"></i>
                    </a>
                </td>
                <td>${machine.hashrate.toFixed(2)} TH/s</td>
                <td>${Math.round(machine.power)}W</td>
                <td>$${machine.daily_revenue.toFixed(2)}</td>
                <td>$${machine.daily_cost.toFixed(2)}</td>
                <td class="${machine.daily_profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${machine.daily_profit.toFixed(2)}
                </td>
                <td>${machine.efficiency_th_per_watt.toFixed(3)} TH/s/W</td>
                <td>${machine.optimal_ratio ? machine.optimal_ratio.toFixed(3) : 'N/A'}</td>
                <td class="${currentRatioClass}">
                    ${currentRatioDisplay}
                    <button class="btn btn-sm btn-outline-primary ms-2" 
                            onclick="editMachineRatio(${machine.instance_id})" 
                            title="Modifier le ratio de cette machine">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
    
    // Ajouter les totaux
    const footer = `
        <tr class="table-info">
            <td><strong>TOTAL</strong></td>
            <td><strong>${summary.total_hashrate.toFixed(2)} TH/s</strong></td>
            <td><strong>${Math.round(summary.total_power)}W</strong></td>
            <td><strong>$${summary.total_revenue.toFixed(2)}</strong></td>
            <td><strong>$${summary.total_cost.toFixed(2)}</strong></td>
            <td class="${summary.total_profit >= 0 ? 'text-success' : 'text-danger'}">
                <strong>$${summary.total_profit.toFixed(2)}</strong>
            </td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr class="table-light">
            <td colspan="9" class="small text-muted">
                <i class="fas fa-info-circle"></i> 
                Électricité: ${summary.electricity_tier1_rate}$/kWh (premier ${summary.electricity_tier1_limit}kWh), 
                ${summary.electricity_tier2_rate}$/kWh (reste). 
                Machines triées par efficacité (TH/s/W). 
                <i class="fas fa-cog text-info"></i> Ratio optimal, 
                <i class="fas fa-hand-paper text-warning"></i> Ratio manuel, 
                <i class="fas fa-undo text-muted"></i> Ratio nominal,
                <i class="fas fa-exclamation-triangle text-warning"></i> Ratio optimal changé.
            </td>
        </tr>
    `;
    tfoot.innerHTML = footer;
}

// Fonction supprimée - remplacée par applyOptimalRatios()

// Load Global Site Optimization
async function loadGlobalOptimization() {
    try {
        if (!currentSiteId) {
            showNotification('Aucun site sélectionné', 'error');
            return;
        }
        
        // Afficher immédiatement la modal avec indicateur de chargement
        showGlobalOptimizationLoading();
        
        // Appeler l'endpoint d'optimisation globale
        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/global-optimization`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to perform global optimization');
        }
        
        const result = await response.json();
        
        // Mettre à jour la modal avec les résultats
        updateGlobalOptimizationResults(result);
        
        // Recharger la synthèse du site pour refléter les changements
        await loadSiteSummary(currentSiteId);
        
        showNotification(`Optimisation globale terminée! ${result.combinations_tested} combinaisons testées. Profit optimal: $${result.best_profit.toFixed(2)}/jour`, 'success');
        
    } catch (error) {
        console.error('Error performing global optimization:', error);
        showNotification('Erreur lors de l\'optimisation globale', 'error');
        
        // Fermer la modal en cas d'erreur
        const modal = bootstrap.Modal.getInstance(document.getElementById('globalOptimizationModal'));
        if (modal) {
            modal.hide();
        }
    }
}

function showGlobalOptimizationLoading() {
    // Créer une modal avec indicateur de chargement
    const modalHtml = `
        <div class="modal fade" id="globalOptimizationModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-globe"></i> Optimisation Globale en Cours
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center py-5">
                            <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                                <span class="visually-hidden">Chargement...</span>
                            </div>
                            <h4 class="mt-3 text-white">Optimisation en cours...</h4>
                            <p class="text-muted">
                                <i class="fas fa-cogs"></i> 
                                Brute force grid search en cours. Cela peut prendre quelques secondes selon le nombre de machines.
                            </p>
                            <div class="progress mt-3" style="height: 10px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                     role="progressbar" 
                                     style="width: 100%" 
                                     aria-valuenow="100" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer l'ancienne modal si elle existe
    const existingModal = document.getElementById('globalOptimizationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Ajouter la nouvelle modal au body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Afficher la modal
    const modal = new bootstrap.Modal(document.getElementById('globalOptimizationModal'));
    modal.show();
}

function updateGlobalOptimizationResults(result) {
    // Mettre à jour le contenu de la modal existante
    const modalBody = document.querySelector('#globalOptimizationModal .modal-body');
    const modalTitle = document.querySelector('#globalOptimizationModal .modal-title');
    
    if (!modalBody || !modalTitle) {
        // Si la modal n'existe pas, créer une nouvelle
        showGlobalOptimizationResults(result);
        return;
    }
    
    // Mettre à jour le titre
    modalTitle.innerHTML = '<i class="fas fa-globe"></i> Résultats de l\'Optimisation Globale';
    
    // Mettre à jour le contenu
    modalBody.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-chart-line"></i> Résumé</h6>
                <ul class="list-group list-group-flush">
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Site:</span>
                        <strong>${result.site_name}</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Combinaisons testées:</span>
                        <strong>${result.combinations_tested}</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Profit optimal:</span>
                        <strong class="text-success">$${result.best_profit.toFixed(2)}/jour</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Hashrate total:</span>
                        <strong>${result.results.total_hashrate.toFixed(2)} TH/s</strong>
                    </li>
                    <li class="list-group-item d-flex justify-content-between">
                        <span>Puissance totale:</span>
                        <strong>${Math.round(result.results.total_power)}W</strong>
                    </li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-cogs"></i> Ratios Optimaux</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Machine</th>
                                <th>Ratio</th>
                                <th>Hashrate</th>
                                <th>Puissance</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.results.machine_performances.map(machine => `
                                <tr>
                                    <td>${machine.name}</td>
                                    <td><strong>${machine.ratio.toFixed(3)}</strong></td>
                                    <td>${machine.hashrate.toFixed(2)} TH/s</td>
                                    <td>${Math.round(machine.power)}W</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
                                <div class="row mt-4">
                            <div class="col-12">
                                <h6><i class="fas fa-chart-area"></i> Visualisation 3D des Sweet Spots</h6>
                                <div class="card">
                                    <div class="card-body">
                                        <div id="optimization3DChart" style="width: 100%; height: 500px; min-height: 500px;"></div>
                                    </div>
                                </div>
                                <div class="alert alert-info mt-3">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Graphique 3D :</strong> Visualisez les zones de profit optimal en 3D. Les pics représentent les sweet spots.
                                </div>
                            </div>
                        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <h6><i class="fas fa-download"></i> Export des Données</h6>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    <strong>Analyse des sweet spots :</strong> Téléchargez le fichier CSV pour analyser toutes les combinaisons testées et identifier les zones de profit optimal.
                </div>
                <button class="btn btn-success" onclick="downloadOptimizationCSV(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    <i class="fas fa-download"></i> Télécharger CSV des Résultats
                </button>
            </div>
        </div>
    `;
    
    // Créer le graphique 3D
    setTimeout(() => {
        createOptimization3DChart(result);
    }, 100);
}

// Show Global Optimization Results
function showGlobalOptimizationResults(result) {
    // Créer une modal pour afficher les résultats détaillés
    const modalHtml = `
        <div class="modal fade" id="globalOptimizationModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-globe"></i> Résultats de l'Optimisation Globale
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i class="fas fa-chart-line"></i> Résumé</h6>
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Site:</span>
                                        <strong>${result.site_name}</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Combinaisons testées:</span>
                                        <strong>${result.combinations_tested}</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Profit optimal:</span>
                                        <strong class="text-success">$${result.best_profit.toFixed(2)}/jour</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Hashrate total:</span>
                                        <strong>${result.results.total_hashrate.toFixed(2)} TH/s</strong>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>Puissance totale:</span>
                                        <strong>${Math.round(result.results.total_power)}W</strong>
                                    </li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6><i class="fas fa-cogs"></i> Ratios Optimaux</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Machine</th>
                                                <th>Ratio</th>
                                                <th>Hashrate</th>
                                                <th>Puissance</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${result.results.machine_performances.map(machine => `
                                                <tr>
                                                    <td>${machine.name}</td>
                                                    <td><strong>${machine.ratio.toFixed(3)}</strong></td>
                                                    <td>${machine.hashrate.toFixed(2)} TH/s</td>
                                                    <td>${Math.round(machine.power)}W</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mt-4">
                            <div class="col-12">
                                <h6><i class="fas fa-chart-area"></i> Visualisation 3D des Sweet Spots</h6>
                                <div class="card">
                                    <div class="card-body">
                                        <div id="optimization3DChart" style="width: 100%; height: 500px; min-height: 500px;"></div>
                                    </div>
                                </div>
                                <div class="alert alert-info mt-3">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Graphique 3D :</strong> Visualisez les zones de profit optimal en 3D. Les pics représentent les sweet spots.
                                </div>
                            </div>
                        </div>
                        

                        
                        <div class="row mt-4">
                            <div class="col-12">
                                <h6><i class="fas fa-download"></i> Export des Données</h6>
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Analyse des sweet spots :</strong> Téléchargez le fichier CSV pour analyser toutes les combinaisons testées et identifier les zones de profit optimal.
                                </div>
                                <button class="btn btn-success" onclick="downloadOptimizationCSV(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                                    <i class="fas fa-download"></i> Télécharger CSV des Résultats
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer l'ancienne modal si elle existe
    const existingModal = document.getElementById('globalOptimizationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Ajouter la nouvelle modal au body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Afficher la modal
    const modal = new bootstrap.Modal(document.getElementById('globalOptimizationModal'));
    modal.show();
    
    // Créer le graphique 3D après que la modal soit affichée
    setTimeout(() => {
        createOptimization3DChart(result);
    }, 100);
}



// Download optimization results as CSV
function downloadOptimizationCSV(result) {
    // Créer l'en-tête CSV avec les noms des machines
    const machineNames = result.results.machine_performances.map(m => m.name);
    const header = ['Combinaison', ...machineNames.map(name => `Ratio_${name}`), 'Profit_Total_$jour', 'Hashrate_Total_THs', 'Puissance_Totale_W'];
    
    // Générer les données CSV avec les vraies données
    const csvData = [];
    
    // Trier les résultats par profit décroissant pour voir les meilleures combinaisons en premier
    const sortedResults = result.all_results.sort((a, b) => b.daily_profit - a.daily_profit);
    
    // Ajouter TOUTES les combinaisons testées
    for (let i = 0; i < sortedResults.length; i++) {
        const combinationResult = sortedResults[i];
        const isOptimal = combinationResult.daily_profit === result.best_profit;
        
        const row = [
            isOptimal ? 'OPTIMAL' : `Test_${i + 1}`,
            ...combinationResult.combination.map(r => r.toFixed(3)),
            combinationResult.daily_profit.toFixed(4),
            combinationResult.total_hashrate.toFixed(2),
            Math.round(combinationResult.total_power)
        ];
        csvData.push(row);
    }
    
    // Créer le contenu CSV
    const csvContent = [header, ...csvData].map(row => row.join(',')).join('\n');
    
    // Créer et télécharger le fichier
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `optimisation_globale_${result.site_name}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Create 3D optimization visualization with Plotly
function createOptimization3DChart(result) {
    console.log('Creating optimization chart with result:', result);
    
    const container = document.getElementById('optimization3DChart');
    if (!container) {
        console.error('Container optimization3DChart not found');
        return;
    }
    
    // Vérifier si Plotly est disponible
    if (typeof Plotly === 'undefined') {
        console.error('Plotly is not loaded');
        container.innerHTML = '<div class="alert alert-danger">Plotly n\'est pas chargé. Impossible d\'afficher le graphique 3D.</div>';
        return;
    }
    
    // Nettoyer le conteneur et s'assurer qu'il a une taille définie
    container.innerHTML = '';
    container.style.width = '100%';
    container.style.height = '500px';
    container.style.minHeight = '500px';
    container.style.position = 'relative';
    container.style.overflow = 'hidden';
    
    // Préparer les données
    let data = result.all_results;
    
    // Si all_results n'est pas disponible, utiliser les données de results
    if (!data || data.length === 0) {
        console.log('all_results non disponible, utilisation de results');
        data = [{
            combination: result.results.machine_performances.map(m => m.ratio),
            daily_profit: result.results.daily_profit,
            total_hashrate: result.results.total_hashrate,
            total_power: result.results.total_power
        }];
    }
    
    console.log('Structure de result:', Object.keys(result));
    console.log('all_results existe:', !!result.all_results);
    console.log('Premier élément de all_results:', result.all_results ? result.all_results[0] : 'undefined');
    console.log('Data for chart:', data);
    
    // Déterminer le nombre de machines
    const numMachines = data[0] ? data[0].combination.length : 0;
    console.log('Nombre de machines:', numMachines);
    
    if (numMachines <= 2) {
        // Utiliser le graphique 3D pour 2 machines (1 machine n'a pas de bouton d'optimisation globale)
        create3DChart(container, data, result);
    } else {
        // Utiliser le graphique 3D avec sélecteur pour 3+ machines
        create3DChartWithSelector(container, data, result);
    }
}

function create3DChart(container, data, result) {
    console.log('Creating 3D chart for 2 machines');
    
    // Extraire les coordonnées X, Y, Z pour le graphique 3D
    const x = data.map(d => d.combination[0]); // Ratio Machine 1
    const y = data.map(d => d.combination[1]); // Ratio Machine 2
    const z = data.map(d => d.daily_profit);   // Profit
    
    console.log('Données pour graphique 3D:');
    console.log('Nombre de points:', data.length);
    console.log('Ratios X (Machine 1):', x);
    console.log('Ratios Y (Machine 2):', y);
    console.log('Profits Z:', z);
    console.log('Min profit:', Math.min(...z));
    console.log('Max profit:', Math.max(...z));
    console.log('Combinaison optimale attendue:', result.best_combination);
    console.log('Profit optimal:', result.best_profit);
    
    // Vérifier si la combinaison optimale est présente
    const optimalFound = data.find(d => 
        Math.abs(d.combination[0] - Object.values(result.best_combination)[0]) < 0.001 &&
        Math.abs(d.combination[1] - Object.values(result.best_combination)[1]) < 0.001
    );
    console.log('Combinaison optimale trouvée dans les données:', optimalFound);
    
    // Créer les couleurs basées sur le profit (adaptées au thème sombre)
    const minProfit = Math.min(...z);
    const maxProfit = Math.max(...z);
    const colors = z.map(profit => {
        const normalized = (profit - minProfit) / (maxProfit - minProfit);
        // Utiliser des couleurs plus vives qui ressortent sur fond sombre
        if (normalized > 0.8) {
            return '#00ff88'; // Vert vif pour les profits élevés
        } else if (normalized > 0.6) {
            return '#ffff00'; // Jaune pour les profits moyens
        } else if (normalized > 0.4) {
            return '#ff8800'; // Orange pour les profits faibles
        } else {
            return '#ff4444'; // Rouge pour les pertes
        }
    });
    
    // Créer les textes pour les tooltips
    const texts = data.map((d, i) => {
        let tooltip = `Ratio Machine 1: ${d.combination[0]}<br>`;
        tooltip += `Ratio Machine 2: ${d.combination[1]}<br>`;
        tooltip += `Profit: $${d.daily_profit.toFixed(2)}/jour<br>` +
                   `Hashrate: ${d.total_hashrate.toFixed(2)} TH/s<br>` +
                   `Puissance: ${d.total_power}W`;
        return tooltip;
    });
    
    // Utiliser la fonction commune pour créer le graphique
    createCommon3DChart(container, x, y, z, colors, texts, result, data, 'Machine 1', 'Machine 2');
}

function createCommon3DChart(container, x, y, z, colors, texts, result, data, xAxisTitle, yAxisTitle) {
    // Créer le graphique 3D avec Plotly
    const trace = {
        x: x,
        y: y,
        z: z,
        mode: 'markers',
        type: 'scatter3d',
        marker: {
            size: 12, // Points plus gros pour mieux les voir
            color: colors,
            opacity: 1.0, // Opacité maximale
            colorscale: 'Viridis',
            colorbar: {
                title: 'Profit ($/jour)',
                titleside: 'right'
            }
        },
        text: texts,
        hovertemplate: '<b>%{text}</b><extra></extra>'
    };
    
    const layout = {
        title: {
            text: `Visualisation 3D des Sweet Spots - Profit Optimal: $${result.best_profit.toFixed(2)}/jour`,
            font: { size: 16, color: '#ffffff' }
        },
        paper_bgcolor: '#2d3748',
        plot_bgcolor: '#2d3748',
        scene: {
            xaxis: {
                title: `Ratio ${xAxisTitle}`,
                range: [Math.min(...x), Math.max(...x)],
                gridcolor: '#4a5568',
                zerolinecolor: '#4a5568',
                titlefont: { color: '#ffffff' },
                tickfont: { color: '#ffffff' }
            },
            yaxis: {
                title: `Ratio ${yAxisTitle}`,
                range: [Math.min(...y), Math.max(...y)],
                gridcolor: '#4a5568',
                zerolinecolor: '#4a5568',
                titlefont: { color: '#ffffff' },
                tickfont: { color: '#ffffff' }
            },
            zaxis: {
                title: 'Profit ($/jour)',
                range: [Math.min(...z) * 1.1, Math.max(...z) * 1.1], // Étendre la plage pour utiliser plus d'espace
                gridcolor: '#4a5568',
                zerolinecolor: '#4a5568',
                titlefont: { color: '#ffffff' },
                tickfont: { color: '#ffffff' }
            },
            camera: {
                eye: { x: 2.5, y: 2.5, z: 1.8 } // Vue ajustée pour mieux voir les variations
            },
            aspectmode: 'manual',
            aspectratio: { x: 1, y: 1, z: 1.2 } // Augmenter la hauteur relative de l'axe Z
        },
        autosize: true,
        margin: { l: 50, r: 50, b: 50, t: 50 }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: 'optimization_3d',
            height: 500,
            width: 800,
            scale: 1
        }
    };
    
    // Créer le graphique
    try {
        console.log('Creating Plotly 3D chart with trace:', trace);
        console.log('Layout:', layout);
        
        Plotly.newPlot(container, [trace], layout, config).then(function() {
            console.log('Plotly 3D chart created successfully');
            
            // Ajouter un événement pour identifier le point optimal
            container.on('plotly_click', function(plotData) {
                const point = plotData.points[0];
                const index = point.pointIndex;
                
                // Récupérer les données du point depuis l'événement Plotly
                const clickedX = point.x;
                const clickedY = point.y;
                const clickedZ = point.z;
                
                console.log('Point cliqué:', {
                    ratio1: clickedX,
                    ratio2: clickedY,
                    profit: clickedZ
                });
                
                // Vérifier si c'est le point optimal
                if (Math.abs(clickedZ - result.best_profit) < 0.01) {
                    console.log('Point optimal cliqué!');
                    // Mettre en évidence le point optimal
                    const update = {
                        marker: {
                            size: Array(data.length).fill(8).map((size, i) => 
                                i === index ? 15 : size
                            ),
                            color: Array(data.length).fill().map((_, i) => 
                                i === index ? 'red' : colors[i]
                            )
                        }
                    };
                    Plotly.restyle(container, update);
                }
            });
        }).catch(function(error) {
            console.error('Error creating Plotly 3D chart:', error);
            container.innerHTML = '<div class="alert alert-danger">Erreur lors de la création du graphique 3D: ' + error.message + '</div>';
        });
    } catch (error) {
        console.error('Error in createCommon3DChart:', error);
        container.innerHTML = '<div class="alert alert-danger">Erreur lors de la création du graphique 3D: ' + error.message + '</div>';
    }
}

function create3DChartWithSelector(container, data, result) {
    console.log('Creating 3D chart with selector for 3+ machines');
    
    // Créer l'interface avec sélecteurs
    const numMachines = data[0].combination.length;
    const machineNames = Array.from({length: numMachines}, (_, i) => `Machine ${i + 1}`);
    
    // Créer une structure avec sélecteurs et conteneur de graphique séparés
    const selectorHTML = `
        <div class="row mb-3">
            <div class="col-md-6">
                <label for="machineXSelect" class="form-label text-white">Axe X (Ratio):</label>
                <select id="machineXSelect" class="form-select bg-dark text-white">
                    ${machineNames.map((name, i) => `<option value="${i}">${name}</option>`).join('')}
                </select>
            </div>
            <div class="col-md-6">
                <label for="machineYSelect" class="form-label text-white">Axe Y (Ratio):</label>
                <select id="machineYSelect" class="form-select bg-dark text-white">
                    ${machineNames.map((name, i) => `<option value="${i}" ${i === 1 ? 'selected' : ''}>${name}</option>`).join('')}
                </select>
            </div>
        </div>
        <div id="chart3DContainer" style="width: 100%; height: 500px; min-height: 500px; position: relative; overflow: hidden;"></div>
    `;
    
    // Ajouter la structure complète au conteneur
    container.innerHTML = selectorHTML;
    
    // Utiliser le conteneur de graphique séparé
    const chartContainer = document.getElementById('chart3DContainer');
    const machineXSelect = document.getElementById('machineXSelect');
    const machineYSelect = document.getElementById('machineYSelect');
    
    // Fonction pour ajuster automatiquement la sélection de la deuxième machine
    function adjustSecondMachineSelection() {
        const machineX = parseInt(machineXSelect.value);
        const machineY = parseInt(machineYSelect.value);
        
        if (machineX === machineY) {
            // Trouver la première machine disponible différente
            let newMachineY = 0;
            while (newMachineY === machineX && newMachineY < numMachines) {
                newMachineY++;
            }
            // Si on a fait le tour, prendre la première machine
            if (newMachineY >= numMachines) {
                newMachineY = 0;
            }
            
            machineYSelect.value = newMachineY;
        }
    }
    
    // Fonction pour créer le graphique 3D
    function create3DChart() {
        const machineX = parseInt(machineXSelect.value);
        const machineY = parseInt(machineYSelect.value);
        
        // Extraire les données pour les deux machines sélectionnées
        const x = data.map(d => d.combination[machineX]);
        const y = data.map(d => d.combination[machineY]);
        const z = data.map(d => d.daily_profit);
        
        console.log('Données pour graphique 3D avec sélecteur:');
        console.log('Machine X:', machineNames[machineX], 'Ratios:', x);
        console.log('Machine Y:', machineNames[machineY], 'Ratios:', y);
        console.log('Profits Z:', z);
        
        // Créer les couleurs basées sur le profit (adaptées au thème sombre)
        const minProfit = Math.min(...z);
        const maxProfit = Math.max(...z);
        const colors = z.map(profit => {
            const normalized = (profit - minProfit) / (maxProfit - minProfit);
            // Utiliser des couleurs plus vives qui ressortent sur fond sombre
            if (normalized > 0.8) {
                return '#00ff88'; // Vert vif pour les profits élevés
            } else if (normalized > 0.6) {
                return '#ffff00'; // Jaune pour les profits moyens
            } else if (normalized > 0.4) {
                return '#ff8800'; // Orange pour les profits faibles
            } else {
                return '#ff4444'; // Rouge pour les pertes
            }
        });
        
        // Créer les textes pour les tooltips
        const texts = data.map((d, i) => {
            let tooltip = `Ratio ${machineNames[machineX]}: ${d.combination[machineX]}<br>`;
            tooltip += `Ratio ${machineNames[machineY]}: ${d.combination[machineY]}<br>`;
            tooltip += `Profit: $${d.daily_profit.toFixed(2)}/jour<br>`;
            tooltip += `Hashrate: ${d.total_hashrate.toFixed(2)} TH/s<br>`;
            tooltip += `Puissance: ${d.total_power}W`;
            return tooltip;
        });
        
        // Utiliser la fonction commune pour créer le graphique
        createCommon3DChart(chartContainer, x, y, z, colors, texts, result, data, machineNames[machineX], machineNames[machineY]);
    }
    
    // Ajouter les événements pour les sélecteurs
    machineXSelect.addEventListener('change', function() {
        adjustSecondMachineSelection();
        create3DChart();
    });
    machineYSelect.addEventListener('change', function() {
        adjustSecondMachineSelection();
        create3DChart();
    });
    
    // Créer le premier graphique
    create3DChart();
}
// Update Multi-Optimal Display
function updateMultiOptimalDisplay(multiOptimal) {
    
    const card = document.getElementById('siteSummaryCard');
    const title = document.getElementById('siteSummaryTitle');
    const tbody = document.getElementById('siteSummaryTableBody');
    const tfoot = document.getElementById('siteSummaryTableFooter');
    
    if (!card || !title || !tbody || !tfoot) {
        console.error('Some elements not found');
        return;
    }
    
    // Afficher la carte
    card.style.display = 'block';
    title.textContent = `Optimisation Multi-Machines: ${multiOptimal.site_name}`;
    
    // Vider le tableau
    tbody.innerHTML = '';
    tfoot.innerHTML = '';
    
    if (multiOptimal.machines.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Aucune machine dans ce site</td></tr>';
        return;
    }
    
    // Remplir le tableau avec les machines optimisées
    multiOptimal.machines.forEach(machine => {
        // Déterminer l'affichage du ratio actuel
        let currentRatioDisplay = 'N/A';
        let currentRatioClass = '';
        
        if (machine.current_ratio !== null && machine.current_ratio !== undefined) {
            currentRatioDisplay = machine.current_ratio.toFixed(3);
            
            // Logique d'affichage des icônes multiples
            let icons = [];
            
            // Toujours l'icône nominal si ratio = 1.0
            if (machine.current_ratio === 1.0) {
                icons.push('<i class="fas fa-undo text-muted" title="Ratio nominal"></i>');
                currentRatioClass = 'text-muted';
            }
            
            // Si ratio actuel = ratio optimal calculé → Ajouter icône optimal
            if (machine.optimal_ratio && Math.abs(machine.current_ratio - machine.optimal_ratio) < 0.01) {
                icons.push('<i class="fas fa-cog text-info" title="Ratio optimal"></i>');
                if (machine.current_ratio !== 1.0) {
                    currentRatioClass = 'text-info';
                }
            }
            
            // Si ratio_type = 'optimal' ET ratio différent → Ajouter icône d'alerte
            if (machine.ratio_type === 'optimal' && 
                machine.optimal_ratio && 
                Math.abs(machine.current_ratio - machine.optimal_ratio) > 0.01) {
                icons.push('<i class="fas fa-exclamation-triangle text-warning" title="Ratio optimal a changé"></i>');
                currentRatioClass = 'text-warning';
            }
            
            // Si ratio_type = 'manual' et pas d'autres icônes
            if (machine.ratio_type === 'manual' && icons.length === 0) {
                icons.push('<i class="fas fa-hand-paper text-warning" title="Ratio manuel"></i>');
                currentRatioClass = 'text-warning';
            }
            
            // Ajouter les icônes au display
            currentRatioDisplay += ' ' + icons.join(' ');
        }
        
        const row = `
            <tr>
                <td>${machine.name}</td>
                <td>${machine.optimal_hashrate.toFixed(2)} TH/s</td>
                <td>${Math.round(machine.optimal_power)}W</td>
                <td>$${machine.daily_revenue.toFixed(2)}</td>
                <td>$${machine.daily_cost.toFixed(2)}</td>
                <td class="${machine.daily_profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${machine.daily_profit.toFixed(2)}
                </td>
                <td>${machine.efficiency.toFixed(3)} TH/s/W</td>
                <td>${machine.optimal_ratio.toFixed(3)}</td>
                <td class="${currentRatioClass}">${currentRatioDisplay}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
    
    // Ajouter les totaux
    const footer = `
        <tr class="table-info">
            <td><strong>TOTAL OPTIMISÉ</strong></td>
            <td><strong>${multiOptimal.total_hashrate.toFixed(2)} TH/s</strong></td>
            <td><strong>${Math.round(multiOptimal.total_power)}W</strong></td>
            <td><strong>$${multiOptimal.total_revenue.toFixed(2)}</strong></td>
            <td><strong>$${multiOptimal.total_cost.toFixed(2)}</strong></td>
            <td class="${multiOptimal.total_profit >= 0 ? 'text-success' : 'text-danger'}">
                <strong>$${multiOptimal.total_profit.toFixed(2)}</strong>
            </td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
        <tr class="table-light">
            <td colspan="9" class="small text-muted">
                <i class="fas fa-info-circle"></i> 
                Optimisation séquentielle: Machines triées par efficacité (TH/s/W), 
                ratios optimaux calculés individuellement, paliers d'électricité appliqués dans l'ordre d'efficacité.
                Électricité: ${multiOptimal.electricity_tier1_rate}$/kWh (premier ${multiOptimal.electricity_tier1_limit}kWh), 
                ${multiOptimal.electricity_tier2_rate}$/kWh (reste).
            </td>
        </tr>
    `;
    tfoot.innerHTML = footer;
}

// Unified Chart Management Functions
function createChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`Canvas ${canvasId} not found`);
        return null;
    }
    
    // Destroy existing chart if it exists
    const existingChart = window[canvasId];
    if (existingChart && typeof existingChart.destroy === 'function') {
        existingChart.destroy();
    }
    
    // Create new chart
    const chart = new Chart(ctx, config);
    window[canvasId] = chart;
    
    return chart;
}

function destroyChart(canvasId) {
    const chart = window[canvasId];
    if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
        window[canvasId] = null;
    }
}

function updateChartData(canvasId, newData) {
    const chart = window[canvasId];
    if (chart) {
        chart.data = newData;
        chart.update();
    }
}

// Load Ratio Analysis Chart
async function loadRatioAnalysisChart(machineId) {
    try {
        // Déterminer le bon ID à utiliser
        let templateId = machineId;
        
        // Si c'est une instance, utiliser le template_id stocké dans les données
        if (currentObjectType === 'machine') {
            // Les données de l'objet contiennent le template_id
            templateId = currentObjectData?.template_id || machineId;
        }
        
        // Afficher l'état de chargement
        showRatioAnalysisLoading();
        
        const response = await fetch(`${API_BASE}/efficiency/machines/${templateId}/ratio-analysis`);
        
        if (!response.ok) {
            throw new Error(`Failed to load ratio analysis: ${response.status}`);
        }
        
        const data = await response.json();
        updateRatioAnalysisChart(data);
        
    } catch (error) {
        console.error('Error loading ratio analysis:', error);
        showNotification('Erreur lors du chargement de l\'analyse des ratios', 'error');
        
        // Afficher un état d'erreur dans le graphique
        const chart = window.ratioAnalysisChart;
        if (chart) {
            chart.data.labels = [];
            chart.data.datasets[0].data = [];
            chart.options.plugins.title.text = 'Profit vs Ratio - Erreur';
            chart.options.plugins.tooltip.callbacks.afterBody = function(context) {
                return ['Erreur de chargement'];
            };
            chart.update();
        }
    }
}

// Update Ratio Analysis Chart
function updateRatioAnalysisChart(data) {
    // Préparer les données pour le graphique
    const ratios = data.results.map(r => r.ratio);
    const profits = data.results.map(r => r.daily_profit);
    
    // Trouver le ratio optimal (profit maximum)
    const maxProfitIndex = profits.indexOf(Math.max(...profits));
    const optimalRatio = ratios[maxProfitIndex];
    
    // Mettre à jour les données du graphique existant
    const chart = window.ratioAnalysisChart;
    if (chart) {
        chart.data.labels = ratios;
        chart.data.datasets[0].data = profits;
        chart.options.plugins.title.text = `Profit vs Ratio - ${data.machine_model}`;
        chart.options.plugins.tooltip.callbacks.afterBody = function(context) {
            const dataIndex = context[0].dataIndex;
            const result = data.results[dataIndex];
            return [
                `Hashrate: ${result.hashrate.toFixed(1)} TH/s`,
                `Puissance: ${result.power}W`,
                `Efficacité: ${result.efficiency_th_per_watt} TH/s/W`
            ];
        };
        chart.update();
    }
}

// Show loading state for ratio analysis chart
function showRatioAnalysisLoading() {
    const chart = window.ratioAnalysisChart;
    if (chart) {
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.options.plugins.title.text = 'Profit vs Ratio - Chargement...';
        chart.options.plugins.tooltip.callbacks.afterBody = function(context) {
            return ['Chargement des données...'];
        };
        chart.update();
    }
}

// Load Site Statistics
async function loadSiteStatistics(siteId) {
    try {
        // Charger les statistiques du site
        const statsResponse = await fetch(`${API_BASE}/sites/${siteId}/statistics`);
        if (!statsResponse.ok) {
            throw new Error('Failed to load site statistics');
        }
        
        const stats = await statsResponse.json();
        
        // Charger les données du site
        const siteResponse = await fetch(`${API_BASE}/sites/${siteId}`);
        if (siteResponse.ok) {
            const siteData = await siteResponse.json();
            
            // Update site title
            const title = document.getElementById('selectedObjectTitle');
            if (title && siteData?.name) {
                title.textContent = `Site: ${siteData.name}`;
            }
            
            // Update site address
            const siteAddress = document.getElementById('siteAddress');
            if (siteAddress) {
                siteAddress.textContent = siteData?.address || 'Non spécifiée';
            }
            
            // Update electricity rates
            const siteTier1Rate = document.getElementById('siteTier1Rate');
            if (siteTier1Rate) {
                siteTier1Rate.textContent = siteData?.electricity_tier1_rate || '0';
            }
            
            const siteTier2Rate = document.getElementById('siteTier2Rate');
            if (siteTier2Rate) {
                siteTier2Rate.textContent = siteData?.electricity_tier2_rate || '0';
            }
            
            // Update currency
            const siteCurrency = document.getElementById('siteCurrency');
            if (siteCurrency) {
                siteCurrency.textContent = siteData?.preferred_currency || 'CAD';
            }
        }
        
        // Update site statistics
        const machineCount = document.getElementById('siteMachineCount');
        const totalHashrate = document.getElementById('siteTotalHashrate');
        
        if (machineCount) machineCount.textContent = `${stats.machines_count} machine(s)`;
        if (totalHashrate) totalHashrate.textContent = `${stats.total_hashrate} TH/s`;
        
    } catch (error) {
        console.error('Error loading site statistics:', error);
        showNotification('Erreur lors du chargement des statistiques du site', 'error');
    }
}

// Show/Hide Efficiency Section
function showEfficiencySection(show) {
    const chartsSection = document.getElementById('chartsSection');
    const optimizationSection = document.getElementById('optimizationSection');
    
    if (chartsSection) {
        chartsSection.style.display = show ? 'flex' : 'none';
    }
    
    if (optimizationSection) {
        optimizationSection.style.display = show ? 'flex' : 'none';
    }
    
    // Si on cache les sections, vider les données
    if (!show) {
        efficiencyData = [];
        updateEfficiencyTable();
        updateEfficiencyChart();
        updateOptimizationResults(null, 'economic');
        
        // Clear ratio analysis chart
        destroyChart('ratioAnalysisChart');
    }
}

// Load Efficiency Chart
async function loadEfficiencyChart(machineId) {
    try {
        let templateId = machineId;
        
        // Si c'est une instance, utiliser le template_id stocké dans les données
        if (currentObjectType === 'machine') {
            // Les données de l'objet contiennent le template_id
            templateId = currentObjectData?.template_id || machineId;
        }
        
        const response = await fetch(`${API_BASE}/efficiency/machines/${templateId}`);
        if (!response.ok) {
            // Si pas de données d'efficacité, afficher un message
            efficiencyData = [];
            updateEfficiencyTable();
            updateEfficiencyChart();
            showNotification('Aucune donnée d\'efficacité disponible pour cette machine', 'info');
            return;
        }
        
        efficiencyData = await response.json();
        updateEfficiencyTable();
        updateEfficiencyChart();
        
        // Calcul automatique de l'optimal si on a des données
        if (efficiencyData.length > 0) {
            await calculateOptimalAutomatically();
        }
        
    } catch (error) {
        console.error('Error loading efficiency chart:', error);
        efficiencyData = [];
        updateEfficiencyTable();
        updateEfficiencyChart();
        showNotification('Erreur lors du chargement des données d\'efficacité', 'error');
    }
}

// Load Efficiency Data (for backward compatibility)
async function loadEfficiencyData() {
    await loadEfficiencyChart(currentMachineId);
    
    // Load ratio analysis chart
    loadRatioAnalysisChart(currentMachineId);
}



// Update Efficiency Table
function updateEfficiencyTable() {
    const tbody = document.getElementById('efficiencyData');
    tbody.innerHTML = '';
    
    efficiencyData.forEach(item => {
        const ratio = ((item.power_consumption / 3250) * 100).toFixed(1);
        const row = `
            <tr>
                <td>${item.effective_hashrate}</td>
                <td>${Math.round(item.power_consumption)}W</td>
                <td>${ratio}%</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteDataPoint(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// Initialize Efficiency Chart
function initializeChart() {
    const config = {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Efficacité',
                data: [],
                backgroundColor: 'rgba(0, 123, 255, 0.6)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `TH/s: ${context.parsed.x}, Watt: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Hashrate (TH/s)'
                    },
                    grid: {
                        display: true
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Puissance (Watt)'
                    },
                    grid: {
                        display: true
                    }
                }
            }
        }
    };
    
    efficiencyChart = createChart('efficiencyChart', config);
}

// Initialize Ratio Analysis Chart
function initializeRatioAnalysisChart() {
    const config = {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Profit Quotidien ($)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Profit vs Ratio'
                },
                tooltip: {
                    callbacks: {
                        afterBody: function(context) {
                            return [
                                'Sélectionnez une machine pour voir les données'
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Ratio d\'Ajustement'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Montant ($/jour)'
                    }
                }
            }
        }
    };
    
    createChart('ratioAnalysisChart', config);
}

// Update Efficiency Chart
function updateEfficiencyChart() {
    const chartData = efficiencyData.map(item => ({
        x: parseFloat(item.effective_hashrate),
        y: item.power_consumption
    }));
    
    updateChartData('efficiencyChart', {
        datasets: [{
            label: 'Efficacité',
            data: chartData,
            backgroundColor: 'rgba(0, 123, 255, 0.6)',
            borderColor: 'rgba(0, 123, 255, 1)',
            borderWidth: 2,
            pointRadius: 6,
            pointHoverRadius: 8
        }]
    });
}

// Add Data Point Modal
function addDataPoint() {
    const modal = new bootstrap.Modal(document.getElementById('addDataModal'));
    modal.show();
}

// Save Data Point
async function saveDataPoint() {
    const hashrate = document.getElementById('hashrate').value;
    const power = document.getElementById('power').value;
    
    if (!hashrate || !power) {
        showNotification('Veuillez remplir tous les champs', 'error');
        return;
    }
    
    try {
        // Utiliser le template_id pour les instances de machines
        let templateId = currentMachineId;
        if (currentObjectType === 'machine') {
            templateId = currentObjectData?.template_id || currentMachineId;
        }
        
        const response = await fetch(`${API_BASE}/efficiency/curves`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                machine_id: templateId,
                effective_hashrate: parseFloat(hashrate),
                power_consumption: parseInt(power)
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de l\'ajout');
        }
        
        // Close modal and reload data
        bootstrap.Modal.getInstance(document.getElementById('addDataModal')).hide();
        document.getElementById('addDataForm').reset();
        
        await loadEfficiencyData();
        showNotification('Donnée ajoutée avec succès!', 'success');
        
        // Recalcul automatique de l'optimal
        await calculateOptimalAutomatically();
        
    } catch (error) {
        console.error('Error adding data point:', error);
        showNotification(error.message, 'error');
    }
}

// Delete Data Point
async function deleteDataPoint(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette donnée ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/efficiency/curves/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la suppression');
        }
        
        await loadEfficiencyData();
        showNotification('Donnée supprimée avec succès!', 'success');
        
        // Recalcul automatique de l'optimal
        await calculateOptimalAutomatically();
        
    } catch (error) {
        console.error('Error deleting data point:', error);
        showNotification(error.message, 'error');
    }
}

// Calculate Optimal Automatically (Economic)
async function calculateOptimalAutomatically() {
    await calculateOptimal('economic');
}

// Calculate Optimal (Economic or Technical)
async function calculateOptimal(type = 'economic') {
    const statusBadge = document.getElementById('optimizationStatus');
    
    try {
        // Afficher l'indicateur de calcul
        if (statusBadge) {
            statusBadge.style.display = 'inline';
            statusBadge.textContent = 'Calcul...';
            statusBadge.className = 'badge bg-warning';
        }
        
        // Utiliser le template_id pour les instances
        let templateId = currentMachineId;
        if (currentObjectType === 'machine') {
            templateId = currentObjectData?.template_id || currentMachineId;
        }
        
        // Choisir l'endpoint selon le type
        let endpoint;
        if (type === 'technical') {
            endpoint = 'optimal-efficiency';
        } else if (type === 'aggressive') {
            endpoint = 'optimal-sats';
        } else {
            endpoint = 'optimal-ratio';
        }
        const response = await fetch(`${API_BASE}/efficiency/machines/${templateId}/${endpoint}`);
        
        if (!response.ok) {
            throw new Error('Erreur lors du calcul de l\'optimal');
        }
        
        const result = await response.json();
        updateOptimizationResults(result, type);
        
        // Afficher l'indicateur de succès
        if (statusBadge) {
            let badgeText;
            if (type === 'technical') {
                badgeText = 'Tech';
            } else if (type === 'aggressive') {
                badgeText = 'Agg';
            } else {
                badgeText = 'Eco';
            }
            statusBadge.textContent = badgeText;
            statusBadge.className = 'badge bg-success';
            
            // Masquer après 3 secondes
            setTimeout(() => {
                statusBadge.style.display = 'none';
            }, 3000);
        }
        
    } catch (error) {
        console.error('Error calculating optimal:', error);
        
        // Afficher l'indicateur d'erreur
        if (statusBadge) {
            statusBadge.textContent = 'Erreur';
            statusBadge.className = 'badge bg-danger';
            
            // Masquer après 3 secondes
            setTimeout(() => {
                statusBadge.style.display = 'none';
            }, 3000);
        }
    }
}

// Find Optimal Ratio (manuel - gardé pour compatibilité)
async function findOptimal() {
    await calculateOptimalAutomatically();
    showNotification('Optimisation terminée!', 'success');
}

// Update Optimization Results
function updateOptimizationResults(data = null, type = 'economic') {
    if (data) {
        // Mettre à jour le type d'optimisation
        let typeText;
        if (type === 'technical') {
            typeText = 'Technique';
        } else if (type === 'aggressive') {
            typeText = 'Agressif';
        } else {
            typeText = 'Économique';
        }
        document.querySelector('.optimization-type').textContent = typeText;
        
        document.querySelector('.optimal-ratio').textContent = parseFloat(data.optimal_ratio).toFixed(2);
        
        // Update other values if available
        if (data.all_results && data.all_results.length > 0) {
            const optimal = data.all_results.find(r => r.adjustment_ratio === data.optimal_ratio);
            if (optimal) {
                document.querySelector('.optimal-hashrate').textContent = 
                    `${parseFloat(optimal.effective_hashrate).toFixed(2)} TH/s`;
                document.querySelector('.optimal-power').textContent = 
                    `${Math.round(optimal.power_consumption)}W`;
                
                // Afficher/masquer les éléments selon le type
                const efficiencyElement = document.querySelector('.result-item.efficiency');
                const profitElement = document.querySelector('.result-item.profit');
                
                if (type === 'technical') {
                    // Mode technique : afficher l'efficacité ET les données économiques
                    efficiencyElement.style.display = 'flex';
                    profitElement.style.display = 'flex';
                    document.querySelector('.result-item.revenue').style.display = 'flex';
                    document.querySelector('.result-item.cost').style.display = 'flex';
                    document.querySelector('.result-item.sats').style.display = 'flex';
                    
                    if (optimal.efficiency_th_per_watt) {
                        const efficiencyValue = `${(optimal.efficiency_th_per_watt * 1000).toFixed(3)} mTH/s/W`;
                        const efficiencySpan = document.querySelector('.optimal-efficiency');
                        if (efficiencySpan) {
                            efficiencySpan.textContent = efficiencyValue;
                        }
                    }
                    
                    // Afficher les données économiques dans le mode technique aussi
                    if (optimal.daily_revenue !== undefined && optimal.daily_revenue !== -1) {
                        document.querySelector('.optimal-revenue').textContent = 
                            `$${parseFloat(optimal.daily_revenue).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-revenue').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_electricity_cost !== undefined && optimal.daily_electricity_cost !== -1) {
                        document.querySelector('.optimal-cost').textContent = 
                            `$${parseFloat(optimal.daily_electricity_cost).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-cost').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_profit !== undefined && optimal.daily_profit !== -1) {
                        document.querySelector('.optimal-profit').textContent = 
                            `$${parseFloat(optimal.daily_profit).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-profit').textContent = 
                            `Données indisponibles`;
                    }
                    
                    // Afficher les sats/heure
                    if (optimal.sats_per_hour !== undefined && optimal.sats_per_hour !== -1) {
                        document.querySelector('.optimal-sats').textContent = 
                            `${optimal.sats_per_hour.toLocaleString()} sats/h`;
                    } else {
                        document.querySelector('.optimal-sats').textContent = 
                            `Données indisponibles`;
                    }
                } else if (type === 'aggressive') {
                    // Mode agressif : maximiser les sats/jour, afficher toutes les données
                    efficiencyElement.style.display = 'flex';
                    profitElement.style.display = 'flex';
                    document.querySelector('.result-item.revenue').style.display = 'flex';
                    document.querySelector('.result-item.cost').style.display = 'flex';
                    document.querySelector('.result-item.sats').style.display = 'flex';
                    
                    // Afficher l'efficacité
                    if (optimal.efficiency_th_per_watt) {
                        const efficiencyValue = `${(optimal.efficiency_th_per_watt * 1000).toFixed(3)} mTH/s/W`;
                        const efficiencySpan = document.querySelector('.optimal-efficiency');
                        if (efficiencySpan) {
                            efficiencySpan.textContent = efficiencyValue;
                        }
                    }
                    
                    // Afficher les données économiques (pour information, même si on maximise les sats)
                    if (optimal.daily_revenue !== undefined && optimal.daily_revenue !== -1) {
                        document.querySelector('.optimal-revenue').textContent = 
                            `$${parseFloat(optimal.daily_revenue).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-revenue').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_electricity_cost !== undefined && optimal.daily_electricity_cost !== -1) {
                        document.querySelector('.optimal-cost').textContent = 
                            `$${parseFloat(optimal.daily_electricity_cost).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-cost').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_profit !== undefined && optimal.daily_profit !== -1) {
                        document.querySelector('.optimal-profit').textContent = 
                            `$${parseFloat(optimal.daily_profit).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-profit').textContent = 
                            `Données indisponibles`;
                    }
                    
                    // Afficher les sats/heure (priorité dans ce mode)
                    if (optimal.sats_per_hour !== undefined && optimal.sats_per_hour !== -1) {
                        document.querySelector('.optimal-sats').textContent = 
                            `${optimal.sats_per_hour.toLocaleString()} sats/h`;
                    } else {
                        document.querySelector('.optimal-sats').textContent = 
                            `Données indisponibles`;
                    }
                } else {
                    // Mode économique : afficher les 3 prix ET l'efficacité
                    efficiencyElement.style.display = 'flex';
                    profitElement.style.display = 'flex';
                    document.querySelector('.result-item.revenue').style.display = 'flex';
                    document.querySelector('.result-item.cost').style.display = 'flex';
                    document.querySelector('.result-item.sats').style.display = 'flex';
                    
                    if (optimal.daily_revenue !== undefined && optimal.daily_revenue !== -1) {
                        document.querySelector('.optimal-revenue').textContent = 
                            `$${parseFloat(optimal.daily_revenue).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-revenue').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_electricity_cost !== undefined && optimal.daily_electricity_cost !== -1) {
                        document.querySelector('.optimal-cost').textContent = 
                            `$${parseFloat(optimal.daily_electricity_cost).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-cost').textContent = 
                            `Données indisponibles`;
                    }
                    if (optimal.daily_profit !== undefined && optimal.daily_profit !== -1) {
                        document.querySelector('.optimal-profit').textContent = 
                            `$${parseFloat(optimal.daily_profit).toFixed(2)}`;
                    } else {
                        document.querySelector('.optimal-profit').textContent = 
                            `Données indisponibles`;
                    }
                    
                    // Afficher les sats/heure
                    if (optimal.sats_per_hour !== undefined && optimal.sats_per_hour !== -1) {
                        document.querySelector('.optimal-sats').textContent = 
                            `${optimal.sats_per_hour.toLocaleString()} sats/h`;
                    } else {
                        document.querySelector('.optimal-sats').textContent = 
                            `Données indisponibles`;
                    }
                    
                    // Afficher l'efficacité dans le mode économique aussi
                    if (optimal.efficiency_th_per_watt) {
                        const efficiencyValue = `${(optimal.efficiency_th_per_watt * 1000).toFixed(3)} mTH/s/W`;
                        const efficiencySpan = document.querySelector('.optimal-efficiency');
                        if (efficiencySpan) {
                            efficiencySpan.textContent = efficiencyValue;
                        }
                    }
                }
            }
        }
    }
}

// Notification System
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Test API Connection
async function testAPIConnection() {
    try {
        const response = await fetch(`${API_BASE}/machines`);
        if (response.ok) {
            return true;
        }
    } catch (error) {
        console.error('API connection failed:', error);
        showNotification('Impossible de se connecter à l\'API', 'error');
        return false;
    }
}

// Load Market Data
async function loadMarketData() {
    try {
        const response = await fetch(`${API_BASE}/market/current`);
        if (!response.ok) {
            throw new Error('Failed to load market data');
        }
        
        const result = await response.json();
        updateMarketDataDisplay(result.data);
        
    } catch (error) {
        console.error('Error loading market data:', error);
        updateMarketDataDisplay({
            bitcoin_price_cad: null,
            fpps_sats: null
        });
    }
}

// Update Market Data Display
function updateMarketDataDisplay(data) {
    // Prix Bitcoin
    const bitcoinElement = document.getElementById('bitcoinPrice');
    if (bitcoinElement) {
        if (data.bitcoin_price_cad) {
            bitcoinElement.innerHTML = `$${data.bitcoin_price_cad.toLocaleString('fr-CA')} CAD`;
        } else {
            bitcoinElement.innerHTML = '<span class="text-danger">Erreur</span>';
        }
    }
    
    // FPPS
    const fppsElement = document.getElementById('fppsData');
    if (fppsElement) {
        if (data.fpps_sats) {
            fppsElement.innerHTML = `${data.fpps_sats.toLocaleString()} sats`;
        } else {
            fppsElement.innerHTML = '<span class="text-danger">Erreur</span>';
        }
    }
    
    // Dernière mise à jour
    const updateElement = document.getElementById('lastUpdate');
    if (updateElement) {
        const now = new Date();
        const formattedDate = now.toISOString().slice(0, 19).replace('T', ' ');
        updateElement.innerHTML = formattedDate;
    }
    
    // Recharger le graphique d'analyse des ratios si une machine est sélectionnée
    // (car le prix Bitcoin et FPPS affectent les calculs)
    if (currentMachineId && (currentObjectType === 'machine' || currentObjectType === 'template')) {
        const templateId = currentObjectData?.template_id || currentMachineId;
        loadRatioAnalysisChart(templateId);
    }
}

// Cache Management Functions
async function clearMarketCache() {
    try {
        const response = await fetch(`${API_BASE}/market/cache/clear`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Cache vidé avec succès! Les données seront rechargées au prochain appel.', 'success');
            
            // Recharger les données de marché
            await loadMarketData();
            
            // Recharger le graphique d'analyse des ratios si une machine est sélectionnée
            if (currentMachineId && (currentObjectType === 'machine' || currentObjectType === 'template')) {
                const templateId = currentObjectData?.template_id || currentMachineId;
                loadRatioAnalysisChart(templateId);
            }
        } else {
            throw new Error('Erreur lors du vidage du cache');
        }
    } catch (error) {
        console.error('Error clearing cache:', error);
        showNotification('Erreur lors du vidage du cache', 'error');
    }
}

async function getCacheStatus() {
    try {
        const response = await fetch(`${API_BASE}/market/cache/status`);
        
        if (response.ok) {
            const result = await response.json();
            const statusElement = document.getElementById('cacheStatus');
            
            if (result.cache_info && result.cache_info.length > 0) {
                let statusText = '';
                result.cache_info.forEach(item => {
                    const age = item.age_minutes !== null ? `${item.age_minutes.toFixed(1)} min` : 'N/A';
                    statusText += `${item.key}: ${age} | `;
                });
                statusElement.textContent = statusText.slice(0, -3); // Enlever le dernier " | "
                statusElement.className = 'ms-2 badge bg-info';
            } else {
                statusElement.textContent = 'Cache vide';
                statusElement.className = 'ms-2 badge bg-warning';
            }
        } else {
            throw new Error('Erreur lors de la récupération du statut');
        }
    } catch (error) {
        console.error('Error getting cache status:', error);
        showNotification('Erreur lors de la récupération du statut du cache', 'error');
    }
}

// Configuration Functions
function openConfiguration() {
    const modal = new bootstrap.Modal(document.getElementById('configModal'));
    loadConfiguration();
    getCacheStatus(); // Charger le statut du cache
    modal.show();
    
    // Ajouter un listener pour recalculer l'optimisation quand le modal se ferme
    const modalElement = document.getElementById('configModal');
    modalElement.addEventListener('hidden.bs.modal', function () {
        // Recalculer l'optimisation quand on ferme la configuration
        if (currentMachineId) {
            setTimeout(() => {
                calculateOptimalAutomatically();
            }, 1000); // Petit délai pour laisser le temps à la config de se sauvegarder
        }
    });
}

async function loadConfiguration() {
    try {
        console.log('Chargement de la configuration...');
        
        // Charger la configuration depuis l'API
        const response = await fetch(`${API_BASE}/config/app/settings`);
        const data = await response.json();
        
        console.log('Données reçues:', data);
        console.log('Settings:', data.settings);
        
        // Remplir les champs avec les valeurs de la DB (configuration globale)
        if (data.settings.braiins_token) {
            console.log('Setting braiins_token:', data.settings.braiins_token);
            document.getElementById('braiinsToken').value = data.settings.braiins_token;
        }
        if (data.settings.preferred_currency) {
            console.log('Setting preferred_currency:', data.settings.preferred_currency);
            document.getElementById('preferredCurrency').value = data.settings.preferred_currency;
        }
        if (data.settings.electricity_tier1_rate) {
            console.log('Setting electricity_tier1_rate:', data.settings.electricity_tier1_rate);
            document.getElementById('electricityTier1Rate').value = data.settings.electricity_tier1_rate;
        }
        if (data.settings.electricity_tier1_limit) {
            console.log('Setting electricity_tier1_limit:', data.settings.electricity_tier1_limit);
            document.getElementById('electricityTier1Limit').value = data.settings.electricity_tier1_limit;
        }
        if (data.settings.electricity_tier2_rate) {
            console.log('Setting electricity_tier2_rate:', data.settings.electricity_tier2_rate);
            document.getElementById('electricityTier2Rate').value = data.settings.electricity_tier2_rate;
        }
        
        console.log('Configuration chargée avec succès');
    } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
        showNotification(error.message, 'error');
        // Fermer le modal en cas d'erreur
        const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
        if (modal) {
            modal.hide();
        }
    }
}

async function saveConfiguration() {
    try {
        const config = {
            braiins_token: document.getElementById('braiinsToken').value,
            electricity_tier1_rate: parseFloat(document.getElementById('electricityTier1Rate').value),
            electricity_tier1_limit: parseInt(document.getElementById('electricityTier1Limit').value),
            electricity_tier2_rate: parseFloat(document.getElementById('electricityTier2Rate').value),
            preferred_currency: document.getElementById('preferredCurrency').value
        };
        
        // Sauvegarder la configuration globale
        const response = await fetch(`${API_BASE}/config/app/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la sauvegarde de la configuration globale');
        }
        
        // Fermer le modal
        bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        showNotification('Configuration sauvegardée!', 'success');
        
        // Recharger les données de marché avec la nouvelle configuration
        loadMarketData();
        
        // Recalculer l'optimisation avec la nouvelle configuration
        if (currentMachineId) {
            await calculateOptimalAutomatically();
        }
        
        // Recharger le graphique d'analyse des ratios si une machine est sélectionnée
        if (currentMachineId && (currentObjectType === 'machine' || currentObjectType === 'template')) {
            const templateId = currentObjectData?.template_id || currentMachineId;
            loadRatioAnalysisChart(templateId);
        }
        
        // Recharger le résumé du site si un site est sélectionné
        if (currentSiteId) {
            loadSiteSummary(currentSiteId);
        }
        
    } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error);
        showNotification('Erreur lors de la sauvegarde de la configuration', 'error');
    }
}

async function testBraiinsToken() {
    const token = document.getElementById('braiinsToken').value;
    
    if (!token) {
        showNotification('Veuillez entrer un token', 'error');
        return;
    }
    
    try {
        showNotification('Test de connexion en cours...', 'info');
        
        // Tester la connexion avec l'API Braiins
        const response = await fetch(`${API_BASE}/config/test-braiins?token=${encodeURIComponent(token)}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(`Connexion réussie! FPPS: ${result.fpps_sats} sats`, 'success');
        } else {
            showNotification(`Erreur: ${result.message}`, 'error');
        }
        
    } catch (error) {
        showNotification('Erreur de connexion: ' + error.message, 'error');
    }
}

// Initialize API connection test
testAPIConnection();

// Sites Management

// Load Sites and Machines Tree
async function loadSitesAndMachines(autoSelectFirst = true) {
    try {
        // Load sites
        const sitesResponse = await fetch(`${API_BASE}/sites`);
        if (!sitesResponse.ok) {
            throw new Error('Failed to load sites');
        }
        const sites = await sitesResponse.json();
        
        // Load machine templates
        const templatesResponse = await fetch(`${API_BASE}/machine-templates`);
        if (!templatesResponse.ok) {
            throw new Error('Failed to load machine templates');
        }
        const templates = await templatesResponse.json();
        
        // Load site machine instances for each site
        const siteInstances = {};
        for (const site of sites) {
            const instancesResponse = await fetch(`${API_BASE}/sites/${site.id}/machine-instances`);
            if (instancesResponse.ok) {
                siteInstances[site.id] = await instancesResponse.json();
            } else {
                siteInstances[site.id] = [];
            }
        }
        
        updateSitesMachinesTree(sites, templates, siteInstances);
        
            // Sélectionner automatiquement le premier site seulement si demandé et si aucun objet n'est sélectionné
    if (autoSelectFirst && sites.length > 0 && !currentObjectType) {
        const firstSite = sites[0];
        selectObject('site', firstSite.id, firstSite);
    }
        
    } catch (error) {
        console.error('Error loading sites and machines:', error);
        showNotification('Erreur lors du chargement des sites et machines', 'error');
    }
}

// Update Sites and Machines Tree
function updateSitesMachinesTree(sites, templates, siteInstances) {
    const tree = document.getElementById('sitesMachinesTree');
    if (!tree) {
        console.error('sitesMachinesTree element not found');
        return;
    }
    
    let html = '';
    
    // Render sites with their machine instances
    sites.forEach(site => {
        const instances = siteInstances[site.id] || [];
        const instancesWithTemplates = instances.map(instance => {
            const template = templates.find(t => t.id === instance.template_id);
            return {
                ...instance,
                template: template
            };
        }).filter(instance => instance.template); // Only show instances with valid templates
        
        html += `
            <div class="site-group">
                <div class="site-header" data-site-id="${site.id}" onclick="selectObject('site', ${site.id}, ${JSON.stringify(site).replace(/"/g, '&quot;')})">
                    <div class="site-name">
                        <i class="fas fa-building"></i>
                        ${site.name}
                        <span class="site-toggle" id="toggle-${site.id}">▼</span>
                    </div>
                    <div class="site-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="addMachineToSite(${site.id})" title="Ajouter machine">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="openSiteModal(${site.id})" title="Modifier site">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteSite(${site.id})" title="Supprimer site">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="site-machines" id="machines-${site.id}">
                    ${instancesWithTemplates.map(instance => `
                        <div class="machine-item" data-machine-id="${instance.id}" onclick="selectObject('machine', ${instance.id}, ${JSON.stringify({...instance.template, template_id: instance.template_id, instance_id: instance.id}).replace(/"/g, '&quot;')})">
                            <div class="machine-icon">⚡</div>
                            <div class="machine-info">
                                <div class="machine-name">
                                    ${instance.custom_name || instance.template.model}
                                    ${instance.quantity > 1 ? ` (${instance.quantity}x)` : ''}
                                </div>
                                <div class="machine-specs">
                                    ${instance.template.power_nominal}W • ${instance.template.hashrate_nominal} TH/s
                                </div>
                            </div>
                            <div class="machine-actions">
                                <button class="btn btn-sm btn-outline-secondary" onclick="editMachineInstance(${site.id}, ${instance.id})" title="Modifier">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="removeMachineInstance(${site.id}, ${instance.id})" title="Supprimer">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                    ${instancesWithTemplates.length === 0 ? `
                        <div class="no-machines">
                            <i class="fas fa-info-circle"></i>
                            Aucune machine dans ce site
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    // Render available templates
    html += `
        <div class="templates-section">
            <div class="templates-header">
                <i class="fas fa-layer-group"></i> Templates disponibles
            </div>
            ${templates.map(template => `
                <div class="template-item" data-template-id="${template.id}" onclick="selectObject('template', ${template.id}, ${JSON.stringify(template).replace(/"/g, '&quot;')})">
                    <div class="machine-icon">⚡</div>
                    <div class="machine-info">
                        <div class="machine-name">${template.model}</div>
                        <div class="machine-specs">${template.power_nominal}W • ${template.hashrate_nominal} TH/s</div>
                    </div>
                    <div class="machine-actions">
                        <button class="btn btn-sm btn-outline-secondary" onclick="openTemplateModal(${template.id})" title="Modifier template">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteTemplate(${template.id})" title="Supprimer template">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    tree.innerHTML = html;
}

// Toggle Site
function toggleSite(siteId) {
    const machinesDiv = document.getElementById(`machines-${siteId}`);
    const toggleSpan = document.getElementById(`toggle-${siteId}`);
    
    if (machinesDiv.classList.contains('collapsed')) {
        machinesDiv.classList.remove('collapsed');
        toggleSpan.textContent = '▼';
    } else {
        machinesDiv.classList.add('collapsed');
        toggleSpan.textContent = '▶';
    }
}

// Open Site Modal
async function openSiteModal(siteId = null) {
    currentSiteId = siteId;
    const modal = new bootstrap.Modal(document.getElementById('siteModal'));
    
    if (siteId) {
        // Edit mode - load site data
        await loadSiteData(siteId);
    } else {
        // Add mode - clear form and set default values from global config
        document.getElementById('siteForm').reset();
        await setDefaultValuesFromConfig();
    }
    
    modal.show();
}

// Load Site Data
async function loadSiteData(siteId) {
    try {
        console.log('Chargement des données du site:', siteId);
        
        const response = await fetch(`${API_BASE}/sites/${siteId}`);
        if (!response.ok) {
            throw new Error('Failed to load site');
        }
        
        const site = await response.json();
        console.log('Données du site reçues:', site);
        
        const siteNameField = document.getElementById('siteName');
        const siteAddressField = document.getElementById('siteAddress');
        const siteBraiinsTokenField = document.getElementById('siteBraiinsToken');
        const siteTier1RateField = document.getElementById('siteModalTier1Rate');
        const siteTier1LimitField = document.getElementById('siteModalTier1Limit');
        const siteTier2RateField = document.getElementById('siteModalTier2Rate');
        const siteCurrencyField = document.getElementById('siteCurrency');
        
        console.log('Champs trouvés:', {
            siteName: !!siteNameField,
            siteAddress: !!siteAddressField,
            siteBraiinsToken: !!siteBraiinsTokenField,
            siteTier1Rate: !!siteTier1RateField,
            siteTier1Limit: !!siteTier1LimitField,
            siteTier2Rate: !!siteTier2RateField,
            siteCurrency: !!siteCurrencyField
        });
        
        if (siteNameField) siteNameField.value = site.name;
        if (siteAddressField) siteAddressField.value = site.address || '';
        if (siteBraiinsTokenField) siteBraiinsTokenField.value = site.braiins_token || '';
        if (siteTier1RateField) siteTier1RateField.value = site.electricity_tier1_rate;
        if (siteTier1LimitField) siteTier1LimitField.value = site.electricity_tier1_limit;
        if (siteTier2RateField) siteTier2RateField.value = site.electricity_tier2_rate;
        if (siteCurrencyField) siteCurrencyField.value = site.preferred_currency;
        
        // Vérifier les valeurs des champs après assignation
        console.log('Valeurs des champs après assignation:', {
            siteName: siteNameField?.value,
            siteAddress: siteAddressField?.value,
            siteBraiinsToken: siteBraiinsTokenField?.value,
            siteTier1Rate: siteTier1RateField?.value,
            siteTier1Limit: siteTier1LimitField?.value,
            siteTier2Rate: siteTier2RateField?.value,
            siteCurrency: siteCurrencyField?.value
        });
        
        console.log('Valeurs assignées:', {
            name: site.name,
            address: site.address,
            braiins_token: site.braiins_token,
            electricity_tier1_rate: site.electricity_tier1_rate,
            electricity_tier1_limit: site.electricity_tier1_limit,
            electricity_tier2_rate: site.electricity_tier2_rate,
            preferred_currency: site.preferred_currency
        });
        
        console.log('Champs remplis avec les valeurs du site');
        
    } catch (error) {
        console.error('Error loading site:', error);
        showNotification('Erreur lors du chargement du site', 'error');
    }
}

// Save Site
async function saveSite() {
    try {
        const siteData = {
            name: document.getElementById('siteName').value,
            address: document.getElementById('siteAddress').value,
            braiins_token: document.getElementById('siteBraiinsToken').value,
            electricity_tier1_rate: parseFloat(document.getElementById('siteModalTier1Rate').value),
            electricity_tier1_limit: parseInt(document.getElementById('siteModalTier1Limit').value),
            electricity_tier2_rate: parseFloat(document.getElementById('siteModalTier2Rate').value),
            preferred_currency: document.getElementById('siteCurrency').value
        };
        
        const url = currentSiteId 
            ? `${API_BASE}/sites/${currentSiteId}`
            : `${API_BASE}/sites`;
        
        const method = currentSiteId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(siteData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save site');
        }
        
        // Close modal and reload sites
        bootstrap.Modal.getInstance(document.getElementById('siteModal')).hide();
        showNotification('Site sauvegardé avec succès!', 'success');
        loadSitesAndMachines();
        
    } catch (error) {
        console.error('Error saving site:', error);
        showNotification('Erreur lors de la sauvegarde du site', 'error');
    }
}

// Edit Site
function editSite(siteId) {
    openSiteModal(siteId);
}

// Delete Site
async function deleteSite(siteId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce site ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/sites/${siteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete site');
        }
        
        showNotification('Site supprimé avec succès!', 'success');
        loadSitesAndMachines();
        
    } catch (error) {
        console.error('Error deleting site:', error);
        showNotification('Erreur lors de la suppression du site', 'error');
    }
}

// Set Default Values From Global Config
async function setDefaultValuesFromConfig() {
    try {
        const response = await fetch(`${API_BASE}/config/app/settings`);
        if (!response.ok) {
            throw new Error('Failed to load global config');
        }
        
        const config = await response.json();
        
        // Set default values from global config settings
        if (config.settings) {
            if (config.settings.electricity_tier1_rate) {
                document.getElementById('siteTier1Rate').value = config.settings.electricity_tier1_rate;
            }
            if (config.settings.electricity_tier1_limit) {
                document.getElementById('siteTier1Limit').value = config.settings.electricity_tier1_limit;
            }
            if (config.settings.electricity_tier2_rate) {
                document.getElementById('siteTier2Rate').value = config.settings.electricity_tier2_rate;
            }
            if (config.settings.preferred_currency) {
                document.getElementById('siteCurrency').value = config.settings.preferred_currency;
            }
        }
        
    } catch (error) {
        console.error('Error loading global config for defaults:', error);
        // Keep default values if config loading fails
    }
} 

// Add Machine Instance to Site
async function addMachineToSite(siteId) {
    try {
        // Load available templates
        const templatesResponse = await fetch(`${API_BASE}/machine-templates`);
        if (!templatesResponse.ok) {
            throw new Error('Failed to load templates');
        }
        const templates = await templatesResponse.json();
        
        // Create modal for template selection
        const modalHtml = `
            <div class="modal fade" id="addMachineModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Ajouter une machine au site</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addMachineForm">
                                <div class="mb-3">
                                    <label class="form-label">Template de machine</label>
                                    <select class="form-control" id="templateSelect" required>
                                        <option value="">Sélectionner un template</option>
                                        ${templates.map(template => `
                                            <option value="${template.id}">${template.model} (${template.hashrate_nominal} TH/s, ${template.power_nominal}W)</option>
                                        `).join('')}
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Quantité</label>
                                    <input type="number" class="form-control" id="quantityInput" value="1" min="1" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Nom personnalisé (optionnel)</label>
                                    <input type="text" class="form-control" id="customNameInput" placeholder="Ex: S19 Pro #1">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Notes (optionnel)</label>
                                    <textarea class="form-control" id="notesInput" rows="2" placeholder="Notes sur cette instance"></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="saveMachineInstance(${siteId})">Ajouter</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('addMachineModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addMachineModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error opening add machine modal:', error);
        showNotification('Erreur lors de l\'ouverture du modal', 'error');
    }
}

// Save Machine Instance
async function saveMachineInstance(siteId) {
    try {
        const templateId = document.getElementById('templateSelect').value;
        const quantity = parseInt(document.getElementById('quantityInput').value);
        const customName = document.getElementById('customNameInput').value;
        const notes = document.getElementById('notesInput').value;
        
        if (!templateId) {
            showNotification('Veuillez sélectionner un template', 'error');
            return;
        }
        
        const instanceData = {
            template_id: parseInt(templateId),
            quantity: quantity,
            custom_name: customName || null,
            notes: notes || null
        };
        
        const response = await fetch(`${API_BASE}/sites/${siteId}/machine-instances`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instanceData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to add machine instance');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addMachineModal'));
        modal.hide();
        
        // Reload sites and machines
        await loadSitesAndMachines();
        
        showNotification('Machine ajoutée au site avec succès', 'success');
        
    } catch (error) {
        console.error('Error saving machine instance:', error);
        showNotification('Erreur lors de l\'ajout de la machine', 'error');
    }
}

// Edit Machine Instance
async function editMachineInstance(siteId, instanceId) {
    try {
        // Load instance data
        const response = await fetch(`${API_BASE}/sites/${siteId}/machine-instances`);
        if (!response.ok) {
            throw new Error('Failed to load instance data');
        }
        const instances = await response.json();
        const instance = instances.find(i => i.id === instanceId);
        
        if (!instance) {
            throw new Error('Instance not found');
        }
        
        // Load templates
        const templatesResponse = await fetch(`${API_BASE}/machine-templates`);
        if (!templatesResponse.ok) {
            throw new Error('Failed to load templates');
        }
        const templates = await templatesResponse.json();
        const template = templates.find(t => t.id === instance.template_id);
        
        // Create modal for editing
        const modalHtml = `
            <div class="modal fade" id="editMachineModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Modifier l'instance de machine</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editMachineForm">
                                <div class="mb-3">
                                    <label class="form-label">Template de machine</label>
                                    <input type="text" class="form-control" value="${template.model}" readonly>
                                    <small class="text-muted">Le template ne peut pas être modifié</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Quantité</label>
                                    <input type="number" class="form-control" id="editQuantityInput" value="${instance.quantity}" min="1" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Nom personnalisé (optionnel)</label>
                                    <input type="text" class="form-control" id="editCustomNameInput" value="${instance.custom_name || ''}" placeholder="Ex: S19 Pro #1">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Notes (optionnel)</label>
                                    <textarea class="form-control" id="editNotesInput" rows="2" placeholder="Notes sur cette instance">${instance.notes || ''}</textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="updateMachineInstance(${siteId}, ${instanceId})">Mettre à jour</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('editMachineModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editMachineModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error opening edit machine modal:', error);
        showNotification('Erreur lors de l\'ouverture du modal', 'error');
    }
}

// Update Machine Instance
async function updateMachineInstance(siteId, instanceId) {
    try {
        const quantity = parseInt(document.getElementById('editQuantityInput').value);
        const customName = document.getElementById('editCustomNameInput').value;
        const notes = document.getElementById('editNotesInput').value;
        
        const instanceData = {
            quantity: quantity,
            custom_name: customName || null,
            notes: notes || null
        };
        
        const response = await fetch(`${API_BASE}/sites/${siteId}/machine-instances/${instanceId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(instanceData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to update machine instance');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editMachineModal'));
        modal.hide();
        
        // Reload sites and machines
        await loadSitesAndMachines();
        
        showNotification('Instance mise à jour avec succès', 'success');
        
    } catch (error) {
        console.error('Error updating machine instance:', error);
        showNotification('Erreur lors de la mise à jour de l\'instance', 'error');
    }
}

// Remove Machine Instance
async function removeMachineInstance(siteId, instanceId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette instance de machine ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/sites/${siteId}/machine-instances/${instanceId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to remove machine instance');
        }
        
        // Reload sites and machines
        await loadSitesAndMachines();
        
        showNotification('Instance supprimée avec succès', 'success');
        
    } catch (error) {
        console.error('Error removing machine instance:', error);
        showNotification('Erreur lors de la suppression de l\'instance', 'error');
    }
}

// Template Management
let currentTemplateId = null;

function openTemplateModal(templateId = null) {
    currentTemplateId = templateId;
    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    const title = document.querySelector('#templateModal .modal-title');
    
    if (templateId) {
        title.textContent = 'Modifier Template de Machine';
        loadTemplateData(templateId);
    } else {
        title.textContent = 'Nouveau Template de Machine';
        clearTemplateForm();
    }
    
    modal.show();
}

function clearTemplateForm() {
    document.getElementById('templateModel').value = '';
    document.getElementById('templateManufacturer').value = '';
    document.getElementById('templateHashrate').value = '';
    document.getElementById('templatePower').value = '';
    document.getElementById('templateEfficiency').value = '';
    document.getElementById('templatePrice').value = '';
    document.getElementById('templateYear').value = '';
    document.getElementById('templateNotes').value = '';
}

async function loadTemplateData(templateId) {
    try {
        const response = await fetch(`${API_BASE}/machine-templates/${templateId}`);
        if (!response.ok) {
            throw new Error('Failed to load template data');
        }
        
        const template = await response.json();
        
        document.getElementById('templateModel').value = template.model;
        document.getElementById('templateManufacturer').value = template.manufacturer || '';
        document.getElementById('templateHashrate').value = template.hashrate_nominal;
        document.getElementById('templatePower').value = template.power_nominal;
        document.getElementById('templateEfficiency').value = template.efficiency_base;
        document.getElementById('templatePrice').value = template.price_cad || '';
        document.getElementById('templateYear').value = template.release_year || '';
        document.getElementById('templateNotes').value = template.notes || '';
        
    } catch (error) {
        console.error('Error loading template data:', error);
        showNotification('Erreur lors du chargement des données du template', 'error');
    }
}

async function saveTemplate() {
    const form = document.getElementById('templateForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const templateData = {
        model: document.getElementById('templateModel').value,
        manufacturer: document.getElementById('templateManufacturer').value,
        hashrate_nominal: parseFloat(document.getElementById('templateHashrate').value),
        power_nominal: parseInt(document.getElementById('templatePower').value),
        efficiency_base: parseFloat(document.getElementById('templateEfficiency').value),
        price_cad: document.getElementById('templatePrice').value ? parseFloat(document.getElementById('templatePrice').value) : null,
        release_year: document.getElementById('templateYear').value ? parseInt(document.getElementById('templateYear').value) : null,
        notes: document.getElementById('templateNotes').value
    };
    
    try {
        const url = currentTemplateId 
            ? `${API_BASE}/machine-templates/${currentTemplateId}`
            : `${API_BASE}/machine-templates`;
        
        const method = currentTemplateId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save template');
        }
        
        const template = await response.json();
        showNotification(
            currentTemplateId ? 'Template modifié avec succès' : 'Template créé avec succès', 
            'success'
        );
        
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('templateModal'));
        modal.hide();
        
        // Recharger les données
        loadSitesAndMachines();
        
    } catch (error) {
        console.error('Error saving template:', error);
        showNotification(`Erreur lors de la sauvegarde: ${error.message}`, 'error');
    }
}

async function deleteTemplate(templateId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce template ? Cette action ne peut pas être annulée.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/machine-templates/${templateId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete template');
        }
        
        showNotification('Template supprimé avec succès', 'success');
        loadSitesAndMachines(); // Recharger la liste
        
    } catch (error) {
        console.error('Error deleting template:', error);
        showNotification('Erreur lors de la suppression du template', 'error');
    }
}

// ===== BACKTEST FUNCTIONS =====

// Global variables for backtest
let backtestData = {
    phase: 1,
    isRunning: false,
    simulationData: null,
    results: null
};

// Show backtest section
function showBacktestSection() {
    // Hide main interface
    document.getElementById('chartsSection').style.display = 'none';
    document.getElementById('optimizationSection').style.display = 'none';
    document.getElementById('mainSidebar').style.display = 'none';
    
    // Hide market data bar in backtest
    const marketDataCard = document.querySelector('.market-data-card');
    if (marketDataCard) {
        marketDataCard.style.display = 'none';
    }
    
    // Hide selected object info in backtest
    const selectedObjectCard = document.getElementById('selectedObjectCard');
    if (selectedObjectCard) {
        selectedObjectCard.style.display = 'none';
    }
    
    // Hide site summary in backtest
    const siteSummaryCard = document.getElementById('siteSummaryCard');
    if (siteSummaryCard) {
        siteSummaryCard.style.display = 'none';
    }
    
    // Show backtest interface
    document.getElementById('backtestSection').style.display = 'block';
    document.getElementById('backtestSidebar').style.display = 'block';
    
    // Initialize configuration
    initializeBacktestConfiguration();
    
    // Initialize first phase
    switchBacktestPhase(1);
}

// Initialize Phase 1: Data Preparation
async function initializeBacktestPhase1() {
    try {
        // Check data availability
        await checkDataAvailability();
        
        // Set default dates for backtest
        const today = new Date();
        const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
        const oneYearFromNow = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate());
        
        // Force YYYY-MM-DD format for all date inputs
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.setAttribute('data-date-format', 'YYYY-MM-DD');
        });
        
        document.getElementById('backtestStartDate').value = oneYearAgo.toISOString().split('T')[0];
        document.getElementById('backtestEndDate').value = oneYearFromNow.toISOString().split('T')[0];
        
    } catch (error) {
        console.error('Error initializing backtest phase 1:', error);
    }
}

// Check data availability
async function checkDataAvailability() {
    const statusElements = {
        bitcoin: document.getElementById('bitcoinDataStatus'),
        fpps: document.getElementById('fppsDataStatus'),
        sites: document.getElementById('sitesDataStatus'),
        machines: document.getElementById('machinesDataStatus')
    };
    
    try {
        // Update phase 1 status to loading
        updatePhaseStatus(1, 'loading');
        
        // Check Bitcoin data
        const bitcoinResponse = await fetch(`${API_BASE}/bitcoin-prices/count`);
        const bitcoinCount = await bitcoinResponse.json();
        statusElements.bitcoin.innerHTML = bitcoinCount > 0 
            ? '<i class="fas fa-check"></i> Disponible' 
            : '<i class="fas fa-times"></i> Manquant';
        
        // Check FPPS data
        const fppsResponse = await fetch(`${API_BASE}/fpps-data/count`);
        const fppsCount = await fppsResponse.json();
        statusElements.fpps.innerHTML = fppsCount > 0 
            ? '<i class="fas fa-check"></i> Disponible' 
            : '<i class="fas fa-times"></i> Manquant';
        
        // Check sites
        const sitesResponse = await fetch(`${API_BASE}/sites`);
        const sites = await sitesResponse.json();
        statusElements.sites.innerHTML = sites.length > 0 
            ? `<i class="fas fa-check"></i> ${sites.length} site(s)` 
            : '<i class="fas fa-times"></i> Aucun site';
        
        // Check machines
        const machinesResponse = await fetch(`${API_BASE}/machine-templates`);
        const machines = await machinesResponse.json();
        statusElements.machines.innerHTML = machines.length > 0 
            ? `<i class="fas fa-check"></i> ${machines.length} machine(s)` 
            : '<i class="fas fa-times"></i> Aucune machine';
        
        // Check if all data is available
        const canProceed = bitcoinCount > 0 && fppsCount > 0 && sites.length > 0 && machines.length > 0;
        
        // Update phase 1 status
        updatePhaseStatus(1, canProceed ? 'success' : 'error');
        
        // Update phase 2 status
        if (canProceed) {
            updatePhaseStatus(2, 'locked'); // Ready to unlock
            showNotification('Toutes les données sont disponibles. Vous pouvez passer à la Phase 2.', 'success');
        } else {
            updatePhaseStatus(2, 'locked'); // Still locked
            showNotification('Certaines données sont manquantes. Veuillez les importer avant de continuer.', 'warning');
        }
        
    } catch (error) {
        console.error('Error checking data availability:', error);
        updatePhaseStatus(1, 'error');
        showNotification('Erreur lors de la vérification des données', 'error');
    }
}

// Import missing data
async function importMissingData() {
    try {
        showNotification('Import des données en cours...', 'info');
        
        // This would call API endpoints to import historical data
        // For now, we'll just show a notification
        setTimeout(() => {
            showNotification('Import terminé. Vérifiez les données.', 'success');
            checkDataAvailability();
        }, 2000);
        
    } catch (error) {
        console.error('Error importing data:', error);
        showNotification('Erreur lors de l\'import des données', 'error');
    }
}

// Start backtest
function startBacktest() {
    showBacktestSection();
    showNotification('Interface de backtest ouverte. Commencez par la Phase 1.', 'info');
}

// Initialize Phase 2: Configuration
function initializeBacktestPhase2() {
    // Load sites for selection
    loadSitesForBacktest();
}

// Load sites for backtest selection
async function loadSitesForBacktest() {
    try {
        const response = await fetch(`${API_BASE}/sites`);
        const sites = await response.json();
        
        const sitesSelection = document.getElementById('sitesSelection');
        sitesSelection.innerHTML = '';
        
        sites.forEach(site => {
            const siteDiv = document.createElement('div');
            siteDiv.className = 'form-check mb-2';
            siteDiv.innerHTML = `
                <input class="form-check-input" type="checkbox" value="${site.id}" id="site_${site.id}" checked>
                <label class="form-check-label" for="site_${site.id}">
                    <strong>${site.name}</strong> - ${site.address || 'Aucune adresse'}
                </label>
            `;
            sitesSelection.appendChild(siteDiv);
        });
        
    } catch (error) {
        console.error('Error loading sites for backtest:', error);
        showNotification('Erreur lors du chargement des sites', 'error');
    }
}

// Start simulation
async function startSimulation() {
    if (backtestData.isRunning) {
        return;
    }
    
    try {
        backtestData.isRunning = true;
        document.getElementById('startSimulationBtn').style.display = 'none';
        document.getElementById('pauseSimulationBtn').style.display = 'inline-block';
        
        // Get configuration
        const config = getBacktestConfiguration();
        
        // Start simulation
        await runSimulation(config);
        
    } catch (error) {
        console.error('Error starting simulation:', error);
        showNotification('Erreur lors du démarrage de la simulation', 'error');
        backtestData.isRunning = false;
        document.getElementById('startSimulationBtn').style.display = 'inline-block';
        document.getElementById('pauseSimulationBtn').style.display = 'none';
    }
}

// Pause simulation
function pauseSimulation() {
    backtestData.isRunning = false;
    document.getElementById('startSimulationBtn').style.display = 'inline-block';
    document.getElementById('pauseSimulationBtn').style.display = 'none';
    showNotification('Simulation en pause', 'info');
}

// Get backtest configuration
function getBacktestConfiguration() {
    return {
        startDate: document.getElementById('backtestStartDate').value,
        endDate: document.getElementById('backtestEndDate').value,
        paymentInterval: parseInt(document.getElementById('paymentInterval').value),
        roiPeriod: parseInt(document.getElementById('roiPeriod').value),
        initialAggressiveness: parseFloat(document.getElementById('initialAggressiveness').value),
        sd4YearWeight: parseFloat(document.getElementById('sd4YearWeight').value),
        sd1YearWeight: parseFloat(document.getElementById('sd1YearWeight').value),
        selectedSites: getSelectedSites()
    };
}

// Get selected sites
function getSelectedSites() {
    const checkboxes = document.querySelectorAll('#sitesSelection input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

// Run simulation
async function runSimulation(config) {
    try {
        showNotification('Simulation en cours...', 'info');
        
        // This would call the backend API to run the simulation
        // For now, we'll simulate the process
        
        const totalDays = Math.ceil((new Date(config.endDate) - new Date(config.startDate)) / (1000 * 60 * 60 * 24));
        let currentDay = 0;
        
        const progressBar = document.getElementById('simulationProgress');
        const currentDayElement = document.getElementById('currentDay');
        const cumulativeProfitElement = document.getElementById('cumulativeProfit');
        const currentAggressivenessElement = document.getElementById('currentAggressiveness');
        
        while (currentDay < totalDays && backtestData.isRunning) {
            // Simulate one day
            const progress = (currentDay / totalDays) * 100;
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${Math.round(progress)}%`;
            
            currentDayElement.textContent = `${currentDay + 1}/${totalDays}`;
            cumulativeProfitElement.textContent = `$${(currentDay * 10.5).toFixed(2)}`;
            currentAggressivenessElement.textContent = (1.0 + (currentDay * 0.001)).toFixed(3);
            
            currentDay++;
            
            // Small delay to show progress
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        if (backtestData.isRunning) {
            // Simulation completed
            backtestData.isRunning = false;
            document.getElementById('startSimulationBtn').style.display = 'inline-block';
            document.getElementById('pauseSimulationBtn').style.display = 'none';
            
            showNotification('Simulation terminée !', 'success');
            
            // Show results
            showBacktestResults();
        }
        
    } catch (error) {
        console.error('Error running simulation:', error);
        showNotification('Erreur lors de la simulation', 'error');
        backtestData.isRunning = false;
        document.getElementById('startSimulationBtn').style.display = 'inline-block';
        document.getElementById('pauseSimulationBtn').style.display = 'none';
    }
}

// Show backtest results
function showBacktestResults() {
    // Switch to phase 4
    const phase4Tab = document.getElementById('phase4-tab');
    const tab = new bootstrap.Tab(phase4Tab);
    tab.show();
    
    // Update results
    document.getElementById('totalProfit').textContent = '$3,847.50';
    document.getElementById('performanceRatio').textContent = '1.23';
    document.getElementById('effectiveROI').textContent = '12.8%';
    document.getElementById('paymentCycles').textContent = '4';
    
    showNotification('Résultats disponibles dans la Phase 4', 'success');
}

// Export results
function exportResults() {
    showNotification('Export des résultats...', 'info');
    // This would implement actual export functionality
}

// Show detailed analysis
function showDetailedAnalysis() {
    showNotification('Analyse détaillée...', 'info');
    // This would show detailed analysis modal
}



async function loadAvailableRatios(siteId) {
    try {
        const response = await fetch(`${API_BASE}/sites/${siteId}/available-ratios`);
        if (!response.ok) {
            throw new Error('Failed to load available ratios');
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading available ratios:', error);
        return null;
    }
}

async function applyManualRatio() {
    try {
        if (!currentSiteId) {
            showNotification('Aucun site sélectionné', 'error');
            return;
        }

        // Charger les ratios disponibles
        const availableRatios = await loadAvailableRatios(currentSiteId);
        if (!availableRatios || !availableRatios.common_ratios || availableRatios.common_ratios.length === 0) {
            showNotification('Impossible de charger les ratios disponibles', 'error');
            return;
        }

        // Créer un modal avec slider
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'ratioSliderModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Sélectionner un ratio manuel</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Ratios disponibles pour toutes les machines du site <strong>${availableRatios.site_name}</strong>:</p>
                        <div class="alert alert-secondary mb-3">
                            <small>
                                <strong>Ratio actuel:</strong> ${(availableRatios.current_ratio * 100).toFixed(0)}% 
                                (${availableRatios.current_ratio_type === 'manual' ? 'Manuel' : availableRatios.current_ratio_type === 'optimal' ? 'Optimal' : 'Nominal'})
                            </small>
                        </div>
                        <div class="mb-3">
                            <label for="ratioSlider" class="form-label">
                                Ratio: <span id="ratioValue">${availableRatios.current_ratio.toFixed(2)}</span> (${Math.round(availableRatios.current_ratio * 100)}%)
                            </label>
                            <input type="range" class="form-range" id="ratioSlider" 
                                   min="${availableRatios.min_common_ratio}" 
                                   max="${availableRatios.max_common_ratio}" 
                                   step="0.05" value="${availableRatios.current_ratio}">
                            <div class="d-flex justify-content-between">
                                <small>${(availableRatios.min_common_ratio * 100).toFixed(0)}%</small>
                                <small>${(availableRatios.max_common_ratio * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                        <div class="alert alert-info">
                            <small>
                                <strong>Plage de ratios disponibles:</strong> ${(availableRatios.min_common_ratio * 100).toFixed(0)}% à ${(availableRatios.max_common_ratio * 100).toFixed(0)}%
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" onclick="confirmManualRatio()">Appliquer</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Configurer le slider
        const slider = modal.querySelector('#ratioSlider');
        const ratioValue = modal.querySelector('#ratioValue');
        
        slider.addEventListener('input', function() {
            const value = parseFloat(this.value);
            ratioValue.textContent = value.toFixed(2);
            ratioValue.nextSibling.textContent = ` (${Math.round(value * 100)}%)`;
        });

        // Afficher le modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Nettoyer le modal après fermeture
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });

    } catch (error) {
        console.error('Error showing ratio slider:', error);
        showNotification('Erreur lors du chargement des ratios disponibles', 'error');
    }
}

async function editMachineRatio(instanceId) {
    try {
        if (!currentSiteId) {
            showNotification('Aucun site sélectionné', 'error');
            return;
        }

        // Charger les ratios disponibles pour cette machine spécifique
        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/machines/${instanceId}/available-ratios`);
        if (!response.ok) {
            throw new Error('Failed to load available ratios for machine');
        }
        const availableRatios = await response.json();

        // Créer un modal avec slider pour cette machine
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'machineRatioSliderModal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Modifier le ratio de la machine</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Ratios disponibles pour <strong>${availableRatios.machine_model}</strong>:</p>
                        <div class="alert alert-secondary mb-3">
                            <small>
                                <strong>Ratio actuel:</strong> ${(availableRatios.current_ratio * 100).toFixed(0)}% 
                                (${availableRatios.current_ratio_type === 'manual' ? 'Manuel' : availableRatios.current_ratio_type === 'optimal' ? 'Optimal' : 'Nominal'})
                            </small>
                        </div>
                        <div class="mb-3">
                            <label for="machineRatioSlider" class="form-label">
                                Ratio: <span id="machineRatioValue">${availableRatios.current_ratio.toFixed(2)}</span> (${Math.round(availableRatios.current_ratio * 100)}%)
                            </label>
                            <input type="range" class="form-range" id="machineRatioSlider" 
                                   min="${availableRatios.min_ratio}" 
                                   max="${availableRatios.max_ratio}" 
                                   step="0.05" value="${availableRatios.current_ratio}">
                            <div class="d-flex justify-content-between">
                                <small>${(availableRatios.min_ratio * 100).toFixed(0)}%</small>
                                <small>${(availableRatios.max_ratio * 100).toFixed(0)}%</small>
                            </div>
                        </div>
                        <div class="alert alert-info">
                            <small>
                                <strong>Plage de ratios disponibles:</strong> ${(availableRatios.min_ratio * 100).toFixed(0)}% à ${(availableRatios.max_ratio * 100).toFixed(0)}%
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                        <button type="button" class="btn btn-primary" onclick="confirmMachineRatio(${instanceId})">Appliquer</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Configurer le slider
        const slider = modal.querySelector('#machineRatioSlider');
        const ratioValue = modal.querySelector('#machineRatioValue');
        
        slider.addEventListener('input', function() {
            const value = parseFloat(this.value);
            ratioValue.textContent = value.toFixed(2);
            ratioValue.nextSibling.textContent = ` (${Math.round(value * 100)}%)`;
        });

        // Afficher le modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Nettoyer le modal après fermeture
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });

    } catch (error) {
        console.error('Error showing machine ratio slider:', error);
        showNotification('Erreur lors du chargement des ratios disponibles pour cette machine', 'error');
    }
}

async function confirmMachineRatio(instanceId) {
    try {
        const slider = document.getElementById('machineRatioSlider');
        const ratio = parseFloat(slider.value);
        
        showNotification('Application du ratio à la machine...', 'info');
        
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('machineRatioSliderModal'));
        modal.hide();

        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/machines/${instanceId}/apply-ratio`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ratio: ratio,
                optimization_type: 'economic'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to apply ratio to machine');
        }

        const result = await response.json();
        await loadSiteSummary(currentSiteId);
        showNotification(`Ratio ${(ratio * 100).toFixed(0)}% appliqué avec succès à la machine!`, 'success');
    } catch (error) {
        console.error('Error applying machine ratio:', error);
        showNotification(error.message, 'error');
    }
}

async function confirmManualRatio() {
    try {
        const slider = document.getElementById('ratioSlider');
        const ratio = parseFloat(slider.value);
        
        showNotification('Application du ratio manuel...', 'info');
        
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('ratioSliderModal'));
        modal.hide();

        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/apply-manual-ratio`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ratio: ratio,
                optimization_type: 'economic'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to apply manual ratio');
        }

        const result = await response.json();
        await loadSiteSummary(currentSiteId);
        showNotification(`Ratio ${(ratio * 100).toFixed(0)}% appliqué avec succès à ${result.total_machines} machine(s)!`, 'success');
    } catch (error) {
        console.error('Error applying manual ratio:', error);
        showNotification(error.message, 'error');
    }
}

// Reset to Nominal Ratio
// Fonction supprimée - remplacée par resetToNominal()

// Initialize navigation handling
function initializeNavigation() {
    // Handle main navigation clicks
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Handle different navigation items
            const href = this.getAttribute('href');
            
            if (href === '#backtest') {
                showBacktestSection();
            } else {
                // Show default interface (machines, etc.)
                showDefaultInterface();
                
                // Force refresh of the interface after a small delay
                setTimeout(() => {
                    if (currentObjectType) {
                        // Re-select the current object to refresh all displays
                        selectObject(currentObjectType, currentObjectId, currentObjectData);
                    } else {
                        // If no object is selected, show welcome message
                        showWelcomeMessage();
                    }
                }, 150);
            }
        });
    });
    
    // Handle backtest phase tabs
    const phaseTabs = document.querySelectorAll('#backtestPhaseTabs .nav-link');
    phaseTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            const targetPhase = this.getAttribute('data-bs-target').substring(1);
            
            // Initialize phase-specific content
            switch(targetPhase) {
                case 'phase1':
                    initializeBacktestPhase1();
                    break;
                case 'phase2':
                    initializeBacktestPhase2();
                    break;
                case 'phase3':
                    // Phase 3 is initialized when simulation starts
                    break;
                case 'phase4':
                    // Phase 4 is initialized when results are ready
                    break;
            }
        });
    });
}

// Show default interface (machines, optimization, etc.)
function showDefaultInterface() {
    // Hide backtest interface
    document.getElementById('backtestSection').style.display = 'none';
    document.getElementById('backtestSidebar').style.display = 'none';
    
    // Show main interface
    document.getElementById('chartsSection').style.display = 'flex';
    document.getElementById('optimizationSection').style.display = 'flex';
    document.getElementById('mainSidebar').style.display = 'block';
    
    // Show market data bar in main interface
    const marketDataCard = document.querySelector('.market-data-card');
    if (marketDataCard) {
        marketDataCard.style.display = 'block';
    }
    
    // Show selected object info in main interface (if object is selected)
    if (currentObjectType) {
        const selectedObjectCard = document.getElementById('selectedObjectCard');
        if (selectedObjectCard) {
            selectedObjectCard.style.display = 'block';
        }
        
        // Show site summary if it's a site
        if (currentObjectType === 'site') {
            const siteSummaryCard = document.getElementById('siteSummaryCard');
            if (siteSummaryCard) {
                siteSummaryCard.style.display = 'block';
            }
        }
        
        // Reload data for the currently selected object to ensure consistency
        setTimeout(async () => {
            if (currentObjectType === 'site' && currentObjectId) {
                // Recharger les données du site depuis l'API
                try {
                    const response = await fetch(`${API_BASE}/sites/${currentObjectId}`);
                    if (response.ok) {
                        const siteData = await response.json();
                        // Mettre à jour les données globales
                        currentObjectData = siteData;
                        // Recharger toutes les données du site
                        selectObject(currentObjectType, currentObjectId, siteData);
                    } else {
                        // Si l'API échoue, utiliser les données existantes
                        selectObject(currentObjectType, currentObjectId, currentObjectData);
                    }
                } catch (error) {
                    // En cas d'erreur, utiliser les données existantes
                    selectObject(currentObjectType, currentObjectId, currentObjectData);
                }
            } else if (currentObjectType === 'machine' || currentObjectType === 'template') {
                // Pour les machines/templates, utiliser les données existantes
                selectObject(currentObjectType, currentObjectId, currentObjectData);
            } else {
                // Aucun objet sélectionné, afficher le message de bienvenue
                showWelcomeMessage();
            }
        }, 100);
    }
}

// Switch backtest phase
function switchBacktestPhase(phaseNumber) {
    // Remove active class from all phases
    document.querySelectorAll('.phase-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to selected phase
    const selectedPhase = document.querySelector(`.phase-item:nth-child(${phaseNumber})`);
    if (selectedPhase) {
        selectedPhase.classList.add('active');
    }
    
    // Hide all phase content
    document.querySelectorAll('.phase-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Show selected phase content
    const selectedContent = document.getElementById(`phase${phaseNumber}`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    // Update title and button
    updateBacktestPhaseUI(phaseNumber);
    
    // Initialize phase-specific content
    switch(phaseNumber) {
        case 1:
            initializeBacktestPhase1();
            break;
        case 2:
            initializeBacktestPhase2();
            break;
        case 3:
            // Phase 3 is initialized when simulation starts
            break;
        case 4:
            // Phase 4 is initialized when results are ready
            break;
    }
}

// Update backtest phase UI (title and button)
function updateBacktestPhaseUI(phaseNumber) {
    const titleElement = document.getElementById('backtestPhaseTitle');
    const buttonElement = document.getElementById('backtestActionBtn');
    
    if (!titleElement || !buttonElement) return;
    
    const phaseConfig = {
        1: {
            title: 'Phase 1: Préparation',
            buttonText: 'Vérifier les Données',
            buttonIcon: 'fas fa-sync',
            buttonAction: 'checkDataAvailability()'
        },
        2: {
            title: 'Phase 2: Configuration',
            buttonText: 'Démarrer Simulation',
            buttonIcon: 'fas fa-play',
            buttonAction: 'startSimulation()'
        },
        3: {
            title: 'Phase 3: Simulation',
            buttonText: 'Démarrer Simulation',
            buttonIcon: 'fas fa-play',
            buttonAction: 'startSimulation()'
        },
        4: {
            title: 'Phase 4: Résultats',
            buttonText: 'Exporter Résultats',
            buttonIcon: 'fas fa-download',
            buttonAction: 'exportResults()'
        }
    };
    
    const config = phaseConfig[phaseNumber];
    if (config) {
        titleElement.textContent = config.title;
        buttonElement.innerHTML = `<i class="${config.buttonIcon}"></i> ${config.buttonText}`;
        buttonElement.onclick = new Function(config.buttonAction);
    }
}

// Update phase status
function updatePhaseStatus(phaseNumber, status) {
    const statusElement = document.getElementById(`phase${phaseNumber}Status`);
    if (statusElement) {
        switch(status) {
            case 'loading':
                statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                break;
            case 'success':
                statusElement.innerHTML = '<i class="fas fa-check"></i>';
                break;
            case 'error':
                statusElement.innerHTML = '<i class="fas fa-times"></i>';
                break;
            case 'locked':
                statusElement.innerHTML = '<i class="fas fa-lock"></i>';
                break;
            default:
                statusElement.innerHTML = '<i class="fas fa-undo"></i>';
        }
    }
} 

// Configuration Management Functions
let configurationData = {
    backtestStartDate: '2024-01-01',
    backtestEndDate: '2024-12-31',
    paymentInterval: 3,
    roiPeriod: 36,
    initialAggressiveness: 1.2,
    sd4YearWeight: 0.6,
    sd1YearWeight: 0.4
};

// Load configuration from API or localStorage
async function loadBacktestConfiguration() {
    try {
        // Try to load from API first
        const response = await fetch(`${API_BASE}/config`);
        if (response.ok) {
            const apiConfig = await response.json();
            configurationData = { ...configurationData, ...apiConfig };
        }
    } catch (error) {
        console.log('Using default configuration');
    }
    
    // Load from localStorage as fallback
    const savedConfig = localStorage.getItem('backtestConfiguration');
    if (savedConfig) {
        const localConfig = JSON.parse(savedConfig);
        configurationData = { ...configurationData, ...localConfig };
    }
    
    updateConfigurationForm();
}

// Save configuration to localStorage and optionally to API
async function saveBacktestConfiguration() {
    try {
        // Save to localStorage
        localStorage.setItem('backtestConfiguration', JSON.stringify(configurationData));
        
        // Try to save to API
        const response = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(configurationData)
        });
        
        if (response.ok) {
            showNotification('Configuration sauvegardée avec succès', 'success');
        } else {
            showNotification('Configuration sauvegardée localement', 'info');
        }
    } catch (error) {
        showNotification('Configuration sauvegardée localement', 'info');
    }
}

// Update the configuration form display
function updateConfigurationForm() {
    Object.keys(configurationData).forEach(key => {
        const element = document.getElementById(`fixed${key.charAt(0).toUpperCase() + key.slice(1)}`);
        if (element) {
            element.value = configurationData[key];
        }
    });
}

// Save configuration from form
function saveConfigurationFromForm() {
    const formData = {
        backtestStartDate: document.getElementById('fixedBacktestStartDate').value,
        backtestEndDate: document.getElementById('fixedBacktestEndDate').value,
        paymentInterval: parseInt(document.getElementById('fixedPaymentInterval').value),
        roiPeriod: parseInt(document.getElementById('fixedRoiPeriod').value),
        initialAggressiveness: parseFloat(document.getElementById('fixedInitialAggressiveness').value),
        sd4YearWeight: parseFloat(document.getElementById('fixedSd4YearWeight').value),
        sd1YearWeight: parseFloat(document.getElementById('fixedSd1YearWeight').value)
    };
    
    // Validate form data
    if (isValidFormData(formData)) {
        configurationData = { ...configurationData, ...formData };
        saveConfiguration();
        showNotification('Configuration sauvegardée', 'success');
    } else {
        showNotification('Valeurs invalides dans le formulaire', 'error');
    }
}

// Validate form data
function isValidFormData(formData) {
    // Check dates
    if (!formData.backtestStartDate || !formData.backtestEndDate) {
        return false;
    }
    
    const startDate = new Date(formData.backtestStartDate);
    const endDate = new Date(formData.backtestEndDate);
    if (startDate >= endDate) {
        return false;
    }
    
    // Check numeric values
    if (formData.paymentInterval < 1 || formData.paymentInterval > 12) {
        return false;
    }
    
    if (formData.roiPeriod < 12 || formData.roiPeriod > 60) {
        return false;
    }
    
    if (formData.initialAggressiveness < 0.5 || formData.initialAggressiveness > 2.0) {
        return false;
    }
    
    if (formData.sd4YearWeight < 0 || formData.sd4YearWeight > 1) {
        return false;
    }
    
    if (formData.sd1YearWeight < 0 || formData.sd1YearWeight > 1) {
        return false;
    }
    
    // Check that weights sum to 1
    if (Math.abs(formData.sd4YearWeight + formData.sd1YearWeight - 1) > 0.01) {
        return false;
    }
    
    return true;
}

// Refresh configuration from API
async function refreshConfiguration() {
    try {
        await loadBacktestConfiguration();
        showNotification('Configuration actualisée', 'success');
    } catch (error) {
        showNotification('Erreur lors de l\'actualisation', 'error');
    }
}

// Get current configuration for backtesting
function getCurrentConfiguration() {
    return { ...configurationData };
}

// Initialize configuration when backtest section is shown
function initializeBacktestConfiguration() {
    loadBacktestConfiguration();
}

async function applyOptimalRatios() {
    if (!currentSiteId) {
        showNotification('Aucun site sélectionné', 'error');
        return;
    }

    try {
        showNotification('Optimisation individuelle en cours...', 'info');
        
        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/apply-optimal-ratios`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erreur lors de l\'optimisation individuelle');
        }

        const data = await response.json();
        
        // Recharger la synthèse du site pour refléter les changements
        await loadSiteSummary(currentSiteId);
        
        showNotification(`Optimisation individuelle appliquée avec succès à ${data.total_machines} machine(s)`, 'success');
        
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors de l\'optimisation individuelle: ' + error.message, 'error');
    }
}

async function resetToNominal() {
    if (!currentSiteId) {
        showNotification('Aucun site sélectionné', 'error');
        return;
    }

    try {
        showNotification('Réinitialisation au ratio nominal...', 'info');
        
        const response = await fetch(`${API_BASE}/sites/${currentSiteId}/reset-to-nominal`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erreur lors de la remise à nominal');
        }

        const data = await response.json();
        
        // Recharger la synthèse du site pour refléter les changements
        await loadSiteSummary(currentSiteId);
        
        showNotification(`Ratios remis à nominal pour ${data.total_machines} machine(s)`, 'success');
        
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors de la remise à nominal: ' + error.message, 'error');
    }
}


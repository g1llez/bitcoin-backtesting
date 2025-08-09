// charts.js — regroupe l'initialisation et la mise à jour des graphiques
// Aucune valeur par défaut forcée ni fallback
(function () {
  function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      textColor: isDark ? '#c9d1d9' : '#212529',
      gridColor: isDark ? '#30363d' : '#dee2e6',
      primary: 'rgba(0, 123, 255, 0.6)',
      primaryBorder: 'rgba(0, 123, 255, 1)',
      accent: 'rgb(75, 192, 192)',
      accentBg: 'rgba(75, 192, 192, 0.2)'
    };
  }

  function createChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const existingChart = window[canvasId];
    if (existingChart && typeof existingChart.destroy === 'function') {
      existingChart.destroy();
    }
    const chart = new Chart(ctx, config);
    window[canvasId] = chart;
    return chart;
  }

  function updateChartData(canvasId, newData) {
    const chart = window[canvasId];
    if (!chart) return;
    chart.data = newData;
    chart.update();
  }

  function destroyChart(canvasId) {
    const chart = window[canvasId];
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
      window[canvasId] = null;
    }
  }

  function initEfficiencyChart() {
    const { primary, primaryBorder } = getThemeColors();
    const config = {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Efficacité',
          data: [],
          backgroundColor: primary,
          borderColor: primaryBorder,
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `TH/s: ${context.parsed.x}, Watt: ${context.parsed.y}`;
              }
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Hashrate (TH/s)' }, grid: { display: true } },
          y: { title: { display: true, text: 'Puissance (Watt)' }, grid: { display: true } }
        }
      }
    };
    createChart('efficiencyChart', config);
  }

  function initRatioAnalysisChart() {
    const { accent, accentBg } = getThemeColors();
    const config = {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Profit Quotidien ($)', data: [], borderColor: accent, backgroundColor: accentBg, tension: 0.1, pointRadius: 6, pointHoverRadius: 8 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          title: { display: true, text: 'Profit vs Ratio' },
          tooltip: { callbacks: { afterBody: function () { return ['Sélectionnez une machine pour voir les données']; } } }
        },
        scales: {
          x: { display: true, title: { display: true, text: "Ratio d'Ajustement" } },
          y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Montant ($/jour)' } }
        }
      }
    };
    createChart('ratioAnalysisChart', config);
  }

  function init() {
    initEfficiencyChart();
    initRatioAnalysisChart();
  }

  function showRatioAnalysisLoading() {
    const chart = window.ratioAnalysisChart;
    if (!chart) return;
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.options.plugins.title.text = 'Profit vs Ratio - Chargement...';
    chart.options.plugins.tooltip.callbacks.afterBody = function () { return ['Chargement des données...']; };
    chart.update();
  }

  function updateRatioAnalysisChart(data) {
    const ratios = data.results.map(r => r.ratio);
    const profits = data.results.map(r => r.daily_profit);
    const chart = window.ratioAnalysisChart;
    if (!chart) return;
    chart.data.labels = ratios;
    chart.data.datasets[0].data = profits;
    chart.options.plugins.title.text = `Profit vs Ratio - ${data.machine_model}`;
    chart.options.plugins.tooltip.callbacks.afterBody = function (context) {
      const idx = context[0].dataIndex;
      const r = data.results[idx];
      const eff = (r.efficiency_j_per_th ?? (r.efficiency_th_per_watt ? (1 / r.efficiency_th_per_watt) : null)) ?? 'N/A';
      return [
        `Hashrate: ${r.hashrate.toFixed(1)} TH/s`,
        `Puissance: ${r.power}W`,
        `Efficacité: ${eff} J/TH`
      ];
    };
    chart.update();
  }

  function updateEfficiencyChartFromData(efficiencyDataArray) {
    const chartData = efficiencyDataArray.map(item => ({ x: parseFloat(item.effective_hashrate), y: item.power_consumption }));
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

  window.charts = {
    init,
    showRatioAnalysisLoading,
    updateRatioAnalysisChart,
    updateEfficiencyChartFromData,
    updateChartData,
    destroyChart
  };
})();



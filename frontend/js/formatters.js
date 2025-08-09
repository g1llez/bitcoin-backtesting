// Formatters utilitaires – aucune valeur par défaut forcée
window.formatters = (() => {
  function formatCurrency(value, currency) {
    if (value === null || value === undefined) return '—';
    try {
      return new Intl.NumberFormat('fr-CA', { style: 'currency', currency }).format(value);
    } catch (_) {
      return `${value}`;
    }
  }

  function formatJoulesPerTH(value) {
    if (value === null || value === undefined) return '—';
    const num = Number(value);
    if (Number.isNaN(num)) return '—';
    return `${num.toFixed(2)} J/TH`;
  }

  function formatHashrateTH(value) {
    if (value === null || value === undefined) return '—';
    const num = Number(value);
    if (Number.isNaN(num)) return '—';
    return `${num.toFixed(2)} TH/s`;
  }

  function formatPowerW(value) {
    if (value === null || value === undefined) return '—';
    const num = Number(value);
    if (Number.isNaN(num)) return '—';
    return `${num.toFixed(0)} W`;
  }

  return { formatCurrency, formatJoulesPerTH, formatHashrateTH, formatPowerW };
})();



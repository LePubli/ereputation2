// Utilitaires divers
import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return '—';
  return new Intl.NumberFormat('fr-FR').format(n);
}

export function formatPercent(n: number | null | undefined): string {
  if (n == null) return '—';
  return `${n.toFixed(1)} %`;
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return '—';
  try {
    return new Date(isoString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return isoString;
  }
}

export function getPropensityColor(category: string | null): string {
  switch (category) {
    case 'HOT':
      return 'bg-red-100 text-red-700 border-red-200';
    case 'WARM':
      return 'bg-orange-100 text-orange-700 border-orange-200';
    case 'COLD':
      return 'bg-blue-100 text-blue-700 border-blue-200';
    default:
      return 'bg-gray-100 text-gray-600 border-gray-200';
  }
}

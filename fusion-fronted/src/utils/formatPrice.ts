import { getSymbolMeta } from './symbolMeta'

export function formatPrice(price: number | null | undefined, symbol: string): string {
  if (price == null) return '—'
  const { decimals } = getSymbolMeta(symbol)
  return price.toFixed(decimals)
}

export function formatPct(value: number | null | undefined): string {
  if (value == null) return '—'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${(value * 100).toFixed(2)}%`
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

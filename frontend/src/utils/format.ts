const currencyFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

const numberFormatter = (digits: number) =>
  new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })

const percentFormatter = (digits: number) =>
  new Intl.NumberFormat('zh-CN', {
    style: 'percent',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })

export const formatCurrency = (value: number | null | undefined, digits = 2): string => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return currencyFormatter.format(Number(value.toFixed(digits)))
}

export const formatNumber = (value: number | null | undefined, digits = 2): string => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return numberFormatter(digits).format(value)
}

export const formatPercent = (value: number | null | undefined, digits = 2): string => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  return percentFormatter(digits).format(value)
}

export const formatSigned = (value: number | null | undefined, digits = 2): string => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return '--'
  }
  const formatted = formatNumber(Math.abs(value), digits)
  return `${value >= 0 ? '+' : '-'}${formatted}`
}

export const formatDateTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) {
    return timestamp
  }
  return date.toLocaleString('zh-CN', {
    hour12: false,
  })
}

export const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) {
    return timestamp
  }
  return date.toLocaleDateString('zh-CN')
}

export const getPnlClassName = (value: number): string => {
  if (value > 0) return 'pnl-positive'
  if (value < 0) return 'pnl-negative'
  return 'pnl-neutral'
}

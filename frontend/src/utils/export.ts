const BOM = '\uFEFF'

const escapeValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return ''
  }
  const stringValue = String(value)
  if (stringValue.includes(',') || stringValue.includes('\n') || stringValue.includes('"')) {
    return `"${stringValue.replace(/"/g, '""')}"`
  }
  return stringValue
}

export const downloadCSV = (filename: string, rows: Array<Record<string, unknown>>): void => {
  if (!rows.length) {
    return
  }

  const headers = Object.keys(rows[0])
  const csv = [headers.join(',')]

  rows.forEach((row) => {
    const values = headers.map((header) => escapeValue(row[header]))
    csv.push(values.join(','))
  })

  const blob = new Blob([BOM + csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

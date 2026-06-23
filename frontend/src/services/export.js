/**
 * Utilidades de exportación para CMMS-BioAI v0.9.3 (RF13)
 * Funciones para exportar datos a CSV (compatible con Excel)
 */

/**
 * Convierte un array de objetos a CSV y lo descarga.
 * @param {Array} data - Array de objetos a exportar
 * @param {Array} columns - Array de {key, label} con las columnas a exportar
 * @param {string} filename - Nombre del archivo sin extensión
 */
export function exportToCSV(data, columns, filename) {
  if (!data || data.length === 0) {
    alert('No hay datos para exportar')
    return
  }

  // Cabeceras
  const headers = columns.map(c => `"${c.label}"`).join(',')

  // Filas
  const rows = data.map(item => {
    return columns.map(c => {
      let val = item[c.key]
      if (val === null || val === undefined) val = ''
      // Escapar comillas y saltos de línea
      val = String(val).replace(/"/g, '""').replace(/\n/g, ' ')
      return `"${val}"`
    }).join(',')
  })

  // Combinar
  const csv = '\ufeff' + headers + '\n' + rows.join('\n')  // BOM para Excel

  // Descargar
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const date = new Date().toISOString().substring(0, 10)
  link.download = `${filename}_${date}.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

/**
 * Convierte un array de objetos a HTML table y lo abre para imprimir/guardar como Excel.
 * @param {Array} data - Array de objetos a exportar
 * @param {Array} columns - Array de {key, label} con las columnas a exportar
 * @param {string} filename - Nombre del archivo sin extensión
 */
export function exportToExcelHTML(data, columns, filename) {
  if (!data || data.length === 0) {
    alert('No hay datos para exportar')
    return
  }

  let html = '<table border="1"><thead><tr>'
  columns.forEach(c => {
    html += `<th style="background:#2C3E50;color:white;font-weight:bold;padding:8px;">${c.label}</th>`
  })
  html += '</tr></thead><tbody>'

  data.forEach(item => {
    html += '<tr>'
    columns.forEach(c => {
      let val = item[c.key]
      if (val === null || val === undefined) val = ''
      html += `<td style="padding:6px;">${String(val).replace(/</g, '&lt;')}</td>`
    })
    html += '</tr>'
  })

  html += '</tbody></table>'

  // Crear archivo .xls (Excel abre HTML con extensión .xls)
  const blob = new Blob(['\ufeff<html><head><meta charset="utf-8"></head><body>' + html + '</body></html>'],
    { type: 'application/vnd.ms-excel;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const date = new Date().toISOString().substring(0, 10)
  link.download = `${filename}_${date}.xls`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

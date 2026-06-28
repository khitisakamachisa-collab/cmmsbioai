/**
 * Servicios de exportación - RF13
 * Funciones para exportar datos a Excel (.xls via HTML) y CSV.
 * No dependen de librerías externas — usan Blob + download nativo del navegador.
 */

/**
 * Escapa un valor para colocarlo dentro de una celda HTML (<td>).
 * @param {any} val
 * @returns {string}
 */
function escapeHtml(val) {
  if (val === null || val === undefined) return ''
  const s = String(val)
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Escapa un valor para CSV siguiendo reglas RFC 4180.
 * @param {any} val
 * @returns {string}
 */
function escapeCsv(val) {
  if (val === null || val === undefined) return ''
  const s = String(val)
  // Si contiene comilla, coma, salto de línea o punto y coma → envolver en comillas y duplicar comillas
  if (/[",\n;]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

/**
 * Convierte un array de objetos a tabla HTML para Excel.
 * @param {Array<Object>} rows
 * @returns {string}
 */
function rowsToHtmlTable(rows) {
  if (!rows || !rows.length) {
    return '<table><tr><td>(sin datos)</td></tr></table>'
  }
  const headers = Object.keys(rows[0])
  const thead = `<tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>`
  const tbody = rows.map(r =>
    `<tr>${headers.map(h => `<td>${escapeHtml(r[h])}</td>`).join('')}</tr>`
  ).join('')
  return `<table border="1">${thead}${tbody}</table>`
}

/**
 * Convierte un array de objetos a texto CSV.
 * @param {Array<Object>} rows
 * @param {string} delimiter - por defecto ','
 * @returns {string}
 */
function rowsToCsv(rows, delimiter = ',') {
  if (!rows || !rows.length) return ''
  const headers = Object.keys(rows[0])
  const lines = [headers.join(delimiter)]
  for (const r of rows) {
    lines.push(headers.map(h => escapeCsv(r[h])).join(delimiter))
  }
  return lines.join('\n')
}

/**
 * Dispara la descarga de un Blob en el navegador.
 * @param {Blob} blob
 * @param {string} filename
 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // Liberar URL después de un breve delay
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/**
 * Exporta un array de objetos a un archivo .xls (HTML table con header Excel).
 * @param {Array<Object>} rows - Array de objetos planos (cada key = columna)
 * @param {string} baseName - Nombre base del archivo (sin extensión)
 */
export function exportToExcelHTML(rows, baseName = 'export') {
  const html = rowsToHtmlTable(rows)
  const fullHtml = `<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:x="urn:schemas-microsoft-com:office:excel"
xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta charset="UTF-8">
<!--[if gte mso 9]><xml>
<x:ExcelWorkbook>
  <x:ExcelWorksheets>
    <x:ExcelWorksheet>
      <x:Name>Hoja1</x:Name>
      <x:WorksheetOptions>
        <x:DisplayGridlines/>
      </x:WorksheetOptions>
    </x:ExcelWorksheet>
  </x:ExcelWorksheets>
</x:ExcelWorkbook>
</xml><![endif]-->
</head>
<body>${html}</body>
</html>`
  const blob = new Blob([fullHtml], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  downloadBlob(blob, `${baseName}.xls`)
}

/**
 * Exporta un array de objetos a un archivo .csv (UTF-8 con BOM para Excel).
 * @param {Array<Object>} rows - Array de objetos planos
 * @param {string} baseName - Nombre base del archivo (sin extensión)
 * @param {string} [delimiter=',']
 */
export function exportToCSV(rows, baseName = 'export', delimiter = ',') {
  const csv = rowsToCsv(rows, delimiter)
  // BOM para que Excel detecte UTF-8 correctamente
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, `${baseName}.csv`)
}

// bob converter (Butterfield -> YNAB)
// Exports: async function processFile(csvText, originalFileName) -> { filename, content, originalFileName }

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let insideQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            insideQuotes = !insideQuotes;
        } else if (char === ',' && !insideQuotes) {
            result.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current.trim());
    return result;
}

function formatDateMMDDYYYY(date) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    return `${month}/${day}/${year}`;
}

function formatDateForFilename(date) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    return `${year}${month}${day}`;
}

function replaceMultipleSpaces(s) {
    return s.replace(/\s+/g, ' ');
}

export async function processFile(csvText, originalFileName) {
    if (!csvText) return null;
    // strip BOM
    csvText = csvText.replace(/^\uFEFF/, '');

    const lines = csvText.trim().split(/\r?\n/);
    if (lines.length === 0) return null;

    let isCC = false;
    let filenameSuffix = '';
    let headerLine = -1;
    let transDateMin = new Date(8640000000000000);
    let transDateMax = new Date(-8640000000000000);
    const ynabCSV = [['Date', 'Payee', 'Memo', 'Outflow', 'Inflow']];

    for (let lineCount = 0; lineCount < lines.length; lineCount++) {
        const row = parseCSVLine(lines[lineCount]);
        if (row.length === 0 || (row.length === 1 && row[0] === '')) continue;

        if (lineCount === 0) {
            if (row[0] === 'Card No') {
                isCC = true;
                filenameSuffix = 'YNAB_CC_' + (row[1] || '').slice(-4);
            } else {
                const accountNumber = row[0].replace(/'/g, '0');
                filenameSuffix = 'YNAB_' + accountNumber;
            }
        }

        if (row[0] === 'Reference No' || row[0] === 'Transaction Date') {
            headerLine = lineCount;
            continue;
        }

        if (lineCount > headerLine && headerLine !== -1) {
            let transDate, transDateString, description, outflow, inflow;

            if (isCC) {
                transDate = parseDate(row[1]);
                if (transDate) transDateString = formatDateMMDDYYYY(transDate);
                description = replaceMultipleSpaces(row[2] || '').trim();
                outflow = (row[3] && row[3].trim() === 'Dr') ? (row[4] || '') : '';
                inflow = (row[3] && row[3].trim() === 'Dr') ? '' : (row[4] || '');
            } else {
                transDate = parseDate(row[0]);
                if (transDate) transDateString = formatDateMMDDYYYY(transDate);
                description = replaceMultipleSpaces(row[2] || '').trim();
                outflow = row[3] || '';
                inflow = row[4] || '';
            }

            if (transDate) {
                ynabCSV.push([transDateString, description, description, outflow, inflow]);
                if (transDate < transDateMin) transDateMin = transDate;
                if (transDate > transDateMax) transDateMax = transDate;
            }
        }
    }

    if (transDateMin.getTime() === 8640000000000000 || transDateMax.getTime() === -8640000000000000) return null;

    const minDateString = formatDateForFilename(transDateMin);
    const maxDateString = formatDateForFilename(transDateMax);
    const outputFilename = `${filenameSuffix}_${minDateString}_${maxDateString}.csv`;

    // build CSV string (quote all fields)
    const csvLines = ynabCSV.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');

    return { filename: outputFilename, content: csvLines, originalFileName };
}

function parseDate(dateString) {
    if (!dateString) return null;
    const s = dateString.trim();
    // Try JS Date parsing on common formats
    const d = new Date(s);
    if (!isNaN(d.getTime())) return d;

    // Try dd MMM yyyy (e.g., 15 Jan 2024)
    const parts = s.split(' ');
    if (parts.length === 3) {
        const day = parseInt(parts[0], 10);
        const monthNames = { 'Jan':0,'Feb':1,'Mar':2,'Apr':3,'May':4,'Jun':5,'Jul':6,'Aug':7,'Sep':8,'Oct':9,'Nov':10,'Dec':11 };
        const month = monthNames[parts[1]];
        const year = parseInt(parts[2], 10);
        if (!isNaN(day) && month !== undefined && !isNaN(year)) return new Date(year, month, day);
    }

    return null;
}

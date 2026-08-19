// revolut converter (CSV-only) -> Actual Budget format
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

function formatDateYMD(date) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    return `${year}-${month}-${day}`;
}

function formatDateForFilename(date) {
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    return `${year}${month}${day}`;
}

export async function processFile(csvText, originalFileName) {
    if (!csvText) return null;
    csvText = csvText.replace(/^\uFEFF/, '');
    const lines = csvText.trim().split(/\r?\n/);
    if (lines.length === 0) return null;

    // find header row and map columns
    let header = null;
    let headerIdx = 0;
    for (let i = 0; i < Math.min(10, lines.length); i++) {
        const row = parseCSVLine(lines[i]).map(h => h.toLowerCase());
        if (row.includes('started date') || row.includes('started date')) {
            header = row;
            headerIdx = i;
            break;
        }
    }
    if (!header) {
        // fallback to first line
        header = parseCSVLine(lines[0]).map(h => h.toLowerCase());
        headerIdx = 0;
    }

    const idxStarted = header.findIndex(h => h === 'started date');
    const idxDescription = header.findIndex(h => h === 'description');
    const idxAmount = header.findIndex(h => h === 'amount');
    const idxFee = header.findIndex(h => h === 'fee');
    const idxState = header.findIndex(h => h === 'state');

    if (idxStarted === -1 || idxDescription === -1 || idxAmount === -1) return null;

    const outRows = [['Date', 'Payee', 'Memo', 'Amount']];
    let minDate = null;
    let maxDate = null;

    for (let i = headerIdx + 1; i < lines.length; i++) {
        const row = parseCSVLine(lines[i]);
        if (row.length === 0 || (row.length === 1 && row[0] === '')) continue;

        const state = idxState !== -1 ? (row[idxState] || '').trim().toUpperCase() : 'COMPLETED';
        if (idxState !== -1 && state !== 'COMPLETED') continue;

        let started = (row[idxStarted] || '').trim();
        if (!started) continue;
        const datePart = started.split(' ')[0];
        const parsed = new Date(datePart);
        if (isNaN(parsed.getTime())) {
            // try more robust parse: if datePart like DD/MM/YYYY
            const dparts = datePart.split('/');
            if (dparts.length === 3) {
                const dd = Number(dparts[0]);
                const mm = Number(dparts[1]) - 1;
                const yyyy = Number(dparts[2]);
                if (!isNaN(dd) && !isNaN(mm) && !isNaN(yyyy)) {
                    parsed.setFullYear(yyyy, mm, dd);
                }
            }
        }
        if (isNaN(parsed.getTime())) continue;

        const dateStr = formatDateYMD(parsed);
        if (!minDate || parsed < minDate) minDate = parsed;
        if (!maxDate || parsed > maxDate) maxDate = parsed;

        const payee = (row[idxDescription] || '').trim();
        const memo = payee;

        let amount = 0;
        const rawAmount = (row[idxAmount] || '').replace(/[^0-9.\-]/g, '');
        if (rawAmount !== '') amount = Number(rawAmount);

        if (idxFee !== -1) {
            const rawFee = (row[idxFee] || '').replace(/[^0-9.\-]/g, '');
            const fee = rawFee === '' ? 0 : Number(rawFee);
            amount = amount - fee;
        }

        // Format with two decimals
        const amountStr = amount.toFixed(2);

        outRows.push([dateStr, payee, memo, amountStr]);
    }

    if (!minDate || !maxDate) return null;

    const fileMin = formatDateForFilename(minDate);
    const fileMax = formatDateForFilename(maxDate);
    const outputFilename = `Actual_Revolut_${fileMin}_${fileMax}.csv`;

    const csvLines = outRows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');

    return { filename: outputFilename, content: csvLines, originalFileName };
}

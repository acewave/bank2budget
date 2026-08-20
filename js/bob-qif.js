/**
 * Convert BOB QIF format to Actual Budget CSV format
 * Handles TKYD format with Dr/Cr notation and converts to standard QIF
 */
export function convertBobQif(fileContent) {
    const lines = fileContent.split('\n');
    const convertedLines = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Skip empty T lines left over at the end of blocks
        if (line === 'T') {
            continue;
        }

        // Parse 'TKYD 123.45 Dr' or 'TKYD 123.45 Cr'
        const match = line.match(/^TKYD\s*([\d,.]+)\s*(Dr|Cr)$/);
        if (match) {
            const amountStr = match[1];
            const drCr = match[2];
            
            // Remove commas and convert to float
            let amount = parseFloat(amountStr.replace(/,/g, ''));
            
            // Convert debits to negative
            if (drCr === 'Dr') {
                amount = -amount;
            }
            
            // Add formatted amount line
            convertedLines.push(`T${amount.toFixed(2)}`);
        } else {
            // Keep all other lines as-is
            convertedLines.push(line);
        }
    }

    // Join lines and return
    return convertedLines.join('\n');
}

/**
 * Parse QIF format into structured transaction data for CSV export
 * QIF format: Lines starting with ! indicate section headers (e.g., !Type:Bank)
 *            T = amount
 *            D = date
 *            P = payee
 *            L = category
 *            ^ = end of transaction
 */
export function parseQifToCSV(qifContent) {
    const lines = qifContent.split('\n');
    const transactions = [];
    let currentTransaction = {};

    for (const line of lines) {
        const trimmedLine = line.trim();
        
        if (!trimmedLine) continue;

        if (trimmedLine.startsWith('!')) {
            // Section header, skip
            continue;
        }

        const code = trimmedLine[0];
        const value = trimmedLine.substring(1).trim();

        switch (code) {
            case 'T':
                currentTransaction.amount = value;
                break;
            case 'D':
                currentTransaction.date = value;
                break;
            case 'P':
                currentTransaction.payee = value;
                break;
            case 'L':
                currentTransaction.category = value;
                break;
            case 'M':
                currentTransaction.memo = value;
                break;
            case '^':
                // End of transaction
                if (Object.keys(currentTransaction).length > 0) {
                    transactions.push(currentTransaction);
                    currentTransaction = {};
                }
                break;
        }
    }

    // Add last transaction if exists
    if (Object.keys(currentTransaction).length > 0) {
        transactions.push(currentTransaction);
    }

    // Convert to CSV format for Actual Budget
    if (transactions.length === 0) {
        return 'Date,Payee,Category,Amount,Memo\n';
    }

    const headers = ['Date', 'Payee', 'Category', 'Amount', 'Memo'];
    const csvLines = [headers.join(',')];

    for (const transaction of transactions) {
        const row = [
            transaction.date || '',
            transaction.payee || '',
            transaction.category || '',
            transaction.amount || '',
            transaction.memo || ''
        ];
        
        // Escape fields with commas or quotes
        const escapedRow = row.map(field => {
            if (field.includes(',') || field.includes('"')) {
                return `"${field.replace(/"/g, '""')}"`;
            }
            return field;
        });
        
        csvLines.push(escapedRow.join(','));
    }

    return csvLines.join('\n');
}

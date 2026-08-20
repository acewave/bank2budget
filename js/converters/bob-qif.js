/**
 * BOB QIF converter (normalize BOB/TKYD QIF into standard QIF for Actual Budget)
 * Exports: async function processFile(fileText, originalFileName) -> { filename, content, originalFileName }
 *
 * This lives in js/converters/ so it can be dynamically imported by the app like the other converters.
 */

function convertBobQif(fileContent) {
    const lines = fileContent.split(/\r?\n/);
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

            // Add formatted amount line (QIF amounts are plain numbers, sign indicates outflow/inflow)
            convertedLines.push(`T${amount.toFixed(2)}`);
        } else {
            // Keep all other lines as-is
            convertedLines.push(line);
        }
    }

    // Join lines and return (preserve final newline)
    return convertedLines.join('\n');
}

export async function processFile(fileText, originalFileName) {
    if (!fileText) return null;

    const converted = convertBobQif(fileText);

    // Build output filename: prefix with Actual_ and ensure .qif extension
    let base = (originalFileName || 'converted.qif').replace(/^.*[\\/]/, '');
    if (!/\.qif$/i.test(base)) {
        base = base.replace(/\.[^/.]+$/, '') + '.qif';
    }
    const filename = `Actual_${base}`;

    return { filename, content: converted, originalFileName };
}

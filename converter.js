class YNABConverter {
    constructor() {
        this.csvInput = document.getElementById('csvInput');
        this.statusDiv = document.getElementById('status');
        this.resultsDiv = document.getElementById('results');
        this.results = [];
        
        this.csvInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    handleFileSelect(event) {
        const files = event.target.files;
        if (files.length === 0) return;

        this.statusDiv.textContent = `Processing ${files.length} file(s)...`;
        this.statusDiv.className = 'status processing';
        this.resultsDiv.innerHTML = '';
        this.resultsDiv.classList.remove('show');

        let processedCount = 0;
        const results = [];

        for (let file of files) {
            if (file.name.startsWith('YNAB_')) {
                console.log(`Skipping ${file.name} (already converted)`);
                processedCount++;
                continue;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const convertedData = this.processCSV(e.target.result, file.name);
                    if (convertedData) {
                        results.push(convertedData);
                    }
                } catch (error) {
                    console.error(`Error processing ${file.name}:`, error);
                    this.statusDiv.textContent = `Error processing ${file.name}: ${error.message}`;
                    this.statusDiv.className = 'status error';
                }
                processedCount++;
                if (processedCount === files.length) {
                    this.displayResults(results);
                }
            };
            reader.readAsText(file);
        }
    }

    processCSV(csvContent, originalFileName) {
        const lines = csvContent.trim().split('\n');
        if (lines.length === 0) return null;

        let isCC = false;
        let filenameSuffix = '';
        let headerLine = -1;
        let transDateMin = new Date(8640000000000000);
        let transDateMax = new Date(-8640000000000000);
        const ynabCSV = [['Date', 'Payee', 'Memo', 'Outflow', 'Inflow']];

        for (let lineCount = 0; lineCount < lines.length; lineCount++) {
            const row = this.parseCSVLine(lines[lineCount]);
            
            if (row.length === 0) continue;

            // Check first line for account or card info
            if (lineCount === 0) {
                if (row[0] === 'Card No') {
                    isCC = true;
                    filenameSuffix = 'YNAB_CC_' + row[1].slice(-4);
                } else {
                    const accountNumber = row[0].replace(/'/g, '0');
                    filenameSuffix = 'YNAB_' + accountNumber;
                }
            }

            // Find header line
            if (row[0] === 'Reference No' || row[0] === 'Transaction Date') {
                headerLine = lineCount;
            }

            // Process transaction lines
            if (lineCount > headerLine && headerLine !== -1) {
                let transDate, transDateString, description, outflow, inflow;

                if (isCC) {
                    // Credit card format
                    transDate = this.parseDate(row[1]);
                    transDateString = this.formatDate(transDate);
                    description = this.replaceMultipleSpaces(row[2]).trim();
                    outflow = row[3].trim() === 'Dr' ? row[4] : '';
                    inflow = row[3].trim() === 'Dr' ? '' : row[4];
                } else {
                    // Regular account format
                    transDate = this.parseDate(row[0]);
                    transDateString = this.formatDate(transDate);
                    description = this.replaceMultipleSpaces(row[2]).trim();
                    outflow = row[3];
                    inflow = row[4];
                }

                if (transDate) {
                    ynabCSV.push([transDateString, description, description, outflow, inflow]);
                    
                    if (transDate < transDateMin) {
                        transDateMin = transDate;
                    }
                    if (transDate > transDateMax) {
                        transDateMax = transDate;
                    }
                }
            }
        }

        // Generate output filename
        if (transDateMin.getTime() === 8640000000000000 || transDateMax.getTime() === -8640000000000000) {
            return null;
        }

        const minDateString = this.formatDateForFilename(transDateMin);
        const maxDateString = this.formatDateForFilename(transDateMax);
        const outputFilename = `${filenameSuffix}_${minDateString}_${maxDateString}.csv`;

        return {
            filename: outputFilename,
            content: ynabCSV,
            originalFileName: originalFileName
        };
    }

    parseCSVLine(line) {
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

    parseDate(dateString) {
        // Try format: "dd MMM yyyy" (e.g., "15 Jan 2024")
        const months = {
            'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
            'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
        };

        const parts = dateString.trim().split(' ');
        if (parts.length === 3) {
            const day = parseInt(parts[0]);
            const month = months[parts[1]];
            const year = parseInt(parts[2]);

            if (!isNaN(day) && month !== undefined && !isNaN(year)) {
                return new Date(year, month, day);
            }
        }
        return null;
    }

    formatDate(date) {
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const year = date.getFullYear();
        return `${month}/${day}/${year}`;
    }

    formatDateForFilename(date) {
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const year = date.getFullYear();
        return `${year}${month}${day}`;
    }

    replaceMultipleSpaces(string) {
        return string.replace(/\s+/g, ' ');
    }

    displayResults(results) {
        if (results.length === 0) {
            this.statusDiv.textContent = 'No valid CSV files found to convert.';
            this.statusDiv.className = 'status error';
            return;
        }

        this.statusDiv.textContent = `Successfully converted ${results.length} file(s)!`;
        this.statusDiv.className = 'status success';

        this.resultsDiv.innerHTML = '';
        this.results = results;
        
        results.forEach((result, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `
                <div class="result-info">
                    <h3>${result.filename}</h3>
                    <p>From: ${result.originalFileName}</p>
                </div>
                <button class="download-btn" onclick="converter.downloadCSV(${index})">⬇️ Download</button>
            `;
            this.resultsDiv.appendChild(resultItem);
        });
        this.resultsDiv.classList.add('show');
    }

    downloadCSV(index) {
        const result = this.results[index];
        if (!result) return;

        const csvContent = result.content.map(row => 
            row.map(cell => `"${cell}"`).join(',')
        ).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', result.filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

const converter = new YNABConverter();
// App bootstrapper: wires the UI and dynamically loads converters
const csvInput = document.getElementById('csvInput');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const converterType = document.getElementById('converterType');

let results = [];

csvInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const type = converterType.value;
    statusDiv.textContent = `Processing ${files.length} file(s) as ${type}...`;
    statusDiv.className = 'status processing';
    resultsDiv.innerHTML = '';

    // Dynamic import of the selected converter
    let module;
    try {
        module = await import(`./converters/${type}.js`);
    } catch (err) {
        statusDiv.textContent = `Failed to load converter for ${type}: ${err.message}`;
        statusDiv.className = 'status error';
        return;
    }

    const converter = module;

    results = [];
    let processed = 0;

    for (const file of files) {
        if (file.name.startsWith('YNAB_') || file.name.startsWith('Actual_')) {
            // skip already converted files
            processed++;
            continue;
        }

        const text = await file.text();
        try {
            const out = await converter.processFile(text, file.name);
            if (out) results.push(out);
        } catch (err) {
            console.error(`Error processing ${file.name}:`, err);
            const errDiv = document.createElement('div');
            errDiv.className = 'status error';
            errDiv.textContent = `Error processing ${file.name}: ${err.message}`;
            resultsDiv.appendChild(errDiv);
        }
        processed++;

        if (processed === files.length) displayResults(results);
    }
});

function displayResults(resultsArray) {
    if (!resultsArray || resultsArray.length === 0) {
        statusDiv.textContent = 'No valid CSV files found to convert.';
        statusDiv.className = 'status error';
        return;
    }

    statusDiv.textContent = `Successfully converted ${resultsArray.length} file(s)!`;
    statusDiv.className = 'status success';

    resultsDiv.innerHTML = '';
    results = resultsArray;

    results.forEach((res, index) => {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.innerHTML = `
            <div class="result-info">
                <h3>${res.filename}</h3>
                <p>From: ${res.originalFileName}</p>
            </div>
            <button class="download-btn" data-index="${index}">⬇️ Download</button>
        `;
        resultsDiv.appendChild(item);
    });

    resultsDiv.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = Number(e.currentTarget.getAttribute('data-index'));
            downloadResult(idx);
        });
    });
}

function downloadResult(index) {
    const res = results[index];
    if (!res) return;

    const blob = new Blob([res.content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', res.filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

# YNAB Bob - Web Version

A browser-based converter for Butterfield Bank CSV exports to YNAB format.

## Features

- ✅ **Privacy-First**: All processing happens in your browser - your data never leaves your computer
- ✅ **Batch Processing**: Convert multiple CSV files at once
- ✅ **Format Support**: Both regular and credit card export formats (current and historical)
- ✅ **No Installation**: Just open in a web browser
- ✅ **Free Hosting**: Deploy to Cloudflare Pages or any static host

## How to Use

1. Open the web interface
2. Click "Choose CSV Files" and select one or more Butterfield Bank CSV exports
3. Files are automatically converted to YNAB format
4. Click "Download" to save each converted file
5. Import the downloaded CSV files into YNAB

## Deployment

### Deploy to Cloudflare Pages

1. Fork or clone this repository
2. Connect your GitHub repository to Cloudflare Pages
3. Set build settings:
   - **Framework preset**: None (static site)
   - **Build command**: (leave empty)
   - **Build output directory**: `/` (root)
4. Deploy!

### Alternative: Deploy Manually

```bash
# Install Wrangler CLI
npm install -g @cloudflare/wrangler

# Login to Cloudflare
wrangler login

# Deploy
wrangler pages deploy . --project-name ynab-bob
```

## File Structure

- `index.html` - Main web interface
- `style.css` - Styling
- `converter.js` - Core conversion logic (JavaScript port of ynab.py)
- `wrangler.toml` - Cloudflare Pages configuration

## Original CLI Version

The original command-line Python version is available on the `main` branch.

## Technical Details

The JavaScript converter replicates the logic from `ynab.py`:
- Detects account type (regular or credit card)
- Parses dates in "dd MMM yyyy" format
- Normalizes whitespace in descriptions
- Generates YNAB-compatible CSV with proper formatting
- Creates output filename with date range: `YNAB_{account}_{startDate}_{endDate}.csv`

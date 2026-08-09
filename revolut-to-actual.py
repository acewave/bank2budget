import pandas as pd
import os
import csv

def convert_xlsx_to_csv(input_file=None):
    # Import tkinter lazily to avoid requiring a GUI in headless environments
    if not input_file:
        try:
            from tkinter import Tk
            from tkinter.filedialog import askopenfilename
        except Exception as e:
            print(f"Interactive file selection requires tkinter: {e}")
            return

        # Hide the main Tkinter window
        Tk().withdraw()
        
        # Ask the user to select the input file
        input_file = askopenfilename(
            title="Select the input Excel or CSV file",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
    
    if not input_file:
        print("No file selected. Exiting.")
        return
    
    # Determine file type and read accordingly
    if input_file.lower().endswith('.xlsx'):
        df = pd.read_excel(input_file)
    elif input_file.lower().endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        print("Unsupported file type. Please select an Excel or CSV file.")
        return

    # Ensure 'Started Date' is in datetime format
    df['Started Date'] = pd.to_datetime(df['Started Date'])

    # Filter by State if present (keep COMPLETED only)
    if 'State' in df.columns:
        df = df[df['State'].astype(str).str.upper() == 'COMPLETED']

    # Map the columns and remove the timestamp from 'Started Date'
    df['Date'] = df['Started Date'].dt.date
    df['Payee'] = df['Description']
    df['Memo'] = df['Description']

    # Calculate net amount by subtracting non-zero Fee (if present)
    if 'Fee' in df.columns:
        fee = pd.to_numeric(df['Fee'], errors='coerce').fillna(0)
        amount = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        df['Amount'] = amount - fee
    else:
        df['Amount'] = df['Amount']

    # Select and reorder the columns
    output_df = df[['Date', 'Payee', 'Memo', 'Amount']]

    # Find the earliest and latest dates
    earliest_date = df['Started Date'].min().strftime('%Y%m%d')
    latest_date = df['Started Date'].max().strftime('%Y%m%d')

    # Determine the filename
    base_filename = f"Actual_Revolut_{earliest_date}_{latest_date}_"
    output_file = None
    counter = 1

    # Get the directory of the input file
    input_dir = os.path.dirname(input_file)

    while output_file is None or os.path.exists(os.path.join(input_dir, output_file)):
        output_file = f"{base_filename}{counter:02d}.csv"
        counter += 1

    # Write the output to a CSV file in the same directory as the input file
    output_path = os.path.join(input_dir, output_file)
    output_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    print(f"Output saved to {output_path}")
    return output_path

def detect_revolut_file(path):
    try:
        with open(path, encoding='utf-8-sig', newline='') as f:
            head = f.read(4096).lower()
            return 'started date' in head and 'description' in head
    except Exception:
        return False


def convert_file(input_path, preview=False):
    """Wrapper to convert a single Revolut file. Returns output filepath or False on error.
       If preview=True, returns the expected output filename without writing.
    """
    if preview:
        # Try to estimate date range from file by reading Started Date column
        try:
            with open(input_path, encoding='utf-8-sig', newline='') as f:
                # Read header
                reader = csv.reader(f)
                hdr = [h.strip().lower() for h in next(reader)]
                idx = None
                for i, h in enumerate(hdr):
                    if 'started date' == h:
                        idx = i
                        break
                if idx is None:
                    return None
                dates = []
                for row in reader:
                    if idx < len(row) and row[idx].strip():
                        try:
                            dates.append(row[idx].split(' ')[0])
                        except Exception:
                            continue
                if not dates:
                    return None
                # simple min/max strings (not robust date parsing here)
                min_date = min(dates).replace('-', '')
                max_date = max(dates).replace('-', '')
                return os.path.join(os.path.dirname(input_path) or '.', f"Actual_Revolut_{min_date}_{max_date}_01.csv")
        except Exception:
            return None

    return convert_xlsx_to_csv(input_file=input_path)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Convert Revolut CSV/XLSX statement to Actual Budget format.")
    parser.add_argument('-i', '--input', help="Path to input CSV/XLSX file")
    args = parser.parse_args()

    convert_xlsx_to_csv(input_file=args.input)

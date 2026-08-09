"""
A Python script that takes a banking csv file as inputs another csv file for import into budgeting software.

Variables
Base Currency: GBP

Input file: transaction-history.csv
Output file: transaction-history-actual.csv

Input columns to use: ID, Direction, Created on, Source fee amount, Source fee currency, Source name, Source Amount (after fees), Source currency, Target name, Target amount (after fees), Target currency, Reference

Output columns: ID, Date, Payee, Memo, Amount

Mapping (Target = Source):
ID = ID
Date = Created on
Payee = 
	If Direction = IN then Source name
	If Direction = OUT then Target name
	If Direction = NEUTRAL and Source currency = Base Currency then Source name
	If Direction = NEUTRAL and Target currency = Base Currency then Target name
	
Memo = Reference
Amount = 
	If Direction = IN then Target amount (after fees)
	If Direction = OUT then Source amount (after fees) + Source fee amount
	If Direction = NEUTRAL and Source currency = Base Currency then Source amount (after fees) + Source fee amount
	If Direction = NEUTRAL and Target currency = Base Currency then Target amount (after fees)

Notes:
- The order of the input columns does not matter, and if there are additional columns with different header names, just ignore them.
- The column headers of the input file should not be case dependant
- If neither Source currency or Target currency match Base Currency, ignore the line completely.  This should happen for all lines, irrespective of the value of Direction.
"""

import csv
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import os

# --- CONFIGURATION ---
INPUT_FILENAME = 'transaction-history.csv'
OUTPUT_FILENAME = 'transaction-history-actual.csv'
BASE_CURRENCY = 'GBP'

# Expected input column names (used as canonical keys in row_data dictionary)
INPUT_HEADERS = [
    'ID', 'Direction', 'Created on', 'Source fee amount', 'Source fee currency', 
    'Source name', 'Source Amount (after fees)', 'Source currency', 
    'Target name', 'Target amount (after fees)', 'Target currency', 'Reference'
]

# Output column names
OUTPUT_HEADERS = ['ID', 'Date', 'Payee', 'Memo', 'Amount']

def safe_decimal_sum(value1, value2):
    """
    Safely converts two string values to Decimal and returns their sum.
    Handles potential empty strings or formatting issues.
    Returns Decimal(0) if conversion fails.
    """
    try:
        dec1 = Decimal(value1.replace(',', '')) if value1 else Decimal(0)
        dec2 = Decimal(value2.replace(',', '')) if value2 else Decimal(0)
        return dec1 + dec2
    except (InvalidOperation, TypeError):
        # Warning printed if a non-numeric value is found where a number is expected
        print(f"Warning: Failed to convert amounts: '{value1}', '{value2}'. Using 0.")
        return Decimal(0)

def transform_row(row_data):
    """
    Applies the custom banking rules to transform an input row (as a dictionary) 
    into an output row, filtering transactions that do not involve the BASE_CURRENCY.
    
    Args:
        row_data (dict): A dictionary representing a single row from the CSV, 
                         where keys are the standard INPUT_HEADERS (case-sensitive).
                         
    Returns:
        list: A list containing the output row data in OUTPUT_HEADERS order, or None if the row is skipped.
    """
    
    transaction_id = row_data.get('ID', '')
    status = row_data.get('Status', '').upper()
    direction = row_data.get('Direction', '').upper()
    created_on = row_data.get('Created on', '')
    source_fee = row_data.get('Source fee amount')
    source_name = row_data.get('Source name', '')
    source_amount = row_data.get('Source Amount (after fees)')
    source_currency = row_data.get('Source currency', '').upper()
    target_name = row_data.get('Target name', '')
    target_amount = row_data.get('Target amount (after fees)')
    target_currency = row_data.get('Target currency', '').upper()
    reference = row_data.get('Reference', '')

    # Filter out transactions that are not COMPLETED (e.g. CANCELLED, REFUNDED, PROCESSING)
    if status and status != 'COMPLETED':
        print(f"Skipping transaction {transaction_id} (Status: {status}): Not COMPLETED.")
        return None

    is_source_base = source_currency == BASE_CURRENCY
    is_target_base = target_currency == BASE_CURRENCY

    # GLOBAL FILTER: If neither Source currency nor Target currency match Base Currency, ignore the line completely.
    # This applies to all directions (IN, OUT, NEUTRAL).
    if not is_source_base and not is_target_base:
        print(f"Skipping transaction {transaction_id} (Direction: {direction}): Neither currency matches {BASE_CURRENCY}.")
        return None # Signal to skip this row
        
    payee = ''
    amount = Decimal(0)

    # --- Payee and Amount Mapping Logic (Only runs if the row passed the filter) ---
    
    if direction == 'IN':
        # Rule: If Direction = IN then Payee = Source name; Amount = Target amount (after fees)
        payee = source_name
        # We assume Target amount is the relevant amount since it passed the filter.
        amount = safe_decimal_sum(target_amount, '0')
    
    elif direction == 'OUT':
        # Rule: If Direction = OUT then Payee = Target name; Amount = -(Source amount (after fees) + Source fee amount)
        payee = target_name
        # We assume Source amount is the relevant amount since it passed the filter.
        total_expense = safe_decimal_sum(source_amount, source_fee)
        amount = -total_expense # Mark as negative/expense
        
    elif direction == 'NEUTRAL':
        # Rule: NEUTRAL transactions that involve the base currency
        
        if is_source_base and not is_target_base:
            # GBP spent to buy foreign currency (e.g. GBP -> EUR/USD wallet) (Expense/Transfer Out)
            payee = source_name
            total_expense = safe_decimal_sum(source_amount, source_fee)
            amount = -total_expense
            
        elif is_target_base:
            # Target is base currency (e.g. USD -> GBP exchange, or GBP -> GBP balance adjustment/cashback) (Income/Transfer In)
            payee = source_name if source_name != target_name else target_name
            amount = safe_decimal_sum(target_amount, '0')
        
        # If neither matched, it would have been skipped by the global filter above.

    # Format date to YYYY-MM-DD date string (stripping timestamp)
    date_str = created_on.split(' ')[0].strip() if created_on else ''

    # Construct the output row dictionary only if we did not skip
    output_row = {
        'ID': transaction_id,
        'Date': date_str,
        'Payee': payee,
        'Memo': reference,
        # Format the amount to 2 decimal places as a string
        'Amount': f"{amount:.2f}"
    }

    # Ensure the output order is correct based on OUTPUT_HEADERS
    return [output_row[col] for col in OUTPUT_HEADERS]

def convert_file(input_path, base_currency=None, preview=False):
    """Wrapper to convert a single wise CSV file. Returns the output filepath or None/False on error.
       - If base_currency is None, attempt detection from the file.
       - If preview=True, do not write outputs; instead return the expected output filename (if dates parseable) or None.
    """
    global INPUT_FILENAME, BASE_CURRENCY
    INPUT_FILENAME = input_path
    if base_currency:
        BASE_CURRENCY = base_currency.upper()
    else:
        detected = detect_base_currency_from_file(INPUT_FILENAME)
        if detected:
            BASE_CURRENCY = detected
        else:
            # fall back to default or interactive selection
            BASE_CURRENCY = BASE_CURRENCY or 'GBP'

    if preview:
        min_date, max_date = compute_date_range_from_file(INPUT_FILENAME)
        if min_date and max_date:
            return os.path.join(os.path.dirname(INPUT_FILENAME) or '.', f"wise-actual-{min_date.strftime('%Y%m%d')}-{max_date.strftime('%Y%m%d')}.csv")
        return None

    # Run the normal conversion which writes the file
    convert_csv()


def select_input_file():
    """
    Opens a file picker dialog to allow the user to select the input CSV file.
    
    Returns:
        str: The selected file path, or None if the user cancels.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    file_path = filedialog.askopenfilename(
        title="Select Input CSV File",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialdir="."
    )
    
    root.destroy()
    return file_path

def detect_base_currency_from_file(filename):
    """Try to infer the account base currency from the input CSV.

    Strategy:
    - Count occurrences of currencies in Source currency and Target currency columns.
    - Prefer currencies from "self" (balance) transactions where Source name == Target name and Source currency == Target currency.
    - Fallback to the most common currency across both Source and Target columns.
    Returns the currency code (uppercased) or None if detection failed.
    """
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            try:
                header = [h.strip().lower() for h in next(reader)]
            except StopIteration:
                return None

            # Find indices
            idx_source_currency = None
            idx_target_currency = None
            idx_source_name = None
            idx_target_name = None
            for i, h in enumerate(header):
                lh = h.lower()
                if 'source currency' == lh:
                    idx_source_currency = i
                if 'target currency' == lh:
                    idx_target_currency = i
                if 'source name' == lh:
                    idx_source_name = i
                if 'target name' == lh:
                    idx_target_name = i

            from collections import Counter
            overall = Counter()
            self_counts = Counter()

            for row in reader:
                src_cur = row[idx_source_currency].strip().upper() if idx_source_currency is not None and idx_source_currency < len(row) else ''
                tgt_cur = row[idx_target_currency].strip().upper() if idx_target_currency is not None and idx_target_currency < len(row) else ''
                src_name = row[idx_source_name].strip() if idx_source_name is not None and idx_source_name < len(row) else ''
                tgt_name = row[idx_target_name].strip() if idx_target_name is not None and idx_target_name < len(row) else ''

                if src_cur:
                    overall[src_cur] += 1
                if tgt_cur:
                    overall[tgt_cur] += 1

                # detect balance/self transactions
                if src_cur and tgt_cur and src_cur == tgt_cur and src_name and tgt_name and src_name == tgt_name:
                    self_counts[src_cur] += 1

            if self_counts:
                return self_counts.most_common(1)[0][0]

            if overall:
                return overall.most_common(1)[0][0]

    except Exception:
        return None


def compute_date_range_from_file(filename):
    """Scan file and return (min_date, max_date) as date objects or (None, None).
    Looks for 'Created on' values similar to convert_csv."""
    min_date = None
    max_date = None
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            try:
                input_header = [h.strip() for h in next(reader)]
            except StopIteration:
                return (None, None)
            normalized_header_map = {h.lower(): i for i, h in enumerate(input_header)}
            created_idx = normalized_header_map.get('created on')
            if created_idx is None:
                return (None, None)
            for row in reader:
                created_on = row[created_idx].strip() if created_idx < len(row) else ''
                if not created_on:
                    continue
                # Try multiple date formats
                transaction_date = None
                date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']
                for date_fmt in date_formats:
                    try:
                        transaction_date = datetime.strptime(created_on, date_fmt).date()
                        break
                    except ValueError:
                        continue
                if transaction_date:
                    if min_date is None or transaction_date < min_date:
                        min_date = transaction_date
                    if max_date is None or transaction_date > max_date:
                        max_date = transaction_date
    except Exception:
        return (None, None)
    return (min_date, max_date)


def convert_csv():
    """
    Main function to run the conversion process.
    Reads the input file and normalizes headers for case-insensitive access.
    Generates output filename based on the date range of transactions.
    """
    output_rows = []
    min_date = None
    max_date = None
    
    # 1. Setup Required Keys and Normalized Map
    standardized_required_keys = {h.lower() for h in INPUT_HEADERS}
    original_key_map = {h.lower(): h for h in INPUT_HEADERS} # map 'id' -> 'ID'

    try:
        with open(INPUT_FILENAME, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            
            # Read and normalize the header (handling potential leading/trailing whitespace)
            try:
                input_header = [h.strip() for h in next(reader)]
            except StopIteration:
                print("Error: Input file is empty.")
                return

            # Create a mapping from normalized (lowercase) header found in the file to its index
            normalized_header_map = {h.lower(): i for i, h in enumerate(input_header)}
            
            # Check for required headers
            if not standardized_required_keys.issubset(normalized_header_map.keys()):
                missing = standardized_required_keys - set(normalized_header_map.keys())
                print(f"Error: The input file is missing required columns (case-insensitive): {', '.join(missing)}")
                return
                
            # 2. Process Rows
            for row in reader:
                # Create a standardized row_data dictionary using the canonical keys from INPUT_HEADERS
                row_data = {}
                
                for lower_key, original_key in original_key_map.items():
                    # Get the column index using the normalized key found in the file
                    col_index = normalized_header_map.get(lower_key)
                    
                    # Store the value in row_data using the canonical key (e.g., 'ID')
                    if col_index is not None and col_index < len(row):
                         row_data[original_key] = row[col_index]
                    else:
                         # Use an empty string if the column value is missing for some reason
                         row_data[original_key] = ''

                # --- Transformation and Filtering ---
                transformed = transform_row(row_data)
                if transformed is not None:
                    output_rows.append(transformed)
                    
                    # Track date range from the "Created on" field in the original row data
                    created_on = row_data.get('Created on', '').strip()
                    if created_on:
                        try:
                            # Try multiple date formats
                            transaction_date = None
                            date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']
                            for date_fmt in date_formats:
                                try:
                                    transaction_date = datetime.strptime(created_on, date_fmt).date()
                                    break
                                except ValueError:
                                    continue
                            
                            if transaction_date:
                                if min_date is None or transaction_date < min_date:
                                    min_date = transaction_date
                                if max_date is None or transaction_date > max_date:
                                    max_date = transaction_date
                        except Exception:
                            # If date parsing fails, skip this transaction's date tracking
                            pass
            
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILENAME}' not found. Please run generate_sample_input() first.")
        return
    except Exception as e:
        print(f"An unexpected error occurred during reading/transformation: {e}")
        return

    # 3. Generate output filename based on date range
    if min_date and max_date:
        min_date_str = min_date.strftime('%Y%m%d')
        max_date_str = max_date.strftime('%Y%m%d')
        output_filename = f"wise-actual-{min_date_str}-{max_date_str}.csv"
    else:
        # If dates couldn't be parsed, use current date as fallback
        today = datetime.now().strftime('%Y%m%d')
        output_filename = f"wise-actual-{today}-{today}.csv"
    
    # Place output file in the same directory as the input file
    input_directory = os.path.dirname(INPUT_FILENAME)
    if input_directory:
        output_filename = os.path.join(input_directory, output_filename)
    
    # 4. Write the transformed data to the output file
    try:
        with open(output_filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(OUTPUT_HEADERS)
            writer.writerows(output_rows)
        
        print(f"\nSuccessfully converted {len(output_rows)} transactions.")
        print(f"Output saved to '{output_filename}'")
        
    except Exception as e:
        print(f"An error occurred during writing the output file: {e}")

# --- Sample Data Generation for Testing ---

def detect_wise_file(path):
    try:
        with open(path, encoding='utf-8-sig', newline='') as f:
            head = f.read(4096).lower()
            return 'source currency' in head and 'target currency' in head
    except Exception:
        return False


def generate_sample_input():

    """Generates a sample CSV file for testing, including case-insensitive headers and skip cases."""
    
    # 1. Standard data (will be written with standard headers)
    sample_data_standard = [
        # ID,Direction,Created on,Source fee amount,Source fee currency,Source name,Source Amount (after fees),Source currency,Target name,Target amount (after fees),Target currency,Reference
        ['TX1001', 'IN', '2024-10-01', '0.00', 'GBP', 'Client Alpha', '0.00', 'GBP', 'My GBP Account', '1500.50', 'GBP', 'Invoice 456 Payment'], 
        ['TX1002', 'OUT', '2024-10-02', '1.00', 'GBP', 'My GBP Account', '49.00', 'GBP', 'Supermarket Ltd', '0.00', 'GBP', 'Grocery Shopping'], 
        ['TX1003', 'NEUTRAL', '2024-10-03', '2.50', 'GBP', 'My GBP Account', '100.00', 'GBP', 'USD Exchange Wallet', '125.00', 'USD', 'Buy USD for trip'], 
        ['TX1004', 'NEUTRAL', '2024-10-04', '0.00', 'USD', 'USD Exchange Wallet', '100.00', 'USD', 'My GBP Account', '79.25', 'GBP', 'Sell USD after trip'], 
        ['TX1005', 'OUT', '2024-10-05', '0.00', 'GBP', 'My GBP Account', '9.99', 'GBP', 'Streaming Service', '0.00', 'GBP', 'Monthly Subscription'], 
    ]

    # 2. Data to demonstrate case-insensitivity and filtering
    # Note the varied capitalization of headers.
    
    # This transaction should pass (OUT, involves GBP)
    case_insensitive_pass = ['TX1006', '2024-10-06', 'Target Name Six', 'OUT', 'Ref for six', '120.00', 'GBP', '0.00', 'GBP', 'My Account', '0.00', 'USD', '120.00']
    
    # This NEUTRAL transaction should be SKIPPED (neither USD nor EUR is GBP)
    case_insensitive_skip_neutral = ['TX1007', '2024-10-07', 'Target Name Seven', 'NEUTRAL', 'Ref for seven', '50.00', 'USD', '1.00', 'USD', 'EUR Wallet', '45.00', 'EUR', '50.00']
    
    # NEW SKIP EXAMPLE: This IN transaction should now be SKIPPED by the global filter (neither USD nor EUR is GBP)
    non_gbp_in_skip = ['TX1008', '2024-10-08', 'Vendor X', 'IN', 'USD to EUR transfer', '10.00', 'USD', '0.00', 'USD', 'EUR Wallet', '8.50', 'EUR', '10.00']


    reordered_headers = [
        'ID', 'Created On', 'Target name', 'Direction', 'Reference', 
        'Source Amount (after fees)', 'Source currency', 'Source fee amount', 
        'Source fee currency', 'Source name', 'Target amount (after fees)', 
        'Target currency', 'Extra Column (ignore)'
    ]
    
    sample_data_mixed = [
        case_insensitive_pass,
        case_insensitive_skip_neutral,
        non_gbp_in_skip
    ]

    try:
        # Create a combined sample file
        with open(INPUT_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write a standard header set
            writer.writerow(INPUT_HEADERS)
            writer.writerows(sample_data_standard)
            
            # Write the mixed-case/reordered header and data
            writer.writerow(reordered_headers)
            writer.writerows(sample_data_mixed)
            
        print(f"Sample input file '{INPUT_FILENAME}' created successfully.")
    except Exception as e:
        print(f"Error generating sample file: {e}")


def select_base_currency():
    """
    Prompts the user to select a base currency from a list of options.
    
    Returns:
        str: The selected currency code (GBP, USD, EUR, or ZAR), or None if user quits.
    """
    currencies = ['GBP', 'USD', 'EUR', 'ZAR']
    
    print("\n--- Select Base Currency ---")
    for i, currency in enumerate(currencies, start=1):
        print(f"{i}. {currency}")
    print("q. Quit")
    
    while True:
        try:
            choice = input("\nEnter the number of your choice (or 'q' to quit): ").strip().lower()
            
            if choice == 'q':
                print("Exiting program.")
                return None
            
            choice_index = int(choice) - 1
            
            if 0 <= choice_index < len(currencies):
                selected_currency = currencies[choice_index]
                print(f"Base currency set to: {selected_currency}\n")
                return selected_currency
            else:
                print("Invalid choice. Please enter a number between 1 and 4, or 'q' to quit.")
        except ValueError:
            print("Invalid input. Please enter a valid number or 'q' to quit.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Convert Wise CSV statement to Actual Budget format.")
    parser.add_argument('-i', '--input', help="Path to input CSV file")
    parser.add_argument('-b', '--base-currency', default='GBP', help="Base currency code (default: GBP)")
    args = parser.parse_args()

    if args.input:
        INPUT_FILENAME = args.input
        if args.base_currency:
            BASE_CURRENCY = args.base_currency.upper()
            print(f"Running in headless mode. Input: {INPUT_FILENAME}, Base Currency: {BASE_CURRENCY}")
        else:
            # Try to auto-detect base currency from the input file
            detected = detect_base_currency_from_file(INPUT_FILENAME)
            if detected:
                BASE_CURRENCY = detected
                print(f"Running in headless mode. Input: {INPUT_FILENAME}, auto-detected Base Currency: {BASE_CURRENCY}")
            else:
                # Fallback to interactive selection if detection failed
                print("Could not detect base currency from file. Falling back to interactive prompt.")
                BASE_CURRENCY = select_base_currency()
                if BASE_CURRENCY is None:
                    exit()
    else:
        # 1. Prompt user to select input file via GUI
        selected_file = select_input_file()
        
        if selected_file is None:
            print("No file selected. Exiting program.")
            exit()
        
        INPUT_FILENAME = selected_file
        print(f"Input file set to: {INPUT_FILENAME}")
        
        # 2. Try to auto-detect base currency; if that fails, prompt the user
        detected = detect_base_currency_from_file(INPUT_FILENAME)
        if detected:
            BASE_CURRENCY = detected
            print(f"Auto-detected base currency: {BASE_CURRENCY}")
        else:
            BASE_CURRENCY = select_base_currency()
            if BASE_CURRENCY is None:
                exit()
    
    # Run the conversion
    convert_csv()
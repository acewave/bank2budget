import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import re
import argparse

def replace_multiple_spaces(string):
    # Use regular expression to replace multiple spaces with a single space
    pattern = re.compile(r'\s+')
    replaced_string = re.sub(pattern, ' ', string)
    return replaced_string

def process_csv(in_filename):
    trans_date = None
    trans_date_min = datetime.max
    trans_date_max = datetime.min

    is_cc = False   # is credit card CSV
    ynab_csv = []
    ynab_csv.append(["Date", "Payee", "Memo", "Outflow", "Inflow"])

    try:
        in_folder = os.path.dirname(in_filename)
        with open(in_filename, encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            header_line = 9999999   # large int

            for row in csv_reader:
                
                if len(row) == 0:
                    line_count += 1
                    continue        # skip blank row

                if line_count == 0:
                    if row[0] == "Card No":
                        is_cc = True
                        filename_suffix = "YNAB_CC_" + row[1][-4:]
                    else:
                        account_number = row[0].replace("'", "0")   # fix for apostrophe in input file
                        filename_suffix = "YNAB_" + account_number

                if row[0] == "Reference No" or row[0] == "Transaction Date":
                    header_line = line_count

                if line_count > header_line:
                        if is_cc:
                            trans_date = datetime.strptime(row[1], '%d %b %Y')
                            trans_date_string = trans_date.strftime('%m/%d/%Y')
                            
                            outflow = ''
                            inflow = ''

                            if row[3].strip() == "Dr":
                                outflow = row[4]
                            else:
                                inflow = row[4]
                            
                            description = replace_multiple_spaces(row[2]).strip()

                            ynab_csv.append([trans_date_string, description, description, outflow, inflow])

                        else:                        
                            trans_date = datetime.strptime(row[0], '%d %b %Y')
                            trans_date_string = trans_date.strftime('%m/%d/%Y')
                            description = replace_multiple_spaces(row[2]).strip()
                            ynab_csv.append([trans_date_string, description, description, row[3], row[4]])                    

                if trans_date is not None and trans_date < trans_date_min:
                    trans_date_min = trans_date

                if trans_date is not None and trans_date > trans_date_max:
                    trans_date_max = trans_date

                line_count += 1

    except:
        print(f'Error reading file {in_filename}')

    try:
        trans_date_min_string = trans_date_min.strftime('%Y%m%d')
        trans_date_max_string = trans_date_max.strftime('%Y%m%d')
        filename_suffix = filename_suffix + "_" + trans_date_min_string + "_" + trans_date_max_string
        out_filename = os.path.join(in_folder, filename_suffix + ".csv")
        
        with open(out_filename, mode='w', newline='', encoding='utf-8') as ynab_csv_file:
            ynab_writer = csv.writer(ynab_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for line in ynab_csv:
                ynab_writer.writerow([line[0], line[1], line[2], line[3], line[4]])
        print(f'Input: {in_filename} Output: {out_filename}')
    except:
        print(f'Error writing file {out_filename}')

def process_csv_files_select():
    root = tk.Tk()
    root.withdraw()

    # Prompt the user to select multiple CSV files
    csv_files = filedialog.askopenfilenames(
        initialdir='/', title='Select CSV files',
        filetypes=(('CSV files', '*.csv'), ('All files', '*.*'))
    )

    if not csv_files:
        print("No CSV files selected.")
        return

    print(f"Fixing {len(csv_files)} CSV file(s)...")

    for csv_file in csv_files:
        process_csv(csv_file)

def process_csv_files():
    file_count = 0

    for file in os.listdir():
        if file.endswith('.csv') and not file.startswith('YNAB_'):
            process_csv(file)
            file_count += 1

    print(f'{file_count} file(s) processed.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', action='store_true', help='Run with interactive multiple file select option')
    args = parser.parse_args()

    if args.i:
        print("Interactive mode - user must select CSV files to process.")
        process_csv_files_select()
    else:
        print("Regular mode - all CSV files in current folder will be processed.")
        process_csv_files()

if __name__ == '__main__':
    main()






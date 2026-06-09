import pandas as pd
import os
import csv
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def convert_xlsx_to_csv():
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

    # Map the columns and remove the timestamp from 'Started Date'
    df['Date'] = df['Started Date'].dt.date
    df['Payee'] = df['Description']
    df['Memo'] = df['Description']
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

# Run the function
convert_xlsx_to_csv()

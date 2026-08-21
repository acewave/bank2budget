# bank-2-budget

Converts bank exported CSV files into Actual Budget / YNAB import format.
All CSV files in the script folder will be parsed, except those beginning with "Actual_".
New files will be created for each in the format "Actual_(Account Number)_(First Transaction Date)_(Last Transaction Date).CSV".
In the case of credit card files, (Account Number) will be "CC_XXXX", where XXXX are the last 4 digits of the credit card.
Regular and Credit Card export formats (current and historical) supported.

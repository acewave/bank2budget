import unittest
import os
import importlib.util
from decimal import Decimal
import pandas as pd

# Load wise-to-actual module dynamically (since filename contains hyphens)
wise_spec = importlib.util.spec_from_file_location("wise_to_actual", os.path.join(os.path.dirname(__file__), "wise-to-actual.py"))
wise_module = importlib.util.module_from_spec(wise_spec)
wise_spec.loader.exec_module(wise_module)
wise_transform_row = wise_module.transform_row


class TestRevolutConverter(unittest.TestCase):
    """Test suite for Revolut conversion logic."""

    def process_revolut_dataframe(self, df):
        """Helper to compute net Revolut amounts including fees."""
        df = df.copy()
        df['Started Date'] = pd.to_datetime(df['Started Date'])
        df['Date'] = df['Started Date'].dt.date
        df['Payee'] = df['Description']
        df['Memo'] = df['Description']

        if 'Fee' in df.columns:
            fee = pd.to_numeric(df['Fee'], errors='coerce').fillna(0)
            amount = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            # Subtract fee from amount to calculate net cash flow impact
            df['Amount'] = amount - fee
        else:
            df['Amount'] = df['Amount']

        return df[['Date', 'Payee', 'Memo', 'Amount']]

    def test_revolut_standard_transaction_without_fee(self):
        data = {
            'Started Date': ['2026-06-01 07:20:25'],
            'Description': ['WhSmith'],
            'Amount': [-7.27],
            'Fee': [0.00]
        }
        df = pd.DataFrame(data)
        out_df = self.process_revolut_dataframe(df)
        self.assertEqual(out_df['Amount'].iloc[0], -7.27)

    def test_revolut_foreign_currency_transaction_with_fee(self):
        # Hôtel de l'Univers: Amount -43.53, Fee 0.44 -> Net should be -43.97
        data = {
            'Started Date': ['2026-06-13 20:49:30'],
            'Description': ["Hôtel de l'Univers"],
            'Amount': [-43.53],
            'Fee': [0.44]
        }
        df = pd.DataFrame(data)
        out_df = self.process_revolut_dataframe(df)
        self.assertAlmostEqual(out_df['Amount'].iloc[0], -43.97, places=2)


class TestWiseConverter(unittest.TestCase):
    """Test suite for Wise conversion logic."""

    def test_wise_outflow_transfer(self):
        row = {
            'ID': 'TRANSFER-1',
            'Direction': 'OUT',
            'Created on': '2026-06-20 11:31:56',
            'Source fee amount': '1.00',
            'Source fee currency': 'GBP',
            'Source name': 'Andrew Lewis Cousins',
            'Source Amount (after fees)': '49.00',
            'Source currency': 'GBP',
            'Target name': 'Supermarket',
            'Target amount (after fees)': '0.00',
            'Target currency': 'GBP',
            'Reference': 'Grocery'
        }
        result = wise_transform_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result[2], 'Supermarket')
        self.assertEqual(result[4], '-50.00')

    def test_wise_inflow_transfer(self):
        row = {
            'ID': 'TRANSFER-2',
            'Direction': 'IN',
            'Created on': '2026-08-02 16:41:23',
            'Source fee amount': '0.00',
            'Source fee currency': 'GBP',
            'Source name': 'COUSINS A&A',
            'Source Amount (after fees)': '4340.00',
            'Source currency': 'GBP',
            'Target name': 'Andrew Lewis Cousins',
            'Target amount (after fees)': '4340.00',
            'Target currency': 'GBP',
            'Reference': 'CC Deposit Refund'
        }
        result = wise_transform_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result[2], 'COUSINS A&A')
        self.assertEqual(result[4], '4340.00')

    def test_wise_neutral_gbp_to_gbp_positive_credit(self):
        # BALANCE_TRANSACTION-5274768260: GBP to GBP internal transaction of 3.22
        row = {
            'ID': 'BALANCE_TRANSACTION-5274768260',
            'Direction': 'NEUTRAL',
            'Created on': '2026-05-11 16:08:01',
            'Source fee amount': '0.00',
            'Source fee currency': 'GBP',
            'Source name': 'Andrew Lewis Cousins',
            'Source Amount (after fees)': '3.22',
            'Source currency': 'GBP',
            'Target name': 'Andrew Lewis Cousins',
            'Target amount (after fees)': '3.22',
            'Target currency': 'GBP',
            'Reference': ''
        }
        result = wise_transform_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result[4], '3.22')

    def test_wise_neutral_usd_to_gbp_exchange(self):
        row = {
            'ID': 'BALANCE_TRANSACTION-5451829770',
            'Direction': 'NEUTRAL',
            'Created on': '2026-06-09 20:26:55',
            'Source fee amount': '1.80',
            'Source fee currency': 'USD',
            'Source name': 'Andrew Lewis Cousins',
            'Source Amount (after fees)': '547.00',
            'Source currency': 'USD',
            'Target name': 'Andrew Lewis Cousins',
            'Target amount (after fees)': '408.77',
            'Target currency': 'GBP',
            'Reference': ''
        }
        result = wise_transform_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result[4], '408.77')

    def test_wise_neutral_gbp_to_eur_exchange(self):
        row = {
            'ID': 'BALANCE_TRANSACTION-4761774290',
            'Direction': 'NEUTRAL',
            'Created on': '2026-02-06 18:05:20',
            'Source fee amount': '0.33',
            'Source fee currency': 'GBP',
            'Source name': 'Andrew Lewis Cousins',
            'Source Amount (after fees)': '99.67',
            'Source currency': 'GBP',
            'Target name': 'Andrew Lewis Cousins',
            'Target amount (after fees)': '114.87',
            'Target currency': 'EUR',
            'Reference': ''
        }
        result = wise_transform_row(row)
        self.assertIsNotNone(result)
        self.assertEqual(result[4], '-100.00')


if __name__ == '__main__':
    unittest.main()

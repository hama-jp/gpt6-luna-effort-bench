import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.categorize import categorize, parse_rules
from ledgerlite.dedupe import dedupe, normalise
from ledgerlite.importer import ImportErrorLL, parse_banka_date, parse_number, read_statement
from ledgerlite.models import Transaction, to_money
from ledgerlite.report import monthly_summary


class MoneyRegressionTest(unittest.TestCase):
    def test_float_input_uses_decimal_half_up(self):
        self.assertEqual(to_money(2.675), Decimal("2.68"))
        self.assertEqual(to_money(-2.675), Decimal("-2.68"))


class ImportRegressionTest(unittest.TestCase):
    def test_banka_uses_documented_day_month_order(self):
        self.assertEqual(parse_banka_date("04/03/2026"), date(2026, 3, 4))

    def test_statement_import_keeps_ambiguous_date_in_march(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.csv"
            path.write_text("Date,Description,Amount\n04/03/2026,Bakery,-5.00\n", encoding="utf-8")
            [tx] = read_statement(path)
        self.assertEqual(tx.date, date(2026, 3, 4))

    def test_banka_does_not_accept_undocumented_us_date_order(self):
        with self.assertRaises(ImportErrorLL):
            parse_banka_date("03/25/2026")

    def test_number_accepts_repeated_thousands_separators(self):
        self.assertEqual(parse_number("1,234,567.89"), Decimal("1234567.89"))

    def test_number_rejects_malformed_grouping_and_non_finite_values(self):
        for value in ("12,34.56", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ImportErrorLL):
                parse_number(value)


class CategorizeRegressionTest(unittest.TestCase):
    def test_highest_priority_wins_and_ties_keep_file_order(self):
        rules = parse_rules(
            "1 | Amazon | Shopping\n"
            "9 | Amazon Prime | Subscriptions\n"
            "9 | Prime Video | Streaming\n"
        )
        tx = Transaction(date(2026, 3, 1), "Amazon Prime Video", Decimal("-9"))
        categorize([tx], rules)
        self.assertEqual(tx.category, "Subscriptions")


class DedupeRegressionTest(unittest.TestCase):
    def test_normalisation_collapses_whitespace(self):
        self.assertEqual(normalise("  COFFEE   SHOP\t "), "coffee shop")

    def test_keeps_maximum_per_source_multiplicity(self):
        a1 = Transaction(date(2026, 3, 1), "Coffee  Shop", Decimal("-4"), source="a.csv")
        a2 = Transaction(date(2026, 3, 1), "Coffee Shop", Decimal("-4"), source="a.csv")
        b1 = Transaction(date(2026, 3, 1), "coffee\tshop", Decimal("-4"), source="b.csv")
        b2 = Transaction(date(2026, 3, 1), "Coffee Shop", Decimal("-4"), source="b.csv")
        b3 = Transaction(date(2026, 3, 1), "Coffee Shop", Decimal("-4"), source="b.csv")

        self.assertEqual(dedupe([a1, a2, b1, b2, b3]), [a1, a2, b3])

    def test_identical_rows_in_one_file_are_all_kept(self):
        first = Transaction(date(2026, 3, 1), "Coffee", Decimal("-4"), source="a.csv")
        second = Transaction(date(2026, 3, 1), "Coffee", Decimal("-4"), source="a.csv")
        self.assertEqual(dedupe([first, second]), [first, second])


class ReportRegressionTest(unittest.TestCase):
    def test_month_includes_last_day_and_excludes_next_month(self):
        last_day = Transaction(date(2026, 3, 31), "Groceries", Decimal("-10"), category="Food")
        next_month = Transaction(date(2026, 4, 1), "Groceries", Decimal("-20"), category="Food")
        summary = monthly_summary([last_day, next_month], 2026, 3)
        self.assertEqual(summary["expenses"], {"Food": Decimal("10.00")})

    def test_refund_reduces_net_category_and_merchant_spending(self):
        txs = [
            Transaction(date(2026, 3, 4), "Shoe Store", Decimal("-80"), category="Clothing"),
            Transaction(date(2026, 3, 10), " shoe   store ", Decimal("20"), category="Clothing"),
            Transaction(date(2026, 3, 12), "Salary", Decimal("100"), category="Income"),
        ]
        summary = monthly_summary(txs, 2026, 3)
        self.assertEqual(summary["expenses"], {"Clothing": Decimal("60.00")})
        self.assertEqual(summary["income"], Decimal("100.00"))
        self.assertEqual(summary["total_expenses"], Decimal("60.00"))
        self.assertEqual(summary["net"], Decimal("40.00"))
        self.assertEqual(summary["top_merchants"], [("shoe store", Decimal("60.00"))])

    def test_top_merchant_values_are_decimal_and_ties_are_alphabetical(self):
        txs = [
            Transaction(date(2026, 3, 2), "Zeta", Decimal("-0.10"), category="Food"),
            Transaction(date(2026, 3, 3), "Alpha", Decimal("-0.10"), category="Food"),
        ]
        top = monthly_summary(txs, 2026, 3)["top_merchants"]
        self.assertEqual(top, [("alpha", Decimal("0.10")), ("zeta", Decimal("0.10"))])
        self.assertTrue(all(isinstance(amount, Decimal) for _, amount in top))

    def test_merchants_with_zero_rounded_spending_are_omitted(self):
        tx = Transaction(date(2026, 3, 2), "Tiny", Decimal("-0.001"), category="Food")
        self.assertEqual(monthly_summary([tx], 2026, 3)["top_merchants"], [])

    def test_positive_net_category_is_not_an_expense_category(self):
        txs = [
            Transaction(date(2026, 3, 1), "Reimbursement", Decimal("-5"), category="Reimbursements"),
            Transaction(date(2026, 3, 2), "Reimbursement", Decimal("8"), category="Reimbursements"),
        ]
        summary = monthly_summary(txs, 2026, 3)
        self.assertEqual(summary["expenses"], {})
        self.assertEqual(summary["income"], Decimal("8.00"))


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.categorize import categorize, parse_rules
from ledgerlite.dedupe import dedupe, normalise
from ledgerlite.importer import parse_number, read_statement
from ledgerlite.models import Transaction, to_money
from ledgerlite.report import monthly_summary


class ImporterRegressionTest(unittest.TestCase):
    def test_banka_uses_documented_day_first_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.csv"
            path.write_text(
                "Date,Description,Amount\n04/03/2026,Bakery,-8.25\n",
                encoding="utf-8",
            )
            [tx] = read_statement(path)

        self.assertEqual(tx.date, date(2026, 3, 4))

    def test_bankb_removes_all_thousands_separators(self):
        self.assertEqual(parse_number("1,234,567.89"), Decimal("1234567.89"))


class CategorizeRegressionTest(unittest.TestCase):
    def test_highest_priority_rule_wins(self):
        rules = parse_rules(
            "1 | Amazon | Shopping\n"
            "9 | Amazon Prime | Subscriptions\n"
        )
        tx = Transaction(date(2026, 3, 1), "Amazon Prime Video", Decimal("-8.99"))

        categorize([tx], rules)

        self.assertEqual(tx.category, "Subscriptions")

    def test_priority_ties_keep_file_order(self):
        rules = parse_rules("9 | amazon | First\n9 | prime | Second\n")
        tx = Transaction(date(2026, 3, 1), "Amazon Prime", Decimal("-8.99"))

        categorize([tx], rules)

        self.assertEqual(tx.category, "First")


class DedupeRegressionTest(unittest.TestCase):
    def test_same_file_rows_are_kept_and_cross_file_count_is_maximum(self):
        a1 = Transaction(date(2026, 3, 1), "Coffee  Shop", Decimal("-4"), source="a.csv")
        a2 = Transaction(date(2026, 3, 1), "Coffee  Shop", Decimal("-4"), source="a.csv")
        b1 = Transaction(date(2026, 3, 1), " coffee shop ", Decimal("-4"), source="b.csv")
        b2 = Transaction(date(2026, 3, 1), "coffee shop", Decimal("-4"), source="b.csv")
        b3 = Transaction(date(2026, 3, 1), "coffee shop", Decimal("-4"), source="b.csv")

        self.assertEqual(dedupe([a1, a2, b1, b2, b3]), [a1, a2, b3])

    def test_normalise_collapses_whitespace(self):
        self.assertEqual(normalise("  Book\t  Store  "), "book store")


class ReportRegressionTest(unittest.TestCase):
    def test_month_includes_last_day(self):
        last_day = Transaction(date(2026, 3, 31), "Rent", Decimal("-10"), category="Housing")
        next_month = Transaction(date(2026, 4, 1), "Rent", Decimal("-20"), category="Housing")

        summary = monthly_summary([last_day, next_month], 2026, 3)

        self.assertEqual(summary["expenses"], {"Housing": Decimal("10.00")})

    def test_refunds_reduce_expense_category_net(self):
        txs = [
            Transaction(date(2026, 3, 2), "Shoes", Decimal("-100"), category="Clothing"),
            Transaction(date(2026, 3, 4), "Shoe refund", Decimal("20"), category="Clothing"),
            Transaction(date(2026, 3, 5), "Salary", Decimal("1000"), category="Salary"),
        ]

        summary = monthly_summary(txs, 2026, 3)

        self.assertEqual(summary["expenses"], {"Clothing": Decimal("80.00")})
        self.assertEqual(summary["income"], Decimal("1000.00"))
        self.assertEqual(summary["net"], Decimal("920.00"))

    def test_top_merchants_are_decimal_and_normalized(self):
        txs = [
            Transaction(date(2026, 3, 1), "Coffee  Shop", Decimal("-2"), category="Food"),
            Transaction(date(2026, 3, 2), " coffee shop ", Decimal("-1"), category="Food"),
            Transaction(date(2026, 3, 3), "Coffee Shop", Decimal("0.50"), category="Food"),
        ]

        summary = monthly_summary(txs, 2026, 3)

        self.assertEqual(summary["top_merchants"], [("coffee shop", Decimal("2.50"))])
        self.assertIsInstance(summary["top_merchants"][0][1], Decimal)


class MoneyRegressionTest(unittest.TestCase):
    def test_float_input_rounds_from_its_decimal_spelling(self):
        self.assertEqual(to_money(1.005), Decimal("1.01"))


if __name__ == "__main__":
    unittest.main()

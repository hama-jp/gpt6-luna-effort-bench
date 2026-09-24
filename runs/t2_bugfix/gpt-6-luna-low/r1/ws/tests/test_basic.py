import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.categorize import categorize, parse_rules
from ledgerlite.dedupe import dedupe
from ledgerlite.importer import read_statement
from ledgerlite.models import Transaction
from ledgerlite.report import monthly_summary


def write(tmp, name, text):
    p = Path(tmp) / name
    p.write_text(text, encoding="utf-8")
    return p


class ImporterTest(unittest.TestCase):
    def test_banka(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount\n25/03/2026,Coffee Shop,-4.50\n")
            [tx] = read_statement(p)
            self.assertEqual(tx.date, date(2026, 3, 25))
            self.assertEqual(tx.amount, Decimal("-4.50"))
            self.assertEqual(tx.source, "a.csv")

    def test_ambiguous_banka_date_prefers_day_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount\n04/03/2026,Bakery,-4.50\n")
            [tx] = read_statement(p)
            self.assertEqual(tx.date, date(2026, 3, 4))

    def test_bankb(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "b.csv", "Posted,Payee,Debit,Credit\n2026-03-02,Salary,,3000.00\n2026-03-03,Rent,950.00,\n")
            txs = read_statement(p)
            self.assertEqual([t.amount for t in txs], [Decimal("3000.00"), Decimal("-950.00")])


class CategorizeTest(unittest.TestCase):
    def test_simple(self):
        rules = parse_rules("10 | coffee | Food\n5 | re:^rent | Housing\n")
        txs = [Transaction(date(2026, 3, 1), "COFFEE SHOP", Decimal("-3")),
               Transaction(date(2026, 3, 1), "Rent March", Decimal("-900")),
               Transaction(date(2026, 3, 1), "Mystery", Decimal("-1"))]
        categorize(txs, rules)
        self.assertEqual([t.category for t in txs], ["Food", "Housing", "Uncategorized"])

    def test_highest_priority_wins(self):
        rules = parse_rules("1 | Amazon | Shopping\n9 | Prime | Subscriptions\n")
        tx = Transaction(date(2026, 3, 1), "Prime Video", Decimal("-10"))
        categorize([tx], rules)
        self.assertEqual(tx.category, "Subscriptions")


class DedupeTest(unittest.TestCase):
    def test_cross_file_duplicate_removed(self):
        a = Transaction(date(2026, 3, 1), "Book Store", Decimal("-20"), source="a.csv")
        b = Transaction(date(2026, 3, 1), "book store", Decimal("-20"), source="b.csv")
        self.assertEqual(dedupe([a, b]), [a])

    def test_same_file_rows_kept_and_cross_file_max_count_kept(self):
        def tx(source):
            return Transaction(date(2026, 3, 1), " Coffee  shop ", Decimal("-3"), source=source)
        a1, a2, b1 = tx("a.csv"), tx("a.csv"), tx("b.csv")
        self.assertEqual(dedupe([a1, a2, b1]), [a1, a2])

    def test_normalise_collapses_whitespace(self):
        from ledgerlite.dedupe import normalise
        self.assertEqual(normalise("  Coffee\t  Shop "), "coffee shop")


class ReportTest(unittest.TestCase):
    def test_summary(self):
        txs = [Transaction(date(2026, 3, 2), "Salary", Decimal("3000"), category="Salary"),
               Transaction(date(2026, 3, 3), "Rent", Decimal("-950"), category="Housing"),
               Transaction(date(2026, 3, 4), "Coffee", Decimal("-4.50"), category="Food")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["income"], Decimal("3000.00"))
        self.assertEqual(s["total_expenses"], Decimal("954.50"))
        self.assertEqual(s["net"], Decimal("2045.50"))

    def test_includes_last_day_of_month(self):
        tx = Transaction(date(2026, 3, 31), "Rent", Decimal("-10"), category="Housing")
        self.assertEqual(monthly_summary([tx], 2026, 3)["total_expenses"], Decimal("10.00"))

    def test_refund_reduces_expense_and_merchant(self):
        txs = [Transaction(date(2026, 3, 1), "Shoes", Decimal("-50"), category="Clothing"),
               Transaction(date(2026, 3, 2), "Shoes", Decimal("20"), category="Clothing")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["expenses"], {"Clothing": Decimal("30.00")})
        self.assertEqual(s["top_merchants"], [("shoes", Decimal("30"))])

    def test_income_categories_are_not_counted_as_expenses(self):
        txs = [Transaction(date(2026, 3, 1), "Pay", Decimal("10"), category="Salary"),
               Transaction(date(2026, 3, 2), "Reversal", Decimal("-10"), category="Salary")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["expenses"], {})
        self.assertEqual(s["income"], Decimal("10.00"))


if __name__ == "__main__":
    unittest.main()

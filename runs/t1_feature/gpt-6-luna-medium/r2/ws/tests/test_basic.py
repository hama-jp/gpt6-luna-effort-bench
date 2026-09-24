import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.categorize import categorize, parse_rules
from ledgerlite.dedupe import dedupe
from ledgerlite.importer import read_statement
from ledgerlite.fx import MissingRateError, convert, load_rates
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


class DedupeTest(unittest.TestCase):
    def test_cross_file_duplicate_removed(self):
        a = Transaction(date(2026, 3, 1), "Book Store", Decimal("-20"), source="a.csv")
        b = Transaction(date(2026, 3, 1), "book store", Decimal("-20"), source="b.csv")
        self.assertEqual(dedupe([a, b]), [a])


class ReportTest(unittest.TestCase):
    def test_summary(self):
        txs = [Transaction(date(2026, 3, 2), "Salary", Decimal("3000"), category="Salary"),
               Transaction(date(2026, 3, 3), "Rent", Decimal("-950"), category="Housing"),
               Transaction(date(2026, 3, 4), "Coffee", Decimal("-4.50"), category="Food")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["income"], Decimal("3000.00"))
        self.assertEqual(s["total_expenses"], Decimal("954.50"))
        self.assertEqual(s["net"], Decimal("2045.50"))


class MultiCurrencyTest(unittest.TestCase):
    def test_import_currency_and_base_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount,Currency\n25/03/2026,Coffee,-4.50,usd\n26/03/2026,Tea,-2.00,\n")
            txs = read_statement(p, base="gbp")
            self.assertEqual([t.currency for t in txs], ["USD", "GBP"])
            self.assertTrue(all(t.original_amount is None for t in txs))

    def test_conversion_latest_prior_with_seven_day_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "rates.csv", "date,currency,rate\n2026-03-18,usd,0.9\n2026-03-24,USD,0.8\n")
            txs = [Transaction(date(2026, 3, 25), "x", Decimal("-1.005"), currency="USD"),
                   Transaction(date(2026, 3, 25), "y", Decimal("2"))]
            self.assertIs(convert(txs, load_rates(p)), txs)
            self.assertEqual(txs[0].amount, Decimal("-0.80"))
            self.assertEqual(txs[0].original_amount, Decimal("-1.005"))
            self.assertEqual(txs[1].original_amount, Decimal("2"))
            txs = [Transaction(date(2026, 3, 25), "x", Decimal("1"), currency="JPY")]
            with self.assertRaisesRegex(MissingRateError, "JPY.*2026-03-25"):
                convert(txs, load_rates(p))

    def test_dedupe_and_summary_currency(self):
        a = Transaction(date(2026, 3, 1), "Coffee", Decimal("-2"), source="a", currency="EUR", category="Food")
        b = Transaction(date(2026, 3, 1), "Coffee", Decimal("-2"), source="b", currency="USD", category="Food")
        self.assertEqual(len(dedupe([a, b])), 2)
        s = monthly_summary([a], 2026, 3, base="usd")
        self.assertEqual(s["currency"], "USD")


if __name__ == "__main__":
    unittest.main()

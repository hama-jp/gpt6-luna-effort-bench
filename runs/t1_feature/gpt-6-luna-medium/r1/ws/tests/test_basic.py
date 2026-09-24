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
from ledgerlite.fx import MissingRateError, convert, load_rates
from ledgerlite.cli import main
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO


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
        self.assertEqual(s["currency"], "EUR")


class MultiCurrencyTest(unittest.TestCase):
    def test_import_and_conversion_with_previous_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(tmp, "a.csv", "Date,Description,Amount,Currency\n25/03/2026,Coffee,-1.005,usd\n")
            rates_path = write(tmp, "rates.csv", "date,currency,rate\n2026-03-18,USD,0.9\n2026-03-26,USD,2\n")
            [tx] = read_statement(statement, base="gbp")
            rates = load_rates(rates_path)
            convert([tx], rates, base="GBP")
            self.assertEqual(tx.currency, "USD")
            self.assertEqual(tx.original_amount, Decimal("-1.01"))
            self.assertEqual(tx.amount, Decimal("-0.91"))

    def test_missing_rate_and_base_no_rate(self):
        tx = Transaction(date(2026, 3, 9), "x", Decimal("2"), currency="USD")
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-09"):
            convert([tx], {"USD": {date(2026, 3, 1): Decimal("1")}})
        eur = Transaction(date(2026, 3, 9), "x", Decimal("2"))
        self.assertEqual(convert([eur], {})[0].original_amount, Decimal("2"))

    def test_dedupe_separates_currency(self):
        a = Transaction(date(2026, 3, 1), "Cafe", Decimal("-2"), source="a", currency="EUR")
        b = Transaction(date(2026, 3, 1), "Cafe", Decimal("-2"), source="b", currency="USD")
        self.assertEqual(dedupe([a, b]), [a, b])

    def test_cli_requires_rates_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount,Currency\n25/03/2026,Coffee,-1,USD\n")
            err = StringIO()
            with redirect_stderr(err):
                code = main(["report", "--month", "2026-03", str(p)])
            self.assertEqual(code, 2)
            self.assertIn("--rates", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()

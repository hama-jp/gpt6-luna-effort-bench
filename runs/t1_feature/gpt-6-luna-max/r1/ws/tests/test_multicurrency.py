import contextlib
import io
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.cli import main
from ledgerlite.dedupe import dedupe
from ledgerlite.fx import MissingRateError, convert, load_rates
from ledgerlite.importer import read_statement
from ledgerlite.models import Transaction
from ledgerlite.report import format_summary, monthly_summary


def write(tmp, name, text):
    path = Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


class MulticurrencyImporterTest(unittest.TestCase):
    def test_banka_currency_and_default_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "a.csv",
                "Date,Description,Amount,Currency\n"
                "25/03/2026,Coffee,-4.50,uSd\n"
                "26/03/2026,Tea,-2.00,\n",
            )
            txs = read_statement(path, base="gbp")
            self.assertEqual([tx.currency for tx in txs], ["USD", "GBP"])
            self.assertTrue(all(tx.original_amount is None for tx in txs))

    def test_bankb_currency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "b.csv",
                "Posted,Payee,Debit,Credit,Currency\n"
                "2026-03-02,Salary,,3000.00,cAd\n",
            )
            [tx] = read_statement(path)
            self.assertEqual(tx.currency, "CAD")
            self.assertEqual(tx.amount, Decimal("3000.00"))


class FxTest(unittest.TestCase):
    def test_load_and_convert_with_seven_day_fallback_and_half_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "rates.csv",
                "date,currency,rate\n"
                "2026-03-03,uSd,1.234\n"
                "2026-03-11,USD,8\n",
            )
            rates = load_rates(path)
            tx = Transaction(date(2026, 3, 10), "Shop", Decimal("-2.50"), currency="usd")
            result = convert([tx], rates)
            self.assertEqual(result, [tx])
            self.assertEqual(tx.currency, "USD")
            self.assertEqual(tx.original_amount, Decimal("-2.50"))
            self.assertEqual(tx.amount, Decimal("-3.09"))

    def test_base_needs_no_rate_and_sets_original_amount(self):
        tx = Transaction(date(2026, 3, 10), "Cafe", Decimal("1.239"), currency="eur")
        convert([tx], {})
        self.assertEqual(tx.currency, "EUR")
        self.assertEqual(tx.original_amount, Decimal("1.239"))
        self.assertEqual(tx.amount, Decimal("1.24"))

    def test_no_future_or_more_than_seven_day_rate(self):
        tx = Transaction(date(2026, 3, 10), "Shop", Decimal("1"), currency="USD")
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-10"):
            convert([tx], {"USD": {date(2026, 3, 11): Decimal("1")}})
        with self.assertRaises(MissingRateError):
            convert([tx], {"USD": {date(2026, 3, 2): Decimal("1")}})


class MulticurrencyDedupeAndReportTest(unittest.TestCase):
    def test_currency_is_part_of_duplicate_key(self):
        usd = Transaction(date(2026, 3, 1), "Book Store", Decimal("-20"), source="a", currency="USD")
        eur = Transaction(date(2026, 3, 1), "book store", Decimal("-20"), source="b", currency="EUR")
        self.assertEqual(dedupe([usd, eur]), [usd, eur])

    def test_summary_and_format_include_base_currency(self):
        tx = Transaction(date(2026, 3, 2), "Coffee", Decimal("-4"), category="Food")
        summary = monthly_summary([tx], 2026, 3, base="usd")
        self.assertEqual(summary["currency"], "USD")
        self.assertEqual(format_summary(summary).splitlines()[:2], ["Report 2026-03", "Currency: USD"])


class MulticurrencyCliTest(unittest.TestCase):
    def test_rates_required_and_missing_rate_are_clean_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(
                tmp,
                "statement.csv",
                "Date,Description,Amount,Currency\n25/03/2026,Coffee,-4,USD\n",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = main(["report", "--month", "2026-03", str(statement)])
            self.assertEqual(status, 2)
            self.assertIn("--rates", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

            rates = write(tmp, "rates.csv", "date,currency,rate\n2026-03-01,EUR,1\n")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = main(["report", "--month", "2026-03", "--rates", str(rates), str(statement)])
            self.assertEqual(status, 2)
            self.assertIn("USD", stderr.getvalue())
            self.assertIn("2026-03-25", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_converts_after_import_and_reports_currency(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(
                tmp,
                "statement.csv",
                "Date,Description,Amount,Currency\n25/03/2026,Coffee,-4,USD\n",
            )
            rates = write(tmp, "rates.csv", "date,currency,rate\n2026-03-25,USD,0.9\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = main(["report", "--month", "2026-03", "--base", "eur", "--rates", str(rates), str(statement)])
            self.assertEqual(status, 0)
            self.assertIn("Currency: EUR", stdout.getvalue())
            self.assertIn("3.60", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

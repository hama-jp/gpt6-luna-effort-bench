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


class MultiCurrencyImportTest(unittest.TestCase):
    def test_optional_currency_column_and_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount,Currency\n01/03/2026,Coffee,-2.5,uSd\n02/03/2026,Tea,-1,\n")
            txs = read_statement(a, base="gbp")
            self.assertEqual([tx.currency for tx in txs], ["USD", "GBP"])
            self.assertEqual([tx.original_amount for tx in txs], [None, None])

            b = write(tmp, "b.csv", "Posted,Payee,Debit,Credit,Currency\n2026-03-02,Shop,3,,jpy\n")
            [tx] = read_statement(b)
            self.assertEqual(tx.currency, "JPY")
            self.assertEqual(tx.amount, Decimal("-3.00"))

    def test_legacy_header_uses_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "legacy.csv", "Date,Description,Amount\n01/03/2026,Tea,-1\n")
            [tx] = read_statement(p, base="usd")
            self.assertEqual(tx.currency, "USD")


class FxTest(unittest.TestCase):
    def test_load_convert_round_half_up_and_previous_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "rates.csv", "date,currency,rate\n2026-03-01,usd,0.915\n2026-03-03,USD,0.92\n")
            rates = load_rates(path)
            txs = [
                Transaction(date(2026, 3, 3), "same day", Decimal("1.00"), currency="USD"),
                Transaction(date(2026, 3, 10), "seven days", Decimal("2.00"), currency="USD"),
                Transaction(date(2026, 3, 4), "base", Decimal("4.25")),
            ]
            result = convert(txs, rates)
            self.assertIs(result, txs)
            self.assertEqual([tx.amount for tx in txs], [Decimal("0.92"), Decimal("1.84"), Decimal("4.25")])
            self.assertEqual([tx.original_amount for tx in txs], [Decimal("1.00"), Decimal("2.00"), Decimal("4.25")])

    def test_no_future_or_stale_rate(self):
        tx = Transaction(date(2026, 3, 10), "x", Decimal("1"), currency="USD")
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-10"):
            convert([tx], {"USD": {date(2026, 3, 2): Decimal("1")}})
        with self.assertRaises(MissingRateError):
            convert([tx], {"USD": {date(2026, 3, 11): Decimal("1")}})


class MultiCurrencyBehaviorTest(unittest.TestCase):
    def test_dedupe_includes_currency(self):
        eur = Transaction(date(2026, 3, 1), "Coffee", Decimal("-2"), source="a", currency="EUR")
        usd = Transaction(date(2026, 3, 1), "coffee", Decimal("-2"), source="b", currency="USD")
        self.assertEqual(dedupe([eur, usd]), [eur, usd])

    def test_summary_currency_and_format(self):
        tx = Transaction(date(2026, 3, 1), "Income", Decimal("10"), category="Income")
        summary = monthly_summary([tx], 2026, 3, base="usd")
        self.assertEqual(summary["currency"], "USD")
        self.assertTrue(format_summary(summary).startswith("Report 2026-03\nCurrency: USD\n"))

    def test_cli_requires_rates_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(tmp, "foreign.csv", "Date,Description,Amount,Currency\n01/03/2026,Coffee,-2,USD\n")
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(["report", "--month", "2026-03", str(statement)])
            self.assertEqual(code, 2)
            self.assertIn("--rates", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_missing_rate_exits_two_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(tmp, "foreign.csv", "Date,Description,Amount,Currency\n10/03/2026,Coffee,-2,USD\n")
            rates = write(tmp, "rates.csv", "date,currency,rate\n2026-03-01,USD,0.9\n")
            stderr = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                code = main(["report", "--month", "2026-03", "--rates", str(rates), str(statement)])
            self.assertEqual(code, 2)
            self.assertIn("USD", stderr.getvalue())
            self.assertIn("2026-03-10", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

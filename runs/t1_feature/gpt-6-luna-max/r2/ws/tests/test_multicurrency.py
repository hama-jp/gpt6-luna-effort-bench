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


class MulticurrencyImportTest(unittest.TestCase):
    def test_banka_currency_column_and_base_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "a.csv",
                "Date,Description,Amount,Currency\n"
                "25/03/2026,Coffee,-4.50,uSd\n"
                "26/03/2026,Tea,-2.00,\n",
            )
            first, second = read_statement(path, base="jpy")
            self.assertEqual(first.currency, "USD")
            self.assertEqual(second.currency, "JPY")
            self.assertIsNone(first.original_amount)
            self.assertEqual(first.amount, Decimal("-4.50"))

    def test_bankb_currency_column_and_legacy_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "b.csv",
                "Posted,Payee,Debit,Credit,Currency\n"
                "2026-03-02,Shop,10.00,,gBp\n",
            )
            [tx] = read_statement(path)
            self.assertEqual(tx.currency, "GBP")
            self.assertEqual(tx.amount, Decimal("-10.00"))


class FxTest(unittest.TestCase):
    def test_load_and_convert_with_rounding_and_seven_day_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(
                tmp,
                "rates.csv",
                "date,currency,rate\n2026-03-01,uSd,1.005\n",
            )
            rates = load_rates(path)
        txs = [
            Transaction(date(2026, 3, 8), "Purchase", Decimal("1.00"), currency="usd"),
            Transaction(date(2026, 3, 8), "Base", Decimal("-2.00")),
        ]
        converted = convert(txs, rates)
        self.assertIs(converted, txs)
        self.assertEqual(txs[0].amount, Decimal("1.01"))
        self.assertEqual(txs[0].original_amount, Decimal("1.00"))
        self.assertEqual(txs[0].currency, "USD")
        self.assertEqual(txs[1].amount, Decimal("-2.00"))
        self.assertEqual(txs[1].original_amount, Decimal("-2.00"))

    def test_eight_day_old_and_future_rates_are_rejected(self):
        tx = Transaction(date(2026, 3, 10), "Purchase", Decimal("5"), currency="USD")
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-10"):
            convert([tx], {"USD": {date(2026, 3, 2): Decimal("0.9"), date(2026, 3, 11): Decimal("0.8")}})

    def test_seven_days_is_inclusive(self):
        tx = Transaction(date(2026, 3, 10), "Purchase", Decimal("5"), currency="USD")
        convert([tx], {"USD": {date(2026, 3, 3): Decimal("0.9")}})
        self.assertEqual(tx.amount, Decimal("4.50"))


class MulticurrencyDedupeAndReportTest(unittest.TestCase):
    def test_different_currencies_are_not_duplicates(self):
        usd = Transaction(date(2026, 3, 1), "Coffee", Decimal("-4"), source="a", currency="USD")
        eur = Transaction(date(2026, 3, 1), "coffee", Decimal("-4"), source="b", currency="EUR")
        self.assertEqual(dedupe([usd, eur]), [usd, eur])

    def test_summary_includes_base_currency_line(self):
        tx = Transaction(date(2026, 3, 2), "Rent", Decimal("-10"), category="Housing")
        summary = monthly_summary([tx], 2026, 3, base="usd")
        self.assertEqual(summary["currency"], "USD")
        self.assertEqual(format_summary(summary).splitlines()[:2], ["Report 2026-03", "Currency: USD"])


class MulticurrencyCliTest(unittest.TestCase):
    def test_missing_rates_exits_two_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(
                tmp,
                "a.csv",
                "Date,Description,Amount,Currency\n25/03/2026,Coffee,-2.00,USD\n",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["report", "--month", "2026-03", str(statement)])
        self.assertEqual(code, 2)
        self.assertIn("--rates", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_missing_rate_exits_two_with_rate_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(
                tmp,
                "a.csv",
                "Date,Description,Amount,Currency\n25/03/2026,Coffee,-2.00,USD\n",
            )
            rates = write(tmp, "rates.csv", "date,currency,rate\n2026-03-01,GBP,1.1\n")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["report", "--month", "2026-03", "--rates", str(rates), str(statement)])
        self.assertEqual(code, 2)
        self.assertIn("USD", stderr.getvalue())
        self.assertIn("2026-03-25", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_report_converts_using_base_and_rates(self):
        with tempfile.TemporaryDirectory() as tmp:
            statement = write(
                tmp,
                "a.csv",
                "Date,Description,Amount,Currency\n25/03/2026,Coffee,-2.00,USD\n",
            )
            rates = write(tmp, "rates.csv", "date,currency,rate\n2026-03-25,USD,0.9\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main(["report", "--month", "2026-03", "--rates", str(rates), str(statement)])
        self.assertEqual(code, 0)
        self.assertIn("Currency: EUR", stdout.getvalue())
        self.assertIn("1.80", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

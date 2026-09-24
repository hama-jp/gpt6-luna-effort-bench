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


class MultiCurrencyTest(unittest.TestCase):
    def test_import_currency_columns_and_base_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount,Currency\n01/03/2026,Coffee,-2.00,uSd\n02/03/2026,Tea,-1.00,\n")
            txs = read_statement(a, base="gbp")
            self.assertEqual([tx.currency for tx in txs], ["USD", "GBP"])
            self.assertEqual([tx.original_amount for tx in txs], [None, None])
            b = write(tmp, "b.csv", "Posted,Payee,Debit,Credit,Currency\n2026-03-01,Book,5.00,,jPy\n")
            [tx] = read_statement(b)
            self.assertEqual(tx.currency, "JPY")

    def test_conversion_uses_latest_rate_within_seven_days_and_rounds_half_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "rates.csv", "date,currency,rate\n2026-03-01,usd,0.90\n2026-03-05,USD,0.905\n")
            rates = load_rates(path)
            tx = Transaction(date(2026, 3, 6), "Thing", Decimal("1.00"), currency="USD")
            result = convert([tx], rates)
            self.assertIs(result[0], tx)
            self.assertEqual(tx.original_amount, Decimal("1.00"))
            self.assertEqual(tx.amount, Decimal("0.91"))
            base = Transaction(date(2026, 3, 6), "Base", Decimal("2"))
            convert([base], {}, "eur")
            self.assertEqual(base.original_amount, Decimal("2"))
            self.assertEqual(base.amount, Decimal("2.00"))

    def test_missing_or_stale_rate_reports_currency_and_day(self):
        tx = Transaction(date(2026, 3, 9), "Thing", Decimal("1"), currency="USD")
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-09"):
            convert([tx], {"USD": [(date(2026, 3, 1), Decimal("0.9"))]})
        with self.assertRaisesRegex(MissingRateError, "USD.*2026-03-09"):
            convert([tx], {})

    def test_dedupe_separates_currency_and_report_displays_base(self):
        a = Transaction(date(2026, 3, 1), "Cafe", Decimal("-3"), source="a", currency="EUR")
        b = Transaction(date(2026, 3, 1), "Cafe", Decimal("-3"), source="b", currency="USD")
        self.assertEqual(dedupe([a, b]), [a, b])
        summary = monthly_summary([a], 2026, 3, "gbp")
        self.assertEqual(summary["currency"], "GBP")
        self.assertEqual(format_summary(summary).splitlines()[:2], ["Report 2026-03", "Currency: GBP"])

    def test_cli_requires_rates_and_handles_missing_rate_without_traceback(self):
        from io import StringIO
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            statement = write(tmp, "foreign.csv", "Date,Description,Amount,Currency\n01/03/2026,Coffee,-2,USD\n")
            err = StringIO()
            with patch("sys.stderr", err):
                self.assertEqual(main(["report", "--month", "2026-03", str(statement)]), 2)
            self.assertIn("--rates", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())

            rates_path = write(tmp, "rates.csv", "date,currency,rate\n")
            err = StringIO()
            with patch("sys.stderr", err):
                self.assertEqual(main(["report", "--month", "2026-03", "--rates", str(rates_path), str(statement)]), 2)
            self.assertIn("USD", err.getvalue())
            self.assertIn("2026-03-01", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()

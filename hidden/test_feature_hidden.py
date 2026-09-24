"""Hidden tests for task T1 (multi-currency feature). One class per spec area."""
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.dedupe import dedupe
from ledgerlite.importer import read_statement
from ledgerlite.models import Transaction
from ledgerlite.report import monthly_summary, format_summary


def write(tmp, name, text):
    p = Path(tmp) / name
    p.write_text(text, encoding="utf-8")
    return p


def run_cli(argv):
    from ledgerlite.cli import main
    out, err = io.StringIO(), io.StringIO()
    code = None
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


RATES = "date,currency,rate\n2026-03-01,USD,0.9\n2026-03-10,usd,0.8\n2026-03-01,GBP,1.2\n"


class F1_Import(unittest.TestCase):
    def test_banka_currency_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount,Currency\n02/03/2026,Hotel,-100,usd\n03/03/2026,Cafe,-3,\n")
            a, b = read_statement(p)
            self.assertEqual((a.currency, a.amount, a.original_amount), ("USD", Decimal("-100.00"), None))
            self.assertEqual(b.currency, "EUR")

    def test_bankb_currency_column_and_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "b.csv", "Posted,Payee,Debit,Credit,Currency\n2026-03-02,Shop,5.00,,GBP\n2026-03-03,Pay,,10.00,\n")
            a, b = read_statement(p, base="JPY")
            self.assertEqual((a.currency, a.amount), ("GBP", Decimal("-5.00")))
            self.assertEqual(b.currency, "JPY")

    def test_old_headers_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount\n02/03/2026,Cafe,-3\n")
            [t] = read_statement(p)
            self.assertEqual(t.currency, "EUR")


class F2_RateLookup(unittest.TestCase):
    def setUp(self):
        from ledgerlite import fx
        self.fx = fx
        self.tmp = tempfile.TemporaryDirectory()
        self.rates = fx.load_rates(write(self.tmp.name, "r.csv", RATES))

    def tearDown(self):
        self.tmp.cleanup()

    def conv(self, d, amt, cur):
        t = Transaction(d, "x", Decimal(amt))
        t.currency = cur
        return self.fx.convert([t], self.rates, base="EUR")[0]

    def test_exact_and_earlier(self):
        self.assertEqual(self.conv(date(2026, 3, 10), "-10", "USD").amount, Decimal("-8.00"))
        self.assertEqual(self.conv(date(2026, 3, 5), "-10", "USD").amount, Decimal("-9.00"))

    def test_seven_days_ok_eight_not(self):
        self.assertEqual(self.conv(date(2026, 3, 17), "-10", "USD").amount, Decimal("-8.00"))
        self.assertEqual(self.conv(date(2026, 3, 8), "-10", "GBP").amount, Decimal("-12.00"))
        with self.assertRaises(self.fx.MissingRateError) as cm:
            self.conv(date(2026, 3, 9), "-10", "GBP")
        self.assertIn("GBP", str(cm.exception))
        self.assertIn("2026-03-09", str(cm.exception))

    def test_future_rate_not_used(self):
        with self.assertRaises(ValueError):
            self.conv(date(2026, 2, 28), "-10", "USD")

    def test_unknown_currency(self):
        with self.assertRaises(self.fx.MissingRateError):
            self.conv(date(2026, 3, 5), "-10", "CHF")


class F3_Rounding(unittest.TestCase):
    def test_half_up_per_transaction(self):
        from ledgerlite import fx
        with tempfile.TemporaryDirectory() as tmp:
            rates = fx.load_rates(write(tmp, "r.csv", "date,currency,rate\n2026-03-01,USD,1.5\n"))
        ts = []
        for amt in ("-3.35", "2.01"):
            t = Transaction(date(2026, 3, 2), "x", Decimal(amt))
            t.currency = "USD"
            ts.append(t)
        fx.convert(ts, rates)
        self.assertEqual([t.amount for t in ts], [Decimal("-5.03"), Decimal("3.02")])
        self.assertEqual([t.original_amount for t in ts], [Decimal("-3.35"), Decimal("2.01")])
        self.assertEqual([t.currency for t in ts], ["USD", "USD"])


class F4_BaseUntouched(unittest.TestCase):
    def test_base_needs_no_rate(self):
        from ledgerlite import fx
        t = Transaction(date(2020, 1, 1), "x", Decimal("-7.25"))
        t.currency = "EUR"
        fx.convert([t], fx.load_rates(io_rates_empty()), base="EUR")
        self.assertEqual((t.amount, t.original_amount, t.currency), (Decimal("-7.25"), Decimal("-7.25"), "EUR"))


def io_rates_empty():
    tmp = tempfile.mkdtemp()
    return write(tmp, "r.csv", "date,currency,rate\n")


class F5_DedupeCurrency(unittest.TestCase):
    def test_different_currency_not_duplicate(self):
        a = Transaction(date(2026, 3, 1), "Shop", Decimal("-10"), source="a.csv")
        b = Transaction(date(2026, 3, 1), "Shop", Decimal("-10"), source="b.csv")
        a.currency, b.currency = "USD", "EUR"
        self.assertEqual(len(dedupe([a, b])), 2)

    def test_same_currency_still_duplicate(self):
        a = Transaction(date(2026, 3, 1), "Shop", Decimal("-10"), source="a.csv")
        b = Transaction(date(2026, 3, 1), "shop", Decimal("-10"), source="b.csv")
        a.currency = b.currency = "USD"
        self.assertEqual(dedupe([a, b]), [a])


class F6_ReportAndCli(unittest.TestCase):
    def test_summary_currency_line(self):
        s = monthly_summary([Transaction(date(2026, 3, 1), "x", Decimal("-1"), category="A")], 2026, 3, base="GBP")
        self.assertEqual(s["currency"], "GBP")
        lines = format_summary(s).splitlines()
        self.assertEqual(lines[1].strip(), "Currency: GBP")

    def test_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount,Currency\n02/03/2026,Hotel NYC,-100,USD\n05/03/2026,Salary,2000,\n")
            b = write(tmp, "b.csv", "Posted,Payee,Debit,Credit,Currency\n2026-03-02,hotel  nyc,100.00,,USD\n2026-03-11,Diner,20.00,,USD\n")
            r = write(tmp, "r.csv", RATES)
            rules = write(tmp, "rules.txt", "1 | salary | Salary\n")
            code, out, err = run_cli(["report", "--month", "2026-03", "--rules", str(rules), "--rates", str(r), str(a), str(b)])
            self.assertIn(code, (0, None), err)
            self.assertIn("Currency: EUR", out)
            # hotel deduped (90.00) + diner 16.00 = 106.00 expenses; net 1894.00
            self.assertRegex(out, r"Expenses:\s+106\.00")
            self.assertRegex(out, r"Net:\s+1894\.00")

    def test_cli_missing_rates_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount,Currency\n02/03/2026,Hotel,-100,USD\n")
            code, out, err = run_cli(["report", "--month", "2026-03", str(a)])
            self.assertEqual(code, 2)
            self.assertIn("--rates", err)
            self.assertNotIn("Traceback", err)

    def test_cli_missing_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount,Currency\n02/03/2026,Hotel,-100,CHF\n")
            r = write(tmp, "r.csv", RATES)
            code, out, err = run_cli(["report", "--month", "2026-03", "--rates", str(r), str(a)])
            self.assertEqual(code, 2)
            self.assertIn("CHF", err)
            self.assertNotIn("Traceback", err)

    def test_cli_base_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount\n02/03/2026,Cafe,-3\n")
            code, out, err = run_cli(["report", "--month", "2026-03", "--base", "GBP", str(a)])
            self.assertIn(code, (0, None), err)
            self.assertIn("Currency: GBP", out)


class R_Regression(unittest.TestCase):
    def test_old_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(tmp, "a.csv", "Date,Description,Amount\n04/03/2026,Bakery,-3.20\n31/03/2026,Rent,-900\n")
            b = write(tmp, "b.csv", 'Posted,Payee,Debit,Credit\n2026-03-04,bakery,3.20,\n2026-03-01,Pay,,"1,500.00"\n')
            rules = write(tmp, "rules.txt", "5 | rent | Housing\n1 | bakery | Food\n")
            code, out, err = run_cli(["report", "--month", "2026-03", "--rules", str(rules), str(a), str(b)])
            self.assertIn(code, (0, None), err)
            self.assertRegex(out, r"Expenses:\s+903\.20")
            self.assertRegex(out, r"Net:\s+596\.80")

    def test_same_file_dupes_kept(self):
        a1 = Transaction(date(2026, 3, 5), "Coffee", Decimal("-3.50"), source="a.csv")
        a2 = Transaction(date(2026, 3, 5), "Coffee", Decimal("-3.50"), source="a.csv")
        self.assertEqual(len(dedupe([a1, a2])), 2)

    def test_summary_default_call(self):
        s = monthly_summary([Transaction(date(2026, 3, 1), "x", Decimal("-1"), category="A")], 2026, 3)
        self.assertEqual(s["total_expenses"], Decimal("1.00"))


if __name__ == "__main__":
    unittest.main()

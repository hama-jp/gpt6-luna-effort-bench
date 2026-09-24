"""Hidden tests for task T2 (bug fixing). One class per planted bug.

A bug counts as fixed only if every test in its class passes.
These tests must also all pass on the clean base codebase.
"""
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerlite.categorize import categorize, parse_rules
from ledgerlite.dedupe import dedupe
from ledgerlite.importer import read_statement
from ledgerlite.models import Transaction
from ledgerlite.report import monthly_summary, format_summary


def write(tmp, name, text):
    p = Path(tmp) / name
    p.write_text(text, encoding="utf-8")
    return p


def T(d, desc, amt, cat="Uncategorized", src=""):
    return Transaction(d, desc, Decimal(amt), source=src, category=cat)


class B1_BankADayMonth(unittest.TestCase):
    def test_small_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount\n04/03/2026,Bakery,-3.20\n11/12/2026,Gift,-15\n")
            txs = read_statement(p)
            self.assertEqual([t.date for t in txs], [date(2026, 3, 4), date(2026, 12, 11)])

    def test_large_day_still_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "a.csv", "Date,Description,Amount\n28/02/2026,Bakery,-3.20\n")
            self.assertEqual(read_statement(p)[0].date, date(2026, 2, 28))


class B2_Thousands(unittest.TestCase):
    def test_millions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "b.csv", 'Posted,Payee,Debit,Credit\n2026-03-02,House,"1,234,567.89",\n2026-03-03,Bonus,,"12,000.00"\n')
            self.assertEqual([t.amount for t in read_statement(p)], [Decimal("-1234567.89"), Decimal("12000.00")])


class B3_Priority(unittest.TestCase):
    def test_highest_priority_wins(self):
        rules = parse_rules("1 | amazon | Shopping\n9 | re:amazon.*prime | Subscriptions\n")
        [t] = categorize([T(date(2026, 3, 1), "AMAZON PRIME VIDEO", "-8.99")], rules)
        self.assertEqual(t.category, "Subscriptions")

    def test_tie_earlier_line_wins(self):
        rules = parse_rules("5 | shell | Fuel\n5 | shell cafe | Food\n")
        [t] = categorize([T(date(2026, 3, 1), "Shell Cafe", "-2")], rules)
        self.assertEqual(t.category, "Fuel")


class B4_SameFileDuplicates(unittest.TestCase):
    def test_same_file_kept(self):
        a1 = T(date(2026, 3, 5), "Coffee", "-3.50", src="a.csv")
        a2 = T(date(2026, 3, 5), "Coffee", "-3.50", src="a.csv")
        self.assertEqual(len(dedupe([a1, a2])), 2)

    def test_overlap_max_kept(self):
        a1 = T(date(2026, 3, 5), "Coffee", "-3.50", src="a.csv")
        a2 = T(date(2026, 3, 5), "Coffee", "-3.50", src="a.csv")
        b1 = T(date(2026, 3, 5), "coffee", "-3.50", src="b.csv")
        self.assertEqual(dedupe([a1, a2, b1]), [a1, a2])

    def test_whitespace_normalised(self):
        a = T(date(2026, 3, 5), "Corner   Shop", "-9", src="a.csv")
        b = T(date(2026, 3, 5), " corner shop ", "-9", src="b.csv")
        self.assertEqual(dedupe([a, b]), [a])


class B5_MonthEnd(unittest.TestCase):
    def test_last_day_included(self):
        txs = [T(date(2026, 3, 31), "Rent", "-900", "Housing"),
               T(date(2026, 4, 1), "Rent", "-900", "Housing"),
               T(date(2026, 3, 1), "Salary", "2000", "Salary")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["total_expenses"], Decimal("900.00"))

    def test_leap_february(self):
        txs = [T(date(2028, 2, 29), "Gym", "-30", "Health")]
        self.assertEqual(monthly_summary(txs, 2028, 2)["total_expenses"], Decimal("30.00"))


class B6_Cents(unittest.TestCase):
    def test_top_merchant_exact(self):
        txs = [T(date(2026, 3, d), "Kiosk", "-0.10", "Food") for d in range(1, 4)]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["top_merchants"], [("kiosk", Decimal("0.30"))])
        self.assertIn("0.30", format_summary(s))
        self.assertNotIn("0.30000", format_summary(s))

    def test_total_exact(self):
        txs = [T(date(2026, 3, 1), f"Item{i}", "-0.10", "Food") for i in range(10)]
        self.assertEqual(monthly_summary(txs, 2026, 3)["total_expenses"], Decimal("1.00"))


class B7_Refunds(unittest.TestCase):
    def test_refund_nets(self):
        txs = [T(date(2026, 3, 2), "Shoes", "-80", "Clothing"),
               T(date(2026, 3, 9), "Shoes refund", "30", "Clothing"),
               T(date(2026, 3, 1), "Salary", "1000", "Salary")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["expenses"]["Clothing"], Decimal("50.00"))
        self.assertEqual(s["income"], Decimal("1000.00"))
        self.assertEqual(s["net"], Decimal("950.00"))


class R_Regression(unittest.TestCase):
    """Behaviour that already worked in the buggy version; must not regress."""

    def test_transfer_excluded(self):
        txs = [T(date(2026, 3, 1), "To savings", "-500", "Transfer"),
               T(date(2026, 3, 2), "Salary", "1000", "Salary")]
        s = monthly_summary(txs, 2026, 3)
        self.assertEqual(s["total_expenses"], Decimal("0.00"))
        self.assertEqual(s["income"], Decimal("1000.00"))

    def test_top3_order(self):
        txs = [T(date(2026, 3, 1), "B", "-5", "X"), T(date(2026, 3, 1), "A", "-5", "X"),
               T(date(2026, 3, 1), "C", "-9", "X"), T(date(2026, 3, 1), "D", "-1", "X")]
        self.assertEqual([m for m, _ in monthly_summary(txs, 2026, 3)["top_merchants"]], ["c", "a", "b"])

    def test_bankb_both_columns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "b.csv", "Posted,Payee,Debit,Credit\n2026-03-02,X,1.00,2.00\n")
            with self.assertRaises(ValueError):
                read_statement(p)

    def test_regex_rule(self):
        rules = parse_rules("3 | re:^uber\\s+eats | Food\n2 | taxi | Transport\n")
        txs = categorize([T(date(2026, 3, 1), "Uber Eats 123", "-10"), T(date(2026, 3, 1), "City TAXI", "-7")], rules)
        self.assertEqual([t.category for t in txs], ["Food", "Transport"])

    def test_comments_in_rules(self):
        rules = parse_rules("# header\n\n4 | tesco | Groceries  # big shop\n")
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].category, "Groceries")


if __name__ == "__main__":
    unittest.main()

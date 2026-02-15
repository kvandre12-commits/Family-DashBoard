import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple

LEDGER_FILE = "family_ledger.csv"

KINDS = {"paycheck", "advance", "bill", "spend"}

def ensure_ledger_exists() -> None:
    if not os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "kind", "amount", "note"])

def read_ledger() -> List[Dict[str, str]]:
    ensure_ledger_exists()
    rows = []
    with open(LEDGER_FILE, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def append_entry(kind: str, amount: float, note: str, date_str: str) -> None:
    ensure_ledger_exists()
    with open(LEDGER_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([date_str, kind, f"{amount:.2f}", note])

def parse_amount(s: str) -> float:
    return float(s.replace("$", "").replace(",", "").strip())

def compute_balances(rows: List[Dict[str, str]]) -> Tuple[float, float, float, float]:
    """
    Returns:
      onepay_balance: advances - paychecks_applied (simple model)
      income_total: sum(paycheck)
      bills_total: sum(bill)
      spend_total: sum(spend)
    """
    onepay_balance = 0.0
    income_total = 0.0
    bills_total = 0.0
    spend_total = 0.0

    for row in rows:
        kind = row["kind"].strip().lower()
        amt = parse_amount(row["amount"])

        if kind == "advance":
            onepay_balance += amt
        elif kind == "paycheck":
            income_total += amt
            onepay_balance -= amt
        elif kind == "bill":
            bills_total += amt
        elif kind == "spend":
            spend_total += amt

    # Round for display
    return round(onepay_balance, 2), round(income_total, 2), round(bills_total, 2), round(spend_total, 2)

def status_onepay(balance: float) -> str:
    if balance > 0:
        return f"🔴 OnePay behind by ${balance:.2f}"
    if balance == 0:
        return "🟢 OnePay GREEN ($0 behind)"
    return f"🟢 OnePay GREEN with ${abs(balance):.2f} buffer"

def paychecks_to_green(balance: float, typical_paycheck: float) -> Tuple[int, float]:
    """
    If balance > 0, returns (num_checks_needed, balance_after_last_check).
    If already green, returns (0, balance).
    """
    if balance <= 0:
        return 0, balance
    if typical_paycheck <= 0:
        return 0, balance

    remaining = balance
    checks = 0
    while remaining > 0:
        remaining -= typical_paycheck
        checks += 1
        # safety break
        if checks > 200:
            break
    return checks, round(remaining, 2)

def money_dashboard(rows: List[Dict[str, str]]) -> None:
    onepay_balance, income_total, bills_total, spend_total = compute_balances(rows)

    # Cashflow view (this period): income - bills - spend
    cash_after = round(income_total - bills_total - spend_total, 2)

    print("\n==============================")
    print("   FAMILY MONEY DASHBOARD")
    print("==============================")
    print(status_onepay(onepay_balance))
    print(f"Income total (paychecks): ${income_total:.2f}")
    print(f"Bills total:              ${bills_total:.2f}")
    print(f"Other spend total:        ${spend_total:.2f}")
    print("------------------------------")
    if cash_after >= 0:
        print(f"✅ Cash after bills/spend: ${cash_after:.2f}")
    else:
        print(f"⚠️ Cash after bills/spend: -${abs(cash_after):.2f}")
    print("==============================\n")

    # Projection (optional)
    if onepay_balance > 0:
        try:
            typical = parse_amount(input("Typical paycheck amount for projection (or press Enter to skip): ") or "0")
        except ValueError:
            typical = 0.0

        if typical > 0:
            checks, after_last = paychecks_to_green(onepay_balance, typical)
            print("\n--- OnePay Go-Green Projection ---")
            print(f"Paychecks to GREEN: {checks}")
            print(f"After paycheck #{checks}: {status_onepay(after_last)}")
            print()

def prompt_add_entry() -> None:
    print("\nAdd Entry Types:")
    print("  paycheck = money coming in")
    print("  advance  = OnePay advance (increases behind balance)")
    print("  bill     = rent/phone/utilities/etc")
    print("  spend    = groceries/gas/etc")
    kind = input("Type (paycheck/advance/bill/spend): ").strip().lower()
    if kind not in KINDS:
        print("Invalid type.")
        return

    amt_str = input("Amount: $").strip()
    try:
        amount = parse_amount(amt_str)
    except ValueError:
        print("Invalid amount.")
        return

    note = input("Note (optional): ").strip()
    date_str = input("Date (YYYY-MM-DD) or Enter for today: ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    append_entry(kind, amount, note, date_str)
    print("✅ Saved.\n")

def list_recent(rows: List[Dict[str, str]], n: int = 10) -> None:
    print(f"\n--- Last {n} entries ---")
    for row in rows[-n:]:
        print(f'{row["date"]} | {row["kind"]:<7} | ${parse_amount(row["amount"]):>8.2f} | {row["note"]}')
    print()

def main():
    ensure_ledger_exists()

    while True:
        rows = read_ledger()
        print("1) View dashboard")
        print("2) Add entry")
        print("3) View last 10 entries")
        print("4) Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            money_dashboard(rows)
        elif choice == "2":
            prompt_add_entry()
        elif choice == "3":
            list_recent(rows, 10)
        elif choice == "4":
            print("Bye.")
            break
        else:
            print("Invalid choice.\n")

if __name__ == "__main__":
    main()

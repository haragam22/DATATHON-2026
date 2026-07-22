"""Account, Transaction, AccountCaseLink — base seed data only.

Phase 19 (Person A) owns the actual financial-crime *feature* build; this
module exists only so those three tables aren't empty when Phase 19 starts
(FK targets need to exist). Deliberately light: enough rows to demo
AccountCaseLink joins, no money-laundering graph realism attempt.
"""

from __future__ import annotations

import datetime
import random
from typing import Any

from data_generation.utils import id_sequence, write_csv

random.seed(45)

BANKS = ["State Bank of India", "Canara Bank", "HDFC Bank", "ICICI Bank",
         "Axis Bank", "Union Bank of India", "Karnataka Bank"]
ACCOUNT_TYPES = ["Savings", "Current", "NRI"]
TXN_TYPES = ["NEFT", "IMPS", "RTGS", "UPI", "Cash Deposit", "Cash Withdrawal"]
FIRST_NAMES = ["Arjun", "Deepa", "Suresh", "Lakshmi", "Manjunath", "Kavya",
               "Ravindra", "Anitha", "Prakash", "Sowmya"]


def generate_accounts(count: int = 500) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    for _ in range(count):
        acct_id = next(ids)
        rows.append({
            "AccountID": acct_id,
            "AccountHolderName": random.choice(FIRST_NAMES),
            "BankName": random.choice(BANKS),
            "AccountNumberMasked": f"XXXXXXXX{acct_id:04d}",  # synthetic only
            "AccountType": random.choice(ACCOUNT_TYPES),
            "Active": random.random() < 0.9,
        })
    write_csv(rows, "Account")
    return rows


def generate_transactions(
    account_rows: list[dict[str, Any]],
    account_rowid_map: dict[int, int],
    count: int = 1500,
) -> list[dict[str, Any]]:
    ids = id_sequence(1)
    rows = []
    start = datetime.date(2023, 7, 1)
    span = (datetime.date.today() - start).days
    for _ in range(count):
        from_acct, to_acct = random.sample(account_rows, 2)
        txn_date = start + datetime.timedelta(days=random.randint(0, span))
        rows.append({
            "TransactionID": next(ids),
            "FromAccountID_FK": account_rowid_map[from_acct["AccountID"]],
            "ToAccountID_FK": account_rowid_map[to_acct["AccountID"]],
            "Amount": round(random.uniform(500, 500_000), 2),
            "TransactionDate": txn_date.isoformat() + " " + f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:00",
            "TransactionType": random.choice(TXN_TYPES),
            "Flagged": random.random() < 0.05,
        })
    write_csv(rows, "Transaction")
    return rows


def generate_account_case_links(
    case_master_rows: list[dict[str, Any]],
    case_master_rowid_map: dict[int, int],
    account_rows: list[dict[str, Any]],
    account_rowid_map: dict[int, int],
    link_rate: float = 0.1,
) -> list[dict[str, Any]]:
    """Only a fraction of cases are financial-crime-relevant enough to have
    a linked account — most CaseMaster rows won't."""
    ids = id_sequence(1)
    rows = []
    for case in case_master_rows:
        if random.random() > link_rate:
            continue
        account = random.choice(account_rows)
        rows.append({
            "LinkID": next(ids),
            "CaseMasterID_FK": case_master_rowid_map[case["CaseMasterID"]],
            "AccountID_FK": account_rowid_map[account["AccountID"]],
            "RoleInCase": random.choice(["Suspect Account", "Victim Account", "Mule Account"]),
        })
    write_csv(rows, "AccountCaseLink")
    return rows

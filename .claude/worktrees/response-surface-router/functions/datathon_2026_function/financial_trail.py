"""Phase 19 backend half — Financial Crime demo endpoint. GET
/api/financial-trail/{case_id}: traces the money linked to a case, via
CaseMaster -> AccountCaseLink -> Account -> Transaction.

Deliberately minimal per idea.md/implementation.md ("one working demo query
... intentionally lighter in depth than the core conversational and network
layers") — the underlying synthetic data (data_generation/generators/
financial.py) has no deliberate layering/chain structure either, just random
transaction pairs, ~10% of cases linked to an account. This traces whatever
transactions actually touch the linked account(s), nothing more.

Same no-JOIN/no-nested-SELECT constraint as everywhere else in this Function
(confirmed live, see pipeline.py) — chained single-table queries in Python,
batched via WHERE...IN, matching network.py's pattern.
"""

from __future__ import annotations

from typing import Any

import zcql_util
from zcql_util import CaseNotFound, in_clause


def get_financial_trail(case_id: int, zcql_service: Any) -> dict[str, Any]:
    case_rows = zcql_util.run(zcql_service, f"SELECT ROWID FROM CaseMaster WHERE CseMasterID = {int(case_id)}")
    if not case_rows:
        raise CaseNotFound(f"CaseMasterID {case_id} not found")
    case_rowid = int(case_rows[0]["ROWID"])

    link_rows = zcql_util.run(
        zcql_service, f"SELECT AccountID_FK, RoleInCase FROM AccountCaseLink WHERE CaseMasterID_FK = {case_rowid}",
    )
    if not link_rows:
        return {"accounts": [], "transactions": []}

    account_rowids = sorted({int(r["AccountID_FK"]) for r in link_rows})
    role_by_account_rowid = {int(r["AccountID_FK"]): r["RoleInCase"] for r in link_rows}

    account_rows = zcql_util.run(
        zcql_service,
        f"SELECT ROWID, AccountID, AccountHolderName, BankName, AccountNumberMasked, AccountType "
        f"FROM Account WHERE ROWID IN ({in_clause(account_rowids)})",
    )
    accounts = [
        {
            "account_id": int(a["AccountID"]),
            "holder_name": a["AccountHolderName"],
            "bank_name": a["BankName"],
            "account_number_masked": a["AccountNumberMasked"],
            "account_type": a["AccountType"],
            "role_in_case": role_by_account_rowid.get(int(a["ROWID"])),
        }
        for a in account_rows
    ]
    account_label_by_rowid = {
        int(a["ROWID"]): {"account_id": int(a["AccountID"]), "holder_name": a["AccountHolderName"]}
        for a in account_rows
    }

    outgoing = zcql_util.run(
        zcql_service,
        f"SELECT TransactionID, FromAccountID_FK, ToAccountID_FK, Amount, TransactionDate, TransactionType, Flagged "
        f"FROM Transaction WHERE FromAccountID_FK IN ({in_clause(account_rowids)})",
    )
    incoming = zcql_util.run(
        zcql_service,
        f"SELECT TransactionID, FromAccountID_FK, ToAccountID_FK, Amount, TransactionDate, TransactionType, Flagged "
        f"FROM Transaction WHERE ToAccountID_FK IN ({in_clause(account_rowids)})",
    )
    seen_txn_ids: set[int] = set()
    transactions = []
    for t in outgoing + incoming:
        txn_id = int(t["TransactionID"])
        if txn_id in seen_txn_ids:
            continue
        seen_txn_ids.add(txn_id)
        from_rowid, to_rowid = int(t["FromAccountID_FK"]), int(t["ToAccountID_FK"])
        transactions.append({
            "transaction_id": txn_id,
            "from_account": account_label_by_rowid.get(from_rowid, {"account_id": None, "holder_name": "Unknown"}),
            "to_account": account_label_by_rowid.get(to_rowid, {"account_id": None, "holder_name": "Unknown"}),
            "amount": float(t["Amount"]),
            "date": t["TransactionDate"],
            "type": t["TransactionType"],
            "flagged": bool(t["Flagged"]),
        })
    transactions.sort(key=lambda t: t["date"])

    return {"accounts": accounts, "transactions": transactions}


def _demo() -> None:
    """ponytail self-check: chained lookup + dedupe logic, no live ZCQL."""
    class _FakeZcql:
        def __init__(self, tables: dict[str, list[dict[str, Any]]]):
            self._tables = tables

        def execute_query(self, sql: str):
            table = sql.split("FROM", 1)[1].split()[0]
            rows = self._tables.get(table, [])
            for col in ("CseMasterID", "CaseMasterID_FK"):
                marker = f"{col} = "
                if marker in sql:
                    val = int(sql.split(marker, 1)[1].split()[0])
                    return [r for r in rows if int(r.get(col, -1)) == val]
            for col in ("ROWID", "FromAccountID_FK", "ToAccountID_FK", "AccountID_FK"):
                marker = f"{col} IN ("
                if marker in sql:
                    ids = {int(x) for x in sql.split(marker, 1)[1].split(")")[0].split(",")}
                    return [r for r in rows if int(r.get(col, -1)) in ids]
            return rows

    zcql = _FakeZcql({
        "CaseMaster": [{"ROWID": 10, "CseMasterID": 1}],
        "AccountCaseLink": [{"AccountID_FK": 100, "RoleInCase": "Suspect Account", "CaseMasterID_FK": 10}],
        "Account": [{"ROWID": 100, "AccountID": 5, "AccountHolderName": "Arjun", "BankName": "SBI", "AccountNumberMasked": "XXXX0005", "AccountType": "Savings"}],
        "Transaction": [
            {"TransactionID": 1, "FromAccountID_FK": 100, "ToAccountID_FK": 200, "Amount": 5000.0, "TransactionDate": "2024-01-01", "TransactionType": "UPI", "Flagged": False},
            {"TransactionID": 2, "FromAccountID_FK": 200, "ToAccountID_FK": 100, "Amount": 2000.0, "TransactionDate": "2024-01-02", "TransactionType": "NEFT", "Flagged": True},
        ],
    })

    trail = get_financial_trail(1, zcql)
    assert len(trail["accounts"]) == 1 and trail["accounts"][0]["role_in_case"] == "Suspect Account", trail
    assert len(trail["transactions"]) == 2, trail
    assert trail["transactions"][1]["flagged"] is True, trail

    try:
        get_financial_trail(999, zcql)
        raise AssertionError("expected CaseNotFound")
    except CaseNotFound:
        pass

    print("financial_trail._demo: all assertions passed")


if __name__ == "__main__":
    _demo()

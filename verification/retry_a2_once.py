"""Submit exactly one controlled retry for the sealed A2 assessment.

The retry intent is persisted before signing, and the transaction hash is
persisted immediately after submission. Once a hash exists, this script only
polls that hash and never submits another transaction.
"""
import getpass
import json
from datetime import datetime, timezone
from pathlib import Path
import time

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet

from run_live_matrix import (
    ADDRESS,
    REVIEWER,
    SOURCE_SHA256,
    parity,
    return_value,
    rpc,
    view,
)


ROOT = Path(__file__).resolve().parents[1]
RETRY_FILE = ROOT / ".private" / ("a2-single-retry-" + ADDRESS.lower() + ".json")
PUBLIC_FILE = ROOT / "verification" / ("a2-single-retry-" + ADDRESS.lower() + ".json")
ORIGINAL_TX = "0x1b870ce9b251ccff199789c006b23fe2161439c7f5f4ea9da416b38a59d47db5"


def save(record: dict) -> None:
    RETRY_FILE.parent.mkdir(exist_ok=True)
    RETRY_FILE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    public = {key: value for key, value in record.items() if key != "wallet_balance"}
    PUBLIC_FILE.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not RETRY_FILE.exists():
        parity()
        parts = view("get_release", [3]).split("|")
        if len(parts) != 12 or parts[0] != "SEALED":
            raise RuntimeError("A2_NOT_SEALED")

        keys = json.loads(getpass.getpass("TEST_KEYS_REQUIRED_NO_ECHO: "))
        accounts = [
            create_account(account_private_key="0x" + key.removeprefix("0x"))
            for key in keys
        ]
        del keys
        matching = [account for account in accounts if account.address.lower() == REVIEWER.lower()]
        if len(matching) != 1:
            raise RuntimeError("REVIEWER_WALLET_MISMATCH")
        account = matching[0]
        balance = int(rpc("eth_getBalance", [REVIEWER, "latest"]), 16)
        if balance <= 0:
            raise RuntimeError("REVIEWER_BALANCE_EMPTY")

        record = {
            "contract": ADDRESS,
            "chain_id": 61999,
            "source_sha256": SOURCE_SHA256,
            "release_id": 3,
            "method": "assess_release",
            "args": [3],
            "original_tx": ORIGINAL_TX,
            "attempt_limit": 1,
            "submitted_attempts": 0,
            "status": "INTENT_SAVED",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "wallet_balance": balance,
        }
        save(record)
        client = create_client(chain=studionet, account=account)
        tx_hash = client.write_contract(
            address=ADDRESS,
            function_name="assess_release",
            args=[3],
            value=0,
        )
        record["hash"] = str(tx_hash)
        record["submitted_attempts"] = 1
        record["status"] = "SUBMITTED"
        save(record)
        print(json.dumps({"hash": record["hash"], "status": "SUBMITTED"}), flush=True)
    else:
        record = json.loads(RETRY_FILE.read_text(encoding="utf-8"))
        if record.get("attempt_limit") != 1 or record.get("submitted_attempts") != 1 or not record.get("hash"):
            raise RuntimeError("RETRY_JOURNAL_INVALID")

    while True:
        tx = rpc("eth_getTransactionByHash", [record["hash"]])
        status = tx.get("status") if tx else "PENDING"
        print(json.dumps({"hash": record["hash"], "status": status}), flush=True)
        if status == "FINALIZED":
            break
        if status in {"CANCELED", "UNDETERMINED"}:
            raise RuntimeError("RETRY_TERMINAL_FAILURE:" + status)
        time.sleep(10)

    actual = return_value(tx)
    parts = view("get_release", [3]).split("|")
    record.update({
        "status": "FINALIZED",
        "consensus": tx.get("result_name"),
        "return_value": actual,
        "readback": {
            "status": parts[0],
            "category": parts[8],
            "compliance": parts[9],
            "reason": parts[10],
        },
        "finished_at": datetime.now(timezone.utc).isoformat(),
    })
    save(record)
    print(json.dumps({
        "single_retry_complete": True,
        "hash": record["hash"],
        "status": record["status"],
        "consensus": record["consensus"],
        "return": actual,
        "readback": record["readback"],
    }), flush=True)


if __name__ == "__main__":
    main()

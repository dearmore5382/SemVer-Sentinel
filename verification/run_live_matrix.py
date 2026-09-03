"""Checkpointed Studionet matrix. Keys are read once through a no-echo prompt.

Every planned write has a frozen sender, method, arguments, expected return and
postcondition. An intent is persisted before signing; a hash is persisted once;
the runner only polls that hash and never retries a submission automatically.
"""
import base64
import getpass
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet


ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594"
SOURCE_SHA256 = "573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db"
PUBLISHER = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
REVIEWER = "0xA63DE24e30C88FB1019E8956654730316e36eDBE"
RPC = "https://studio.genlayer.com/api"
PRIVATE = ROOT / ".private" / ("live-matrix-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("live-matrix-" + ADDRESS.lower() + ".json")
POLICY = "Existing operations, required request fields, response fields and documented behavior must remain compatible."


def fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def args_from(data, old_version=None, new_version=None):
    return [
        data["package"], old_version or data["old_version"], new_version or data["new_version"],
        data["policy"], data["old_api"], data["new_api"],
    ]


ADDITIVE = fixture("additive.json")
BREAKING = fixture("breaking-patch.json")
INJECTION = fixture("prompt-injection.json")
PLAN = [
    {"id": "H1-create", "actor": PUBLISHER, "method": "create_release", "args": args_from(ADDITIVE), "expected": "0", "count": 1, "record": [0, "DRAFT", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "F1-wrong-seal", "actor": REVIEWER, "method": "seal_release", "args": [0], "expected": "PUBLISHER_ONLY", "count": 1, "record": [0, "DRAFT", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "H1-seal", "actor": PUBLISHER, "method": "seal_release", "args": [0], "expected": "RELEASE_SEALED", "count": 1, "record": [0, "SEALED", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "H1-assess", "actor": REVIEWER, "method": "assess_release", "args": [0], "expected": "COMPLIANT", "count": 1, "record": [0, "REVIEWED", "NON_BREAKING", "COMPLIANT"]},
    {"id": "A3-replay", "actor": PUBLISHER, "method": "assess_release", "args": [0], "expected": "RELEASE_NOT_ASSESSABLE", "count": 1, "record": [0, "REVIEWED", "NON_BREAKING", "COMPLIANT"]},
    {"id": "F2-equal-version", "actor": PUBLISHER, "method": "create_release", "args": ["signal-kit", "1.4.2", "1.4.2", POLICY, ADDITIVE["old_api"], ADDITIVE["new_api"]], "expected": "INVALID_VERSION_TRANSITION", "count": 1, "record": [0, "REVIEWED", "NON_BREAKING", "COMPLIANT"]},
    {"id": "A1-create", "actor": PUBLISHER, "method": "create_release", "args": args_from(BREAKING), "expected": "1", "count": 2, "record": [1, "DRAFT", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "A1-seal", "actor": PUBLISHER, "method": "seal_release", "args": [1], "expected": "RELEASE_SEALED", "count": 2, "record": [1, "SEALED", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "A1-assess", "actor": REVIEWER, "method": "assess_release", "args": [1], "expected": "VERSION_VIOLATION", "count": 2, "record": [1, "REVIEWED", "BREAKING", "VERSION_VIOLATION"]},
    {"id": "H2-create", "actor": PUBLISHER, "method": "create_release", "args": args_from(BREAKING, "1.4.2", "2.0.0"), "expected": "2", "count": 3, "record": [2, "DRAFT", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "H2-seal", "actor": PUBLISHER, "method": "seal_release", "args": [2], "expected": "RELEASE_SEALED", "count": 3, "record": [2, "SEALED", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "H2-assess", "actor": REVIEWER, "method": "assess_release", "args": [2], "expected": "COMPLIANT", "count": 3, "record": [2, "REVIEWED", "BREAKING", "COMPLIANT"]},
    {"id": "A2-create", "actor": PUBLISHER, "method": "create_release", "args": args_from(INJECTION), "expected": "3", "count": 4, "record": [3, "DRAFT", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "A2-seal", "actor": PUBLISHER, "method": "seal_release", "args": [3], "expected": "RELEASE_SEALED", "count": 4, "record": [3, "SEALED", "UNEVALUATED", "UNEVALUATED"]},
    {"id": "A2-assess", "actor": REVIEWER, "method": "assess_release", "args": [3], "expected": "VERSION_VIOLATION", "count": 4, "record": [3, "REVIEWED", "BREAKING", "VERSION_VIOLATION"]},
]


def rpc(method, params):
    if method not in {"eth_chainId", "eth_getBalance", "eth_getTransactionByHash", "gen_getContractCode", "gen_call"}:
        raise ValueError("RPC_NOT_ALLOWED")
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=40)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError("RPC_ERROR_" + str(data["error"].get("code")))
    return data["result"]


def view(method, args=None):
    encoded = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    params = {"type": "read", "to": ADDRESS, "from": PUBLISHER, "value": "0x0", "data": encoded, "transaction_hash_variant": "latest-final"}
    raw = rpc("gen_call", [params])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def parity():
    if int(rpc("eth_chainId", []), 16) != 61999:
        raise RuntimeError("WRONG_CHAIN")
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    if hashlib.sha256(deployed).hexdigest() != SOURCE_SHA256 or deployed != (ROOT / "contracts" / "SemVerSentinel.py").read_bytes():
        raise RuntimeError("SOURCE_MISMATCH")


def return_value(tx):
    leaders = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    if isinstance(leaders, dict):
        leaders = [leaders]
    leaders = [item for item in leaders if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    result = leaders[-1].get("result")
    raw = base64.b64decode(result["raw"] if isinstance(result, dict) else result)
    if not raw or raw[0] != 0:
        raise RuntimeError("CONTRACT_EXECUTION_ERROR")
    return str(calldata.decode(raw[1:]))


def verify_tx(tx, step):
    if tx.get("status") != "FINALIZED" or tx.get("result_name") != "MAJORITY_AGREE":
        raise RuntimeError("FINALITY_OR_CONSENSUS_FAILED")
    if str(tx.get("hash")).lower() != step["hash"].lower():
        raise RuntimeError("HASH_MISMATCH")
    if str(tx.get("from_address")).lower() != step["actor"].lower() or str(tx.get("to_address")).lower() != ADDRESS.lower():
        raise RuntimeError("PARTY_MISMATCH")
    decoded = calldata.decode(base64.b64decode(tx["data"]["calldata"]))
    if decoded != {"method": step["method"], "args": step["args"]}:
        raise RuntimeError("CALLDATA_MISMATCH")
    actual = return_value(tx)
    if actual != step["expected"]:
        raise RuntimeError("UNEXPECTED_RETURN:" + actual)
    return actual


def verify_readback(item):
    if int(view("get_release_count")) != item["count"]:
        raise RuntimeError("COUNT_MISMATCH")
    release_id, status, category, compliance = item["record"]
    parts = view("get_release", [release_id]).split("|")
    if len(parts) != 12 or parts[0] != status or parts[8] != category or parts[9] != compliance:
        raise RuntimeError("RECORD_MISMATCH")
    return {"release_count": item["count"], "release_id": release_id, "status": parts[0], "category": parts[8], "compliance": parts[9], "reason": parts[10]}


def public_report(journal):
    clean = {key: value for key, value in journal.items() if key != "wallet_balances"}
    clean["steps"] = []
    for step in journal["steps"]:
        tx = step.get("receipt") or {}
        clean["steps"].append({
            "id": step["id"], "actor": step["actor"], "method": step["method"], "args": step["args"],
            "expected": step["expected"], "hash": step.get("hash"), "status": step.get("status"),
            "final_status": tx.get("status"), "consensus": tx.get("result_name"), "readback": step.get("readback"),
        })
    PUBLIC.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("INTERACTIVE_NO_ECHO_TERMINAL_REQUIRED")
    keys = json.loads(getpass.getpass("KEY_INPUT_REQUIRED_NO_ECHO: "))
    accounts = [create_account(account_private_key="0x" + key.removeprefix("0x")) for key in keys]
    del keys
    clients = {account.address.lower(): create_client(chain=studionet, account=account) for account in accounts}
    if set(clients) != {PUBLISHER.lower(), REVIEWER.lower()}:
        raise RuntimeError("AUTHORIZED_WALLET_MISMATCH")
    parity()
    balances = {address: int(rpc("eth_getBalance", [address, "latest"]), 16) for address in (PUBLISHER, REVIEWER)}
    if not all(value > 0 for value in balances.values()):
        raise RuntimeError("TEST_WALLET_BALANCE_EMPTY")
    if PRIVATE.exists():
        journal = json.loads(PRIVATE.read_text(encoding="utf-8"))
        if journal["contract"].lower() != ADDRESS.lower() or journal["source_sha256"] != SOURCE_SHA256:
            raise RuntimeError("JOURNAL_IDENTITY_MISMATCH")
    else:
        if int(view("get_release_count")) != 0:
            raise RuntimeError("EXPECTED_FRESH_CONTRACT")
        journal = {"contract": ADDRESS, "chain_id": 61999, "source_sha256": SOURCE_SHA256, "started_at": datetime.now(timezone.utc).isoformat(), "wallet_balances": balances, "steps": [], "complete": False}
    PRIVATE.parent.mkdir(exist_ok=True)

    def save():
        PRIVATE.write_text(json.dumps(journal, indent=2), encoding="utf-8")
        public_report(journal)

    save()
    print(json.dumps({"ready": True, "balances": balances, "completed_steps": len(journal["steps"]), "total_steps": len(PLAN)}), flush=True)
    for index in range(len(PLAN)):
        item = PLAN[index]
        parity()
        if index < len(journal["steps"]):
            step = journal["steps"][index]
            if step["id"] != item["id"]:
                raise RuntimeError("JOURNAL_PLAN_MISMATCH")
            if step["status"] == "READBACK_VERIFIED":
                continue
            if step["status"] != "SUBMITTED" or not step.get("hash"):
                raise RuntimeError("UNKNOWN_SUBMISSION_KEEP_INTENT")
            print(json.dumps({"step": step["id"], "hash": step["hash"], "status": "RESUME_POLL"}), flush=True)
        else:
            step = dict(item)
            step["status"] = "INTENT_SAVED"
            step["submitted_at"] = datetime.now(timezone.utc).isoformat()
            journal["steps"].append(step)
            save()
            tx_hash = clients[step["actor"].lower()].write_contract(address=ADDRESS, function_name=step["method"], args=step["args"], value=0, leader_only=False)
            step["hash"] = str(tx_hash)
            step["status"] = "SUBMITTED"
            save()
            print(json.dumps({"step": step["id"], "hash": step["hash"], "status": "SUBMITTED"}), flush=True)
        deadline = time.monotonic() + 1200
        last_status = None
        while time.monotonic() < deadline:
            tx = rpc("eth_getTransactionByHash", [step["hash"]])
            status = None if tx is None else tx.get("status")
            if status != last_status:
                print(json.dumps({"step": step["id"], "hash": step["hash"], "status": status}), flush=True)
                last_status = status
            if tx and status == "FINALIZED":
                step["receipt"] = tx
                verify_tx(tx, step)
                step["readback"] = verify_readback(item)
                step["status"] = "READBACK_VERIFIED"
                save()
                print(json.dumps({"step": step["id"], "verified": True, "return": step["expected"], "readback": step["readback"]}), flush=True)
                break
            time.sleep(8)
        else:
            raise RuntimeError("POLL_TIMEOUT_KEEP_EXISTING_HASH")
    journal["complete"] = True
    journal["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps({"live_matrix_complete": True, "steps": len(journal["steps"]), "final_release_count": int(view("get_release_count"))}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"fatal_error_type": type(exc).__name__, "journal_preserved": True}), flush=True)
        raise

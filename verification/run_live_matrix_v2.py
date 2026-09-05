"""Checkpointed v2 Studionet audit. Never automatically resubmits a hash."""
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
ADDRESS = "0x118f353B758ca1B26d07ec1082B12495107Cf5b3"
SOURCE_SHA256 = "24c3b47811ff42d3733edfbd49259f3ed04770ea1171f1c425c153c81ac6298a"
PUBLISHER = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
REVIEWER = "0xA63DE24e30C88FB1019E8956654730316e36eDBE"
RPC = "https://studio.genlayer.com/api"
REVISION = "c199fa1b2eab1b8daa76c86ebe448f1c6dfac1f6"
RAW = f"https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/{REVISION}/fixtures/artifacts/"
POLICY = "Existing operations, required request fields, response fields and documented behavior must remain compatible."
PRIVATE = ROOT / ".private" / ("live-matrix-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("live-matrix-" + ADDRESS.lower() + ".json")

DIGESTS = {
    "additive-minor.json": "12032ff8f4d678650ad67434a000dca2044226fcbadd2fcd777b5197dc9d73d8",
    "breaking-major.json": "5a80f119d002c5b0f9ae47f4185df6794d821e52ebe87a6719badf9d3a6a6d32",
    "prompt-injection-patch.json": "be9e1e09edf2d22358c78eecec4cc3186f8787374296362f6d6a4f2246dd3b1c",
    "wrong-authority.json": "7a7dbf8b59b12b11f055549df755baee9439a17f8822bf344075899f51d145b9",
    "wrong-package.json": "db264be2680eeac65b33520eecce91af102a68a043bfee7faf30fa3b35808413",
}

def create_args(old, new, name, digest=None, url=None):
    return [old, new, POLICY, url or RAW + name, digest or DIGESTS[name]]

def step(case, actor, method, args, expected, count, record=None):
    return {"id": case, "actor": actor, "method": method, "args": args, "expected": expected, "count": count, "record": record}

PLAN = [
    step("F1-mutable-url", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json", url="https://raw.githubusercontent.com/dearmore5382/SemVer-Sentinel/main/fixtures/artifacts/additive-minor.json"), "IMMUTABLE_GITHUB_ARTIFACT_REQUIRED", 0),
    step("F2-deceptive-host", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json", url=f"https://raw.githubusercontent.com.evil.example/dearmore5382/SemVer-Sentinel/{REVISION}/artifact.json"), "IMMUTABLE_GITHUB_ARTIFACT_REQUIRED", 0),
    step("H1-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json"), "0", 1, [0, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("G1-outsider-seal", REVIEWER, "seal_release", [0], "PUBLISHER_ONLY", 1, [0, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("H1-seal", PUBLISHER, "seal_release", [0], "RELEASE_SEALED", 1, [0, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("H1-assess", REVIEWER, "assess_release", [0], "COMPLIANT", 1, [0, "REVIEWED", "NON_BREAKING", "COMPLIANT"]),
    step("G2-replay", PUBLISHER, "assess_release", [0], "RELEASE_NOT_ASSESSABLE", 1, [0, "REVIEWED", "NON_BREAKING", "COMPLIANT"]),
    step("H2-create", PUBLISHER, "create_release", create_args("1.4.2", "2.0.0", "breaking-major.json"), "1", 2, [1, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("H2-seal", PUBLISHER, "seal_release", [1], "RELEASE_SEALED", 2, [1, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("H2-assess", REVIEWER, "assess_release", [1], "COMPLIANT", 2, [1, "REVIEWED", "BREAKING", "COMPLIANT"]),
    step("A1-create", PUBLISHER, "create_release", create_args("1.4.2", "1.4.3", "prompt-injection-patch.json"), "2", 3, [2, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("A1-seal", PUBLISHER, "seal_release", [2], "RELEASE_SEALED", 3, [2, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("A1-assess", REVIEWER, "assess_release", [2], "VERSION_VIOLATION", 3, [2, "REVIEWED", "BREAKING", "VERSION_VIOLATION"]),
    step("F3-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json", digest="0" * 64), "3", 4, [3, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("F3-seal", PUBLISHER, "seal_release", [3], "RELEASE_SEALED", 4, [3, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("F3-assess", REVIEWER, "assess_release", [3], "ARTIFACT_REJECTED", 4, [3, "REJECTED", "REJECTED", "ARTIFACT_REJECTED"]),
    step("F4-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "wrong-authority.json"), "4", 5, [4, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("F4-seal", PUBLISHER, "seal_release", [4], "RELEASE_SEALED", 5, [4, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("F4-assess", REVIEWER, "assess_release", [4], "ARTIFACT_REJECTED", 5, [4, "REJECTED", "REJECTED", "ARTIFACT_REJECTED"]),
    step("F5-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "wrong-package.json"), "5", 6, [5, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("F5-seal", PUBLISHER, "seal_release", [5], "RELEASE_SEALED", 6, [5, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    step("F5-assess", REVIEWER, "assess_release", [5], "ARTIFACT_REJECTED", 6, [5, "REJECTED", "REJECTED", "ARTIFACT_REJECTED"]),
    step("R1-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json", digest="0" * 64, url=RAW + "missing.json"), "6", 7, [6, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("R1-seal", PUBLISHER, "seal_release", [6], "RELEASE_SEALED", 7, [6, "SEALED", "UNEVALUATED", "UNEVALUATED"]),
    # GitHub raw serves a deterministic 404 response body, so a missing path is
    # content with the wrong digest and must be rejected rather than retried.
    step("R1-assess", REVIEWER, "assess_release", [6], "ARTIFACT_REJECTED", 7, [6, "REJECTED", "REJECTED", "ARTIFACT_REJECTED"]),
    step("G1-cancel-create", PUBLISHER, "create_release", create_args("1.4.2", "1.5.0", "additive-minor.json"), "7", 8, [7, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("G1-outsider-cancel", REVIEWER, "cancel_draft", [7], "PUBLISHER_ONLY", 8, [7, "DRAFT", "UNEVALUATED", "UNEVALUATED"]),
    step("G1-owner-cancel", PUBLISHER, "cancel_draft", [7], "RELEASE_CANCELLED", 8, [7, "CANCELLED", "UNEVALUATED", "UNEVALUATED"]),
]

def rpc(method, params):
    allowed = {"eth_chainId", "eth_getBalance", "eth_getTransactionByHash", "gen_getContractCode", "gen_call"}
    if method not in allowed:
        raise ValueError("RPC_NOT_ALLOWED")
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=45)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError("RPC_ERROR:" + str(data["error"].get("message")))
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

def verify_tx(tx, item):
    if tx.get("status") != "FINALIZED" or tx.get("result_name") != "MAJORITY_AGREE":
        raise RuntimeError("FINALITY_OR_CONSENSUS_FAILED")
    if str(tx.get("hash")).lower() != item["hash"].lower():
        raise RuntimeError("HASH_MISMATCH")
    if str(tx.get("from_address")).lower() != item["actor"].lower() or str(tx.get("to_address")).lower() != ADDRESS.lower():
        raise RuntimeError("PARTY_MISMATCH")
    decoded = calldata.decode(base64.b64decode(tx["data"]["calldata"]))
    if decoded != {"method": item["method"], "args": item["args"]}:
        raise RuntimeError("CALLDATA_MISMATCH")
    actual = return_value(tx)
    if actual != item["expected"] and not (item["method"] == "assess_release" and actual == "ASSESSMENT_RETRYABLE"):
        raise RuntimeError("UNEXPECTED_RETURN:" + actual)
    return actual

def verify_readback(item):
    if int(view("get_release_count")) != item["count"]:
        raise RuntimeError("COUNT_MISMATCH")
    if item["record"] is None:
        return {"release_count": item["count"]}
    release_id, status, category, compliance = item["record"]
    parts = view("get_release", [release_id]).split("|")
    if len(parts) != 14 or parts[0] != status or parts[10] != category or parts[11] != compliance:
        raise RuntimeError("RECORD_MISMATCH:" + "|".join(parts[:13]))
    return {"release_count": item["count"], "release_id": release_id, "status": parts[0], "package": parts[2], "commit": parts[7], "expected_digest": parts[8], "actual_digest": parts[9], "category": parts[10], "compliance": parts[11], "reason": parts[12]}

def save(journal):
    PRIVATE.parent.mkdir(exist_ok=True)
    PRIVATE.write_text(json.dumps(journal, indent=2), encoding="utf-8")
    public = json.loads(json.dumps({key: value for key, value in journal.items() if key != "wallet_balances"}))
    for item in public["steps"]:
        item.pop("receipt", None)
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")

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
        journal = {"contract": ADDRESS, "chain_id": 61999, "source_sha256": SOURCE_SHA256, "artifact_revision": REVISION, "started_at": datetime.now(timezone.utc).isoformat(), "wallet_balances": balances, "steps": [], "complete": False}
    save(journal)
    print(json.dumps({"ready": True, "balances": balances, "completed_steps": len(journal["steps"]), "total_steps": len(PLAN)}), flush=True)
    for index, planned in enumerate(PLAN):
        parity()
        if index < len(journal["steps"]):
            current = journal["steps"][index]
            if current["id"] != planned["id"]:
                raise RuntimeError("JOURNAL_PLAN_MISMATCH")
            if current["id"] == "R1-assess" and current["expected"] == "ASSESSMENT_RETRYABLE":
                current["expected"] = planned["expected"]
                current["record"] = planned["record"]
                current["expectation_correction"] = "GitHub raw 404 is a fetched body; exact digest binding safely rejects it."
                save(journal)
            if current["status"] == "READBACK_VERIFIED":
                continue
            if current["status"] != "SUBMITTED" or not current.get("hash"):
                raise RuntimeError("UNKNOWN_SUBMISSION_KEEP_INTENT")
        else:
            current = dict(planned)
            current["status"] = "INTENT_SAVED"
            current["submitted_at"] = datetime.now(timezone.utc).isoformat()
            journal["steps"].append(current)
            save(journal)
            tx_hash = clients[current["actor"].lower()].write_contract(address=ADDRESS, function_name=current["method"], args=current["args"], value=0, leader_only=False)
            current["hash"] = str(tx_hash)
            current["status"] = "SUBMITTED"
            save(journal)
            print(json.dumps({"step": current["id"], "hash": current["hash"], "status": "SUBMITTED"}), flush=True)
        deadline = time.monotonic() + 1200
        last_status = None
        while time.monotonic() < deadline:
            tx = rpc("eth_getTransactionByHash", [current["hash"]])
            status = None if tx is None else tx.get("status")
            if status != last_status:
                print(json.dumps({"step": current["id"], "hash": current["hash"], "status": status}), flush=True)
                last_status = status
            if tx and status == "FINALIZED":
                actual = verify_tx(tx, current)
                if actual == "ASSESSMENT_RETRYABLE" and current["expected"] != actual:
                    release_id = planned["record"][0]
                    parts = view("get_release", [release_id]).split("|")
                    if len(parts) != 14 or parts[0] != "SEALED" or parts[10] != "UNEVALUATED" or parts[11] != "UNEVALUATED":
                        raise RuntimeError("RETRYABLE_MUTATED_STATE")
                    attempts = current.setdefault("retryable_attempts", [])
                    attempts.append({"hash": current["hash"], "final_status": tx.get("status"), "consensus": tx.get("result_name"), "return": actual, "readback_status": parts[0]})
                    if len(attempts) > 1:
                        current["status"] = "RETRY_LIMIT_REACHED"
                        save(journal)
                        raise RuntimeError("SINGLE_RETRY_EXHAUSTED")
                    retry_hash = clients[current["actor"].lower()].write_contract(address=ADDRESS, function_name=current["method"], args=current["args"], value=0, leader_only=False)
                    current["hash"] = str(retry_hash)
                    current["status"] = "SUBMITTED"
                    current["retry_submitted_at"] = datetime.now(timezone.utc).isoformat()
                    save(journal)
                    print(json.dumps({"step": current["id"], "hash": current["hash"], "status": "ONE_DOCUMENTED_RETRY", "prior": attempts[-1]["hash"]}), flush=True)
                    deadline = time.monotonic() + 1200
                    last_status = None
                    continue
                current["receipt"] = tx
                current["readback"] = verify_readback(planned)
                current["status"] = "READBACK_VERIFIED"
                save(journal)
                print(json.dumps({"step": current["id"], "verified": True, "return": current["expected"], "readback": current["readback"]}), flush=True)
                break
            time.sleep(8)
        else:
            raise RuntimeError("POLL_TIMEOUT_KEEP_EXISTING_HASH")
    journal["complete"] = True
    journal["completed_at"] = datetime.now(timezone.utc).isoformat()
    save(journal)
    print(json.dumps({"live_matrix_complete": True, "steps": len(journal["steps"]), "final_release_count": int(view("get_release_count"))}), flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"fatal_error_type": type(exc).__name__, "journal_preserved": True}), flush=True)
        raise

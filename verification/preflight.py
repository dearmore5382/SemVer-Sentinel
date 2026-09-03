"""Read-only Studionet deployment parity and initial-state check."""
import base64
import hashlib
import json
from pathlib import Path

import requests
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize


ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xfdA283EF4D39763ECbFf3BC739cBfB12fF5E3594"
SENDER = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
RPC = "https://studio.genlayer.com/api"
SOURCE = ROOT / "contracts" / "SemVerSentinel.py"
EXPECTED_SHA256 = "573c0feeda059b10071ba8863f92d5fa51723f10f50c112bd877924217c2e4db"


def rpc(method, params):
    if method not in {"eth_chainId", "gen_getContractCode", "gen_getContractSchema", "gen_call"}:
        raise ValueError("READ_ONLY_RPC_ONLY")
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=40)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(json.dumps({"code": data["error"].get("code"), "message": data["error"].get("message")}))
    return data["result"]


def view(method, args=None):
    encoded = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    params = {
        "type": "read", "to": ADDRESS, "from": SENDER, "value": "0x0", "data": encoded,
        "transaction_hash_variant": "latest-final",
    }
    raw = rpc("gen_call", [params])
    return calldata.decode(bytes.fromhex(raw.removeprefix("0x")))


def main():
    chain_id = int(rpc("eth_chainId", []), 16)
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    local = SOURCE.read_bytes()
    deployed_hash = hashlib.sha256(deployed).hexdigest()
    local_hash = hashlib.sha256(local).hexdigest()
    if chain_id != 61999:
        raise RuntimeError("WRONG_CHAIN")
    if local_hash != EXPECTED_SHA256 or deployed != local:
        raise RuntimeError("SOURCE_PARITY_FAILED:" + deployed_hash)
    count = int(view("get_release_count"))
    schema = rpc("gen_getContractSchema", [ADDRESS])
    report = {
        "network": "Studionet", "chain_id": chain_id, "contract": ADDRESS,
        "source_sha256": deployed_hash, "exact_source_parity": True,
        "initial_release_count": count, "schema": schema,
    }
    output = ROOT / "verification" / ("preflight-" + ADDRESS.lower() + ".json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "schema"}, indent=2))
    if count != 0:
        raise RuntimeError("INITIAL_STATE_NOT_EMPTY")


if __name__ == "__main__":
    main()

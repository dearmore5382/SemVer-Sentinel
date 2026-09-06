"""Read-only source parity and initial-state check for v3."""
import base64
import hashlib
import json
from pathlib import Path
import requests
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xd44DF7b3D9bdD91731D46801E8a7eb057640be0E"
SENDER = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
RPC = "https://studio.genlayer.com/api"
EXPECTED_SHA256 = "a52d21bf67dcfb08daefc0f5a17b39fbc5793b08091f72db461db4202aa01301"

def rpc(method, params):
    if method not in {"eth_chainId", "gen_getContractCode", "gen_getContractSchema", "gen_call"}:
        raise ValueError("READ_ONLY_RPC_ONLY")
    response = requests.post(RPC, json={"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout=45)
    response.raise_for_status(); data = response.json()
    if "error" in data: raise RuntimeError(json.dumps(data["error"]))
    return data["result"]

def view(method, args=None):
    encoded = serialize([calldata.encode({"method":method,"args":args or []}), b"\x00"])
    params = {"type":"read","to":ADDRESS,"from":SENDER,"value":"0x0","data":encoded,"transaction_hash_variant":"latest-final"}
    return calldata.decode(bytes.fromhex(rpc("gen_call", [params]).removeprefix("0x")))

def main():
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    local = (ROOT / "contracts" / "SemVerSentinel.py").read_bytes()
    report = {"network":"Studionet","chain_id":int(rpc("eth_chainId", []),16),"contract":ADDRESS,"source_sha256":hashlib.sha256(deployed).hexdigest(),"exact_source_parity":deployed == local,"initial_release_count":int(view("get_release_count")),"schema":rpc("gen_getContractSchema", [ADDRESS])}
    if report["chain_id"] != 61999: raise RuntimeError("WRONG_CHAIN")
    if report["source_sha256"] != EXPECTED_SHA256 or not report["exact_source_parity"]: raise RuntimeError("SOURCE_PARITY_FAILED:"+report["source_sha256"])
    output = ROOT / "verification" / ("preflight-" + ADDRESS.lower() + ".json")
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "schema"},indent=2))

if __name__ == "__main__": main()

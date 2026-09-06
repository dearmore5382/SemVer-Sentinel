"""Checkpointed v3 Studionet audit; never silently resubmits a transaction."""
import base64, getpass, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT=Path(__file__).resolve().parents[1]
ADDRESS="0xd44DF7b3D9bdD91731D46801E8a7eb057640be0E"
SOURCE_SHA256="a52d21bf67dcfb08daefc0f5a17b39fbc5793b08091f72db461db4202aa01301"
RPC="https://studio.genlayer.com/api"
POLICY="Existing exported TypeScript declarations and required parameters must remain compatible."
PRIVATE=ROOT/".private"/("live-matrix-"+ADDRESS.lower()+".json")
PUBLIC=ROOT/"verification"/("live-matrix-"+ADDRESS.lower()+".json")

def rpc(method,params):
    if method not in {"eth_chainId","eth_getBalance","eth_getTransactionByHash","gen_getContractCode","gen_call"}: raise ValueError("RPC_NOT_ALLOWED")
    response=requests.post(RPC,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout=45); response.raise_for_status(); data=response.json()
    if "error" in data: raise RuntimeError("RPC_ERROR:"+str(data["error"].get("message")))
    return data["result"]

def view(method,args=None,sender="0x0000000000000000000000000000000000000001"):
    encoded=serialize([calldata.encode({"method":method,"args":args or []}),b"\x00"])
    raw=rpc("gen_call",[{"type":"read","to":ADDRESS,"from":sender,"value":"0x0","data":encoded,"transaction_hash_variant":"latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))

def source_parity():
    deployed=base64.b64decode(rpc("gen_getContractCode",[ADDRESS])); local=(ROOT/"contracts"/"SemVerSentinel.py").read_bytes()
    if int(rpc("eth_chainId",[]),16)!=61999 or deployed!=local or hashlib.sha256(deployed).hexdigest()!=SOURCE_SHA256: raise RuntimeError("SOURCE_PARITY_FAILED")

def tx_return(tx):
    receipts=(tx.get("consensus_data") or {}).get("leader_receipt") or []; receipts=[receipts] if isinstance(receipts,dict) else receipts
    leaders=[x for x in receipts if x.get("mode")=="leader"]
    if not leaders or leaders[-1].get("execution_result")!="SUCCESS": raise RuntimeError("LEADER_EXECUTION_FAILED")
    value=leaders[-1].get("result"); raw=base64.b64decode(value["raw"] if isinstance(value,dict) else value)
    if not raw or raw[0]!=0: raise RuntimeError("CONTRACT_EXECUTION_ERROR")
    return str(calldata.decode(raw[1:]))

def save(journal):
    PRIVATE.parent.mkdir(exist_ok=True); PRIVATE.write_text(json.dumps(journal,indent=2),encoding="utf-8")
    public=json.loads(json.dumps(journal)); public.pop("balances",None)
    for item in public["steps"]: item.pop("receipt",None)
    PUBLIC.write_text(json.dumps(public,indent=2)+"\n",encoding="utf-8")

def main():
    if not sys.stdin.isatty(): raise RuntimeError("INTERACTIVE_NO_ECHO_TERMINAL_REQUIRED")
    keys=json.loads(getpass.getpass("KEY_INPUT_REQUIRED_NO_ECHO: ")); accounts=[create_account(account_private_key="0x"+k.removeprefix("0x")) for k in keys]; del keys
    if len(accounts)!=2: raise RuntimeError("TWO_TEST_WALLETS_REQUIRED")
    owner,outsider=accounts; clients={a.address.lower():create_client(chain=studionet,account=a) for a in accounts}
    source_parity(); balances={a.address:int(rpc("eth_getBalance",[a.address,"latest"]),16) for a in accounts}
    if not all(balances.values()): raise RuntimeError("TEST_WALLET_BALANCE_EMPTY")
    plan=[
      {"id":"F1-invalid-input","actor":owner.address,"method":"create_release","args":["https://evil","1.0.0","1.1.0",POLICY],"expected":"INVALID_NPM_PACKAGE","count":0},
      {"id":"H1-create","actor":owner.address,"method":"create_release","args":["p-limit","3.0.0","3.1.0",POLICY],"expected":"0","count":1},
      {"id":"A1-outsider-seal","actor":outsider.address,"method":"seal_release","args":[0],"expected":"PUBLISHER_ONLY","count":1},
      {"id":"H1-seal","actor":owner.address,"method":"seal_release","args":[0],"expected":"RELEASE_SEALED","count":1},
      {"id":"H1-assess","actor":outsider.address,"method":"assess_release","args":[0],"expected_one_of":["COMPLIANT","REVIEW_REQUIRED","VERSION_VIOLATION"],"count":1,"verified_artifact":True},
      {"id":"A2-replay","actor":owner.address,"method":"assess_release","args":[0],"expected":"RELEASE_NOT_ASSESSABLE","count":1},
      {"id":"F2-create-missing","actor":owner.address,"method":"create_release","args":["semver-sentinel-package-that-does-not-exist","1.0.0","1.1.0",POLICY],"expected":"1","count":2},
      {"id":"F2-seal-missing","actor":owner.address,"method":"seal_release","args":[1],"expected":"RELEASE_SEALED","count":2},
      {"id":"F2-assess-missing","actor":outsider.address,"method":"assess_release","args":[1],"expected":"ARTIFACT_REJECTED","count":2},
    ]
    if PRIVATE.exists(): journal=json.loads(PRIVATE.read_text(encoding="utf-8"))
    else:
        if int(view("get_release_count",sender=owner.address))!=0: raise RuntimeError("EXPECTED_FRESH_CONTRACT")
        journal={"contract":ADDRESS,"source_sha256":SOURCE_SHA256,"started_at":datetime.now(timezone.utc).isoformat(),"wallets":[a.address for a in accounts],"balances":balances,"steps":[],"complete":False}; save(journal)
    print(json.dumps({"ready":True,"wallets":journal["wallets"],"balances":balances,"completed":len(journal["steps"]),"total":len(plan)}),flush=True)
    for index,want in enumerate(plan):
        source_parity()
        if index<len(journal["steps"]):
            item=journal["steps"][index]
            if item["id"]!=want["id"]: raise RuntimeError("JOURNAL_PLAN_MISMATCH")
            if item.get("status")=="READBACK_VERIFIED": continue
            if item.get("status")!="SUBMITTED": raise RuntimeError("UNKNOWN_INTENT_STATE")
        else:
            item=dict(want); item["status"]="INTENT_SAVED"; journal["steps"].append(item); save(journal)
            item["hash"]=str(clients[item["actor"].lower()].write_contract(address=ADDRESS,function_name=item["method"],args=item["args"],value=0,leader_only=False)); item["status"]="SUBMITTED"; save(journal)
            print(json.dumps({"step":item["id"],"hash":item["hash"],"status":"SUBMITTED"}),flush=True)
        deadline=time.monotonic()+1200
        while time.monotonic()<deadline:
            tx=rpc("eth_getTransactionByHash",[item["hash"]])
            if tx and tx.get("status")=="FINALIZED":
                if tx.get("result_name")!="MAJORITY_AGREE": raise RuntimeError("CONSENSUS_FAILED")
                actual=tx_return(tx); allowed=item.get("expected_one_of",[item.get("expected")])
                if item["id"]=="H1-assess" and actual=="ASSESSMENT_RETRYABLE":
                    parts=view("get_release",[0],owner.address).split("|")
                    if parts[0]!="SEALED" or parts[6]!="UNEVALUATED" or parts[7]!="UNEVALUATED": raise RuntimeError("RETRYABLE_MUTATED_STATE")
                    attempts=item.setdefault("retryable_attempts",[]); attempts.append({"hash":item["hash"],"return":actual,"state":parts[0]})
                    if len(attempts)>1: item["status"]="RETRY_LIMIT_REACHED"; save(journal); raise RuntimeError("SINGLE_RETRY_EXHAUSTED")
                    item["hash"]=str(clients[item["actor"].lower()].write_contract(address=ADDRESS,function_name=item["method"],args=item["args"],value=0,leader_only=False)); item["status"]="SUBMITTED"; save(journal)
                    print(json.dumps({"step":item["id"],"status":"ONE_DOCUMENTED_RETRY","hash":item["hash"],"prior":attempts[-1]["hash"]}),flush=True); deadline=time.monotonic()+1200; continue
                if actual not in allowed: raise RuntimeError("UNEXPECTED_RETURN:"+actual)
                count=int(view("get_release_count",sender=owner.address))
                if count!=item["count"]: raise RuntimeError("COUNT_MISMATCH")
                readback={"release_count":count}
                if item["id"]=="H1-assess":
                    parts=view("get_release",[0],owner.address).split("|"); proof=json.loads(parts[9])
                    if parts[0]!="REVIEWED" or proof["provenance_status"]!="VERIFIED" or not all(proof[k] for k in ("old_integrity","new_integrity","old_source_sha256","new_source_sha256")): raise RuntimeError("VERIFIED_BINDING_MISSING")
                    readback={"status":parts[0],"package":parts[2],"versions":parts[3:5],"category":parts[6],"compliance":parts[7],"reason":parts[8],"proof":proof}
                if item["id"]=="F2-assess-missing":
                    parts=view("get_release",[1],owner.address).split("|")
                    if parts[0]!="REJECTED" or parts[7]!="ARTIFACT_REJECTED": raise RuntimeError("FAIL_CLOSED_READBACK_MISSING")
                    readback={"status":parts[0],"compliance":parts[7],"reason":parts[8]}
                item.update({"actual":actual,"receipt":tx,"readback":readback,"status":"READBACK_VERIFIED"}); save(journal); print(json.dumps({"step":item["id"],"actual":actual,"readback":readback}),flush=True); break
            time.sleep(8)
        else: raise RuntimeError("POLL_TIMEOUT_KEEP_HASH")
    journal["complete"]=True; journal["completed_at"]=datetime.now(timezone.utc).isoformat(); save(journal); print(json.dumps({"complete":True,"steps":len(plan)}))

if __name__=="__main__": main()

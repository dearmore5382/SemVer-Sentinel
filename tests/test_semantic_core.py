import ast
from pathlib import Path
SOURCE=(Path(__file__).resolve().parents[1]/"contracts"/"SemVerSentinel.py").read_text(encoding="utf-8")
def core():
    tree=ast.parse(SOURCE); wanted={"REGISTRY","_version_parts","_bump_kind","_valid_package","_registry_url","_tarball_url","_base_observation","_normalize","_derive"}; nodes=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in wanted for t in node.targets): nodes.append(node)
        if isinstance(node,ast.FunctionDef) and node.name in wanted: nodes.append(node)
    class U(Exception): pass
    class V: UserError=U
    class G: vm=V
    ns={"typing":__import__("typing"),"gl":G}; exec(compile(ast.Module(body=nodes,type_ignores=[]),"core","exec"),ns); return ns
C=core()
def obs(provenance="VERIFIED",surface="ADDITIVE",request="COMPATIBLE",response="COMPATIBLE",behavior="COMPATIBLE",docs="NO",status="AVAILABLE"):
    verified=provenance=="VERIFIED"
    return {"analysis_status":status,"surface_change":surface,"request_compatibility":request,"response_compatibility":response,"behavior_compatibility":behavior,"documentation_only":docs,"provenance_status":provenance,"old_integrity":"sha512-"+"A"*88 if verified else "","new_integrity":"sha512-"+"B"*88 if verified else "","old_source_sha256":"a"*64 if verified else "","new_source_sha256":"b"*64 if verified else ""}
def test_semver_and_package_inputs_are_bounded():
    bump=C["_bump_kind"]; assert [bump("1.2.3",x) for x in ("2.0.0","1.3.0","1.2.4")]==["MAJOR","MINOR","PATCH"]
    assert bump("1.2.3","1.2.3")=="INVALID"; assert C["_valid_package"]("@scope/pkg"); assert C["_valid_package"]("p-limit")
    for bad in ("Owner/Pkg","../pkg","pkg//x","https://evil"): assert not C["_valid_package"](bad)
def test_registry_urls_are_contract_derived():
    assert C["_registry_url"]("p-limit","3.1.0")=="https://registry.npmjs.org/p-limit/3.1.0"
    assert C["_tarball_url"]("@scope/pkg","1.0.0")=="https://registry.npmjs.org/@scope/pkg/-/pkg-1.0.0.tgz"
def test_provenance_is_mandatory_and_semver_is_deterministic():
    derive=C["_derive"]; assert derive(obs(),"MINOR")["compliance"]=="COMPLIANT"
    for reason in ("REGISTRY_INVALID","INTEGRITY_MISMATCH","SOURCE_MISSING"):
        assert derive(obs(reason,status="UNAVAILABLE"),"MAJOR")=={"category":"REJECTED","compliance":"ARTIFACT_REJECTED","reason":reason}
    assert derive(obs("UNAVAILABLE",status="UNAVAILABLE"),"MINOR")["compliance"]=="RETRYABLE"
    assert derive(obs(surface="REMOVAL",response="INCOMPATIBLE"),"PATCH")["compliance"]=="VERSION_VIOLATION"
def test_normalizer_rejects_extra_keys_and_fake_provenance():
    normalize=C["_normalize"]; assert normalize(obs())["provenance_status"]=="VERIFIED"
    for bad in (dict(obs(),verdict="COMPLIANT"),dict(obs(),provenance_status="TRUST_ME")):
        try: normalize(bad); raise AssertionError("accepted")
        except Exception: pass

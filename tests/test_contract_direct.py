import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

from gltest.direct import VMContext, create_address, deploy_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "SemVerSentinel.py"
POLICY = "Existing operations, required inputs, response fields and documented behavior must remain compatible."
OLD = "POST /signals body { name: string } -> 201 { id: string, state: string }"
NEW = "POST /signals body { name: string } -> 201 { id: string, state: string }\nGET /signals/{id} -> 200"


def deploy():
    publisher = create_address("publisher")
    outsider = create_address("outsider")
    vm = VMContext(publisher)
    with patch("os.unlink", lambda _path: None):
        with vm.activate():
            contract = deploy_contract(CONTRACT, vm)
            loaded_gl = contract._instance.create_release.__globals__["gl"]
            _ = loaded_gl.nondet
            _ = loaded_gl.vm
    gl_proxy = contract._instance.create_release.__globals__["gl"]
    sdk_root = str(Path(gl_proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    importlib.import_module("genlayer")
    return vm, contract, publisher, outsider


def sync_message(vm, contract):
    gl_proxy = contract._instance.create_release.__globals__["gl"]
    sdk_root = str(Path(gl_proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    message = gl_proxy.message
    address_type = type(message.sender_address)
    value_type = type(message.value)
    sender = vm.sender
    if isinstance(sender, bytes):
        sender = address_type(sender)
    gl_proxy._cached_gl.message = message._replace(sender_address=sender, origin_address=sender, value=value_type(vm.value))
    gl_proxy._cached_gl.message_raw["sender_address"] = sender
    gl_proxy._cached_gl.message_raw["origin_address"] = sender


def observation(surface="ADDITIVE", request="COMPATIBLE", response="COMPATIBLE", behavior="COMPATIBLE", docs="NO", status="AVAILABLE"):
    return json.dumps({
        "analysis_status": status,
        "surface_change": surface,
        "request_compatibility": request,
        "response_compatibility": response,
        "behavior_compatibility": behavior,
        "documentation_only": docs,
    }, separators=(",", ":"))


def create(vm, contract, old="1.4.2", new="1.5.0"):
    with vm.activate():
        sync_message(vm, contract)
        return contract.create_release("signal-kit", old, new, POLICY, OLD, NEW)


def assess(vm, contract, release_id, result):
    vm.clear_mocks()
    vm.mock_llm(r"(?s).*analysis_status.*surface_change.*request_compatibility.*", result)
    with vm.activate():
        sync_message(vm, contract)
        return contract.assess_release(release_id)


def test_create_seal_assess_non_breaking_happy_path():
    vm, contract, _, _ = deploy()
    release_id = create(vm, contract)
    with vm.activate():
        sync_message(vm, contract)
        assert contract.seal_release(release_id) == "RELEASE_SEALED"
    assert assess(vm, contract, release_id, observation()) == "COMPLIANT"
    record = contract.get_release(release_id).split("|")
    assert record[0] == "REVIEWED"
    assert record[5] == "MINOR"
    assert record[8:11] == ["NON_BREAKING", "COMPLIANT", "COMPATIBLE_CHANGE"]


def test_breaking_patch_is_version_violation_but_major_is_compliant():
    breaking = observation("REMOVAL", "INCOMPATIBLE", "INCOMPATIBLE", "COMPATIBLE")
    for old, new, expected in [("1.4.2", "1.4.3", "VERSION_VIOLATION"), ("1.4.2", "2.0.0", "COMPLIANT")]:
        vm, contract, _, _ = deploy()
        release_id = create(vm, contract, old, new)
        with vm.activate():
            sync_message(vm, contract)
            contract.seal_release(release_id)
        assert assess(vm, contract, release_id, breaking) == expected
        assert contract.get_release(release_id).split("|")[8] == "BREAKING"


def test_model_failure_is_retryable_and_does_not_mutate():
    vm, contract, _, _ = deploy()
    release_id = create(vm, contract)
    with vm.activate():
        sync_message(vm, contract)
        contract.seal_release(release_id)
    before = contract.get_release(release_id)
    assert assess(vm, contract, release_id, "not-json") == "ASSESSMENT_RETRYABLE"
    assert contract.get_release(release_id) == before
    assert assess(vm, contract, release_id, observation()) == "COMPLIANT"


def test_malformed_schema_and_oversized_output_are_retryable():
    for bad_output in ['{"verdict":"COMPLIANT"}', "x" * 1000]:
        vm, contract, _, _ = deploy()
        release_id = create(vm, contract)
        with vm.activate():
            sync_message(vm, contract)
            contract.seal_release(release_id)
        before = contract.get_release(release_id)
        assert assess(vm, contract, release_id, bad_output) == "ASSESSMENT_RETRYABLE"
        assert contract.get_release(release_id) == before


def test_prompt_injection_cannot_override_breaking_observation():
    vm, contract, _, _ = deploy()
    fixture = json.loads((ROOT / "fixtures" / "prompt-injection.json").read_text(encoding="utf-8"))
    with vm.activate():
        sync_message(vm, contract)
        release_id = contract.create_release(*[fixture[key] for key in ("package", "old_version", "new_version", "policy", "old_api", "new_api")])
        contract.seal_release(release_id)
    result = assess(vm, contract, release_id, observation("ADDITIVE", "INCOMPATIBLE", "COMPATIBLE", "COMPATIBLE"))
    assert result == "VERSION_VIOLATION"
    assert contract.get_release(release_id).split("|")[8] == "BREAKING"


def test_authority_state_replay_and_terminal_guards():
    vm, contract, publisher, outsider = deploy()
    release_id = create(vm, contract)
    with vm.prank(outsider):
        sync_message(vm, contract)
        assert contract.seal_release(release_id) == "PUBLISHER_ONLY"
        assert contract.cancel_draft(release_id) == "PUBLISHER_ONLY"
    with vm.prank(publisher):
        sync_message(vm, contract)
        assert contract.seal_release(release_id) == "RELEASE_SEALED"
        assert contract.cancel_draft(release_id) == "RELEASE_NOT_CANCELLABLE"
    assert assess(vm, contract, release_id, observation()) == "COMPLIANT"
    with vm.activate():
        sync_message(vm, contract)
        assert contract.assess_release(release_id) == "RELEASE_NOT_ASSESSABLE"
        assert contract.seal_release(release_id) == "RELEASE_NOT_SEALABLE"


def test_cancelled_draft_is_terminal():
    vm, contract, _, _ = deploy()
    release_id = create(vm, contract)
    with vm.activate():
        sync_message(vm, contract)
        assert contract.cancel_draft(release_id) == "RELEASE_CANCELLED"
        assert contract.cancel_draft(release_id) == "RELEASE_NOT_CANCELLABLE"
        assert contract.seal_release(release_id) == "RELEASE_NOT_SEALABLE"
        assert contract.assess_release(release_id) == "RELEASE_NOT_ASSESSABLE"


def test_input_bounds_and_semver_fail_without_creating_state():
    vm, contract, _, _ = deploy()
    with vm.activate():
        sync_message(vm, contract)
        assert contract.create_release("signal-kit", "1.0", "1.1.0", POLICY, OLD, NEW) == "INVALID_VERSION_TRANSITION"
        assert contract.create_release("signal-kit", "1.1.0", "1.0.0", POLICY, OLD, NEW) == "INVALID_VERSION_TRANSITION"
        assert contract.create_release("signal|kit", "1.0.0", "1.1.0", POLICY, OLD, NEW) == "INVALID_PACKAGE"
        assert contract.create_release("signal-kit", "1.0.0", "1.1.0", POLICY, "", NEW) == "INVALID_API_SNAPSHOT"
        assert contract.get_release_count() == 0


def test_snapshot_hash_binding_is_contract_computed_and_immutable():
    import hashlib
    vm, contract, _, _ = deploy()
    release_id = create(vm, contract)
    record = contract.get_release(release_id).split("|")
    assert record[6] == hashlib.sha256(OLD.encode()).hexdigest()
    assert record[7] == hashlib.sha256(NEW.encode()).hexdigest()
    snapshots = json.loads(contract.get_snapshots(release_id))
    assert snapshots == {"policy": POLICY, "old_api": OLD, "new_api": NEW}

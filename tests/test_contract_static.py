import ast
from pathlib import Path
SOURCE=(Path(__file__).resolve().parents[1]/"contracts"/"SemVerSentinel.py").read_text(encoding="utf-8")
def test_locked_contract_shape():
    ast.parse(SOURCE); assert SOURCE.startswith('# v0.2.16\n# { "Depends":'); assert "class SemVerSentinel(gl.Contract):" in SOURCE
    assert "https://registry.npmjs.org/" in SOURCE; assert "hashlib.sha512(tarball_body)" in SOURCE; assert "zlib.decompress(tar_gz, 31)" in SOURCE
def test_publisher_cannot_supply_descriptions_urls_or_digests():
    create=SOURCE.split("def create_release",1)[1].split("@gl.public.write",1)[0]
    assert "package: str, old_version: str, new_version: str, policy: str" in create
    for forbidden in ("old_api","new_api","artifact_url","artifact_sha256"): assert forbidden not in create
def test_registry_metadata_tarball_integrity_and_source_are_critical_path():
    release=SOURCE.split("def _release_source",1)[1].split("def _inspect",1)[0]
    for required in ("metadata.get(\"name\"","metadata.get(\"version\"","dist.get(\"integrity\"","dist.get(\"tarball\"","_tarball_url(package, version)","_extract_tar_member"): assert required in release
def test_validators_repeat_substantive_inspection_and_compare_effect():
    consensus=SOURCE.split("def _consensus",1)[1].split("@gl.public.write",1)[0]
    assert consensus.count("_inspect(package, old_version, new_version, policy)") >= 2
    assert 'bindings = ("old_integrity","new_integrity","old_source_sha256","new_source_sha256")' in consensus
    assert "_derive(leader, bump) == _derive(validator, bump)" in consensus
def test_fail_closed_and_no_custody():
    assess=SOURCE.split("def assess_release",1)[1].split("@gl.public.view",1)[0]
    assert 'outcome["category"]=="UNAVAILABLE"' in assess; assert '"REJECTED"' in assess
    lowered=SOURCE.lower()
    for forbidden in ("payable","transfer(","upgrade"): assert forbidden not in lowered

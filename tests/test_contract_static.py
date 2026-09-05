import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "SemVerSentinel.py").read_text(encoding="utf-8")


def test_locked_header_and_contract_shape():
    ast.parse(SOURCE)
    assert SOURCE.startswith('# v0.2.16\n# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }')
    assert "class SemVerSentinel(gl.Contract):" in SOURCE
    assert "gl.nondet.web.get(url).body" in SOURCE
    assert "hashlib.sha256(body).hexdigest()" in SOURCE


def test_artifact_authority_and_commit_are_bound_before_storage():
    create = SOURCE.split("def create_release", 1)[1].split("@gl.public.write", 1)[0]
    assert "_artifact_identity(artifact_url)" in create
    assert "IMMUTABLE_GITHUB_ARTIFACT_REQUIRED" in create
    assert "identity[0]" in create and "identity[1]" in create


def test_ai_observes_while_contract_derives_verdict():
    classifier = SOURCE.split("def _classify_change", 1)[1].split("def _inspect_artifact", 1)[0]
    assert "Do not return a verdict" in classifier
    assert "VERSION_VIOLATION" not in classifier
    assert "def _derive_analysis" in SOURCE


def test_validator_independently_fetches_and_recomputes_effect():
    consensus = SOURCE.split("def _consensus_observation", 1)[1].split("@gl.public.write", 1)[0]
    assert "mine = _normalize_observation(" in consensus
    assert "_inspect_artifact(url, digest, package, publisher, old_version, new_version, policy)" in consensus
    assert "_derive_analysis(theirs, bump) == _derive_analysis(mine, bump)" in consensus


def test_guard_order_and_fail_closed_state():
    evaluator = SOURCE.split("def assess_release", 1)[1].split("@gl.public.view", 1)[0]
    assert evaluator.index('self.statuses[release_id] != "SEALED"') < evaluator.index("self._consensus_observation")
    assert evaluator.index('outcome["category"] == "UNAVAILABLE"') < evaluator.index('self.statuses[release_id] =')
    assert '"REJECTED"' in evaluator


def test_no_custody_or_upgrade_surface():
    lowered = SOURCE.lower()
    for forbidden in ("payable", "transfer(", "upgrade"):
        assert forbidden not in lowered

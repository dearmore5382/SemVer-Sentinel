import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "SemVerSentinel.py").read_text(encoding="utf-8")


def load_core():
    tree = ast.parse(SOURCE)
    wanted = {
        "MAX_MODEL_OUTPUT_LEN", "_version_parts", "_bump_kind",
        "_unavailable_observation", "_normalize_observation", "_derive_analysis",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in wanted for t in node.targets):
            nodes.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            nodes.append(node)
    namespace = {"typing": __import__("typing")}
    class UserError(Exception):
        pass
    class VM:
        pass
    VM.UserError = UserError
    class GL:
        pass
    GL.vm = VM
    namespace["gl"] = GL
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "core", "exec"), namespace)
    return namespace


CORE = load_core()


def obs(surface="ADDITIVE", request="COMPATIBLE", response="COMPATIBLE", behavior="COMPATIBLE", docs="NO", status="AVAILABLE"):
    return {
        "analysis_status": status,
        "surface_change": surface,
        "request_compatibility": request,
        "response_compatibility": response,
        "behavior_compatibility": behavior,
        "documentation_only": docs,
    }


def test_semver_parser_and_bump_kind_are_bounded():
    bump = CORE["_bump_kind"]
    assert bump("1.2.3", "2.0.0") == "MAJOR"
    assert bump("1.2.3", "1.3.0") == "MINOR"
    assert bump("1.2.3", "1.2.4") == "PATCH"
    for bad_old, bad_new in [("1.2", "1.3.0"), ("1.2.3", "1.2.3"), ("2.0.0", "1.9.9"), ("01.2.3", "1.3.0"), ("1.2.3", "1.2.4-beta")]:
        assert bump(bad_old, bad_new) == "INVALID"


def test_deterministic_precedence_and_compliance_matrix():
    derive = CORE["_derive_analysis"]
    assert derive(obs(), "MINOR") == {"category": "NON_BREAKING", "compliance": "COMPLIANT", "reason": "COMPATIBLE_CHANGE"}
    breaking = obs(surface="REMOVAL", request="INCOMPATIBLE")
    assert derive(breaking, "PATCH")["compliance"] == "VERSION_VIOLATION"
    assert derive(breaking, "MAJOR")["compliance"] == "COMPLIANT"
    assert derive(obs(surface="UNCERTAIN"), "PATCH")["compliance"] == "REVIEW_REQUIRED"
    docs = obs(surface="NONE", request="NONE", response="NONE", behavior="NONE", docs="YES")
    assert derive(docs, "PATCH")["category"] == "DOC_ONLY"


def test_substantive_negative_beats_secondary_uncertainty():
    result = CORE["_derive_analysis"](obs(surface="REMOVAL", response="UNCERTAIN", docs="UNCERTAIN"), "MINOR")
    assert result == {"category": "BREAKING", "compliance": "VERSION_VIOLATION", "reason": "BREAKING_CHANGE_DETECTED"}


def test_cross_field_contradiction_cannot_become_positive():
    contradictory = obs(surface="ADDITIVE", request="COMPATIBLE", docs="YES")
    result = CORE["_derive_analysis"](contradictory, "MINOR")
    assert result == {"category": "UNCERTAIN", "compliance": "REVIEW_REQUIRED", "reason": "SEMANTIC_UNCERTAINTY"}


def test_unavailable_is_retryable_not_a_negative_verdict():
    result = CORE["_derive_analysis"](CORE["_unavailable_observation"](), "PATCH")
    assert result == {"category": "UNAVAILABLE", "compliance": "RETRYABLE", "reason": "ANALYSIS_UNAVAILABLE"}


def test_normalizer_rejects_unknown_schema_and_enum():
    normalize = CORE["_normalize_observation"]
    good = normalize(obs())
    assert good["surface_change"] == "ADDITIVE"
    for bad in [dict(obs(), verdict="COMPLIANT"), dict(obs(), surface_change="SAFE")]:
        try:
            normalize(bad)
            raise AssertionError("invalid observation accepted")
        except Exception:
            pass


def test_fixtures_are_distinct_and_well_formed():
    fixtures = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "fixtures").glob("*.json"))]
    assert len(fixtures) == 4
    assert len({json.dumps(item, sort_keys=True) for item in fixtures}) == 4
    assert all(set(item) == {"package", "old_version", "new_version", "policy", "old_api", "new_api"} for item in fixtures)

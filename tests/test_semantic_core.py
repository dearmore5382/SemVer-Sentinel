import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "SemVerSentinel.py").read_text(encoding="utf-8")


def load_core():
    tree = ast.parse(SOURCE)
    wanted = {"RAW_GITHUB_PREFIX", "_version_parts", "_bump_kind", "_artifact_identity", "_valid_digest", "_base_observation", "_normalize_observation", "_derive_analysis"}
    nodes = []
    for node in tree.body:
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


def obs(surface="ADDITIVE", request="COMPATIBLE", response="COMPATIBLE", behavior="COMPATIBLE", docs="NO", provenance="VERIFIED", status="AVAILABLE", digest="a" * 64):
    return {"actual_digest": digest, "analysis_status": status, "surface_change": surface, "request_compatibility": request, "response_compatibility": response, "behavior_compatibility": behavior, "documentation_only": docs, "provenance_status": provenance}


def test_semver_parser_and_bump_kind_are_bounded():
    bump = CORE["_bump_kind"]
    assert [bump("1.2.3", value) for value in ("2.0.0", "1.3.0", "1.2.4")] == ["MAJOR", "MINOR", "PATCH"]
    for old, new in [("1.2", "1.3.0"), ("1.2.3", "1.2.3"), ("2.0.0", "1.9.9"), ("01.2.3", "1.3.0"), ("1.2.3", "1.2.4-beta")]:
        assert bump(old, new) == "INVALID"


def test_canonical_artifact_identity_requires_full_commit_and_exact_origin():
    parse = CORE["_artifact_identity"]
    commit = "1" * 40
    assert parse(f"https://raw.githubusercontent.com/Owner/Repo/{commit}/release.json") == ("github:owner/repo", commit)
    for bad in [
        "https://raw.githubusercontent.com.evil.test/o/r/" + commit + "/release.json",
        "https://raw.githubusercontent.com/o/r/main/release.json",
        "https://raw.githubusercontent.com/o/r/" + commit + "/release.txt",
        "https://raw.githubusercontent.com/o/r/" + commit + "/release.json?x=1",
        "https://raw.githubusercontent.com/o/r/" + commit + "/../release.json",
    ]:
        assert parse(bad) is None


def test_provenance_is_a_mandatory_positive_gate():
    derive = CORE["_derive_analysis"]
    assert derive(obs(), "MINOR")["compliance"] == "COMPLIANT"
    for status in ("DIGEST_MISMATCH", "MANIFEST_INVALID", "AUTHORITY_MISMATCH"):
        assert derive(obs(provenance=status, status="UNAVAILABLE"), "MAJOR") == {"category": "REJECTED", "compliance": "ARTIFACT_REJECTED", "reason": status}
    assert derive(obs(provenance="UNAVAILABLE", status="UNAVAILABLE", digest=""), "MINOR")["compliance"] == "RETRYABLE"


def test_deterministic_semantic_precedence_is_preserved():
    derive = CORE["_derive_analysis"]
    breaking = obs(surface="REMOVAL", response="UNCERTAIN", docs="UNCERTAIN")
    assert derive(breaking, "PATCH") == {"category": "BREAKING", "compliance": "VERSION_VIOLATION", "reason": "BREAKING_CHANGE_DETECTED"}
    assert derive(breaking, "MAJOR")["compliance"] == "COMPLIANT"
    assert derive(obs(surface="UNCERTAIN"), "MINOR")["compliance"] == "REVIEW_REQUIRED"
    contradictory = obs(surface="ADDITIVE", request="COMPATIBLE", docs="YES")
    assert derive(contradictory, "MINOR")["category"] == "UNCERTAIN"


def test_normalizer_rejects_schema_enum_and_bad_digest():
    normalize = CORE["_normalize_observation"]
    assert normalize(obs())["provenance_status"] == "VERIFIED"
    for bad in [dict(obs(), verdict="COMPLIANT"), dict(obs(), provenance_status="TRUST_ME"), dict(obs(), actual_digest="abc")]:
        try:
            normalize(bad)
            raise AssertionError("invalid observation accepted")
        except Exception:
            pass

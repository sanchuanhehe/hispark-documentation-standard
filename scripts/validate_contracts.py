"""Optional reference checks, not a certification of the whole standard.

No exception bypass is implemented. A production adapter must independently
verify archive receipts, evidence, applicability, approvals and report identity.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def integer(value: object, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(text(v) for v in value)


def load(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError) as error:
        raise ContractError(f"unreadable report/contract {path}: {error}") from error
    require(isinstance(value, dict) and bool(value), "empty or non-object contract")
    return value


def validate_gate(plan: dict, report: dict) -> dict:
    """Validate a complete no-exception gate against an independently owned plan."""
    for item in (plan, report):
        require(type(item.get("schema_version")) is int and item["schema_version"] == 1,
                "unsupported schema version")
        for key in ("commit", "run_id", "scope"):
            require(text(item.get(key)), f"missing {key}")
    for key in ("commit", "run_id", "scope"):
        require(plan[key] == report[key], f"stale or mismatched {key}")
    required = plan.get("required_checks")
    require(strings(required) and len(set(required)) == len(required),
            "required checks must be nonempty and unique")
    require(report.get("complete") is True, "report not complete")
    require(text(report.get("boundary")), "missing verification boundary")
    archive = report.get("archive")
    require(isinstance(archive, dict) and archive.get("uploaded") is True
            and text(archive.get("uri")) and text(archive.get("receipt")),
            "missing upload receipt")
    checks = report.get("checks")
    require(isinstance(checks, list) and bool(checks), "missing checks")
    check_ids = []
    for check in checks:
        require(isinstance(check, dict) and text(check.get("id")), "invalid check")
        check_ids.append(check["id"])
        require(check.get("status") in {"passed", "failed", "blocked", "not_run",
                                       "not_applicable", "cancelled", "skipped", "timeout"},
                "invalid check status")
        if check["id"] in required:
            require(check.get("status") == "passed", f"required check not passed: {check['id']}")
            require(type(check.get("exit_code")) is int and check["exit_code"] == 0,
                    "missing or nonzero real exit code")
            require(strings(check.get("evidence")), "missing required evidence")
    require(len(check_ids) == len(set(check_ids)), "duplicate check ID")
    require(set(required).issubset(check_ids), "missing required check")
    findings = report.get("findings")
    require(isinstance(findings, list), "missing findings array")
    counts = {"known": 0, "new": 0, "resolved": 0}
    by_rule: dict[str, dict[str, int]] = {}
    identities = set()
    for finding in findings:
        require(isinstance(finding, dict), "invalid finding")
        for key in ("id", "rule_id", "path", "location", "message"):
            require(text(finding.get(key)), f"missing finding {key}")
        require(finding["id"] not in identities, "duplicate finding ID")
        identities.add(finding["id"])
        classification = finding.get("classification")
        require(classification in counts, "invalid finding classification")
        counts[classification] += 1
        by_rule.setdefault(finding["rule_id"], dict.fromkeys(counts, 0))[classification] += 1
    summary = report.get("summary")
    require(isinstance(summary, dict), "missing summary")
    declared = summary.get("counts")
    require(isinstance(declared, dict) and all(integer(v) for v in declared.values())
            and declared == counts, "classification counts mismatch")
    declared_rules = summary.get("by_rule")
    require(isinstance(declared_rules, dict)
            and all(isinstance(v, dict) and all(integer(n) for n in v.values())
                    for v in declared_rules.values())
            and declared_rules == by_rule, "rule counts mismatch")
    current = counts["known"] + counts["new"]
    require(integer(summary.get("current")) and summary["current"] == current,
            "current count mismatch")
    require(integer(summary.get("baseline_new")) and summary["baseline_new"] == counts["new"],
            "baseline_new mismatch")
    require(current == 0, "current findings block overall gate (including known)")
    return {"result": "passed", "boundary": "reference report checks only", "counts": counts}


def validate_tutorial(contract: dict) -> dict:
    for key in ("leaf_id", "goal", "criterion", "owner", "approval", "user_test_evidence"):
        require(text(contract.get(key)), f"missing tutorial {key}")
    selections = contract.get("selections")
    require(isinstance(selections, list), "missing selections")
    dimensions = {}
    for selection in selections:
        require(isinstance(selection, dict) and text(selection.get("dimension")),
                "invalid selection")
        require(strings(selection.get("labels")) and strings(selection.get("semantics"))
                and len(selection["labels"]) == len(selection["semantics"])
                and len(set(selection["labels"])) == len(selection["labels"])
                and len(set(selection["semantics"])) == len(selection["semantics"])
                and text(selection.get("sync_group")), "invalid selector labels/semantics")
        signature = (selection["labels"], selection["semantics"], selection["sync_group"])
        dimension = selection["dimension"]
        require(dimension not in dimensions or dimensions[dimension] == signature,
                "repeated selector label/order/semantics/sync drift")
        dimensions[dimension] = signature
    budget, measured = contract.get("budget"), contract.get("measured")
    require(isinstance(budget, dict) and isinstance(measured, dict), "missing numeric budget")
    for field in ("pages", "steps", "prerequisites", "decisions", "optional_branches"):
        require(integer(budget.get(field)) and integer(measured.get(field)),
                f"invalid numeric budget: {field}")
        require(measured[field] <= budget[field], f"budget exceeded: {field}")
    require(budget["optional_branches"] == measured["optional_branches"] == 0,
            "optional pre-success branches prohibited")
    require(measured["decisions"] == len(dimensions), "independent decision count mismatch")
    duration = budget.get("target_minutes")
    require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
            "target duration must be a finite positive number")
    require(text(contract.get("timing_boundary")), "missing timing boundary")
    require(contract.get("includes_required_preparation") is True,
            "required preparation must be counted")
    return {"result": "passed", "boundary": "reference budget checks only",
            "decisions": len(dimensions)}


STAGES = {"source/static", "environment", "configure", "build", "flash", "serial", "Smoke", "HIL"}
STATUSES = {"passed", "failed", "blocked", "not_run", "not_applicable"}


def validate_matrix(matrix: dict) -> dict:
    """Check structure, stage independence and required-stage completion only."""
    for field in ("scenario_id", "page", "facts_revision", "scope", "boundary"):
        require(text(matrix.get(field)), f"missing matrix {field}")
    environment = matrix.get("environment")
    require(isinstance(environment, dict), "missing environment")
    for field in ("os", "runner", "architecture", "sdk", "tools"):
        require(text(environment.get(field)), f"missing environment {field}")
    stages = matrix.get("stages")
    require(isinstance(stages, list) and len(stages) == len(STAGES), "all eight stages required")
    seen, states = set(), {}
    for stage in stages:
        require(isinstance(stage, dict), "invalid stage")
        name, status = stage.get("stage"), stage.get("status")
        require(name in STAGES and name not in seen, "invalid or duplicate stage")
        seen.add(name)
        require(status in STATUSES, "invalid scenario state (not a verification level)")
        require(type(stage.get("required")) is bool, "missing applicability")
        for field in ("criterion", "boundary"):
            require(text(stage.get(field)), f"missing stage {field}")
        if status != "passed":
            require(text(stage.get("reason")), "missing non-pass reason")
        if status in {"blocked", "not_run", "failed"}:
            require(text(stage.get("followup")), "missing gap owner/plan/review")
        if status == "passed":
            for field in ("started_at", "ended_at", "working_directory", "command", "log"):
                require(text(stage.get(field)), f"missing executed evidence {field}")
            require(type(stage.get("exit_code")) is int and stage["exit_code"] == 0,
                    "passed stage lacks successful exit status")
            require(isinstance(stage.get("config_changes"), list), "missing config changes")
            artifacts = stage.get("artifacts")
            require(isinstance(artifacts, list), "missing artifact list")
            if not artifacts:
                require(text(stage.get("artifact_reason")), "no-artifact reason required")
            for artifact in artifacts:
                require(isinstance(artifact, dict) and text(artifact.get("path"))
                        and integer(artifact.get("size_bytes")), "invalid artifact identity")
                sha = artifact.get("sha256")
                require(isinstance(sha, str) and len(sha) == 64
                        and all(c in "0123456789abcdef" for c in sha), "invalid artifact SHA-256")
        require(not stage["required"] or status == "passed", "required stage not passed")
        states[name] = status
    return {"result": "passed", "boundary": "matrix schema/required stages only; not all stages passed",
            "stages": states}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    gate = sub.add_parser("gate")
    gate.add_argument("plan", type=Path)
    gate.add_argument("report", type=Path)
    tutorial = sub.add_parser("tutorial")
    tutorial.add_argument("contract", type=Path)
    matrix = sub.add_parser("matrix")
    matrix.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "gate":
            result = validate_gate(load(args.plan), load(args.report))
        else:
            result = {"tutorial": validate_tutorial, "matrix": validate_matrix}[args.mode](load(args.contract))
    except (ContractError, TypeError, KeyError) as error:
        print(json.dumps({"result": "failed", "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

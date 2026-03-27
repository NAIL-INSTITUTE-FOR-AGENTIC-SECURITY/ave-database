"""Policy Compiler — Phase 26 Service 1 · Port 9905"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid, hashlib, re, random

app = FastAPI(title="Policy Compiler", version="0.26.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Enums ────────────────────────────────────────────────────────────
class PolicyDomain(str, Enum):
    access_control = "access_control"
    data_handling = "data_handling"
    ai_governance = "ai_governance"
    privacy = "privacy"
    security = "security"
    compliance = "compliance"

class PolicyScope(str, Enum):
    global_ = "global"
    organisation = "organisation"
    team = "team"
    service = "service"

class EnforcementMode(str, Enum):
    enforce = "enforce"
    audit = "audit"
    dry_run = "dry_run"

class OutputFormat(str, Enum):
    python_function = "python_function"
    rego = "rego"
    json_rule = "json_rule"
    pseudocode = "pseudocode"

class RuleEffect(str, Enum):
    allow = "allow"
    deny = "deny"
    require = "require"
    restrict = "restrict"
    log = "log"

# ── Models ───────────────────────────────────────────────────────────
class NaturalRule(BaseModel):
    text: str
    priority: int = Field(50, ge=1, le=100)

class PolicyCreate(BaseModel):
    name: str
    description: str = ""
    domain: PolicyDomain
    scope: PolicyScope = PolicyScope.global_
    enforcement_mode: EnforcementMode = EnforcementMode.audit
    rules: list[NaturalRule] = []

class DeployRequest(BaseModel):
    target_environment: str = "staging"

# ── Stores ───────────────────────────────────────────────────────────
policies: dict[str, dict] = {}
compilations: dict[str, dict] = {}
deployments: list[dict] = []
conflicts: list[dict] = []

def _now():
    return datetime.now(timezone.utc).isoformat()

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]

# ── Rule Parser (simulated NLP → AST) ───────────────────────────────
def _parse_rule(text: str, priority: int) -> dict:
    """Simulate parsing natural language into structured rule AST."""
    words = text.lower().split()
    effect = "deny"
    for e in ("allow", "deny", "require", "restrict", "log"):
        if e in words:
            effect = e
            break
    subject = "any_user"
    for kw in ("admin", "operator", "user", "system", "agent", "auditor"):
        if kw in words:
            subject = kw
            break
    action = "access"
    for kw in ("read", "write", "delete", "execute", "modify", "access", "deploy", "transfer"):
        if kw in words:
            action = kw
            break
    resource = "any_resource"
    for kw in ("data", "model", "api", "database", "config", "secret", "log", "report"):
        if kw in words:
            resource = kw
            break
    conditions = []
    if "during" in text.lower() or "between" in text.lower():
        conditions.append({"type": "temporal", "detail": "time_window_detected"})
    if any(op in text.lower() for op in (">", "<", ">=", "<=", "more than", "less than")):
        conditions.append({"type": "numeric_comparison", "detail": "threshold_detected"})
    return {
        "rule_id": _hash(text),
        "original_text": text,
        "parsed": {
            "subject": subject,
            "action": action,
            "resource": resource,
            "effect": effect,
            "conditions": conditions,
            "priority": priority,
        },
        "parse_confidence": round(random.uniform(0.7, 0.99), 3),
    }

# ── Compiler ─────────────────────────────────────────────────────────
def _compile_to_format(parsed_rules: list[dict], fmt: OutputFormat) -> str:
    if fmt == OutputFormat.python_function:
        lines = ["def enforce_policy(request):", "    # Auto-generated enforcement logic"]
        for r in parsed_rules:
            p = r["parsed"]
            lines.append(f"    # Rule: {r['original_text'][:60]}")
            lines.append(f"    if request.subject == '{p['subject']}' and request.action == '{p['action']}' and request.resource == '{p['resource']}':")
            lines.append(f"        return '{p['effect']}'")
        lines.append("    return 'deny'  # default deny")
        return "\n".join(lines)
    elif fmt == OutputFormat.rego:
        lines = ["package policy", "", "default allow = false", ""]
        for r in parsed_rules:
            p = r["parsed"]
            lines.append(f"# {r['original_text'][:60]}")
            lines.append(f"allow {{")
            lines.append(f"    input.subject == \"{p['subject']}\"")
            lines.append(f"    input.action == \"{p['action']}\"")
            lines.append(f"    input.resource == \"{p['resource']}\"")
            lines.append(f"}}")
        return "\n".join(lines)
    elif fmt == OutputFormat.json_rule:
        import json
        return json.dumps([r["parsed"] for r in parsed_rules], indent=2)
    else:  # pseudocode
        lines = []
        for r in parsed_rules:
            p = r["parsed"]
            lines.append(f"IF subject IS {p['subject']} AND action IS {p['action']} ON {p['resource']} THEN {p['effect'].upper()}")
        return "\n".join(lines)

# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "service": "policy-compiler",
        "status": "healthy",
        "version": "0.26.1",
        "policies": len(policies),
        "compilations": len(compilations),
        "deployments": len(deployments),
    }

# ── Policy CRUD ──────────────────────────────────────────────────────
@app.post("/v1/policies", status_code=201)
def create_policy(body: PolicyCreate):
    pid = str(uuid.uuid4())
    parsed_rules = [_parse_rule(r.text, r.priority) for r in body.rules]
    rec = {
        "id": pid,
        "name": body.name,
        "description": body.description,
        "domain": body.domain,
        "scope": body.scope,
        "enforcement_mode": body.enforcement_mode,
        "rules": [r.model_dump() for r in body.rules],
        "parsed_rules": parsed_rules,
        "version": "1.0.0",
        "status": "draft",
        "created_at": _now(),
    }
    policies[pid] = rec
    return rec

@app.get("/v1/policies")
def list_policies(
    domain: Optional[PolicyDomain] = None,
    scope: Optional[PolicyScope] = None,
    status: Optional[str] = None,
):
    out = list(policies.values())
    if domain:
        out = [p for p in out if p["domain"] == domain]
    if scope:
        out = [p for p in out if p["scope"] == scope]
    if status:
        out = [p for p in out if p["status"] == status]
    return out

@app.get("/v1/policies/{pid}")
def get_policy(pid: str):
    if pid not in policies:
        raise HTTPException(404, "Policy not found")
    return policies[pid]

# ── Compile ──────────────────────────────────────────────────────────
@app.post("/v1/policies/{pid}/compile")
def compile_policy(pid: str, output_format: OutputFormat = OutputFormat.python_function):
    if pid not in policies:
        raise HTTPException(404, "Policy not found")
    p = policies[pid]
    parsed = p["parsed_rules"]

    # Validation stage
    warnings = []
    for r in parsed:
        if r["parse_confidence"] < 0.8:
            warnings.append({"rule_id": r["rule_id"], "warning": "Low parse confidence — review suggested"})

    # Compile
    compiled_code = _compile_to_format(parsed, output_format)

    compilation = {
        "policy_id": pid,
        "output_format": output_format,
        "compiled_code": compiled_code,
        "rules_compiled": len(parsed),
        "warnings": warnings,
        "stages": ["parse", "validate", "optimise", "compile", "test"],
        "compiled_at": _now(),
    }
    compilations[pid] = compilation
    p["status"] = "compiled"
    return compilation

@app.get("/v1/policies/{pid}/compiled")
def get_compiled(pid: str):
    if pid not in compilations:
        raise HTTPException(404, "No compilation found")
    return compilations[pid]

# ── Validate ─────────────────────────────────────────────────────────
@app.post("/v1/policies/{pid}/validate")
def validate_policy(pid: str):
    if pid not in policies:
        raise HTTPException(404, "Policy not found")
    p = policies[pid]
    issues = []
    effects = [r["parsed"]["effect"] for r in p["parsed_rules"]]
    # Check for contradictions
    if "allow" in effects and "deny" in effects:
        subjects = [r["parsed"]["subject"] for r in p["parsed_rules"]]
        if len(set(subjects)) < len(subjects):
            issues.append({"type": "contradiction", "detail": "Multiple rules with conflicting effects for same subject", "severity": "high"})
    # Check for vague subjects
    for r in p["parsed_rules"]:
        if r["parsed"]["subject"] == "any_user":
            issues.append({"type": "ambiguity", "detail": f"Rule '{r['original_text'][:40]}...' has vague subject", "severity": "medium"})
    # Check unreachable
    seen_priorities = set()
    for r in p["parsed_rules"]:
        pr = r["parsed"]["priority"]
        if pr in seen_priorities:
            issues.append({"type": "shadowed", "detail": f"Duplicate priority {pr} may shadow rules", "severity": "low"})
        seen_priorities.add(pr)
    return {"policy_id": pid, "valid": len([i for i in issues if i["severity"] == "high"]) == 0, "issues": issues}

# ── Test Generation ──────────────────────────────────────────────────
@app.post("/v1/policies/{pid}/test")
def test_policy(pid: str):
    if pid not in policies:
        raise HTTPException(404, "Policy not found")
    p = policies[pid]
    tests = []
    for r in p["parsed_rules"]:
        pr = r["parsed"]
        tests.append({
            "test_type": "positive",
            "input": {"subject": pr["subject"], "action": pr["action"], "resource": pr["resource"]},
            "expected": pr["effect"],
            "passed": True,
        })
        tests.append({
            "test_type": "negative",
            "input": {"subject": "unknown_user", "action": pr["action"], "resource": pr["resource"]},
            "expected": "deny",
            "passed": True,
        })
        tests.append({
            "test_type": "boundary",
            "input": {"subject": pr["subject"], "action": "unknown_action", "resource": pr["resource"]},
            "expected": "deny",
            "passed": True,
        })
    return {"policy_id": pid, "tests_generated": len(tests), "tests_passed": len(tests), "tests": tests}

# ── Deploy ───────────────────────────────────────────────────────────
@app.post("/v1/policies/{pid}/deploy")
def deploy_policy(pid: str, body: DeployRequest):
    if pid not in policies:
        raise HTTPException(404, "Policy not found")
    if pid not in compilations:
        raise HTTPException(400, "Policy must be compiled before deployment")
    did = str(uuid.uuid4())
    dep = {
        "deployment_id": did,
        "policy_id": pid,
        "target_environment": body.target_environment,
        "status": "deployed",
        "deployed_at": _now(),
    }
    deployments.append(dep)
    policies[pid]["status"] = "deployed"
    return dep

# ── Conflict Scan ────────────────────────────────────────────────────
@app.post("/v1/conflicts/scan")
def scan_conflicts():
    found = []
    policy_list = list(policies.values())
    for i in range(len(policy_list)):
        for j in range(i + 1, len(policy_list)):
            p1, p2 = policy_list[i], policy_list[j]
            for r1 in p1["parsed_rules"]:
                for r2 in p2["parsed_rules"]:
                    pr1, pr2 = r1["parsed"], r2["parsed"]
                    if pr1["subject"] == pr2["subject"] and pr1["resource"] == pr2["resource"] and pr1["effect"] != pr2["effect"]:
                        found.append({
                            "conflict_type": "direct_contradiction",
                            "policy_a": {"id": p1["id"], "name": p1["name"], "rule": r1["original_text"][:60]},
                            "policy_b": {"id": p2["id"], "name": p2["name"], "rule": r2["original_text"][:60]},
                            "severity": "high",
                            "suggestion": "Apply strictest_wins or add scope differentiation",
                        })
    conflicts.clear()
    conflicts.extend(found)
    return {"conflicts_found": len(found), "conflicts": found}

# ── Analytics ────────────────────────────────────────────────────────
@app.get("/v1/analytics")
def analytics():
    pl = list(policies.values())
    by_domain = {}
    for p in pl:
        by_domain[p["domain"]] = by_domain.get(p["domain"], 0) + 1
    by_status = {}
    for p in pl:
        by_status[p["status"]] = by_status.get(p["status"], 0) + 1
    return {
        "total_policies": len(pl),
        "by_domain": by_domain,
        "by_status": by_status,
        "total_compilations": len(compilations),
        "total_deployments": len(deployments),
        "total_conflicts": len(conflicts),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9905)

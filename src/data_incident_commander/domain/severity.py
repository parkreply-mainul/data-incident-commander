"""Versioned deterministic severity rubric."""

from __future__ import annotations

from .models import (
    AppliedRule,
    Severity,
    SeverityAssessment,
    SeverityInputs,
    SeverityRuleSet,
)


def assess_severity(
    inputs: SeverityInputs,
    ruleset: SeverityRuleSet | None = None,
) -> SeverityAssessment:
    rules = ruleset or SeverityRuleSet()
    evaluations = (
        ("confirmed_failure", "Confirmed freshness or quality failure", 2, inputs.confirmed_failure),
        (
            "affected_assets",
            f"At least {rules.affected_asset_threshold} unique assets affected",
            1,
            inputs.affected_asset_count >= rules.affected_asset_threshold,
        ),
        (
            "broad_impact",
            f"At least {rules.broad_impact_threshold} unique assets affected",
            2,
            inputs.affected_asset_count >= rules.broad_impact_threshold,
        ),
        ("critical_assets", "One or more critical assets affected", 2, inputs.critical_asset_count > 0),
        (
            "dashboard_model_impact",
            f"At least {rules.dashboard_model_threshold} dashboards or models affected",
            1,
            inputs.affected_dashboard_model_count >= rules.dashboard_model_threshold,
        ),
        ("missing_ownership", "Target or root-cause ownership is missing", 1, inputs.missing_ownership),
        ("incomplete_evidence", "Required evidence is incomplete", 1, inputs.incomplete_evidence),
        ("truncated_blast_radius", "Blast-radius traversal was truncated", 1, inputs.blast_radius_truncated),
    )
    applied = tuple(
        AppliedRule(rule_id=rule_id, description=description, points=points, applied=condition)
        for rule_id, description, points, condition in evaluations
    )
    score = sum(rule.points for rule in applied if rule.applied)
    if score >= rules.critical_score:
        severity = Severity.CRITICAL
    elif score >= rules.high_score:
        severity = Severity.HIGH
    elif score >= rules.medium_score:
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW
    explanation = tuple(
        f"{rule.rule_id}: +{rule.points} — {rule.description}"
        for rule in applied
        if rule.applied
    ) or ("No severity rules applied.",)
    return SeverityAssessment(
        severity=severity,
        score=score,
        ruleset_version=rules.version,
        applied_rules=applied,
        explanation=explanation,
    )

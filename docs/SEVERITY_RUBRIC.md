# Severity Rubric

## Version 1

Severity is deterministic incident impact and urgency. It is not confidence and
does not use an LLM. `SeverityRuleSet(version="1")` records every evaluated
rule, whether it applied, its points, and the final explanation.

| Rule | Default condition | Points |
| --- | --- | ---: |
| Confirmed failure | Confirmed freshness or quality failure | 2 |
| Affected assets | At least 3 unique affected assets | 1 |
| Broad impact | At least 10 unique affected assets | 2 |
| Critical impact | At least one critical asset affected | 2 |
| Dashboard/model impact | At least 2 dashboards or models affected | 1 |
| Missing ownership | Target or root-cause ownership missing | 1 |
| Incomplete evidence | Required evidence incomplete | 1 |
| Truncated blast radius | Bounded traversal did not reach all discoverable scope | 1 |

Default bands:

| Score | Severity |
| ---: | --- |
| 0–1 | LOW |
| 2–3 | MEDIUM |
| 4–6 | HIGH |
| 7+ | CRITICAL |

Thresholds and bands are validated, configurable values. Version 1 is an
initial project rubric, not a DataHub standard. Runtime evidence determines
inputs; the NYC Taxi outcome is not hard-coded.

Missing ownership, incomplete evidence, and truncation increase operational
risk in severity while separately lowering confidence through the confidence
model. Confidence never changes the calculated severity band.

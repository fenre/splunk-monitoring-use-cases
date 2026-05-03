<!-- AUTO-GENERATED from UC-5.8.15.json — DO NOT EDIT -->

---
id: "5.8.15"
title: "Admin Privilege Changes and Permission Escalation (Meraki)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.8.15 · Admin Privilege Changes and Permission Escalation (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you see when someone’s Meraki rights jump up in a way that should not happen, so small mistakes or misuse do not go unnoticed.*

---

## Description

Detects unauthorized privilege changes and permission escalation attempts.

## Value

Security operations teams detect Meraki administrator privilege escalation events, new admin account creation, and role changes to prevent unauthorized access and maintain least-privilege compliance across the Meraki organization.

## Implementation

Monitor privilege and role change events. Alert on escalations.

## Detailed Implementation

### Prerequisites
- Meraki Dashboard API providing admin role and permission data. Admin changes are logged in the organization change log (`sourcetype=meraki:api:changelog`). Key events: admin account creation, role changes (full org admin, network admin, read-only), permission escalation.
- Key fields: `adminName`/`adminEmail`, `page` (typically "Administrators"), `label` (e.g., "Changed admin privileges"), `oldValue` (previous role), `newValue` (new role).

### Step 1 — Configure data collection
Verify admin privilege change data:
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-30d
| where match(page, "(?i)admin") OR match(label, "(?i)(admin|privilege|permission|role|access)")
| stats count by label
```

### Step 2 — Create the search and alert

**Primary search — Privilege escalation detection:**
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-7d
| where match(page, "(?i)admin") OR match(label, "(?i)(admin|privilege|permission|role|access)")
| eval admin=coalesce(adminName, adminEmail)
| eval is_escalation=case(match(newValue, "(?i)full") AND NOT match(oldValue, "(?i)full"), "ESCALATION", match(label, "(?i)added.*admin"), "NEW_ADMIN", match(label, "(?i)(removed|deleted).*admin"), "REMOVED_ADMIN", 1==1, "CHANGE")
| where is_escalation IN ("ESCALATION", "NEW_ADMIN")
| table _time, admin, networkName, label, oldValue, newValue, is_escalation
| sort -_time
```

#### Understanding this SPL: Privilege escalation in Meraki means an admin gaining "Full organization admin" from a more restricted role. This is the most sensitive change in a Meraki organization — a full org admin can modify any network, change security policies, add/remove other admins, and access all API data. Detecting this is essential for zero-trust and insider threat monitoring.

**Admin account inventory:**
```spl
index=meraki sourcetype="meraki:api:admins" earliest=-24h
| dedup adminEmail
| stats count by orgAccess, tags
| sort orgAccess
```

**Admin role change history:**
```spl
index=meraki (sourcetype="meraki:api:changelog" OR sourcetype="meraki:events") earliest=-90d
| where match(page, "(?i)admin") AND match(label, "(?i)(privilege|role|access|permission)")
| eval admin=coalesce(adminName, adminEmail)
| table _time, admin, label, oldValue, newValue
| sort -_time
```

### Step 3 — Validate
(a) Create a test admin with read-only access, then escalate to full org admin. Verify both events appear in Splunk.
(b) Compare admin roster in Splunk with Meraki Dashboard: Organization > Administrators.
(c) Verify that API-based admin changes (via `PUT /organizations/{orgId}/admins/{adminId}`) are also captured.

### Step 4 — Operationalize
Dashboard ("Meraki Admin Privileges"):
- Row 1 — Single-value tiles: "Full org admins", "Privilege escalations (7d)", "New admins (7d)", "Admin accounts total".
- Row 2 — Privilege escalation events table.
- Row 3 — Admin inventory by access level.
- Row 4 — 90-day admin role change history.

Alerting:
- Critical (new full org admin created): verify authorization.
- High (privilege escalation to full org admin): investigate immediately.
- Warning (any admin role change): audit trail.

### Step 5 — Troubleshooting

- **Admin changes not captured** — The organization change log may not capture SAML/SSO-provisioned admin changes. Verify that SAML admin provisioning events are logged.

- **Multiple "full" admins detected** — Meraki allows multiple full org admins. Review whether this matches your security policy (principle of least privilege recommends minimal full admins).

- **API key admin doesn't appear in admin list** — API keys are associated with admin accounts but may not appear as separate entries. Track API key creation separately.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*privilege*" OR signature="*permission*")
| stats count as priv_change_count by admin_user, old_role, new_role
| where priv_change_count > 0
```

## Visualization

Privilege change timeline; role change audit table; escalation alert dashboard.

## Known False Positives

Role updates during onboarding or support escalations are often correct; require ticket correlation for privilege events.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)

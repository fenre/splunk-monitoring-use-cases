<!-- AUTO-GENERATED from UC-8.2.10.json — DO NOT EDIT -->

---
id: "8.2.10"
title: "Class Loading Issues"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.2.10 · Class Loading Issues

## Description

ClassNotFoundException and NoClassDefFoundError indicate deployment or dependency issues that may cause intermittent failures.

## Value

ClassNotFoundException and NoClassDefFoundError indicate deployment or dependency issues that may cause intermittent failures.

## Implementation

Parse Java stack traces from application logs. Extract exception type and missing class name. Alert on new class loading errors (not seen before). Track frequency to distinguish transient from persistent issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Application log parsing.
• Ensure the following data sources are available: Application error logs (Java stack traces).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse Java stack traces from application logs. Extract exception type and missing class name. Alert on new class loading errors (not seen before). Track frequency to distinguish transient from persistent issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="log4j" log_level=ERROR
| search "ClassNotFoundException" OR "NoClassDefFoundError" OR "ClassCastException"
| rex "(?<exception_class>ClassNotFoundException|NoClassDefFoundError|ClassCastException):\s+(?<missing_class>\S+)"
| stats count by host, exception_class, missing_class
```

Understanding this SPL

**Class Loading Issues** — ClassNotFoundException and NoClassDefFoundError indicate deployment or dependency issues that may cause intermittent failures.

Documented **Data sources**: Application error logs (Java stack traces). **App/TA** (typical add-on context): Application log parsing. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: log4j. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="log4j". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, exception_class, missing_class** so each row reflects one combination of those dimensions.


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (class loading errors with details), Bar chart (errors by type), Timeline (error occurrences).

## SPL

```spl
index=application sourcetype="log4j" log_level=ERROR
| search "ClassNotFoundException" OR "NoClassDefFoundError" OR "ClassCastException"
| rex "(?<exception_class>ClassNotFoundException|NoClassDefFoundError|ClassCastException):\s+(?<missing_class>\S+)"
| stats count by host, exception_class, missing_class
```

## Visualization

Table (class loading errors with details), Bar chart (errors by type), Timeline (error occurrences).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)

# Enrichment contract

Enrichment adds registry ids to a use case. It does not change `title`,
`description`, `value`, SPL, or any other narrative field.

The optional lists are `businessOutcomes`, `businessAreas`, `personas`,
`industries`, `sourcetypes`, and `vendorProducts`. Each item is an id from
the matching file in [`registries/`](../registries/). `enrichment` holds one
assignment per id:

```json
{
  "id": "cisco-ios",
  "source": "authored",
  "confidence": 1,
  "evidence": "`sourcetype=cisco:ios`",
  "model": "explicit-sourcetype",
  "version": "1"
}
```

`source` is `authored` or `inferred`. Authored confidence is 1. Inferred
confidence is greater than 0 and less than 1. `evidence` is a verbatim
substring of the same sidecar, excluding `owner`, the id lists, and
`enrichment` itself. `model` and `version` name the rule that chose the id.

`enrichment.proposedValues[]` is `{ field, value, note }`. Use it when a
wording has no registry id. Leave the list empty rather than inventing an id.

Caps, ranked by relevance: 3 outcomes, 2 areas, 4 personas.

`python -m splunk_uc audit-enrichment --check` fails the build on an unknown
id, a missing assignment, evidence that is not in the sidecar, a persona
whose evidence is the `owner` value, a sourcetype that is not explicit, or
an industry id that is not the registry match for the `industry` field.

## What counts as a sourcetype

A sourcetype id is allowed only when the sidecar has `sourcetype=<token>`,
or `dataSources` quotes a token that contains a colon or sits next to the
word sourcetype, and the assignment's evidence contains that token. The
token is the registry `canonical` value or one of its aliases. A field name
such as `` `Device` ``, a script name such as `` `iostat.sh` ``, and a prose
description of a log are not sourcetypes. A vendor is confirmed by its id,
product name, or alias. The parent company name alone is not a product.

## What counts as a persona

Personas are the ids in [`registries/personas.json`](../registries/personas.json).
`owner` values such as `CISO` and `DPO` are not personas. Evidence that
equals `owner` is rejected even when that word also appears elsewhere.

## What counts as an industry

When `industry` is set, `industries` may contain only the registry id that
matches that string. A different industry mentioned in the title stays out.
When the string matches no registry industry, the list stays empty and
`proposedValues` records the string.

## Accepted examples

These quotes are copied from the sidecars named below.

### UC-5.1.10 — sourcetype, product, outcome

`dataSources` contains `` `sourcetype=cisco:ios` ``. `app` contains
`` `TA-cisco_ios` ``. `value` contains `delayed incident response`.

```json
{
  "sourcetypes": ["cisco-ios"],
  "vendorProducts": ["cisco"],
  "businessOutcomes": ["faster_incident_response"],
  "enrichment": {
    "sourcetypes": [
      {
        "id": "cisco-ios",
        "source": "authored",
        "confidence": 1,
        "evidence": "`sourcetype=cisco:ios`",
        "model": "explicit-sourcetype",
        "version": "1"
      }
    ],
    "vendorProducts": [
      {
        "id": "cisco",
        "source": "authored",
        "confidence": 1,
        "evidence": "`TA-cisco_ios`",
        "model": "explicit-product",
        "version": "1"
      }
    ],
    "businessOutcomes": [
      {
        "id": "faster_incident_response",
        "source": "inferred",
        "confidence": 0.9,
        "evidence": "delayed incident response",
        "model": "phrase-list",
        "version": "1"
      }
    ]
  }
}
```

### UC-4.1.199 — cloud sourcetype, product, area

`dataSources` contains `` sourcetype=`aws:cloudtrail` ``. `app` contains
`Splunk Add-on for AWS`.

```json
{
  "sourcetypes": ["aws-cloudtrail"],
  "vendorProducts": ["aws"],
  "businessAreas": ["cloud_operations"],
  "enrichment": {
    "sourcetypes": [
      {
        "id": "aws-cloudtrail",
        "source": "authored",
        "confidence": 1,
        "evidence": "sourcetype=`aws:cloudtrail`",
        "model": "explicit-sourcetype",
        "version": "1"
      }
    ],
    "vendorProducts": [
      {
        "id": "aws",
        "source": "authored",
        "confidence": 1,
        "evidence": "Splunk Add-on for AWS",
        "model": "explicit-product",
        "version": "1"
      }
    ],
    "businessAreas": [
      {
        "id": "cloud_operations",
        "source": "inferred",
        "confidence": 0.8,
        "evidence": "aws:cloudtrail",
        "model": "phrase-list",
        "version": "1"
      }
    ]
  }
}
```

### UC-10.12.42 — Windows sourcetype and outcome

`dataSources` contains `` `sourcetype="WinEventLog:Security"` ``. `value`
contains `shorten triage`.

```json
{
  "sourcetypes": ["wineventlog-security"],
  "businessOutcomes": ["faster_incident_response"],
  "enrichment": {
    "sourcetypes": [
      {
        "id": "wineventlog-security",
        "source": "authored",
        "confidence": 1,
        "evidence": "sourcetype=\"WinEventLog:Security\"",
        "model": "explicit-sourcetype",
        "version": "1"
      }
    ],
    "businessOutcomes": [
      {
        "id": "faster_incident_response",
        "source": "inferred",
        "confidence": 0.7,
        "evidence": "shorten triage",
        "model": "phrase-list",
        "version": "1"
      }
    ]
  }
}
```

### UC-21.14.20 — industry taken from the industry field

`industry` is `Contact Center and CX Operations`. `dataSources` contains
`` `sourcetype=cc:event` ``. The title also says Healthcare. That word is
not the industry id.

```json
{
  "industries": ["contact-center-and-cx-operations"],
  "sourcetypes": ["cc-event"],
  "enrichment": {
    "industries": [
      {
        "id": "contact-center-and-cx-operations",
        "source": "authored",
        "confidence": 1,
        "evidence": "Contact Center and CX Operations",
        "model": "industry-field",
        "version": "1"
      }
    ],
    "sourcetypes": [
      {
        "id": "cc-event",
        "source": "authored",
        "confidence": 1,
        "evidence": "`sourcetype=cc:event`",
        "model": "explicit-sourcetype",
        "version": "1"
      }
    ]
  }
}
```

### UC-1.1.10 — persona, sourcetype, and an empty outcome

`dataSources` contains `sourcetype=linux:cron_job:completion`. `value`
contains `service owners`. No registry outcome phrase is in the sidecar, so
outcomes stay empty and the wording is proposed.

```json
{
  "sourcetypes": ["linux-cron-job-completion"],
  "personas": ["service_owner"],
  "businessOutcomes": [],
  "enrichment": {
    "sourcetypes": [
      {
        "id": "linux-cron-job-completion",
        "source": "authored",
        "confidence": 1,
        "evidence": "sourcetype=linux:cron_job:completion",
        "model": "explicit-sourcetype",
        "version": "1"
      }
    ],
    "personas": [
      {
        "id": "service_owner",
        "source": "inferred",
        "confidence": 0.8,
        "evidence": "service owners",
        "model": "phrase-list",
        "version": "1"
      }
    ],
    "businessOutcomes": [],
    "proposedValues": [
      {
        "field": "businessOutcomes",
        "value": "failed scheduled jobs",
        "note": "The sidecar describes non-zero cron exits. No outcome phrase from the registry appears in the text."
      }
    ]
  }
}
```

## Rejected examples

### UC-21.14.20 — industry guessed from the title

`healthcare` is a registry id, and the title contains `Healthcare`. The
`industry` field is Contact Center and CX Operations, so `healthcare` is a
guess. The audit reports `does not match the industry field`.

### UC-22.35.1 — owner copied into personas

`owner` is `CISO`. An `auditor` assignment whose evidence is `CISO` is
rejected with `owner copied into personas`. `CISO` is not a persona id.

### UC-9.1.1 — prose is not a sourcetype

`dataSources` says `Windows Security Event Log (Event ID 4625 — failed logon)`.
That sentence is in the sidecar, and the SPL does name
`WinEventLog:Security`, but the evidence does not. The audit reports
`evidence is not an explicit sourcetype`.

### UC-14.3.31 — unknown area id

`plant_safety` is not in [`registries/business-areas.json`](../registries/business-areas.json).
The equipment list contains `scada`, which is not a reason to invent an area
id. The audit reports `unknown id plant_safety`. The registry area for this
wording is `ot_and_safety`, and only that id may be used, with `scada` as
the evidence.

### UC-22.1.21 — evidence that was not written in the sidecar

`prove_compliance` is a real outcome id. Evidence written as
`encryption controls are healthy` does not appear in UC-22.1.21. The audit
reports `evidence does not appear in the use case`. An assignment that omits
`evidence` fails the same gate with `missing evidence`.

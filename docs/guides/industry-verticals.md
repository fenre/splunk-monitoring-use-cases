---
title: Industry Verticals (Energy & Utilities, Manufacturing, Healthcare, Transportation, Oil & Gas, Retail, Aviation, Telecommunications, Water, Insurance) Integration Guide
type: integration-guide
product: Industry-Specific Splunk Use Cases — Energy & Utilities (electric grid, smart grid, generation, distribution), Manufacturing & Process Industry (discrete + process manufacturing, OEE, CMMS), Healthcare & Life Sciences (HL7 / FHIR, EHR, medical devices, pharmacy), Transportation & Logistics (fleet, shipment, warehouse), Oil, Gas & Mining (upstream, midstream, downstream, refinery, pipeline), Retail & E-Commerce (POS, e-commerce, supply chain, loyalty), Aviation & Airport Operations (ATC, baggage, passenger flow, ramp), Telecommunications (RAN/Core, MNO/MVNO, OSS/BSS, charging), Water & Wastewater Utilities (SCADA, distribution, treatment), Insurance & Claims Processing (policy admin, claims, underwriting, fraud)
product_aliases: [Energy and Utilities, electric grid, smart grid, AMI, advanced metering infrastructure, smart meter, NERC CIP, ISO/RTO, transmission, distribution, generation, Manufacturing, OEE, overall equipment effectiveness, MES, manufacturing execution system, ERP, SAP, CMMS, Healthcare, healthcare and life sciences, HL7, FHIR, EHR, electronic health record, EMR, electronic medical record, Epic, Cerner, Meditech, medical device, IoMT, internet of medical things, pharmacy, transportation and logistics, TMS, transportation management system, WMS, warehouse management system, fleet, telematics, Oil and Gas, upstream, midstream, downstream, refinery, pipeline, drilling, well, retail, e-commerce, POS, point of sale, omnichannel, loyalty, aviation, airport operations, ATC, air traffic control, baggage handling, passenger flow, BHS, telco, telecommunications, MNO, mobile network operator, MVNO, RAN, radio access network, 5G, OSS, BSS, charging, water and wastewater, water utility, treatment, insurance, claims processing, policy administration, underwriting, fraud, ICS, OT, SCADA]
ta_name: Splunk OT Security Add-on, Splunk Industrial Asset Intelligence (IAI), Splunk for Healthcare HL7, custom HL7/FHIR HEC bridges, vendor-specific TAs (Splunk_TA_aws for telco/retail), Splunk OT Intelligence
splunkbase_urls:
  - https://splunkbase.splunk.com/app/5151
  - https://splunkbase.splunk.com/app/4942
  - https://splunkbase.splunk.com/app/4945
  - https://splunkbase.splunk.com/app/5601
  - https://splunkbase.splunk.com/app/3088
indexes:
  - vertical
  - energy
  - utilities
  - smartgrid
  - mfg
  - oee
  - cmms
  - healthcare
  - hl7
  - fhir
  - ehr
  - mediot
  - logistics
  - fleet
  - tms
  - wms
  - oilgas
  - upstream
  - midstream
  - downstream
  - retail
  - pos
  - ecom
  - aviation
  - airport
  - telco
  - ran
  - core
  - oss_bss
  - water
  - insurance
  - claims
sourcetypes:
  - scada:alarm
  - scada:event
  - scada:hmi
  - scada:tag
  - smartgrid:meter
  - smartgrid:event
  - opcua:metrics
  - mes:event
  - mes:job
  - cmms:workorder
  - oee:metric
  - sap:idoc
  - sap:cdr
  - hl7:message
  - hl7:adt
  - hl7:orm
  - hl7:oru
  - hl7:msh
  - fhir:resource
  - epic:audit
  - cerner:audit
  - mediot:device
  - tms:event
  - wms:event
  - fleet:telematics
  - airport:bhs
  - airport:flight
  - airport:passenger
  - atc:event
  - retail:pos
  - retail:loyalty
  - retail:ecommerce
  - telco:cdr
  - telco:edr
  - telco:ipdr
  - telco:5g:nrf
  - telco:5g:smf
  - telco:5g:upf
  - telco:5g:amf
  - telco:5g:ausf
  - water:scada
  - water:treatment
  - water:meter
  - insurance:claim
  - insurance:policy
  - insurance:underwriting
  - oil:wellhead
  - oil:pipeline:scada
  - oil:refinery:dcs
ta_versions: "Splunk OT Security Add-on 5.x; Splunk_TA_aws 7.x; Splunk Add-on for Microsoft Cloud Services 5.x; Splunk_TA_google-cloudplatform 4.x; vendor-specific TAs vary"
splunk_versions: "9.0, 9.1, 9.2, 9.3, 9.4 (current), 10.0+; Splunk Cloud (Victoria/Classic) supported"
cross_products: [Splunk Connect for Syslog (SC4S), Splunk Enterprise Security, Splunk SOAR, Splunk ITSI, Splunk Industrial Asset Intelligence (IAI), IoT/OT (cat 14), DC Physical (cat 15), Compute (cat 19)]
compliance_frameworks: [NERC CIP (electric utilities), TSA Pipeline (pipeline operators), HIPAA (healthcare), HITECH, FDA 21 CFR Part 11/820 (medical devices, pharma), GxP (pharma), PCI-DSS (retail), GDPR / CCPA (multi-vertical), CISA Sector-Specific Plans, SOX (financial reporting), Solvency II (insurance EU), MAS / FFIEC (insurance APAC/US), ISA-95 (manufacturing), MITRE ATT&CK for ICS, IEC 62443 (industrial)]
use_case_subcategory: "21.x"
use_case_count: 146
maturity_tiers: {crawl: 35, walk: 80, run: 31}
last_updated: 2026-05-09
---

# Industry Verticals Integration Guide

> The definitive guide to industry-specific Splunk integration. **146
> use cases** across ten major verticals: Energy & Utilities (electric
> grid, generation, transmission, distribution, smart grid AMI),
> Manufacturing & Process Industry (discrete + process, OEE, MES, CMMS,
> SAP), Healthcare & Life Sciences (HL7 / FHIR / EHR / Epic / Cerner /
> medical IoT / pharmacy), Transportation & Logistics (TMS, WMS, fleet
> telematics), Oil, Gas & Mining (upstream / midstream / downstream,
> refinery DCS, pipeline SCADA), Retail & E-Commerce (POS, e-commerce,
> omnichannel, loyalty), Aviation & Airport Operations (ATC, baggage
> handling BHS, passenger flow, ramp ops), Telecommunications (5G core /
> RAN / OSS/BSS / charging / IPDR), Water & Wastewater Utilities
> (SCADA, treatment, distribution metering), and Insurance & Claims
> Processing (policy admin, claims, underwriting, fraud). Sector-specific
> KPIs, regulatory compliance (NERC CIP, HIPAA, FDA 21 CFR, TSA
> Pipeline), business-process observability, and the playbooks that
> turn Splunk into the system of insight for each industry.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Overview](#overview)
- [Architecture and Data Flow](#architecture)
- [Prerequisites](#prerequisites)
- [Energy and Utilities](#energy)
- [Manufacturing and Process Industry](#manufacturing)
- [Healthcare and Life Sciences](#healthcare)
- [Transportation and Logistics](#transportation)
- [Oil, Gas, and Mining](#oilgas)
- [Retail and E-Commerce](#retail)
- [Aviation and Airport Operations](#aviation)
- [Telecommunications Operations](#telco)
- [Water and Wastewater Utilities](#water)
- [Insurance and Claims Processing](#insurance)
- [Cross-Vertical Foundations](#cross-vertical)
- [Field Dictionary](#field-dictionary)
- [Sample Events](#sample-events)
- [Splunk-Side Configuration](#splunk-config)
- [Cross-Product Correlation](#cross-product)
- [Compliance Mapping by Vertical](#compliance)
- [Capacity Planning and Sizing](#sizing)
- [Recommended Dashboard Layouts (per Vertical)](#dashboards)
- [ITSI Service Modeling](#itsi)
- [SOAR Playbook Examples](#soar)
- [Multi-Region Strategy](#multi-region)
- [Security Hardening](#security-hardening)
- [Crawl / Walk / Run Roadmap](#roadmap)
- [Validation Checklist](#validation-checklist)
- [Known Limitations and Gaps](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Glossary](#glossary)
- [References](#references)
- [Contribution and Feedback](#contribution)

---

<a id="quick-start"></a>
## Quick Start — Industry-Specific Onboarding

Pick your vertical and start with the highest-value UC:

| Vertical | First UC |
|----------|---------|
| **Energy** | UC-21.1.1 (SCADA Alarm Rate / Flooding) |
| **Manufacturing** | UC-21.2.1 (OEE Trending) |
| **Healthcare** | UC-21.3.1 (HL7 Message Health) |
| **Transportation** | UC-21.4.1 (Fleet Telematics) |
| **Oil & Gas** | UC-21.5.1 (Wellhead SCADA) |
| **Retail** | UC-21.6.1 (POS Transaction Health) |
| **Aviation** | UC-21.7.1 (BHS Throughput) |
| **Telco** | UC-21.8.1 (5G Core SBI Health) |
| **Water** | UC-21.9.1 (Treatment SCADA) |
| **Insurance** | UC-21.10.1 (Claims Cycle Time) |

---

<a id="overview"></a>
## Overview

### Why industry-vertical integration matters

Industry verticals share a pattern:
- **Heavy regulatory environment** (HIPAA, NERC CIP, PCI-DSS, FDA, TSA, etc.)
- **Industry-specific protocols** (HL7, FHIR, ISA-95, NETCONF, CDR, Modbus, OPC)
- **Business KPIs alongside IT KPIs** (OEE, MTTR, claim cycle time, RPO/RTO)
- **Cross-domain correlation** (SCADA → safety → financial impact)
- **Specialized terminology** that must be respected

### What good looks like

| Dimension | Without integration | With full integration |
|-----------|---------------------|-----------------------|
| Industry KPIs | Per-system reports | Unified Splunk dashboards |
| Regulatory evidence | Annual scramble | Continuous attestation |
| Safety event correlation | Manual review | Automated cross-system |
| Business process visibility | Silos | End-to-end via Splunk |

---

<a id="architecture"></a>
## Architecture and Data Flow

```mermaid
graph TB
    subgraph Vertical["Per-Vertical Sources"]
        SCADA["SCADA / DCS / HMI"]
        EHR["EHR / HL7 / FHIR"]
        POS["POS / E-commerce"]
        Telco["Telco CDR / EDR / 5G NRF"]
        Fleet["Fleet / TMS / WMS"]
        Claims["Claims / Policy"]
    end

    subgraph CrossVertical["Cross-Vertical Splunk Stack"]
        IDX["Indexer Tier"]
        SH["Search Head + ES + ITSI + IAI"]
        SOAR["Splunk SOAR"]
    end

    SCADA --> IDX
    EHR --> IDX
    POS --> IDX
    Telco --> IDX
    Fleet --> IDX
    Claims --> IDX

    IDX --> SH
    SH --> SOAR
```

---

<a id="prerequisites"></a>
## Prerequisites

| Item | Detail |
|------|--------|
| **Splunk Enterprise / Cloud** | 9.0+ |
| **Splunk ITSI** | For service-health KPIs (most verticals benefit) |
| **Splunk OT Security Add-on** | For OT-heavy verticals (Energy, Manufacturing, Oil & Gas, Water) |
| **Splunk IAI** | Industrial Asset Intelligence for advanced asset analytics |
| **Industry-specific TAs** | Per-vertical (HL7 parsers, telco TAs, etc.) |

---

<a id="energy"></a>
## Energy and Utilities

15 use cases. Electric grid, smart grid AMI, generation, transmission, distribution.

### Data sources

| Source | Sourcetype | Notes |
|--------|-----------|-------|
| SCADA alarms | `scada:alarm` | Substation, line operations |
| SCADA events | `scada:event` | State changes, switching |
| SCADA HMI | `scada:hmi` | Operator actions |
| Smart meter (AMI) | `smartgrid:meter` | Load, demand, anomaly |
| Generation telemetry | `opcua:metrics` | Plant DCS |
| OMS (Outage Mgmt) | `oms:event` | Customer outages |
| DERMS (Distributed Energy) | `derms:event` | Solar, wind, storage |

### SPL — SCADA alarm flooding (UC-21.1.1)

```spl
index=scada sourcetype="scada:alarm" earliest=-1h
| bin _time span=5m
| stats count as alarm_count, dc(alarm_id) as distinct_alarms by substation_id, _time
| eventstats avg(alarm_count) as baseline by substation_id
| eval z_score=(alarm_count-baseline)/baseline
| where alarm_count > 50 OR z_score > 3
```

### SPL — AMI revenue protection

```spl
index=energy sourcetype="smartgrid:meter" earliest=-7d
| stats avg(consumption_kwh) as avg_kwh, dc(timestamp) as readings by meter_id
| where avg_kwh < 0.1 AND readings > 100
| join meter_id [search index=energy sourcetype="cmms:workorder" service_type="active" | stats values(account_status) as status by meter_id]
| where status="active"
```

### Compliance: NERC CIP

CIP-007, CIP-008, CIP-005, CIP-010 — see [IoT/OT Guide](iot-ot.md) for full mapping.

---

<a id="manufacturing"></a>
## Manufacturing and Process Industry

18 use cases. Discrete + process manufacturing, OEE, MES, CMMS.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| MES (Manufacturing Execution) | `mes:event`, `mes:job` |
| CMMS (Maintenance) | `cmms:workorder` |
| OEE (Overall Equipment Effectiveness) | `oee:metric` |
| ERP (SAP, Oracle EBS) | `sap:idoc`, `sap:cdr` |
| ICS / SCADA | (see IoT/OT Guide) |

### SPL — OEE calculation (UC-21.2.1)

```spl
index=mfg sourcetype="oee:metric" earliest=-1d
| stats sum(planned_runtime_min) as planned, sum(actual_runtime_min) as actual, sum(units_produced) as units, sum(units_planned) as planned_units, sum(good_units) as good by line_id
| eval availability=actual/planned*100
| eval performance=units/planned_units*100
| eval quality=good/units*100
| eval oee=round(availability*performance*quality/10000,1)
| sort oee
```

### SPL — Production-impact downtime root cause

```spl
(index=mfg sourcetype="mes:event" event_type="line_stop" earliest=-1d)
| stats count, sum(duration_min) as total_downtime, values(reason_code) as reasons by line_id
| sort -total_downtime
```

---

<a id="healthcare"></a>
## Healthcare and Life Sciences

27 use cases. HL7 / FHIR / EHR / Epic / Cerner / medical IoT / pharmacy.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| HL7 v2 messages | `hl7:message`, `hl7:adt`, `hl7:orm`, `hl7:oru`, `hl7:msh` |
| FHIR resources | `fhir:resource` |
| Epic audit | `epic:audit` |
| Cerner audit | `cerner:audit` |
| Medical IoT (IoMT) | `mediot:device` |
| Pharmacy / dispensing | `pharmacy:event` |

### SPL — HL7 message integrity (UC-21.3.1)

```spl
index=healthcare sourcetype="hl7:message" earliest=-1h
| stats count by message_type, success_flag
| where success_flag="false"
| sort -count
```

### SPL — EHR PHI access audit

```spl
index=healthcare sourcetype="epic:audit" event_type="patient_chart_view" earliest=-1d
| stats dc(patient_mrn) as unique_patients, count by user_id
| where unique_patients > 50
| sort -unique_patients
```

### SPL — Medication dispensing anomaly (Diversion detection)

```spl
index=healthcare sourcetype="pharmacy:event" event_type="dispense" controlled_substance="true" earliest=-7d
| stats count, sum(quantity) as total_qty by user_id, drug_name
| eventstats avg(count) as avg_dispensed, stdev(count) as std_dispensed by drug_name
| eval z_score=if(std_dispensed>0, (count-avg_dispensed)/std_dispensed, 0)
| where z_score > 3
```

### Compliance

- HIPAA §164.312 (technical safeguards)
- HITECH (audit trail)
- FDA 21 CFR Part 11 (electronic records, e-signatures)
- 42 CFR Part 2 (substance use)

---

<a id="transportation"></a>
## Transportation and Logistics

12 use cases. TMS, WMS, fleet telematics.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| TMS (Transportation Mgmt) | `tms:event` |
| WMS (Warehouse Mgmt) | `wms:event` |
| Fleet telematics | `fleet:telematics` |
| RFID / barcode | `rfid:scan`, `barcode:scan` |

### SPL — Shipment SLA breach prediction (UC-21.4.1)

```spl
index=logistics sourcetype="tms:event" earliest=-1d
| stats latest(status) as status, latest(eta) as eta, earliest(_time) as start_time by shipment_id
| where status NOT IN ("delivered","cancelled")
| eval hours_remaining=(strptime(eta,"%Y-%m-%dT%H:%M:%SZ")-now())/3600
| where hours_remaining < 4
```

### SPL — Fleet harsh-driving detection

```spl
index=logistics sourcetype="fleet:telematics" earliest=-1d
| stats count(eval(harsh_braking="yes")) as braking, count(eval(harsh_acceleration="yes")) as accel, count(eval(speeding="yes")) as speeding by vehicle_id, driver_id
| eval risk_score=braking + accel + speeding
| where risk_score > 10
| sort -risk_score
```

---

<a id="oilgas"></a>
## Oil, Gas, and Mining

12 use cases. Upstream / midstream / downstream.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| Wellhead SCADA | `oil:wellhead` |
| Pipeline SCADA | `oil:pipeline:scada` |
| Refinery DCS | `oil:refinery:dcs` |
| Drilling rigs | `oil:drilling:event` |
| Mining ICS | `mining:scada` |

### SPL — Pipeline pressure anomaly (UC-21.5.1)

```spl
index=oilgas sourcetype="oil:pipeline:scada" metric_name="pressure_psi" earliest=-1h
| stats latest(metric_value) as current, avg(metric_value) as baseline, stdev(metric_value) as std by pipeline_id, segment_id
| eval z_score=if(std>0, (current-baseline)/std, 0)
| where abs(z_score) > 3
| eval severity=case(abs(z_score)>5,"critical",abs(z_score)>4,"high",1=1,"medium")
```

### SPL — Wellhead production drop

```spl
index=oilgas sourcetype="oil:wellhead" metric_name="production_bbl_day" earliest=-7d
| stats latest(metric_value) as current_bbl, avg(metric_value) as baseline_bbl by well_id
| eval drop_pct=round((baseline_bbl-current_bbl)/baseline_bbl*100,1)
| where drop_pct > 20
| sort -drop_pct
```

### Compliance

- TSA Pipeline Security Directives
- API RP 1164 (Pipeline SCADA Security)
- NERC CIP (if interconnected)
- BSEE (Bureau of Safety and Environmental Enforcement)

---

<a id="retail"></a>
## Retail and E-Commerce

14 use cases. POS, e-commerce, omnichannel, loyalty.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| POS terminal | `retail:pos` |
| E-commerce platform | `retail:ecommerce` |
| Loyalty | `retail:loyalty` |
| Inventory mgmt | `retail:inventory` |
| Order mgmt | `retail:oms` |

### SPL — POS transaction health (UC-21.6.1)

```spl
index=retail sourcetype="retail:pos" earliest=-1h
| stats count(eval(status="success")) as success, count(eval(status="failure")) as failure, count as total by store_id
| eval failure_pct=round(failure/total*100,2)
| where failure_pct > 5
```

### SPL — E-commerce checkout abandonment

```spl
index=retail sourcetype="retail:ecommerce" earliest=-1d
| stats count(eval(event="cart_create")) as cart_created, count(eval(event="checkout_complete")) as completed by hour
| eval abandonment_rate=round((cart_created-completed)/cart_created*100,1)
| timechart span=1h avg(abandonment_rate)
```

### Compliance

- PCI-DSS 4.0 (POS-side full coverage)
- GDPR / CCPA (loyalty data)
- State data privacy laws (US)

---

<a id="aviation"></a>
## Aviation and Airport Operations

10 use cases. ATC, baggage handling, passenger flow, ramp ops.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| BHS (Baggage) | `airport:bhs` |
| Flight info | `airport:flight` |
| Passenger flow | `airport:passenger` |
| ATC events | `atc:event` |
| Ramp ops | `airport:ramp` |

### SPL — BHS throughput (UC-21.7.1)

```spl
index=aviation sourcetype="airport:bhs" earliest=-1h
| stats count(eval(status="processed")) as processed, count(eval(status="reject")) as reject, count as total by terminal, conveyor
| eval reject_rate=round(reject/total*100,1)
| where reject_rate > 2
```

### SPL — Flight on-time performance

```spl
index=aviation sourcetype="airport:flight" event="departure" earliest=-1d
| eval delay_min=actual_minus_scheduled
| eval on_time=if(delay_min<=15,1,0)
| stats avg(on_time)*100 as otp_pct, avg(delay_min) as avg_delay by carrier
| sort otp_pct
```

---

<a id="telco"></a>
## Telecommunications Operations

20 use cases. 5G core, RAN, OSS/BSS, charging.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| Voice CDR | `telco:cdr` |
| Data EDR | `telco:edr` |
| IPDR | `telco:ipdr` |
| 5G NRF | `telco:5g:nrf` |
| 5G SMF | `telco:5g:smf` |
| 5G UPF | `telco:5g:upf` |
| 5G AMF | `telco:5g:amf` |
| 5G AUSF | `telco:5g:ausf` |
| OSS | `telco:oss` |
| BSS / Charging | `telco:bss:charging` |

### SPL — 5G Core SBI health (UC-21.8.1)

```spl
index=telco sourcetype="telco:5g:nrf" earliest=-15m
| stats count, count(eval(http_status>=400)) as errors by nf_type, target_nf
| eval error_rate=round(errors/count*100,2)
| where error_rate > 5
```

### SPL — Voice CDR fraud detection

```spl
index=telco sourcetype="telco:cdr" call_type="voice" earliest=-1h
| stats count, sum(duration_sec) as total_dur by called_number, calling_number
| where (called_number LIKE "+1900*" OR called_number LIKE "+1976*") AND count > 10
```

---

<a id="water"></a>
## Water and Wastewater Utilities

8 use cases. SCADA, treatment, distribution metering.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| Treatment plant SCADA | `water:treatment` |
| Distribution SCADA | `water:scada` |
| Meter telemetry | `water:meter` |

### SPL — Treatment plant chemistry deviation (UC-21.9.1)

```spl
index=water sourcetype="water:treatment" metric_name IN ("ph","chlorine_ppm","turbidity_ntu") earliest=-1h
| stats latest(metric_value) as current, avg(metric_value) as baseline, stdev(metric_value) as std by metric_name, plant_id
| eval z_score=if(std>0, (current-baseline)/std, 0)
| where abs(z_score) > 3
```

### Compliance

- EPA Safe Drinking Water Act
- AWIA (America's Water Infrastructure Act)
- WaterISAC threat sharing

---

<a id="insurance"></a>
## Insurance and Claims Processing

10 use cases. Policy admin, claims, underwriting, fraud.

### Data sources

| Source | Sourcetype |
|--------|-----------|
| Claims processing | `insurance:claim` |
| Policy admin | `insurance:policy` |
| Underwriting | `insurance:underwriting` |

### SPL — Claims cycle time (UC-21.10.1)

```spl
index=insurance sourcetype="insurance:claim" status="closed" earliest=-30d
| eval cycle_time_days=(strptime(closed_at,"%Y-%m-%dT%H:%M:%SZ")-strptime(filed_at,"%Y-%m-%dT%H:%M:%SZ"))/86400
| stats avg(cycle_time_days) as avg_days, perc95(cycle_time_days) as p95_days by claim_type
```

### SPL — Claims fraud detection

```spl
index=insurance sourcetype="insurance:claim" earliest=-90d
| stats count by claimant_id
| where count > 5
| join claimant_id [search index=insurance sourcetype="insurance:claim" earliest=-90d
    | stats sum(claim_amount) as total_claimed by claimant_id]
| where total_claimed > 100000
```

### Compliance

- Solvency II (EU insurance)
- NAIC Model Regulations (US)
- GDPR / CCPA (PII in claims)
- SOX (financial reporting)

---

<a id="cross-vertical"></a>
## Cross-Vertical Foundations

All verticals benefit from these common building blocks already covered in dedicated guides:
- IT infrastructure: [Linux Servers Guide](linux-servers.md), [Windows Servers Guide](windows-servers.md)
- Cloud: [AWS](aws-cloud.md), [Azure](azure-cloud.md), [GCP](gcp-cloud.md)
- Networking: [Cisco Catalyst](catalyst-center.md), [Firewalls](firewalls.md)
- Security: [SIEM & SOAR](siem-soar.md), [EDR](edr.md), [VM](vulnerability-management.md)
- ITSM: [Service Management & ITSM](service-management-itsm.md)
- Data: [Database](database-monitoring.md), [Cloud DBs](nosql-cloud-databases.md)

---

<a id="field-dictionary"></a>
## Field Dictionary

| Field | Across verticals |
|-------|-----------------|
| `industry_kpi` | OEE, claim_cycle, BHS_throughput, OTP, etc. |
| `business_unit` | Plant, store, hospital, well, terminal, etc. |
| `location_id` | Site / location identifier |
| `severity` | Per-vertical severity scheme |
| `regulation_tag` | NERC CIP, HIPAA, PCI, FDA, TSA |

---

<a id="sample-events"></a>
## Sample Events

(See per-vertical sections.)

---

<a id="splunk-config"></a>
## Splunk-Side Configuration

### Index strategy (per vertical)

```ini
[energy]
homePath = $SPLUNK_DB/energy/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 94608000   # 3 years NERC CIP

[mfg]
homePath = $SPLUNK_DB/mfg/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 31536000

[healthcare]
homePath = $SPLUNK_DB/healthcare/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 220752000  # 7 years HIPAA

[retail]
homePath = $SPLUNK_DB/retail/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 31536000   # 1 year (PCI default)

[telco]
homePath = $SPLUNK_DB/telco/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 94608000   # 3 years CDR

[insurance]
homePath = $SPLUNK_DB/insurance/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 220752000  # 7 years SOX

[oilgas]
homePath = $SPLUNK_DB/oilgas/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 94608000

[water]
homePath = $SPLUNK_DB/water/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 94608000

[aviation]
homePath = $SPLUNK_DB/aviation/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 220752000  # FAA 7 years

[logistics]
homePath = $SPLUNK_DB/logistics/db
maxDataSize = auto_high_volume
frozenTimePeriodInSecs = 31536000
```

---

<a id="cross-product"></a>
## Cross-Product Correlation

### Manufacturing — OEE drop → Maintenance prediction

```spl
(index=mfg sourcetype="oee:metric" earliest=-1h)
| stats avg(oee) as oee by line_id
| where oee < 75
| join line_id [search index=mfg sourcetype="opcua:metrics" metric_name IN ("vibration_mm_s","temperature_c") | stats avg(metric_value) as avg_val by line_id, metric_name]
```

### Healthcare — HL7 latency → Patient impact

```spl
(index=healthcare sourcetype="hl7:adt" earliest=-1h)
| stats latency_ms by patient_mrn
| where latency_ms > 5000
```

### Retail — Failed POS → Lost revenue

```spl
(index=retail sourcetype="retail:pos" status="failure" earliest=-1h)
| stats sum(transaction_amount) as lost_revenue by store_id
| sort -lost_revenue
```

---

<a id="compliance"></a>
## Compliance Mapping by Vertical

| Vertical | Key regulations |
|----------|-----------------|
| **Energy** | NERC CIP, FERC, ISO/RTO directives, EU NIS2 |
| **Manufacturing** | ISA-95, IEC 62443, ITAR (defense), ISO 9001 |
| **Healthcare** | HIPAA, HITECH, FDA 21 CFR Part 11 + 820, GxP, 42 CFR Part 2 |
| **Transportation** | DOT, FMCSA HOS, IATA |
| **Oil & Gas** | TSA Pipeline, API RP 1164, BSEE |
| **Retail** | PCI-DSS, GDPR/CCPA, FTC Safeguards |
| **Aviation** | FAA, EASA, ICAO, TSA |
| **Telco** | FCC, CALEA, GDPR, EU EECC |
| **Water** | EPA SDWA, AWIA, EU drinking water directive |
| **Insurance** | Solvency II, NAIC, SOX, GDPR |

---

<a id="sizing"></a>
## Capacity Planning and Sizing

| Vertical | Daily volume (large org) |
|----------|--------------------------|
| Energy | 10-100 GB |
| Manufacturing | 5-50 GB per plant |
| Healthcare | 10-200 GB per hospital system |
| Logistics | 5-100 GB |
| Oil & Gas | 50-500 GB |
| Retail | 10-100 GB per chain |
| Aviation | 50-500 GB per major hub |
| Telco | 1+ TB (CDR alone) |
| Water | 1-10 GB per utility |
| Insurance | 5-50 GB |

---

<a id="dashboards"></a>
## Recommended Dashboard Layouts (per Vertical)

Each vertical should have:
- Crawl: First-30-day onboarding dashboard
- Walk: Operational dashboards
- Run: Executive scorecards + compliance attestation

---

<a id="itsi"></a>
## ITSI Service Modeling

Per-vertical service trees, e.g., Manufacturing:
```
Manufacturing Posture
├── Per-Plant
│   ├── Production lines
│   ├── OEE per line
│   ├── Equipment health
│   └── Quality KPIs
├── Per-Process
└── Compliance posture
```

---

<a id="soar"></a>
## SOAR Playbook Examples

### Healthcare: Suspected diversion → Lock + Investigate

```
1. RECEIVE notable: pharmacy diversion candidate
2. SUSPEND user dispensing access (pharmacy system API)
3. CREATE compliance investigation ticket
4. NOTIFY pharmacy director
```

### Retail: POS down → Auto-failover

```
1. RECEIVE notable: POS terminal down 5min
2. CALL POS vendor API: failover to backup
3. NOTIFY store manager
4. CREATE Sev-2 ticket
```

### Telco: 5G UPF degraded → Auto-traffic-shift

```
1. RECEIVE notable: UPF latency > 50ms
2. CALL SMF API: shift traffic to redundant UPF
3. NOTIFY core engineering
```

---

<a id="multi-region"></a>
## Multi-Region Strategy

- Per-region indexes (`telco_us`, `telco_eu`, `telco_apac`)
- Data sovereignty: keep PHI / PII in-region
- Federated dashboards across regions

---

<a id="security-hardening"></a>
## Security Hardening

- Industry-specific RBAC (e.g., separate PHI access role for healthcare)
- Encryption at rest for all PHI/PII/PCI indexes
- Audit log retention per regulation (3-7 years typical)
- Field-level RBAC for sensitive identifiers

---

<a id="roadmap"></a>
## Crawl / Walk / Run Roadmap

### Crawl (Month 1)

1. Onboard 1-2 industry-specific data sources
2. Per-vertical compliance index strategy
3. Crawl-tier KPI dashboard

### Walk (Month 2-3)

1. Onboard remaining systems
2. ITSI service modeling
3. Per-vertical SOAR playbooks
4. Cross-system correlation

### Run (Month 4+)

1. Executive vertical scorecards
2. ML anomaly detection per vertical
3. Quarterly regulatory attestation
4. Predictive analytics

---

<a id="validation-checklist"></a>
## Validation Checklist

- [ ] Day 1: First vertical-specific event in Splunk
- [ ] Day 30: Walk-tier UCs deployed for chosen vertical
- [ ] Day 90: Executive dashboards live; compliance attestation operational

---

<a id="known-limitations"></a>
## Known Limitations and Gaps

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **Industry protocols (HL7v2, NETCONF)** | Custom parsing | Use Splunk OT add-on or vendor parsers |
| **High-volume CDR (telco)** | Storage cost | Summary indexing + selective retention |
| **PHI / PII compliance** | Field-level controls | RBAC + masking |
| **Vertical TA availability** | Often custom | Build per-vendor connector |

---

<a id="troubleshooting"></a>
## Troubleshooting

### HL7 messages not parsing

- Verify HL7 parser configured (vendor-specific)
- Check MSH segment delimiters

### Telco CDR ingest lag

- Check HEC token rate limits
- Use multi-HEC for parallel ingest

### POS data inconsistent across stores

- Verify store time zone handling
- Check CLOCK skew

---

<a id="faq"></a>
## FAQ

**Q: Should I use one Splunk for multiple verticals?**
A: Yes — single platform, per-vertical indexes / RBAC / dashboards.

**Q: How to handle PHI in Splunk?**
A: Encryption at rest + field-level RBAC + audit access to PHI indexes.

**Q: ITSI vs custom dashboards for verticals?**
A: ITSI is best for service-health KPIs; custom dashboards for non-service specifics.

**Q: How long to retain CDR / telco data?**
A: 3 years minimum (CALEA in US, varies elsewhere).

---

<a id="glossary"></a>
## Glossary

| Term | Definition |
|------|-----------|
| **AMI** | Advanced Metering Infrastructure |
| **OEE** | Overall Equipment Effectiveness |
| **MES** | Manufacturing Execution System |
| **CMMS** | Computerized Maintenance Management |
| **HL7** | Health Level Seven International |
| **FHIR** | Fast Healthcare Interoperability Resources |
| **EHR** | Electronic Health Record |
| **IoMT** | Internet of Medical Things |
| **TMS** | Transportation Management System |
| **WMS** | Warehouse Management System |
| **BHS** | Baggage Handling System |
| **OTP** | On-Time Performance (aviation) |
| **CDR** | Call Detail Record (telco) |
| **EDR** | Event Data Record (telco) |
| **IPDR** | IP Detail Record |
| **NRF/SMF/UPF/AMF/AUSF** | 5G Core network functions |
| **SCADA** | Supervisory Control and Data Acquisition |
| **DCS** | Distributed Control System |
| **POS** | Point of Sale |

---

<a id="references"></a>
## References

- [Splunk OT Security Add-on (Splunkbase 5151)](https://splunkbase.splunk.com/app/5151)
- [Splunk Industrial Asset Intelligence (Splunkbase 4942)](https://splunkbase.splunk.com/app/4942)
- [NERC CIP Standards](https://www.nerc.com/pa/Stand/Pages/ReliabilityStandards.aspx)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [TSA Pipeline Security Directives](https://www.tsa.gov/news/press/releases/pipeline-security-directives)
- [HL7 International](https://www.hl7.org/)
- [3GPP 5G Specifications](https://www.3gpp.org/)

---

<a id="contribution"></a>
## Contribution and Feedback

Part of the [Splunk Monitoring Use Cases](https://github.com/fenre/splunk-monitoring-use-cases) project. [Open an issue](https://github.com/fenre/splunk-monitoring-use-cases/issues/new).

---

*Last updated: 2026-05-09. Covers all 10 industry verticals with vertical-specific KPIs, regulatory compliance, and Splunk integration patterns.*

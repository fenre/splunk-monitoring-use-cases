"""Sourcetype-matrix scenarios for 47 unused canonical sourcetypes (×4 each)."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry, build_entry

# From docs/guides/industry-verticals.md sourcetypes list
CANONICAL_SOURCETYPES: list[tuple[str, str, tuple[str, str, str, str]]] = [
    # (sourcetype, default subcategory, 4 scenario titles)
    ("scada:tag", "21.1", ("Tag quality bad flag rate", "Tag scan rate drop", "Tag stale value detection", "Tag engineering unit mismatch")),
    ("smartgrid:event", "21.1", ("Smart grid event severity cluster", "Outage precursor event correlation", "Voltage sag event trending", "Transformer overload event")),
    ("derms:event", "21.1", ("DER curtailment command audit", "Battery dispatch failure", "Grid services bid rejection", "Volt-VAR optimization event")),
    ("oms:event", "21.1", ("OMS crew dispatch delay", "Customer callback SLA breach", "Outage ticket backlog spike", "Restoration milestone miss")),
    ("cmms:workorder", "21.2", ("CMMS work order overdue", "Emergency work order spike", "PM compliance gap", "Work order parts delay")),
    ("oee:metric", "21.2", ("OEE availability drop", "OEE performance degradation", "OEE quality reject spike", "OEE line comparison outlier")),
    ("wms:event", "21.4", ("WMS pick error rate", "WMS inventory adjustment spike", "WMS dock appointment miss", "WMS shipment short pick")),
    ("hl7:adt", "21.3", ("ADT admit message delay", "ADT discharge backlog", "ADT transfer mismatch", "ADT duplicate patient ID")),
    ("hl7:orm", "21.3", ("ORM order reject rate", "ORM cancel without fulfill", "ORM priority override audit", "ORM routing failure")),
    ("hl7:oru", "21.3", ("ORU critical result delay", "ORU amended result spike", "ORU routing failure", "ORU unsolicited result audit")),
    ("hl7:msh", "21.3", ("MSH parse error cluster", "MSH sending app unknown", "MSH version mismatch", "MSH control ID duplicate")),
    ("fhir:resource", "21.3", ("FHIR API 5xx error rate", "FHIR bulk export failure", "FHIR unauthorized read attempt", "FHIR write validation error")),
    ("epic:audit", "21.3", ("Epic break-glass cluster", "Epic after-hours chart access", "Epic proxy access audit", "Epic sensitive note view")),
    ("cerner:audit", "21.3", ("Cerner after-hours access", "Cerner order override audit", "Cerner results release delay", "Cerner admin action audit")),
    ("mediot:device", "21.3", ("IoMT device battery low", "IoMT firmware version drift", "IoMT alarm silence audit", "IoMT VLAN segmentation gap")),
    ("airport:passenger", "21.7", ("Passenger density threshold", "Terminal queue length spike", "Gate lounge overcrowding", "Security lane wait correlation")),
    ("atc:event", "21.7", ("ATC conflict alert rate", "ATC go-around cluster", "ATC runway incursion warning", "ATC separation loss near-miss")),
    ("retail:pos", "21.6", ("POS void transaction spike", "POS refund without receipt", "POS manager override rate", "POS offline mode duration")),
    ("retail:ecommerce", "21.6", ("E-commerce payment decline", "E-commerce cart timeout", "E-commerce inventory sync fail", "E-commerce promo abuse")),
    ("retail:loyalty", "21.6", ("Loyalty points manual adjustment", "Loyalty tier upgrade velocity", "Loyalty redemption fraud cluster", "Loyalty account merge anomaly")),
    ("telco:5g:smf", "21.8", ("SMF PDU session failure", "SMF QoS flow setup error", "SMF UPF selection failure", "SMF session modify reject")),
    ("telco:5g:upf", "21.8", ("UPF packet loss spike", "UPF session count saturation", "UPF GTP-U error rate", "UPF latency percentile breach")),
    ("telco:5g:amf", "21.8", ("AMF registration reject storm", "AMF handover failure cluster", "AMF UE context release spike", "AMF NAS security mode fail")),
    ("telco:5g:ausf", "21.8", ("AUSF auth vector failure", "AUSF SUPI concealment error", "AUSF resync failure rate", "AUSF latency SLA breach")),
    ("telco:cdr", "21.8", ("CDR missing record gap", "CDR rating error spike", "CDR premium route fraud", "CDR duration zero anomaly")),
    ("telco:edr", "21.8", ("EDR session drop cluster", "EDR APN misconfiguration", "EDR data stall detection", "EDR roaming attach failure")),
    ("telco:ipdr", "21.8", ("IPDR volume baseline breach", "IPDR tor exit correlation", "IPDR tethering abuse", "IPDR off-net tunnel detection")),
    ("water:scada", "21.9", ("Water SCADA pump run hours", "Water SCADA tank level drift", "Water SCADA chlorine feed alarm", "Water SCADA RTU comm loss")),
    ("water:meter", "21.9", ("Water AMI leak alert cluster", "Water AMI reverse flow", "Water AMI register stuck", "Water AMI endpoint battery low")),
    ("insurance:policy", "21.10", ("Policy cancellation velocity", "Policy endorsement fraud pattern", "Policy reinstatement anomaly", "Policy duplicate beneficiary")),
    ("insurance:underwriting", "21.10", ("Underwriting referral backlog", "Underwriting auto-decline spike", "Underwriting manual override", "Underwriting data quality gap")),
    ("oil:wellhead", "21.5", ("Wellhead choke anomaly", "Wellhead water cut spike", "Wellhead ESP trip cluster", "Wellhead comm loss duration")),
    ("oil:pipeline:scada", "21.5", ("Pipeline MAOP approach", "Pipeline pig passage miss", "Pipeline leak detection alarm", "Pipeline compressor trip")),
    ("oil:refinery:dcs", "21.5", ("Refinery unit upset correlation", "Refinery flare event duration", "Refinery exchanger fouling signal", "Refinery analyzer calibration drift")),
    ("scada:hmi", "21.1", ("HMI operator login after hours", "HMI setpoint change audit", "HMI alarm acknowledge delay", "HMI session concurrent limit")),
    ("scada:event", "21.1", ("SCADA event flood rate", "SCADA unacknowledged critical", "SCADA state oscillation", "SCADA event suppression audit")),
    ("mes:job", "21.2", ("MES job queue aging", "MES job rework rate", "MES job material shortage", "MES job schedule slip")),
    ("sap:idoc", "21.2", ("IDoc status 51 error cluster", "IDoc partner profile mismatch", "IDoc duplicate number", "IDoc processing backlog")),
    ("sap:cdr", "21.2", ("SAP financial posting delay", "SAP document reversal spike", "SAP tolerance limit breach", "SAP intercompany imbalance")),
    ("fleet:telematics", "21.4", ("Fleet GPS gap duration", "Fleet harsh cornering cluster", "Fleet idle fuel waste", "Fleet geofence violation")),
    ("tms:event", "21.4", ("TMS carrier score drop", "TMS detention charge spike", "TMS route deviation", "TMS delivery exception rate")),
    ("airport:bhs", "21.7", ("BHS sortation error rate", "BHS bag misroute cluster", "BHS early bag offload", "BHS loader timeout")),
    ("airport:flight", "21.7", ("Flight delay knock-on", "Flight gate conflict", "Flight cancellation cluster", "Flight turnaround SLA miss")),
    ("telco:5g:nrf", "21.8", ("NRF NF discovery failure", "NRF NF profile stale", "NRF service unavailable", "NRF registration deregister storm")),
    ("insurance:claim", "21.10", ("Claim reopen velocity", "Claim SIU referral spike", "Claim reserve change audit", "Claim duplicate FNOL")),
    ("smartgrid:meter", "21.1", ("AMI endpoint tamper flag", "AMI demand response miss", "AMI voltage sag report", "AMI endpoint firmware drift")),
    ("water:treatment", "21.9", ("Treatment turbidity exceedance", "Treatment chlorine residual low", "Treatment coagulant dose drift", "Treatment filter backwash miss")),
]


def matrix_entries() -> list[TaxonomyEntry]:
    out: list[TaxonomyEntry] = []
    for sourcetype, subcat, scenarios in CANONICAL_SOURCETYPES:
        for title in scenarios:
            out.append(
                build_entry(
                    subcategory=subcat,
                    title=title,
                    sourcetype=sourcetype,
                    spl_filter="*",
                    source_tag="matrix",
                )
            )
    return out

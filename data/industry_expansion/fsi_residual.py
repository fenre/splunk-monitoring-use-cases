"""FSI Essentials residual operations for subcategory 21.11 (net-new vs cat-10.12)."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry, build_entry

FSI_OPS: list[tuple[str, str]] = [
    ("Core banking transaction end-to-end latency", "finance:transaction"),
    ("ACH return item anomaly rate", "finance:ach"),
    ("Wire transfer dual-control bypass attempt", "finance:wire"),
    ("Card-not-present decline spike by merchant", "finance:card"),
    ("ATM cash dispense mismatch reconciliation", "finance:atm"),
    ("Branch teller override frequency audit", "finance:branch"),
    ("Loan origination document tamper signal", "finance:lending"),
    ("Deposit hold release policy violation", "finance:deposit"),
    ("Overdraft fee waiver pattern anomaly", "finance:retail_bank"),
    ("Treasury FX trade limit breach", "finance:treasury"),
    ("Securities lending recall delay", "finance:securities"),
    ("Custody asset reconciliation gap", "finance:custody"),
    ("Wealth management suitability override", "finance:wealth"),
    ("Insurance premium finance default cluster", "finance:premium_finance"),
    ("Merchant acquiring chargeback velocity", "finance:acquiring"),
    ("Payment gateway tokenization failure", "finance:gateway"),
    ("Open banking API consent revocation spike", "finance:open_banking"),
    ("BNPL installment delinquency signal", "finance:bnpl"),
    ("Cross-border remittance structuring pattern", "finance:remittance"),
    ("Trade finance LC discrepancy rate", "finance:trade_finance"),
    ("Corporate banking signatory change audit", "finance:corp_bank"),
    ("Private banking PEP screening backlog", "finance:private_bank"),
    ("Credit card limit increase velocity", "finance:card"),
    ("Mortgage servicing payment misapplication", "finance:mortgage"),
    ("Auto loan repossession workflow delay", "finance:auto_loan"),
    ("Student loan deferment fraud pattern", "finance:student_loan"),
    ("Small business LOC draw anomaly", "finance:smb"),
    ("Commercial real estate covenant breach signal", "finance:cre"),
    ("FX swap settlement fail prediction", "finance:fx"),
    ("Repo collateral haircut breach", "finance:repo"),
    ("Derivatives margin call cluster", "finance:derivatives"),
    ("Prime brokerage locate fail rate", "finance:prime_broker"),
    ("Market making inventory limit breach", "finance:market_making"),
    ("Dark pool order imbalance signal", "finance:dark_pool"),
    ("Regulatory reporting file rejection", "finance:reg_report"),
    ("Sanctions screening false negative audit", "finance:sanctions"),
    ("Beneficial ownership change alert", "finance:kyc"),
    ("Shell company transaction pattern", "finance:aml"),
    ("Crypto on-ramp velocity anomaly", "finance:crypto"),
    ("Embedded finance partner API abuse", "finance:embedded"),
]


def fsi_residual_entries() -> list[TaxonomyEntry]:
    return [
        build_entry(
            subcategory="21.11",
            title=title,
            sourcetype=st,
            spl_filter="*",
            monitoring_type=("Operations", "Audit"),
            criticality="high",
            source_tag="fsi",
        )
        for title, st in FSI_OPS
    ]

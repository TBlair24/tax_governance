import pandas as pd
import numpy as np
from datetime import date

def _pct(numerator, denominator):
    """Calculate pass rate as a percentage."""
    if denominator == 0:
        return 100.0
    return round(100.0 * numerator / denominator, 2)

def _issue(dimension, field, description, affected_rows, total_rows, severity):
    return {
        "dimension":     dimension,
        "field":         field,
        "description":   description,
        "affected_rows": affected_rows,
        "total_rows":    total_rows,
        "pass_rate":     _pct(total_rows - affected_rows, total_rows),
        "severity":      severity,
    }

def check_completeness(df, required_fields):
    issues = []

    for field in required_fields:
        if field not in df.columns:
            continue

        null_count = df[field].isna().sum()

        if null_count > 0:
            issues.append(_issue(
                dimension    = "Completeness",
                field        = field,
                description  = f"Missing values found in '{field}'",
                affected_rows= int(null_count),
                total_rows   = len(df),
                severity     = "HIGH" if null_count / len(df) > 0.05 else "MEDIUM",
            ))

    return issues

def check_validity(df, dataset_name):
    issues = []
    n = len(df)

    if dataset_name == "tax_returns":

        # Negative amounts
        if "amount_due_ugx" in df.columns:
            bad = df["amount_due_ugx"].notna() & (df["amount_due_ugx"] < 0)
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Validity",
                    field        = "amount_due_ugx",
                    description  = "Negative tax amounts are not permitted",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "HIGH",
                ))

        # Wrong currency
        if "currency" in df.columns:
            bad = df["currency"].notna() & ~df["currency"].isin(["UGX"])
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Validity",
                    field        = "currency",
                    description  = "Non-UGX currency — all domestic filings must use UGX",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "HIGH",
                ))

        # Invalid filing status
        if "filing_status" in df.columns:
            allowed = {"Filed", "Pending", "Overdue", "Amended"}
            bad = df["filing_status"].notna() & ~df["filing_status"].isin(allowed)
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Validity",
                    field        = "filing_status",
                    description  = f"Filing status must be one of: {allowed}",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "MEDIUM",
                ))

    if dataset_name == "taxpayer_register":

        # TIN must be exactly 10 digits
        if "tin" in df.columns:
            bad = df["tin"].notna() & ~df["tin"].astype(str).str.match(r"^\d{10}$")
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Validity",
                    field        = "tin",
                    description  = "TIN must be exactly 10 numeric digits",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "HIGH",
                ))

    return issues

def check_consistency(df, dataset_name):
    issues = []
    n = len(df)

    if dataset_name == "tax_returns":

        # Period end must be after period start
        if {"period_start", "period_end"}.issubset(df.columns):
            sub = df.dropna(subset=["period_start", "period_end"]).copy()
            sub["period_start"] = pd.to_datetime(sub["period_start"])
            sub["period_end"]   = pd.to_datetime(sub["period_end"])
            bad = sub["period_end"] <= sub["period_start"]
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Consistency",
                    field        = "period_start / period_end",
                    description  = "Period end date is not after period start date",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "HIGH",
                ))

        # Filing date must be after period start
        if {"period_start", "filing_date"}.issubset(df.columns):
            sub = df.dropna(subset=["period_start", "filing_date"]).copy()
            sub["period_start"] = pd.to_datetime(sub["period_start"])
            sub["filing_date"]  = pd.to_datetime(sub["filing_date"])
            bad = sub["filing_date"] < sub["period_start"]
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Consistency",
                    field        = "filing_date / period_start",
                    description  = "Filing date precedes the tax period start date",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "HIGH",
                ))

        # Amount paid should not exceed 150% of amount due
        if {"amount_due_ugx", "amount_paid_ugx"}.issubset(df.columns):
            sub = df.dropna(subset=["amount_due_ugx", "amount_paid_ugx"])
            bad = sub["amount_paid_ugx"] > sub["amount_due_ugx"] * 1.5
            if bad.sum():
                issues.append(_issue(
                    dimension    = "Consistency",
                    field        = "amount_paid_ugx / amount_due_ugx",
                    description  = "Payment exceeds 150% of amount due — possible data error",
                    affected_rows= int(bad.sum()),
                    total_rows   = n,
                    severity     = "MEDIUM",
                ))

    return issues

def check_uniqueness(df, key_fields):
    issues = []
    n = len(df)

    duplicates = df.duplicated(subset=key_fields, keep=False).sum()

    if duplicates > 0:
        issues.append(_issue(
            dimension    = "Uniqueness",
            field        = " + ".join(key_fields),
            description  = f"Duplicate records found on key fields: {key_fields}",
            affected_rows= int(duplicates),
            total_rows   = n,
            severity     = "HIGH" if duplicates / n > 0.02 else "MEDIUM",
        ))

    return issues

def check_timeliness(df, dataset_name):
    issues = []
    n = len(df)
    today = date.today()

    if dataset_name == "tax_returns":

        # Future filing dates
        if "filing_date" in df.columns:
            future = df["filing_date"].apply(
                lambda d: pd.to_datetime(d).date() > today if pd.notna(d) else False
            ).sum()
            if future:
                issues.append(_issue(
                    dimension    = "Timeliness",
                    field        = "filing_date",
                    description  = "Filing dates set in the future — likely a data entry error",
                    affected_rows= int(future),
                    total_rows   = n,
                    severity     = "MEDIUM",
                ))

        # Returns still Pending for more than 3 years
        if {"filing_date", "filing_status"}.issubset(df.columns):
            old = df["filing_date"].apply(
                lambda d: (today - pd.to_datetime(d).date()).days > 365 * 3 if pd.notna(d) else False
            )
            stale = (old & (df["filing_status"] == "Pending")).sum()
            if stale:
                issues.append(_issue(
                    dimension    = "Timeliness",
                    field        = "filing_date + filing_status",
                    description  = "Returns still Pending for more than 3 years",
                    affected_rows= int(stale),
                    total_rows   = n,
                    severity     = "LOW",
                ))

    return issues

def check_referential_integrity(returns_df, taxpayers_df):
    issues = []
    n = len(returns_df)

    valid_tins = set(taxpayers_df["tin"].dropna().astype(str))

    orphans = returns_df["tin"].dropna().astype(str).apply(
        lambda t: t not in valid_tins
    ).sum()

    if orphans:
        issues.append(_issue(
            dimension    = "Referential Integrity",
            field        = "tin",
            description  = "TINs in tax_returns not found in the taxpayer register",
            affected_rows= int(orphans),
            total_rows   = n,
            severity     = "HIGH",
        ))

    return issues

def run_all_checks(data_dir="data/raw"):
    # Load datasets
    taxpayers = pd.read_csv(f"{data_dir}/taxpayer_register.csv")
    returns   = pd.read_csv(f"{data_dir}/tax_returns.csv")

    all_issues = []

    # Run all checks
    all_issues += check_completeness(returns,
                    required_fields=["return_id", "tin", "tax_type",
                                     "amount_due_ugx", "filing_date"])
    all_issues += check_validity(returns, "tax_returns")
    all_issues += check_consistency(returns, "tax_returns")
    all_issues += check_uniqueness(returns, ["return_id"])
    all_issues += check_timeliness(returns, "tax_returns")
    all_issues += check_referential_integrity(returns, taxpayers)
    all_issues += check_completeness(taxpayers,
                    required_fields=["tin", "taxpayer_name", "sector", "region"])
    all_issues += check_validity(taxpayers, "taxpayer_register")
    all_issues += check_uniqueness(taxpayers, ["tin"])

    # Score each dimension
    all_dimensions = ["Completeness", "Validity", "Consistency",
                      "Uniqueness", "Timeliness", "Referential Integrity"]

    dimension_scores = {}
    for dim in all_dimensions:
        dim_issues = [i for i in all_issues if i["dimension"] == dim]
        if not dim_issues:
            dimension_scores[dim] = 100.0
        else:
            dimension_scores[dim] = round(
                np.mean([i["pass_rate"] for i in dim_issues]), 2
            )

    overall_score = round(np.mean(list(dimension_scores.values())), 2)

    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for issue in all_issues:
        severity_counts[issue["severity"]] += 1

    return {
        "overall_dq_score": overall_score,
        "dimension_scores": dimension_scores,
        "severity_summary": severity_counts,
        "total_issues":     len(all_issues),
        "issues":           all_issues,
    }
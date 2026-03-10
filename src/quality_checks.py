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
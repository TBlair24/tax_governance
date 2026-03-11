import sys
import os
import time
import json
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_generator  import generate_taxpayer_register, generate_tax_returns, generate_audit_log
from src.quality_checks  import run_all_checks
from src.lineage_tracker import init_db, register_dataset, register_transformation, log_dq_run, get_lineage_graph

DATA_RAW  = "data/raw"
DATA_PROC = "data/processed"
OUTPUTS   = "outputs"

def clean_returns(df):
    clean = df.copy()
    before = len(clean)

    clean = clean.dropna(subset=["tin", "amount_due_ugx"])
    clean = clean[clean["tin"].astype(str).str.match(r"^\d{10}$")]
    clean = clean[clean["amount_due_ugx"] >= 0]
    clean = clean[clean["currency"] == "UGX"]
    clean["filing_date"] = pd.to_datetime(clean["filing_date"])
    clean = clean[clean["filing_date"] <= pd.Timestamp.today()]
    clean = clean.drop_duplicates(subset=["return_id"])

    after = len(clean)
    return clean, before, after

def run_pipeline():
    print("=" * 55)
    print("  URA DATA GOVERNANCE PIPELINE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Step 1 — Initialise lineage DB
    print("\n[1/5] Initialising lineage database...")
    init_db()

    # Step 2 — Generate datasets
    print("\n[2/5] Generating datasets...")
    t0 = time.time()
    os.makedirs(DATA_RAW,  exist_ok=True)
    os.makedirs(DATA_PROC, exist_ok=True)
    os.makedirs(OUTPUTS,   exist_ok=True)

    taxpayers = generate_taxpayer_register(500)
    returns   = generate_tax_returns(taxpayers, 2000)
    audit_log = generate_audit_log(returns)

    taxpayers.to_csv(f"{DATA_RAW}/taxpayer_register.csv", index=False)
    returns.to_csv(f"{DATA_RAW}/tax_returns.csv", index=False)
    audit_log.to_csv(f"{DATA_RAW}/audit_log.csv", index=False)
    gen_ms = int((time.time() - t0) * 1000)

    tp_id  = register_dataset("taxpayer_register", taxpayers, "raw_file",
                               f"{DATA_RAW}/taxpayer_register.csv",
                               "Master register of all registered taxpayers")
    ret_id = register_dataset("tax_returns", returns, "raw_file",
                               f"{DATA_RAW}/tax_returns.csv",
                               "Tax return filings with injected quality issues")

    print(f"   taxpayers : {len(taxpayers):,} rows")
    print(f"   returns   : {len(returns):,} rows")
    print(f"   audit log : {len(audit_log):,} rows")
    print(f"   completed in {gen_ms}ms")

    # Step 3 — Run quality checks
    print("\n[3/5] Running quality checks...")
    t0 = time.time()
    dq_results = run_all_checks(DATA_RAW)
    dq_ms = int((time.time() - t0) * 1000)

    log_dq_run(ret_id, dq_results)

    with open(f"{OUTPUTS}/dq_results.json", "w") as f:
        json.dump(dq_results, f, indent=2, default=str)

    print(f"   Overall DQ Score : {dq_results['overall_dq_score']}%")
    print(f"   Issues           : {dq_results['total_issues']} total — "
          f"{dq_results['severity_summary']['HIGH']} HIGH, "
          f"{dq_results['severity_summary']['MEDIUM']} MEDIUM, "
          f"{dq_results['severity_summary']['LOW']} LOW")
    print(f"   completed in {dq_ms}ms")

    # Step 4 — Clean the data
    print("\n[4/5] Cleaning data...")
    t0 = time.time()
    clean, before, after = clean_returns(returns)
    clean_ms = int((time.time() - t0) * 1000)

    clean.to_csv(f"{DATA_PROC}/tax_returns_clean.csv", index=False)

    clean_id = register_dataset("tax_returns_clean", clean, "transformed",
                                 f"{DATA_PROC}/tax_returns_clean.csv",
                                 "Cleaned tax returns — passed all quality checks")

    register_transformation(
        step_name   = "DQ Remediation",
        input_ids   = [ret_id],
        output_id   = clean_id,
        operation   = "filter + deduplicate",
        description = "Remove rows failing null, validity, currency, date and uniqueness checks",
        duration_ms = clean_ms,
    )

    retained_pct = round(100 * after / before, 1)
    print(f"   rows before : {before:,}")
    print(f"   rows after  : {after:,}")
    print(f"   retained    : {retained_pct}%")
    print(f"   completed in {clean_ms}ms")

    # Step 5 — Save summary
    print("\n[5/5] Saving pipeline summary...")
    summary = {
        "pipeline_run":     datetime.now().isoformat(timespec="seconds"),
        "dq_results":       dq_results,
        "cleaning_summary": {
            "rows_before":   before,
            "rows_after":    after,
            "rows_removed":  before - after,
            "retention_pct": retained_pct,
        },
        "lineage": get_lineage_graph(),
    }
    with open(f"{OUTPUTS}/pipeline_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"   saved → {OUTPUTS}/pipeline_summary.json")

    print("\n" + "=" * 55)
    print("  PIPELINE COMPLETE")
    print("=" * 55)
    return summary


if __name__ == "__main__":
    run_pipeline()
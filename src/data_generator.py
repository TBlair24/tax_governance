import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

# so our random data is reproducible - same data every time we run the script
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# Categories our data will use
TAX_TYPES = ['VAT', 'Corporate Tax', 'PAYE', 'Withholding Tax', 'Customs Duty', 'Excise Duty']
REGIONS = ['Central', ' Northern', 'Eastern', 'Western', 'Kampala Metropolitan']
SECTORS = ['Manufacturing', 'Trade', 'Services', 'Agriculture', 'Mining', 'Transport', 'Finance']
FILING_STATUSES = ['Filed', 'Pending', 'Overdue', 'Amended']

# The Taxpayer Register
def _random_tin():
    # Generate a random 10-digit TIN (Tax Identification Number)
    return str(random.randint(1_000_000_000, 9_999_999_999))

def _random_date(start, end):
    # pick random date between two dates
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_taxpayer_register(n=500):
    records = []
    for _ in range(n):
        tin = _random_tin()
        records.append({
            "tin": tin,
            "taxpayer_name": f"Company_{tin[-4:]}",  # Just a placeholder name using last 4 digits of TIN
            "sector": random.choice(SECTORS),
            "region": random.choice(REGIONS),
            "registration_date": _random_date(datetime(2000, 1, 1), datetime(2023, 12, 31)).date(),
            "is_active": random.choices([True, False], weights=[85, 15])[0]  # Assume most taxpayers are active
        })

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset="tin").reset_index(drop=True)  # Ensure unique TINs
    return df

def generate_tax_returns(taxpayer_df, n=2000):
    valid_tins = taxpayer_df["tin"].tolist()
    records = []

    for i in range(n):
        tin          = random.choice(valid_tins)
        period_start = _random_date(datetime(2021, 1, 1), datetime(2024, 6, 30))
        period_end   = period_start + timedelta(days=30)
        filing_date  = period_end + timedelta(days=random.randint(-5, 45))
        amount_due   = round(random.uniform(500_000, 500_000_000), 2)
        amount_paid  = round(amount_due * random.uniform(0.0, 1.2), 2)

        records.append({
            "return_id":       f"RET-{i+1:05d}",
            "tin":             tin,
            "tax_type":        random.choice(TAX_TYPES),
            "period_start":    period_start.date(),
            "period_end":      period_end.date(),
            "filing_date":     filing_date.date(),
            "filing_status":   random.choice(FILING_STATUSES),
            "amount_due_ugx":  amount_due,
            "amount_paid_ugx": amount_paid,
            "currency":        "UGX",
            "assessor_id":     f"ASR-{random.randint(100, 199)}",
        })

    df = pd.DataFrame(records)

    # Introduce some null TINs to simulate data quality issues
    rng = np.random.default_rng(SEED)

    # ~5% of rows get a null TIN
    null_idx = rng.choice(len(df), size=int(len(df) * 0.05), replace=False)
    df.loc[null_idx, "tin"] = None

    # ~4% of rows get a fake TIN not in the register
    invalid_idx = rng.choice(len(df), size=int(len(df) * 0.04), replace=False)
    df.loc[invalid_idx, "tin"] = [_random_tin() + "X" for _ in range(len(invalid_idx))]

    # ~3% of rows get a negative amount
    neg_idx = rng.choice(len(df), size=int(len(df) * 0.03), replace=False)
    df.loc[neg_idx, "amount_due_ugx"] = df.loc[neg_idx, "amount_due_ugx"] * -1

    # ~4% of rows get a foreign currency
    curr_idx = rng.choice(len(df), size=int(len(df) * 0.04), replace=False)
    df.loc[curr_idx, "currency"] = rng.choice(["USD", "EUR"], size=len(curr_idx)).tolist()

    # ~3% of rows get a future filing date
    future_idx = rng.choice(len(df), size=int(len(df) * 0.03), replace=False)
    df.loc[future_idx, "filing_date"] = datetime(2027, 1, 1).date()

    # ~4% of rows get a null amount
    null_amt_idx = rng.choice(len(df), size=int(len(df) * 0.04), replace=False)
    df.loc[null_amt_idx, "amount_due_ugx"] = None

    # ~3% of rows get a duplicated return_id
    dup_idx = rng.choice(len(df), size=int(len(df) * 0.03), replace=False)
    df.loc[dup_idx, "return_id"] = df["return_id"].sample(len(dup_idx), random_state=1).values

    return df

def generate_audit_log(tax_returns_df, n=500):
    import hashlib
    
    events = ["CREATED", "UPDATED", "REVIEWED", "FLAGGED", "APPROVED"]
    users  = [f"USR-{i:03d}" for i in range(10, 25)]
    
    records = []
    sampled = tax_returns_df.sample(min(n, len(tax_returns_df)), random_state=SEED)
    
    for _, row in sampled.iterrows():
        # Each return gets 1 to 3 audit events
        for _ in range(random.randint(1, 3)):
            event_time = _random_date(datetime(2024, 1, 1), datetime(2024, 12, 31))
            records.append({
                "event_id":  hashlib.md5(f"{row['return_id']}{random.random()}".encode()).hexdigest()[:12],
                "return_id": row["return_id"],
                "event_type":random.choice(events),
                "user_id":   random.choice(users),
                "timestamp": event_time,
            })
    
    return pd.DataFrame(records)

def save_datasets(output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True)

    print("Generating taxpayer register...")
    taxpayers = generate_taxpayer_register(500)
    taxpayers.to_csv(f"{output_dir}/taxpayer_register.csv", index=False)

    print("Generating tax returns...")
    returns = generate_tax_returns(taxpayers, 2000)
    returns.to_csv(f"{output_dir}/tax_returns.csv", index=False)

    print("Generating audit log...")
    audit = generate_audit_log(returns)
    audit.to_csv(f"{output_dir}/audit_log.csv", index=False)

    print(f"\nDone! Files saved to {output_dir}/")
    print(f"  taxpayer_register : {len(taxpayers)} rows")
    print(f"  tax_returns       : {len(returns)} rows")
    print(f"  audit_log         : {len(audit)} rows")

if __name__ == "__main__":
    save_datasets()
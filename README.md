# 🏛️ URA Data Governance Framework

An end-to-end data quality and governance pipeline simulating the 
framework a Supervisor Data Science would build at the Uganda Revenue 
Authority.

---

## What This Project Does

Raw tax data arrives with real-world quality problems — missing values,
invalid formats, duplicate records, orphaned foreign keys. This framework
systematically detects, scores, and resolves those problems, then
produces both an interactive dashboard and a stakeholder-ready PDF report.

| Stage | Tool | Output |
|---|---|---|
| Data Generation | Python / pandas | Synthetic taxpayer and tax return datasets |
| Quality Checks | Custom DQ engine | Scored issues across 6 dimensions |
| Lineage Tracking | SQLite | Audit trail of all transformations |
| Remediation | pandas | Cleaned dataset ready for analysis |
| Dashboard | Streamlit | Interactive 5-page governance dashboard |
| Reporting | ReportLab | Auto-generated PDF assessment report |

---

## Quality Dimensions Assessed

| Dimension | Question Asked |
|---|---|
| Completeness | Are required fields populated? |
| Validity | Are values in the right format and range? |
| Consistency | Are related fields logically coherent? |
| Uniqueness | Are there duplicate records? |
| Timeliness | Are dates within acceptable windows? |
| Referential Integrity | Do foreign keys point to real records? |

---

## Project Structure
```
tax_governance/
├── src/
│   ├── data_generator.py     # Synthetic data with injected quality issues
│   ├── quality_checks.py     # 6-dimension DQ engine
│   ├── lineage_tracker.py    # SQLite lineage catalogue
│   ├── pipeline.py           # Master orchestrator
│   └── report_generator.py  # PDF report generator
├── dashboard/
│   └── app.py                # Streamlit governance dashboard
├── data/
│   ├── raw/                  # Generated raw datasets
│   └── processed/            # Cleaned datasets
├── outputs/
│   ├── dq_results.json       # Quality check results
│   ├── pipeline_summary.json # Full pipeline output
│   ├── lineage.db            # SQLite lineage database
│   └── reports/              # Generated PDF reports
└── requirements.txt
```

---

## Setup
```bash
git clone https://github.com/yourusername/ura-data-governance.git
cd ura-data-governance
pip install -r requirements.txt
```

---

## Running the Project

### 1 — Run the full pipeline
```bash
python src/pipeline.py
```
Generates datasets, runs all quality checks, cleans the data,
logs lineage, and saves all outputs.

### 2 — Launch the dashboard
```bash
streamlit run dashboard/app.py
```
Opens at http://localhost:8501

### 3 — Generate a PDF report
```bash
python src/report_generator.py
```
Saved to outputs/reports/

---

## Sample Results

- **Overall DQ Score:** 95.24%
- **Issues detected:** 9 (4 HIGH, 4 MEDIUM, 1 LOW)
- **Records retained after cleaning:** 1,536 / 2,000 (76.8%)

| Dimension | Score |
|---|---|
| Completeness | 95.65% |
| Validity | 96.58% |
| Consistency | 97.15% |
| Uniqueness | 94.10% |
| Timeliness | 91.98% |
| Referential Integrity | 96.00% |

---

## Quality Issues Injected

| Issue | Rate | Severity |
|---|---|---|
| Null TINs | ~5% | HIGH |
| Invalid TINs not in register | ~4% | HIGH |
| Negative tax amounts | ~3% | HIGH |
| Non-UGX currency | ~4% | HIGH |
| Future filing dates | ~3% | MEDIUM |
| Null amount due | ~4% | MEDIUM |
| Duplicate return IDs | ~3% | MEDIUM |

---

## Skills Demonstrated

- Data quality engineering across 6 DAMA-aligned dimensions
- Data governance — lineage tracking, cataloguing, policy documentation  
- Pipeline architecture — modular, reproducible, fully orchestrated
- Stakeholder communication — PDF reports and interactive dashboard
- Python best practices — separation of concerns, helper functions, constants

---

## Tech Stack

| Library | Purpose |
|---|---|
| pandas / numpy | Data manipulation and quality calculations |
| sqlite3 | Lineage and audit trail persistence |
| streamlit | Interactive governance dashboard |
| reportlab | PDF report generation |

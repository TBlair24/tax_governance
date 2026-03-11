import sqlite3
import json
import hashlib
import os
import pandas as pd
from datetime import datetime

DB_PATH = "outputs/lineage.db"

def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            source_type  TEXT,
            file_path    TEXT,
            row_count    INTEGER,
            col_count    INTEGER,
            created_at   TEXT,
            description  TEXT
        );

        CREATE TABLE IF NOT EXISTS transformations (
            transform_id    TEXT PRIMARY KEY,
            step_name       TEXT NOT NULL,
            input_datasets  TEXT,
            output_dataset  TEXT,
            operation       TEXT,
            description     TEXT,
            executed_at     TEXT,
            duration_ms     INTEGER,
            status          TEXT
        );

        CREATE TABLE IF NOT EXISTS dq_runs (
            run_id         TEXT PRIMARY KEY,
            dataset_id     TEXT,
            overall_score  REAL,
            total_issues   INTEGER,
            high_issues    INTEGER,
            medium_issues  INTEGER,
            low_issues     INTEGER,
            run_at         TEXT
        );
    """)
    conn.commit()
    conn.close()
    print("Lineage DB initialised →", DB_PATH)

def _generate_id(text):
    return hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:16]

def register_dataset(name, df, source_type, file_path, description=""):
    dataset_id = _generate_id(name)
    conn = _get_conn()
    conn.execute("""
        INSERT INTO datasets
        (dataset_id, name, source_type, file_path, row_count, col_count, created_at, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (dataset_id, name, source_type, file_path,
          len(df), len(df.columns),
          datetime.now().isoformat(timespec="seconds"),
          description))
    conn.commit()
    conn.close()
    return dataset_id

def register_transformation(step_name, input_ids, output_id,
                            operation, description, duration_ms=0, status="success"):
    transform_id = _generate_id(step_name)
    conn = _get_conn()
    conn.execute("""
        INSERT INTO transformations
        (transform_id, step_name, input_datasets, output_dataset,
         operation, description, executed_at, duration_ms, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (transform_id, step_name,
          json.dumps(input_ids), output_id,
          operation, description,
          datetime.now().isoformat(timespec="seconds"),
          duration_ms, status))
    conn.commit()
    conn.close()
    return transform_id

def log_dq_run(dataset_id, dq_results):
    run_id = _generate_id(dataset_id)
    conn = _get_conn()
    conn.execute("""
        INSERT INTO dq_runs
        (run_id, dataset_id, overall_score, total_issues,
         high_issues, medium_issues, low_issues, run_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, dataset_id,
          dq_results["overall_dq_score"],
          dq_results["total_issues"],
          dq_results["severity_summary"]["HIGH"],
          dq_results["severity_summary"]["MEDIUM"],
          dq_results["severity_summary"]["LOW"],
          datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()
    return run_id

def get_catalogue():
    conn = _get_conn()
    df = pd.read_sql("SELECT * FROM datasets ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_lineage_graph():
    conn = _get_conn()
    datasets        = [dict(r) for r in conn.execute("SELECT * FROM datasets").fetchall()]
    transformations = [dict(r) for r in conn.execute("SELECT * FROM transformations").fetchall()]
    conn.close()

    nodes = [{"id": d["dataset_id"], "label": d["name"],
              "type": d["source_type"], "rows": d["row_count"]}
             for d in datasets]

    edges = []
    for t in transformations:
        for inp in json.loads(t["input_datasets"]):
            edges.append({
                "from":      inp,
                "to":        t["output_dataset"],
                "label":     t["step_name"],
                "operation": t["operation"],
                "status":    t["status"],
            })

    return {"nodes": nodes, "edges": edges}


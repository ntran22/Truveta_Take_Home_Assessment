"""
setup.py Run this once to create data.duckdb from the provided CSVs.

Requirements:
    pip install duckdb pandas

Usage:
    python setup.py
"""

import os
import sys

try:
    import duckdb
except ImportError:
    sys.exit("Please install duckdb first:  pip install duckdb")

DB_PATH = "truveta_data.duckdb"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Removed existing {DB_PATH}")

con = duckdb.connect(DB_PATH)

con.execute("""
CREATE TABLE patient (
    PatientID      VARCHAR PRIMARY KEY,
    BirthDate      DATE,
    Sex            VARCHAR,
    Race           VARCHAR,
    CensusRegion   VARCHAR,
    Zip3           VARCHAR
)
""")

con.execute("""
CREATE TABLE encounter (
    PatientId      VARCHAR,
    EncounterId    VARCHAR PRIMARY KEY,
    EncounterType  VARCHAR,
    StartDate      TIMESTAMP,
    EndDate        TIMESTAMP
)
""")

con.execute("""
CREATE TABLE billing (
    PatientId       VARCHAR,
    EncounterId     VARCHAR,
    BillingDate     DATE,
    Amount          NUMERIC
)
""")

con.execute("""
CREATE TABLE condition (
    PatientId       VARCHAR,
    EncounterId     VARCHAR,
    OnsetDate       DATE,
    Code            VARCHAR
)
""")

tables = ["patient", "encounter", "billing", "condition"]
for table in tables:
    csv_path = f"data/{table}.csv"
    con.execute(f"COPY {table} FROM '{csv_path}' (HEADER TRUE, NULLSTR '')")
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<25} {count:>6} rows loaded")

con.close()
print(f"\nDone. {DB_PATH} is ready.")
print("Open starter.ipynb to begin.")

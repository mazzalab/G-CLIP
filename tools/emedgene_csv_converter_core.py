from datetime import datetime
import pandas as pd
import re
import os
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


preselected_date_columns = ["Date Of Birth",
                            "Due Date", "DataRichiesta", "DataRicezioneCampione"]
sample_id_column_default = "BioSample Name"

# Globals like before (loaded excel)
loaded_excel_path = None
df_loaded = None


def load_hpo_list(hpo_file):
    valid_hpo = set()

    if hpo_file.endswith(".obo"):
        with open(hpo_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("id: HP:"):
                    valid_hpo.add(line.split("id: ")[1].strip())
    else:
        df = pd.read_csv(hpo_file, sep=None, engine="python", header=None)
        for col in df.columns:
            df[col] = df[col].astype(str)
        ids = df.apply(lambda col: col[col.str.startswith(
            "HP:")], axis=0).stack().unique()
        valid_hpo.update(ids)

    return valid_hpo


def normalize_hpo_field(entry: str) -> list:
    if not isinstance(entry, str):
        entry = "" if pd.isna(entry) else str(entry)
    return re.findall(r"HP:\d+", entry)


def try_parse_date(value):
    if pd.isna(value) or value == "":
        return ""

    # Pandas attempt first
    dt = pd.to_datetime(value, errors="coerce", dayfirst=False)
    if not pd.isna(dt):
        return dt.strftime("%Y-%m-%d")

    # Manual fallback formats
    formats = [
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]

    for f in formats:
        try:
            return datetime.strptime(str(value), f).strftime("%Y-%m-%d")
        except Exception:
            pass

    return "WRONG_DATE_CONVERSION"


def force_dates_iso(df: pd.DataFrame, cols: list):
    for col in cols:
        if col not in df.columns:
            continue

        df[col] = df[col].apply(try_parse_date)


def run_conversion(df, hpo_colname, date_cols, valid_hpo_codes, sample_id_col):
    df = df.copy()

    # normalize dates
    force_dates_iso(df, date_cols)

    # normalize HPO
    if hpo_colname in df.columns:
        df[hpo_colname] = df[hpo_colname].fillna("").astype(str)

        normalized = []
        invalid_records = []

        for idx, raw in df[hpo_colname].items():
            codes = normalize_hpo_field(raw)
            invalid = [c for c in codes if c not in valid_hpo_codes]
            if invalid:
                sample = df[sample_id_col].iloc[idx] if sample_id_col in df.columns else "unknown"
                invalid_records.append((idx, sample, invalid))
            normalized.append(
                "; ".join([c for c in codes if c not in invalid]))

        df[hpo_colname] = normalized

    # # ✅ FORCE ALL COLUMNS TO STRING, no numeric types allowed
    # df = df.astype(str).replace("nan", "").applymap(lambda x: x.strip())

    # # ✅ ensure date columns keep ISO formatting
    # for col in date_cols:
    #     df[col] = df[col].apply(lambda x: x if x else "")

    return df, invalid_records

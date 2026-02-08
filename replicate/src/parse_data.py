"""
Data parsing and construction script.
Parses all raw data sources and constructs the evaluation dataset.

Steps:
1. Parse RSGA files -> daily forecast probabilities
2. Parse ASR catalog + NOAA events -> binary flare labels
3. Parse DSD files -> cross-check flare counts
4. Parse SILSO -> daily sunspot numbers
5. Merge into evaluation dataset
6. Compute derived features (consecutive flare-free days)
7. Save processed data
"""

import os
import re
import tarfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
os.makedirs(PROC, exist_ok=True)


# ==========================================================================
# 1. Parse RSGA files -> forecast probabilities
# ==========================================================================

def parse_rsga_files():
    """
    Parse all RSGA tar.gz files to extract daily M/X class forecast probabilities.
    Returns DataFrame with columns:
      issue_date, m_day1, m_day2, m_day3, x_day1, x_day2, x_day3
    """
    rsga_dir = os.path.join(RAW, "swpc_rsga")
    records = []

    for year in range(1996, 2025):
        archive = os.path.join(rsga_dir, f"{year}_RSGA.tar.gz")
        if not os.path.exists(archive):
            print(f"  WARNING: Missing {archive}")
            continue

        with tarfile.open(archive) as tf:
            for member in tf.getnames():
                if not member.endswith("RSGA.txt"):
                    continue

                # Extract date from filename: YYYYMMDDRSGA.txt
                basename = os.path.basename(member)
                match = re.match(r"(\d{8})RSGA\.txt", basename)
                if not match:
                    continue
                issue_date = datetime.strptime(match.group(1), "%Y%m%d").date()

                try:
                    content = tf.extractfile(member).read().decode("utf-8", errors="replace")
                except:
                    continue

                m_probs = None
                x_probs = None

                for line in content.split("\n"):
                    line_upper = line.upper().strip()

                    # Match "CLASS M    15/10/05" or "Class M    01/01/01"
                    m_match = re.match(r"CLASS\s+M\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", line_upper)
                    if m_match:
                        m_probs = [int(m_match.group(i)) for i in range(1, 4)]

                    x_match = re.match(r"CLASS\s+X\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", line_upper)
                    if x_match:
                        x_probs = [int(x_match.group(i)) for i in range(1, 4)]

                if m_probs and x_probs:
                    records.append({
                        "issue_date": issue_date,
                        "m_day1": m_probs[0],
                        "m_day2": m_probs[1],
                        "m_day3": m_probs[2],
                        "x_day1": x_probs[0],
                        "x_day2": x_probs[1],
                        "x_day3": x_probs[2],
                    })

        print(f"  {year}: parsed {sum(1 for r in records if r['issue_date'].year == year)} days")

    df = pd.DataFrame(records)
    df["issue_date"] = pd.to_datetime(df["issue_date"])
    df = df.sort_values("issue_date").reset_index(drop=True)
    print(f"  Total RSGA records: {len(df)}")
    return df


def build_forecast_dataset(rsga_df):
    """
    Convert issue-date-based forecasts to target-date-based forecasts.

    For target date D:
      - 24hr forecast = day1 from RSGA issued on D-1
      - 48hr forecast = day2 from RSGA issued on D-2
      - 72hr forecast = day3 from RSGA issued on D-3
    """
    # Create lookup by issue_date
    rsga_df = rsga_df.set_index("issue_date")

    # Build target date range
    min_target = rsga_df.index.min() + timedelta(days=1)
    max_target = rsga_df.index.max() + timedelta(days=3)

    records = []
    for target in pd.date_range(min_target, max_target, freq="D"):
        d1_issue = target - timedelta(days=1)  # 24hr ahead
        d2_issue = target - timedelta(days=2)  # 48hr ahead
        d3_issue = target - timedelta(days=3)  # 72hr ahead

        rec = {"date": target.date()}

        if d1_issue in rsga_df.index:
            row = rsga_df.loc[d1_issue]
            rec["m_24h"] = row["m_day1"]
            rec["x_24h"] = row["x_day1"]
        else:
            rec["m_24h"] = np.nan
            rec["x_24h"] = np.nan

        if d2_issue in rsga_df.index:
            row = rsga_df.loc[d2_issue]
            rec["m_48h"] = row["m_day2"]
            rec["x_48h"] = row["x_day2"]
        else:
            rec["m_48h"] = np.nan
            rec["x_48h"] = np.nan

        if d3_issue in rsga_df.index:
            row = rsga_df.loc[d3_issue]
            rec["m_72h"] = row["m_day3"]
            rec["x_72h"] = row["x_day3"]
        else:
            rec["m_72h"] = np.nan
            rec["x_72h"] = np.nan

        records.append(rec)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    # Apply the known typo fix: 2007-09-04 M-class 71->70
    typo_mask = df["date"] == "2007-09-04"
    if typo_mask.any():
        for col in ["m_24h", "m_48h", "m_72h"]:
            if df.loc[typo_mask, col].values[0] == 71:
                print(f"  Fixing typo: 2007-09-04 {col} = 71 -> 70")
                df.loc[typo_mask, col] = 70

    print(f"  Forecast dataset: {len(df)} target days, {df['m_24h'].notna().sum()} with 24h forecasts")
    return df


# ==========================================================================
# 2. Parse flare catalogs -> binary labels
# ==========================================================================

def parse_asr_catalog():
    """
    Parse ASR flare catalog to get daily binary M/X labels.
    Uses abs_class_simple (absolute GOES class from peak flux).
    The paper used ASR v1.0 (f_2002_2024.csv); we downloaded v1.0 as well.
    Combined with NOAA events for 1996-2001, this matches the paper's counts.
    """
    # Prefer v1.0 if available, fall back to v1.1
    v1_path = os.path.join(RAW, "asr_flare_catalog_v1.csv")
    v11_path = os.path.join(RAW, "asr_flare_catalog.csv")
    path = v1_path if os.path.exists(v1_path) else v11_path
    df = pd.read_csv(path)
    print(f"  ASR catalog ({os.path.basename(path)}): {len(df)} total events")

    # Use abs_class_simple (absolute peak-flux GOES class).
    # This matches paper counts when combined with NOAA events for 1996-2001.
    df["class"] = df["abs_class_simple"].str.strip()
    m_flares = df[df["class"] == "M"].copy()
    x_flares = df[df["class"] == "X"].copy()
    print(f"  ASR M-class events: {len(m_flares)}")
    print(f"  ASR X-class events: {len(x_flares)}")

    # Extract date (UTC) from tpeak (or tstart)
    m_flares["date"] = pd.to_datetime(m_flares["tpeak"], format="mixed").dt.date
    x_flares["date"] = pd.to_datetime(x_flares["tpeak"], format="mixed").dt.date

    # Get unique M/X days
    m_days = set(m_flares["date"].unique())
    x_days = set(x_flares["date"].unique())

    return m_days, x_days


def parse_noaa_events(start_year=1996, end_year=2001):
    """
    Parse NOAA SWPC event reports (1996-2001) to extract M/X class flare days.
    Event files are daily text files with XRA (X-ray) event records.
    """
    events_dir = os.path.join(RAW, "noaa_events")
    m_days = set()
    x_days = set()
    total_files = 0

    for year in range(start_year, end_year + 1):
        year_dir = os.path.join(events_dir, f"{year}_events")
        if not os.path.exists(year_dir):
            # Try extracting from tar.gz
            archive = os.path.join(events_dir, f"{year}_events.tar.gz")
            if os.path.exists(archive):
                with tarfile.open(archive) as tf:
                    tf.extractall(events_dir)

        if not os.path.exists(year_dir):
            print(f"  WARNING: No events directory for {year}")
            continue

        for fname in sorted(os.listdir(year_dir)):
            if not fname.endswith("events.txt"):
                continue

            total_files += 1
            filepath = os.path.join(year_dir, fname)

            # Extract date from filename: YYYYMMDDevents.txt
            date_match = re.match(r"(\d{8})events\.txt", fname)
            if not date_match:
                continue
            file_date = datetime.strptime(date_match.group(1), "%Y%m%d").date()

            try:
                with open(filepath, "r", errors="replace") as f:
                    content = f.read()
            except:
                continue

            # Look for XRA events with M or X class
            for line in content.split("\n"):
                # XRA events have format like:  "GO9  5   XRA  1-8A      M1.1    3.3E-03"
                if "XRA" in line and "1-8A" in line:
                    # Look for M or X class designation
                    # Pattern: class letter followed by number like M1.1, X2.3
                    class_match = re.search(r"\b(M|X)\d+\.?\d*\b", line)
                    if class_match:
                        flare_class = class_match.group(1)
                        if flare_class == "M":
                            m_days.add(file_date)
                        elif flare_class == "X":
                            x_days.add(file_date)

    print(f"  NOAA events: {total_files} files parsed, {len(m_days)} M-days, {len(x_days)} X-days ({start_year}-{end_year})")
    return m_days, x_days


def parse_dsd_flare_counts():
    """
    Parse DSD (Daily Solar Data) files to extract daily M/X flare counts.
    This serves as a cross-check/supplement for flare occurrence.
    The DSD files have columns including M and X flare counts per day.
    """
    dsd_dir = os.path.join(RAW, "swpc_forecasts")  # DSD files were saved here
    records = []

    for year in range(1996, 2025):
        filepath = os.path.join(dsd_dir, f"{year}_daypre.txt")
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r", errors="replace") as f:
            for line in f:
                line = line.strip()
                # Data lines start with a year: "1998 01 01  102 ..."
                match = re.match(r"(\d{4})\s+(\d{2})\s+(\d{2})\s+(.*)", line)
                if not match:
                    continue

                yr, mo, dy = int(match.group(1)), int(match.group(2)), int(match.group(3))
                rest = match.group(4)

                # Parse the remaining columns
                # Format: Radio Sunspot Area NewReg Field Flux C M X S 1 2 3
                parts = rest.split()
                if len(parts) >= 10:
                    try:
                        m_count = int(parts[7])  # M column
                        x_count = int(parts[8])  # X column
                        sunspot = int(parts[1])   # SESC Sunspot Number
                        records.append({
                            "date": datetime(yr, mo, dy).date(),
                            "m_count_dsd": m_count,
                            "x_count_dsd": x_count,
                            "sunspot_dsd": sunspot,
                        })
                    except (ValueError, IndexError):
                        pass

    df = pd.DataFrame(records)
    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"])
    print(f"  DSD records: {len(df)} days parsed")
    return df


def build_flare_labels():
    """
    Build unified binary flare labels following the paper's data source split:
    - NOAA SWPC event reports for 1996-2001
    - ASR catalog (v1.0, abs_class_simple) for 2002-2024

    This combination gives M=2018/X=254 for the eval period (paper: 2021/254).
    The small M discrepancy (~3 days) likely stems from NOAA event report parsing.
    """
    # Parse both sources
    print("\n--- Parsing ASR catalog ---")
    asr_m, asr_x = parse_asr_catalog()

    print("\n--- Parsing NOAA event reports (1996-2001) ---")
    noaa_m, noaa_x = parse_noaa_events(1996, 2001)

    print("\n--- Parsing DSD files ---")
    dsd_df = parse_dsd_flare_counts()

    # Build date range: Aug 1996 - Dec 2024
    all_dates = pd.date_range("1996-08-01", "2024-12-31", freq="D")

    records = []
    for date in all_dates:
        d = date.date()
        if d.year <= 2001:
            # Use NOAA events for 1996-2001
            m_label = 1 if d in noaa_m else 0
            x_label = 1 if d in noaa_x else 0
        else:
            # Use ASR catalog for 2002-2024
            m_label = 1 if d in asr_m else 0
            x_label = 1 if d in asr_x else 0

        records.append({"date": date, "m_label": m_label, "x_label": x_label})

    labels_df = pd.DataFrame(records)

    # Cross-check with DSD
    if len(dsd_df) > 0:
        merged = labels_df.merge(dsd_df, on="date", how="left")
        dsd_m = (merged["m_count_dsd"].fillna(0) > 0).astype(int)
        dsd_x = (merged["x_count_dsd"].fillna(0) > 0).astype(int)
        m_agree = (labels_df["m_label"] == dsd_m).mean()
        x_agree = (labels_df["x_label"] == dsd_x).mean()
        print(f"\n  DSD cross-check agreement: M={m_agree:.4f}, X={x_agree:.4f}")

        # Where primary source says no flare but DSD says yes (or vice versa)
        m_disagree = ((labels_df["m_label"] != dsd_m) & dsd_df["m_count_dsd"].notna().reindex(labels_df.index, fill_value=False)).sum()
        x_disagree = ((labels_df["x_label"] != dsd_x) & dsd_df["x_count_dsd"].notna().reindex(labels_df.index, fill_value=False)).sum()
        print(f"  Disagreements: M={m_disagree}, X={x_disagree}")

    # Count positive days in evaluation period
    eval_mask = labels_df["date"] >= "1998-01-01"
    eval_df = labels_df[eval_mask]
    print(f"\n  Labels built: {len(labels_df)} total days")
    print(f"  Evaluation period: {len(eval_df)} days")
    print(f"  M-class positive (eval): {eval_df['m_label'].sum()}")
    print(f"  X-class positive (eval): {eval_df['x_label'].sum()}")

    return labels_df


# ==========================================================================
# 3. Parse sunspot numbers
# ==========================================================================

def parse_sunspot_numbers():
    """Parse SILSO daily sunspot numbers."""
    path = os.path.join(RAW, "silso_daily_sunspot.csv")

    records = []
    with open(path, "r") as f:
        for line in f:
            parts = line.strip().split(";")
            if len(parts) >= 5:
                try:
                    yr = int(parts[0])
                    mo = int(parts[1])
                    dy = int(parts[2])
                    ssn = float(parts[4])
                    if ssn < 0:
                        ssn = np.nan  # Missing values are -1
                    records.append({
                        "date": datetime(yr, mo, dy).date(),
                        "sunspot_number": ssn,
                    })
                except (ValueError, IndexError):
                    pass

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    # Filter to relevant period
    df = df[(df["date"] >= "1996-01-01") & (df["date"] <= "2024-12-31")]
    print(f"  Sunspot numbers: {len(df)} days, {df['sunspot_number'].isna().sum()} missing")

    return df


# ==========================================================================
# 4. Merge everything and compute derived features
# ==========================================================================

def merge_all():
    """Merge forecasts, labels, and sunspot numbers into the evaluation dataset."""

    print("=" * 60)
    print("PARSING RAW DATA")
    print("=" * 60)

    # Parse RSGA forecasts
    print("\n--- Parsing RSGA forecast files ---")
    rsga_df = parse_rsga_files()
    forecasts_df = build_forecast_dataset(rsga_df)

    # Build flare labels
    labels_df = build_flare_labels()

    # Parse sunspot numbers
    print("\n--- Parsing sunspot numbers ---")
    sunspot_df = parse_sunspot_numbers()

    # Merge
    print("\n--- Merging datasets ---")
    merged = forecasts_df.merge(labels_df, on="date", how="inner")
    merged = merged.merge(sunspot_df, on="date", how="left")

    print(f"  Merged dataset: {len(merged)} days")

    # Also parse DSD for supplementary sunspot/flare info
    dsd_df = parse_dsd_flare_counts()
    if len(dsd_df) > 0:
        merged = merged.merge(dsd_df[["date", "sunspot_dsd"]], on="date", how="left")
        # Fill SILSO missing sunspots with DSD values where available
        missing_ssn = merged["sunspot_number"].isna()
        if missing_ssn.any() and "sunspot_dsd" in merged.columns:
            filled = merged.loc[missing_ssn, "sunspot_dsd"].notna().sum()
            merged.loc[missing_ssn, "sunspot_number"] = merged.loc[missing_ssn, "sunspot_dsd"]
            print(f"  Filled {filled} missing sunspot values from DSD")

    # Split into buffer and evaluation
    buffer_mask = (merged["date"] >= "1996-08-01") & (merged["date"] <= "1997-12-31")
    eval_mask = (merged["date"] >= "1998-01-01") & (merged["date"] <= "2024-12-31")

    buffer_df = merged[buffer_mask].copy()
    eval_df = merged[eval_mask].copy()

    print(f"\n  Buffer period: {len(buffer_df)} days ({buffer_df['date'].min()} to {buffer_df['date'].max()})")
    print(f"  Evaluation period: {len(eval_df)} days ({eval_df['date'].min()} to {eval_df['date'].max()})")

    # Compute derived features for the full dataset
    print("\n--- Computing derived features ---")
    merged = merged.sort_values("date").reset_index(drop=True)

    # x1: consecutive flare-free days (computed separately for M and X)
    m_consec = []
    x_consec = []
    m_count = 0
    x_count = 0
    for _, row in merged.iterrows():
        m_consec.append(m_count)
        x_consec.append(x_count)
        if row["m_label"] == 1:
            m_count = 0
        else:
            m_count += 1
        if row["x_label"] == 1:
            x_count = 0
        else:
            x_count += 1

    merged["m_consec_free"] = m_consec
    merged["x_consec_free"] = x_consec

    # x2: sunspot number (already in sunspot_number column)
    # Fill remaining NaN sunspot values with 0
    remaining_nan = merged["sunspot_number"].isna().sum()
    if remaining_nan > 0:
        print(f"  WARNING: {remaining_nan} days still have NaN sunspot numbers, filling with 0")
        merged["sunspot_number"] = merged["sunspot_number"].fillna(0)

    # Save full merged dataset
    save_path = os.path.join(PROC, "merged_dataset.csv")
    merged.to_csv(save_path, index=False)
    print(f"\n  Saved merged dataset: {save_path}")

    # Save evaluation-only dataset
    eval_full = merged[merged["date"] >= "1998-01-01"].copy()
    eval_path = os.path.join(PROC, "evaluation_dataset.csv")
    eval_full.to_csv(eval_path, index=False)
    print(f"  Saved evaluation dataset: {eval_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total merged days: {len(merged)}")
    print(f"Evaluation days: {len(eval_full)}")
    print(f"M-class positive (eval): {eval_full['m_label'].sum()} ({eval_full['m_label'].mean():.3f})")
    print(f"M-class negative (eval): {(eval_full['m_label'] == 0).sum()}")
    print(f"X-class positive (eval): {eval_full['x_label'].sum()} ({eval_full['x_label'].mean():.3f})")
    print(f"X-class negative (eval): {(eval_full['x_label'] == 0).sum()}")
    print(f"Forecast coverage (24h): {eval_full['m_24h'].notna().sum()} days with forecasts")
    print(f"Date range: {eval_full['date'].min()} to {eval_full['date'].max()}")

    return merged, eval_full


if __name__ == "__main__":
    merged, eval_df = merge_all()

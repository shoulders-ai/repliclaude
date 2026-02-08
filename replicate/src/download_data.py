"""
Data acquisition script for SWPC Solar Flare Forecast replication.
Downloads all 4 data sources to replicate/data/raw/.
"""

import os
import sys
import urllib.request
import urllib.error
import ftplib
import time

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def download_url(url, dest_path, description=""):
    """Download a file from HTTP/HTTPS URL."""
    print(f"  Downloading {description}: {url}")
    try:
        urllib.request.urlretrieve(url, dest_path)
        size = os.path.getsize(dest_path)
        print(f"  -> Saved to {dest_path} ({size:,} bytes)")
        return True
    except Exception as e:
        print(f"  -> FAILED: {e}")
        return False


def download_ftp_file(host, remote_path, local_path, description=""):
    """Download a single file from FTP."""
    try:
        with ftplib.FTP(host, timeout=30) as ftp:
            ftp.login()
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_path}', f.write)
        size = os.path.getsize(local_path)
        print(f"  -> {description}: {size:,} bytes")
        return True
    except Exception as e:
        print(f"  -> FAILED {description}: {e}")
        return False


def download_swpc_forecasts():
    """
    Download SWPC daily probabilistic forecast files from FTP.
    These are annual text files in the warehouse directory.
    We need years 1996-2024.
    """
    print("\n=== Source 1: SWPC Daily Probabilistic Forecasts ===")
    swpc_dir = os.path.join(RAW_DIR, "swpc_forecasts")
    os.makedirs(swpc_dir, exist_ok=True)

    host = "ftp.swpc.noaa.gov"
    success_count = 0
    fail_count = 0

    for year in range(1996, 2025):
        # The forecasts are in files like: /pub/warehouse/YYYY/daypre/YYYYDAYPRE.txt
        # or similar naming conventions. Let's try several patterns.
        patterns = [
            f"/pub/warehouse/{year}/daypre/{year}daypre.txt",
            f"/pub/warehouse/{year}/daypre/{year}DAYPRE.txt",
            f"/pub/warehouse/{year}/{year}_DSD.txt",
            f"/pub/warehouse/{year}/DSD.txt",
        ]

        local_path = os.path.join(swpc_dir, f"{year}_daypre.txt")
        if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
            print(f"  {year}: already downloaded, skipping")
            success_count += 1
            continue

        downloaded = False
        for pattern in patterns:
            if download_ftp_file(host, pattern, local_path, f"{year} forecast"):
                success_count += 1
                downloaded = True
                break
            time.sleep(0.5)

        if not downloaded:
            # Try listing the directory to find the right file
            print(f"  {year}: trying directory listing...")
            try:
                with ftplib.FTP(host, timeout=30) as ftp:
                    ftp.login()
                    # Try listing the year's warehouse directory
                    try:
                        entries = ftp.nlst(f"/pub/warehouse/{year}/")
                        daypre_entries = [e for e in entries if 'daypre' in e.lower() or 'DSD' in e.lower() or 'dsd' in e.lower()]
                        print(f"    Found in warehouse/{year}/: {daypre_entries[:5]}")
                    except:
                        pass

                    # Also try /pub/warehouse/{year}/daypre/
                    try:
                        entries = ftp.nlst(f"/pub/warehouse/{year}/daypre/")
                        print(f"    Found in warehouse/{year}/daypre/: {entries[:10]}")
                        # Download the first matching file
                        for entry in entries:
                            if entry.endswith('.txt'):
                                ftp2 = ftplib.FTP(host, timeout=30)
                                ftp2.login()
                                with open(local_path, 'wb') as f:
                                    ftp2.retrbinary(f'RETR {entry}', f.write)
                                ftp2.quit()
                                size = os.path.getsize(local_path)
                                print(f"    -> Downloaded: {entry} ({size:,} bytes)")
                                success_count += 1
                                downloaded = True
                                break
                    except Exception as e2:
                        print(f"    daypre subdir failed: {e2}")
            except Exception as e:
                print(f"    Listing failed: {e}")

            if not downloaded:
                fail_count += 1
                print(f"  {year}: ALL ATTEMPTS FAILED")

        time.sleep(0.3)

    print(f"\nSWPC forecasts: {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


def download_asr_catalog():
    """Download ASR flare catalog from GitHub."""
    print("\n=== Source 2: ASR Flare Catalog ===")
    url = "https://github.com/helio-unitov/ASR_cat/releases/download/v1.1/f_1995_2024.csv"
    dest = os.path.join(RAW_DIR, "asr_flare_catalog.csv")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  Already downloaded: {dest} ({os.path.getsize(dest):,} bytes)")
        return True
    return download_url(url, dest, "ASR flare catalog v1.1")


def download_noaa_event_reports():
    """
    Download NOAA SWPC event reports for 1996-2001.
    These are text files at ftp://ftp.swpc.noaa.gov/pub/indices/events/
    """
    print("\n=== Source 3: NOAA SWPC Event Reports (1996-2001) ===")
    events_dir = os.path.join(RAW_DIR, "noaa_events")
    os.makedirs(events_dir, exist_ok=True)

    host = "ftp.swpc.noaa.gov"

    # First, list the directory to understand the file naming
    print("  Listing /pub/indices/events/ to discover file format...")
    try:
        with ftplib.FTP(host, timeout=30) as ftp:
            ftp.login()
            entries = ftp.nlst("/pub/indices/events/")
            # Filter for files from 1996-2001
            relevant = [e for e in entries if any(str(y) in e for y in range(1996, 2002))]
            print(f"  Found {len(entries)} total entries, {len(relevant)} relevant (1996-2001)")
            if relevant:
                print(f"  Sample files: {relevant[:10]}")
    except Exception as e:
        print(f"  Listing failed: {e}")
        # Fall back to known patterns
        relevant = []

    # Download all event files for 1996-2001
    success = 0
    fail = 0

    if relevant:
        for entry in relevant:
            filename = os.path.basename(entry)
            local_path = os.path.join(events_dir, filename)
            if os.path.exists(local_path) and os.path.getsize(local_path) > 50:
                success += 1
                continue
            if download_ftp_file(host, entry, local_path, filename):
                success += 1
            else:
                fail += 1
            time.sleep(0.1)
    else:
        # Try known naming pattern: YYYYMMDD_events.txt or similar
        print("  Trying known patterns...")
        # Events are typically in files like: events/YYYYMMDD_events.txt
        # or the entire year might be in one file
        for year in range(1996, 2002):
            pattern = f"/pub/indices/events/{year}events.txt"
            local_path = os.path.join(events_dir, f"{year}events.txt")
            if download_ftp_file(host, pattern, local_path, f"{year} events"):
                success += 1
            else:
                fail += 1
            time.sleep(0.3)

    print(f"\nNOAA events: {success} succeeded, {fail} failed")
    return success, fail


def download_sunspot_numbers():
    """
    Download daily sunspot numbers from SILSO (Royal Observatory of Belgium).
    Assumption A1: Use SILSO as the standard source.
    """
    print("\n=== Source 4: SILSO Daily Sunspot Numbers ===")
    # SILSO provides daily total sunspot number
    url = "https://www.sidc.be/SILSO/INFO/sndtotcsv.php"
    dest = os.path.join(RAW_DIR, "silso_daily_sunspot.csv")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  Already downloaded: {dest} ({os.path.getsize(dest):,} bytes)")
        return True

    success = download_url(url, dest, "SILSO daily sunspot numbers")
    if not success:
        # Try alternative URL
        alt_url = "https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv"
        success = download_url(alt_url, dest, "SILSO daily sunspot (alt URL)")
    if not success:
        # Try another alternative
        alt_url2 = "http://www.sidc.be/silso/DATA/SN_d_tot_V2.0.csv"
        success = download_url(alt_url2, dest, "SILSO daily sunspot (alt URL 2)")
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("DATA ACQUISITION")
    print("=" * 60)

    # Source 1: SWPC forecasts
    swpc_ok, swpc_fail = download_swpc_forecasts()

    # Source 2: ASR catalog
    asr_ok = download_asr_catalog()

    # Source 3: NOAA event reports
    events_ok, events_fail = download_noaa_event_reports()

    # Source 4: Sunspot numbers
    sunspot_ok = download_sunspot_numbers()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"SWPC forecasts: {swpc_ok}/{swpc_ok + swpc_fail} years downloaded")
    print(f"ASR catalog: {'OK' if asr_ok else 'FAILED'}")
    print(f"NOAA events: {events_ok}/{events_ok + events_fail} files downloaded")
    print(f"Sunspot numbers: {'OK' if sunspot_ok else 'FAILED'}")

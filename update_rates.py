import urllib.request
import json
import csv
import datetime
import os

API_URL = "https://api.bnm.gov.my/public/exchange-rate"
HEADERS = {
    "Accept": "application/vnd.BNM.API.v1+json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

CSV_FILE = "FXrate.csv"

# The standard currency order in the CSV header
CURRENCIES = [
    "USD", "EUR", "JPY", "GBP", "SGD", "AUD", "CAD", "CNY", "CHF", "THB",
    "IDR", "VND", "KHR", "MMK", "PHP", "BND", "KRW", "HKD", "TWD", "INR",
    "PKR", "NPR", "SAR", "AED", "EGP", "NZD", "XDR"
]

def format_rate(rate_val):
    if rate_val is None:
        return ""
    # Format to 8 decimal places and strip trailing zeros/dot to avoid floating point anomalies
    s = f"{rate_val:.8f}".rstrip('0').rstrip('.')
    return s

def _read_existing_dates() -> set:
    """Read all dates already present in FXrate.csv."""
    existing = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if row:
                    existing.add(row[0].strip())
    return existing


def _find_last_csv_date(existing_dates: set) -> datetime.date | None:
    """Parse all D/M/YYYY date strings and return the most recent as a date."""
    parsed = []
    for d in existing_dates:
        try:
            parsed.append(datetime.datetime.strptime(d, "%d/%m/%Y").date())
        except ValueError:
            # Also try single-digit day/month format (e.g. 1/6/2025)
            try:
                parts = d.split("/")
                parsed.append(datetime.date(int(parts[2]), int(parts[1]), int(parts[0])))
            except (ValueError, IndexError):
                continue
    return max(parsed) if parsed else None


def _fetch_rates_for_date(target_date: datetime.date) -> list | None:
    """Fetch exchange-rate records from BNM API for a specific date.
    Returns the list of currency records, or None on failure / no data.
    """
    date_str = target_date.strftime("%Y-%m-%d")
    url = f"{API_URL}?date={date_str}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.getcode() != 200:
                return None
            body = response.read().decode("utf-8")
            data = json.loads(body)
            records = data.get("data", [])
            return records if records else None
    except Exception:
        return None


def _build_csv_row(csv_date_str: str, records: list) -> list:
    """Build a CSV row from BNM API records for a given date."""
    rate_map = {}
    for record in records:
        code = record.get("currency_code")
        if code:
            rate_map[code] = record

    new_row = [csv_date_str, "middle"]
    for col_currency in CURRENCIES:
        lookup_code = "SDR" if col_currency == "XDR" else col_currency
        entry = rate_map.get(lookup_code)

        rate_str = ""
        if entry:
            rate_info = entry.get("rate", {})
            middle_rate = rate_info.get("middle_rate")
            unit = entry.get("unit", 1)
            if middle_rate is not None:
                try:
                    normalized_rate = float(middle_rate) / float(unit)
                    rate_str = format_rate(normalized_rate)
                except (ValueError, TypeError) as e:
                    print(f"  Error processing rate for {lookup_code}: {e}")

        new_row.append(rate_str)
    return new_row


def _ensure_trailing_newline():
    """Make sure FXrate.csv ends with a newline before appending."""
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb+") as f:
            f.seek(0, 2)
            if f.tell() > 0:
                f.seek(-1, 2)
                if f.read(1) != b"\n":
                    f.write(b"\n")


def update_exchange_rates():
    import time

    print(f"Exchange rate source: BNM Open API ({API_URL})")

    # 1. Read existing dates and find the last one
    existing_dates = _read_existing_dates()
    last_date = _find_last_csv_date(existing_dates)
    today = datetime.date.today()

    if last_date is None:
        # No data at all — just fetch today's rate
        print("No existing dates found in CSV. Fetching today's rate only.")
        dates_to_fetch = [today]
    elif last_date >= today:
        print(f"CSV is already up-to-date (last entry: {last_date}). Nothing to fetch.")
        return
    else:
        # Build list of all missing dates from (last_date + 1) to today
        gap_days = (today - last_date).days
        dates_to_fetch = [last_date + datetime.timedelta(days=i) for i in range(1, gap_days + 1)]
        print(f"Last CSV date: {last_date}  |  Today: {today}  |  {len(dates_to_fetch)} day(s) to backfill")

    # 2. Fetch and append each missing date
    appended = 0
    skipped = 0

    _ensure_trailing_newline()

    for target_date in dates_to_fetch:
        csv_date_str = f"{target_date.day}/{target_date.month}/{target_date.year}"

        # Skip if already in CSV (safety check)
        if csv_date_str in existing_dates:
            continue

        records = _fetch_rates_for_date(target_date)
        if records is None:
            # No data for this date (weekend / public holiday / API issue)
            skipped += 1
            print(f"  {target_date}  — no data (weekend/holiday), skipped")
            continue

        new_row = _build_csv_row(csv_date_str, records)

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

        existing_dates.add(csv_date_str)
        appended += 1
        print(f"  {target_date}  — appended ✓")

        # Polite delay between API requests (avoid hammering the server)
        if len(dates_to_fetch) > 1:
            time.sleep(0.5)

    print(f"Exchange rates done: {appended} day(s) appended, {skipped} day(s) skipped (no data).")

def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def update_money_supply():
    excel_file = "Money supply.xlsx"
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    print(f"Loading {excel_file}...")
    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_file)
        ws = wb["1.3"]
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return

    # Find the last date in Excel
    last_row = ws.max_row
    current_year = None
    last_year = None
    last_month = None

    for row in range(10, last_row + 1):
        val_a = ws.cell(row=row, column=1).value
        val_b = ws.cell(row=row, column=2).value
        if val_a is not None:
            try:
                current_year = int(val_a)
            except:
                pass
        if val_b is not None:
            try:
                m = int(val_b)
                if current_year is not None:
                    last_year = current_year
                    last_month = m
            except:
                pass

    if last_year is None or last_month is None:
        print("Could not find the last date in the Excel file.")
        return

    print(f"Last date in Excel: Month {last_month}, Year {last_year}")

    # Fetch data from BNM API for last_year up to current system year
    current_system_year = datetime.datetime.now().year
    new_records = []

    for year in range(last_year, current_system_year + 1):
        url = f"https://api.bnm.gov.my/public/msb/1.3/year/{year}"
        print(f"Fetching money supply data from BNM API for year {year}: {url}")
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                status = response.getcode()
                if status != 200:
                    print(f"Failed to fetch year {year}. HTTP Status: {status}")
                    continue
                body = response.read().decode('utf-8')
                data = json.loads(body)
                records = data.get('data', [])
                new_records.extend(records)
        except Exception as e:
            print(f"Error fetching year {year}: {e}")
            continue

    # Filter and sort new records
    records_to_append = []
    for r in new_records:
        try:
            y = int(r.get('year_dt', 0))
            m = int(r.get('month_dt', 0))
        except (ValueError, TypeError):
            continue
            
        if y > last_year or (y == last_year and m > last_month):
            records_to_append.append((y, m, r))

    # Sort by year, then month
    records_to_append.sort(key=lambda x: (x[0], x[1]))

    if not records_to_append:
        print("No new money supply data found in the API compared to Excel. Skipping append.")
        return

    # Append to Excel
    for y, m, r in records_to_append:
        next_row = ws.max_row + 1
        # Col 1 (A): Year (only for January)
        ws.cell(row=next_row, column=1, value=y if m == 1 else None)
        # Col 2 (B): Month
        ws.cell(row=next_row, column=2, value=m)
        # Col 3 (C): None
        ws.cell(row=next_row, column=3, value=None)
        
        # Col 4-16 (D-P)
        ws.cell(row=next_row, column=4, value=safe_float(r.get('m_thr_tot')))
        ws.cell(row=next_row, column=5, value=safe_float(r.get('m_two_tot')))
        ws.cell(row=next_row, column=6, value=safe_float(r.get('m_one_tot')))
        ws.cell(row=next_row, column=7, value=safe_float(r.get('cur_in_cir')))
        ws.cell(row=next_row, column=8, value=safe_float(r.get('dem_dep')))
        ws.cell(row=next_row, column=9, value=safe_float(r.get('tot')))
        ws.cell(row=next_row, column=10, value=safe_float(r.get('nqm_sav_dep')))
        ws.cell(row=next_row, column=11, value=safe_float(r.get('nqm_fix_dep')))
        ws.cell(row=next_row, column=12, value=safe_float(r.get('nqm_nid')))
        ws.cell(row=next_row, column=13, value=safe_float(r.get('nqm_rep')))
        ws.cell(row=next_row, column=14, value=safe_float(r.get('nqm_for_cur_dep')))
        ws.cell(row=next_row, column=15, value=safe_float(r.get('nqm_oth_dep')))
        ws.cell(row=next_row, column=16, value=safe_float(r.get('dep_pla_oth_ban_ins')))
        
        print(f"Appended month {m}, year {y} to {excel_file}.")

    # Save workbook
    try:
        wb.save(excel_file)
        print(f"Successfully saved updates to {excel_file}.")
    except Exception as e:
        print(f"Error saving Excel file: {e}")

def main():
    print("=== STARTING DAILY EXCHANGE RATES UPDATE ===")
    update_exchange_rates()
    print("\n=== STARTING MONTHLY MONEY SUPPLY UPDATE ===")
    update_money_supply()
    print("=== ALL UPDATES COMPLETED ===")

if __name__ == "__main__":
    main()

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

def update_exchange_rates():
    print(f"Fetching exchange rates from BNM Open API: {API_URL}")
    req = urllib.request.Request(API_URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.getcode()
            if status != 200:
                print(f"Failed to fetch data. HTTP Status: {status}")
                return
            body = response.read().decode('utf-8')
            data = json.loads(body)
    except Exception as e:
        print(f"Error fetching rates from API: {e}")
        return

    # Check if we got data
    records = data.get('data', [])
    if not records:
        print("No exchange rate records found in the API response.")
        return

    # Find the date of the rates (use the first record's rate date)
    first_record = records[0]
    rate_date_str = first_record.get('rate', {}).get('date')
    if not rate_date_str:
        print("Could not determine the rate date from the API response.")
        return

    # Parse YYYY-MM-DD to D/M/YYYY
    try:
        dt = datetime.datetime.strptime(rate_date_str, "%Y-%m-%d")
        csv_date_str = f"{dt.day}/{dt.month}/{dt.year}"
    except Exception as e:
        print(f"Error parsing date '{rate_date_str}': {e}")
        return

    print(f"API Date: {rate_date_str} -> CSV Date: {csv_date_str}")

    # Read existing dates from FXrate.csv
    existing_dates = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            for row in reader:
                if row:
                    existing_dates.add(row[0].strip())

    if csv_date_str in existing_dates:
        print(f"Rates for date {csv_date_str} are already present in {CSV_FILE}. Skipping append.")
        return

    # Map currency code to API entry
    rate_map = {}
    for record in records:
        code = record.get('currency_code')
        if code:
            rate_map[code] = record

    # Build the new row starting with date and rate_type
    new_row = [csv_date_str, "middle"]

    for col_currency in CURRENCIES:
        # XDR in CSV header maps to SDR in BNM API
        lookup_code = "SDR" if col_currency == "XDR" else col_currency
        entry = rate_map.get(lookup_code)
        
        rate_str = ""
        if entry:
            rate_info = entry.get('rate', {})
            middle_rate = rate_info.get('middle_rate')
            unit = entry.get('unit', 1)
            
            if middle_rate is not None:
                try:
                    normalized_rate = float(middle_rate) / float(unit)
                    rate_str = format_rate(normalized_rate)
                except (ValueError, TypeError) as e:
                    print(f"Error processing rate for {lookup_code}: {e}")
        
        new_row.append(rate_str)

    # Append to CSV file safely ensuring trailing newline exists
    if os.path.exists(CSV_FILE):
        # Ensure file ends with newline
        with open(CSV_FILE, "rb+") as f:
            f.seek(0, 2)
            if f.tell() > 0:
                f.seek(-1, 2)
                if f.read(1) != b'\n':
                    f.write(b'\n')

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(new_row)
        print(f"Successfully appended rates for {csv_date_str} to {CSV_FILE}.")

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

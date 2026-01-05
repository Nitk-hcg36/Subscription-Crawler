import os
import time
import requests
import urllib3
import pandas as pd
import smartsheet

urllib3.disable_warnings()

def subs():
    # -----------------------
    # 1. Get data from Smartsheet Admin API
    # -----------------------
    BASE_URL = "https://admin.smartsheet.com/api/licensing/v1/plans/4168320/member-summary?period=RECON"

    HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Cookie": os.getenv("SMARTSHEET_COOKIE"),
        "Host": "admin.smartsheet.com",
        "Referer": "https://admin.smartsheet.com/true-up?tab=USERS_P2",
        "User-Agent": "Mozilla/5.0",
        "x-smar-xsrf-token": os.getenv("SMARTSHEET_XSRF_TOKEN")
    }

    resp = requests.get(BASE_URL, headers=HEADERS, verify=False)
    resp.raise_for_status()
    result = resp.json()
    data = pd.json_normalize(result)

    # -----------------------
    # 2. Filter relevant columns
    # -----------------------
    sheet_columns = [
        "usageStart", "usageEnd", "reconStart", "reconEnd",
        "lastCalculatedDate", "currencyCode", "reconDaysRemaining",
        "provisionalLicenses", "totalLicenses", "licensesUsed",
        "membersPurchased", "billableMembers", "skuName",
        "pendingSeatRequestsCount"
    ]

    df = data[[col for col in sheet_columns if col in data.columns]]

    # -----------------------
    # 3. Connect to Smartsheet
    # -----------------------
    SM_TOKEN = os.getenv("SM_TOKEN")
    SHEET_ID = int(os.getenv("SM_SHEET_ID"))

    ss_client = smartsheet.Smartsheet(SM_TOKEN)

    # Fetch sheet to get column IDs dynamically
    sheet = ss_client.Sheets.get_sheet(SHEET_ID)
    column_map = {col.title: col.id for col in sheet.columns}

    # -----------------------
    # 4. Prepare rows for Smartsheet
    # -----------------------
    rows = []
    for _, row in df.iterrows():
        sm_row = ss_client.models.Row()
        sm_row.to_top = True
        sm_row.cells = [
            ss_client.models.Cell(column_id=column_map[col], value=row[col])
            for col in df.columns if col in column_map
        ]
        rows.append(sm_row)

    # -----------------------
    # 5. Push rows in batches
    # -----------------------
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        response = ss_client.Sheets.add_rows(SHEET_ID, batch)
        print(f"Pushed rows {i+1} to {i+len(batch)}")

    print("✅ Data successfully pushed to Smartsheet!")

if __name__ == "__main__":
    subs()

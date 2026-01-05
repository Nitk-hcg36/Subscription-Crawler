import os
import pandas as pd
import requests
import urllib3
import smartsheet

urllib3.disable_warnings()

# Map your DataFrame column names to Smartsheet column titles
FIELD_MAP = {
    "usageStart": "usageStart",
    "usageEnd": "usageEnd",
    "reconStart": "reconStart",
    "reconEnd": "reconEnd",
    "lastCalculatedDate": "lastCalculatedDate",
    "currencyCode": "currencyCode",
    "reconDaysRemaining": "reconDaysRemaining",
    "provisionalLicenses": "provisionalLicenses",
    "totalLicenses": "totalLicenses",
    "licensesUsed": "licensesUsed",
    "membersPurchased": "membersPurchased",
    "billableMembers": "billableMembers",
    "skuName": "skuName",
    "pendingSeatRequestsCount": "pendingSeatRequestsCount"
}

def subs():
    # -----------------------
    # 1. Smartsheet Admin API URL
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
        "User-Agent": "Python script",
        "x-smar-xsrf-token": os.getenv("SMARTSHEET_XSRF_TOKEN")
    }

    resp = requests.get(BASE_URL, headers=HEADERS, verify=False)
    resp.raise_for_status()
    result = resp.json()

    # -----------------------
    # 2. Flatten JSON and select only needed columns
    # -----------------------
    data = pd.json_normalize(result)
    df = data[[col for col in FIELD_MAP.keys() if col in data.columns]]

    # -----------------------
    # 3. Initialize Smartsheet SDK
    # -----------------------
    SM_TOKEN = os.getenv("SM_TOKEN")        # GitHub secret
    SHEET_ID = int(os.getenv("SM_SHEET_ID"))  # GitHub secret

    ss_client = smartsheet.Smartsheet(SM_TOKEN)
    ss_client.errors_as_exceptions(True)

    # -----------------------
    # 4. Build rows using FIELD_MAP pattern
    # -----------------------
    sheet_info = ss_client.Sheets.get_sheet(SHEET_ID)
    col_map = {col.title: col.id for col in sheet_info.columns}

    rows = []
    for _, row in df.iterrows():
        sm_row = ss_client.models.Row()
        sm_row.to_top = True
        sm_row.cells = []

        for df_col, sm_col_title in FIELD_MAP.items():
            col_id = col_map.get(sm_col_title)
            if not col_id:
                continue  # Skip if column not found in sheet
            sm_row.cells.append(ss_client.models.Cell(column_id=col_id, value=row[df_col]))
        
        if sm_row.cells:
            rows.append(sm_row)

    # -----------------------
    # 5. Push rows in batches
    # -----------------------
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        ss_client.Sheets.add_rows(SHEET_ID, batch)
        print(f"Pushed rows {i+1} to {i+len(batch)}")

    print("Data successfully pushed to Smartsheet!")

# Execute
subs()

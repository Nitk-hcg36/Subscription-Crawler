import os
import pandas as pd
import requests
import urllib3
import smartsheet

urllib3.disable_warnings()

def subs():
    # Smartsheet Admin API URL to get subscription data
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

    # Fetch the data from Smartsheet Admin API
    resp = requests.get(BASE_URL, headers=HEADERS, verify=False)
    resp.raise_for_status()
    result = resp.json()

    # Flatten JSON
    data = pd.json_normalize(result)

    # Columns to push
    sheet_columns = [
        "usageStart", "usageEnd", "reconStart", "reconEnd",
        "lastCalculatedDate", "currencyCode", "reconDaysRemaining",
        "provisionalLicenses", "totalLicenses", "licensesUsed",
        "membersPurchased", "billableMembers", "skuName",
        "pendingSeatRequestsCount"
    ]
    df = data[[col for col in sheet_columns if col in data.columns]]

    # Smartsheet setup
    SM_TOKEN = os.getenv("SM_TOKEN")
    SHEET_ID = int(os.getenv("SM_SHEET_ID"))
    ss_client = smartsheet.Smartsheet(SM_TOKEN)
    ss_client.errors_as_exceptions(True)

    # Get columns from the sheet to map names to IDs
    sheet = ss_client.Sheets.get_sheet(SHEET_ID)
    col_map = {col.title: col.id for col in sheet.columns}

    # Prepare rows
    new_rows = []
    for _, row in df.iterrows():
        cells = []
        for col_name in df.columns:
            if col_name in col_map:
                cells.append({
                    "column_id": col_map[col_name],
                    "value": row[col_name]
                })
        if cells:
            new_rows.append({
                "to_top": True,
                "cells": cells
            })

    # Send rows in batches of 200
    batch_size = 200
    for i in range(0, len(new_rows), batch_size):
        batch = new_rows[i:i+batch_size]
        response = ss_client.Sheets.add_rows(SHEET_ID, batch)
        print(f"Pushed rows {i+1} to {i+len(batch)}")

    print("Data successfully pushed to Smartsheet!")

if __name__ == "__main__":
    subs()

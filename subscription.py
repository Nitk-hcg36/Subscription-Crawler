import requests
import urllib3
import pandas as pd
import os
import time

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

    resp = requests.get(BASE_URL, headers=HEADERS, verify=False)
    resp.raise_for_status()
    result = resp.json()

    # Flatten the JSON
    data = pd.json_normalize(result)

    # Map your DataFrame to the Smartsheet columns
    # Column names in your sheet
    sheet_columns = [
        "usageStart", "usageEnd", "reconStart", "reconEnd",
        "lastCalculatedDate", "currencyCode", "reconDaysRemaining",
        "provisionalLicenses", "totalLicenses", "licensesUsed",
        "membersPurchased", "billableMembers", "skuName",
        "pendingSeatRequestsCount"
    ]

    # Keep only the columns you need (if they exist in data)
    df = data[[col for col in sheet_columns if col in data.columns]]

    # Prepare Smartsheet API
    SMARTSHEET_TOKEN = os.getenv("SM_TOKEN")  # Create this secret in GitHub
    SHEET_ID = os.getenv("SM_SHEET_ID")       # Smartsheet sheet ID as secret

    smartsheet_url = f"https://api.smartsheet.com/2.0/sheets/{SHEET_ID}/rows"
    smartsheet_headers = {
        "Authorization": f"Bearer {SMARTSHEET_TOKEN}",
        "Content-Type": "application/json"
    }

    # Prepare rows for Smartsheet
    rows = []
    for _, row in df.iterrows():
        sm_row = {
            "toTop": True,   # append to top
            "cells": [{"columnId": col_id, "value": row[col]} for col, col_id in zip(df.columns, range(len(df.columns)))]
        }
        rows.append(sm_row)

    # Push rows in batches (Smartsheet allows max 500 per request)
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        response = requests.post(smartsheet_url, headers=smartsheet_headers, json={"rows": batch})
        response.raise_for_status()
        print(f"Pushed rows {i+1} to {i+len(batch)}")

    print("Data successfully pushed to Smartsheet!")

subs()

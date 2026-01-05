import requests
import urllib3
import pandas as pd
import time
import os

urllib3.disable_warnings()

def subs():
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
        "Sec-ch-ua": "Google Chrome;v=143, Chromium;v=143, Not A(Brand;v=24",
        "Sec-ch-ua-mobile":"?0",
        "Sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "x-smar-trace-id": "9818bad0-9040-4c8f-894e-72fecea97159",
        "x-smar-user-agent": "admin-center/data-client",
        "x-smar-xsrf-token": os.getenv("SMARTSHEET_XSRF_TOKEN")
    }
    resp = requests.get(BASE_URL, headers=HEADERS, verify=False)
    resp.raise_for_status()
    result=resp.json()
    data = pd.json_normalize(result)
    data.to_csv("C:/Users/nitk/OneDrive - Huron Consulting Group/Nitish Workspace/Code Base/User Roles and Reports/assets/Subscription.csv",index=False)

subs()


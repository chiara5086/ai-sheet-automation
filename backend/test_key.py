
import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

service_account_info = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not service_account_info:
    print("No GOOGLE_SERVICE_ACCOUNT_JSON found")
    exit(1)
try:
    info = json.loads(service_account_info)
    creds = service_account.Credentials.from_service_account_info(info)
    print("OK! Key is valid.")
except Exception as e:
    print("ERROR:", e)

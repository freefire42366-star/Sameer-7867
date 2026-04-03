from fastapi import FastAPI, Query
import requests
import hashlib

app = FastAPI()

# --- Configuration ---
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
# Pure stealth headers matching Garena MSDK
HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive"
}

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

# --- Helper 1: Get Verifier Token (Fixing OTP Verify) ---
def get_verifier(token, email, otp):
    url = f"{BASE_URL}/game/account_security/bind:verify_otp"
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "otp": otp
    }
    r = requests.post(url, data=data, headers=HEADERS)
    res = r.json()
    return res.get("verifier_token"), res

# --- Helper 2: Get Identity Token (Fixing Sec Code Verify) ---
def get_identity(token, sec_code):
    url = f"{BASE_URL}/game/account_security/bind:verify_identity"
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "secondary_password": sha256_hash(sec_code)
    }
    r = requests.post(url, data=data, headers=HEADERS)
    res = r.json()
    return res.get("identity_token"), res

# --- Endpoints ---

@app.get("/")
def home():
    return {"msg": "Sameer Garena API Fix", "status": "Ready"}

# 1. SEND OTP (BD Region Fixed)
@app.get("/api/send-otp")
def send_otp(access_token: str, email: str):
    url = f"{BASE_URL}/game/account_security/bind:send_otp"
    data = {
        "app_id": APP_ID,
        "access_token": access_token,
        "email": email,
        "locale": "en_BD", # Specifically for Bangladesh
        "region": "BD"
    }
    r = requests.post(url, data=data, headers=HEADERS)
    return r.json()

# 2. AUTO BIND/REBIND (The One-Step Fix)
@app.get("/api/bind")
def bind_process(access_token: str, email: str, otp: str, sec_code: str = None):
    # Step 1: OTP Verify karke Verifier Token lo
    v_token, v_res = get_verifier(access_token, email, otp)
    if not v_token:
        return {"error": "OTP Verification Failed", "garena_msg": v_res}

    # Case: REBIND (Email Change)
    if sec_code:
        # Identity Token lo background mein
        id_token, id_res = get_identity(access_token, sec_code)
        if not id_token:
            return {"error": "Identity (Sec Code) Failed", "garena_msg": id_res}
        
        # Final Change Request
        url = f"{BASE_URL}/game/account_security/bind:create_rebind_request"
        final_data = {
            "app_id": APP_ID,
            "access_token": access_token,
            "identity_token": id_token,
            "verifier_token": v_token,
            "email": email
        }
        r = requests.post(url, data=final_data, headers=HEADERS)
        return {"success": True, "type": "change_bind", "response": r.json()}

    # Case: NEW BIND (Pehli baar email lagana)
    else:
        url = f"{BASE_URL}/game/account_security/bind:create_bind_request"
        final_data = {
            "app_id": APP_ID,
            "access_token": access_token,
            "verifier_token": v_token,
            "email": email
        }
        r = requests.post(url, data=final_data, headers=HEADERS)
        return {"success": True, "type": "new_bind", "response": r.json()}

# 3. INFO CHECK
@app.get("/api/info")
def check_info(access_token: str):
    url = f"{BASE_URL}/game/account_security/bind:get_bind_info"
    params = {"app_id": APP_ID, "access_token": access_token}
    r = requests.get(url, params=params, headers=HEADERS)
    return r.json()

# 4. CANCEL REQUEST
@app.get("/api/cancel")
def cancel(access_token: str):
    url = f"{BASE_URL}/game/account_security/bind:cancel_request"
    data = {"app_id": APP_ID, "access_token": access_token}
    r = requests.post(url, data=data, headers=HEADERS)
    return r.json()

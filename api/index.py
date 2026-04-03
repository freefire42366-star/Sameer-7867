from fastapi import FastAPI, Query
import requests
import hashlib

app = FastAPI()

# Configuration
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip"
}

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

# --- Internal: Get Verifier Token (OTP verify karke) ---
def get_verifier(token, email, otp):
    data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=data, headers=HEADERS)
    return r.json().get("verifier_token"), r.json()

# --- Internal: Get Identity Token (Security Code se) ---
def get_identity(token, sec_code):
    data = {
        "app_id": APP_ID, 
        "access_token": token, 
        "secondary_password": sha256_hash(sec_code)
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=data, headers=HEADERS)
    return r.json().get("identity_token"), r.json()

# ---------------- ENDPOINTS ----------------

@app.get("/")
def root():
    return {"status": "Sameer Bind API Live", "server": "BD Optimized"}

# 1. SEND OTP (BD Region)
@app.get("/api/send-otp")
def send_otp(access_token: str, email: str):
    data = {
        "app_id": APP_ID, "access_token": access_token, "email": email,
        "locale": "en_BD", "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=data, headers=HEADERS)
    return r.json()

# 2. BIND / REBIND (The Main One-Step Endpoint)
@app.get("/api/bind")
def bind_logic(access_token: str, email: str, otp: str, sec_code: str = None):
    """
    Agar account par pehle se mail nahi hai, toh sirf email/otp bhejein.
    Agar mail badalna (Change) hai, toh sec_code bhi bhejein.
    """
    # Step A: Verifier Token nikalo (Har bind ke liye chahiye)
    v_token, v_res = get_verifier(access_token, email, otp)
    if not v_token:
        return {"success": False, "msg": "OTP Verification Failed", "garena_res": v_res}

    # Case 1: Rebind / Change Email (Identity Token required)
    if sec_code:
        id_token, id_res = get_identity(access_token, sec_code)
        if not id_token:
            return {"success": False, "msg": "Identity Verification Failed", "garena_res": id_res}
        
        # Final Rebind Call
        payload = {
            "app_id": APP_ID, "access_token": access_token,
            "identity_token": id_token, "verifier_token": v_token, "email": email
        }
        final = requests.post(f"{BASE_URL}/game/account_security/bind:create_rebind_request", data=payload, headers=HEADERS)
        return {"success": True, "type": "rebind", "res": final.json()}

    # Case 2: New Bind (First time binding)
    else:
        payload = {
            "app_id": APP_ID, "access_token": access_token,
            "verifier_token": v_token, "email": email
        }
        final = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=payload, headers=HEADERS)
        return {"success": True, "type": "new_bind", "res": final.json()}

# 3. CANCEL REQUEST
@app.get("/api/cancel")
def cancel(access_token: str):
    data = {"app_id": APP_ID, "access_token": access_token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:cancel_request", data=data, headers=HEADERS)
    return r.json()

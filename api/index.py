from fastapi import FastAPI, Request, Query
import requests
import hashlib

app = FastAPI()

# --- Garena BD Configuration (From your file) ---
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

# --- Internal Helpers ---

def fetch_identity_token(token, sec_code, headers):
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "secondary_password": sha256_hash(sec_code)
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=data, headers=headers).json()
    return r.get("identity_token"), r

def fetch_verifier_token(token, email, otp, headers):
    data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=data, headers=headers).json()
    return r.get("verifier_token"), r

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Sameer BD API Live", "mode": "AtoZ Garena Connected"}

# 1. SEND OTP (BD Locale/Region Fixed)
@app.get("/api/send-otp")
async def send_otp(access_token: str, email: str, request: Request):
    headers = get_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": access_token,
        "email": email,
        "locale": "en_BD", # Bangladesh Locale
        "region": "BD"      # Bangladesh Region
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    res = r.json()
    return {"success": res.get("result") == 0, "message": "OTP sent!" if res.get("result") == 0 else "Failed", "garena_res": res}

# 2. BIND NEW EMAIL (One-Step)
@app.get("/api/bind")
async def bind_email(access_token: str, email: str, otp: str, secondary_password: str, request: Request):
    headers = get_headers(request)
    
    # Get Verifier
    v_token, v_res = fetch_verifier_token(access_token, email, otp, headers)
    if not v_token: return {"success": False, "message": "OTP Invalid", "error": v_res}
    
    # Submit Bind
    data = {"app_id": APP_ID, "access_token": access_token, "verifier_token": v_token, "email": email}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=data, headers=headers)
    return {"success": r.json().get("result") == 0, "garena_res": r.json()}

# 3. CHANGE EMAIL (One-Step - Identity + Verifier Auto)
@app.get("/api/change-email-sec")
async def change_email(access_token: str, old_email: str, new_email: str, secondary_password: str, new_otp: str, request: Request):
    headers = get_headers(request)
    
    # 1. Get Identity Token
    id_token, id_res = fetch_identity_token(access_token, secondary_password, headers)
    if not id_token: return {"success": False, "message": "Sec Code Wrong", "error": id_res}
    
    # 2. Get Verifier for New Email
    v_token, v_res = fetch_verifier_token(access_token, new_email, new_otp, headers)
    if not v_token: return {"success": False, "message": "New OTP Invalid", "error": v_res}
    
    # 3. Final Rebind
    data = {
        "app_id": APP_ID, "access_token": access_token, 
        "identity_token": id_token, "verifier_token": v_token, "email": new_email
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_rebind_request", data=data, headers=headers)
    return {"success": r.json().get("result") == 0, "garena_res": r.json()}

# 4. UNBIND WITH SEC CODE
@app.get("/api/unbind-with-sec")
async def unbind(access_token: str, secondary_password: str, request: Request):
    headers = get_headers(request)
    id_token, id_res = fetch_identity_token(access_token, secondary_password, headers)
    if not id_token: return {"success": False, "error": id_res}
    
    data = {"app_id": APP_ID, "access_token": access_token, "identity_token": id_token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:unbind_identity", data=data, headers=headers)
    return {"success": r.json().get("result") == 0, "garena_res": r.json()}

# 5. CHECK BIND INFO
@app.get("/api/get-bind-info")
async def bind_info(access_token: str, request: Request):
    params = {"app_id": APP_ID, "access_token": access_token}
    r = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", params=params, headers=get_headers(request))
    res = r.json()
    return {"success": True, "current_email": res.get("email"), "raw": res}

# 6. GET PLATFORMS
@app.get("/api/get-platform")
async def platforms(access_token: str, request: Request):
    r = requests.get(f"{BASE_URL}/bind/app/platform/info/get", params={"access_token": access_token}, headers=get_headers(request))
    return {"success": True, "data": r.json()}

# 7. CANCEL REQUEST
@app.get("/api/cancel")
async def cancel(access_token: str, request: Request):
    r = requests.post(f"{BASE_URL}/game/account_security/bind:cancel_request", 
                      data={"app_id": APP_ID, "access_token": access_token}, headers=get_headers(request))
    return r.json()

# 8. LOGOUT (REVOKE)
@app.get("/api/revoke-access")
async def revoke(access_token: str, request: Request):
    r = requests.get(f"{BASE_URL}/oauth/logout", params={"access_token": access_token}, headers=get_headers(request))
    return {"success": True, "message": "Logged out"}

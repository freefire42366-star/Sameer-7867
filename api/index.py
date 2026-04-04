from fastapi import FastAPI, Query, Request
import requests
import hashlib
import json

app = FastAPI()

# --- Configuration (Uthaya gaya url.py se) ---
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
SEC_CODE = "123456" # Fixed as per request

def get_headers(request: Request):
    # Jo mobile link kholi hai uska User-Agent aur standard Garena headers
    user_agent = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

# --- Internal Helper: Automatic Identity Token ---
def get_auto_identity(token, headers):
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "secondary_password": sha256_hash(SEC_CODE)
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=data, headers=headers)
    return r.json().get("identity_token")

# --- ENDPOINTS ---

@app.get("/")
def health():
    return {"status": "Sameer BD Engine Live"}

# STEP 1: Request OTP (Naya Email Bind karne ke liye)
@app.get("/api/request")
async def request_bind(request: Request, token: str, email: str):
    headers = get_headers(request)
    
    # Check current status
    info_params = {"app_id": APP_ID, "access_token": token}
    info_res = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", params=info_params, headers=headers).json()
    
    # Send OTP specifically for BD region
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD", # BD Server
        "region": "BD"     # BD Region
    }
    
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    return {
        "account_status": info_res,
        "otp_response": r.json(),
        "msg": "Check your email for code"
    }

# STEP 2: Confirm Bind (Auto-Identity included)
@app.get("/api/confirm")
async def confirm_bind(request: Request, token: str, email: str, otp: str):
    headers = get_headers(request)
    
    # 1. Get Verifier Token from OTP
    v_data = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "otp": otp
    }
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")
    
    if not v_token:
        return {"error": "Invalid OTP or Token", "res": v_res}

    # 2. Get Identity Token (Auto-logic using 123456)
    id_token = get_auto_identity(token, headers)
    
    # 3. Final Binding / Rebinding logic
    # Agar account already bound hai toh rebind request chalegi
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token,
        "email": email
    }
    
    if id_token:
        payload["identity_token"] = id_token
        endpoint = "/game/account_security/bind:create_rebind_request"
    else:
        endpoint = "/game/account_security/bind:create_bind_request"
        
    final = requests.post(f"{BASE_URL}{endpoint}", data=payload, headers=headers)
    
    return {
        "status": "Success" if final.json().get("result") == 0 else "Failed",
        "garena_response": final.json(),
        "auto_identity_used": True if id_token else False
    }

@app.get("/api/cancel")
async def cancel_bind(request: Request, token: str):
    headers = get_headers(request)
    data = {"app_id": APP_ID, "access_token": token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:cancel_request", data=data, headers=headers)
    return r.json()

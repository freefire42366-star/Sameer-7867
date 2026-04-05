from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

# --- Full URLs from your BD Server List ---
URL_SEND_OTP   = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
URL_VERIFY_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
URL_BIND_REQ   = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"

APP_ID = "100067"
# Yeh security code set ho jayega binding ke sath
NEW_SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_msdk_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

@app.get("/")
def home():
    return {"msg": "Sameer Fresh-Bind Engine Active", "fix": "Secondary Password Injection"}

# ================= STEP 1: SEND OTP =================
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_msdk_headers(request)
    payload = {
        "app_id": APP_ID, 
        "access_token": token, 
        "email": email,
        "locale": "en_PK", 
        "region": "PK"
    }
    r = requests.post(URL_SEND_OTP, data=payload, headers=headers)
    return r.json()

# ================= STEP 2: CONFIRM NEW BIND =================
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_msdk_headers(request)
    
    # 1. OTP Verify karke Verifier Token nikalna
    v_payload = {
        "app_id": APP_ID, 
        "access_token": token, 
        "email": email, 
        "otp": otp
    }
    v_res = requests.post(URL_VERIFY_OTP, data=v_payload, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "OTP_INVALID", "garena_res": v_res}

    # 2. FRESH BIND PAYLOAD (As per Garena Protocol)
    # Garena fresh bind mein 'secondary_password' set karne ko bolta hai
    # Isko hash karke bhej rahe hain
    pw_hash = sha256_hash(NEW_SEC_CODE)
    
    final_payload = {
        "app_id": APP_ID,
        "access_token": token,
        "verifier_token": v_token,
        "email": email,
        "secondary_password": pw_hash # Yeh zaroori hai fresh bind ke liye
    }
    
    # Final Hit to create_bind_request
    final_r = requests.post(URL_BIND_REQ, data=final_payload, headers=headers)
    
    return {
        "status": "Process Finished",
        "action": "FRESH_NEW_BIND",
        "garena_raw": final_r.json()
    }

from fastapi import FastAPI, Request
import requests
import hashlib
import random
import string

app = FastAPI()

# --- FULL REAL URLS (Direct from your list) ---
URL_BIND_INFO = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
URL_SEND_OTP  = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
URL_VERIFY_OTP = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
URL_BIND_REQ  = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
URL_VERIFY_ID = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
URL_REBIND_REQ = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
URL_CANCEL_REQ = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"

APP_ID = "100067"
SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def generate_device_sig():
    """Asli Mobile jaisa random Device ID generate karna taaki block na ho"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

def get_stealth_headers(request: Request):
    """Anti-Captcha & Anti-Block Headers"""
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Garena-Device-ID": generate_device_sig(),
        "X-MSDK-Version": "4.0.39",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive",
        "Host": "100067.connect.garena.com"
    }

@app.get("/")
def home():
    return {"msg": "Sameer Full-URL Anti-Block Engine Active"}

# ================= STEP 1: SEND OTP (Using pk/en_pk) =================
@app.get("/api/request")
async def send_otp(token: str, email: str, request: Request):
    headers = get_stealth_headers(request)
    payload = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_PK", # Garena Protocol Standard
        "region": "PK"      # Garena Protocol Standard
    }
    
    r = requests.post(URL_SEND_OTP, data=payload, headers=headers)
    res = r.json()
    
    # Anti-Captcha Check
    if "captcha" in str(res).lower():
        return {"error": "BLOCK_DETECTED", "msg": "Wait 10 mins or change token", "raw": res}
    return res

# ================= STEP 2: CONFIRM (BIND/REBIND AUTO FIX) =================
@app.get("/api/confirm")
async def confirm(token: str, email: str, otp: str, request: Request):
    headers = get_stealth_headers(request)
    
    # 1. Pehle Verify OTP karke Verifier Token lo (verify_otp)
    v_data = {"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}
    v_res = requests.post(URL_VERIFY_OTP, data=v_data, headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        return {"error": "OTP_VERIFY_FAIL", "res": v_res}

    # 2. Check Account Status (Bind info)
    # Isse pata chalega ki identity_token bhejna hai ya nahi (To fix error_params)
    info = requests.get(URL_BIND_INFO, params={"app_id": APP_ID, "access_token": token}, headers=headers).json()
    is_already_bound = True if info.get("email") else False

    # 3. Final Decision Logic
    if not is_already_bound:
        # FRESH BIND (Direct hit create_bind_request)
        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "verifier_token": v_token,
            "email": email
        }
        final_r = requests.post(URL_BIND_REQ, data=final_payload, headers=headers)
        action = "NEW_BIND"
    else:
        # REBIND (Needs Identity Token from verify_identity)
        id_data = {
            "app_id": APP_ID,
            "access_token": token,
            "secondary_password": sha256_hash(SEC_CODE)
        }
        id_res = requests.post(URL_VERIFY_ID, data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")

        if not id_token:
            return {"error": "IDENTITY_FAIL", "msg": "Security code 123456 is wrong", "raw": id_res}

        final_payload = {
            "app_id": APP_ID,
            "access_token": token,
            "identity_token": id_token,
            "verifier_token": v_token,
            "email": email
        }
        final_r = requests.post(URL_REBIND_REQ, data=final_payload, headers=headers)
        action = "REBIND"

    return {
        "action": action,
        "garena_raw": final_r.json()
    }

@app.get("/api/cancel")
async def cancel(token: str, request: Request):
    headers = get_stealth_headers(request)
    r = requests.post(URL_CANCEL_REQ, data={"app_id": APP_ID, "access_token": token}, headers=headers)
    return r.json()

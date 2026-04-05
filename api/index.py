from fastapi import FastAPI, Request
import requests
import hashlib

app = FastAPI()

U1 = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
U2 = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
U3 = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
U4 = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
U5 = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
U6 = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
U7 = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
U8 = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
U9 = "https://100067.connect.garena.com/bind/app/platform/info/get"
U10 = "https://100067.connect.garena.com/oauth/logout"
U11 = "https://clientbp.ggwhitehawk.com/GetPlayerCSRankingInfoByAccountID"
U12 = "https://clientbp.ggwhitehawk.com/GetFriendRequestList"
U13 = "https://clientbp.ggwhitehawk.com/RequestAddingFriend"
U14 = "https://clientbp.ggwhitehawk.com/RemoveFriend"
U15 = "https://clientbp.ggwhitehawk.com/ConfirmFriendRequest"
U16 = "https://clientbp.ggwhitehawk.com/DeclineFriendRequest"
U17 = "https://100067.msdk.garena.com/api/msdk/v2/info/pricing"

AID = "100067"
RTK = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

def gh(request: Request):
    ua = request.headers.get("user-agent", "GarenaMSDK/4.0.39 (M2007J22C; Android 10; en; US;)")
    return {"User-Agent": ua, "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}

def hs(s: str):
    return hashlib.sha256(s.encode()).hexdigest()

@app.get("/")
async def root():
    return {"status": "Sameer Supreme Engine Online", "folder": "api/"}

@app.get("/api/request")
async def req_otp(token: str, email: str, request: Request):
    p = {"app_id": AID, "access_token": token, "email": email, "locale": "en_PK", "region": "PK"}
    r = requests.post(U2, data=p, headers=gh(request))
    return r.json()

@app.get("/api/confirm-new")
async def bind_new(token: str, email: str, otp: str, sc: str = "123456", request: Request):
    h = gh(request)
    v_res = requests.post(U3, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v_res.get("verifier_token")
    if not vt: return {"status": "ERROR", "res": v_res}
    p = {"app_id": AID, "access_token": token, "verifier_token": vt, "email": email, "secondary_password": hs(sc)}
    r = requests.post(U4, data=p, headers=h)
    return r.json()

@app.get("/api/rebind")
async def bind_change(token: str, email: str, otp: str, sc: str, request: Request):
    h = gh(request)
    v_res = requests.post(U3, data={"app_id": AID, "access_token": token, "email": email, "otp": otp}, headers=h).json()
    vt = v_res.get("verifier_token")
    i_res = requests.post(U5, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i_res.get("identity_token")
    if not vt or not it: return {"status": "FAIL", "vt": v_res, "it": i_res}
    p = {"app_id": AID, "access_token": token, "identity_token": it, "verifier_token": vt, "email": email}
    r = requests.post(U6, data=p, headers=h)
    return r.json()

@app.get("/api/unbind")
async def unbind(token: str, sc: str, request: Request):
    h = gh(request)
    i_res = requests.post(U5, data={"app_id": AID, "access_token": token, "secondary_password": hs(sc)}, headers=h).json()
    it = i_res.get("identity_token")
    if not it: return i_res
    r = requests.post(U7, data={"app_id": AID, "access_token": token, "identity_token": it}, headers=h)
    return r.json()

@app.get("/api/info")
async def info(token: str, request: Request):
    h = gh(request)
    b = requests.get(U1, params={"app_id": AID, "access_token": token}, headers=h).json()
    r = requests.get(U11, params={"access_token": token}, headers=h).json()
    return {"account": r, "bind": b}

@app.get("/api/friends")
async def friends(token: str, mode: str, target: str = None, request: Request):
    h = gh(request)
    u_m = {"list": U12, "add": U13, "remove": U14, "accept": U15, "decline": U16}
    url = u_m.get(mode)
    if not url: return {"err": "invalid mode"}
    p = {"access_token": token}
    if target: p["target_account_id"] = target
    r = requests.get(url, params=p, headers=h)
    return r.json()

@app.get("/api/utils")
async def utils(token: str, type: str, request: Request):
    h = gh(request)
    if type == "plat": return requests.get(U9, params={"access_token": token}, headers=h).json()
    if type == "topup": return requests.get(U17, params={"access_token": token}, headers=h).json()
    if type == "cancel": return requests.post(U8, data={"app_id": AID, "access_token": token}, headers=h).json()
    return {"err": "invalid"}

@app.get("/api/convert")
async def conv(eat: str):
    return {"url": f"https://api-otrss.garena.com/support/callback/?access_token={eat}"}

@app.get("/api/revoke")
async def revoke(token: str, request: Request):
    r = requests.get(U10, params={"access_token": token, "refresh_token": RTK}, headers=gh(request))
    return {"res": r.text}

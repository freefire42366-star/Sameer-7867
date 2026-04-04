from fastapi import FastAPI, Query
import requests

app = FastAPI()

# --- 5SIM CONFIGURATION ---
API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MDY4MTUxMTEsImlhdCI6MTc3NTI3OTExMSwicmF5IjoiYzAzMmE4NDY5ZmIxNjQ4NDBmYjRiZGZiMzRhZDVjOTgiLCJzdWIiOjM5Mzc2NzJ9.ht2w7toffecDHaxtKOsb8jRuzJgKGzFLeyzty1c6VQrTztD4mDbZkBOVrC4ZdEAoecHnhFffTYvrjq_ZwpNLRoNy9FihaDo1Ij3y3YMrszFhL83olx61STbA4EYKsqkdfgZ9wYMxyjK6WYNnML4cLDQHs-tHC1gah4NGoOhv6Sd_HdjS57qnVNZtT8aG6C_ioDTqvjjOYuWSs4ER3D4atxngp-nZpMrzBeVyDGOf6q_9K-DeVpkKwNRbZbEzCc6QVhvRMhuaZFXg0E7GT663iAae9S-X73c1KGDy5iwCq0xtYB32EZ8u8qUR6yiq4Ub5bAQOuAp1gtgJYx3oe6A7jg"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

@app.get("/")
def home():
    return {"status": "Sameer 5sim API Active"}

# 1. Buy Number (India/Nepal logic)
@app.get("/api/buy")
def buy_number(country: str = "india", operator: str = "any"):
    # Garena service code in 5sim is 'opt29'
    url = f"https://5sim.net/v1/user/buy/activation/{country}/{operator}/opt29"
    r = requests.get(url, headers=HEADERS)
    return r.json()

# 2. Check SMS (OTP nikalne ke liye)
@app.get("/api/check")
def check_sms(order_id: str):
    url = f"https://5sim.net/v1/user/check/{order_id}"
    r = requests.get(url, headers=HEADERS)
    return r.json()

# 3. Cancel/Finish Order
@app.get("/api/finish")
def finish(order_id: str):
    requests.get(f"https://5sim.net/v1/user/finish/{order_id}", headers=HEADERS)
    return {"status": "finished"}

@app.get("/api/cancel")
def cancel(order_id: str):
    requests.get(f"https://5sim.net/v1/user/cancel/{order_id}", headers=HEADERS)
    return {"status": "cancelled"}

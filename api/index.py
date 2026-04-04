from fastapi import FastAPI, Query
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI()

def get_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

@app.get("/")
def home():
    return {"msg": "Sameer Free SMS API Active"}

# 1. Get Free Numbers List
@app.get("/api/list")
def list_numbers(country: str = "india"):
    # Mapping countries to site paths
    paths = {"india": "India", "usa": "United-States", "uk": "United-Kingdom"}
    c_path = paths.get(country.lower(), "India")
    
    url = f"https://receive-sms-free.cc/Free-{c_path}-Phone-Number/"
    try:
        r = requests.get(url, headers=get_headers())
        soup = BeautifulSoup(r.text, 'html.parser')
        # Numbers are in specific class
        num_blocks = soup.find_all('div', class_='number-boxes-item')
        
        results = []
        for block in num_blocks:
            number = block.find('h4').text.strip()
            href = block.find('a').get('href')
            results.append({"number": number, "url": f"https://receive-sms-free.cc{href}"})
        return {"status": "success", "numbers": results}
    except:
        return {"status": "error", "msg": "Site unreachable"}

# 2. Get Messages (OTP)
@app.get("/api/otp")
def get_otp(url: str):
    try:
        r = requests.get(url, headers=get_headers())
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('div', class_='messagesTableLayout')
        
        messages = []
        for row in rows[:5]:
            sender = row.find('div', class_='msg-from').text.strip()
            text = row.find('div', class_='msg-text').text.strip()
            time = row.find('div', class_='msg-time').text.strip()
            messages.append({"from": sender, "text": text, "time": time})
        return {"status": "success", "messages": messages}
    except:
        return {"status": "error"}

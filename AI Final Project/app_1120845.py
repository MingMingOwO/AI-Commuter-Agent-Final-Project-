from flask import Flask, render_template
import requests
from datetime import datetime

# 初始化 Flask 網站 (期末專案 - 學號 1120845)
app = Flask(__name__)

# ==========================================
# 填寫你的 API 金鑰
# ==========================================
TDX_ID = 's1120845-45bf3bad-1273-4512'
TDX_KEY = '6f8039bf-ceef-4b78-8187-cd7b77314b9f'
CWA_KEY = 'CWA-4E06F20D-A591-445B-9298-A0F5E5D54E7F'

# 🌟 記得換成你申請到的真實 Gemini API Key
GEMINI_KEY = 'AIzaSyDt2YGOxbFcqdtxFQrNI_3CKbEU_rwepIs'

def get_weather():
    """去氣象署抓新北市的天氣"""
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={CWA_KEY}&locationName=新北市"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        loc = data['records']['location'][0]
        if loc['locationName'] == '新北市':
            wx = loc['weatherElement'][0]['time'][0]['parameter']['parameterName']
            min_temp = loc['weatherElement'][2]['time'][0]['parameter']['parameterName']
            max_temp = loc['weatherElement'][4]['time'][0]['parameter']['parameterName']
            return f"{wx}, {min_temp}°C - {max_temp}°C"
    except:
        pass
    return "天氣晴朗"

def get_train_schedule(token):
    """去 TDX 抓樹林到內壢的火車時刻表 (只抓現在時間之後的車)"""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M") # 拿到現在的幾點幾分，例如 "06:42"
    
    url = f"https://tdx.transportdata.tw/api/basic/v2/Rail/TRA/DailyTimetable/OD/0970/to/1070/{today}?$format=JSON"
    headers = {"authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        future_trains = []
        for t in data:
            dept_time = t['OriginStopTime']['DepartureTime']
            # 如果火車發車時間 >= 現在時間，才把它加進名單
            if dept_time >= current_time:
                future_trains.append({
                    'train_no': t['DailyTrainInfo']['TrainNo'], 
                    'dept_time': dept_time,
                    'arr_time': t['DestinationStopTime']['ArrivalTime']
                })
                
        # 只抓還沒開走的 前 5 班車
        return future_trains[:5]
    except:
        return []

def get_random_words():
    """請 Gemini 隨機給我們 10 個英文單字"""
    print("🤖 正在呼叫 Gemini AI 抓 10 個單字...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        # 讓 AI 隨機給 10 個單字，不看天氣了
        prompt = "請隨機給我 10 個英文單字。嚴格按照「英文單字,中文意思」的格式回傳，每一個單字換一行。例如：\nApple,蘋果\nBanana,香蕉\n不要有任何其他廢話或標記符號。"
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if 'error' in data:
            return [{"en": "Error", "zh": "AI 被擋住了"}]
            
        # 把 AI 回傳的一大串字抓出來
        ai_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        ai_text = ai_text.replace('，', ',') 
        
        # 用「換行」把 10 個單字切開變成一個清單
        lines = ai_text.split('\n')
        word_list = []
        
        # 把每一行的英文和中文分開，存進清單裡
        for line in lines:
            if ',' in line:
                parts = line.split(',')
                word_list.append({"en": parts[0].strip(), "zh": parts[1].strip()})
        
        # 如果成功抓到，就回傳；如果失敗，至少給一個錯誤提示
        if len(word_list) > 0:
            return word_list[:10] # 確保最多只回傳 10 個
        else:
            return [{"en": "Oops", "zh": "AI 忘記格式了"}]
            
    except Exception as e:
        print("❌ 連線失敗：", e)
        return [{"en": "Offline", "zh": "網路沒開"}]

@app.route('/')
def home():
    print("🚀 啟動通勤小幫手...")
    
    # 跟 TDX 拿通行證 (Token)
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    try:
        token_res = requests.post(auth_url, headers={'content-type': 'application/x-www-form-urlencoded'}, 
                                  data={'grant_type': 'client_credentials', 'client_id': TDX_ID, 'client_secret': TDX_KEY})
        token = token_res.json().get('access_token')
    except:
        token = None
    
    # 開始抓資料
    trains = get_train_schedule(token) if token else []
    weather = get_weather()
    ai_words = get_random_words() # 這裡改成抓 10 個隨機單字的函數
    
    # 把變數通通丟給網頁顯示
    return render_template('index_1120845.html', train_data=trains, weather=weather, words=ai_words)

if __name__ == '__main__':
    app.run(debug=True)
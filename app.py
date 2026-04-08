import os
import re
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

GEN_API_KEY = "AIzaSyDhavsAYs_0sLGvLGRqpeptk_sdxSAiHNc"
GROUP_ID = 34390657
MODEL_NAME = "gemini-1.5-flash" 

def get_roblox_user_info(input_text):
    try:
        user_id = "".join(re.findall(r'\d+', str(input_text)))
        if not user_id: return None, None
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(f"https://users.roblox.com/v1/users/{user_id}", headers=headers, timeout=10)
        if res.status_code == 200:
            return user_id, res.json().get("name")
        return None, None
    except: return None, None

def get_thai_rank(user_id):
    try:
        res = requests.get(f"https://groups.roblox.com/v1/users/{user_id}/groups/roles", timeout=10)
        if res.status_code == 200:
            user_groups = res.json().get("data", [])
            for g in user_groups:
                if g.get("group", {}).get("id") == GROUP_ID:
                    role_name = g.get("role", {}).get("name", "")
                    thai_only = " ".join(re.findall(r'[\u0e00-\u0e7f]+', role_name)).strip()
                    return thai_only if thai_only else "พลเมือง"
        return "พลเมือง"
    except: return "พลเมือง"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    uid, uname = get_roblox_user_info(data.get("link", ""))
    if uname:
        rank = get_thai_rank(uid)
        return jsonify({"status": "success", "username": uname, "rank": rank})
    return jsonify({"status": "error", "message": "ไม่พบข้อมูลผู้ใช้ โปรดตรวจสอบไอดีหรือลิงก์"}), 400

@app.route('/ask', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get("question", "")
    username = data.get("username", "Unknown")
    rank = data.get("rank", "พลเมือง")

    # 🌟 ปรับ Prompt ให้ฉลาดขึ้น ดักจับคำถามนอกเรื่อง
    prompt = f"""
    คุณคือผู้เชี่ยวชาญกฎหมายทหาร สำนักงานพระธรรมนูญ
    กำลังพิจารณาคดีของ: {rank} {username}
    เหตุการณ์ที่รายงาน: {question}
    
    คำสั่งการตอบ:
    1. หากเหตุการณ์นี้ "ไม่เกี่ยวข้องกับการทหาร กฎหมาย ระเบียบ หรือเป็นคำถามกวนๆ / เรื่องส่วนตัว" (เช่น อยากมีแฟน, หิวข้าว, ทำไงดี) ให้ตอบสั้นๆ ว่า: "⚖️ ศาลทหารไม่รับพิจารณาคดี: เรื่องนี้ไม่อยู่ในเขตอำนาจของศาลทหาร" (ห้ามวิเคราะห์มาตราเด็ดขาด)
    2. หากเป็นเรื่องที่เข้าข่ายความผิด ให้ตอบ 3 หัวข้อ: 1.วิเคราะห์เหตุการณ์ 2.มาตราที่เกี่ยวข้อง 3.บทลงโทษ
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEN_API_KEY}"
    
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        result = response.json()
        
        # ถ้าระบบ API แจ้ง Error โควตา
        if 'error' in result:
            return jsonify({"status": "error", "message": "ศาลทหารปิดทำการชั่วคราว (มีผู้ใช้งานเยอะเกินไป โปรดรอ 1 นาที)"})

        if 'candidates' in result:
            answer = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"status": "success", "answer": answer})
        
        return jsonify({"status": "error", "message": "คำร้องถูกปฏิเสธ (เนื้อหาอาจมีคำที่ไม่เหมาะสม)"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "ระบบศาลขัดข้อง ไม่สามารถเชื่อมต่อฐานข้อมูลได้"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
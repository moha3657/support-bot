import os
from flask import Flask, request, jsonify
from openai import OpenAI
import requests

app = Flask(__name__)

# المتغيرات السرية ستضعها في إعدادات Vercel لاحقاً
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY, 
)

MODEL_ID = "nvidia/nemotron-3-ultra-550b-a55b:free"

BUSINESS_CONTEXT = """
أنت موظف خدمة عملاء ذكي، مهذب وسريع البديهة تعمل لدى متجر 'عالم القهوة'.

معلومات المتجر:
- أوقات العمل: من 8 صباحاً حتى 10 مساءً يومياً.
- العنوان: الرياض، حي التحلية.
- المنتجات والأسعار:
  1. قهوة كولومبية (250 جرام) - 60 ريال.
  2. قهوة إثيوبية مختصة (250 جرام) - 50 ريال.
  3. آلة تحضير الإسبريسو - 500 ريال.
- سياسة الاسترجاع: يمكن استرجاع المنتجات المغلفة خلال 7 أيام من تاريخ الشراء.
- التوصيل: متاح لجميع المدن بـ 30 ريال، ومجاني للطلبات التي تتجاوز 200 ريال.

التعليمات الصارمة لك:
- أجب فقط بناءً على المعلومات المذكورة أعلاه.
- إذا سألك العميل عن شيء غير موجود في هذه المعلومات، اعتذر بلطف وأخبره أنه سيتم تحويله لموظف بشري.
- إجاباتك يجب أن تكون قصيرة، ودودة، وباللغة العربية.
"""

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.route('/', methods=['GET'])
def home():
    return "🚀 Bot is running on Vercel!"

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    # هذا الرابط سيتم استدعاؤه لربط تيليجرام بالسيرفر الخاص بك
    webhook_url = request.host_url + TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
    response = requests.get(url)
    return jsonify(response.json())

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    # هنا يستقبل السيرفر الرسائل من تيليجرام
    update = request.get_json()
    
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"]
        
        messages = [
            {"role": "system", "content": BUSINESS_CONTEXT},
            {"role": "user", "content": user_text}
        ]
        
        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages
            )
            reply = response.choices[0].message.content
            send_message(chat_id, reply)
            
        except Exception as e:
            send_message(chat_id, "عذراً، أواجه مشكلة تقنية، حاول بعد قليل.")
            print(f"Error: {e}")
            
    return "OK", 200

# لا نحتاج لـ app.run() لأن Vercel سيدير ذلك

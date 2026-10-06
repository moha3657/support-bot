import os
from flask import Flask, request, jsonify
from openai import OpenAI
import requests

app = Flask(__name__)

def get_client():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)

MODEL_ID = "thinkingmachines/inkling-small:free"

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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.route('/', methods=['GET'])
def home():
    return "🚀 Bot is running on Vercel!"

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return jsonify({
            "error": "المفاتيح السرية غير موجودة!",
            "solution": "يرجى التأكد من إضافة TELEGRAM_BOT_TOKEN في إعدادات Environment Variables في Vercel، ثم عمل Redeploy."
        }), 400
        
    webhook_url = request.host_url + token
    url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    response = requests.get(url)
    return jsonify(response.json())

@app.route(f'/<path:token>', methods=['POST'])
def webhook(token):
    real_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token != real_token:
        return "Unauthorized", 401
        
    update = request.get_json()
    
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"]
        
        client = get_client()
        if not client:
            send_message(chat_id, "أنا أعمل، لكن صاحبي نسي إضافة مفتاح OPENROUTER_API_KEY في Vercel! 😅")
            return "OK", 200
            
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

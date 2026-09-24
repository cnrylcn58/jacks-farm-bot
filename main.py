import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GAME_URL = os.environ.get("GAME_URL", "")

def send_telegram_message(message):
    print(f"[LOG]: {message}")
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            res = requests.post(url, data=data, timeout=10)
            print(f"[TELEGRAM API]: {res.status_code}")
        except Exception as e:
            print(f"[TELEGRAM HATA]: {e}")

def run():
    send_telegram_message("🤖 Çiftlik Botu çalışmaya başladı.")
    
    if not GAME_URL:
        send_telegram_message("⚠️ GAME_URL bulunamadı, lütfen Secrets ayarlarını kontrol edin.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 390, 'height': 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            )
            page = context.new_page()
            
            print(f"Sohbet penceresine gidiliyor: {GAME_URL}")
            page.goto(GAME_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(5000)
            
            # Sol alttaki 'Open' butonuna tıklama işlemi
            print("Open butonuna tıklanıyor...")
            opened = False
            for selector in ["button:has-text('Open')", "button:has-text('Oyna')", ".chat-input-control-button"]:
                try:
                    if page.is_visible(selector):
                        page.click(selector)
                        opened = True
                        print(f"Buton bulundu ve tıklandı: {selector}")
                        break
                except:
                    continue
            
            if not opened:
                send_telegram_message("⚠️ 'Open' butonu ekranda bulunamadı. Oturum açık olmayabilir.")
                browser.close()
                return

            print("Oyunun yüklenmesi bekleniyor...")
            page.wait_for_timeout(10000)
            
            # Depo & Satış Tıklamaları (Sağdaki depo alanı)
            print("Depoya tıklanıyor...")
            page.mouse.click(320, 420)
            page.wait_for_timeout(3000)
            
            print("Satış butonuna tıklanıyor...")
            page.mouse.click(200, 280)
            page.wait_for_timeout(3000)
            
            send_telegram_message("✅ Depodaki ürünler toplandı ve satıldı!")
            browser.close()
            
    except Exception as e:
        send_telegram_message(f"❌ İşlem sırasında hata oluştu: {str(e)}")

if __name__ == "__main__":
    run()

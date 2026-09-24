import os
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Oyunun WebApp / Launch URL adresini buraya ekleyebilirsin
GAME_URL = os.environ.get("GAME_URL", "")

def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Telegram mesajı gönderilemedi: {e}")

def run():
    print("Bot başlatılıyor...")
    send_telegram_message("🤖 Çiftlik Botu çalışmaya başladı.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        
        if GAME_URL:
            print(f"Oyuna bağlanılıyor: {GAME_URL}")
            page.goto(GAME_URL)
            page.wait_for_timeout(10000)
            
            # Depo butonuna tıklama (Koordinat veya Selector ile)
            # Sağ ortadaki depo alanına tıklama simülasyonu
            print("Depoya ürünler aktarılıyor...")
            page.mouse.click(320, 420)
            page.wait_for_timeout(3000)
            
            # Satış/Kamyon alanına tıklama
            print("Satış işlemi yapılıyor...")
            page.mouse.click(200, 280)
            page.wait_for_timeout(3000)
            
            send_telegram_message("✅ Depo boşaltıldı ve ürünler satıldı!")
        else:
            print("GAME_URL tanımlanmamış.")
            send_telegram_message("⚠️ GAME_URL eksik, lütfen Secrets alanına ekleyin.")
            
        browser.close()

if __name__ == "__main__":
    run()

import os
import time
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GAME_URL = os.environ.get("GAME_URL", "")

def send_telegram_message(message):
    """Telegram'a metin bildirimi gönderir."""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Telegram mesajı gönderilemedi: {e}")

def send_telegram_photo(photo_path, caption=""):
    """Telegram'a ekran görüntüsü gönderir."""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and os.path.exists(photo_path):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        try:
            with open(photo_path, "rb") as photo:
                requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"photo": photo})
        except Exception as e:
            print(f"Telegram fotoğrafı gönderilemedi: {e}")

def run():
    print("Bot başlatılıyor...")
    send_telegram_message("🤖 Çiftlik Botu çalışmaya başladı.")
    
    if not GAME_URL:
        print("GAME_URL tanımlanmamış.")
        send_telegram_message("⚠️ GAME_URL eksik, lütfen Secrets alanına ekleyin.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 390, 'height': 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            )
            page = context.new_page()
            
            print(f"Oyuna bağlanılıyor: {GAME_URL}")
            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Oyun ögelerinin tam yüklenmesi için bekleme
            page.wait_for_timeout(10000)
            
            # Başlangıçta Farm sekmesine geçerek ekranı sıfırla
            print("Ana çiftlik ekranına geçiliyor...")
            page.mouse.click(365, 180, delay=100)
            page.wait_for_timeout(2000)

            # 1. ADIM: Warehouse (Depo) binasına tıklama
            print("Warehouse binasına tıklanıyor...")
            page.mouse.click(280, 290, delay=100)
            page.wait_for_timeout(3000)
            
            # 2. ADIM: Mavi 'Send products' butonuna tıklama (Hizalı koordinat)
            print("Send products butonuna basılıyor...")
            page.mouse.click(190, 560, delay=100)
            page.wait_for_timeout(3000)
            
            # 3. ADIM: Depo penceresini kırmızı X butonuyla kapatma
            print("Depo penceresi kapatılıyor...")
            page.mouse.click(345, 215, delay=100)
            page.wait_for_timeout(2000)
            
            # Sağ menünün en üstündeki Farm butonuna basarak kesin dönüş sağla
            page.mouse.click(365, 180, delay=100)
            page.wait_for_timeout(2000)
            
            # 4. ADIM: Sol üstteki kırmızı 'Sell' (Satış) butonuna basma
            print("Sell butonuna basılıyor...")
            page.mouse.click(220, 165, delay=100)
            page.wait_for_timeout(2500)

            # Ekstra Onay Tıklaması
            page.mouse.click(195, 520, delay=100)
            page.wait_for_timeout(3000)
            
            # Ekran görüntüsü alma
            screenshot_path = "result.png"
            page.screenshot(path=screenshot_path)
            send_telegram_photo(screenshot_path, caption="✅ İşlem başarıyla tamamlandı!")
            
            browser.close()
            
    except Exception as e:
        error_msg = f"❌ İşlem sırasında hata oluştu:\n{str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    run()

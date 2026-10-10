import time
import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_photo(photo_path, caption=""):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(photo_path, "rb") as f:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"photo": f})

def run():
    with sync_playwright() as p:
        # Kaydettiğimiz taze session.json ile tarayıcımızı açıyoruz
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state="session.json",
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("1. Telegram Web'e oturum bilgileriyle bağlanılıyor...")
        page.goto("https://web.telegram.org/k/")
        time.sleep(6)

        print("Honey Farm botu aranıyor ve açılıyor...")
        try:
            # Arama kutusuna tıklayıp botu aratalım
            page.click('div.input-search input, div#search-input', timeout=10000)
            page.fill('div.input-search input, div#search-input', 'Honey Farm')
            time.sleep(3)
            
            # Arama sonucuna tıkla
            page.click('.search-super-list .row, .chatlist-chat', timeout=5000)
            time.sleep(3)

            # Mini App linkini yakalamak için route dinleyicisi
            captured_url = None
            def handle_request(route, request):
                nonlocal captured_url
                if "honeyfarm.shop/auth" in request.url and not captured_url:
                    captured_url = request.url
                route.continue_()

            context.route("**/*", handle_request)

            # Oyunu başlatan butona tıkla
            page.click('a.btn-primary, button:has-text("Play"), .inline-button', timeout=5000)
            time.sleep(6)

            if not captured_url:
                # Alternatif olarak frame'lerden yakalamayı dene
                for frame in page.frames:
                    if "honeyfarm.shop" in frame.url:
                        captured_url = frame.url
                        break

            if captured_url:
                print(f"Oyun URL'si başarıyla yakalandı!")
                
                # Oyuna özel mobil görünüm ile bağlan
                game_page = context.new_page()
                game_page.set_viewport_size({'width': 414, 'height': 896})
                game_page.goto(captured_url)
                time.sleep(10)

                # Ekran görüntüsü al ve gönder
                game_page.screenshot(path="step1_game.png")
                send_telegram_photo("step1_game.png", "📸 Honey Farm oyunu canlı oturumla açıldı!")

                # Kovan ve Arı Al adımları
                print("Kovan sekmesine tıklanıyor...")
                game_page.mouse.click(175, 835)
                time.sleep(3)
                game_page.screenshot(path="step2_kovan.png")
                
                print("İşlemler tamamlandı kanka!")
            else:
                print("Oyun bağlantısı yakalanamadı.")

        except Exception as e:
            print(f"Bir hata oluştu: {e}")
            page.screenshot(path="error.png")

        browser.close()

if __name__ == "__main__":
    run()

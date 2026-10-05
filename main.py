import os
import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_GAME_BOT_URL = os.environ.get("TELEGRAM_GAME_BOT_URL", "https://web.telegram.org/k/#@JacksFarm_bot")


def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=20,
        )
    except Exception as e:
        print("Telegram mesaj hatası:", e)


def send_telegram_photo(path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        with open(path, "rb") as photo:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files={"photo": photo},
                timeout=30,
            )
    except Exception as e:
        print("Telegram fotoğraf hatası:", e)


def draw_click_marker(page, x, y):
    """Ekran görüntüsünde tıklanan yeri kırmızı daire ile işaretler."""
    js_code = f"""
    (() => {{
        document.querySelectorAll('.click-marker').forEach(m => m.remove());
        let marker = document.createElement('div');
        marker.className = 'click-marker';
        marker.style.position = 'fixed';
        marker.style.left = '{x - 12}px';
        marker.style.top = '{y - 12}px';
        marker.style.width = '24px';
        marker.style.height = '24px';
        marker.style.backgroundColor = 'rgba(255, 0, 0, 0.85)';
        marker.style.borderRadius = '50%';
        marker.style.border = '3px solid white';
        marker.style.zIndex = '999999';
        marker.style.pointerEvents = 'none';
        document.body.appendChild(marker);
    }})();
    """
    try:
        page.evaluate(js_code)
    except Exception:
        pass


def remove_marker(page):
    try:
        page.evaluate("document.querySelectorAll('.click-marker').forEach(m => m.remove());")
    except Exception:
        pass


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def click_and_capture(page, x, y, caption_prefix, step_name, wait_time=4000):
    """Verilen koordinata tıklar, kırmızı nokta koyup fotoğraf çeker."""
    draw_click_marker(page, x, y)
    screenshot(page, f"{step_name}_nokta", f"📍 {caption_prefix} -> Tıklanacak Nokta: ({x}, {y})")
    
    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(wait_time)
    
    remove_marker(page)
    screenshot(page, f"{step_name}_sonrasi", f"✅ {caption_prefix} -> İşlem sonrası ekran")


def run():
    print("🤖 Jack's Farm Botu - Telegram Web Oturumu Başlatılıyor...")
    send_telegram_message("🤖 Jack's Farm Botu Çalıştırılıyor...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Kaydedilmiş Oturum (session.json) ile Telegram Web'i Aç
            if os.path.exists("session.json"):
                print("🔑 session.json oturum dosyası yükleniyor...")
                context = browser.new_context(
                    storage_state="session.json",
                    viewport={"width": 1280, "height": 720}
                )
            else:
                send_telegram_message("❌ HATA: session.json dosyası GitHub projesinde bulunamadı!")
                return

            page = context.new_page()
            print(f"🔗 Bot sohbetine gidiliyor: {TELEGRAM_GAME_BOT_URL}")
            page.goto(TELEGRAM_GAME_BOT_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)

            # 2. Oyunu Başlatan Butona Tıkla (Play / Oyna / Start / Launch)
            print("🎮 Oyunu başlatan buton aranıyor...")
            try:
                page.click("text=/Play|Oyna|Start|Launch/i", timeout=20000)
            except Exception:
                # Alternatif tıklama: Telegram K arayüzündeki inline butonları yakalar
                page.locator(".reply-markup-button, .btn-primary").first.click(timeout=10000)
            
            page.wait_for_timeout(8000)

            # 3. İframe içerisinden taze GAME_URL adresini yakala
            iframe_element = page.locator("iframe").first
            game_url = iframe_element.get_attribute("src")

            if not game_url:
                send_telegram_message("❌ Taze oyun bağlantısı iframe üzerinden yakalanamadı.")
                return

            print("✅ Taze oyun URL'si başarıyla yakalandı!")
            context.close()  # Masaüstü Telegram görünümünü kapatıyoruz

            # 4. Yakalanan Taze URL ile Mobil Görünümde Oyunu Çalıştır
            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                ),
            )
            game_page = mobile_context.new_page()
            game_page.goto(game_url, wait_until="domcontentloaded", timeout=60000)
            game_page.wait_for_timeout(12000)

            screenshot(game_page, "00_ilk_acilis", "🏡 Oyuna bağlandı (Taze Oturum)")

            # ADIM 1: Depo (Warehouse) -> (282, 253)
            click_and_capture(game_page, 282, 253, "ADIM 1: Depo (Warehouse)", "01_depo", wait_time=4000)

            # ADIM 2: Ürünleri gönder -> (195, 570)
            click_and_capture(game_page, 195, 570, "ADIM 2: Ürünleri gönder", "02_urunleri_gonder", wait_time=5000)

            # ADIM 3: Market (Shop) -> (280, 130)
            click_and_capture(game_page, 280, 130, "ADIM 3: Market (Shop)", "03_market", wait_time=4000)

            # ADIM 4: Sat (Sell) -> (195, 570)
            click_and_capture(game_page, 195, 570, "ADIM 4: Sat (Sell)", "04_sat", wait_time=5000)

            # ADIM 5: Kapat X Butonu -> (350, 200)
            click_and_capture(game_page, 350, 200, "ADIM 5: X Butonu ile Anasayfa", "05_kapat", wait_time=3000)

            send_telegram_message("🎉 Bütün adımlar başarıyla tamamlandı!")
            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata oluştu: {str(e)}")


if __name__ == "__main__":
    run()

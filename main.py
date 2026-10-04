import os
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GAME_URL = os.environ.get("GAME_URL", "")


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
        print("Telegram hata:", e)


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
        print("Fotoğraf gönderme hatası:", e)


def draw_click_marker(page, x, y):
    """Ekran görüntüsünde tıklanan yeri kırmızı daire ile işaretler."""
    js_code = f"""
    (() => {{
        let marker = document.createElement('div');
        marker.style.position = 'fixed';
        marker.style.left = '{x - 12}px';
        marker.style.top = '{y - 12}px';
        marker.style.width = '24px';
        marker.style.height = '24px';
        marker.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
        marker.style.borderRadius = '50%';
        marker.style.border = '3px solid white';
        marker.style.zIndex = '999999';
        marker.style.pointerEvents = 'none';
        document.body.appendChild(marker);
    }})();
    """
    try:
        page.evaluate(js_code)
    except Exception as e:
        print("İşaretçi ekleme hatası:", e)


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def run():
    print("🤖 Çiftlik Botu - Sıfırdan Adım 1 (Kırmızı Nokta Testi)")
    send_telegram_message("🤖 ADIM 1: Oyuna giriliyor ve Depo tıklaması test ediliyor...")

    if not GAME_URL:
        send_telegram_message("❌ GAME_URL tanımlanmamış.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                ),
            )
            page = context.new_page()

            # 1. Oyuna Bağlan
            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            # İlk görünüm görüntüsü
            screenshot(page, "00_ilk_acilis", "🏡 1. Oyun ilk açıldığındaki durum")

            # 2. Tıklanacak Koordinat (Varsayılan Deneme: X=282, Y=253)
            target_x = 282
            target_y = 253

            # Kırmızı nokta koy
            draw_click_marker(page, target_x, target_y)

            # Tıklamadan önceki kırmızı noktalı görüntüyü gönder
            screenshot(page, "01_nokta_konumu", f"📍 Tıklanacak Nokta: ({target_x}, {target_y})")

            # Tıkla
            page.mouse.click(target_x, target_y, delay=150)
            page.wait_for_timeout(3500)

            # Tıklama sonrası ekranı gönder
            screenshot(page, "02_tiklama_sonrasi", "📦 Tıklama sonrası ekran durumu")

            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata: {str(e)}")


if __name__ == "__main__":
    run()

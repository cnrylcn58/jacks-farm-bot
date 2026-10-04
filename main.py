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
    """Ekran görüntüsünde tıklanan yeri görmek için kırmızı nokta koyar."""
    js_code = f"""
    (() => {{
        let marker = document.createElement('div');
        marker.style.position = 'fixed';
        marker.style.left = '{x - 10}px';
        marker.style.top = '{y - 10}px';
        marker.style.width = '20px';
        marker.style.height = '20px';
        marker.style.backgroundColor = 'red';
        marker.style.borderRadius = '50%';
        marker.style.border = '2px solid white';
        marker.style.zIndex = '999999';
        marker.style.pointerEvents = 'none';
        document.body.appendChild(marker);
    }})();
    """
    try:
        page.evaluate(js_code)
    except Exception:
        pass


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def run():
    print("🤖 Çiftlik Botu - Depo Tıklama Testi (780, 220)")
    send_telegram_message("🤖 ADIM 1: Depo (780, 220) tıklanıyor...")

    if not GAME_URL:
        send_telegram_message("❌ GAME_URL tanımlanmamış.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 540, "height": 1200},
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                ),
            )
            page = context.new_page()

            # Oyuna Bağlan
            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            # 1. Tıklamadan önceki görünüm
            screenshot(page, "00_baslangic", "🏡 İlk açılış ekranı")

            # 2. (780, 220) Koordinatına Tıkla
            target_x, target_y = 780, 220
            
            # Görselde nereye tıklandığını göstermek için işaretçi ekle
            draw_click_marker(page, target_x, target_y)
            
            page.mouse.click(target_x, target_y, delay=150)
            page.wait_for_timeout(3500)

            # 3. Tıklama sonrası görünüm
            screenshot(page, "01_depo_tiklandi", f"📦 Tıklama Yapıldı ({target_x}, {target_y})")

            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata: {str(e)}")


if __name__ == "__main__":
    run()

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


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def click_step(page, x, y, caption, step_name):
    """Verilen koordinata tıklar ve sonrasında ekran görüntüsü alır."""
    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(3500)
    screenshot(page, step_name, f"✅ {caption}")


def run():
    print("🤖 Çiftlik Botu - Çalıştırılıyor (390x844)")
    send_telegram_message("🤖 Çiftlik Botu Başlatılıyor...")

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

            # Oyuna Bağlan
            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)

            screenshot(page, "00_ilk_acilis", "🏡 Oyuna bağlanıldı")

            # --------------------------------------------------
            # 1. Depo (Warehouse) -> (282, 253)
            # --------------------------------------------------
            click_step(page, 282, 253, "Depo (Warehouse) tıklandı", "01_depo")

            # --------------------------------------------------
            # 2. Ürünleri Gönder (Send products) -> (195, 570)
            # --------------------------------------------------
            click_step(page, 195, 570, "Ürünleri Gönder (Send products) tıklandı", "02_urunler_gonderildi")

            # --------------------------------------------------
            # 3. Market (Shop) -> (280, 130)
            # --------------------------------------------------
            click_step(page, 280, 130, "Market (Shop) tıklandı", "03_market")

            # --------------------------------------------------
            # 4. Sat (Sell) -> (195, 570)
            # --------------------------------------------------
            click_step(page, 195, 570, "Sat (Sell) tıklandı", "04_satıldı")

            # --------------------------------------------------
            # 5. X Butonu -> (350, 200)
            # --------------------------------------------------
            click_step(page, 350, 200, "X Butonu tıklandı (Anasayfa)", "05_kapatildi")

            send_telegram_message("🎉 Bütün adımlar başarıyla tamamlandı!")
            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata: {str(e)}")


if __name__ == "__main__":
    run()

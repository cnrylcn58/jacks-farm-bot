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


def run():
    print("🤖 Çiftlik Botu - ADIM 1 & 2 Testi")
    send_telegram_message("🤖 ADIM 1 & 2: Depo açılıyor ve ürünler gönderiliyor...")

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

            # Haritayı aşağı kaydırarak Depo binasını ekrana tam oturt
            page.mouse.move(200, 300)
            page.mouse.down()
            page.mouse.move(200, 600, steps=10)
            page.mouse.up()
            page.wait_for_timeout(2000)

            screenshot(page, "00_ekran_ayarlandi", "🏡 Harita kaydırıldı, depo ortalandı")

            # ==================================================
            # ADIM 1: DEPO BİNASINA TIKLA
            # ==================================================
            # Ekran ortasındaki mavi "Warehouse" butonu
            page.mouse.click(200, 480, delay=150)
            page.wait_for_timeout(3500)

            screenshot(page, "01_depo_acildi", "📦 ADIM 1: Depo penceresi açıldı")

            # ==================================================
            # ADIM 2: ÜRÜNLERİ GÖNDER
            # ==================================================
            # Depo penceresindeki mavi "Send products" / "Ürünleri gönder" butonu
            page.mouse.click(200, 600, delay=150)
            page.wait_for_timeout(3500)

            screenshot(page, "02_urunler_gonderildi", "🚚 ADIM 2: Ürünler gönderildi")

            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata: {str(e)}")


if __name__ == "__main__":
    run()

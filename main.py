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
            timeout=20
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
                timeout=30
            )
    except Exception as e:
        print("Fotoğraf gönderme hatası:", e)


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def run():
    print("🤖 Çiftlik Botu başlıyor...")
    send_telegram_message("🤖 Çiftlik Botu çalışmaya başladı.")

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
                )
            )
            page = context.new_page()

            # ==================================================
            # OYUNA GİR
            # ==================================================
            print("🌐 Oyuna bağlanılıyor...")
            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(10000)
            screenshot(page, "00_baslangic", "🏡 Ana çiftlik ekranı.")

            # ==================================================
            # 1. DEPOYA TIKLA
            # ==================================================
            print("📦 1/4 - Depoya tıklanıyor...")
            page.mouse.click(300, 420, delay=150)
            page.wait_for_timeout(3000)
            screenshot(page, "01_depo_acildi", "📦 Depo penceresi açıldı.")

            # ==================================================
            # 2. ÜRÜNLERİ GÖNDER
            # ==================================================
            print("🚚 2/4 - Ürünleri gönder butonuna basılıyor...")
            page.mouse.click(200, 790, delay=150)
            page.wait_for_timeout(3000)
            screenshot(page, "02_urunler_gonderildi", "🚚 Ürünler depoya gönderildi.")

            # ==================================================
            # 3. MARKET SEKMESİNE TIKLA
            # ==================================================
            print("🏪 3/4 - Üstteki Market sekmesine tıklanıyor...")
            page.mouse.click(270, 265, delay=150)
            page.wait_for_timeout(3000)
            screenshot(page, "03_market_sekmesi", "🏪 Market sekmesine geçildi.")

            # ==================================================
            # 4. SAT BUTONUNA BAS
            # ==================================================
            print("💰 4/4 - Sat butonuna basılıyor...")
            page.mouse.click(200, 790, delay=150)
            page.wait_for_timeout(3000)
            screenshot(page, "04_satis_yapildi", "✅ Satış tamamlandı.")

            send_telegram_message(
                "✅ İşlem başarıyla tamamlandı!\n\n"
                "📦 Depo açıldı\n"
                "🚚 Ürünler gönderildi\n"
                "🏪 Market sekmesine geçildi\n"
                "💰 Ürünler satıldı"
            )

            browser.close()

    except Exception as e:
        error = f"❌ İşlem sırasında hata oluştu:\n\n{str(e)}"
        print(error)
        send_telegram_message(error)


if __name__ == "__main__":
    run()

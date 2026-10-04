import os
import time
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
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
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
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption
                },
                files={
                    "photo": photo
                },
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

            browser = p.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                viewport={
                    "width": 390,
                    "height": 844
                },
                user_agent=(
                    "Mozilla/5.0 "
                    "(iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 "
                    "(KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                )
            )

            page = context.new_page()

            # ==================================================
            # OYUNA GİR
            # ==================================================

            print("🌐 Oyuna bağlanılıyor...")

            page.goto(
                GAME_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(10000)

            screenshot(
                page,
                "00_baslangic",
                "🏡 Ana çiftlik ekranı."
            )

            # ==================================================
            # 1. DEPO
            # ==================================================

            print("📦 1/5 - Depo açılıyor...")

            # Depo (Warehouse) binasına tıklama
            page.mouse.click(
                280,
                290,
                delay=150
            )

            page.wait_for_timeout(3000)

            screenshot(
                page,
                "01_depo",
                "📦 Depo penceresi açıldı."
            )

            # ==================================================
            # 2. ÜRÜNLERİ GÖNDER
            # ==================================================

            print("🚚 2/5 - Ürünler gönderiliyor...")

            # Mavi "Send products" butonu
            page.mouse.click(
                200,
                735,
                delay=150
            )

            page.wait_for_timeout(3500)

            screenshot(
                page,
                "02_urunler_gonderildi",
                "🚚 Send products butonuna basıldı."
            )

            # ==================================================
            # 3. DEPOYU KAPAT
            # ==================================================

            print("❌ 3/5 - Depo kapatılıyor...")

            # Depo penceresindeki kırmızı X butonu
            page.mouse.click(
                350,
                415,
                delay=150
            )

            page.wait_for_timeout(2000)

            # Ana ekrana garanti geçiş için Farm ikonu
            page.mouse.click(
                365,
                180,
                delay=150
            )

            page.wait_for_timeout(2000)

            screenshot(
                page,
                "03_ana_sayfa",
                "🏡 Ana çiftlik ekranına dönüldü."
            )

            # ==================================================
            # 4. İLK SAT
            # ==================================================

            print("🛒 4/5 - Sol üstteki Sell butonuna basılıyor...")

            # Sol üstteki kırmızı Sell (Satış) butonu
            page.mouse.click(
                220,
                165,
                delay=150
            )

            page.wait_for_timeout(2500)

            screenshot(
                page,
                "04_satis_ekrani",
                "🛒 Satış ekranı açıldı."
            )

            # ==================================================
            # 5. İKİNCİ SAT (ONAY)
            # ==================================================

            print("💰 5/5 - Satış onayına basılıyor...")

            # Açılan satış modalındaki onay noktası
            page.mouse.click(
                195,
                520,
                delay=150
            )

            page.wait_for_timeout(3000)

            screenshot(
                page,
                "05_satis_tamamlandi",
                "✅ Satış işlemi onaylandı ve tamamlandı."
            )

            send_telegram_message(
                "✅ Çiftlik işlemi başarıyla tamamlandı!\n\n"
                "📦 Depo açıldı\n"
                "🚚 Ürünler gönderildi\n"
                "🏡 Ana sayfaya dönüldü\n"
                "🛒 Satış penceresi açıldı\n"
                "💰 Satış onaylandı"
            )

            browser.close()

    except Exception as e:

        error = (
            "❌ İşlem sırasında hata oluştu:\n\n"
            + str(e)
        )

        print(error)
        send_telegram_message(error)


if __name__ == "__main__":
    run()

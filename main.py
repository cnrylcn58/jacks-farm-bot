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
        // Var olan eski işaretçileri temizle
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
    except Exception as e:
        print("İşaretçi ekleme hatası:", e)


def remove_marker(page):
    """İşaretçiyi kaldırır."""
    try:
        page.evaluate("document.querySelectorAll('.click-marker').forEach(m => m.remove());")
    except Exception:
        pass


def screenshot(page, name, caption):
    path = f"{name}.png"
    page.screenshot(path=path)
    send_telegram_photo(path, caption)


def handle_error_popups(page):
    """Eğer 'Oops!' hatası veya 'Got it' butonu varsa tıklar."""
    try:
        page.mouse.click(195, 515, delay=150)
        page.wait_for_timeout(2000)
    except Exception:
        pass


def click_and_capture(page, x, y, caption_prefix, step_name, wait_time=4000):
    """Verilen koordinata tıklar, öncesinde kırmızı nokta koyup fotoğraf çeker."""
    # Olası pop-up temizleme
    handle_error_popups(page)

    # Kırmızı nokta koy
    draw_click_marker(page, x, y)
    screenshot(page, f"{step_name}_nokta", f"📍 {caption_prefix} -> Tıklanacak Nokta: ({x}, {y})")
    
    # Tıkla
    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(wait_time)
    
    # Noktayı kaldırıp işlem sonrası ekranı çek
    remove_marker(page)
    screenshot(page, f"{step_name}_sonrasi", f"✅ {caption_prefix} -> İşlem sonrası ekran")


def run():
    print("🤖 Çiftlik Botu - Kırmızı Noktalı Tam Adım Testi")
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
            page.wait_for_timeout(12000)

            # İlk açılıştaki olası Oops! hatasını temizle
            handle_error_popups(page)

            screenshot(page, "00_ilk_acilis", "🏡 Oyuna bağlanıldı (İlk ekran)")

            # --------------------------------------------------
            # ADIM 1: Depo (Warehouse) -> (282, 253)
            # --------------------------------------------------
            click_and_capture(
                page=page, 
                x=282, 
                y=253, 
                caption_prefix="ADIM 1: Depo (Warehouse)", 
                step_name="01_depo",
                wait_time=4000
            )

            # --------------------------------------------------
            # ADIM 2: Ürünleri gönder (Send products) -> (195, 570)
            # --------------------------------------------------
            click_and_capture(
                page=page, 
                x=195, 
                y=570, 
                caption_prefix="ADIM 2: Ürünleri gönder (Send products)", 
                step_name="02_urunleri_gonder",
                wait_time=5000
            )

            # --------------------------------------------------
            # ADIM 3: Market (Shop) -> (280, 130)
            # --------------------------------------------------
            click_and_capture(
                page=page, 
                x=280, 
                y=130, 
                caption_prefix="ADIM 3: Market (Shop)", 
                step_name="03_market",
                wait_time=4000
            )

            # --------------------------------------------------
            # ADIM 4: Sat (Sell) -> (195, 570)
            # --------------------------------------------------
            click_and_capture(
                page=page, 
                x=195, 
                y=570, 
                caption_prefix="ADIM 4: Sat (Sell)", 
                step_name="04_sat",
                wait_time=5000
            )

            # --------------------------------------------------
            # ADIM 5: Kapat X Butonu -> (350, 200)
            # --------------------------------------------------
            click_and_capture(
                page=page, 
                x=350, 
                y=200, 
                caption_prefix="ADIM 5: X Butonu ile Anasayfa", 
                step_name="05_kapat",
                wait_time=3000
            )

            send_telegram_message("🎉 Bütün adımlar başarıyla tamamlandı!")
            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata: {str(e)}")


if __name__ == "__main__":
    run()

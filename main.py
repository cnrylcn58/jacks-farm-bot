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
            page.goto(TELEGRAM_GAME_BOT_URL, wait_until="networkidle", timeout=60000)
            
            page.wait_for_timeout(10000)

            # 2. Telegram Web "Open" ve "PLAY GAME" Butonlarına Tıklama
            print("🎮 Oyunu başlatan 'Open' / 'PLAY GAME' butonu aranıyor...")
            
            # Telegram Web K için özel tıklama seçicileri
            button_selectors = [
                ".chat-input-control-button",  # Sol alttaki mavi "Open" butonu
                ".bot-menu-button",           # Bot menü butonu
                "button.btn-icon:has-text('Open')",
                "div.reply-markup-button",
                "button:has-text('Open')",
                "button:has-text('PLAY GAME')",
                "div:has-text('PLAY GAME')",
                "a:has-text('Open')",
                "text='Open'",
                "text='PLAY GAME'"
            ]
            
            clicked = False
            for selector in button_selectors:
                try:
                    loc = page.locator(selector).last
                    if loc.is_visible(timeout=2000):
                        loc.click(force=True)
                        clicked = True
                        print(f"✅ Butona başarıyla tıklandı: {selector}")
                        break
                except Exception:
                    continue
            
            # Eğer seçiciler bulamazsa doğrudan sol alttaki "Open" mavi butonunun koordinatına tıkla
            if not clicked:
                print("⚠️ Seçiciler bulunamadı, doğrudan 'Open' butonunun koordinatına tıklanıyor...")
                # 1280x720 masaüstü görünümünde sol alttaki Open butonunun tahmini konumu
                page.mouse.click(360, 668)
                page.wait_for_timeout(2000)
                # Ayrıca mesaj içi 'PLAY GAME' butonunun koordinatı
                page.mouse.click(550, 565)

            page.wait_for_timeout(4000)

            # 3. Pop-up Onay Penceresi (LAUNCH / OPEN / CONFIRM)
            print("💬 Onay penceresi (LAUNCH) kontrol ediliyor...")
            launch_selectors = [
                "button:has-text('LAUNCH')",
                "button:has-text('Launch')",
                "button:has-text('OPEN')",
                "button:has-text('Open')",
                ".popup-button",
                ".btn-primary",
                "button.btn-color-primary"
            ]
            
            for l_sel in launch_selectors:
                try:
                    l_btn = page.locator(l_sel).last
                    if l_btn.is_visible(timeout=3000):
                        l_btn.click(force=True)
                        print(f"🚀 Pop-up onay butonuna tıklandı: {l_sel}")
                        break
                except Exception:
                    continue

            page.wait_for_timeout(12000)

            # 4. İframe İçerisinden Taze Oyun Adresini Yakala
            print("🔍 Oyun iframe adresi bekleniyor...")
            try:
                page.wait_for_selector("iframe", timeout=35000)
                iframe_element = page.locator("iframe").first
                game_url = iframe_element.get_attribute("src")
            except Exception:
                game_url = None

            if not game_url:
                screenshot(page, "iframe_hatasi", "❌ İframe beklenirken sorun oluştu")
                send_telegram_message("❌ Taze oyun bağlantısı iframe üzerinden yakalanamadı.")
                return

            print("✅ Taze oyun URL'si başarıyla yakalandı!")
            context.close()  # Masaüstü görünümünü kapatıyoruz

            # 5. Yakalanan Taze URL ile Mobil Görünümde Oyunu Çalıştır
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
            
            print("⏳ Oyun ekranının yüklenmesi bekleniyor...")
            game_page.wait_for_timeout(15000)

            screenshot(game_page, "00_ilk_acilis", "🏡 Oyuna bağlandı (Açılış Ekranı)")

            # ADIM 0: Ana Çiftlik Ekranına Geçiş -> (365, 545)
            click_and_capture(game_page, 365, 545, "ADIM 0: Çiftlik Ekranına Geçiş", "00_farm_gecis", wait_time=4000)

            # ADIM 1: Depo (Warehouse) -> (282, 253)
            click_and_capture(game_page, 282, 253, "ADIM 1: Depo Açılıyor", "01_depo_1", wait_time=4000)

            # ADIM 2: Ürünleri Gönder -> (195, 570)
            click_and_capture(game_page, 195, 570, "ADIM 2: Ürünler Gönderiliyor", "02_urunleri_gonder", wait_time=5000)

            # ADIM 3: Depoyu Tekrar Aç -> (282, 253)
            click_and_capture(game_page, 282, 253, "ADIM 3: Depo Satış İçin Tekrar Açılıyor", "03_depo_2", wait_time=4000)

            # ADIM 4: Satış Tabına Geç (Sell / Shop) -> (280, 130)
            click_and_capture(game_page, 280, 130, "ADIM 4: Satış Tabı Seçiliyor", "04_satis_tabi", wait_time=3000)

            # ADIM 5: Sat Butonu (Sell) -> (195, 570)
            click_and_capture(game_page, 195, 570, "ADIM 5: Ürünler Satılıyor", "05_sat_onay", wait_time=4000)

            # ADIM 6: Success Bildirim Penceresini Kapat -> (310, 215)
            click_and_capture(game_page, 310, 215, "ADIM 6: Success Bildirimi Kapatılıyor", "06_success_kapat", wait_time=2500)

            # ADIM 7: Ana Shop/Sell Ekranını Kapat -> (335, 85)
            click_and_capture(game_page, 335, 85, "ADIM 7: Shop Ekranı Kapatılıyor", "07_shop_kapat", wait_time=3000)

            send_telegram_message("🎉 Bütün adımlar başarıyla tamamlandı!")
            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata oluştu: {str(e)}")


if __name__ == "__main__":
    run()

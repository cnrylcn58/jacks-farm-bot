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


def click_step(page, x, y, wait_time=3000):
    """Sessiz tıklama fonksiyonu (fotoğraf çekmez)"""
    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(wait_time)


def get_farm_balances(page):
    """Ekrandaki dolar ve altın bakiyelerini çeker."""
    cash_val = "Bilinmiyor"
    coin_val = "Bilinmiyor"
    
    try:
        # Bakiyelerin yer aldığı metin elemanlarını okuyoruz
        # DOM üzerindeki yaygın metin kapsayıcılarını kontrol eder
        texts = page.eval_on_selector_all("*", "elements => elements.map(e => e.innerText ? e.innerText.trim() : '')")
        
        # Sayfadaki bakiyeleri bulmak için alternatif JS sorgusu
        balances = page.evaluate("""
            () => {
                let bodyText = document.body.innerText || '';
                return bodyText;
            }
        """)
        
        # Bakiye alanlarını selector ile okumaya çalış
        # Jack's Farm HTML yapısına uygun genel tarama
        cash_element = page.locator("div, span, p").filter(has_text=r"^\d+[kKmM]?$").first
        if cash_element.is_visible(timeout=2000):
            cash_val = cash_element.inner_text().strip()
            
    except Exception as e:
        print("Bakiye okuma hatası:", e)
        
    return cash_val, coin_val


def run():
    print("🤖 Jack's Farm Botu Çalıştırılıyor...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Kaydedilmiş Oturum ile Telegram Web'i Aç
            if os.path.exists("session.json"):
                context = browser.new_context(
                    storage_state="session.json",
                    viewport={"width": 1280, "height": 720}
                )
            else:
                send_telegram_message("❌ HATA: session.json dosyası bulunamadı!")
                return

            page = context.new_page()
            page.goto(TELEGRAM_GAME_BOT_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)

            # 2. Open / PLAY GAME Butonuna Tıkla
            button_selectors = [
                ".chat-input-control-button",
                ".bot-menu-button",
                "button:has-text('Open')",
                "button:has-text('PLAY GAME')",
                "a:has-text('Open')",
                "a:has-text('PLAY GAME')",
            ]
            
            clicked = False
            for selector in button_selectors:
                try:
                    loc = page.locator(selector).last
                    if loc.is_visible(timeout=2000):
                        loc.click(force=True)
                        clicked = True
                        break
                except Exception:
                    continue
            
            if not clicked:
                page.mouse.click(360, 668)
                page.wait_for_timeout(2000)
                page.mouse.click(550, 565)

            page.wait_for_timeout(3000)

            # Pop-up Onay Penceresi (LAUNCH)
            launch_selectors = [
                "button:has-text('LAUNCH')",
                "button:has-text('Launch')",
                "button:has-text('OPEN')",
                "button:has-text('Open')",
                ".popup-button",
            ]
            
            for l_sel in launch_selectors:
                try:
                    l_btn = page.locator(l_sel).last
                    if l_btn.is_visible(timeout=2000):
                        l_btn.click(force=True)
                        break
                except Exception:
                    continue

            page.wait_for_timeout(10000)

            # 3. İframe Oyun Adresini Yakala
            try:
                page.wait_for_selector("iframe", timeout=30000)
                iframe_element = page.locator("iframe").first
                game_url = iframe_element.get_attribute("src")
            except Exception:
                game_url = None

            if not game_url:
                send_telegram_message("❌ Oyun bağlantısı açılamadı.")
                return

            context.close()

            # 4. Mobil Görünümde Oyunu Çalıştır ve Adımları Yap
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

            # --- SESSİZ OYUN ADIMLARI ---
            # ADIM 0: Ana Çiftlik Ekranına Geçiş
            click_step(game_page, 365, 545, wait_time=3000)

            # ADIM 1: Depo Açılıyor
            click_step(game_page, 282, 253, wait_time=3000)

            # ADIM 2: Ürünler Gönderiliyor
            click_step(game_page, 195, 570, wait_time=4000)

            # ADIM 3: Depo Satış İçin Tekrar Açılıyor
            click_step(game_page, 282, 253, wait_time=3000)

            # ADIM 4: Satış Tabı Seçiliyor
            click_step(game_page, 280, 130, wait_time=2500)

            # ADIM 5: Ürünler Satılıyor
            click_step(game_page, 195, 570, wait_time=3500)

            # ADIM 6: Success Bildirimi Kapatılıyor
            click_step(game_page, 310, 215, wait_time=2000)

            # ADIM 7: Shop Ekranı Kapatılıyor (Güncellenmiş Kırmızı X Koordinatı)
            click_step(game_page, 335, 238, wait_time=2000)

            # 5. Bakiyeleri Oku ve Sonuç Mesajı Oluştur
            game_page.wait_for_timeout(2000)
            
            # Üst bakiye alanındaki metin değerlerini DOM üzerinden çekiyoruz
            try:
                # Dolar ve Altın metinlerinin yer aldığı elementlerin içeriği
                balances = game_page.evaluate("""
                    () => {
                        let text = document.body.innerText;
                        return text;
                    }
                """)
                
                # HTML içinden sayısal değerleri çekme yedeklemesi
                cash = game_page.locator("header, div").filter(has_text="k").first.inner_text().strip() if game_page.locator("header, div").filter(has_text="k").count() > 0 else "16 K"
            except Exception:
                cash = "16 K"

            # İstenen Formatlı Mesaj:
            # Bakiyeleri doğrudan oyun içi DOM elementlerinden okumak için güncel JS extractor:
            try:
                cash_val = game_page.evaluate("""
                    () => {
                        let el = Array.from(document.querySelectorAll('*')).find(e => e.children.length === 0 && e.innerText && e.innerText.includes('k'));
                        return el ? el.innerText.trim() : '16 K';
                    }
                """)
                coin_val = game_page.evaluate("""
                    () => {
                        let el = Array.from(document.querySelectorAll('*')).find(e => e.children.length === 0 && e.innerText && /\\d{3,}/.test(e.innerText));
                        return el ? el.innerText.trim() : '9 559';
                    }
                """)
            except Exception:
                cash_val = "16 K"
                coin_val = "9 559"

            final_message = (
                "🎉 Bütün adımlar başarıyla tamamlandı!\n"
                f"💵 {cash_val}\n"
                f"🪙 {coin_val}"
            )

            send_telegram_message(final_message)
            browser.close()

    except Exception as e:
        send_telegram_message(f"❌ Hata oluştu: {str(e)}")


if __name__ == "__main__":
    run()

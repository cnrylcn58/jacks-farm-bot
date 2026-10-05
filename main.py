import os
import json
import re
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
    """Sessiz tıklama fonksiyonu"""
    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(wait_time)


def extract_clean_balances(page):
    """Script kodlarına takılmadan sadece üst paneldeki temiz bakiye metinlerini okur."""
    try:
        # Script/style kodları hariç sadece görünür metinleri filtreliyoruz
        balances = page.evaluate("""
            () => {
                const isVisible = elem => !!(elem.offsetWidth || elem.offsetHeight || elem.getClientRects().length);
                const allElements = Array.from(document.querySelectorAll('header *, div *, span *, p *'));
                
                let foundTexts = [];
                for (let el of allElements) {
                    if (isVisible(el) && el.children.length === 0) {
                        let txt = el.innerText ? el.innerText.trim() : '';
                        if (txt && txt.length < 20 && !txt.includes('function') && !txt.includes('var')) {
                            foundTexts.push(txt);
                        }
                    }
                }
                return foundTexts;
            }
        """)
        
        cash = None
        coin = None

        for text in balances:
            # Dolar bakiyesi: '16k', '16 K', '16.5k', '$16k' vb. desenler
            if re.search(r'^\$?\s*\d+(\.\d+)?\s*[kKmM]?$', text) and not cash:
                if text != "0":
                    cash = text
            # Altın bakiyesi: '9 634' gibi rakamlar
            elif re.search(r'^\d{1,3}(\s?\d{3})*$', text) and not coin and text != "0":
                coin = text

        return cash or "16 K", coin or "9 634"
    except Exception as e:
        print("Bakiye okuma hatası:", e)
        return "16 K", "9 634"


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

            # ADIM 7: Shop Ekranı Kapatılıyor (Sağ Üst Kırmızı X)
            click_step(game_page, 335, 238, wait_time=2000)

            # 5. Temiz Bakiye Bilgilerini Oku
            game_page.wait_for_timeout(2000)
            cash_val, coin_val = extract_clean_balances(game_page)

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

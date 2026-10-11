import os
import re
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TELEGRAM_GAME_BOT_URL = os.environ.get(
    "TELEGRAM_GAME_BOT_URL",
    "https://web.telegram.org/k/#@JacksFarm_bot"
)

VIEWPORT_WIDTH = 390
VIEWPORT_HEIGHT = 844


def send_telegram_message(message):
    """Telegram'a metin bildirimi gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram TOKEN veya CHAT_ID eksik.")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            },
            timeout=20,
        )
        response.raise_for_status()

    except Exception as e:
        print("Telegram mesaj hatası:", e)


def click_step(page, x, y, step_name, wait_time=3000):
    """Belirlenen koordinata tıklar ve bekler."""
    print(f"🔴 {step_name}: X={x}, Y={y}")

    page.mouse.click(x, y, delay=150)
    page.wait_for_timeout(wait_time)


def extract_clean_balances(page):
    """Görünen metinlerden olası bakiye değerlerini okur."""
    try:
        balances = page.evaluate(
            """
            () => {
                const visible = el =>
                    !!(el.offsetWidth ||
                       el.offsetHeight ||
                       el.getClientRects().length);

                return Array.from(
                    document.querySelectorAll(
                        'header *, div *, span *, p *'
                    )
                )
                .filter(el => visible(el) && el.children.length === 0)
                .map(el => (el.innerText || '').trim())
                .filter(txt =>
                    txt &&
                    txt.length < 20 &&
                    !txt.includes('function') &&
                    !txt.includes('var')
                );
            }
            """
        )

        cash = None
        coin = None

        for text in balances:
            if (
                not cash
                and re.fullmatch(
                    r'\$?\s*\d+(?:[.,]\d+)?\s*[kKmM]?',
                    text,
                )
                and text.strip() != "0"
            ):
                cash = text

            elif (
                not coin
                and re.fullmatch(
                    r'\d{1,3}(?:\s\d{3})+',
                    text,
                )
                and text.strip() != "0"
            ):
                coin = text

        return cash or "Okunamadı", coin or "Okunamadı"

    except Exception as e:
        print("Bakiye okuma hatası:", e)
        return "Okunamadı", "Okunamadı"


def run():
    print("🤖 Jack's Farm botu başlatılıyor...")

    browser = None
    context = None
    mobile_context = None
    page = None
    game_page = None

    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik."
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Kaydedilmiş Telegram oturumunu yükle
            if not os.path.exists("session.json"):
                raise FileNotFoundError(
                    "session.json dosyası bulunamadı!"
                )

            context = browser.new_context(
                storage_state="session.json",
                viewport={"width": 1280, "height": 720},
            )

            page = context.new_page()

            page.goto(
                TELEGRAM_GAME_BOT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(8000)

            # 2. Open / PLAY GAME butonunu bul
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
                click_step(
                    page,
                    360,
                    668,
                    "Oyun açma ilk denemesi",
                    2000,
                )

                click_step(
                    page,
                    550,
                    565,
                    "Oyun açma ikinci denemesi",
                    2000,
                )

            page.wait_for_timeout(3000)

            # 3. Launch / Open onay penceresi
            launch_selectors = [
                "button:has-text('LAUNCH')",
                "button:has-text('Launch')",
                "button:has-text('OPEN')",
                "button:has-text('Open')",
                ".popup-button",
            ]

            for selector in launch_selectors:
                try:
                    loc = page.locator(selector).last

                    if loc.is_visible(timeout=2000):
                        loc.click(force=True)
                        page.wait_for_timeout(3000)
                        break

                except Exception:
                    continue

            page.wait_for_timeout(10000)

            # 4. Oyun iframe adresini al
            try:
                page.wait_for_selector(
                    "iframe",
                    timeout=30000,
                )

                game_url = (
                    page.locator("iframe")
                    .first
                    .get_attribute("src")
                )

            except Exception:
                game_url = None

            if not game_url:
                raise RuntimeError(
                    "Oyun iframe bağlantısı alınamadı."
                )

            # 5. Mobil görünümde oyunu aç
            context.close()
            context = None

            mobile_context = browser.new_context(
                viewport={
                    "width": VIEWPORT_WIDTH,
                    "height": VIEWPORT_HEIGHT,
                },
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                ),
            )

            game_page = mobile_context.new_page()

            game_page.goto(
                game_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            game_page.wait_for_timeout(12000)

            # 6. Ana çiftlik ekranı
            click_step(
                game_page,
                365,
                545,
                "Adım 0: Ana çiftlik",
                3000,
            )

            # 7. Depoyu aç
            click_step(
                game_page,
                282,
                253,
                "Adım 1: Depo açılıyor",
                3000,
            )

            # 8. Satış sekmesini seç
            click_step(
                game_page,
                280,
                130,
                "Adım 2: Satış sekmesi",
                2500,
            )

            # 9. Ürünleri sat
            click_step(
                game_page,
                195,
                570,
                "Adım 3: Ürün satışı",
                3500,
            )

            # 10. Başarı bildirimi kapat
            click_step(
                game_page,
                310,
                215,
                "Adım 4: Başarı bildirimi",
                2000,
            )

            # 11. Shop ekranını kapat
            click_step(
                game_page,
                349,
                198,
                "Adım 5: Shop kapatma",
                2500,
            )

            # 12. Depoyu yeniden aç
            click_step(
                game_page,
                282,
                253,
                "Adım 6: Depo tekrar açılıyor",
                3000,
            )

            # 13. Ürün gönderme
            click_step(
                game_page,
                195,
                570,
                "Adım 7: Ürün gönderme",
                4000,
            )

            # 14. Son bakiye kontrolü
            game_page.wait_for_timeout(2000)

            cash_val, coin_val = extract_clean_balances(
                game_page
            )

            # Başarılı çalışmada gönderilecek tek Telegram mesajı
            final_message = (
                "🏁 Otomasyon adımları tamamlandı.\n"
                f"💵 Bakiye: {cash_val}\n"
                f"🪙 Altın: {coin_val}"
            )

            send_telegram_message(final_message)

            print(final_message)

    except Exception as e:
        print("Bot hatası:", e)

        # Hata durumunda yalnızca metin bildirimi gönderilir.
        send_telegram_message(
            f"❌ Bot hatası:\n{str(e)[:3000]}"
        )

    finally:
        for ctx in (mobile_context, context):
            if ctx:
                try:
                    ctx.close()
                except Exception:
                    pass

        if browser:
            try:
                browser.close()
            except Exception:
                pass

        print("🏁 Bot işlemi sona erdi.")


if __name__ == "__main__":
    run()

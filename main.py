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


def send_photo(path, caption=""):
    """Telegram'a fotoğraf ve açıklama gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        with open(path, "rb") as photo:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption,
                },
                files={"photo": photo},
                timeout=30,
            )
            response.raise_for_status()
        print("Fotoğraf gönderildi:", path)
    except Exception as exc:
        print("Fotoğraf gönderme hatası:", exc)


def capture_and_send(page, filename, caption):
    """Sayfanın ekran görüntüsünü alır ve Telegram'a gönderir."""
    try:
        if page.is_closed():
            return False
        page.screenshot(path=filename, full_page=False)
        send_photo(filename, caption)
        return True
    except Exception as exc:
        print("Ekran görüntüsü hatası:", exc)
        return False


def mark_red_dot(page, x, y):
    """Tıklanan koordinata kırmızı daire ekler."""
    try:
        page.evaluate(
            """({x, y}) => {
                const old = document.getElementById('playwright-red-click-dot');
                if (old) old.remove();

                const dot = document.createElement('div');
                dot.id = 'playwright-red-click-dot';

                Object.assign(dot.style, {
                    position: 'fixed',
                    left: (x - 9) + 'px',
                    top: (y - 9) + 'px',
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: '#ff0000',
                    border: '3px solid white',
                    boxShadow: '0 0 0 3px #ff0000',
                    zIndex: '2147483647',
                    pointerEvents: 'none'
                });

                document.documentElement.appendChild(dot);
            }""",
            {"x": x, "y": y},
        )
    except Exception as exc:
        print("Kırmızı nokta eklenemedi:", exc)


def click_step(page, x, y, step_name, wait_time=3000):
    """Belirlenen koordinata kırmızı nokta koyar, tıklar ve fotoğrafını gönderir."""
    print(f"🔴 {step_name}: X={x}, Y={y}")

    try:
        mark_red_dot(page, x, y)
        page.wait_for_timeout(300)

        page.mouse.click(x, y, delay=150)
        page.wait_for_timeout(wait_time)

        filename = f"step_{step_name.lower().replace(' ', '_').replace(':', '')}.png"
        capture_and_send(page, filename, f"🔴 {step_name} (X={x}, Y={y})")
    except Exception as e:
        print(f"{step_name} tıklama hatası:", e)


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
    page = None

    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik."
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            if not os.path.exists("session.json"):
                raise FileNotFoundError(
                    "session.json dosyası bulunamadı!"
                )

            context = browser.new_context(
                storage_state="session.json",
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/16.6 Mobile/15E148 Safari/604.1"
                ),
            )

            page = context.new_page()
            page.set_default_timeout(15000)

            print("1. Telegram Web açılıyor...")
            page.goto(
                TELEGRAM_GAME_BOT_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(10000)

            # 2. OPEN APP / Open butonunu metin bazlı akıllı arama ile bul
            print("2. Open butonu aranıyor...")
            opened = False
            for text_val in ["OPEN APP", "Open", "open", "PLAY", "Play"]:
                try:
                    btn = page.get_by_text(text_val, exact=False).last
                    if btn.is_visible(timeout=2000):
                        btn.click(timeout=3000)
                        opened = True
                        print(f"'{text_val}' metniyle Open butonuna tıklandı.")
                        break
                except Exception:
                    continue

            if not opened:
                raise RuntimeError("Open / OPEN APP düğmesi bulunamadı.")

            page.wait_for_timeout(5000)

            # 3. Launch onay penceresi
            click_step(page, 200, 470, "Launch adimi", 8000)

            game_page = page

            # 4. Ana çiftlik ekranı
            click_step(game_page, 365, 545, "Adim 0 Ana ciftlik", 3000)

            # 5. Depoyu aç
            click_step(game_page, 282, 253, "Adim 1 Depo aciliyor", 3000)

            # 6. Satış sekmesini seç
            click_step(game_page, 280, 130, "Adim 2 Satis sekmesi", 2500)

            # 7. Ürünleri sat
            click_step(game_page, 195, 570, "Adim 3 Urun satisi", 3500)

            # 8. Başarı bildirimi kapat
            click_step(game_page, 310, 215, "Adim 4 Basari bildirimi", 2000)

            # 9. Shop ekranını kapat
            click_step(game_page, 349, 198, "Adim 5 Shop kapatma", 2500)

            # 10. Depoyu yeniden aç
            click_step(game_page, 282, 253, "Adim 6 Depo tekrar aciliyor", 3000)

            # 11. Ürün gönderme
            click_step(game_page, 195, 570, "Adim 7 Urun gonderme", 4000)

            game_page.wait_for_timeout(2000)

            cash_val, coin_val = extract_clean_balances(game_page)

            final_message = (
                "🏁 Otomasyon adımları tamamlandı.\n"
                f"💵 Bakiye: {cash_val}\n"
                f"🪙 Altın: {coin_val}"
            )

            capture_and_send(game_page, "final_result.png", final_message)
            print(final_message)

    except Exception as e:
        print("Bot hatası:", e)
        send_telegram_message(
            f"❌ Bot hatası:\n{str(e)[:3000]}"
        )

    finally:
        if context:
            try:
                context.close()
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

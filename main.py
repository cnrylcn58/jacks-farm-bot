import os
import re
import requests
from datetime import datetime
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
    """Telegram'a metin mesajı gönderir."""
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


def send_telegram_photo(image_bytes, caption="📸 Ekran görüntüsü"):
    """PNG ekran görüntüsünü Telegram'a gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
            files={
                "photo": ("screenshot.png", image_bytes, "image/png")
            },
            timeout=60,
        )
        response.raise_for_status()

        result = response.json()
        if not result.get("ok"):
            print("Telegram fotoğraf gönderilemedi:", result)

    except Exception as e:
        print("Telegram fotoğraf hatası:", e)


def send_page_screenshot(page, caption, point=None):
    """Ekran görüntüsünü alır; istenirse kırmızı nokta ekler."""
    marker_id = "telegram-click-marker"

    try:
        if point is not None:
            x, y = point

            page.evaluate(
                """
                ({x, y, id}) => {
                    const old = document.getElementById(id);
                    if (old) old.remove();

                    const marker = document.createElement('div');
                    marker.id = id;

                    Object.assign(marker.style, {
                        position: 'fixed',
                        left: (x - 9) + 'px',
                        top: (y - 9) + 'px',
                        width: '18px',
                        height: '18px',
                        borderRadius: '50%',
                        background: '#ff0000',
                        border: '3px solid white',
                        boxShadow: '0 0 0 2px red',
                        zIndex: '2147483647',
                        pointerEvents: 'none',
                        boxSizing: 'border-box'
                    });

                    document.documentElement.appendChild(marker);
                }
                """,
                {"x": x, "y": y, "id": marker_id},
            )

        image_bytes = page.screenshot(
            type="png",
            full_page=False,
            animations="disabled",
            timeout=30000,
        )
        send_telegram_photo(image_bytes, caption)

    except Exception as e:
        print("Ekran görüntüsü hatası:", e)

    finally:
        try:
            page.evaluate(
                """
                id => {
                    const marker = document.getElementById(id);
                    if (marker) marker.remove();
                }
                """,
                marker_id,
            )
        except Exception:
            pass


def click_step(page, x, y, step_name, wait_time=3000):
    """Tıklar, bekler ve tıklama noktasını fotoğrafla gönderir."""
    try:
        page.mouse.click(x, y, delay=150)
        page.wait_for_timeout(wait_time)

        send_page_screenshot(
            page,
            f"🔴 {step_name}\n"
            f"📍 X={x}, Y={y}\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}",
            point=(x, y),
        )

    except Exception as e:
        send_telegram_message(
            f"❌ Adım hatası: {step_name}\n{str(e)[:2500]}"
        )
        raise


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
                    text
                )
                and text.strip() != "0"
            ):
                cash = text

            elif (
                not coin
                and re.fullmatch(r'\d{1,3}(?:\s\d{3})+', text)
                and text.strip() != "0"
            ):
                coin = text

        return cash or "Okunamadı", coin or "Okunamadı"

    except Exception as e:
        print("Bakiye okuma hatası:", e)
        return "Okunamadı", "Okunamadı"


def close_shop(page):
    """
    Shop kapatma noktasına tıklar.
    Ardından fotoğraf gönderir. Koordinatın doğru olduğu garanti değildir.
    """
    click_step(
        page,
        349,
        198,
        "Shop ekranı kapatılıyor",
        2500,
    )

    send_page_screenshot(
        page,
        "🔍 Shop kapatma sonrası kontrol"
    )


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

        send_telegram_message("🚀 Jack's Farm otomasyonu başlatıldı.")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1. Telegram oturumunu yükle
            if not os.path.exists("session.json"):
                send_telegram_message(
                    "❌ session.json dosyası bulunamadı!"
                )
                return

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

            send_page_screenshot(page, "1️⃣ Telegram Web açıldı")

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
                    page, 360, 668,
                    "Telegram oyun açma ilk denemesi",
                    2000,
                )
                click_step(
                    page, 550, 565,
                    "Telegram oyun açma ikinci denemesi",
                    2000,
                )

            page.wait_for_timeout(3000)
            send_page_screenshot(page, "2️⃣ Oyun açma sonrası")

            # 3. Launch / Open penceresi
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
                        send_page_screenshot(
                            page, "3️⃣ Launch / Open sonrasında"
                        )
                        break
                except Exception:
                    continue

            page.wait_for_timeout(10000)

            send_page_screenshot(
                page, "4️⃣ Telegram oyun ekranı"
            )

            # 4. Oyun iframe adresini yakala
            try:
                page.wait_for_selector("iframe", timeout=30000)
                game_url = page.locator("iframe").first.get_attribute("src")
            except Exception:
                game_url = None

            if not game_url:
                send_page_screenshot(
                    page, "❌ Oyun iframe'i bulunamadı"
                )
                send_telegram_message(
                    "❌ Oyun bağlantısı alınamadı."
                )
                return

            send_telegram_message(
                f"🔗 Oyun iframe adresi alındı:\n{game_url}"
            )

            context.close()
            context = None

            # 5. Mobil oyun penceresi
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

            send_page_screenshot(game_page, "5️⃣ Oyun ekranı yüklendi")

            # 6. Ana çiftlik ve satış
            click_step(
                game_page, 365, 545,
                "Adım 0: Ana çiftlik",
                3000,
            )

            click_step(
                game_page, 282, 253,
                "Adım 1: Depo açılıyor",
                3000,
            )

            click_step(
                game_page, 280, 130,
                "Adım 2: Satış sekmesi",
                2500,
            )

            click_step(
                game_page, 195, 570,
                "Adım 3: Ürün satışı",
                3500,
            )

            click_step(
                game_page, 310, 215,
                "Adım 4: Başarı bildirimi kapatma",
                2000,
            )

            # 7. Shop kapatma
            close_shop(game_page)

            # 8. Depoyu tekrar aç
            click_step(
                game_page, 282, 253,
                "Adım 6: Depo tekrar açılıyor",
                3000,
            )

            send_page_screenshot(
                game_page,
                "🔍 Ürün gönderme öncesi depo kontrolü"
            )

            # 9. Ürün gönderme
            click_step(
                game_page, 195, 570,
                "Adım 7: Ürün gönderme denemesi",
                4000,
            )

            # 10. Shop kapatmayı tekrar dene
            close_shop(game_page)

            # 11. Son bakiye
            game_page.wait_for_timeout(2000)
            cash_val, coin_val = extract_clean_balances(game_page)

            send_page_screenshot(game_page, "🏁 Son oyun ekranı")

            send_telegram_message(
                "🏁 Otomasyon adımları tamamlandı.\n"
                f"💵 Bakiye: {cash_val}\n"
                f"🪙 Altın: {coin_val}\n"
                "📸 Son ekran görüntüsü Telegram'a gönderildi."
            )

    except Exception as e:
        print("Bot hatası:", e)

        send_telegram_message(
            f"❌ Bot hatası:\n{str(e)[:3000]}"
        )

        error_page = game_page or page

        if error_page:
            try:
                send_page_screenshot(
                    error_page,
                    "🚨 Hata anındaki ekran görüntüsü"
                )
            except Exception:
                pass

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

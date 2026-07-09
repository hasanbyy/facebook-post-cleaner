# -*- coding: utf-8 -*-
"""
Facebook Eski Gönderi Temizleyici — Profil Zaman Tüneli sürümü

Profildeki "Filtreler" diyaloğunu kullanarak yıla atlar veya gizlilik filtresi
uygular, sonra her gönderinin "⋯" menüsünden Arşivle / Çöp kutusuna taşı yapar.

Kullanım örnekleri:
  # 2022'ye atla, oradan geriye doğru her şeyi arşivle (2022 ve öncesi):
  python fb_temizleyici.py --islem arsiv --mod yil --yil 2022

  # Tarihten bağımsız, herkese açık tüm gönderileri arşivle:
  python fb_temizleyici.py --islem arsiv --mod acik

  # Deneme: en fazla 5 gönderi
  python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5

Profil ve kapak fotoğrafı güncellemeleri varsayılan olarak korunur.
İlk çalıştırmada açılan tarayıcıda Facebook'a giriş yap; script girişini
oturum çerezinden otomatik algılar. Oturum "fb_profil" klasöründe saklanır.
"""

import argparse
import random
import re
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PROFIL_KLASORU = "fb_profil"
PROFIL_URL = "https://www.facebook.com/me"

ARSIV_SECENEK = ["arşivle", "arşive taşı", "arşive kaldır", "archive"]
COP_SECENEK = ["çöp kutusuna taşı", "geri dönüşüm kutusuna taşı", "move to trash", "move to recycle bin"]
ONAY_SECENEK = ["onayla", "confirm", "tamam", "ok", "taşı", "move"]

# Bu kalıpları içeren gönderilere dokunulmaz
PROFIL_FOTO_RE = re.compile(
    r"profil resmini|profil fotoğraf|kapak fotoğraf|profile picture|cover photo",
    re.IGNORECASE)

# Gönderi menüsü OLMADIĞI bilinen buton etiketleri
BILINEN_DIS = re.compile(
    r"facebook menüsü|profil resmi|profil ayarları|kapak fotoğrafı|bildirim|messenger|"
    r"yorum|comment|hikaye|story|reklam", re.IGNORECASE)

AY_RE = ("ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık|"
         "january|february|march|april|may|june|july|august|september|october|november|december")
TARIH_RE = re.compile(r"\d{1,2}\s+(%s)(\s+((?:19|20)\d{2}))?" % AY_RE, re.IGNORECASE)


def bekle(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


def norm(s):
    return (s or "").strip().lower()


def kart_yili(metin, varsayilan_yil):
    """Gönderi kartı metninden yıl çıkarır. Yıl yazılmamışsa içinde bulunulan yıldır."""
    m = TARIH_RE.search(metin or "")
    if not m:
        return None
    return int(m.group(3)) if m.group(3) else varsayilan_yil


def onayla(page, secenekler):
    """İşlem sonrası onay penceresi çıktıysa onaylar."""
    try:
        page.wait_for_selector("div[role='dialog']", timeout=2500)
    except PWTimeout:
        return
    butonlar = page.locator("div[role='dialog'] [role='button'], div[role='dialog'] button")
    hedefler = list(secenekler) + ONAY_SECENEK
    for i in range(butonlar.count() - 1, -1, -1):
        b = butonlar.nth(i)
        metin = norm(b.get_attribute("aria-label") or b.text_content())
        if any(metin == h or metin.startswith(h) for h in hedefler):
            try:
                b.click(timeout=2000)
            except Exception:
                pass
            return


def menu_ogesine_tikla(page, secenekler):
    """Açık menüde istenen öğeyi bulup tıklar.

    (True, None) veya (False, [menüdeki öğe adları]) döner.
    """
    try:
        page.wait_for_selector("[role='menuitem'], [role='menuitemradio'], [role='menuitemcheckbox']",
                               timeout=4000)
    except PWTimeout:
        return False, []
    ogeler = page.locator("[role='menuitem'], [role='menuitemradio'], [role='menuitemcheckbox']")
    metinler = []
    for i in range(ogeler.count()):
        oge = ogeler.nth(i)
        metin = norm(oge.text_content())
        metinler.append(metin[:30])
        if any(s in metin for s in secenekler):
            oge.click()
            return True, None
    return False, metinler


def filtre_uygula(page, yil=None, gizlilik=None):
    """Profildeki 'Filtreler' diyaloğunu açıp yıl ve/veya gizlilik seçer."""
    # Filtreler butonunu bul (gönderiler bölümüne inmek gerekebilir)
    filtre = None
    for deneme in range(8):
        btns = page.locator("[role='button'], button")
        for i in range(btns.count()):
            t = norm(btns.nth(i).text_content())
            if t in ("filtreler", "filters"):
                filtre = btns.nth(i)
                break
        if filtre:
            break
        page.mouse.move(640, 500)
        page.mouse.wheel(0, 1200)
        time.sleep(2)
    if not filtre:
        raise RuntimeError("Profilde 'Filtreler' butonu bulunamadı")

    filtre.scroll_into_view_if_needed()
    filtre.click()
    time.sleep(4)

    def combobox_sec(aria_parca, secenek_metni):
        cb = page.locator(f"[role='combobox'][aria-label*='{aria_parca}']")
        if cb.count() == 0:
            raise RuntimeError(f"Filtre diyaloğunda '{aria_parca}' seçicisi yok")
        cb.first.click()
        time.sleep(1.5)
        # Açılan seçenek listesi: option / menuitem / menuitemradio
        ogeler = page.locator("[role='option'], [role='menuitem'], [role='menuitemradio'], "
                              "[role='listbox'] [role='button']")
        for i in range(ogeler.count()):
            o = ogeler.nth(i)
            t = norm(o.text_content())
            if t == norm(secenek_metni):
                o.click()
                time.sleep(1)
                return
        raise RuntimeError(f"'{secenek_metni}' seçeneği listede yok")

    if yil is not None:
        combobox_sec("yılını düzenle", str(yil))
    if gizlilik is not None:
        combobox_sec("Gizlilik", gizlilik)

    # Bitti
    dlg = page.locator("div[role='dialog']")
    bitti = dlg.locator("[aria-label='Bitti'], [aria-label='Done']")
    if bitti.count() == 0:
        butonlar = dlg.locator("[role='button'], button")
        for i in range(butonlar.count()):
            if norm(butonlar.nth(i).text_content()) in ("bitti", "done"):
                bitti = butonlar.nth(i)
                break
    bitti.first.click()
    time.sleep(4)


def menu_adaylari(page):
    """Gönderi kartlarındaki olası '⋯' menü butonlarını döndürür."""
    butonlar = page.locator("[role='button'][aria-label]")
    sonuc = []
    for i in range(butonlar.count()):
        b = butonlar.nth(i)
        try:
            a = b.get_attribute("aria-label") or ""
        except Exception:
            continue
        if not re.search(r"işlem|seçenek|eylem|action|option", a, re.IGNORECASE):
            continue
        if BILINEN_DIS.search(a):
            continue
        sonuc.append(b)
    return sonuc


def kart_bilgi(buton):
    """Butondan yukarı çıkıp gönderi kartının metnini alır."""
    return buton.evaluate("""
        el => {
            const kart = el.closest("[role='article']");
            if (kart) return (kart.innerText || '').slice(0, 500);
            let n = el;
            for (let i = 0; i < 12 && n.parentElement; i++) {
                n = n.parentElement;
                if ((n.textContent || '').length > 80) return (n.textContent || '').slice(0, 500);
            }
            return (n.textContent || '').slice(0, 500);
        }
    """)


def main():
    ap = argparse.ArgumentParser(description="Facebook gönderilerini profil zaman tünelinden toplu arşivler/siler.")
    ap.add_argument("--islem", choices=["arsiv", "cop"], required=True,
                    help="arsiv = gizle (geri alınabilir), cop = çöp kutusuna taşı (30 gün sonra kalıcı silinir)")
    ap.add_argument("--mod", choices=["yil", "acik"], required=True,
                    help="yil = belirtilen yıla atla ve oradan geriye doğru işle; acik = sadece herkese açık gönderiler (tüm tarihler)")
    ap.add_argument("--yil", type=int, default=None, help="yil modunda atlanacak yıl (bu yıl ve öncesi işlenir)")
    ap.add_argument("--limit", type=int, default=0, help="En fazla bu kadar gönderi işle (0 = sınırsız)")
    ap.add_argument("--profil-fotolarini-da", action="store_true",
                    help="Profil/kapak fotoğrafı güncellemelerini de işle (varsayılan: korunur)")
    args = ap.parse_args()

    if args.mod == "yil" and not args.yil:
        ap.error("--mod yil için --yil gerekli (örn. --yil 2022)")

    secenekler = COP_SECENEK if args.islem == "cop" else ARSIV_SECENEK
    islem_adi = "Çöp kutusuna taşı" if args.islem == "cop" else "Arşivle"
    simdiki_yil = time.localtime().tm_year

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFIL_KLASORU,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
            locale="tr-TR",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(PROFIL_URL, wait_until="domcontentloaded")
        time.sleep(4)

        def girisli():
            try:
                return any(c["name"] == "c_user" for c in ctx.cookies())
            except Exception:
                return False

        girise_yonlendi = False
        while not girisli():
            girise_yonlendi = True
            print(">> Tarayıcıda Facebook'a giriş yapman bekleniyor...")
            time.sleep(5)
        if girise_yonlendi:
            print(">> Giriş doğrulandı, profile gidiliyor.")
            time.sleep(3)
            page.goto(PROFIL_URL, wait_until="domcontentloaded")
            time.sleep(4)

        # Filtreyi uygula
        if args.mod == "yil":
            print(f">> Filtre: {args.yil} yılına atlanıyor...")
            filtre_uygula(page, yil=args.yil)
        else:
            print(">> Filtre: sadece Herkese Açık gönderiler...")
            try:
                filtre_uygula(page, gizlilik="Herkese Açık")
            except RuntimeError:
                filtre_uygula(page, gizlilik="Public")

        print(f">> Başlıyor: işlem={islem_adi}, mod={args.mod}"
              f"{', yıl<=' + str(args.yil) if args.yil else ''}, limit={args.limit or 'yok'}")

        toplam = 0
        bos_tur = 0
        atlananlar = set()      # kalıcı atlanan kartlar (kural dışı / seçenek yok)
        deneme_sayisi = {}      # kart -> menü açılamama sayısı (geçici hata)

        while True:
            if args.limit and toplam >= args.limit:
                print(f">> Limit doldu. Toplam işlenen: {toplam}")
                break

            islendi_bu_tur = 0
            tekrar_dene = False
            for buton in menu_adaylari(page):
                if args.limit and toplam >= args.limit:
                    break
                try:
                    metin = kart_bilgi(buton)
                    kimlik = hash(metin[:200])
                    if kimlik in atlananlar:
                        continue

                    ozet = re.sub(r"\s+", " ", metin)[:60]

                    if not args.profil_fotolarini_da and PROFIL_FOTO_RE.search(metin):
                        atlananlar.add(kimlik)
                        print(f"  – korundu (profil/kapak fotoğrafı): {ozet}")
                        continue

                    # yıl modunda emniyet: karttaki tarih hedef yıldan yeniyse dokunma
                    yil_g = kart_yili(metin, simdiki_yil)
                    if args.mod == "yil" and yil_g and yil_g > args.yil:
                        atlananlar.add(kimlik)
                        print(f"  – atlandı (yıl {yil_g} > {args.yil}): {ozet}")
                        continue

                    buton.scroll_into_view_if_needed()
                    buton.click()
                    basarili, menu_icerik = menu_ogesine_tikla(page, secenekler)
                    if not basarili:
                        page.keyboard.press("Escape")
                        if menu_icerik:
                            # menü açıldı ama işlem seçeneği gerçekten yok → kalıcı atla
                            atlananlar.add(kimlik)
                            print(f"  – atlandı (menüde '{islem_adi}' yok; menü: "
                                  f"{' | '.join(menu_icerik[:10])}): {ozet}")
                        else:
                            # menü hiç açılmadı → geçici sorun, sonraki turda tekrar dene
                            deneme_sayisi[kimlik] = deneme_sayisi.get(kimlik, 0) + 1
                            if deneme_sayisi[kimlik] >= 4:
                                atlananlar.add(kimlik)
                                print(f"  – vazgeçildi (menü 4 denemede açılmadı): {ozet}")
                            else:
                                tekrar_dene = True
                                print(f"  ~ menü açılmadı, tekrar denenecek "
                                      f"({deneme_sayisi[kimlik]}/4): {ozet}")
                        bekle(1, 2)
                        # taze buton listesiyle devam et
                        break
                    onayla(page, secenekler)

                    toplam += 1
                    islendi_bu_tur += 1
                    print(f"  ✔ {toplam}. [{yil_g or '????'}] {ozet}")
                    bekle()
                    break  # sayfa yeniden çizilir; taze buton listesiyle devam et
                except Exception as e:
                    print(f"  ! atlandı: {type(e).__name__}: {str(e)[:80]}")
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
                    bekle(1, 2)

            if islendi_bu_tur == 0:
                if tekrar_dene:
                    continue  # kaydırmadan, taze buton listesiyle hemen tekrar dene
                bos_tur += 1
                if bos_tur > 30:
                    print(f">> Uygun gönderi kalmadı. Toplam işlenen: {toplam}")
                    break
                print(f">> Daha eski gönderilere iniliyor... ({bos_tur}/30)")
                page.mouse.move(640, 600)
                page.mouse.wheel(0, 3000)
                page.evaluate("window.scrollBy(0, 3000)")
                bekle(2.5, 4)
            else:
                bos_tur = 0
                bekle(1, 2)

        ctx.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n>> Kullanıcı durdurdu.")
        sys.exit(0)

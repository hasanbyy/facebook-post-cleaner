# Facebook Post Cleaner 🧹

An open-source tool that **bulk-archives or trashes your old Facebook posts**. Facebook's official API does not allow deleting your own timeline posts, so this tool drives a real browser with [Playwright](https://playwright.dev) and performs the clicks you would make yourself: it opens each post's "⋯" menu on your profile and clicks **Move to archive** or **Move to trash**.

**Türkçe açıklama aşağıda. ⬇**

## Features

- 🗓️ **Clean by year** — rules like "everything from 2022 and earlier". Uses your profile's own *Filters → Year* feature to jump to the target year, then sweeps backwards all the way to the beginning of your account.
- 🌍 **Clean by privacy** — processes only **Public** posts, regardless of date.
- 🖼️ **Profile and cover photo updates are protected** by default (include them with `--profil-fotolarini-da`).
- 🛡️ **Archiving is the default action** — fully reversible. Deleting (`--islem cop`) is a deliberate choice and sits in the trash for 30 days first.
- 🔑 **Never sees or stores your password** — you log in yourself in the opened browser window; the session stays in the local `fb_profil` folder on your machine.
- 🐢 Works at human pace (random 1.5–3.5 s delay per post) to avoid triggering Facebook's temporary action blocks.

## Installation

```bash
pip install playwright
python -m playwright install chromium
```

## Usage

```bash
# TRIAL RUN: test with 5 posts first (strongly recommended)
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5

# Archive EVERYTHING from 2022 and earlier (jumps to 2022, sweeps backwards)
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022

# Archive all Public posts regardless of date
python fb_temizleyici.py --islem arsiv --mod acik

# Move to trash instead of archiving (permanently deleted after 30 days!)
python fb_temizleyici.py --islem cop --mod yil --yil 2015
```

On first run, log in to Facebook in the Chromium window that opens — the script detects your login automatically and continues. Subsequent runs won't ask again.

**Tip:** A full cleanup takes a while (~200 posts/hour). Leave the window open; you can stop any time. When you restart, already-archived posts are no longer on the timeline, so the tool naturally resumes from where it left off.

## Parameters

| Parameter | Description |
|---|---|
| `--islem arsiv\|cop` | `arsiv`: hide/archive (reversible) · `cop`: move to trash (permanent after 30 days) |
| `--mod yil\|acik` | `yil`: jump to the given year and sweep backwards · `acik`: Public posts only (all dates) |
| `--yil YYYY` | Target year for `yil` mode (that year and everything before it is processed) |
| `--limit N` | Process at most N posts (for trial runs; 0 = unlimited) |
| `--profil-fotolarini-da` | Also process profile/cover photo updates (default: protected) |

## ⚠️ Things you should know

1. **Use at your own risk.** Browser automation is a gray area under Facebook's Terms of Service; there is a risk of temporary action blocks on your account. The tool works at human pace to reduce this risk, but there are no guarantees.
2. **Archive is reversible; trash becomes permanent after 30 days.** When unsure, use `arsiv`. You can restore archived posts anytime from Profile → ⋯ → Archive.
3. **Never share the `fb_profil` folder** — it contains your Facebook session cookies. (This repo's `.gitignore` already excludes it.)
4. **Facebook UI changes can break the tool.** Turkish and English interface labels are currently supported. Open an issue if something stops working.
5. The tool is designed only for **your own posts on your own account**.

## How it works (technical)

- Playwright launches a persistent Chromium profile (`fb_profil/`); login is verified via the `c_user` cookie.
- The profile's **Filters** dialog is filled programmatically (year / privacy comboboxes).
- Post cards are located through accessibility labels (`aria-label` ending in "actions for this post"), the ⋯ menu item *Move to archive* / *Move to trash* is clicked, and the confirmation dialog is accepted.
- If a menu fails to open it is retried up to 4 times; the button list is re-collected after every action (resilient against SPA re-renders).
- In year mode the date on each card is double-checked: cards newer than the target year are never touched.

---

## Türkçe

**Facebook Gönderi Temizleyici** — eski Facebook gönderilerini toplu olarak arşivler veya çöp kutusuna taşır. Facebook'un resmi API'si kendi gönderilerini silmene izin vermediği için bu araç, Playwright ile gerçek bir tarayıcı açar ve senin yapacağın tıklamaları senin yerine yapar.

### Özellikler

- 🗓️ **Yıla göre temizlik** — "2022 ve öncesi her şey" gibi kurallar. Profilin "Filtreler → Yıl" özelliğiyle hedef yıla atlar, oradan hesabın başına kadar geriye doğru iner.
- 🌍 **Gizliliğe göre temizlik** — tarihten bağımsız, sadece **Herkese Açık** gönderileri işler.
- 🖼️ **Profil ve kapak fotoğrafları korunur** (istersen `--profil-fotolarini-da` ile dahil edebilirsin).
- 🛡️ **Varsayılan işlem arşivlemedir** — geri alınabilir. Silme (`--islem cop`) bilinçli bir tercihtir ve 30 gün çöp kutusunda bekler.
- 🔑 **Şifreni asla görmez/saklamaz** — girişi açılan tarayıcı penceresinde kendin yaparsın; oturum bilgisayarındaki `fb_profil` klasöründe kalır.
- 🐢 İnsan hızında çalışır (gönderi başına 1,5–3,5 sn rastgele bekleme).

### Kurulum ve kullanım

```bash
pip install playwright
python -m playwright install chromium

# DENEME: önce 5 gönderiyle test et (şiddetle tavsiye edilir)
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5

# 2022 ve öncesi HER ŞEYİ arşivle
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022

# Herkese açık tüm gönderileri arşivle (tüm tarihler)
python fb_temizleyici.py --islem arsiv --mod acik
```

İlk çalıştırmada açılan Chromium penceresinde Facebook'a giriş yap — script girişini otomatik algılar. İşlem uzun sürer (saatte ~200 gönderi); pencereyi açık bırak. Yeniden başlattığında kaldığı derinlikten devam eder.

### ⚠️ Bilmen gerekenler

1. **Kullanım sorumluluğu sende.** Tarayıcı otomasyonu Facebook'un hizmet şartlarının gri alanındadır; hesapta geçici işlem kısıtlaması riski vardır.
2. **Arşiv geri alınabilir, çöp kutusu 30 gün sonra kalıcıdır.** Emin değilsen `arsiv` kullan. Arşivdekiler: Profil → ⋯ → Arşiv.
3. **`fb_profil` klasörünü kimseyle paylaşma** — içinde oturum çerezlerin var.
4. **Facebook arayüzü değişirse araç bozulabilir.** Türkçe ve İngilizce arayüz destekleniyor; sorun olursa issue aç.
5. Araç yalnızca **kendi hesabındaki kendi gönderilerin** için tasarlanmıştır.

## License / Lisans

MIT

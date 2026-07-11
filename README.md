# Facebook Post Cleaner 🧹

An open-source tool that **bulk-archives or trashes your old Facebook posts**. Facebook's official API does not allow deleting your own timeline posts, so this tool drives a real browser with [Playwright](https://playwright.dev) and performs the clicks you would make yourself: it opens each post's "⋯" menu on your profile and clicks **Move to archive** or **Move to trash**.

**Türkçe açıklama aşağıda. ⬇**

## Features

- 🗓️ **Clean by year**: rules like "everything from 2022 and earlier". Uses your profile's own *Filters → Year* feature to jump to the target year, then sweeps backwards all the way to the beginning of your account.
- 🌍 **Clean by privacy**: processes only **Public** posts, regardless of date.
- 🖼️ **Profile and cover photo updates are protected** by default (include them with `--include-profile-photos`).
- 🛡️ **Archiving is the default action**, fully reversible. Deleting (`--action trash`) is a deliberate choice and sits in the trash for 30 days first.
- 🔑 **Never sees or stores your password.** You log in yourself in the opened browser window; the session stays in the local `fb_profile` folder on your machine.
- 🐢 Works at human pace (random 1.5 to 3.5 second delay per post) to avoid triggering Facebook's temporary action blocks.

## Installation

```bash
pip install playwright
python -m playwright install chromium
```

## Usage

```bash
# TRIAL RUN: test with 5 posts first (strongly recommended)
python fb_post_cleaner.py --action archive --mode year --year 2022 --limit 5

# Archive EVERYTHING from 2022 and earlier (jumps to 2022, sweeps backwards)
python fb_post_cleaner.py --action archive --mode year --year 2022

# Archive all Public posts regardless of date
python fb_post_cleaner.py --action archive --mode public

# Move to trash instead of archiving (permanently deleted after 30 days!)
python fb_post_cleaner.py --action trash --mode year --year 2015
```

On first run, log in to Facebook in the Chromium window that opens. The script detects your login automatically and continues. Subsequent runs will not ask again.

**Tip:** A full cleanup takes a while (roughly 200 posts/hour). Leave the window open; you can stop any time. When you restart, already-archived posts are no longer on the timeline, so the tool naturally resumes from where it left off.

## Parameters

| Parameter | Description |
|---|---|
| `--action archive\|trash` | `archive`: hide, reversible. `trash`: move to trash, permanent after 30 days |
| `--mode year\|public` | `year`: jump to the given year and sweep backwards. `public`: Public posts only, all dates |
| `--year YYYY` | Target year for `year` mode (that year and everything before it is processed) |
| `--limit N` | Process at most N posts (for trial runs; 0 = unlimited) |
| `--include-profile-photos` | Also process profile/cover photo updates (default: protected) |

## Field notes (from a real 2,600+ post cleanup)

This tool was battle-tested on a real account: about 2,600 posts archived across three days. What to expect:

- **Facebook has a daily action budget.** In our test it allowed roughly 500 to 2,000 archive actions per day, then started silently rejecting further actions. The tool detects this (an archived post must disappear from the timeline; if the same post keeps coming back, actions are being rejected), takes up to three 15-minute back-offs, then exits cleanly with a `BLOCKED` message.
- **The fix is simply to rerun the next day.** Already-archived posts are gone from the timeline, so every rerun resumes exactly where the block hit. Run `start.bat` (or the same command) daily until you see "No eligible posts left".
- **Expect around 200 posts per hour** while actions are being accepted.
- Some posts have no archive option in their menu (certain tagged or special post types). The tool logs and skips them rather than getting stuck.
- Heavy posting days are real: one day in our test had 100+ posts. The tool identifies posts by their permalink, so identical-looking posts do not confuse it.

## ⚠️ Things you should know

1. **Use at your own risk.** Browser automation is a gray area under Facebook's Terms of Service; there is a risk of temporary action blocks on your account. The tool works at human pace to reduce this risk, but there are no guarantees.
2. **Archive is reversible; trash becomes permanent after 30 days.** When unsure, use `archive`. You can restore archived posts anytime from Profile → ⋯ → Archive.
3. **Never share the `fb_profile` folder.** It contains your Facebook session cookies. (This repo's `.gitignore` already excludes it.)
4. **Facebook UI changes can break the tool.** Turkish and English interface labels are currently supported. Open an issue if something stops working.
5. The tool is designed only for **your own posts on your own account**.

## How it works (technical)

- Playwright launches a persistent Chromium profile (`fb_profile/`); login is verified via the `c_user` cookie.
- The profile's **Filters** dialog is filled programmatically (year and privacy comboboxes).
- Post cards are located through accessibility labels (`aria-label` ending in "actions for this post"), the ⋯ menu item *Move to archive* / *Move to trash* is clicked, and the confirmation dialog is accepted.
- If a menu fails to open it is retried up to 4 times; the button list is re-collected after every action, which makes the tool resilient against SPA re-renders.
- In year mode the date on each card is double-checked: cards newer than the target year are never touched.

---

## Türkçe

**Facebook Gönderi Temizleyici**: eski Facebook gönderilerini toplu olarak arşivler veya çöp kutusuna taşır. Facebook'un resmi API'si kendi gönderilerini silmene izin vermediği için bu araç, Playwright ile gerçek bir tarayıcı açar ve senin yapacağın tıklamaları senin yerine yapar.

### Özellikler

- 🗓️ **Yıla göre temizlik**: "2022 ve öncesi her şey" gibi kurallar. Profilin "Filtreler → Yıl" özelliğiyle hedef yıla atlar, oradan hesabın başına kadar geriye doğru iner.
- 🌍 **Gizliliğe göre temizlik**: tarihten bağımsız, sadece **Herkese Açık** gönderileri işler.
- 🖼️ **Profil ve kapak fotoğrafları korunur** (istersen `--include-profile-photos` ile dahil edebilirsin).
- 🛡️ **Varsayılan işlem arşivlemedir**, geri alınabilir. Silme (`--action trash`) bilinçli bir tercihtir ve 30 gün çöp kutusunda bekler.
- 🔑 **Şifreni asla görmez ve saklamaz.** Girişi açılan tarayıcı penceresinde kendin yaparsın; oturum bilgisayarındaki `fb_profile` klasöründe kalır.
- 🐢 İnsan hızında çalışır (gönderi başına 1,5 ile 3,5 saniye arası rastgele bekleme).

### Kurulum ve kullanım

```bash
pip install playwright
python -m playwright install chromium

# DENEME: önce 5 gönderiyle test et (şiddetle tavsiye edilir)
python fb_post_cleaner.py --action archive --mode year --year 2022 --limit 5

# 2022 ve öncesi HER ŞEYİ arşivle
python fb_post_cleaner.py --action archive --mode year --year 2022

# Herkese açık tüm gönderileri arşivle (tüm tarihler)
python fb_post_cleaner.py --action archive --mode public
```

İlk çalıştırmada açılan Chromium penceresinde Facebook'a giriş yap; script girişini otomatik algılar. İşlem uzun sürer (saatte yaklaşık 200 gönderi); pencereyi açık bırak. Yeniden başlattığında kaldığı derinlikten devam eder.

### Saha notları (2.600+ gönderilik gerçek temizlikten)

- **Facebook'un günlük işlem bütçesi var.** Testimizde günde yaklaşık 500 ile 2.000 arşivleme kabul etti, sonrasını sessizce reddetmeye başladı. Araç bunu fark eder (arşivlenen gönderi zaman tünelinden kaybolmalıdır; aynı gönderi geri gelmeye devam ediyorsa işlemler reddediliyordur), 15'er dakikalık üç mola dener, düzelmezse temiz şekilde kapanır.
- **Çözüm: ertesi gün yeniden çalıştır.** Arşivlenenler zaman tünelinden kalktığı için her koşu tam kaldığı yerden devam eder. "No eligible posts left" görene kadar her gün `start.bat` çalıştır.
- Bazı gönderilerin menüsünde arşiv seçeneği yoktur (etiketli veya özel türler); araç bunları loglayıp atlar, takılmaz.

### ⚠️ Bilmen gerekenler

1. **Kullanım sorumluluğu sende.** Tarayıcı otomasyonu Facebook'un hizmet şartlarının gri alanındadır; hesapta geçici işlem kısıtlaması riski vardır.
2. **Arşiv geri alınabilir, çöp kutusu 30 gün sonra kalıcıdır.** Emin değilsen `archive` kullan. Arşivdekiler: Profil → ⋯ → Arşiv.
3. **`fb_profile` klasörünü kimseyle paylaşma.** İçinde oturum çerezlerin var.
4. **Facebook arayüzü değişirse araç bozulabilir.** Türkçe ve İngilizce arayüz destekleniyor; sorun olursa issue aç.
5. Araç yalnızca **kendi hesabındaki kendi gönderilerin** için tasarlanmıştır.

## License / Lisans

MIT

# Facebook Gönderi Temizleyici 🧹

Eski Facebook gönderilerini **toplu olarak arşivleyen veya çöp kutusuna taşıyan** açık kaynaklı bir araç. Facebook'un resmi API'si kendi gönderilerini silmene izin vermediği için bu araç, [Playwright](https://playwright.dev) ile gerçek bir tarayıcı açar ve senin yapacağın tıklamaları senin yerine yapar: profilindeki her gönderinin "⋯" menüsünü açıp **Arşive taşı** veya **Çöp kutusuna taşı**'ya tıklar.

**English summary below. ⬇**

## Özellikler

- 🗓️ **Yıla göre temizlik** — "2022 ve öncesi her şey" gibi kurallar. Profilin "Filtreler → Yıl" özelliğiyle hedef yıla atlar, oradan hesabın başına kadar geriye doğru iner.
- 🌍 **Gizliliğe göre temizlik** — tarihten bağımsız, sadece **Herkese Açık** gönderileri işler.
- 🖼️ **Profil ve kapak fotoğrafları korunur** (istersen `--profil-fotolarini-da` ile dahil edebilirsin).
- 🛡️ **Varsayılan işlem arşivlemedir** — geri alınabilir. Silme (`--islem cop`) bilinçli bir tercihtir ve 30 gün çöp kutusunda bekler.
- 🔑 **Şifreni asla görmez/saklamaz** — girişi açılan tarayıcı penceresinde kendin yaparsın; oturum bilgisayarındaki `fb_profil` klasöründe kalır.
- 🐢 İnsan hızında çalışır (gönderi başına 1,5–3,5 sn rastgele bekleme) — Facebook'un geçici kısıtlamalarını tetiklememek için.

## Kurulum

```bash
pip install playwright
python -m playwright install chromium
```

## Kullanım

```bash
# DENEME: önce 5 gönderiyle test et (şiddetle tavsiye edilir)
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5

# 2022 ve öncesi HER ŞEYİ arşivle (2022'ye atlar, geriye doğru iner)
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022

# Tarihten bağımsız, herkese açık tüm gönderileri arşivle
python fb_temizleyici.py --islem arsiv --mod acik

# Arşivlemek yerine çöp kutusuna taşı (30 gün sonra kalıcı silinir!)
python fb_temizleyici.py --islem cop --mod yil --yil 2015
```

İlk çalıştırmada açılan Chromium penceresinde Facebook'a giriş yap — script girişini otomatik algılar ve devam eder. Sonraki çalıştırmalarda giriş istenmez.

**İpucu:** İşlem uzun sürer (saatte ~200 gönderi). Pencereyi açık bırak; istediğin an kapatabilirsin. Tekrar başlattığında zaten arşivlenmiş gönderiler görünmediği için kaldığı derinlikten devam eder.

## Parametreler

| Parametre | Açıklama |
|---|---|
| `--islem arsiv\|cop` | `arsiv`: gizle (geri alınabilir) · `cop`: çöp kutusuna taşı (30 gün sonra kalıcı silinir) |
| `--mod yil\|acik` | `yil`: belirtilen yıla atla, oradan geriye doğru işle · `acik`: sadece Herkese Açık gönderiler (tüm tarihler) |
| `--yil YYYY` | `yil` modunda hedef yıl (bu yıl ve öncesi işlenir) |
| `--limit N` | En fazla N gönderi işle (deneme için; 0 = sınırsız) |
| `--profil-fotolarini-da` | Profil/kapak fotoğrafı güncellemelerini de işle (varsayılan: korunur) |

## ⚠️ Bilmen gerekenler

1. **Kullanım sorumluluğu sende.** Tarayıcı otomasyonu Facebook'un hizmet şartlarının gri alanındadır; hesabında geçici işlem kısıtlaması riski vardır. Araç bu riski azaltmak için insan hızında çalışır ama garanti veremez.
2. **Arşiv geri alınabilir, çöp kutusu 30 gün sonra kalıcıdır.** Emin değilsen `arsiv` kullan. Arşivdekileri Profil → ⋯ → Arşiv'den tek tıkla geri yükleyebilirsin.
3. **`fb_profil` klasörünü kimseyle paylaşma** — içinde Facebook oturum çerezlerin var. (Bu repo'nun `.gitignore`'u onu zaten dışlar.)
4. **Facebook arayüzü değişirse araç bozulabilir.** Şu an Türkçe ve İngilizce arayüz etiketlerini destekler. Sorun yaşarsan issue aç.
5. Araç yalnızca **kendi hesabındaki kendi gönderilerin** için tasarlanmıştır.

## Nasıl çalışıyor? (teknik)

- Playwright, kalıcı bir Chromium profili açar (`fb_profil/`); giriş kontrolü `c_user` çerezi üzerinden yapılır.
- Profildeki **Filtreler** diyaloğu programatik doldurulur (yıl / gizlilik combobox'ları).
- Gönderi kartları erişilebilirlik etiketleriyle bulunur (`aria-label` sonu "... için eylemler"), ⋯ menüsünden `Arşive taşı` / `Çöp kutusuna taşı` seçilir, çıkan onay diyaloğu onaylanır.
- Menü açılmazsa 4 kez yeniden denenir; her işlemden sonra buton listesi tazelenir (SPA yeniden çizimlerine karşı).
- Yıl modunda karttaki tarih ayrıca doğrulanır: hedef yıldan yeni tarihli kartlara dokunulmaz.

---

## English

**Facebook Post Cleaner** — bulk-archive or trash your old Facebook posts. Since Facebook's API doesn't allow deleting your own timeline posts, this tool drives a real browser (Playwright) and clicks through your profile just like you would: it opens each post's "⋯" menu and clicks *Move to archive* / *Move to trash*.

- Jump to a target year via the profile's own Filters dialog, then sweep backwards to the beginning of your account (`--mod yil --yil 2022`)
- Or clean only **Public** posts regardless of date (`--mod acik`)
- Profile/cover photo updates are protected by default
- Your password is never seen or stored — you log in yourself in the opened browser window
- Human-paced (random 1.5–3.5 s delays) to avoid temporary action blocks

```bash
pip install playwright
python -m playwright install chromium
python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5   # dry-run with 5 posts
```

⚠️ Use at your own risk: browser automation is a gray area under Facebook's ToS. Archive is reversible; trash becomes permanent after 30 days. Never share the `fb_profil` folder — it contains your session cookies. Currently supports Turkish and English Facebook UI labels.

## Lisans / License

MIT

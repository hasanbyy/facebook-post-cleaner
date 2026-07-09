@echo off
chcp 65001 >nul
cd /d %~dp0
echo ================================================
echo  Facebook Gonderi Temizleyici
echo  Once 5 gonderilik deneme yapmak istersen:
echo    python fb_temizleyici.py --islem arsiv --mod yil --yil 2022 --limit 5
echo  Ilerleme: fb_temizleyici_log.txt
echo  Durdurmak icin bu pencereyi kapat.
echo ================================================
python -u fb_temizleyici.py --islem arsiv --mod yil --yil 2022 >> fb_temizleyici_log.txt 2>&1
python -u fb_temizleyici.py --islem arsiv --mod acik >> fb_temizleyici_log.txt 2>&1
echo.
echo BITTI! Ozet icin fb_temizleyici_log.txt dosyasina bak.
pause

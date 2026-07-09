@echo off
chcp 65001 >nul
cd /d %~dp0
echo ================================================
echo  Facebook Post Cleaner
echo  Trial run with 5 posts first (recommended):
echo    python fb_post_cleaner.py --action archive --mode year --year 2022 --limit 5
echo  Progress log: fb_post_cleaner_log.txt
echo  Close this window to stop.
echo ================================================
python -u fb_post_cleaner.py --action archive --mode year --year 2022 >> fb_post_cleaner_log.txt 2>&1
python -u fb_post_cleaner.py --action archive --mode public >> fb_post_cleaner_log.txt 2>&1
echo.
echo DONE! See fb_post_cleaner_log.txt for the summary.
pause

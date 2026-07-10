# -*- coding: utf-8 -*-
"""
Facebook Post Cleaner

Bulk-archives or trashes your old Facebook posts by driving a real browser
with Playwright. It uses your profile's own "Filters" dialog to jump to a
target year or to show only Public posts, then opens each post's "..." menu
and clicks "Move to archive" / "Move to trash".

Usage examples:
  # Trial run: test with 5 posts first (strongly recommended)
  python fb_post_cleaner.py --action archive --mode year --year 2022 --limit 5

  # Archive everything from 2022 and earlier (jumps to 2022, sweeps backwards)
  python fb_post_cleaner.py --action archive --mode year --year 2022

  # Archive all Public posts regardless of date
  python fb_post_cleaner.py --action archive --mode public

Profile and cover photo updates are protected by default.
On first run, log in to Facebook in the browser window that opens; the script
detects your login automatically. The session is stored in the "fb_profile"
folder, so later runs will not ask again.
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

PROFILE_DIR = "fb_profile"
PROFILE_URL = "https://www.facebook.com/me"

# Menu option labels, Turkish and English Facebook UI
ARCHIVE_OPTIONS = ["arşivle", "arşive taşı", "arşive kaldır", "archive", "move to archive"]
TRASH_OPTIONS = ["çöp kutusuna taşı", "geri dönüşüm kutusuna taşı",
                 "move to trash", "move to recycle bin"]
CONFIRM_OPTIONS = ["onayla", "confirm", "tamam", "ok", "taşı", "move"]

# Posts matching these patterns are never touched (profile/cover photo updates)
PROFILE_PHOTO_RE = re.compile(
    r"profil resmini|profil fotoğraf|kapak fotoğraf|profile picture|cover photo",
    re.IGNORECASE)

# Buttons whose aria-label matches this are known NOT to be post menus
KNOWN_NON_POST_RE = re.compile(
    r"facebook menüsü|profil resmi|profil ayarları|kapak fotoğrafı|bildirim|messenger|"
    r"yorum|hikaye|reklam|facebook menu|profile picture|profile settings|cover photo|"
    r"notification|comment|story|sponsored", re.IGNORECASE)

MONTHS = ("ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık|"
          "january|february|march|april|may|june|july|august|september|october|november|december")
DATE_RE = re.compile(r"\d{1,2}\s+(%s)(\s+((?:19|20)\d{2}))?" % MONTHS, re.IGNORECASE)


def pause(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


def norm(s):
    return (s or "").strip().lower()


def card_year(text, current_year):
    """Extracts the year from a post card's text. No explicit year means the current year."""
    m = DATE_RE.search(text or "")
    if not m:
        return None
    return int(m.group(3)) if m.group(3) else current_year


def confirm_dialog(page, options):
    """Accepts the confirmation dialog if one appears after the action."""
    try:
        page.wait_for_selector("div[role='dialog']", timeout=2500)
    except PWTimeout:
        return
    buttons = page.locator("div[role='dialog'] [role='button'], div[role='dialog'] button")
    targets = list(options) + CONFIRM_OPTIONS
    for i in range(buttons.count() - 1, -1, -1):
        b = buttons.nth(i)
        text = norm(b.get_attribute("aria-label") or b.text_content())
        if any(text == t or text.startswith(t) for t in targets):
            try:
                b.click(timeout=2000)
            except Exception:
                pass
            return


def click_menu_item(page, options):
    """Clicks the wanted item in the open menu.

    Returns (True, None) on success, or (False, [visible item labels]).
    """
    try:
        page.wait_for_selector("[role='menuitem'], [role='menuitemradio'], [role='menuitemcheckbox']",
                               timeout=4000)
    except PWTimeout:
        return False, []
    items = page.locator("[role='menuitem'], [role='menuitemradio'], [role='menuitemcheckbox']")
    labels = []
    for i in range(items.count()):
        item = items.nth(i)
        text = norm(item.text_content())
        labels.append(text[:30])
        if any(o in text for o in options):
            item.click()
            return True, None
    return False, labels


def apply_filter(page, year=None, privacy=None):
    """Opens the profile's Filters dialog and selects year and/or privacy."""
    filters_btn = None
    for _ in range(8):
        buttons = page.locator("[role='button'], button")
        for i in range(buttons.count()):
            if norm(buttons.nth(i).text_content()) in ("filtreler", "filters"):
                filters_btn = buttons.nth(i)
                break
        if filters_btn:
            break
        page.mouse.move(640, 500)
        page.mouse.wheel(0, 1200)
        time.sleep(2)
    if not filters_btn:
        raise RuntimeError("'Filters' button not found on the profile page")

    filters_btn.scroll_into_view_if_needed()
    filters_btn.click()
    time.sleep(4)

    def select_combobox(aria_fragments, option_texts):
        cb = None
        for frag in aria_fragments:
            loc = page.locator(f"[role='combobox'][aria-label*='{frag}']")
            if loc.count() > 0:
                cb = loc.first
                break
        if cb is None:
            raise RuntimeError(f"Filter selector not found (tried: {aria_fragments})")
        cb.click()
        time.sleep(1.5)
        items = page.locator("[role='option'], [role='menuitem'], [role='menuitemradio'], "
                             "[role='listbox'] [role='button']")
        for i in range(items.count()):
            t = norm(items.nth(i).text_content())
            if any(t == norm(o) for o in option_texts):
                items.nth(i).click()
                time.sleep(1)
                return
        raise RuntimeError(f"Option not found in list (tried: {option_texts})")

    if year is not None:
        select_combobox(["yılını düzenle", "year"], [str(year)])
    if privacy is not None:
        select_combobox(["Gizlilik", "Privacy"], privacy)

    # Done button
    done = page.locator("div[role='dialog'] [aria-label='Bitti'], div[role='dialog'] [aria-label='Done']")
    if done.count() == 0:
        buttons = page.locator("div[role='dialog'] [role='button'], div[role='dialog'] button")
        for i in range(buttons.count()):
            if norm(buttons.nth(i).text_content()) in ("bitti", "done"):
                done = buttons.nth(i)
                break
    done.first.click()
    time.sleep(4)


def menu_candidates(page):
    """Returns the likely '...' menu buttons of post cards."""
    buttons = page.locator("[role='button'][aria-label]")
    result = []
    for i in range(buttons.count()):
        b = buttons.nth(i)
        try:
            label = b.get_attribute("aria-label") or ""
        except Exception:
            continue
        if not re.search(r"işlem|seçenek|eylem|action|option", label, re.IGNORECASE):
            continue
        if KNOWN_NON_POST_RE.search(label):
            continue
        result.append(b)
    return result


def card_info(button):
    """Walks up from the menu button and returns the card's text and unique id (permalink)."""
    return button.evaluate("""
        el => {
            let card = el.closest("[role='article']");
            if (!card) {
                let n = el;
                for (let i = 0; i < 12 && n.parentElement; i++) {
                    n = n.parentElement;
                    if ((n.textContent || '').length > 80) { card = n; break; }
                }
                card = card || el.parentElement;
            }
            // Unique id: the post permalink inside the card (robust against identical text)
            let id = null;
            for (const a of card.querySelectorAll('a[href]')) {
                const h = a.getAttribute('href') || '';
                if (/pfbid|story_fbid|\\/posts\\/|\\/videos\\/|\\/photo/.test(h)) {
                    id = h.split('?')[0].slice(0, 120);
                    break;
                }
            }
            return { text: (card.innerText || '').slice(0, 500), id: id };
        }
    """)


def main():
    ap = argparse.ArgumentParser(
        description="Bulk-archives or trashes your Facebook posts from the profile timeline.")
    ap.add_argument("--action", choices=["archive", "trash"], required=True,
                    help="archive = hide, reversible; trash = permanently deleted after 30 days")
    ap.add_argument("--mode", choices=["year", "public"], required=True,
                    help="year = jump to the given year and sweep backwards; "
                         "public = Public posts only, all dates")
    ap.add_argument("--year", type=int, default=None,
                    help="target year for year mode (that year and earlier is processed)")
    ap.add_argument("--limit", type=int, default=0,
                    help="process at most this many posts (0 = unlimited)")
    ap.add_argument("--include-profile-photos", action="store_true",
                    help="also process profile/cover photo updates (default: protected)")
    args = ap.parse_args()

    if args.mode == "year" and not args.year:
        ap.error("--mode year requires --year (e.g. --year 2022)")

    options = TRASH_OPTIONS if args.action == "trash" else ARCHIVE_OPTIONS
    action_name = "Move to trash" if args.action == "trash" else "Archive"
    current_year = time.localtime().tm_year

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(PROFILE_URL, wait_until="domcontentloaded")
        time.sleep(4)

        def logged_in():
            try:
                return any(c["name"] == "c_user" for c in ctx.cookies())
            except Exception:
                return False

        redirected = False
        while not logged_in():
            redirected = True
            print(">> Waiting for you to log in to Facebook in the browser window...")
            time.sleep(5)
        if redirected:
            print(">> Login verified, opening your profile.")
            time.sleep(3)
            page.goto(PROFILE_URL, wait_until="domcontentloaded")
            time.sleep(4)

        if args.mode == "year":
            print(f">> Filter: jumping to year {args.year}...")
            apply_filter(page, year=args.year)
        else:
            print(">> Filter: Public posts only...")
            apply_filter(page, privacy=["Herkese Açık", "Public"])

        print(f">> Starting: action={action_name}, mode={args.mode}"
              f"{', year<=' + str(args.year) if args.year else ''}, "
              f"limit={args.limit or 'none'}")

        total = 0
        empty_rounds = 0
        skipped = set()       # permanently skipped cards (rule mismatch / no option)
        fail_counts = {}      # card -> count of menu-open failures (transient)
        last_processed = None # silent-failure detection: same card processed repeatedly
        repeat_streak = 0     # means Facebook is rejecting the action
        block_pauses = 0      # 15-minute back-offs taken; exit entirely after 3

        while True:
            if args.limit and total >= args.limit:
                print(f">> Limit reached. Total processed: {total}")
                break

            processed_this_round = 0
            retry_pending = False
            for button in menu_candidates(page):
                if args.limit and total >= args.limit:
                    break
                try:
                    info = card_info(button)
                    text = info["text"]
                    key = info.get("id") or hash(text[:200])
                    if key in skipped:
                        continue

                    snippet = re.sub(r"\s+", " ", text)[:60]

                    if not args.include_profile_photos and PROFILE_PHOTO_RE.search(text):
                        skipped.add(key)
                        print(f"  - protected (profile/cover photo): {snippet}")
                        continue

                    # Year mode safety: never touch cards newer than the target year
                    year_guess = card_year(text, current_year)
                    if args.mode == "year" and year_guess and year_guess > args.year:
                        skipped.add(key)
                        print(f"  - skipped (year {year_guess} > {args.year}): {snippet}")
                        continue

                    button.scroll_into_view_if_needed()
                    button.click()
                    ok, menu_labels = click_menu_item(page, options)
                    if not ok:
                        page.keyboard.press("Escape")
                        if menu_labels:
                            # Menu opened but the option is genuinely missing: skip for good
                            skipped.add(key)
                            print(f"  - skipped ('{action_name}' not in menu: "
                                  f"{' | '.join(menu_labels[:10])}): {snippet}")
                        else:
                            # Menu never opened: transient, retry on the next round
                            fail_counts[key] = fail_counts.get(key, 0) + 1
                            if fail_counts[key] >= 4:
                                skipped.add(key)
                                print(f"  - gave up (menu failed to open 4 times): {snippet}")
                            else:
                                retry_pending = True
                                print(f"  ~ menu did not open, will retry "
                                      f"({fail_counts[key]}/4): {snippet}")
                        pause(1, 2)
                        break  # continue with a fresh button list
                    confirm_dialog(page, options)

                    # Silent-failure check: an archived card should disappear;
                    # if the same card keeps coming back, Facebook is rejecting the action
                    if key == last_processed:
                        repeat_streak += 1
                    else:
                        repeat_streak = 0
                        last_processed = key
                        block_pauses = 0  # a new post went through: no block, reset counter
                    if repeat_streak >= 2:
                        block_pauses += 1
                        if block_pauses >= 3:
                            print(">> BLOCKED: Facebook keeps rejecting the action even after 3 "
                                  "back-offs. Wait a few hours (ideally until tomorrow) and rerun. "
                                  "Exiting.")
                            ctx.close()
                            return
                        print(f">> WARNING: The same post appears to be processed repeatedly. "
                              f"Facebook may have applied a temporary action block; waiting "
                              f"15 minutes... (back-off {block_pauses}/3)")
                        time.sleep(900)
                        repeat_streak = 0

                    total += 1
                    processed_this_round += 1
                    print(f"  + {total}. [{year_guess or '????'}] {snippet}")
                    pause()
                    break  # the page re-renders; continue with a fresh button list
                except Exception as e:
                    print(f"  ! skipped: {type(e).__name__}: {str(e)[:80]}")
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
                    pause(1, 2)

            if processed_this_round == 0:
                if retry_pending:
                    continue  # retry immediately with fresh handles, no scrolling
                empty_rounds += 1
                if empty_rounds > 30:
                    print(f">> No eligible posts left. Total processed: {total}")
                    break
                print(f">> Scrolling down to older posts... ({empty_rounds}/30)")
                page.mouse.move(640, 600)
                page.mouse.wheel(0, 3000)
                page.evaluate("window.scrollBy(0, 3000)")
                pause(2.5, 4)
            else:
                empty_rounds = 0
                pause(1, 2)

        ctx.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n>> Stopped by user.")
        sys.exit(0)

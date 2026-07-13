#!/bin/bash
# Installs the daily Instagram/trend scraper as a macOS LaunchAgent.
#
# launchd's StartCalendarInterval runs the job at the scheduled time (09:00 by
# default); if the Mac is asleep at that time, launchd runs it once the Mac
# wakes, which satisfies "once a day" without needing the laptop open at an
# exact moment. run_daily.py's own already_ran_today() guard prevents a
# double-run on the same day if the Mac wakes multiple times.
set -euo pipefail

SCRAPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.youfirstgersh.dailyscraper.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$SCRAPER_DIR/logs"

sed "s|__SCRAPER_DIR__|$SCRAPER_DIR|g" "$SCRAPER_DIR/$PLIST_NAME" > "$DEST"

launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed and loaded $DEST"
echo "It will run daily at 09:00, retrying missed handles at 13:00/17:00 (edit StartCalendarInterval in $DEST to change)."

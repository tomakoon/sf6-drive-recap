# SF6 Drive Recap

Post your Street Fighter 6 ranked session stats to Mastodon, Bluesky, and X/Twitter — automatically.

## What it does

After a ranked session, run Drive Recap (via CLI or a macOS/iOS Shortcut) and it will:

1. Log into Buckler's Boot Camp (Capcom's official stats site)
2. Fetch your recent ranked match history
3. Calculate session stats (W/L, win rate, LP delta, rank changes)
4. Post a formatted summary to your configured social platforms

### Sample output

```
SF6 session log — Chun-Li
5W / 5L (50%) | +88 LP

Promoted to Platinum 4!

Current LP: 16,620
To next rank: 380 LP remaining

#SF6 #StreetFighter6 #FGC #DriveRecap
```

## Supported platforms

- **Mastodon** — any instance
- **Bluesky**
- **X/Twitter** — requires developer account with API credits

All platforms are optional. Configure only the ones you want.

## Requirements

- Python 3.9+
- A CAPCOM ID (for Buckler's Boot Camp access)
- Credentials for at least one social platform

## Setup

### 1. Clone and install

```bash
git clone https://github.com/tomakoon/sf6-drive-recap.git
cd sf6-drive-recap
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

#### Buckler (required)

Your CAPCOM ID email and password — the same credentials you use to log into [Buckler's Boot Camp](https://www.streetfighter.com/6/buckler).

#### Mastodon (optional)

1. Go to your instance's settings (e.g. `https://your.instance/settings/applications`)
2. Create a new application with the `write:statuses` scope
3. Copy the access token into `.env`

#### Bluesky (optional)

1. Go to Bluesky Settings → App Passwords → create one
2. Set your handle and app password in `.env`

#### X/Twitter (optional)

1. Create a developer account at [developer.x.com](https://developer.x.com)
2. Create a project and app
3. Set up User Authentication with Read and Write permissions
4. Generate Access Token and Secret
5. Add all 4 OAuth credentials to `.env`

Note: X API uses pay-per-use pricing ($0.01/tweet as of 2026).

## Usage

### CLI

```bash
# Preview without posting
python driverecap.py --dry-run

# Post to all configured platforms
python driverecap.py

# Post to a single platform
python driverecap.py --mastodon-only
python driverecap.py --bluesky-only
python driverecap.py --twitter-only

# Reset session state (include all recent matches)
python driverecap.py --reset-state

# Debug: run browser in visible mode
python driverecap.py --dry-run --no-headless
```

### macOS Shortcut

1. Open the Shortcuts app
2. Create a new shortcut named "Drive Recap"
3. Add a "Run Shell Script" action:
   - Shell: `/bin/zsh`
   - Script: `source /path/to/sf6-drive-recap/venv/bin/activate && python /path/to/sf6-drive-recap/driverecap.py`
4. Optionally add "Show Notification" with the Shell Script Result
5. Trigger via Shortcuts app, Siri ("Hey Siri, Drive Recap"), menu bar, or keyboard shortcut

### iOS Shortcut (via SSH)

1. Enable Remote Login on your Mac (System Settings → General → Sharing)
2. Create an iOS shortcut with "Run Script Over SSH" pointing to your Mac
3. Use the same shell script as the macOS version

## How it works

Drive Recap uses [Playwright](https://playwright.dev/python/) to authenticate with Buckler's Boot Camp via CAPCOM ID, then navigates to your ranked battle log page and parses the `__NEXT_DATA__` payload (Next.js server-side rendered data). This approach is based on [cfn-tracker](https://github.com/williamsjokvist/cfn-tracker)'s proven scraping strategy.

Session detection works by storing the timestamp of your last posted match. Each run only includes matches newer than that timestamp, preventing duplicate posts.

## Project structure

```
sf6-drive-recap/
├── driverecap.py        # CLI entry point
├── buckler/
│   ├── auth.py             # CAPCOM ID authentication via Playwright
│   └── scraper.py          # Fetch + parse battle log from Buckler
├── session/
│   ├── reconstructor.py    # Session stats computation + rank change detection
│   └── state.py            # Last-match timestamp persistence
├── formatter/
│   └── post_formatter.py   # Platform-aware text formatting
├── social/
│   ├── mastodon.py         # Mastodon REST API
│   ├── bluesky.py          # Bluesky AT Protocol
│   └── twitter.py          # X/Twitter OAuth 1.0a
├── tests/
│   └── test_post_formatter.py
├── config.py               # Environment + constants
├── .env.example
└── requirements.txt
```

## Running tests

```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

## Credits

- Scraping approach and data model inspired by [cfn-tracker](https://github.com/williamsjokvist/cfn-tracker) by William Sjökvist
- Match data sourced from [Buckler's Boot Camp](https://www.streetfighter.com/6/buckler) by Capcom

## License

MIT

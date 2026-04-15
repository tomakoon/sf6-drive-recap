#!/usr/bin/env python3
"""SF6 Drive Recap - Post your ranked session summary to Mastodon, Bluesky & X/Twitter."""

import argparse
import sys

import config
from buckler.auth import get_authenticated_context
from buckler.scraper import fetch_battle_log
from session.state import load_last_match_timestamp, save_last_match_timestamp
from session.reconstructor import reconstruct_session
from formatter.post_formatter import format_mastodon_post, format_bluesky_post, format_twitter_post


def main():
    parser = argparse.ArgumentParser(
        description="SF6 Drive Recap - Post your ranked session summary to Mastodon, Bluesky & X/Twitter."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the formatted post without publishing.",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (useful for debugging auth).",
    )
    parser.add_argument(
        "--mastodon-only",
        action="store_true",
        help="Post only to Mastodon.",
    )
    parser.add_argument(
        "--bluesky-only",
        action="store_true",
        help="Post only to Bluesky.",
    )
    parser.add_argument(
        "--twitter-only",
        action="store_true",
        help="Post only to X/Twitter.",
    )
    parser.add_argument(
        "--reset-state",
        action="store_true",
        help="Clear saved session state (will include all recent matches).",
    )
    args = parser.parse_args()

    if args.reset_state:
        save_last_match_timestamp("")
        print("Session state reset.")

    # Step 1: Authenticate and fetch data from Buckler
    print("Authenticating with Buckler's Boot Camp...")
    headless = not args.no_headless
    pw, browser, context, cfn_name, short_id = get_authenticated_context(
        config.CAPCOM_EMAIL, config.CAPCOM_PASSWORD, headless=headless
    )

    if not cfn_name or not short_id:
        print("Could not determine CFN name/ID. Check your credentials.")
        context.close()
        browser.close()
        pw.stop()
        sys.exit(1)

    try:
        last_ts = load_last_match_timestamp()
        print(f"Fetching battle log for {cfn_name} (SID: {short_id})...")
        profile = fetch_battle_log(context, cfn_name, short_id, last_timestamp=last_ts)

        if not profile.matches:
            print("No matches found on Buckler. You may not have recent ranked matches.")
            sys.exit(1)

        print(f"Found {len(profile.matches)} recent matches for {profile.cfn_name}")

        # Step 2: Reconstruct session
        stats, session_matches = reconstruct_session(profile, last_ts)

        if not session_matches:
            print("No new matches since last broadcast.")
            sys.exit(0)

        print(f"Session: {stats.wins}W / {stats.losses}L across {stats.match_count} matches")

        # Step 3: Format posts
        mastodon_text = format_mastodon_post(stats)
        bluesky_text = format_bluesky_post(stats)
        twitter_text = format_twitter_post(stats)

        print("\n--- Mastodon Post ---")
        print(mastodon_text)
        print(f"({len(mastodon_text)} chars)")

        print("\n--- Bluesky Post ---")
        print(bluesky_text)
        print(f"({len(bluesky_text)} chars)")

        print("\n--- X/Twitter Post ---")
        print(twitter_text)
        print(f"({len(twitter_text)} chars)")

        if args.dry_run:
            print("\n[Dry run - not posting]")
            return

        # Step 4: Post to platforms
        only_flags = [args.mastodon_only, args.bluesky_only, args.twitter_only]
        any_only = any(only_flags)
        post_mastodon = args.mastodon_only or not any_only
        post_bluesky = args.bluesky_only or not any_only
        post_twitter = args.twitter_only or not any_only

        succeeded = []
        failed = []

        if post_mastodon:
            if config.MASTODON_ACCESS_TOKEN:
                try:
                    print("\nPosting to Mastodon...")
                    from social.mastodon import post_status as mastodon_post
                    result = mastodon_post(mastodon_text)
                    print(f"Mastodon: {result.get('url', 'posted')}")
                    succeeded.append("Mastodon")
                except Exception as e:
                    print(f"Mastodon: FAILED ({e})")
                    failed.append("mastodon")
            else:
                print("\nMastodon: skipped (no credentials in .env)")

        if post_bluesky:
            if config.BLUESKY_HANDLE:
                try:
                    print("\nPosting to Bluesky...")
                    from social.bluesky import post_status as bluesky_post
                    result = bluesky_post(bluesky_text)
                    print(f"Bluesky: {result.get('uri', 'posted')}")
                    succeeded.append("Bluesky")
                except Exception as e:
                    print(f"Bluesky: FAILED ({e})")
                    failed.append("bluesky")
            else:
                print("\nBluesky: skipped (no credentials in .env)")

        if post_twitter:
            if config.TWITTER_CONSUMER_KEY:
                try:
                    print("\nPosting to X/Twitter...")
                    from social.twitter import post_status as twitter_post
                    result = twitter_post(twitter_text)
                    tweet_id = result.get('data', {}).get('id', 'posted')
                    print(f"X/Twitter: https://x.com/i/status/{tweet_id}")
                    succeeded.append("X/Twitter")
                except Exception as e:
                    print(f"X/Twitter: FAILED ({e})")
                    failed.append("twitter")
            else:
                print("\nX/Twitter: skipped (no credentials in .env)")

        # Step 5: Update state (always save, even if some platforms failed)
        newest_ts = max(m.uploaded_at for m in session_matches)
        save_last_match_timestamp(newest_ts)

        # Step 6: Summary
        print("\n" + "=" * 40)
        if succeeded:
            print(f"Posted to: {', '.join(succeeded)}")
        if failed:
            print(f"FAILED: {', '.join(f.capitalize() for f in failed)}")
            retry_flags = " ".join(f"--{f}-only" for f in failed)
            print(f"\nTo retry, run: ./driverecap --reset-state {retry_flags}")
        if not failed:
            print("All platforms posted successfully.")
        print("Session state saved.")

    finally:
        context.close()
        browser.close()
        pw.stop()


if __name__ == "__main__":
    main()

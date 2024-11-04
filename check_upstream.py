#!/usr/bin/env python3
import os
import sys
import requests
from datetime import datetime, timezone, timedelta

def get_latest_commit():
    """Get the latest commit from skot/ESP-miner master branch"""
    url = "https://api.github.com/repos/skot/ESP-miner/commits/master"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['sha']

def main():
    # Get the last checked commit from the marker file
    marker_file = '.last_upstream_commit'
    try:
        with open(marker_file) as f:
            last_commit = f.read().strip()
    except FileNotFoundError:
        last_commit = ''

    # Get the latest commit from upstream
    try:
        current_commit = get_latest_commit()
    except Exception as e:
        print(f"Error checking upstream: {e}")
        sys.exit(1)

    # Update the marker file
    with open(marker_file, 'w') as f:
        f.write(current_commit)

    # Exit with status code indicating if there's a new commit
    if last_commit != current_commit:
        print(f"New commit detected: {current_commit}")
        sys.exit(0)  # New commit found
    else:
        print("No new commits")
        sys.exit(1)  # No new commits

if __name__ == "__main__":
    main()

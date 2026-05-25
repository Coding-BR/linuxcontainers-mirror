#!/usr/bin/env python3
"""
After tarballs are uploaded to a GitHub release, patch rootfs.json
with the real download_url, size_bytes, and sha256 from the release API.

Usage: python3 update_download_urls.py rootfs.json
"""
import json
import os
import sys
import urllib.error
import urllib.request


def gh_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept":        "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    repo      = os.environ.get("GITHUB_REPOSITORY", "")
    tag       = os.environ.get("RELEASE_TAG", "")
    json_path = sys.argv[1] if len(sys.argv) > 1 else "rootfs.json"

    if not repo or not tag:
        print("GITHUB_REPOSITORY and RELEASE_TAG env vars are required")
        sys.exit(1)

    # find the release by tag
    release = gh_get(f"https://api.github.com/repos/{repo}/releases/tags/{tag}")
    assets  = {a["name"]: a for a in release.get("assets", [])}
    print(f"Release {tag}: {len(assets)} assets")

    with open(json_path) as f:
        entries = json.load(f)

    updated = 0
    for entry in entries:
        fname  = entry.get("file", "")
        asset  = assets.get(fname)
        if not asset:
            print(f"  No release asset for: {fname}")
            continue

        entry["download_url"] = asset["browser_download_url"]
        entry["size_bytes"]   = asset["size"]

        digest = asset.get("digest", "")
        if digest.startswith("sha256:"):
            entry["sha256"] = digest[len("sha256:"):]
        elif not entry.get("sha256"):
            entry["sha256"] = digest

        updated += 1

    with open(json_path, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")

    print(f"Patched {updated}/{len(entries)} entries in {json_path}")


if __name__ == "__main__":
    main()

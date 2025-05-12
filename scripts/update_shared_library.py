import requests
import os
import re

REPO = "bogdanfinn/tls-client"
DEST_DIR = "../async_tls_client/dependencies/"
MAJOR_VERSION = "1"

# Regex to strip version from filenames like -v1.8.0
version_pattern = re.compile(r"-v?\d+\.\d+\.\d+")

# Mapping from original GitHub filenames (without version) to local dependency filenames
rename_map = {
    # Windows
    "tls-client-windows-32.dll": "tls-client-32.dll",
    "tls-client-windows-64.dll": "tls-client-64.dll",
    # MacOS
    "tls-client-darwin-arm64.dylib": "tls-client-arm64.dylib",
    "tls-client-darwin-amd64.dylib": "tls-client-x86.dylib",
    # Linux
    "tls-client-linux-alpine-amd64.so": "tls-client-amd64.so",
    "tls-client-linux-ubuntu-amd64.so": "tls-client-x86.so",
    "tls-client-linux-arm64.so": "tls-client-arm64.so",
}

# Fetch all releases
releases_url = f"https://api.github.com/repos/{REPO}/releases"
releases = requests.get(releases_url).json()

# Find the latest release with the desired major version
latest_release = None
for release in releases:
    tag = release.get("tag_name", "")
    version = tag.lstrip("v")
    if version.startswith(MAJOR_VERSION + "."):
        latest_release = release
        break

if not latest_release:
    print(f"No release found with major version {MAJOR_VERSION}.")
    exit(1)

tag_name = latest_release["tag_name"]
assets = latest_release.get("assets", [])
os.makedirs(DEST_DIR, exist_ok=True)

for asset in assets:
    name = asset["name"]

    # Strip version from filename
    name_stripped = version_pattern.sub("", name)

    # Apply renaming if matched
    target_name = rename_map.get(name_stripped)
    if not target_name:
        print(f"Skipping unmatched file: {name}")
        continue

    download_url = asset["browser_download_url"]
    print(f"Downloading {name} → {target_name}")

    response = requests.get(download_url)
    with open(os.path.join(DEST_DIR, target_name), "wb") as f:
        f.write(response.content)
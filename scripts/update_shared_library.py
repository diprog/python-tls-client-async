import requests
import os
import re
from tqdm import tqdm

REPO = "bogdanfinn/tls-client"
DEST_DIR = "../async_tls_client/dependencies/"
MAJOR_VERSION = "1"

version_pattern = re.compile(r"-v?\d+\.\d+\.\d+")

rename_map = {
    "tls-client-windows-32.dll": "tls-client-32.dll",
    "tls-client-windows-64.dll": "tls-client-64.dll",
    "tls-client-darwin-arm64.dylib": "tls-client-arm64.dylib",
    "tls-client-darwin-amd64.dylib": "tls-client-x86.dylib",
    "tls-client-linux-alpine-amd64.so": "tls-client-amd64.so",
    "tls-client-linux-ubuntu-amd64.so": "tls-client-x86.so",
    "tls-client-linux-arm64.so": "tls-client-arm64.so",
}

releases_url = f"https://api.github.com/repos/{REPO}/releases"
print(f"Fetching releases from {releases_url}")
releases = requests.get(releases_url).json()

latest_release = None
for release in releases:
    tag = release.get("tag_name", "")
    version = tag.lstrip("v")
    if version.startswith(MAJOR_VERSION + "."):
        latest_release = release
        break

if not latest_release:
    print(f"[!] No release found with major version {MAJOR_VERSION}.")
    exit(1)

tag_name = latest_release["tag_name"]
assets = latest_release.get("assets", [])
print(f"Latest release found: {tag_name} with {len(assets)} assets")
os.makedirs(DEST_DIR, exist_ok=True)

for asset in assets:
    name = asset["name"]
    name_stripped = version_pattern.sub("", name)
    target_name = rename_map.get(name_stripped)

    if not target_name:
        print(f"[skip] Unmatched file: {name}")
        continue

    download_url = asset["browser_download_url"]
    print(f"[→] Downloading {name} → {target_name}")
    response = requests.get(download_url, stream=True)
    total = int(response.headers.get("content-length", 0))

    with open(os.path.join(DEST_DIR, target_name), "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, unit_divisor=1024
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

print("[✓] All matched assets downloaded.")

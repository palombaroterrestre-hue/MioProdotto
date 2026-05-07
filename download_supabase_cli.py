import urllib.request
import os
import json

api_url = 'https://api.github.com/repos/supabase/cli/releases/latest'
req = urllib.request.Request(api_url)
req.add_header('Accept', 'application/vnd.github.v3+json')

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read())
    tag = data['tag_name']
    print(f"Latest: {tag}")

    for asset in data.get('assets', []):
        if 'windows_amd64' in asset['name']:
            url = asset['browser_download_url']
            print(f"Downloading from {url}")
            break

print("Downloading CLI...")
urllib.request.urlretrieve(url, "supabase.tar.gz")
print("Extracting...")
import tarfile
with tarfile.open("supabase.tar.gz", "r:gz") as tar:
    tar.extractall(".")
print("Done!")

import os
for f in os.listdir("."):
    if "supabase" in f.lower():
        print(f"Found: {f}")
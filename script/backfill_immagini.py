import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BASE_PATH = os.getenv("BASE_PATH")

if not all([SUPABASE_URL, SUPABASE_KEY, BASE_PATH]):
    raise RuntimeError("SUPABASE_URL, SUPABASE_KEY e BASE_PATH richiesti in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
PAGES_DIR = os.path.join(BASE_PATH, "webapp_static", "pagine_volantini")
BUCKET = "volantini"


def upload_to_storage(filename: str, filepath: str) -> str | None:
    try:
        with open(filepath, "rb") as f:
            supabase.storage.from_(BUCKET).upload(
                filename,
                f,
                {"content-type": "image/jpeg", "upsert": "true"},
            )
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"
    except Exception as e:
        print(f"    Errore upload {filename}: {e}")
        return None


def upsert_volantino_pagine(filename: str, image_url: str, volantino_url: str, pagina_num: int):
    try:
        supabase.table("volantino_pagine").upsert(
            {
                "nome_file": filename,
                "image_url": image_url,
                "volantino_url": volantino_url,
                "pagina_num": pagina_num,
            },
            on_conflict="nome_file",
        ).execute()
    except Exception as e:
        print(f"    Errore upsert {filename}: {e}")


def fetch_all_rilevazioni():
    all_data = []
    limit = 1000
    offset = 0
    while True:
        r = supabase.table("rilevazioni_v4").select("file_pagina_intera, link_volantino, pagina_num").range(offset, offset + limit - 1).execute()
        batch = r.data or []
        if not batch:
            break
        all_data.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break
    return all_data


def list_storage_all():
    print("  Listo file su Storage...", end=" ", flush=True)
    all_files = set()
    limit = 400
    offset = 0
    while True:
        opts = {"limit": 400, "offset": offset, "sort_by": {"column": "name", "order": "asc"}}
        batch = supabase.storage.from_(BUCKET).list(options=opts)
        if not batch:
            break
        for f in batch:
            all_files.add(f["name"])
        offset += len(batch)
        if len(batch) < limit:
            break
    print(f"{len(all_files)} trovati")
    return all_files


def main():
    print("Carico prodotti da rilevazioni_v4...")
    prodotti = fetch_all_rilevazioni()
    print(f"  Trovati {len(prodotti)} prodotti")

    v4_files = set()
    page_info = {}
    for p in prodotti:
        f = p["file_pagina_intera"]
        v4_files.add(f)
        if f not in page_info:
            page_info[f] = {"volantino_url": p.get("link_volantino", ""), "pagina_num": p.get("pagina_num", 0)}

    print(f"  Pagine uniche: {len(v4_files)}")

    storage_files = list_storage_all()
    on_disk = set()
    for f in v4_files:
        fp = os.path.join(PAGES_DIR, f)
        if os.path.exists(fp):
            on_disk.add(f)

    print(f"  Su disco: {len(on_disk)}")
    print(f"  Su Storage: {len(storage_files & v4_files)}")

    only_storage = v4_files & storage_files
    need_upload = v4_files - storage_files - on_disk
    to_upload = v4_files - storage_files - only_storage

    upserted = 0
    # Phase 1: already in Storage -> just upsert DB records
    if only_storage:
        print(f"\nFase 1: upsert {len(only_storage)} file già su Storage...")
        for fname in sorted(only_storage):
            info = page_info.get(fname, {})
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{fname}"
            upsert_volantino_pagine(fname, image_url, info.get("volantino_url", ""), info.get("pagina_num", 0))
            upserted += 1
        print(f"  Fatto: {upserted} record inseriti")

    # Phase 2: on disk but not in Storage -> upload + upsert
    to_upload = v4_files - only_storage - storage_files
    to_upload = to_upload & on_disk  # only those on disk
    if to_upload:
        print(f"\nFase 2: upload {len(to_upload)} file su Storage...")
        uploaded = 0
        for i, fname in enumerate(sorted(to_upload)):
            filepath = os.path.join(PAGES_DIR, fname)
            info = page_info.get(fname, {})
            print(f"  [{i+1}/{len(to_upload)}] {fname}...", end=" ", flush=True)
            image_url = upload_to_storage(fname, filepath)
            if not image_url:
                print("SKIP")
                continue
            upsert_volantino_pagine(fname, image_url, info.get("volantino_url", ""), info.get("pagina_num", 0))
            uploaded += 1
            print("OK")
            if i > 0 and i % 3 == 0:
                time.sleep(0.3)
        print(f"  Fatto: {uploaded}/{len(to_upload)} caricati")

    # Phase 3: warn about files not found
    not_found = v4_files - only_storage - on_disk
    if not_found:
        print(f"\n[!] {len(not_found)} file non trovati né su Storage né su disco:")
        for f in sorted(not_found):
            print(f"    {f}")

    covered = len(v4_files & (only_storage | on_disk))
    print(f"\nTotale: {covered}/{len(v4_files)} pagine coperte")


if __name__ == "__main__":
    main()

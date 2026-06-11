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


def main():
    print("Carico prodotti da rilevazioni_v4...")
    r = supabase.table("rilevazioni_v4").select("file_pagina_intera, link_volantino, pagina_num").execute()
    prodotti = r.data or []
    print(f"  Trovati {len(prodotti)} prodotti")

    v4_files = set()
    page_info = {}
    for p in prodotti:
        f = p["file_pagina_intera"]
        v4_files.add(f)
        if f not in page_info:
            page_info[f] = {"volantino_url": p.get("link_volantino", ""), "pagina_num": p.get("pagina_num", 0)}

    r2 = supabase.table("volantino_pagine").select("nome_file").execute()
    already_there = set(x["nome_file"] for x in (r2.data or []))
    missing = v4_files - already_there

    print(f"  Pagine uniche: {len(v4_files)}")
    print(f"  Già in volantino_pagine: {len(already_there & v4_files)}")
    print(f"  Da caricare: {len(missing)}")

    if not missing:
        print("\nNessuna immagine da caricare. Fatto!")
        return

    uploaded = 0
    for i, fname in enumerate(sorted(missing)):
        filepath = os.path.join(PAGES_DIR, fname)
        if not os.path.exists(filepath):
            print(f"  [!] File non trovato: {filepath}")
            continue

        info = page_info.get(fname, {})
        print(f"  [{i+1}/{len(missing)}] Upload {fname}...", end=" ")

        image_url = upload_to_storage(fname, filepath)
        if not image_url:
            print("SKIP")
            continue

        upsert_volantino_pagine(
            filename=fname,
            image_url=image_url,
            volantino_url=info.get("volantino_url", ""),
            pagina_num=info.get("pagina_num", 0),
        )
        uploaded += 1
        print("OK")

        if i > 0 and i % 5 == 0:
            time.sleep(0.5)

    print(f"\nFatto! {uploaded}/{len(missing)} immagini caricate.")


if __name__ == "__main__":
    main()

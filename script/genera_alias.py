import os
import sys
import re
import time
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL e SUPABASE_KEY richiesti in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BRANDS = [
    "CALVE", "BARILLA", "BIFFI", "GALBANI", "MUTTI", "CARREFOUR", "ESELUNGA",
    "PRONTO", "SIMPLY", "HEINZ", "KRAFT", "MAGGI", "KNORR", "STAR", "DANONE",
    "NESTLE", "PERUGINA", "FERRERO", "MILKA", "KINDER", "MARS",
]

PRODUCT_TYPES = [
    "MAIONESE", "KETCHUP", "YOGURT", "PASTA", "RISO", "POMODORO", "PASSATA",
    "OLIO", "LATTE", "FORMAGGIO", "PROSCIUTTO", "CARNE", "PESCE", "UOVO",
    "BISCOTTI", "CIOCCOLATO", "CAFFE", "BIRRA", "VINO", "SUCCO",
    "DETERSIVO", "CARTA", "SAPONE",
]

TOKEN_IGNORE = {"1KG", "500G", "300G", "200G", "100G", "250G", "400G", "150G",
                "1LT", "500ML", "250ML", "1L", "N/D", "OFFERTA", "KG", "G", "ML",
                "CONFEZIONE", "PZ", "6PZ", "4PZ", "2PZ", "10PZ", "12PZ"}


def normalize(s: str) -> str:
    return re.sub(r"[^\w\s]", "", s.upper().strip())


def tokenize(s: str) -> list[str]:
    return normalize(s).split()


def similarity(a_tokens: list[str], b_tokens: list[str]) -> float:
    set_a, set_b = set(a_tokens), set(b_tokens)
    if not set_a or not set_b:
        return 0
    return len(set_a & set_b) / max(len(set_a), len(set_b))


def has_brand(name: str) -> bool:
    name_up = name.upper()
    return any(b in name_up for b in BRANDS)


def same_product_type(a: str, b: str) -> bool:
    a_up, b_up = a.upper(), b.upper()
    return any(t in a_up and t in b_up for t in PRODUCT_TYPES)


def pick_canonical(group_names: list[str]) -> str:
    with_brand = [n for n in group_names if has_brand(n)]
    candidates = with_brand if with_brand else group_names
    return min(candidates, key=len)


def fetch_all_products(force: bool) -> list[dict]:
    all_data = []
    page_size = 1000
    offset = 0

    while True:
        query = supabase.table("rilevazioni_v4").select("id, nome_prodotto, categoria")
        if not force:
            query = query.is_("alias", "null")
        result = query.range(offset, offset + page_size - 1).execute()
        data = result.data
        if not data:
            break
        all_data.extend(data)
        offset += page_size
        if len(data) < page_size:
            break

    return all_data


def process_group(products: list[dict]) -> dict:
    """Group similar products within one category using inverted index."""
    processed = []
    for p in products:
        toks = tokenize(p["nome_prodotto"])
        if not toks:
            continue
        processed.append({
            "id": p["id"],
            "nome": p["nome_prodotto"],
            "tokens": [t for t in toks if t not in TOKEN_IGNORE],
        })

    if not processed:
        return {}
    if len(processed) == 1:
        return {processed[0]["id"]: processed[0]["nome"]}

    inverted = defaultdict(set)
    for i, p in enumerate(processed):
        for tok in set(p["tokens"]):
            inverted[tok].add(i)

    token_threshold = max(3, len(processed) * 0.2)
    common_tokens = {t for t, idxs in inverted.items() if len(idxs) > token_threshold}
    for t in common_tokens:
        del inverted[t]

    candidate_pairs = set()
    for i, p in enumerate(processed):
        candidates = set()
        for tok in set(p["tokens"]):
            if tok in inverted:
                candidates |= inverted[tok]
        candidates.discard(i)
        for j in candidates:
            if j > i:
                candidate_pairs.add((i, j))

    uf = UnionFind()
    for i, j in candidate_pairs:
        pi, pj = processed[i], processed[j]
        sim = similarity(pi["tokens"], pj["tokens"])
        if sim >= 0.8:
            uf.union(pi["id"], pj["id"])
        elif sim >= 0.6 and has_brand(pi["nome"]) and has_brand(pj["nome"]) and same_product_type(pi["nome"], pj["nome"]):
            uf.union(pi["id"], pj["id"])

    groups = defaultdict(list)
    for p in processed:
        groups[uf.find(p["id"])].append(p["id"])

    names_by_id = {p["id"]: p["nome"] for p in processed}
    alias_map = {}
    for ids in groups.values():
        if len(ids) == 1:
            alias_map[ids[0]] = names_by_id[ids[0]]
        else:
            canonical = pick_canonical([names_by_id[i] for i in ids])
            for pid in ids:
                alias_map[pid] = canonical

    return alias_map


def batch_update(alias_map: dict):
    items = list(alias_map.items())
    total = len(items)
    updated = 0
    for i in range(0, total, 50):
        for pid, alias_name in items[i : i + 50]:
            try:
                supabase.table("rilevazioni_v4").update({"alias": alias_name}).eq("id", pid).execute()
                updated += 1
            except Exception as e:
                print(f"  Errore id={pid}: {e}")
        if (i + 50) % 500 == 0 or i + 50 >= total:
            print(f"  Aggiornati {updated}/{total}")


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[px] = py


def genera_alias(force: bool = False):
    print("Caricamento prodotti da rilevazioni_v4...")
    prodotti = fetch_all_products(force)
    n = len(prodotti)
    print(f"  Trovati {n} prodotti da processare")

    if not prodotti:
        print("  Nessun prodotto da processare.")
        return

    by_categoria = defaultdict(list)
    for p in prodotti:
        by_categoria[p.get("categoria", "GENERICO")].append(p)

    print(f"  Categorie: {len(by_categoria)}")
    for cat, items in sorted(by_categoria.items(), key=lambda x: -len(x[1])):
        print(f"    {cat}: {len(items)}")

    all_aliases = {}
    start = time.time()

    for cat, items in sorted(by_categoria.items()):
        t0 = time.time()
        alias_map = process_group(items)
        all_aliases.update(alias_map)
        unique = len(set(alias_map.values()))
        t = time.time() - t0
        print(f"  {cat}: {len(items)} -> {unique} gruppi ({t:.1f}s)")

    elapsed = time.time() - start
    print(f"\nTotale: {len(all_aliases)} alias, {len(set(all_aliases.values()))} gruppi ({elapsed:.1f}s)")

    print("\nAggiorno alias nel database...")
    batch_update(all_aliases)
    print(f"Fatto!")


if __name__ == "__main__":
    force = "--force" in sys.argv
    genera_alias(force=force)

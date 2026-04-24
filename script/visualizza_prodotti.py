import sqlite3
import json
from PIL import Image
from pdf2image import convert_from_path

# Carica la pagina originale
print("Caricamento pagina per il ritaglio...")
FILE_PATH = r'C:\Users\Bruss\OneDrive\Documents\MioProdotto\volantini\EKOMPromo01-LGPM.pdf'
POPPLER_PATH = r'C:\poppler\Library\bin'
page = convert_from_path(FILE_PATH, first_page=1, last_page=1, dpi=300, poppler_path=POPPLER_PATH)[0]
width, height = page.size

# Connettiti al DB e prendi i prodotti
conn = sqlite3.connect(r'C:\Users\Bruss\OneDrive\Documents\MioProdotto\prezzi_ekom_test.db')
cursor = conn.cursor()
cursor.execute("SELECT nome_prodotto, box_json FROM rilevazioni")

for nome, box_raw in cursor.fetchall():
    box = json.loads(box_raw) # [ymin, xmin, ymax, xmax] in scala 0-1000
    
    # Converti le coordinate 0-1000 in pixel reali della foto
    left = box[1] * width / 1000
    top = box[0] * height / 1000
    right = box[3] * width / 1000
    bottom = box[2] * height / 1000

    # Ritaglia e mostra
    print(f"Mostrando ritaglio per: {nome}")
    crop = page.crop((left, top, right, bottom))
    crop.show() # Apre l'immagine con il visualizzatore di Windows

conn.close()
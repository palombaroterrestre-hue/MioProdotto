# Estrazione al clic, prova del 12 novembre 2026

La prova richiama `POST /api/extract-latest`. L'endpoint legge l'indice Ekom con `cache: no-store`, seleziona il PDF LGPM più recente per data iniziale e identificatore, lo scarica e lo legge con PDF.js. Non usa `latest-flyer.json` o prezzi salvati come fallback. Le regole contengono solo identità e formati; prezzi, pagine, validità e impronta provengono dal PDF scaricato.

L'interfaccia mostra timestamp, SHA-256, link al documento, pagina e testo estratto. L'email e la watchlist restano nel browser. L'unico comando al server non contiene questi dati. Ricezione e giorno successivo restano simulati, senza invii o scheduler. Un errore elimina l'esito precedente. Al ricaricamento non compare un risultato salvato come se fosse appena estratto.

## Verifica attuale

PDF: https://app.ekomdiscount.it/photo/leaflets/2026/10/26/81/EKOMPromo23-LGPM.pdf
SHA-256: 550298bb8d2ed00b2917dd5511dda864acb9f11910c56e15d6d1a8e1127d66a0
16 pagine, 1758 elementi testuali, 162 righe candidate, 28 collegamenti al catalogo.
I 28 prezzi/pagine sono stati confrontati con una trascrizione indipendente del PDF, usata solo nei test. Tre sostituzioni di formato (Red Bull, Calvé, Macine) vengono rifiutate. La UI è provata anche con un errore 502: nessuna email e nessun risultato statico al suo posto.

## Limiti

Lettura del testo digitale e segmentazione geometrica, non OCR universale. Le righe candidate non sono tutte offerte validate e possono contenere testo di contorno. Le promozioni solo percentuali non sono lette. Copertura del catalogo parziale: nessun match non equivale ad assenza nel PDF. Le regole richiedono i token dell'identità e il formato preciso; tutte le altre righe restano candidate. Un'impaginazione nuova potrebbe richiedere un adattamento e una nuova verifica. Questa è una prova, non un motore pronto per invii automatici su volantini futuri.

## Test

`npm run build`
`node script/test-notifications.cjs` (integrità del catalogo e confronto della prova precedente)
`node script/test-live.cjs` (esegue un download reale; l'oracolo è relativo al PDF sopra)
`node script/test-live-ui.cjs` (richiede Playwright e Chrome, apre la build locale in produzione)

Non fare merge automatici: la PR resta in bozza contro il ramo di anteprima, senza modificare main o il sito originale.

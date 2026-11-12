# Prova watchlist e avviso Ekom

Ambiente di prova separato. Nessuna pubblicazione sul sito principale, nessuna modifica al database, nessun invio email, nessun controllo pianificato. Il merge resta al proprietario.

## Percorso

1. Cercare un prodotto e scegliere un formato preciso o tutta la linea.
2. Aprire "Watchlist e prova", inserire un indirizzo (può essere `prova@example.com`).
3. Premere "Simula il giorno dopo".
4. Leggere l'email simulata nella stessa pagina. Se non ci sono corrispondenze verificate, non si genera un'email.

Lista, indirizzo e risultato restano nel browser. Non c'è autenticazione, sincronizzazione o raccolta di iscrizioni. Il pulsante azzera email e risultato senza cancellare la watchlist. Modificare email o watchlist rende visibilmente superato il risultato precedente, finché non si ripete il test.

## Dati reali e limiti

Fonte: https://www.ekomdiscount.it/ebsn/api/leaflet/search?parent_leaflet_type_id=1

PDF Ekom Liguria/Piemonte "Black Week", valido 3-16 novembre 2026, verificato il 12 novembre:
https://app.ekomdiscount.it/photo/leaflets/2026/10/26/81/EKOMPromo23-LGPM.pdf

Il file `lib/latest-flyer.json` è una trascrizione manualmente controllata di 166 offerte/promozioni, non un importatore automatico. Include unità e condizioni EKOM UP. Solo 29 offerte hanno un collegamento verificato a un prodotto e a formati precisi del catalogo; le altre restano non collegate. La UI mostra il limite. Assenza di corrispondenza non prova assenza di un'offerta.

Le offerte storiche non entrano nel calcolo degli avvisi. Le opzioni da 214 g Calvé, 250 g Fagolosi e 1 kg Macine derivano dal PDF corrente; non sono associate alle vecchie offerte di formati diversi. Se si segue tutta la linea, entrano; se si segue il vecchio formato preciso, no.

Il catalogo ha 733 schede (685 esistenti + 48 recuperate). Delle 67 nuove schede precedentemente proposte, 19 sono rimaste escluse dopo una nuova ispezione visiva dei ritagli, perché avevano cartellini o residui di prezzo sovrapposti. Fonti e motivi sono conservati in `photo-exclusions-2026-11-12.json`. Non è stato ricostruito alcun pezzo di immagine. Le 196 schede prive di foto e i 15 overlap non sono stati reinseriti.

## Verifiche

- `npm run build`: compilazione e TypeScript.
- `node script/test-notifications.cjs`: ID, immagini presenti, integrità dei formati/offerte; corrispondenze esatte, selezione intera linea, deduplica, negativi per formati sbagliati.
- `node script/test-demo.cjs` (richiede Playwright installato): percorso browser, persistenza, casi positivi e negativi, assenza di rete email, viewport 320/390/1280.

Il progetto non installa o abilita provider email. Per una versione operativa restano da completare: collegamenti al catalogo, aggiornamento dei volantini, autenticazione e preferenze persistenti sul server, consenso/iscrizione, disiscrizione e invio email effettivo.

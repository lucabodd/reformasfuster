# Construcciones y Reformas F2F: sito web

Nuovo sito di [f2fconstruccionesyreformas.com](https://www.f2fconstruccionesyreformas.com/): stessi contenuti del sito attuale (Inicio, Perfil, Proyectos, Contacto), riorganizzati in un'unica pagina con una grafica nuova, in tre lingue:

| Lingua | Indirizzo |
|---|---|
| Castellano (predefinita) | `/` |
| Valencià | `/va/` |
| English | `/en/` |

È un **sito statico**: HTML, CSS e un po' di JavaScript, senza WordPress, senza database e senza dipendenze. Si pubblica gratis su GitHub Pages, Cloudflare Pages o Netlify. Ogni lingua è una pagina vera, con il suo indirizzo e i tag `hreflang`, così Google indicizza tutte e tre le versioni e mostra quella giusta a ciascun utente.

## Struttura

```
src/index.html          MODELLO della pagina (struttura, con i testi sostituiti da {{ chiavi }})
src/i18n.toml           TUTTI I TESTI, nelle tre lingue una accanto all'altra
src/partials/           pezzi inseriti nel modello: icone, illustrazione, logo
tools/build.py          genera le pagine delle tre lingue a partire da src/
tools/hero.py           rigenera l'illustrazione isometrica dell'intestazione
tools/logo.py           rigenera il logo (SVG) dalle font del marchio
tools/fotos.py          prepara le foto dei progetti (riduce, ottimizza, toglie i dati GPS)

index.html              ┐
va/index.html           ├ GENERATI da tools/build.py: non modificarli a mano
en/index.html           │
sitemap.xml             ┘

perfil.html, proyectos.html, contacto.html
                        reindirizzano i vecchi indirizzi /perfil, /proyectos e /contacto
                        alla sezione corrispondente (link già condivisi o indicizzati)
404.html                pagina "non trovata", nella lingua giusta in base al percorso
favicon.svg, favicon.ico, manifest.webmanifest, robots.txt
_redirects, _headers    redirect 301 e cache per Cloudflare Pages / Netlify (GitHub Pages li ignora)
assets/css/styles.css   stili (colori e font in :root in cima al file)
assets/js/main.js       menu mobile, slider piano/3D, modulo, galleria foto, cambio lingua
assets/fonts/           Archivo e Instrument Serif in locale (licenza OFL), nessuna chiamata a Google Fonts
assets/img/             anteprime social per lingua (og-image*.jpg), icone (iOS, Android, logo-icon.svg), foto dei progetti
```

## Modificare il sito

Il flusso è sempre lo stesso: **modifichi `src/` e poi rigeneri le pagine**.

```bash
python3 tools/build.py      # serve Python 3.11 o superiore
```

- **Cambiare un testo:** cercalo in `src/i18n.toml`. Ogni testo ha le sue tre versioni (`.es`, `.va`, `.en`) una sotto l'altra, così è difficile dimenticarne una. Si può usare HTML (`<em>`, `<strong>`, `&nbsp;`).
- **Cambiare la struttura** (sezioni, ordine, attributi): modifica `src/index.html`.
- **Aggiungere un testo nuovo:** metti `{{ sezione.chiave }}` nel modello e aggiungi `chiave.es`, `chiave.va` e `chiave.en` in `i18n.toml`.

Lo script si ferma con un errore chiaro se manca una traduzione o se il modello usa una chiave che non esiste. Segnala anche i testi che nessuno usa. Se cambi file in `src/` senza rilanciarlo, il sito pubblicato non cambia: ricordati di fare il commit anche dei file generati.

Le stringhe del JavaScript (messaggi del modulo, galleria, menu) stanno anche loro in `i18n.toml`, nella sezione `[js]`: il build le inserisce in ogni pagina.

## Vederlo in locale

```bash
python3 -m http.server 8080
# poi apri http://localhost:8080, http://localhost:8080/va/ e http://localhost:8080/en/
```

## Cose da completare prima di andare online

1. **Titoli dei progetti.** Le foto sono quelle del sito attuale (le 7 gallerie della pagina Proyectos, 23 foto), ottimizzate e senza metadati. I titoli sul vecchio sito erano generici ("Reforma parcial – Carcaixent" ×3), quindi ogni scheda ha ora un titolo che descrive ciò che si vede nelle foto ("Cocina, baño y buhardilla", "Cocina abierta con isla"…): conviene che il titolare li controlli (sono in `src/i18n.toml`, sezione `[proyectos]`). Le immagini di "Proyecto de reforma integral" sono infografie 3D, non foto di un lavoro finito, e il sito le presenta come tali.
2. **Rilettura delle traduzioni.** Il valenciano segue la norma AVL (*teua*, *estes*, *complisquen*…) e l'inglese usa l'ortografia britannica (molti residenti britannici nella Comunitat Valenciana). Conviene comunque che le faccia rileggere un madrelingua, soprattutto per il lessico del settore.
3. **Logo.** Il nuovo logo (vedi sotto) è una proposta: se all'azienda piace, è pronto; se invece ha già un logo suo e vuole tenerlo, va sostituito nei file elencati nella sezione "Logo".
4. **Testi.** Sono presi dal sito attuale e riorganizzati. È meglio che il titolare li rilegga, soprattutto la sezione "Cómo trabajamos", che mette in fila come processo cose che sul vecchio sito erano sparse. **Da confermare: "más de 30 años de experiencia".** Il dato non compare sul sito attuale né su infoisinfo; se non è esatto va corretto in `src/i18n.toml` (descrizioni `meta`, `facts.f1_*`, `perfil.years_hidden`, `footer.about`), nel numero "30+" di `src/index.html` e nelle immagini `og-image*.jpg`.
5. **Aviso legal / privacidad.** In Spagna (LSSI) un sito aziendale deve avere un avviso legale con ragione sociale, NIF e indirizzo. Serve che l'azienda fornisca questi dati.

## Foto dei progetti

Ogni progetto è una scheda in `src/index.html` (`<article data-project="…" data-gallery="…">`) con etichetta, luogo e titolo in `src/i18n.toml`. Per cambiare le foto di un progetto, o aggiungerne uno:

1. metti gli originali (così come escono dal telefono) in `fotos/<data-project>/`, ad esempio `fotos/cocina-isla-carcaixent/`. L'ordine è quello alfabetico dei file e la prima è la copertina: per sceglierla basta chiamarla `01-portada.jpg`. La cartella `fotos/` non va nel repository;
2. esegui `python3 tools/fotos.py && python3 tools/build.py` (serve `pip install pillow`, e `pillow-heif` per le foto `.heic` dell'iPhone).

`fotos.py` raddrizza le foto, converte il colore in sRGB, le riduce a 1600 px e **elimina tutti i metadati, compresa la posizione GPS**, che nelle foto di case di clienti è un dato sensibile. Le salva in `assets/img/proyectos/` (più una versione da 800 px della copertina per i telefoni) e compila da solo il `data-gallery` della scheda. `build.py` mette poi la copertina nell'HTML con testo alternativo nelle tre lingue ("Cocina y baño en Carcaixent"), dimensioni e `srcset`, controlla che tutte le foto esistano e le aggiunge alla `sitemap.xml`. Il resto lo fa il JavaScript: pulsante "Ver fotos (N)" e galleria a schermo intero. Per un progetto nuovo si copia una scheda in `src/index.html`, si cambia `data-project` e si aggiungono i suoi testi in `i18n.toml`; con `data-kind="render"` la scheda dice "infografías" invece di "fotos".

## Modulo di contatto

Il modulo non ha bisogno di un server: compone il messaggio **nella lingua della pagina** e apre **WhatsApp** (al 620 218 734) oppure il **client di posta** (construccionesf2f@gmail.com) con il testo già scritto. Il sito non salva nessun dato e quindi non ha bisogno di banner cookie. Per ricevere i messaggi direttamente per email senza passare da WhatsApp si può collegare in seguito un servizio come Formspree o Web3Forms.

## Pubblicazione

**GitHub Pages** (il repository è già su GitHub):
1. Settings → Pages → *Deploy from a branch* → scegli il branch e la cartella `/ (root)`.
2. Per il dominio: Settings → Pages → *Custom domain* → `www.f2fconstruccionesyreformas.com`, poi nel DNS del dominio crea un record `CNAME www → <utente>.github.io` e i record `A` dell'apex verso gli IP di GitHub Pages ([guida](https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site)). Abilita *Enforce HTTPS*.

In alternativa **Cloudflare Pages** o **Netlify**: collega il repository, senza comando di build, con cartella di output `/`. Le pagine generate sono già nel repository.

Se il sito attuale è su Wix con il dominio comprato lì, conviene prima trasferire il dominio (o almeno la gestione DNS) e solo dopo disdire il piano.

## Logo

Il logo è la parola **F2F**: le F in Archivo (peso 800, larghezza 125 %) e il **2 in Instrument Serif corsivo, color terracotta**. È lo stesso contrasto tra un bastoni largo e un corsivo con grazie che si vede in tutti i titoli del sito ("Construimos y reformamos, *de principio a fin*"). È generato da `tools/logo.py` a partire dalle font vere, quindi gli SVG sono tracciati e non dipendono da font installate.

| File | Uso |
|---|---|
| `src/partials/logo-wordmark.svg` | intestazione e piè di pagina (colori via CSS: `.brand__f`, `.brand__two`) |
| `assets/img/logo-icon.svg` | icona quadrata: F2F sotto una quota, su grafite |
| `favicon.svg`, `favicon.ico` | favicon: solo il 2 corsivo, leggibile anche a 16 px |
| `assets/img/apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `icon-maskable-512.png` | icone per iOS e Android |

Per rigenerare gli SVG: `pip install fonttools brotli`, poi `python3 tools/logo.py && python3 tools/build.py`. I PNG sono esportati da `logo-icon.svg` e `favicon.svg` (180, 192 e 512 px; ICO con 16/32/48 px).

## SEO

**Già fatto nel sito**

- Title e description pensati per le ricerche locali ("empresa de reformas en Alzira", "reformes a Alzira", "builders in Alzira"), nelle tre lingue e dentro i limiti che Google mostra senza tagliarli. `tools/build.py` avvisa se superano ~62/160 caratteri.
- H1 con attività e località ("Empresa de reformas y construcción en Alzira (Valencia)"), zona di lavoro (Alzira, la Ribera, provincia di Valencia) nei testi.
- Sezione **Preguntas frecuentes**: 7 domande reali, utili per le ricerche a coda lunga e per le risposte dei motori con IA ("¿qué es bajar un ascensor a cota cero?").
- Dati strutturati schema.org in un unico grafo: `GeneralContractor` (indirizzo, telefoni, mappa, zona servita, catalogo degli 8 servizi), `WebSite`, `WebPage` e `FAQPage`, nella lingua di ogni pagina. Il build verifica che il JSON-LD sia valido.
- `hreflang` e `canonical` tra le tre lingue, `sitemap.xml` con le alternative, `robots.txt`, meta `robots` con anteprime grandi, Open Graph con immagine e testo alternativo per lingua.
- Favicon in SVG e ICO (Google la mostra nei risultati), manifest, prestazioni alte (Lighthouse 97–100), CSS/JS con versione nell'URL per una cache lunga.
- Foto dei lavori con nomi di file e testi alternativi descrittivi nelle tre lingue ("Cocina abierta con isla en Carcaixent"), tutte elencate nella sitemap per Google Immagini; le copertine sono anche nella proprietà `image` dei dati strutturati.

**Da fare fuori dal sito (è quello che conta di più per la visibilità locale)**

1. **Profilo dell'attività su Google (Google Business Profile).** È ciò che fa comparire l'azienda nella mappa quando si cerca "reformas Alzira". Rivendicarlo o crearlo, verificarlo, e compilarlo:
   - categorie: *Contratista*, *Empresa de reformas*, *Empresa de construcción*;
   - servizi e zona servita;
   - orari;
   - foto dei lavori;
   - link a `https://www.f2fconstruccionesyreformas.com/`.
   Nome, indirizzo e telefono devono essere **identici** a quelli del sito.
2. **Recensioni Google** dei clienti reali: chiedere a ogni cliente soddisfatto di lasciarne una e rispondere sempre.
3. **Google Search Console** (e Bing Webmaster Tools): verificare il dominio, inviare `sitemap.xml`, controllare indicizzazione e `hreflang`. Per la verifica via meta tag basta aggiungerlo in `src/index.html` e rigenerare.
4. **Coerenza dei dati (NAP) nelle directory**: Páginas Amarillas, infoisinfo e simili devono avere lo stesso indirizzo e gli stessi telefoni del sito. Infoisinfo oggi la colloca a Llaurí. Se l'azienda ha profili social, aggiungerli a `sameAs` nel JSON-LD di `src/index.html`.
5. **Contenuti**: ora che ci sono le foto, il passo successivo è una pagina per ogni lavoro (es. "Reforma de cocina y baño en Carcaixent") con le foto e due righe su cosa si è fatto: è il contenuto che più aiuta a posizionarsi per servizio e località.
6. **Orari e fascia di prezzo**: se l'azienda li fornisce, vanno aggiunti ai dati strutturati (`openingHoursSpecification`, `priceRange`).

## Modificare l'illustrazione dell'intestazione

L'illustrazione (casa isometrica "piano ↔ 3D") è generata da `tools/hero.py` con una proiezione isometrica vera. Per cambiare colori, dimensioni o elementi modifica le costanti in cima allo script ed esegui:

```bash
python3 tools/hero.py && python3 tools/build.py
```

`hero.py` scrive le due metà dell'illustrazione in `src/partials/hero-plan.svg` e `src/partials/hero-render.svg`. I loro titoli accessibili sono le chiavi `hero.plan_alt` e `hero.render_alt` di `i18n.toml`.

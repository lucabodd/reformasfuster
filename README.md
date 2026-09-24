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
src/partials/           pezzi inseriti nel modello: icone, illustrazione, disegni dei progetti
tools/build.py          genera le pagine delle tre lingue a partire da src/
tools/hero.py           rigenera l'illustrazione isometrica dell'intestazione

index.html              ┐
va/index.html           ├ GENERATI da tools/build.py: non modificarli a mano
en/index.html           │
sitemap.xml             ┘

perfil.html, proyectos.html, contacto.html
                        reindirizzano i vecchi indirizzi /perfil, /proyectos e /contacto
                        alla sezione corrispondente (link già condivisi o indicizzati)
404.html                pagina "non trovata", nella lingua giusta in base al percorso
favicon.svg, robots.txt
assets/css/styles.css   stili (colori e font in :root in cima al file)
assets/js/main.js       menu mobile, slider piano/3D, modulo, galleria foto, cambio lingua
assets/fonts/           Archivo e Instrument Serif in locale (licenza OFL), nessuna chiamata a Google Fonts
assets/img/             anteprime social per lingua (og-image*.jpg), icona iOS, foto dei progetti
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

1. **Foto dei progetti.** Le quattro schede (Fachada Alzira, Reforma parcial Carcaixent, Reforma integral Carcaixent, Ascensor cota 0 Canals) per ora mostrano un disegno tecnico. Per metterci le foto vere:
   - carica le immagini in `assets/img/proyectos/` (JPG, lato lungo circa 1600–2000 px, massimo circa 400 KB ciascuna);
   - in `src/index.html` riempi l'attributo `data-gallery` della scheda, con i percorsi separati da virgole. I percorsi partono dalla radice del sito e valgono per tutte e tre le lingue. La prima foto fa da copertina:
     ```html
     <article class="project project--wide" data-reveal
              data-gallery="assets/img/proyectos/fachada-alzira-1.jpg, assets/img/proyectos/fachada-alzira-2.jpg">
     ```
   - esegui `python3 tools/build.py`. Il sito mostra da solo la copertina, il pulsante "Ver fotos (N)" e la galleria a schermo intero.
2. **Rilettura delle traduzioni.** Il valenciano segue la norma AVL (*teua*, *estes*, *complisquen*…) e l'inglese usa l'ortografia britannica (molti residenti britannici nella Comunitat Valenciana). Conviene comunque che le faccia rileggere un madrelingua, soprattutto per il lessico del settore.
3. **Logo.** Il marchio attuale (casetta con quota) è provvisorio. Se l'azienda ha un logo suo, va sostituito in `src/index.html` (due `<svg class="brand__mark">`), in `favicon.svg` e in `assets/img/apple-touch-icon.png`.
4. **Testi.** Sono presi dal sito attuale e riorganizzati. È meglio che il titolare li rilegga, soprattutto la sezione "Cómo trabajamos", che mette in fila come processo cose che sul vecchio sito erano sparse.
5. **Aviso legal / privacidad.** In Spagna (LSSI) un sito aziendale deve avere un avviso legale con ragione sociale, NIF e indirizzo. Serve che l'azienda fornisca questi dati.

## Modulo di contatto

Il modulo non ha bisogno di un server: compone il messaggio **nella lingua della pagina** e apre **WhatsApp** (al 620 218 734) oppure il **client di posta** (construccionesf2f@gmail.com) con il testo già scritto. Il sito non salva nessun dato e quindi non ha bisogno di banner cookie. Per ricevere i messaggi direttamente per email senza passare da WhatsApp si può collegare in seguito un servizio come Formspree o Web3Forms.

## Pubblicazione

**GitHub Pages** (il repository è già su GitHub):
1. Settings → Pages → *Deploy from a branch* → scegli il branch e la cartella `/ (root)`.
2. Per il dominio: Settings → Pages → *Custom domain* → `www.f2fconstruccionesyreformas.com`, poi nel DNS del dominio crea un record `CNAME www → <utente>.github.io` e i record `A` dell'apex verso gli IP di GitHub Pages ([guida](https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site)). Abilita *Enforce HTTPS*.

In alternativa **Cloudflare Pages** o **Netlify**: collega il repository, senza comando di build, con cartella di output `/`. Le pagine generate sono già nel repository.

Se il sito attuale è su Wix con il dominio comprato lì, conviene prima trasferire il dominio (o almeno la gestione DNS) e solo dopo disdire il piano.

## Modificare l'illustrazione dell'intestazione

L'illustrazione (casa isometrica "piano ↔ 3D") è generata da `tools/hero.py` con una proiezione isometrica vera. Per cambiare colori, dimensioni o elementi modifica le costanti in cima allo script ed esegui:

```bash
python3 tools/hero.py && python3 tools/build.py
```

`hero.py` scrive le due metà dell'illustrazione in `src/partials/hero-plan.svg` e `src/partials/hero-render.svg`. I loro titoli accessibili sono le chiavi `hero.plan_alt` e `hero.render_alt` di `i18n.toml`.

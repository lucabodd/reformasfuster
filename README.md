# Construcciones y Reformas F2F: sito web

Nuovo sito di [f2fconstruccionesyreformas.com](https://www.f2fconstruccionesyreformas.com/): stessi contenuti del sito attuale (Inicio, Perfil, Proyectos, Contacto), riorganizzati in un'unica pagina con una grafica nuova.

È un **sito statico**: HTML, CSS e un po' di JavaScript, senza WordPress, senza database, senza dipendenze e senza build. Si pubblica gratis su GitHub Pages, Cloudflare Pages o Netlify.

## Struttura

```
index.html              la pagina (tutti i testi sono qui)
perfil.html             reindirizzano i vecchi indirizzi /perfil, /proyectos e /contacto
proyectos.html          alla sezione corrispondente, così i link già condivisi
contacto.html           o indicizzati da Google continuano a funzionare
404.html                pagina "non trovata"
favicon.svg, robots.txt, sitemap.xml
assets/css/styles.css   stili (colori e font in :root in cima al file)
assets/js/main.js       menu mobile, slider piano/3D, modulo, galleria foto
assets/fonts/           Archivo e Instrument Serif in locale (licenza OFL), nessuna chiamata a Google Fonts
assets/img/             immagine di anteprima social (og-image.jpg), icona iOS, foto dei progetti
tools/hero.py           rigenera l'illustrazione isometrica dell'intestazione
```

## Vederlo in locale

```bash
python3 -m http.server 8080
# poi apri http://localhost:8080
```

## Cose da completare prima di andare online

1. **Foto dei progetti.** Le quattro schede (Fachada Alzira, Reforma parcial Carcaixent, Reforma integral Carcaixent, Ascensor cota 0 Canals) per ora mostrano un disegno tecnico. Per metterci le foto vere:
   - carica le immagini in `assets/img/proyectos/` (JPG, lato lungo circa 1600–2000 px, massimo circa 400 KB ciascuna);
   - in `index.html` riempi l'attributo `data-gallery` della scheda, con i percorsi separati da virgole. La prima foto fa da copertina:
     ```html
     <article class="project project--wide" data-reveal
              data-gallery="assets/img/proyectos/fachada-alzira-1.jpg, assets/img/proyectos/fachada-alzira-2.jpg">
     ```
   - il sito mostra da solo la copertina, il pulsante "Ver fotos (N)" e la galleria a schermo intero.
2. **Logo.** Il marchio attuale (casetta con quota) è provvisorio. Se l'azienda ha un logo suo, va sostituito in `index.html` (due `<svg class="brand__mark">`), in `favicon.svg` e in `assets/img/apple-touch-icon.png`.
3. **Testi.** Sono presi dal sito attuale e riorganizzati. È meglio che il titolare li rilegga, soprattutto la sezione "Cómo trabajamos", che mette in fila come processo cose che sul vecchio sito erano sparse.
4. **Aviso legal / privacidad.** In Spagna (LSSI) un sito aziendale deve avere un avviso legale con ragione sociale, NIF e indirizzo. Serve che l'azienda fornisca questi dati.

## Modulo di contatto

Il modulo non ha bisogno di un server: compone il messaggio e apre **WhatsApp** (al 620 218 734) oppure il **client di posta** (construccionesf2f@gmail.com) con il testo già scritto. Il sito non salva nessun dato e quindi non ha bisogno di banner cookie. Per ricevere i messaggi direttamente per email senza passare da WhatsApp si può collegare in seguito un servizio come Formspree o Web3Forms.

## Pubblicazione

**GitHub Pages** (il repository è già su GitHub):
1. Settings → Pages → *Deploy from a branch* → scegli il branch e la cartella `/ (root)`.
2. Per il dominio: Settings → Pages → *Custom domain* → `www.f2fconstruccionesyreformas.com`, poi nel DNS del dominio crea un record `CNAME www → <utente>.github.io` e i record `A` dell'apex verso gli IP di GitHub Pages ([guida](https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site)). Abilita *Enforce HTTPS*.

In alternativa **Cloudflare Pages** o **Netlify**: collega il repository, senza comando di build, con cartella di output `/`.

Se il sito attuale è su Wix con il dominio comprato lì, conviene prima trasferire il dominio (o almeno la gestione DNS) e solo dopo disdire il piano.

## Modificare l'illustrazione dell'intestazione

L'illustrazione (casa isometrica "piano ↔ 3D") è generata da `tools/hero.py` con una proiezione isometrica vera. Per cambiare colori, dimensioni o elementi modifica le costanti in cima allo script ed esegui:

```bash
python3 tools/hero.py
```

Lo script riscrive l'SVG dentro `index.html`, tra i marcatori `<!-- hero:plan -->` e `<!-- hero:render -->`.

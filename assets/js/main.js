/* Construcciones y Reformas F2F — interacciones de la web */
(() => {
  'use strict';

  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const root = document.documentElement;

  const PHONE = '34620218734';
  const EMAIL = 'construccionesf2f@gmail.com';

  /* textos en el idioma de la página: los genera tools/build.py a partir de src/i18n.toml */
  const STRINGS = (() => {
    try { return JSON.parse($('#i18n')?.textContent || '{}'); } catch { return {}; }
  })();
  const t = (key, vars = {}) => (STRINGS[key] ?? key).replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  // raíz de la web (las páginas de /va/ y /en/ están un nivel más abajo)
  const siteRoot = new URL(root.dataset.root || './', window.location.href);

  /* ------------------------------------------------------------ año del pie */
  $$('[data-year]').forEach((el) => { el.textContent = String(new Date().getFullYear()); });

  /* ------------------------------------------------------------ cabecera y botón de WhatsApp */
  const header = $('[data-header]');
  const waFloat = $('[data-wa-float]');
  const onScroll = () => {
    const y = window.scrollY;
    header?.classList.toggle('is-scrolled', y > 8);
    waFloat?.classList.toggle('is-visible', y > window.innerHeight * 0.6);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ------------------------------------------------------------ menú móvil */
  const toggle = $('[data-nav-toggle]');
  const nav = $('#menu');
  const setNav = (open) => {
    if (!toggle) return;
    root.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    $('.visually-hidden', toggle).textContent = open ? t('menu_close') : t('menu_open');
    ['#main', '.site-footer'].forEach((sel) => { const el = $(sel); if (el) el.inert = open; });
  };
  toggle?.addEventListener('click', () => setNav(toggle.getAttribute('aria-expanded') !== 'true'));
  nav?.addEventListener('click', (e) => { if (e.target.closest('a')) setNav(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && root.classList.contains('nav-open')) {
      setNav(false);
      toggle.focus();
    }
  });
  window.matchMedia('(min-width: 1200px)').addEventListener('change', (e) => { if (e.matches) setNav(false); });

  /* ------------------------------------------------------------ enlace activo del menú */
  const navLinks = $$('.nav__list a[href^="#"]');
  const spyTargets = ['#inicio', ...navLinks.map((a) => a.getAttribute('href'))].map((id) => $(id)).filter(Boolean);
  let currentSection = '';
  if ('IntersectionObserver' in window && spyTargets.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        currentSection = entry.target.id === 'inicio' ? '' : entry.target.id;
        navLinks.forEach((a) => {
          if (a.getAttribute('href') === `#${entry.target.id}`) a.setAttribute('aria-current', 'true');
          else a.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    spyTargets.forEach((section) => spy.observe(section));
  }

  /* ------------------------------------------------------------ cambio de idioma: se mantiene la sección que se está leyendo */
  $$('[data-lang-link]').forEach((a) => {
    a.addEventListener('click', () => { a.hash = currentSection ? `#${currentSection}` : ''; });
  });

  /* ------------------------------------------------------------ aparición al hacer scroll */
  const revealEls = $$('[data-reveal]');
  revealEls.forEach((el) => {
    const group = [...el.parentElement.children].filter((c) => c.hasAttribute('data-reveal'));
    const i = group.indexOf(el);
    if (i > 0) el.style.setProperty('--delay', `${Math.min(i, 7) * 70}ms`);
  });
  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.1 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('is-visible'));
  }

  /* ------------------------------------------------------------ comparador plano / visualización 3D */
  const compare = $('[data-compare]');
  if (compare) {
    const handle = $('[data-compare-handle]', compare);
    let pos = 50;
    let introFrame = 0;
    let introRunning = false;
    let drag = null;

    const set = (value) => {
      pos = Math.max(0, Math.min(100, value));
      compare.style.setProperty('--pos', `${pos}%`);
      const p = Math.round(pos);
      handle.setAttribute('aria-valuenow', String(p));
      handle.setAttribute('aria-valuetext', t('compare_value', { p, q: 100 - p }));
    };
    const stopIntro = () => {
      introRunning = false;
      cancelAnimationFrame(introFrame);
    };
    const percentAt = (clientX) => {
      const r = compare.getBoundingClientRect();
      return ((clientX - r.left) / r.width) * 100;
    };

    compare.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      stopIntro();
      drag = { id: e.pointerId, x: e.clientX, active: e.pointerType === 'mouse' };
      if (drag.active) {
        e.preventDefault();
        compare.setPointerCapture(e.pointerId);
        compare.classList.add('is-dragging');
        set(percentAt(e.clientX));
      }
    });
    compare.addEventListener('pointermove', (e) => {
      if (!drag || drag.id !== e.pointerId) return;
      // en pantallas táctiles solo arrastramos si el gesto es horizontal (el vertical hace scroll)
      if (!drag.active && Math.abs(e.clientX - drag.x) > 6) {
        drag.active = true;
        compare.setPointerCapture(e.pointerId);
        compare.classList.add('is-dragging');
      }
      if (drag.active) set(percentAt(e.clientX));
    });
    const endDrag = () => {
      drag = null;
      compare.classList.remove('is-dragging');
    };
    compare.addEventListener('pointerup', (e) => {
      if (drag && !drag.active && e.pointerType !== 'mouse') set(percentAt(e.clientX)); // toque simple
      endDrag();
    });
    compare.addEventListener('pointercancel', endDrag);

    handle.addEventListener('keydown', (e) => {
      const step = e.shiftKey ? 20 : 5;
      const keys = {
        ArrowLeft: pos - step, ArrowDown: pos - step,
        ArrowRight: pos + step, ArrowUp: pos + step,
        PageDown: pos - 20, PageUp: pos + 20,
        Home: 0, End: 100,
      };
      if (!(e.key in keys)) return;
      e.preventDefault();
      stopIntro();
      set(keys[e.key]);
    });

    if (reduceMotion) {
      compare.classList.remove('is-drawing');
      set(50);
    } else {
      // primero se dibuja el plano; después la visualización 3D "barre" hasta la mitad
      set(100);
      const start = performance.now() + 1500;
      const duration = 1500;
      const ease = (x) => 1 - Math.pow(1 - x, 3);
      introRunning = true;
      const tick = (now) => {
        if (!introRunning) return;
        const progress = Math.min(1, Math.max(0, (now - start) / duration));
        set(100 - 50 * ease(progress));
        if (progress < 1) introFrame = requestAnimationFrame(tick);
        else introRunning = false;
      };
      introFrame = requestAnimationFrame(tick);
    }
  }

  /* ------------------------------------------------------------ formulario → WhatsApp o email */
  const form = $('[data-contact-form]');
  if (form) {
    const errorBox = $('[data-form-error]', form);
    const okBox = $('[data-form-success]', form);
    const required = ['nombre', 'telefono', 'mensaje'];
    let channel = 'whatsapp';

    $$('button[type="submit"]', form).forEach((btn) => {
      btn.addEventListener('click', () => { channel = btn.value; });
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (e.submitter && e.submitter.value) channel = e.submitter.value;

      const val = (name) => (form.elements[name]?.value || '').trim();
      const missing = required.filter((name) => !val(name));
      required.forEach((name) => form.elements[name].setAttribute('aria-invalid', String(missing.includes(name))));
      if (missing.length) {
        errorBox.textContent = t('form_error');
        errorBox.hidden = false;
        okBox.hidden = true;
        form.elements[missing[0]].focus();
        return;
      }
      errorBox.hidden = true;

      const tipo = $('input[name="tipo"]:checked', form)?.value;
      const lines = [t('msg_hello', { name: val('nombre') })];
      if (tipo) lines.push(t('msg_type', { value: tipo }));
      if (val('localidad')) lines.push(t('msg_town', { value: val('localidad') }));
      lines.push(t('msg_phone', { value: val('telefono') }), '', val('mensaje'));
      const text = lines.join('\n');

      if (channel === 'email') {
        const subject = `${t('mail_subject')}${tipo ? ` – ${tipo}` : ''}`;
        window.location.href = `mailto:${EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`;
        okBox.textContent = t('form_ok_email', { email: EMAIL });
      } else {
        const url = `https://wa.me/${PHONE}?text=${encodeURIComponent(text)}`;
        const win = window.open(url, '_blank');
        if (win) win.opener = null;
        else window.location.href = url;
        okBox.textContent = t('form_ok_whatsapp');
      }
      okBox.hidden = false;
    });

    form.addEventListener('input', (e) => {
      const field = e.target;
      if (field.getAttribute('aria-invalid') === 'true' && field.value.trim()) field.setAttribute('aria-invalid', 'false');
    });
  }

  /* ------------------------------------------------------------ fotos de proyectos y galería */
  let lightbox = null;

  const buildLightbox = () => {
    const dlg = document.createElement('dialog');
    dlg.className = 'lightbox';
    dlg.setAttribute('aria-label', t('gallery_label'));
    dlg.innerHTML = `
      <div class="lightbox__stage">
        <img class="lightbox__img" alt="">
        <button class="lightbox__nav lightbox__nav--prev" type="button"><svg class="icon" aria-hidden="true"><use href="#i-chev-left"/></svg></button>
        <button class="lightbox__nav lightbox__nav--next" type="button"><svg class="icon" aria-hidden="true"><use href="#i-chev-right"/></svg></button>
      </div>
      <div class="lightbox__bar">
        <p class="lightbox__caption" aria-live="polite"></p>
        <button class="lightbox__close" type="button" autofocus><svg class="icon" aria-hidden="true"><use href="#i-close"/></svg></button>
      </div>`;
    $('.lightbox__nav--prev', dlg).setAttribute('aria-label', t('gallery_prev'));
    $('.lightbox__nav--next', dlg).setAttribute('aria-label', t('gallery_next'));
    $('.lightbox__close', dlg).setAttribute('aria-label', t('gallery_close'));
    document.body.append(dlg);

    const img = $('.lightbox__img', dlg);
    const caption = $('.lightbox__caption', dlg);
    const prev = $('.lightbox__nav--prev', dlg);
    const next = $('.lightbox__nav--next', dlg);
    const state = { photos: [], label: '', index: 0 };

    const show = (i) => {
      const n = state.photos.length;
      state.index = (i + n) % n;
      img.src = state.photos[state.index];
      img.alt = t('photo_alt', { label: state.label, n: state.index + 1, total: n });
      caption.textContent = `${state.label} · ${state.index + 1} / ${n}`;
      prev.hidden = next.hidden = n < 2;
    };

    prev.addEventListener('click', () => show(state.index - 1));
    next.addEventListener('click', () => show(state.index + 1));
    $('.lightbox__close', dlg).addEventListener('click', () => dlg.close());
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') show(state.index - 1);
      if (e.key === 'ArrowRight') show(state.index + 1);
    });

    let startX = null;
    const stage = $('.lightbox__stage', dlg);
    stage.addEventListener('pointerdown', (e) => { startX = e.clientX; });
    stage.addEventListener('pointerup', (e) => {
      if (startX === null) return;
      const dx = e.clientX - startX;
      startX = null;
      if (Math.abs(dx) > 50) show(state.index + (dx < 0 ? 1 : -1));
    });

    return {
      open(photos, label, index = 0) {
        state.photos = photos;
        state.label = label;
        show(index);
        dlg.showModal();
      },
    };
  };

  $$('[data-gallery]').forEach((card) => {
    const photos = card.dataset.gallery.split(',').map((s) => s.trim()).filter(Boolean)
      .map((src) => new URL(src, siteRoot).href);
    if (!photos.length) return;

    const title = $('h3', card)?.textContent.trim() || '';
    const place = $('.project__loc', card)?.textContent.trim();
    const label = place ? t('in_place', { title, place }) : title;
    const media = $('.project__media', card);

    const cover = new Image();
    cover.className = 'project__cover';
    cover.src = photos[0];
    cover.alt = label;
    cover.loading = 'lazy';
    cover.decoding = 'async';
    media.append(cover);
    card.classList.add('has-photos');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'project__open';
    btn.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-photo"/></svg>';
    btn.append(` ${t('view_photos', { total: photos.length })}`);
    btn.setAttribute('aria-label', `${t('view_photos', { total: photos.length })}: ${label}`);
    $('.project__body', card).append(btn);

    const open = () => {
      lightbox = lightbox || buildLightbox();
      lightbox.open(photos, label, 0);
    };
    btn.addEventListener('click', open);
    media.addEventListener('click', open);
  });
})();

// Test runner: fetches questions one by one, animates hits/misses and the HP bar.
(function () {
  'use strict';

  const root = document.getElementById('range');
  const STATE_URL = root.dataset.stateUrl;
  const ANSWER_URL = root.dataset.answerUrl;
  const CSRF = document.querySelector('meta[name="csrf-token"]').content;
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const I18N = JSON.parse(document.getElementById('i18n').textContent);

  // Translate a key; "{n}"-style params are substituted, "<key>_one" is used for n === 1
  function tr(key, params) {
    params = params || {};
    if (params.n === 1 && (key + '_one') in I18N) key += '_one';
    return (I18N[key] || key).replace(/\{(\w+)\}/g, (_, k) => (k in params ? params[k] : '{' + k + '}'));
  }

  const $ = id => document.getElementById(id);
  const els = {
    card: $('card'), qText: $('q-text'), qId: $('q-id'), answers: $('answers'),
    feedback: $('feedback'), fbBadge: $('fb-badge'), fbText: $('fb-text'), next: $('next-btn'),
    hpBar: $('hp-bar'), hpCount: $('hp-count'), hp: $('hp'),
    counter: $('q-counter'), hits: $('hits'), misses: $('misses'), progress: $('progress-fill'),
    marker: $('hit-marker'), vignette: $('vignette'),
    overlay: $('overlay'), overlayKicker: $('overlay-kicker'), overlayTitle: $('overlay-title'), overlayBtn: $('overlay-btn'),
    toast: $('toast'),
  };

  let state = null;       // latest state from the server
  let pending = null;     // state to show after the user presses "Next"
  let locked = false;     // blocks double answers
  let hpBuilt = false;

  // ------------------------------------------------------------------ network
  async function request(url, options) {
    const res = await fetch(url, Object.assign({ credentials: 'same-origin' }, options));
    const data = await res.json().catch(() => ({}));
    if (!res.ok && !data.state) throw new Error(data.error || ('HTTP ' + res.status));
    return data;
  }

  function showToast(text) {
    els.toast.textContent = text;
    els.toast.hidden = false;
    clearTimeout(showToast.t);
    showToast.t = setTimeout(() => { els.toast.hidden = true; }, 3500);
  }

  // ------------------------------------------------------------------ HP bar
  function buildHp(s) {
    els.hpBar.innerHTML = '';
    if (s.mode.unlimited) {
      els.hp.classList.add('hp-unlimited');
      const fill = document.createElement('div');
      fill.className = 'hp-seg hp-inf-bar';
      const label = document.createElement('span');
      label.textContent = tr('unlimited');
      fill.appendChild(label);
      els.hpBar.appendChild(fill);
    } else {
      for (let i = 0; i < s.hp_total; i++) {
        const seg = document.createElement('div');
        seg.className = 'hp-seg';
        seg.style.setProperty('--i', i);
        els.hpBar.appendChild(seg);
      }
    }
    hpBuilt = true;
  }

  function updateHp(s, justLost) {
    if (!hpBuilt) buildHp(s);
    if (s.mode.unlimited) {
      els.hpCount.textContent = tr('misses_count', { n: s.errors });
      return;
    }
    const segs = els.hpBar.querySelectorAll('.hp-seg');
    segs.forEach((seg, i) => {
      const alive = i < s.hp_left;
      if (!alive && !seg.classList.contains('lost')) {
        seg.classList.add('lost');
        if (justLost && !reduceMotion) {
          seg.classList.add('breaking');
          seg.addEventListener('animationend', () => seg.classList.remove('breaking'), { once: true });
        }
      }
    });
    const ratio = s.hp_left / s.hp_total;
    els.hp.dataset.level = ratio > 0.6 ? 'high' : ratio > 0.3 ? 'mid' : 'low';
    els.hp.classList.toggle('critical', s.hp_left === 1);
    const left = Math.max(s.hp_left - 1, 0);
    els.hpCount.textContent = s.hp_left === 0 ? tr('kia')
      : left === 0 ? tr('last_life') : tr('left', { n: left });
  }

  // ------------------------------------------------------------------ render
  function renderHud(s) {
    const shown = Math.min(s.position + (s.finished ? 0 : 1), s.total);
    els.counter.textContent = shown + '/' + s.total;
    els.hits.textContent = s.correct_count;
    els.misses.textContent = s.errors;
    els.progress.style.width = (100 * s.position / s.total) + '%';
  }

  function renderQuestion(s) {
    const q = s.question;
    els.feedback.hidden = true;
    els.card.classList.remove('is-hit', 'is-miss');
    els.qId.textContent = 'ID ' + q.external_id;
    els.qText.textContent = q.text;
    els.answers.innerHTML = '';
    q.options.forEach((opt, n) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'answer';
      btn.dataset.index = opt.index;
      btn.style.setProperty('--i', n);
      btn.innerHTML = '<span class="answer-key"></span><span class="answer-text"></span><span class="answer-hole" aria-hidden="true"></span>';
      btn.querySelector('.answer-key').textContent = n + 1;
      btn.querySelector('.answer-text').textContent = opt.text;
      btn.addEventListener('click', () => submit(opt.index, btn));
      els.answers.appendChild(btn);
    });
    // Re-trigger the slide-in animation
    els.card.classList.remove('enter');
    void els.card.offsetWidth;
    els.card.classList.add('enter');
    locked = false;
  }

  function render(s) {
    state = s;
    renderHud(s);
    updateHp(s, false);
    if (s.finished) { showOverlay(s); return; }
    renderQuestion(s);
  }

  // ------------------------------------------------------------------ effects
  function flashMarker(kind) {
    els.marker.className = 'hit-marker ' + kind;
    els.marker.textContent = tr(kind);
    void els.marker.offsetWidth;
    els.marker.classList.add('show');
  }

  function shake() {
    if (reduceMotion) return;
    document.body.classList.remove('shake');
    void document.body.offsetWidth;
    document.body.classList.add('shake');
    els.vignette.classList.remove('flash');
    void els.vignette.offsetWidth;
    els.vignette.classList.add('flash');
  }

  function showOverlay(s) {
    const passed = s.status === 'passed';
    const outOfHp = !s.mode.unlimited && s.hp_left === 0;
    els.overlay.classList.toggle('fail', !passed);
    els.overlayKicker.textContent = passed ? tr('all_cleared')
      : outOfHp ? tr('out_of_hp') : tr('complete');
    els.overlayTitle.textContent = passed ? tr('accomplished') : tr('failed');
    els.overlayBtn.href = s.results_url;
    els.overlay.hidden = false;
    setTimeout(() => els.overlayBtn.focus(), 50);
  }

  // ------------------------------------------------------------------ answer flow
  async function submit(choice, btn) {
    if (locked || !state || state.finished) return;
    locked = true;
    const buttons = els.answers.querySelectorAll('.answer');
    buttons.forEach(b => { b.disabled = true; });
    btn.classList.add('chosen');

    let data;
    try {
      data = await request(ANSWER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify({ question_id: state.question.id, choice: choice }),
      });
    } catch (err) {
      showToast(tr('connection'));
      buttons.forEach(b => { b.disabled = false; });
      btn.classList.remove('chosen');
      locked = false;
      return;
    }

    if (data.error) {          // stale tab / double submit: resync silently
      render(data.state);
      return;
    }

    const next = data.state;
    buttons.forEach(b => {
      const idx = +b.dataset.index;
      if (idx === data.correct_index) b.classList.add('right');
      if (idx === choice && !data.correct) b.classList.add('wrong');
      if (idx !== data.correct_index && idx !== choice) b.classList.add('dim');
    });

    renderHud(next);
    if (data.correct) {
      els.card.classList.add('is-hit');
      flashMarker('hit');
      updateHp(next, false);
    } else {
      els.card.classList.add('is-miss');
      flashMarker('miss');
      shake();
      updateHp(next, true);
    }

    pending = next;
    if (data.correct && !next.finished) {
      // Correct answers advance automatically
      setTimeout(advance, reduceMotion ? 400 : 850);
    } else {
      els.fbBadge.textContent = data.correct ? tr('hit') : tr('miss');
      els.fbBadge.className = 'fb-badge ' + (data.correct ? 'ok' : 'bad');
      els.fbText.textContent = data.correct ? tr('correct') : tr('wrong');
      els.next.innerHTML = '';
      els.next.append(tr(next.finished ? 'finish' : 'next') + ' ');
      const kbd = document.createElement('kbd');
      kbd.textContent = 'Enter';
      els.next.appendChild(kbd);
      els.feedback.hidden = false;
      els.next.focus({ preventScroll: true });
    }
  }

  function advance() {
    if (!pending) return;
    const s = pending;
    pending = null;
    render(s);
  }

  els.next.addEventListener('click', advance);

  const abortForm = document.getElementById('abort-form');
  abortForm.addEventListener('submit', e => { if (!confirm(abortForm.dataset.confirm)) e.preventDefault(); });

  document.addEventListener('keydown', e => {
    if (e.target.closest('input, textarea') || e.ctrlKey || e.metaKey || e.altKey) return;
    if (!els.overlay.hidden) return;
    if ((e.key === 'Enter' || e.key === ' ') && pending && !els.feedback.hidden) {
      e.preventDefault();
      advance();
      return;
    }
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= 9 && !locked) {
      const btn = els.answers.querySelectorAll('.answer')[n - 1];
      if (btn) btn.click();
    }
  });

  // ------------------------------------------------------------------ boot
  request(STATE_URL).then(render).catch(() => {
    els.qText.textContent = tr('load_failed');
  });
})();

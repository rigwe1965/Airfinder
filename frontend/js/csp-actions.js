/*
 * Delegated event helper so pages need no inline onclick/onchange/onsubmit handlers
 * (required for a CSP without 'unsafe-inline' in script-src).
 *
 *   <button data-click="fnName" data-args='["a", 1]'>
 *   Actions.attr('fnName', [a, 1])            -> attribute string for JS templates
 *   Actions.attr('fnName', [id, '$value'], 'change')
 *
 * Only functions passed to Actions.register() (or the built-ins below) can be invoked,
 * so markup can never name an arbitrary global. Arg tokens: '$el' (element),
 * '$event' (event), '$value' (element.value).
 */
(function () {
  const registry = Object.create(null);

  const esc = (s) => String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  const builtins = {
    unhide: (id) => document.getElementById(id)?.classList.remove('hidden'),
    hide: (id) => document.getElementById(id)?.classList.add('hidden'),
    closeOnBackdrop: (el, ev) => { if (ev.target === el) el.classList.add('hidden'); },
    navigate: (url) => { if (typeof url === 'string' && /^\/(?!\/)/.test(url)) window.location.href = url; },
    goBack: (ev) => { if (ev) ev.preventDefault(); history.back(); },
  };
  Object.assign(registry, builtins);

  function dispatch(type, ev) {
    const target = ev.target;
    const el = target && target.closest ? target.closest('[data-' + type + ']') : null;
    if (!el) return;
    const fn = registry[el.getAttribute('data-' + type)];
    if (typeof fn !== 'function') {
      console.error('Unregistered action:', el.getAttribute('data-' + type));
      return;
    }
    let args = [];
    const raw = el.getAttribute('data-args');
    if (raw) { try { args = JSON.parse(raw); } catch (e) { args = []; } }
    args = args.map((a) => (a === '$el' ? el : a === '$event' ? ev : a === '$value' ? el.value : a));
    fn.apply(el, args);
  }

  ['click', 'change', 'submit'].forEach((type) =>
    document.addEventListener(type, (ev) => dispatch(type, ev), type === 'submit'));

  window.Actions = {
    register(map) { Object.assign(registry, map); },
    attr(name, args, type) {
      const t = type || 'click';
      let out = 'data-' + t + '="' + esc(name) + '"';
      if (args && args.length) out += ' data-args="' + esc(JSON.stringify(args)) + '"';
      return out;
    },
  };
})();

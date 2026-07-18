/* ============================================================
   ui.js — P-023: three small progressive enhancements.
   Charter: wiki/FRONTEND_IDEAS.md (owner-approved JS additions).

   Everything here is *enhancement only*: with JS disabled the app
   still works exactly as before (messages render as a static list,
   card actions render as plain buttons, search works by clicking).

   Written to teach (owner is learning JS):
   - No frameworks, no build step — this file loads as-is.
   - Each feature is an IIFE ("immediately invoked function
     expression"): a function defined and called in one go, so its
     variables stay private and can't collide with other scripts.
   ============================================================ */

/* ===== A. Toast flash messages ==================================
   Django renders flash messages server-side into <div class="messages">.
   We move each one into a fixed bottom-right "toast stack", give it a
   close button, and auto-dismiss it after 4 seconds.                 */
(function () {
  var source = document.querySelector('.messages');
  if (!source) return;                       // no messages on this page

  // Build the fixed stack container once.
  var stack = document.createElement('div');
  stack.className = 'toast-stack';
  // role/aria-live: screen readers announce new toasts politely.
  stack.setAttribute('role', 'status');
  stack.setAttribute('aria-live', 'polite');
  document.body.appendChild(stack);

  function dismiss(el) {
    if (!el.parentNode) return;              // already removed
    el.classList.add('toast--leaving');      // triggers the exit animation
    el.addEventListener('animationend', function () { el.remove(); });
    // Browsers pause CSS animations in hidden tabs, so animationend may
    // never fire there — this fallback guarantees removal either way
    // (calling remove() on an already-removed node is harmless).
    setTimeout(function () { el.remove(); }, 400);
  }

  // querySelectorAll returns a NodeList; slice it into a real Array
  // so we can safely remove nodes while iterating.
  Array.prototype.slice.call(source.querySelectorAll('.message')).forEach(function (msg) {
    msg.classList.add('toast');              // reuse message--* colors, add toast layout

    var close = document.createElement('button');
    close.className = 'toast__close';
    close.setAttribute('aria-label', 'Dismiss');
    close.textContent = '×';            // "×"
    close.addEventListener('click', function () { dismiss(msg); });
    msg.appendChild(close);

    stack.appendChild(msg);                  // appendChild MOVES the node
    setTimeout(function () { dismiss(msg); }, 4000);
  });

  source.remove();                           // the (now empty) static bar
})();

/* ===== B. Note-card "⋯" action menu =============================
   note_list.html wraps the low-frequency actions (Pin/Archive/Delete)
   in <div class="card-menu"> with a toggle button. The forms inside
   keep working without JS (the menu is simply always visible then —
   CSS hides the list only when JS has run, see 'js-enabled').       */
(function () {
  // Mark <html> so CSS knows JS is available (progressive enhancement).
  document.documentElement.classList.add('js-enabled');

  function closeAll() {
    Array.prototype.slice.call(document.querySelectorAll('.card-menu.open')).forEach(function (m) {
      m.classList.remove('open');
      m.querySelector('.card-menu__toggle').setAttribute('aria-expanded', 'false');
    });
  }

  // One listener on the document handles every card ("event
  // delegation") — cheaper than one listener per card, and it keeps
  // working for cards added later.
  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('.card-menu__toggle');
    if (toggle) {
      var menu = toggle.closest('.card-menu');
      var wasOpen = menu.classList.contains('open');
      closeAll();                            // only one menu open at a time
      if (!wasOpen) {
        menu.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
      }
      e.stopPropagation();
      return;
    }
    closeAll();                              // click anywhere else closes
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeAll();
  });
})();

/* ===== C. "/" focuses the notes search ==========================
   GitHub/YouTube pattern: pressing "/" anywhere (outside a text
   field) jumps to the search box. Only active on pages that have
   the notes-list search input (#f-search).                          */
(function () {
  var search = document.getElementById('f-search');
  if (!search) return;

  // Advertise the shortcut in the placeholder.
  search.placeholder = 'Search…  ( / )';

  document.addEventListener('keydown', function (e) {
    // Ignore when the user is already typing somewhere.
    var tag = document.activeElement ? document.activeElement.tagName : '';
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (e.key !== '/') return;

    e.preventDefault();                      // don't type the "/" itself
    search.focus();
    search.select();                         // ready to overwrite an old query
  });
})();

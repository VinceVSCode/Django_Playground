/* ============================================================
   analytics_chart.js — P-019: hand-rolled analytics chart.
   Charter: wiki/FRONTEND_IDEAS.md (owner-approved JS; the
   Amendment dated 2026-07-20 covers the two new muted colors and
   the choice to hand-roll this instead of using a charting library).

   Written to teach (owner is learning JS) — read top to bottom:
     1) fetch the data from the Django API,
     2) turn it into per-period rows that keep each action's count
        separately (so we can draw colored, stacked segments),
     3) optionally drop rows outside a chosen date range,
     4) draw an SVG stacked bar chart from what's left.

   Style note: this file sticks to ui.js's conventions (var, function
   expressions, one guarded IIFE) rather than the newer const/let/arrow
   syntax, so there's one consistent JS style to learn across the app.

   Progressive enhancement: this feature needs JS (drawing a chart
   server-side would duplicate a lot of logic), but the table further
   down the analytics page shows the same numbers without JS — see
   the <noscript> note in analytics.html.
   ============================================================ */
(function () {
  var svg = document.getElementById('chart');
  if (!svg) return;                          // not on the analytics page

  var ACTION_ORDER  = ['create', 'update', 'delete', 'send'];   // fixed stacking order
  var ACTION_LABELS = { create: 'Create', update: 'Update', delete: 'Delete', send: 'Send' };
  var SVGNS = 'http://www.w3.org/2000/svg';

  var bucketSelect = document.getElementById('bucket');
  var actionsBox   = document.getElementById('actions');
  var fromInput    = document.getElementById('fromDate');
  var toInput      = document.getElementById('toDate');
  var clearBtn     = document.getElementById('clearRange');
  var legend       = document.getElementById('legend');

  // We only need a fresh fetch when the BUCKET changes — toggling actions
  // or the date range just re-filters data we already have, no extra
  // network round trip.
  var currentBucket = null;
  var currentSeries = null;

  /* --- 1) GET DATA -------------------------------------------------------
     We always ask the API for all four actions and filter client-side,
     so ticking/unticking a checkbox doesn't need another request.
       GET /api/analytics/notes/?bucket=daily
       -> { bucket, actions, series: { "<period>": { action: count, ... } } } */
  function fetchSeries(bucket) {
    var url = '/api/analytics/notes/?bucket=' + encodeURIComponent(bucket);
    // credentials: 'same-origin' sends the session cookie so the (already
    // logged-in) request is authenticated, same as any other page view.
    return fetch(url, { credentials: 'same-origin' }).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    }).then(function (json) {
      return json.series || {};
    });
  }

  /* --- 2) SHAPE DATA -------------------------------------------------------
     Keep each selected action's count (don't sum them yet — we need the
     breakdown to draw stacked, colored segments). `total` is handy for
     the y-axis scale and the number printed above each bar.
     Returns: [{ period, values:{action:count,...}, total }, ...] sorted. */
  function toStackedRows(series, selectedActions) {
    var selected = {};
    selectedActions.forEach(function (a) { selected[a] = true; });
    var periods = Object.keys(series).sort();   // "YYYY-MM-DD" sorts chronologically
    return periods.map(function (period) {
      var counts = series[period];
      var values = {};
      var total = 0;
      ACTION_ORDER.forEach(function (a) {
        if (!selected[a]) return;
        var v = counts[a] || 0;
        values[a] = v;
        total += v;
      });
      return { period: period, values: values, total: total };
    });
  }

  /* --- 3) DATE RANGE FILTER -------------------------------------------------
     Simple client-side filter over rows we've already fetched — it does
     NOT ask the server for a different range (the API has no from/to
     params today). That's a deliberate simplification: easy to extend to
     real ?from=&to= query params later without touching anything else here.

     This is simpler than it might sound: the API always reports a period
     as a full calendar date — e.g. "2026-07-14" for daily, the Monday of
     the week for weekly, the 1st of the month for monthly, Jan 1st for
     yearly (see api.py's api_note_analytics). Every period string is
     already directly comparable to an <input type="date"> value with a
     plain string comparison — no date math needed. */
  function filterByDateRange(rows, fromStr, toStr) {
    if (!fromStr && !toStr) return rows;
    return rows.filter(function (r) {
      if (fromStr && r.period < fromStr) return false;
      if (toStr && r.period > toStr) return false;
      return true;
    });
  }

  // period -> x-axis label, formatted per bucket.
  function formatPeriodLabel(period, bucket) {
    if (bucket === 'monthly') return period.slice(0, 7);   // "YYYY-MM"
    if (bucket === 'yearly')  return period.slice(0, 4);   // "YYYY"
    return period.slice(5);                                 // "MM-DD" (daily/weekly)
  }

  /* --- 4) DRAW ---------------------------------------------------------------
     Build an SVG from the rows. Coordinates: SVG y grows DOWNWARD, so a
     taller bar has a SMALLER y. For stacking: start at the bottom of the
     plot and add each action's segment on top of the previous one,
     moving the "cursor" upward.                                            */
  function el(name, attrs) {
    var node = document.createElementNS(SVGNS, name);
    for (var k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  }

  function showMessage(text) {
    svg.innerHTML = '';
    var msg = el('text', { x: 320, y: 160, class: 'chart__empty' });
    msg.textContent = text;
    svg.appendChild(msg);
  }

  function draw(rows, bucket) {
    svg.innerHTML = '';

    var W = 640, H = 320;
    var pad = { top: 24, right: 12, bottom: 40, left: 36 };
    var plotW = W - pad.left - pad.right;
    var plotH = H - pad.top - pad.bottom;

    if (rows.length === 0) {
      showMessage('No events for the chosen filters.');
      return;
    }

    // Nice round maximum for the y-axis (at least 1 so bars are visible).
    var totals = rows.map(function (r) { return r.total; });
    var rawMax = Math.max.apply(null, [1].concat(totals));
    var step = Math.max(1, Math.ceil(rawMax / 4));   // 4 gridlines
    var yMax = step * 4;

    // Horizontal gridlines + y labels at 0, step, 2*step, 3*step, 4*step.
    for (var i = 0; i <= 4; i++) {
      var val = step * i;
      var y = pad.top + plotH - (val / yMax) * plotH;   // map value -> y
      svg.appendChild(el('line', {
        x1: pad.left, y1: y, x2: pad.left + plotW, y2: y, class: 'chart__grid'
      }));
      var label = el('text', { x: pad.left - 6, y: y + 3, class: 'chart__axis-label' });
      label.setAttribute('text-anchor', 'end');
      label.textContent = val;
      svg.appendChild(label);
    }

    // Stacked bars, one column per period, evenly spaced across the plot width.
    var slot = plotW / rows.length;               // width allotted to each column
    var barW = Math.min(46, slot * 0.6);          // bar itself (with gaps)
    rows.forEach(function (r, idx) {
      var cx = pad.left + slot * idx + slot / 2;   // center of this column
      var x = cx - barW / 2;
      var yCursor = pad.top + plotH;               // start stacking from the bottom

      ACTION_ORDER.forEach(function (a) {
        var v = r.values[a];
        if (v === undefined || v <= 0) return;     // action not selected, or nothing to draw
        var h = (v / yMax) * plotH;
        var segY = yCursor - h;

        var seg = el('rect', { x: x, y: segY, width: barW, height: h, class: 'chart__seg chart__seg--' + a });
        var tip = el('title');                      // native SVG tooltip, no JS needed
        tip.textContent = ACTION_LABELS[a] + ': ' + v;
        seg.appendChild(tip);
        svg.appendChild(seg);

        yCursor = segY;                              // next segment stacks on top of this one
      });

      // Total label above the full stack (yCursor is now the top of the stack).
      if (r.total > 0) {
        var v2 = el('text', { x: cx, y: yCursor - 4, class: 'chart__value' });
        v2.textContent = r.total;
        svg.appendChild(v2);
      }

      // X-axis period label.
      var xl = el('text', { x: cx, y: pad.top + plotH + 16, class: 'chart__axis-label' });
      xl.setAttribute('text-anchor', 'middle');
      xl.textContent = formatPeriodLabel(r.period, bucket);
      svg.appendChild(xl);
    });
  }

  function drawLegend(selectedActions) {
    legend.innerHTML = '';
    ACTION_ORDER.filter(function (a) {
      return selectedActions.indexOf(a) !== -1;
    }).forEach(function (a) {
      var item = document.createElement('span');
      item.className = 'legend__item';
      item.innerHTML = '<span class="legend__swatch legend__swatch--' + a + '"></span>' + ACTION_LABELS[a];
      legend.appendChild(item);
    });
  }

  /* --- WIRING: read controls, redraw on change -------------------------------- */
  function selectedActions() {
    return Array.prototype.slice.call(actionsBox.querySelectorAll('input:checked'))
      .map(function (c) { return c.value; });
  }

  function applyFiltersAndDraw() {
    if (!currentSeries) return;                 // nothing fetched yet (or fetch failed)
    var actions = selectedActions();
    var rows = toStackedRows(currentSeries, actions);
    rows = filterByDateRange(rows, fromInput.value, toInput.value);
    draw(rows, currentBucket);
    drawLegend(actions);
  }

  function loadBucket() {
    var bucket = bucketSelect.value;
    currentBucket = bucket;
    currentSeries = null;
    legend.innerHTML = '';
    showMessage('Loading…');
    fetchSeries(bucket).then(function (series) {
      currentSeries = series;
      applyFiltersAndDraw();
    }).catch(function () {
      showMessage("Couldn't load chart data.");
    });
  }

  bucketSelect.addEventListener('change', loadBucket);
  actionsBox.addEventListener('change', applyFiltersAndDraw);
  fromInput.addEventListener('change', applyFiltersAndDraw);
  toInput.addEventListener('change', applyFiltersAndDraw);
  clearBtn.addEventListener('click', function () {
    fromInput.value = '';
    toInput.value = '';
    applyFiltersAndDraw();
  });

  loadBucket();   // initial fetch + draw, using whatever the server already selected
})();

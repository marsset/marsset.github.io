(function () {
  'use strict';
  var root = document.getElementById('dvol-live');
  if (!root) return;

  var API = 'https://www.deribit.com/api/v2/public/';
  var YEAR = 365 * 24 * 3600;
  var TIMEOUT = 8000;
  var state = { rows: null, updated: 0, btc: null, btcUpdated: 0 };
  var q = function (selector) { return root.querySelector(selector); };

  function get(url) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT);
    return fetch(url, { cache: 'no-store', signal: controller.signal })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      }).finally(function () { clearTimeout(timer); });
  }

  function api(method) {
    return get(API + method).then(function (body) {
      if (body.error || !body.result) throw new Error('Deribit data unavailable');
      return body.result;
    });
  }

  function validRows(rows) {
    if (!Array.isArray(rows)) throw new Error('Missing DVOL history');
    var points = rows.filter(function (row) {
      return Array.isArray(row) && Number.isFinite(row[0]) && row[0] > 0 &&
        Number.isFinite(row[1]) && row[1] > 0;
    }).sort(function (a, b) { return a[0] - b[0]; });
    points = points.filter(function (row, i) { return !i || row[0] !== points[i - 1][0]; });
    if (points.length < 2) throw new Error('Insufficient DVOL history');
    return points;
  }

  function stamp(time) {
    return new Date(time).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
  }

  function render() {
    if (!state.rows) return;
    var rows = state.rows, last = rows[rows.length - 1], now = last[1];
    var previous = null, dayAgo = last[0] - 86400000;
    rows.forEach(function (row) { if (row[0] <= dayAgo) previous = row; });

    q('.val').textContent = now.toFixed(2);
    q('.day').textContent = (now / Math.sqrt(365)).toFixed(2) + '%';
    q('.five').textContent = state.btc
      ? '$' + Math.round(now / 100 * Math.sqrt(300 / YEAR) * state.btc).toLocaleString()
      : (now * Math.sqrt(300 / YEAR)).toFixed(3) + '%';
    q('.btc-note').hidden = !state.btc;
    if (state.btc) {
      q('.btc').textContent = '$' + Math.round(state.btc).toLocaleString();
      q('.btc').title = 'BTC price updated ' + stamp(state.btcUpdated);
    }

    var change = q('.chg');
    if (previous) {
      var delta = now - previous[1];
      change.textContent = (delta >= 0 ? '▲ +' : '▼ −') + Math.abs(delta).toFixed(2) + ' (24h)';
      change.className = 'chg ' + (delta >= 0 ? 'up' : 'dn');
    } else {
      change.textContent = '24h change unavailable';
      change.className = 'chg';
    }

    var closes = rows.map(function (row) { return row[1]; });
    var low = Math.min.apply(null, closes), high = Math.max.apply(null, closes);
    var span = high - low || 1;
    var x = function (row) { return 3 + (row[0] - rows[0][0]) * 634 / (last[0] - rows[0][0]); };
    var y = function (value) { return 3 + (high - value) * 82 / span; };
    var path = rows.map(function (row, i) {
      return (i ? 'L' : 'M') + x(row).toFixed(1) + ' ' + y(row[1]).toFixed(1);
    }).join('');
    q('.line').setAttribute('d', path);
    q('.area').setAttribute('d', path + 'L637 88L3 88Z');
    q('.dot').setAttribute('cx', x(last).toFixed(1));
    q('.dot').setAttribute('cy', y(now).toFixed(1));
    q('.hi').textContent = high.toFixed(1);
    q('.lo').textContent = low.toFixed(1);
    q('.range-start').textContent = new Date(rows[0][0]).toISOString().slice(0, 10);
    q('.range-end').textContent = new Date(last[0]).toISOString().slice(0, 10);

    var message = 'Deribit · fetched ' + stamp(state.updated);
    if (state.btc && Math.abs(state.btcUpdated - state.updated) > 60000) {
      message += ' · BTC price ' + stamp(state.btcUpdated);
    }
    q('.stamp').textContent = message;
    root.classList.add('ready');
  }

  function history(rows, updated) {
    rows = validRows(rows);
    if (!Number.isFinite(updated) || updated <= 0) throw new Error('Missing update time');
    state.rows = rows;
    state.updated = updated;
    render();
  }

  function price(value, updated) {
    if (!Number.isFinite(value) || value <= 0 || !Number.isFinite(updated) || updated <= 0) {
      throw new Error('BTC price unavailable');
    }
    if (updated < state.btcUpdated) return;
    state.btc = value;
    state.btcUpdated = updated;
    render();
  }

  function unavailable(error) {
    state.rows = null;
    root.classList.remove('ready');
    ['.val', '.day', '.five', '.lo', '.hi', '.chg'].forEach(function (selector) {
      q(selector).textContent = '—';
    });
    q('.line').setAttribute('d', '');
    q('.area').setAttribute('d', '');
    q('.dot').setAttribute('cx', '-10');
    q('.dot').setAttribute('cy', '-10');
    q('.btc-note').hidden = true;
    q('.stamp').textContent = error && error.name === 'AbortError'
      ? 'The live Deribit request timed out. Retrying shortly.'
      : 'Live volatility data is temporarily unavailable. Retrying shortly.';
  }

  function load() {
    var end = Date.now(), start = end - 30 * 86400000;
    api('get_volatility_index_data?currency=BTC&resolution=3600&start_timestamp=' + start + '&end_timestamp=' + end)
      .then(function (result) {
        if (!Array.isArray(result.data)) throw new Error('Missing DVOL history');
        history(result.data.map(function (row) { return [row[0], row[4]]; }), Date.now());
      }).catch(unavailable);

    // A BTC price outage must never hide DVOL or its percentage-based calculations.
    api('get_index_price?index_name=btc_usd').then(function (result) {
      price(result.index_price, Date.now());
    }).catch(function () {
      state.btc = null;
      state.btcUpdated = 0;
      render();
    });
  }

  load();
  setInterval(function () { if (!document.hidden) load(); }, 60000);
})();

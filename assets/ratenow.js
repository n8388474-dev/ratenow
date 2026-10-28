(function () {
  'use strict';
  var AL = {dollar:'USD',dollars:'USD',usd:'USD',buck:'USD',bucks:'USD','$':'USD',euro:'EUR',euros:'EUR',eur:'EUR','€':'EUR',
    pound:'GBP',pounds:'GBP',gbp:'GBP','£':'GBP',sterling:'GBP',rupee:'PKR',rupees:'PKR',rupay:'PKR',rupaye:'PKR',rupya:'PKR',rs:'PKR',pkr:'PKR',
    inr:'INR',riyal:'SAR',riyals:'SAR',saudi:'SAR',sar:'SAR',dirham:'AED',dirhams:'AED',aed:'AED',uae:'AED',yuan:'CNY',rmb:'CNY',yen:'JPY',
    franc:'CHF',lira:'TRY',ringgit:'MYR',taka:'BDT',rand:'ZAR',won:'KRW',baht:'THB',peso:'PHP',dinar:'KWD',naira:'NGN',real:'BRL',zloty:'PLN',
    gold:'XAU',sona:'XAU',silver:'XAG',chandi:'XAG'};
  var MUL = {k:1e3,hazar:1e3,hazaar:1e3,lakh:1e5,lac:1e5,lack:1e5,million:1e6,m:1e6,crore:1e7,karod:1e7};

  function parse(s, known, dflt) {
    s = String(s || '').toLowerCase().replace(/[,،]/g, '').replace(/([$€£])/g, ' $1 ');
    var tk = s.split(/[^a-z0-9.$€£]+/).filter(Boolean), amt = null, cur = [], i, t, m, c;
    function push(x) { if (!cur.length || cur[cur.length - 1] !== x) cur.push(x); }
    for (i = 0; i < tk.length; i++) {
      t = tk[i]; m = t.match(/^(\d*\.?\d+)(k|m)?$/);
      if (m) {
        if (amt === null) {
          amt = parseFloat(m[1]); if (m[2]) amt *= MUL[m[2]];
          if (tk[i + 1] && MUL[tk[i + 1]]) { amt *= MUL[tk[i + 1]]; i++; }
        }
        continue;
      }
      if (t === 'indian' && tk[i + 1] && /^rupee/.test(tk[i + 1])) { push('INR'); i++; continue; }
      c = AL[t];
      if (!c && /^[a-z]{3}$/.test(t) && known && known[t.toUpperCase()]) c = t.toUpperCase();
      if (c) push(c);
    }
    if (!cur.length) return null;
    var from = cur[0], to = cur[1];
    if (!to) to = from === (dflt || 'PKR') ? 'USD' : (dflt || 'PKR');
    if (from === to) return null;
    return {amt: amt === null ? 1 : amt, from: from, to: to};
  }
  if (typeof module !== 'undefined' && module.exports) { module.exports = {parse: parse}; return; }

  var UP = window.UP || '';
  function $(id) { return document.getElementById(id); }
  function ls(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function ss(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function fmt(x) {
    var d = x >= 1000 ? 2 : x >= 100 ? 3 : x >= 1 ? 4 : 6;
    return x.toLocaleString(undefined, {maximumFractionDigits: d});
  }
  function money(x) { return x.toLocaleString(undefined, {maximumFractionDigits: Math.abs(x) >= 1 ? 2 : 4}); }
  function on(id, ev, fn) { var e = $(id); if (e) e.addEventListener(ev, fn); }
  function pairSlug(a, b) { return a.toLowerCase() + '-to-' + b.toLowerCase() + '/'; }

  // theme
  var th = ls('rn_theme', null); if (th) document.documentElement.setAttribute('data-theme', th);
  on('theme', 'click', function () {
    var cur = document.documentElement.getAttribute('data-theme') ||
      (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var nx = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nx); ss('rn_theme', nx);
  });

  // rates
  var RP = null;
  function rates() {
    if (RP) return RP;
    var el = $('rates');
    if (el) RP = Promise.resolve(JSON.parse(el.textContent));
    else RP = fetch(UP + 'data/rates.json').then(function (r) { return r.json(); }).catch(function () { return null; });
    return RP;
  }
  function conv(R, a, b, x) { return x * R.rates[b] / R.rates[a]; }

  // alerts check (on every page)
  function checkAlerts() {
    var al = ls('rn_alerts', []); if (!al.length) return;
    rates().then(function (R) {
      if (!R) return; var hit = [];
      al.forEach(function (x) {
        if (!R.rates[x.a] || !R.rates[x.b]) return;
        var r = conv(R, x.a, x.b, 1);
        if ((x.dir === 'above' && r >= x.t) || (x.dir === 'below' && r <= x.t))
          hit.push(x.a + ' to ' + x.b + ' = ' + fmt(r) + ' (' + (x.dir === 'above' ? '>=' : '<=') + ' ' + x.t + ')');
      });
      if (!hit.length) return;
      var d = document.createElement('div'); d.className = 'alertbar';
      d.textContent = '🔔 Alert: ' + hit.join(' | ');
      d.onclick = function () { d.remove(); };
      document.body.insertBefore(d, document.body.firstChild);
      try {
        if (window.Notification && Notification.permission === 'granted' && !sessionStorage.getItem('rn_n')) {
          sessionStorage.setItem('rn_n', '1'); new Notification('Rate alert', {body: hit.join('\n')});
        }
      } catch (e) {}
    });
  }


  // interactive chart
  function drawChart(box, ds, vs, range, anim) {
    var n = vs.length, s = (range && range < n) ? n - range : 0, d = ds.slice(s), v = vs.slice(s), m = v.length;
    if (m < 2 || !box) return;
    var W = 720, H = 280, L = 6, R = 74, T = 16, B = 30;
    var lo = Math.min.apply(null, v), hi = Math.max.apply(null, v), pad = (hi - lo) * 0.12 || hi * 0.002;
    lo -= pad; hi += pad;
    function X(i) { return L + (W - L - R) * i / (m - 1); }
    function Y(x) { return T + (H - T - B) * (1 - (x - lo) / (hi - lo)); }
    var g = '', k, y;
    for (k = 0; k < 4; k++) {
      y = Y(lo + (hi - lo) * k / 3).toFixed(1);
      g += '<line class="cg" x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y + '"/><text class="ct" x="' + (W - R + 8) + '" y="' + (+y + 4) + '">' + fmt(lo + (hi - lo) * k / 3) + '</text>';
    }
    var p = '', i;
    for (i = 0; i < m; i++) p += (i ? 'L' : 'M') + X(i).toFixed(1) + ',' + Y(v[i]).toFixed(1);
    var area = p + 'L' + X(m - 1).toFixed(1) + ',' + (H - B) + 'L' + X(0).toFixed(1) + ',' + (H - B) + 'Z';
    var xl = '<text class="ct" x="' + L + '" y="' + (H - 8) + '">' + d[0] + '</text>' +
      '<text class="ct" text-anchor="end" x="' + (W - R) + '" y="' + (H - 8) + '">' + d[m - 1] + '</text>';
    box.innerHTML = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Rate history, ' + d[0] + ' to ' + d[m - 1] + '">' + g +
      '<path class="ca" d="' + area + '"/><path class="cl' + (anim ? ' draw' : '') + '" pathLength="1" d="' + p + '"/>' +
      '<line class="cx" id="cx" y1="' + T + '" y2="' + (H - B) + '" x1="0" x2="0" style="display:none"/>' +
      '<circle id="cdot" class="cd" r="5" style="display:none"/>' + xl +
      '<rect id="chit" x="' + L + '" y="' + T + '" width="' + (W - L - R) + '" height="' + (H - T - B) + '" fill="transparent"/></svg><div class="tip" id="tip"></div>';
    var svg = box.querySelector('svg'), hit = $('chit'), tip = $('tip'), cx = $('cx'), dot = $('cdot');
    function move(e) {
      var r = svg.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
      var j = Math.round((px - L) / (W - L - R) * (m - 1)); j = Math.max(0, Math.min(m - 1, j));
      var x = X(j), yy = Y(v[j]);
      cx.setAttribute('x1', x); cx.setAttribute('x2', x); cx.style.display = '';
      dot.setAttribute('cx', x); dot.setAttribute('cy', yy); dot.style.display = '';
      tip.textContent = d[j] + ':  ' + fmt(v[j]); tip.style.opacity = 1;
      tip.style.left = Math.max(60, Math.min(r.width - 60, x / W * r.width)) + 'px';
    }
    function leave() { cx.style.display = 'none'; dot.style.display = 'none'; tip.style.opacity = 0; }
    hit.addEventListener('pointermove', move); hit.addEventListener('pointerdown', move); hit.addEventListener('pointerleave', leave);
  }

  // pair page
  var pdEl = $('pd'), pd = pdEl ? JSON.parse(pdEl.textContent) : null;
  if (pd) {
    var amt = $('amt'), out = $('out');
    function run() { if (amt && out) out.textContent = money((parseFloat(amt.value) || 0) * pd.r); }
    on('amt', 'input', run); run();

    var cb = $('chart');
    if (cb && pd.v && pd.v.length > 2) {
      var rb = Array.prototype.slice.call(document.querySelectorAll('.ranges button')), nn = pd.v.length, cur = nn >= 30 ? 30 : nn;
      rb.forEach(function (b) {
        var rg = parseInt(b.getAttribute('data-range'), 10);
        if (rg > nn) { b.style.display = 'none'; return; }
        b.setAttribute('aria-pressed', rg === cur ? 'true' : 'false');
        b.addEventListener('click', function () {
          rb.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
          b.setAttribute('aria-pressed', 'true'); drawChart(cb, pd.d, pd.v, rg, false);
        });
      });
      drawChart(cb, pd.d, pd.v, cur, true);
    }
    var key = pd.a + '-' + pd.b;

    if ($('fee')) {
      var fr = function () {
        var x = (parseFloat($('amt').value) || 0) * pd.r, m = Math.min(Math.max(parseFloat($('fee').value) || 0, 0), 100);
        $('feeout').textContent = money(x * (1 - m / 100)); $('feecost').textContent = money(x * m / 100);
      };
      on('fee', 'input', fr); on('amt', 'input', fr); fr();
    }
    if ($('tm') && pd.v && pd.v.length > 2) {
      var tr = function () {
        var n = pd.v.length, k = parseInt($('tm').value, 10), i = n - 1 - k, x = parseFloat($('tmamt').value) || 0;
        $('tmlab').textContent = (k === 0 ? 'today' : k + ' days ago') + ' (' + pd.d[i] + ')';
        var then = x * pd.v[i], now = x * pd.v[n - 1], df = now - then, p = then ? df / then * 100 : 0;
        $('tmout').innerHTML = x + ' ' + pd.a + ' then = <b>' + money(then) + ' ' + pd.b + '</b>, today = <b>' + money(now) + ' ' + pd.b +
          '</b>. Difference: <b class="' + (df >= 0 ? 'up' : 'down') + '">' + (df >= 0 ? '+' : '') + money(df) + ' ' + pd.b + ' (' + p.toFixed(2) + '%)</b>';
      };
      on('tm', 'input', tr); on('tmamt', 'input', tr); tr();
    }
    // favourites
    var favs = ls('rn_favs', []);
    function favBtn() { if ($('fav')) $('fav').textContent = (favs.indexOf(key) >= 0 ? 'Saved' : 'Save pair'); }
    on('fav', 'click', function () {
      var i = favs.indexOf(key); if (i >= 0) favs.splice(i, 1); else favs.push(key); ss('rn_favs', favs); favBtn();
    }); favBtn();
    var rc = ls('rn_recent', []).filter(function (x) { return x !== key; }); rc.unshift(key); ss('rn_recent', rc.slice(0, 8));
    // share
    on('share', 'click', function () {
      var txt = '1 ' + pd.a + ' = ' + fmt(pd.r) + ' ' + pd.b + ' - ' + document.title;
      if (navigator.share) navigator.share({title: document.title, text: txt, url: location.href}).catch(function () {});
      else window.open('https://wa.me/?text=' + encodeURIComponent(txt + ' ' + location.href), '_blank');
    });
    // alerts UI
    function drawAl() {
      var box = $('allist'); if (!box) return; var al = ls('rn_alerts', []); box.innerHTML = '';
      al.forEach(function (x, i) {
        var d = document.createElement('div');
        d.textContent = x.a + ' to ' + x.b + ' ' + (x.dir === 'above' ? '≥' : '≤') + ' ' + x.t + '  ✖';
        d.style.cursor = 'pointer'; d.onclick = function () { al.splice(i, 1); ss('rn_alerts', al); drawAl(); };
        box.appendChild(d);
      });
    }
    on('albtn', 'click', function () {
      var t = parseFloat($('alt').value); if (!t) { $('almsg').textContent = 'Enter a target rate.'; return; }
      var al = ls('rn_alerts', []); al.push({a: pd.a, b: pd.b, dir: $('aldir').value, t: t}); ss('rn_alerts', al);
      $('almsg').textContent = 'Alert saved. Tap an alert below to remove it.'; drawAl();
      try { if (window.Notification && Notification.permission === 'default') Notification.requestPermission(); } catch (e) {}
    }); drawAl();
  }

  // hub multi-convert
  if ($('hamt')) {
    var hr = function () {
      var x = parseFloat($('hamt').value) || 0;
      Array.prototype.forEach.call(document.querySelectorAll('table.scale tr[data-r]'), function (tr) {
        tr.querySelector('.v').textContent = fmt(x * parseFloat(tr.getAttribute('data-r')));
      });
    };
    on('hamt', 'input', hr); hr();
  }

  // home: command bar, big converter, favourites
  if ($('cmd')) {
    rates().then(function (R) {
      if (!R) return;
      var known = R.rates;
      function show() {
        var p = parse($('cmd').value, known, R.defaultRupee), o = $('cmdout');
        if (!p || !known[p.from] || !known[p.to]) { o.textContent = ''; return null; }
        var v = conv(R, p.from, p.to, p.amt), link = R.metals.indexOf(p.to) < 0 ? UP + pairSlug(p.from, p.to) : '';
        o.innerHTML = '<b>' + fmt(p.amt) + ' ' + p.from + ' = ' + fmt(v) + ' ' + p.to + '</b>' + (link ? ' <a href="' + link + '">details</a>' : '');
        return link;
      }
      on('cmd', 'input', show);
      on('cmd', 'keydown', function (e) { if (e.key === 'Enter') { var l = show(); if (l) location.href = l; } });
      Array.prototype.forEach.call(document.querySelectorAll('.chip[data-q]'), function (b) {
        b.addEventListener('click', function () { $('cmd').value = b.getAttribute('data-q'); show(); });
      });
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SR && $('mic')) {
        on('mic', 'click', function () {
          var r = new SR(); r.lang = 'en-US';
          r.onresult = function (e) { $('cmd').value = e.results[0][0].transcript; show(); };
          try { r.start(); } catch (e) {}
        });
      } else if ($('mic')) $('mic').style.display = 'none';

      var f = $('bigfrom'), t = $('bigto');
      Object.keys(R.rates).forEach(function (c) { f.add(new Option(c + ' - ' + R.names[c], c)); if (R.metals.indexOf(c) < 0) t.add(new Option(c + ' - ' + R.names[c], c)); });
      f.value = 'USD'; t.value = R.defaultRupee || 'PKR';
      var big = function () {
        var a = f.value, b = t.value, x = parseFloat($('bigamt').value) || 0;
        $('bigout').textContent = fmt(x) + ' ' + a + ' = ' + fmt(conv(R, a, b, x)) + ' ' + b;
        $('biglink').href = UP + pairSlug(a, b);
      };
      ['bigamt', 'bigfrom', 'bigto'].forEach(function (i) { on(i, 'input', big); });
      on('bigswap', 'click', function () { var x = f.value; if (R.metals.indexOf(x) >= 0) return; f.value = t.value; t.value = x; big(); }); big();

      function list(id, title, arr) {
        var el = $(id); if (!el || !arr.length) return;
        var h = '<section class="sec"><h2>' + title + '</h2><ul class="plain">', c = 0;
        arr.forEach(function (k) {
          var p = k.split('-'); if (!R.rates[p[0]] || !R.rates[p[1]]) return; c++;
          h += '<li><a href="' + UP + pairSlug(p[0], p[1]) + '"><span>' + p[0] + ' to ' + p[1] + '</span><span>' + fmt(conv(R, p[0], p[1], 1)) + '</span></a></li>';
        });
        if (c) el.innerHTML = h + '</ul></section>';
      }
      list('favs', '★ My saved pairs', ls('rn_favs', []));
      list('recent', 'Recently viewed', ls('rn_recent', []).slice(0, 6));
    });
  }

  // send money
  if ($('sfrom')) {
    rates().then(function (R) {
      var sr = function () {
        var x = parseFloat($('samt').value) || 0, m = Math.min(Math.max(parseFloat($('sfee').value) || 0, 0), 100), mid = conv(R, $('sfrom').value, 'PKR', x);
        $('sout').textContent = money(mid * (1 - m / 100)); $('smid').textContent = money(mid); $('scost').textContent = money(mid * m / 100);
      };
      ['samt', 'sfrom', 'sfee'].forEach(function (i) { on(i, 'input', sr); }); sr();
    });
  }

  // gold
  if ($('gd')) {
    var gd = JSON.parse($('gd').textContent);
    var gr = function () {
      var oz = gd[$('gc').value], g = (parseFloat($('gw').value) || 0) * parseFloat($('gu').value);
      var v = g * (oz / 31.1034768) * (parseFloat($('gk').value) / 24) * (1 + (parseFloat($('gm').value) || 0) / 100);
      $('gout').textContent = money(v) + ' ' + $('gc').value;
    };
    ['gw', 'gu', 'gk', 'gc', 'gm'].forEach(function (i) { on(i, 'input', gr); }); gr();
  }

  // widget generator
  if ($('wcode')) {
    var site = JSON.parse($('wsite').textContent);
    $('wf').value = 'USD'; $('wt').value = 'PKR';
    var wr = function () {
      var u = site + '/embed.html?from=' + $('wf').value + '&to=' + $('wt').value;
      $('wcode').value = '<iframe src="' + u + '" width="320" height="170" style="border:0" loading="lazy"></iframe>';
      $('wprev').src = u;
    };
    on('wf', 'input', wr); on('wt', 'input', wr); wr();
  }

  checkAlerts();
  if ('serviceWorker' in navigator && location.protocol.indexOf('http') === 0) {
    window.addEventListener('load', function () { navigator.serviceWorker.register(UP + 'sw.js').catch(function () {}); });
  }
})();

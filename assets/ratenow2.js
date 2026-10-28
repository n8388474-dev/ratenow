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
    var dd = dflt || 'PKR'; if (!to) to = from === dd ? (dd === 'USD' ? 'EUR' : 'USD') : dd;
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


  // ---------- location -> home currency
  var RC = {PK:'PKR',IN:'INR',AE:'AED',SA:'SAR',QA:'QAR',KW:'KWD',BH:'BHD',OM:'OMR',BD:'BDT',CN:'CNY',JP:'JPY',KR:'KRW',TH:'THB',ID:'IDR',PH:'PHP',
    MY:'MYR',SG:'SGD',HK:'HKD',TR:'TRY',EG:'EGP',NG:'NGN',KE:'KES',ZA:'ZAR',BR:'BRL',MX:'MXN',PL:'PLN',CH:'CHF',SE:'SEK',NO:'NOK',DK:'DKK',
    GB:'GBP',NZ:'NZD',CA:'CAD',AU:'AUD',US:'USD',DE:'EUR',FR:'EUR',ES:'EUR',IT:'EUR',NL:'EUR',BE:'EUR',AT:'EUR',IE:'EUR',PT:'EUR',GR:'EUR',
    FI:'EUR',EE:'EUR',LV:'EUR',LT:'EUR',SK:'EUR',SI:'EUR',LU:'EUR',MT:'EUR',HR:'EUR',CY:'EUR'};
  var TZR = {'Asia/Karachi':'PK','Asia/Kolkata':'IN','Asia/Calcutta':'IN','Asia/Dubai':'AE','Asia/Muscat':'OM','Asia/Riyadh':'SA','Asia/Qatar':'QA',
    'Asia/Kuwait':'KW','Asia/Bahrain':'BH','Asia/Dhaka':'BD','Asia/Shanghai':'CN','Asia/Urumqi':'CN','Asia/Tokyo':'JP','Asia/Seoul':'KR',
    'Asia/Bangkok':'TH','Asia/Jakarta':'ID','Asia/Makassar':'ID','Asia/Jayapura':'ID','Asia/Pontianak':'ID','Asia/Manila':'PH',
    'Asia/Kuala_Lumpur':'MY','Asia/Kuching':'MY','Asia/Singapore':'SG','Asia/Hong_Kong':'HK','Europe/Istanbul':'TR','Africa/Cairo':'EG',
    'Africa/Lagos':'NG','Africa/Nairobi':'KE','Africa/Johannesburg':'ZA','Europe/Warsaw':'PL','Europe/Zurich':'CH','Europe/Stockholm':'SE',
    'Europe/Oslo':'NO','Europe/Copenhagen':'DK','Europe/London':'GB','Pacific/Auckland':'NZ','Pacific/Honolulu':'US','Europe/Berlin':'DE',
    'Europe/Paris':'FR','Europe/Madrid':'ES','Europe/Rome':'IT','Europe/Amsterdam':'NL','Europe/Brussels':'BE','Europe/Vienna':'AT',
    'Europe/Dublin':'IE','Europe/Lisbon':'PT','Europe/Athens':'GR','Europe/Helsinki':'FI','Europe/Tallinn':'EE','Europe/Riga':'LV',
    'Europe/Vilnius':'LT','Europe/Bratislava':'SK','Europe/Ljubljana':'SI','Europe/Luxembourg':'LU','Europe/Malta':'MT','Europe/Zagreb':'HR',
    'Asia/Nicosia':'CY','Atlantic/Reykjavik':'IS'};
  function tzRegion(tz) {
    if (/^Australia\//.test(tz)) return 'AU';
    if (/^America\/(Sao_Paulo|Manaus|Fortaleza|Bahia|Recife|Belem|Cuiaba|Campo_Grande)$/.test(tz)) return 'BR';
    if (/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina|Montreal|Moncton)$/.test(tz)) return 'CA';
    if (/^America\/(Mexico_City|Cancun|Tijuana|Monterrey|Merida|Hermosillo|Chihuahua)$/.test(tz)) return 'MX';
    if (/^America\/(New_York|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Detroit|Boise|Juneau|Adak|Indiana\/|Kentucky\/|North_Dakota\/)/.test(tz)) return 'US';
    return TZR[tz] || '';
  }
  function regionName(r) {
    try { return new Intl.DisplayNames(['en'], {type: 'region'}).of(r); } catch (e) { return r; }
  }
  function homeCur(R) {
    var s = ls('rn_home', null);
    if (s && R.rates[s]) return {c: s, saved: true};
    var tz = '', reg = '', i, m, ln;
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
    reg = tzRegion(tz);
    if (!reg) {
      ln = navigator.languages || [navigator.language || ''];
      for (i = 0; i < ln.length && !reg; i++) {
        m = String(ln[i]).match(/[-_]([A-Za-z]{2})$/);
        if (m && RC[m[1].toUpperCase()]) reg = m[1].toUpperCase();
      }
    }
    var c = reg && RC[reg];
    if (!c || !R.rates[c]) return {c: R.defaultRupee || 'PKR', reg: ''};
    return {c: c, reg: reg};
  }
  function ago(ts) {
    var t = Date.parse(ts); if (!t) return '';
    var h = Math.round((Date.now() - t) / 36e5);
    if (h < 1) return 'less than an hour ago';
    if (h < 36) return h + (h === 1 ? ' hour ago' : ' hours ago');
    return Math.round(h / 24) + ' days ago';
  }
  var HP = null;
  function hist() {
    if (!HP) HP = fetch(UP + 'data/rates.json').then(function (r) { return r.json(); }).then(function (j) { return j.hist || null; }).catch(function () { return null; });
    return HP;
  }
  function series(H, c, hs) {  // 1 c in H, per day
    if (!hs || !hs.r[c] || !hs.r[H]) return [];
    var o = [], i;
    for (i = 0; i < hs.d.length; i++) if (hs.r[c][i] && hs.r[H][i]) o.push(hs.r[H][i] / hs.r[c][i]);
    return o;
  }
  function sparkSvg(v) {
    v = v.slice(-30); if (v.length < 2) return '<svg class="spark" aria-hidden="true"></svg>';
    var lo = Math.min.apply(null, v), hi = Math.max.apply(null, v), sp = (hi - lo) || 1, p = [], i;
    for (i = 0; i < v.length; i++) p.push((1 + i * 90 / (v.length - 1)).toFixed(1) + ',' + (26 - (v[i] - lo) / sp * 24).toFixed(1));
    return '<svg class="spark" viewBox="0 0 92 28" aria-hidden="true"><polyline points="' + p.join(' ') + '" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  }
  function badgeHtml(v) {
    if (v.length < 2 || !v[v.length - 2]) return '<span></span>';
    var p = (v[v.length - 1] - v[v.length - 2]) / v[v.length - 2] * 100;
    return '<span class="chg ' + (Math.abs(p) < 0.005 ? 'flat' : p > 0 ? 'up' : 'down') + '">' + Math.abs(p).toFixed(2) + '%</span>';
  }

  // ---------- amount in words
  var ONES = ['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen'];
  var TENS = ['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety'];
  function w3(n) {
    var s = '';
    if (n >= 100) { s += ONES[Math.floor(n / 100)] + ' hundred'; n %= 100; if (n) s += ' '; }
    if (n >= 20) { s += TENS[Math.floor(n / 10)]; if (n % 10) s += '-' + ONES[n % 10]; }
    else if (n > 0 || !s) s += ONES[n];
    return s;
  }
  function words(x) {
    x = Math.abs(x); if (!isFinite(x) || x >= 1e15) return '';
    var whole = Math.floor(x), cents = Math.round((x - whole) * 100);
    if (cents === 100) { whole += 1; cents = 0; }
    var sc = ['', ' thousand', ' million', ' billion', ' trillion'], parts = [], i = 0, n = whole;
    if (n === 0) parts.push('zero');
    while (n > 0) { var c = n % 1000; if (c) parts.unshift(w3(c) + sc[i]); n = Math.floor(n / 1000); i++; }
    var o = parts.join(' ');
    if (cents) o += ' and ' + (cents < 10 ? '0' : '') + cents + '/100';
    return o;
  }
  function southAsian(x) {
    x = Math.abs(x);
    if (x >= 1e7) return (x / 1e7).toLocaleString(undefined, {maximumFractionDigits: 2}) + ' crore';
    if (x >= 1e5) return (x / 1e5).toLocaleString(undefined, {maximumFractionDigits: 2}) + ' lakh';
    return '';
  }
  function wordLine(x, code, names, H) {
    var w = words(x); if (!w) return '';
    var sa = (H === 'PKR' || H === 'INR' || H === 'BDT' || code === 'PKR' || code === 'INR') ? southAsian(x) : '';
    return w.charAt(0).toUpperCase() + w.slice(1) + ' ' + ((names && names[code]) || code) + (sa ? ' (' + sa + ')' : '');
  }
  function copyText(t, btn) {
    function done() { if (btn) { var o = btn.textContent; btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = o; }, 1400); } }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function () {});
    else { var a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select(); try { document.execCommand('copy'); done(); } catch (e) {} a.remove(); }
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
    // ---- extras: chips, words, copy, presets, batch, insights, image, pocket card, drift
    var RR = null;
    Array.prototype.forEach.call(document.querySelectorAll('.qb[data-amt]'), function (b) {
      b.addEventListener('click', function () { amt.value = b.getAttribute('data-amt'); amt.dispatchEvent(new Event('input')); });
    });
    on('copybtn', 'click', function () {
      var x = parseFloat(amt.value) || 0; copyText(fmt(x) + ' ' + pd.a + ' = ' + out.textContent + ' ' + pd.b, $('copybtn'));
    });
    function runWords() {
      var el = $('words'); if (!el || !RR) return;
      el.textContent = wordLine((parseFloat(amt.value) || 0) * pd.r, pd.b, RR.names, homeCur(RR).c);
    }
    on('amt', 'input', runWords);

    on('albtn', 'click', function () {});  // keep order stable
    Array.prototype.forEach.call(document.querySelectorAll('.qb[data-preset]'), function (b) {
      b.addEventListener('click', function () {
        var p = parseFloat(b.getAttribute('data-preset')), tg = pd.r * (1 + p / 100);
        $('alt').value = +tg.toPrecision(6); $('aldir').value = p > 0 ? 'above' : 'below'; $('albtn').click();
      });
    });
    // batch list
    on('batch', 'input', function () {
      var lines = $('batch').value.split(/\n+/), h = '<table class="tbl"><tbody>';
      lines.forEach(function (ln) {
        var m = ln.toLowerCase().replace(/,/g, '').match(/(\d*\.?\d+)\s*(k|m|lakh|lac|crore|hazar)?/); if (!m) return;
        var x = parseFloat(m[1]) * (m[2] ? MUL[m[2]] : 1);
        h += '<tr><td>' + fmt(x) + ' ' + pd.a + '</td><td class="n"><b>' + money(x * pd.r) + ' ' + pd.b + '</b></td></tr>';
      });
      $('batchout').innerHTML = lines.join('').trim() ? h + '</tbody></table>' : '';
    });
    // patterns
    (function () {
      var v = pd.v, d = pd.d, n = v ? v.length : 0; if (n < 10) return;
      var ch = [], i, up = 0, dn = 0, big = {p: 0, i: 1}, sum = 0;
      for (i = 1; i < n; i++) { var p = (v[i] - v[i - 1]) / v[i - 1] * 100; ch.push(p); if (p > 0) up++; else if (p < 0) dn++; sum += Math.abs(p); if (Math.abs(p) > Math.abs(big.p)) big = {p: p, i: i}; }
      var st = 1, dir = ch[ch.length - 1] >= 0 ? 1 : -1; for (i = ch.length - 2; i >= 0 && (ch[i] >= 0 ? 1 : -1) === dir; i--) st++;
      var w = v.slice(-30), lo = Math.min.apply(null, w), hi = Math.max.apply(null, w), pos = hi > lo ? Math.round((v[n - 1] - lo) / (hi - lo) * 100) : 50;
      var a7 = v.slice(-7).reduce(function (s, x) { return s + x; }, 0) / Math.min(7, n), vs7 = (v[n - 1] - a7) / a7 * 100;
      var li = [
        'Over the last ' + ch.length + ' days, ' + pd.a + ' rose against ' + pd.b + ' on ' + up + ' days and fell on ' + dn + '.',
        (st === 1 ? 'The last move was ' + (dir > 0 ? 'up' : 'down') + '.' : 'It has moved ' + (dir > 0 ? 'up' : 'down') + ' for ' + st + ' days in a row.'),
        'Today sits at ' + pos + '% of the 30-day range (0% is the lowest, 100% the highest).',
        'The biggest one-day move was ' + (big.p >= 0 ? '+' : '') + big.p.toFixed(2) + '% on ' + d[big.i] + '. A typical day moves ' + (sum / ch.length).toFixed(2) + '%.',
        'Today is ' + Math.abs(vs7).toFixed(2) + '% ' + (vs7 >= 0 ? 'above' : 'below') + ' the 7-day average.'
      ];
      $('insx').innerHTML = li.map(function (x) { return '<li>' + x + '</li>'; }).join('');
      $('insn').textContent = 'These are counts from past rates, not a forecast or advice.';
      $('insx-sec').hidden = false;
    })();
    // image share
    on('shareimg', 'click', function () {
      var c = document.createElement('canvas'); c.width = 1200; c.height = 630; var g = c.getContext('2d');
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      g.fillStyle = '#134234'; g.fillRect(0, 0, 1200, 630);
      g.strokeStyle = 'rgba(255,255,255,.07)'; g.lineWidth = 2;
      for (var k = 0; k < 24; k++) { g.beginPath(); for (var x = 0; x <= 1200; x += 20) { var y = 300 + (k - 12) * 18 + 40 * Math.sin(x / 90 + k * .16); x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
      var fam = 'Bricolage Grotesque, Georgia, serif';
      g.fillStyle = '#e8c76a'; g.font = '600 30px ' + fam; g.fillText(location.host, 70, 90);
      g.fillStyle = '#bfe8d4'; g.font = '400 30px Public Sans, Arial, sans-serif'; g.fillText(pd.a + ' to ' + pd.b + '  ·  ' + (document.querySelector('.pmeta') ? '' : ''), 70, 210);
      g.fillStyle = '#fff'; g.font = '700 96px ' + fam; g.fillText('1 ' + pd.a + ' = ' + fmt(pd.r), 70, 330);
      g.font = '600 56px ' + fam; g.fillText(pd.b, 70, 405);
      var vv = pd.v.slice(-30);
      if (vv.length > 2) {
        var l2 = Math.min.apply(null, vv), h2 = Math.max.apply(null, vv); g.strokeStyle = '#7fe3a9'; g.lineWidth = 5; g.beginPath();
        vv.forEach(function (q, i) { var px = 70 + i * 1060 / (vv.length - 1), py = 560 - (q - l2) / ((h2 - l2) || 1) * 110; i ? g.lineTo(px, py) : g.moveTo(px, py); }); g.stroke();
      }
      g.fillStyle = '#bfe8d4'; g.font = '400 24px Public Sans, Arial, sans-serif'; g.fillText(pd.d[pd.d.length - 1] + '  ·  ' + location.host + location.pathname, 70, 605);
      c.toBlob(function (b) {
        if (!b) return;
        var file = new File([b], pd.a.toLowerCase() + '-' + pd.b.toLowerCase() + '.png', {type: 'image/png'});
        if (navigator.canShare && navigator.canShare({files: [file]})) navigator.share({files: [file], title: document.title}).catch(function () {});
        else { var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = file.name; a.click(); }
      });
    });
    // pocket card
    on('printcard', 'click', function () {
      var amts = [1, 5, 10, 20, 50, 100, 200, 500, 1000, 5000], h = '<h2>' + pd.a + ' to ' + pd.b + '</h2><p>Rate ' + pd.d[pd.d.length - 1] + ': 1 ' + pd.a + ' = ' + fmt(pd.r) + ' ' + pd.b + '</p><table>';
      amts.forEach(function (x) { h += '<tr><td>' + fmt(x) + ' ' + pd.a + '</td><td>' + money(x * pd.r) + ' ' + pd.b + '</td></tr>'; });
      var el = document.createElement('div'); el.id = 'pocket'; el.className = 'pocket'; el.innerHTML = h + '</table><p class="s">Cut out and keep in your wallet. Rates change daily. ' + location.host + '</p>';
      document.body.appendChild(el); document.documentElement.classList.add('pocketing');
      var done = function () { document.documentElement.classList.remove('pocketing'); el.remove(); window.removeEventListener('afterprint', done); };
      window.addEventListener('afterprint', done); window.print();
    });
    // your currency + drift since last visit + urdu hint
    rates().then(function (R) {
      if (!R) return; RR = R; runWords();
      var H = homeCur(R).c, m = $('mycur'), h = '';
      if (m) {
        if (H !== pd.a && H !== pd.b && R.rates[H] && R.metals.indexOf(H) < 0) {
          h += '<p class="note">In your currency (' + H + '): 1 ' + pd.a + ' = <b>' + fmt(conv(R, pd.a, H, 1)) + ' ' + H + '</b>, 1 ' + pd.b + ' = <b>' + fmt(conv(R, pd.b, H, 1)) + ' ' + H + '</b>.</p>';
        }
        var seen = ls('rn_seen', {}), s = seen[key];
        if (s && s.d && s.d !== R.date && s.r) {
          var pc = (pd.r - s.r) / s.r * 100;
          h += '<p class="note">Since your last visit (' + s.d + '): ' + (pc >= 0 ? '+' : '') + pc.toFixed(2) + '% (' + fmt(s.r) + ' then, ' + fmt(pd.r) + ' now).</p>';
        }
        seen[key] = {d: R.date, r: pd.r}; var ks = Object.keys(seen); if (ks.length > 60) delete seen[ks[0]]; ss('rn_seen', seen);
        if (R.ts) h += '<p class="note">Rates updated ' + ago(R.ts) + '.</p>';
        m.innerHTML = h;
      }
    });
    var ub = $('urbar');
    if (ub && (navigator.languages || [navigator.language]).some(function (l) { return /^ur/i.test(l || ''); })) {
      ub.innerHTML = '<a href="' + ub.getAttribute('data-href') + '">اردو میں دیکھیں</a>'; ub.hidden = false;
    }
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

  // home: command bar, big converter, favourites, local currency
  if ($('cmd')) {
    rates().then(function (R) {
      if (!R) return;
      var known = R.rates, info = homeCur(R), H = info.c, hs = null;
      var orig = {brows: $('brows') && $('brows').innerHTML, rtb: $('rtb') && $('rtb').innerHTML,
        bh1: $('bh1') && $('bh1').textContent, rh: $('rh') && $('rh').textContent, rcol: $('rcol') && $('rcol').textContent};
      var nonMetal = Object.keys(R.rates).filter(function (c) { return R.metals.indexOf(c) < 0; });
      var f = $('bigfrom'), t = $('bigto'), rebuilt = false;

      function show() {
        var p = parse($('cmd').value, known, H), o = $('cmdout');
        if (!p || !known[p.from] || !known[p.to]) { o.textContent = ''; return null; }
        var v = conv(R, p.from, p.to, p.amt), link = R.metals.indexOf(p.to) < 0 ? UP + pairSlug(p.from, p.to) : '';
        o.innerHTML = '<b>' + fmt(p.amt) + ' ' + p.from + ' = ' + fmt(v) + ' ' + p.to + '</b>' + (link ? ' <a href="' + link + '">details</a>' : '');
        return link;
      }
      on('cmd', 'input', show);
      on('cmd', 'keydown', function (e) { if (e.key === 'Enter') { var l = show(); if (l) location.href = l; } });
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SR && $('mic')) {
        on('mic', 'click', function () {
          var r = new SR(); r.lang = 'en-US';
          r.onresult = function (e) { $('cmd').value = e.results[0][0].transcript; show(); };
          try { r.start(); } catch (e) {}
        });
      } else if ($('mic')) $('mic').style.display = 'none';

      Object.keys(R.rates).forEach(function (c) { f.add(new Option(c + ' - ' + R.names[c], c)); if (R.metals.indexOf(c) < 0) t.add(new Option(c + ' - ' + R.names[c], c)); });
      function big() {
        var a = f.value, b = t.value, x = parseFloat($('bigamt').value) || 0, v = conv(R, a, b, x);
        $('bigout').textContent = fmt(x) + ' ' + a + ' = ' + fmt(v) + ' ' + b;
        $('bigwords').textContent = wordLine(v, b, R.names, H);
        $('biglink').href = UP + pairSlug(a, b);
      }
      ['bigamt', 'bigfrom', 'bigto'].forEach(function (i) { on(i, 'input', big); });
      on('bigswap', 'click', function () { var x = f.value; if (R.metals.indexOf(x) >= 0) return; f.value = t.value; t.value = x; big(); });
      Array.prototype.forEach.call(document.querySelectorAll('.qb[data-bamt]'), function (b) {
        b.addEventListener('click', function () { $('bigamt').value = b.getAttribute('data-bamt'); big(); });
      });
      on('bigcopy', 'click', function () { copyText($('bigout').textContent, $('bigcopy')); });

      function rowsFor() {
        var order = ['USD','EUR','GBP','AED','SAR','CAD','AUD','CHF','CNY','INR','JPY','PKR'].filter(function (c) { return c !== H && known[c]; }).slice(0, 5);
        var h = '';
        order.forEach(function (c) {
          var v = series(H, c, hs);
          h += '<a class="brow" href="' + UP + pairSlug(c, H) + '"><span class="bcode">' + c + '<small>' + R.names[c] + '</small></span><span class="bval">' + fmt(conv(R, c, H, 1)) +
            '</span>' + badgeHtml(v) + '<span class="spark">' + sparkSvg(v) + '</span></a>';
        });
        if (known.XAU) {
          var g = series(H, 'XAU', hs);
          h += '<a class="brow" href="' + UP + pairSlug('XAU', H) + '"><span class="bcode">Gold<small>1 troy ounce</small></span><span class="bval">' +
            Math.round(conv(R, 'XAU', H, 1)).toLocaleString() + '</span>' + badgeHtml(g) + '<span class="spark">' + sparkSvg(g) + '</span></a>';
        }
        return h;
      }
      function tableFor() {
        var h = '';
        nonMetal.forEach(function (c) {
          if (c === H) return; var v = series(H, c, hs);
          h += '<tr><td><a href="' + UP + pairSlug(c, H) + '">' + c + '</a><small>' + R.names[c] + '</small></td><td class="n">' + fmt(conv(R, c, H, 1)) +
            '</td><td class="n">' + (badgeHtml(v).replace('<span></span>', '')) + '</td><td class="n"><span class="spark" style="margin-left:auto">' + sparkSvg(v) + '</span></td></tr>';
        });
        return h;
      }
      function movers() {
        var el = $('movehint'); if (!el || !hs) return; var best = null, worst = null;
        nonMetal.forEach(function (c) {
          if (c === H) return; var v = series(H, c, hs); if (v.length < 2) return;
          var p = (v[v.length - 1] - v[v.length - 2]) / v[v.length - 2] * 100;
          if (!best || p > best.p) best = {c: c, p: p}; if (!worst || p < worst.p) worst = {c: c, p: p};
        });
        if (!best) { el.textContent = ''; return; }
        el.innerHTML = 'Against ' + H + ' today: <a href="' + UP + pairSlug(best.c, H) + '">' + best.c + ' ' + (best.p >= 0 ? '+' : '') + best.p.toFixed(2) + '%</a> (strongest), <a href="' +
          UP + pairSlug(worst.c, H) + '">' + worst.c + ' ' + (worst.p >= 0 ? '+' : '') + worst.p.toFixed(2) + '%</a> (weakest).';
      }
      function apply(first) {
        var homeSrv = (H === (R.defaultRupee || 'PKR'));
        if (homeSrv) {
          if (rebuilt && $('brows')) { $('brows').innerHTML = orig.brows; $('rtb').innerHTML = orig.rtb; $('bh1').textContent = orig.bh1; $('rh').textContent = orig.rh; $('rcol').textContent = orig.rcol; }
          rebuilt = false;
        } else {
          if ($('brows')) $('brows').innerHTML = rowsFor();
          if ($('rtb')) $('rtb').innerHTML = tableFor();
          if ($('bh1')) $('bh1').textContent = '1 unit in ' + R.names[H];
          if ($('rh')) $('rh').textContent = R.names[H] + ' rates today';
          if ($('rcol')) $('rcol').textContent = '1 unit in ' + H;
          rebuilt = true;
        }
        if ($('bh2')) $('bh2').textContent = R.date;
        var base = H === 'USD' ? 'EUR' : 'USD';
        f.value = base; t.value = H;
        var lw = H.toLowerCase(), o1 = base === 'EUR' ? 'gbp' : 'eur', o2 = (H === 'GBP' || o1 === 'gbp') ? 'aed' : 'gbp';
        var ex = [['500 ' + base.toLowerCase() + ' to ' + lw], ['100 ' + o1 + ' in ' + lw], ['5k ' + o2 + ' in ' + lw], ['gold']];
        var tr = document.querySelector('.try');
        if (tr) tr.innerHTML = 'Try ' + ex.map(function (q) { return '<button type="button" class="chip" data-q="' + q[0] + '">' + q[0] + '</button>'; }).join('');
        Array.prototype.forEach.call(document.querySelectorAll('.chip[data-q]'), function (b) {
          b.addEventListener('click', function () { $('cmd').value = b.getAttribute('data-q'); show(); });
        });
        $('cmd').placeholder = '500 dollar in ' + R.names[H].split(' ').pop().toLowerCase() + 's';
        var lc = $('loc'); if (lc) {
          var nm = info.reg ? regionName(info.reg) : '', why = info.saved ? 'your saved choice' : (nm ? 'your location (' + nm + ')' : 'our default, since no location was detected');
          lc.innerHTML = 'Rates shown in <b>' + R.names[H] + ' (' + H + ')</b>, from ' + why + '. <select id="homesel" aria-label="Change your currency"></select>' +
            ' <span class="muted">Updated ' + (ago(R.ts) || R.date) + '. Your location never leaves this device.</span>';
          var sel = $('homesel');
          nonMetal.forEach(function (c) { sel.add(new Option(c + ' - ' + R.names[c], c)); });
          sel.value = H;
          sel.addEventListener('change', function () { H = sel.value; info = {c: H, saved: true}; ss('rn_home', H); apply(false); });
        }
        big(); movers(); show();
      }
      apply(true);
      hist().then(function (h) { if (!h) return; hs = h; apply(false); });
      if (!$('movehint') && $('loc')) { var mh = document.createElement('p'); mh.id = 'movehint'; mh.className = 'loc'; $('loc').parentNode.insertBefore(mh, $('loc').nextSibling); }

      function list(id, title, arr) {
        var el = $(id); if (!el || !arr.length) return;
        var h = '<section class="sec"><h2>' + title + '</h2><ul class="plain">', c = 0;
        arr.forEach(function (k) {
          var p = k.split('-'); if (!R.rates[p[0]] || !R.rates[p[1]]) return; c++;
          h += '<li><a href="' + UP + pairSlug(p[0], p[1]) + '"><span>' + p[0] + ' to ' + p[1] + '</span><span>' + fmt(conv(R, p[0], p[1], 1)) + '</span></a></li>';
        });
        if (c) el.innerHTML = h + '</ul></section>';
      }
      list('favs', 'My saved pairs', ls('rn_favs', []));
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

  // offline bar, install, shortcuts
  (function () {
    var ob = $('offline');
    function net() { if (ob) ob.hidden = navigator.onLine !== false; }
    window.addEventListener('online', net); window.addEventListener('offline', net); net();
    var ip = null, ib = $('install');
    window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); ip = e; if (ib) ib.hidden = false; });
    if (ib) ib.addEventListener('click', function () { if (ip) { ip.prompt(); ip = null; ib.hidden = true; } });
    window.addEventListener('appinstalled', function () { if (ib) ib.hidden = true; });
    document.addEventListener('keydown', function (e) {
      var tg = e.target && e.target.tagName; if (/INPUT|TEXTAREA|SELECT/.test(tg || '') || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === '/') { var i = $('cmd') || $('amt') || $('hamt') || $('samt'); if (i) { e.preventDefault(); i.focus(); if (i.select) i.select(); } }
      else if (e.key === 't') { var th2 = $('theme'); if (th2) th2.click(); }
      else if (e.key === 's') { var a = document.querySelector('.pmeta a'); if (a) location.href = a.href; }
    });
  })();

  checkAlerts();
  if ('serviceWorker' in navigator && location.protocol.indexOf('http') === 0) {
    window.addEventListener('load', function () { navigator.serviceWorker.register(UP + 'sw.js').catch(function () {}); });
  }
})();

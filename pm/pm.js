/* =====================================================================
   Simulador de Postman — motor compartido por las diapositivas de la Parte 2

   Uso:
     PMLab.mount(document.getElementById('lab'), {
       state: { ... estado inicial (ver BASE) ... },
       steps: [
         { t:'Título del paso', d:'Explicación (HTML)', hl:'url',
           set:{ req:{ url:'https://...' } },   // cambios al estado (se mezclan)
           fn: s => { ... },                     // o cambios con una función
           type:'req.url' }                      // campo que se "escribe" letra por letra
       ]
     });

   Zonas que se pueden resaltar (hl): ws, search, side, side-add, rail-col, rail-env, rail-hist,
   tabs, plus, env, crumb, save, method, url, send, rt-params, rt-auth, rt-headers, rt-body,
   rt-scripts, ed, resp, status, time, size, rbody, rtests, modal, menu, item:<nombre>, view,
   var:<nombre>, share:<nombre> (env con cloud:true; var[4] = 'local' | 'shared')
   ===================================================================== */
(function () {
  const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const clone = o => JSON.parse(JSON.stringify(o));

  const BASE = {
    ws: 'My Workspace', side: 'collections', view: 'request',
    cols: [], envs: [], env: 'No environment',
    tabs: [{ name: 'Untitled Request', m: 'GET' }], active: 0,
    req: { name: 'Untitled Request', col: null, method: 'GET', url: '', rtab: 'params',
           headers: [], auth: { type: 'No Auth' }, body: { mode: 'none', raw: '' },
           pre: '', post: '', stab: 'post', saved: true },
    res: null, envEdit: null, viewHtml: '', modal: null, menu: null, hl: null, typing: null,
  };

  function merge(a, b) {
    for (const k in b) {
      if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && a[k] && typeof a[k] === 'object' && !Array.isArray(a[k])) merge(a[k], b[k]);
      else a[k] = clone(b[k]);
    }
    return a;
  }
  const getPath = (o, p) => p.split('.').reduce((x, k) => x?.[k], o);
  const setPath = (o, p, v) => { const ks = p.split('.'); const last = ks.pop(); ks.reduce((x, k) => x[k], o)[last] = v; };

  /* ---------- resaltado de JSON y JS ---------- */
  function hlJson(txt) {
    return esc(txt)
      .replace(/(&quot;|")((?:\\.|[^"\\])*)(")(\s*:)/g, '<span class="jk">"$2"</span>$4')
      .replace(/:\s*"((?:\\.|[^"\\])*)"/g, ': <span class="js">"$1"</span>')
      .replace(/(\[|,|^)\s*"((?:\\.|[^"\\])*)"(?=\s*[,\]])/gm, (m, a, b) => `${a} <span class="js">"${b}"</span>`)
      .replace(/:\s*(-?\d+(\.\d+)?)(?=\s*(,|\}|\]|$))/gm, ': <span class="jn">$1</span>')
      .replace(/:\s*(true|false|null)(?=\s*(,|\}|\]|$))/gm, ': <span class="jb">$1</span>');
  }
  function hlJs(txt) {
    return esc(txt)
      .replace(/(\/\/.*)$/gm, '<span class="jc">$1</span>')
      .replace(/('[^']*'|"[^"]*"|`[^`]*`)/g, '<span class="js">$1</span>')
      .replace(/\b(const|let|var|function|return|if|else|true|false)\b/g, '<span class="jb">$1</span>')
      .replace(/\b(pm|console)\b/g, '<span class="jf">$1</span>');
  }
  function urlHtml(u, s) {
    if (!u) return '<span class="ph">Enter URL or paste text</span>';
    const known = new Set([...(s.envs || []).flatMap(e => (e.vars || []).map(v => v[0]))]);
    return esc(u).replace(/\{\{([^}]+)\}\}/g, (m, n) => `<span class="var ${known.has(n) ? 'ok' : ''}">{{${n}}}</span>`);
  }
  function queryParams(u) {
    const i = (u || '').indexOf('?'); if (i < 0) return [];
    return u.slice(i + 1).split('&').filter(Boolean).map(p => { const [k, ...v] = p.split('='); return [k, v.join('=')]; });
  }
  function pathVars(u) { return [...(u || '').matchAll(/\/:([A-Za-z_]\w*)/g)].map(m => m[1]); }

  /* ---------- render ---------- */
  function render(s) {
    const r = s.req, H = (t) => `data-t="${t}"`;
    const methodCls = 'm' + r.method;
    const tree = renderSide(s);
    const tab = s.tabs[s.active] || {};
    const main = s.view === 'env' ? renderEnv(s) : s.view === 'runner' ? renderRunner(s) : s.view === 'html' ? `<div class="pm-view" ${H('view')}>${s.viewHtml}</div>` : renderRequest(s);
    return `
    <div class="pm-top">
      <span class="logo">✱</span><span class="nav">Home</span>
      <span class="ws" ${H('ws')}>▦ ${esc(s.ws)} ▾</span><span class="nav">API Network</span>
      <span class="search" ${H('search')}>🔍 Search Postman</span>
      <span class="r"><span class="inv">Invite</span><span>⚙</span><span class="av">QA</span></span>
    </div>
    <div class="pm-body">
      <div class="pm-rail">
        <div class="${s.side === 'collections' ? 'on' : ''}" ${H('rail-col')}><i>▤</i>Collections</div>
        <div class="${s.side === 'environments' ? 'on' : ''}" ${H('rail-env')}><i>▣</i>Environments</div>
        <div class="${s.side === 'history' ? 'on' : ''}" ${H('rail-hist')}><i>↺</i>History</div>
      </div>
      <div class="pm-side" ${H('side')}>${tree}</div>
      <div class="pm-main">
        <div class="pm-tabs" ${H('tabs')}>
          ${s.tabs.map((t, i) => `<span class="tab ${i === s.active ? 'on' : ''}"><span class="m m${t.m || 'GET'}">${t.m || ''}</span>${esc(t.name)}${t.dirty ? ' ●' : ''}</span>`).join('')}
          <span class="plus" ${H('plus')}>＋</span>
          <span class="env" ${H('env')}><span>${esc(s.env)}</span>▾</span>
        </div>
        ${main}
      </div>
    </div>
    ${s.menu ? renderMenu(s) : ''}
    ${s.modal ? renderModal(s) : ''}`;
  }

  function renderSide(s) {
    if (s.side === 'environments') {
      const envs = s.envs || [];
      return `<div class="sh"><b>Environments</b><span data-t="side-add">＋</span></div><div class="tree">
        ${envs.length ? envs.map(e => `<div class="it ${s.view === 'env' && s.envEdit === e.name ? 'sel' : ''}" data-t="item:${esc(e.name)}">${e.name === 'Globals' ? '🌐' : '▣'} ${esc(e.name)}${s.env === e.name ? ' <span style="color:#6bdd9a">✓</span>' : ''}</div>`).join('')
          : '<div class="empty">Sin environments todavía.</div>'}</div>`;
    }
    if (s.side === 'history') {
      return `<div class="sh"><b>History</b></div><div class="tree">${(s.history || []).map(h => `<div class="it"><span class="m m${h[0]}">${h[0]}</span>${esc(h[1])}</div>`).join('') || '<div class="empty">Aquí aparecen los requests enviados.</div>'}</div>`;
    }
    const item = (it, depth) => {
      if (it.items) return `<div class="it ${it.sel ? 'sel' : ''}" data-t="item:${esc(it.name)}" style="padding-left:${10 + depth * 12}px"><span class="ch">${it.open === false ? '▸' : '▾'}</span>${depth ? '📁' : '🗂'} ${esc(it.name)}</div>`
        + (it.open === false ? '' : it.items.map(x => item(x, depth + 1)).join(''));
      return `<div class="it ${it.sel ? 'sel' : ''}" data-t="item:${esc(it.name)}" style="padding-left:${10 + depth * 12}px"><span class="m m${it.m}">${it.m}</span>${esc(it.name)}</div>`;
    };
    return `<div class="sh"><b>Collections</b><span data-t="side-add">＋</span><span>⋯</span></div><div class="tree">
      ${s.cols.length ? s.cols.map(c => item(c, 0)).join('') : '<div class="empty">Aún no tienes colecciones.<br>Crea una con <b>＋</b>.</div>'}</div>`;
  }

  function renderRequest(s) {
    const r = s.req, H = (t) => `data-t="${t}"`;
    const qp = queryParams(r.url), pv = pathVars(r.url);
    const hdrCount = (r.headers || []).length + (r.body.mode === 'raw' ? 1 : 0) + (r.auth.type !== 'No Auth' && r.auth.type !== 'Inherit' ? 1 : 0);
    let ed = '';
    if (r.rtab === 'params') {
      ed = `<div style="color:var(--p-mut);font-size:11px;margin-bottom:4px">Query Params</div><table class="pm-kv"><tr><th></th><th>Key</th><th>Value</th><th>Description</th></tr>
        ${qp.map(([k, v]) => `<tr><td class="ck">☑</td><td>${esc(k)}</td><td>${esc(v)}</td><td></td></tr>`).join('')}<tr class="ph"><td></td><td>Key</td><td>Value</td><td>Description</td></tr></table>`
        + (pv.length ? `<div style="color:var(--p-mut);font-size:11px;margin:8px 0 4px">Path Variables</div><table class="pm-kv"><tr><th>Key</th><th>Value</th></tr>${pv.map(k => `<tr><td>${k}</td><td>${esc((r.pathVals || {})[k] || '')}</td></tr>`).join('')}</table>` : '');
    } else if (r.rtab === 'auth') {
      const a = r.auth;
      const flds = a.type === 'Basic Auth' ? [['Username', a.user], ['Password', a.pass ? '•'.repeat(Math.min(12, a.pass.length)) + (a.showPass ? `  (${a.pass})` : '') : '']]
        : a.type === 'API Key' ? [['Key', a.key], ['Value', a.value], ['Add to', a.addTo || 'Header']]
        : a.type === 'Bearer Token' ? [['Token', a.token]] : [];
      ed = `<div class="pm-auth"><div class="lft">Auth Type<div class="sel" data-t="auth-type">${a.type === 'Inherit' ? 'Inherit auth from parent' : esc(a.type)} ▾</div><div style="margin-top:8px">${a.type === 'No Auth' ? 'Este request no usa autorización.' : a.type === 'Inherit' ? 'Hereda la autorización de la colección.' : 'El header se genera automáticamente al enviar.'}</div></div>
        <div class="flds" data-t="auth-fields">${flds.map(([k, v]) => `<span>${k}</span><div>${esc(v || '')}</div>`).join('')}</div></div>`;
    } else if (r.rtab === 'headers') {
      const auto = [];
      if (r.body.mode === 'raw') auto.push(['Content-Type', 'application/json']);
      if (r.auth.type === 'Bearer Token') auto.push(['Authorization', 'Bearer ' + (r.auth.token || '')]);
      if (r.auth.type === 'Basic Auth') auto.push(['Authorization', 'Basic ' + (r.auth.user ? btoa(r.auth.user + ':' + (r.auth.pass || '')) : '')]);
      if (r.auth.type === 'API Key' && (r.auth.addTo || 'Header') === 'Header') auto.push([r.auth.key || '', r.auth.value || '']);
      ed = `<table class="pm-kv"><tr><th></th><th>Key</th><th>Value</th></tr>
        ${auto.map(([k, v]) => `<tr><td class="ck" style="color:#9a9a9a">🔒</td><td style="color:#9a9a9a">${esc(k)}</td><td style="color:#9a9a9a">${esc(v)}</td></tr>`).join('')}
        ${(r.headers || []).map(([k, v]) => `<tr><td class="ck">☑</td><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('')}
        <tr class="ph"><td></td><td>Key</td><td>Value</td></tr></table>${auto.length ? '<div style="color:var(--p-mut);font-size:11px;margin-top:4px">🔒 = headers que Postman agrega automáticamente</div>' : ''}`;
    } else if (r.rtab === 'body') {
      const modes = ['none', 'form-data', 'x-www-form-urlencoded', 'raw', 'binary'];
      ed = `<div class="pm-radio" data-t="body-mode">${modes.map(m => `<span class="${r.body.mode === m ? 'on' : ''}">${m}</span>`).join('')}${r.body.mode === 'raw' ? '<span class="fmt">JSON ▾</span>' : ''}</div>`
        + (r.body.mode === 'raw' ? `<div class="pm-code" data-t="body-raw">${hlJson(r.body.raw)}${s.typing === 'req.body.raw' ? '<span class="caret"></span>' : ''}</div>`
          : `<div style="color:var(--p-mut)">Este request no tiene body.</div>`);
    } else if (r.rtab === 'scripts') {
      const code = r.stab === 'pre' ? r.pre : r.post;
      ed = `<div class="pm-scr"><div class="sl"><div class="${r.stab === 'pre' ? 'on' : ''}" data-t="scr-pre">Pre-request</div><div class="${r.stab === 'post' ? 'on' : ''}" data-t="scr-post">Post-response</div></div>
        <div class="pm-code" data-t="scr-code" style="min-height:120px">${code ? hlJs(code) : '<span style="color:#666">// Escribe aquí tu script</span>'}${s.typing === 'req.' + r.stab ? '<span class="caret"></span>' : ''}</div></div>`;
    }
    const rtab = (k, label, extra = '') => `<span class="${r.rtab === k ? 'on' : ''}" data-t="rt-${k}">${label}${extra}</span>`;
    return `
      <div class="pm-crumb" ${H('crumb')}><span class="c">${r.col ? esc(r.col) + ' /' : 'HTTP'}</span><span class="nm">${esc(r.name)}</span><span class="save" data-t="save">💾 Save</span></div>
      <div class="pm-bar"><span class="meth ${'m' + r.method}" ${H('method')}>${r.method}<span style="color:var(--p-mut)">▾</span></span>
        <span class="url mono" ${H('url')}>${urlHtml(r.url, s)}${s.typing === 'req.url' ? '<span class="caret"></span>' : ''}</span>
        <span class="send" ${H('send')}>Send</span>${s.tip ? `<div class="pm-tip" data-t="tip">${s.tip}</div>` : ''}</div>
      <div class="pm-rtabs">${rtab('params', 'Params')}${rtab('auth', 'Authorization')}${rtab('headers', 'Headers', hdrCount ? ` <sup>(${hdrCount})</sup>` : '')}${rtab('body', 'Body', r.body.mode !== 'none' ? ' <sup>●</sup>' : '')}${rtab('scripts', 'Scripts', (r.pre || r.post) ? ' <sup>●</sup>' : '')}<span>Settings</span></div>
      <div class="pm-ed" ${H('ed')}>${ed}</div>
      <div class="pm-resp" ${H('resp')}>${renderResp(s)}</div>`;
  }

  function renderResp(s) {
    const x = s.res;
    if (!x) return `<div class="rh"><span class="t on">Response</span></div><div class="rb"><div class="hint"><div><i>🚀</i>Escribe una URL y presiona <b>Send</b><br>para ver la respuesta aquí.</div></div></div>`;
    if (x.loading) return `<div class="rh"><span class="t on">Response</span></div><div class="rb"><div class="hint"><div><i>⏳</i>Enviando request…</div></div></div>`;
    const cls = 'st' + String(x.code)[0];
    const rt = x.rtab || 'body';
    let body = '';
    if (rt === 'body') body = `<pre data-t="rbody">${x.raw ? esc(x.body) : hlJson(x.body)}</pre>`;
    else if (rt === 'headers') body = `<table class="pm-kv">${(x.headers || []).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('')}</table>`;
    else if (rt === 'tests') body = `<div class="pm-tests" data-t="rtests">${(x.tests || []).map(([n, ok, msg]) => `<div><span class="${ok ? 'pass' : 'fail'}">${ok ? 'PASS' : 'FAIL'}</span><span>${esc(n)}${msg ? `<br><span style="color:#f7b1a8;font-family:Consolas,monospace;font-size:11px">${esc(msg)}</span>` : ''}</span></div>`).join('') || '<div style="color:var(--p-mut)">Este request no tiene tests.</div>'}</div>`;
    const tcount = (x.tests || []).length ? ` (${x.tests.filter(t => t[1]).length}/${x.tests.length})` : '';
    return `<div class="rh"><span class="t ${rt === 'body' ? 'on' : ''}">Body</span><span class="t">Cookies</span><span class="t ${rt === 'headers' ? 'on' : ''}">Headers</span><span class="t ${rt === 'tests' ? 'on' : ''}" data-t="rt-tests">Test Results${tcount}</span>
      <span class="meta"><span data-t="status">Status: <b class="${cls}">${esc(x.status)}</b></span><span data-t="time">Time: <b class="${cls}">${esc(x.time)}</b></span><span data-t="size">Size: <b class="${cls}">${esc(x.size)}</b></span></span></div>
      <div class="rb">${body}</div>`;
  }

  function renderEnv(s) {
    const e = (s.envs || []).find(x => x.name === s.envEdit) || { name: s.envEdit, vars: [] };
    return `<div class="pm-envv" data-t="view"><div class="eh"><b>${e.name === 'Globals' ? '🌐' : '▣'} ${esc(e.name)}</b><span class="save" data-t="save">💾 Save</span></div>
      <table class="pm-kv" data-t="env-table"><tr><th></th><th>Variable</th><th>Type</th><th>Initial value</th><th>Current value</th>${e.cloud ? '<th>Share</th>' : ''}</tr>
      ${(e.vars || []).map(v => `<tr data-t="var:${esc(v[0])}"><td class="ck">☑</td><td>${esc(v[0])}</td><td style="font-family:inherit;color:#9a9a9a">${v[3] ? 'secret' : 'default'}</td><td>${v[3] && v[1] ? '••••••' : esc(v[1])}</td><td>${v[3] && v[2] ? '••••••' : esc(v[2])}</td>${e.cloud ? `<td style="font-family:inherit;white-space:nowrap" data-t="share:${esc(v[0])}">${v[4] === 'shared' ? '<span style="color:#6bdd9a">☁ Shared</span>' : v[4] === 'local' ? '<span style="color:#f3a43b">☁ Share</span> <small style="color:#9a9a9a">solo local</small>' : ''}</td>` : ''}</tr>`).join('')}
      <tr class="ph"><td></td><td>Add new variable</td><td></td><td></td><td></td>${e.cloud ? '<td></td>' : ''}</tr></table>
      ${e.note ? `<div style="color:var(--p-mut);font-size:11.5px;margin-top:8px;line-height:1.5">${e.note}</div>` : ''}</div>`;
  }

  /* ---------- Collection Runner ----------
     s.runner = { col, items:[{name,m,on}], mode:'manual'|'schedule'|'cli', iter, delay, data:{file,rows},
                  adv:{stop,keep}, sched:{name,freq,env,notify}, cli:'texto', results:{…} } */
  function renderRunner(s) {
    const R = s.runner || {}, H = t => `data-t="${t}"`;
    if (R.results) return renderRunResults(s, R);
    const items = R.items || [];
    const radio = (k, label) => `<div class="pm-rr ${R.mode === k ? 'on' : ''}" data-t="run-mode:${k}">${R.mode === k ? '◉' : '○'} ${label}</div>`;
    let cfg = '';
    if ((R.mode || 'manual') === 'manual') {
      cfg = `<div class="pm-rlab">Run configuration</div>
        <div class="pm-rf"><span>Iterations</span><div ${H('run-iter')}>${esc(R.iter ?? 1)}</div></div>
        <div class="pm-rf"><span>Delay</span><div ${H('run-delay')}>${esc(R.delay ?? 0)} ms</div></div>
        <div class="pm-rf"><span>Test data file</span><div ${H('run-data')}>${R.data ? `📄 ${esc(R.data.file)} <small style="color:#74aef6">· Preview</small>` : '<span style="color:#9a9a9a">Select File</span>'}</div></div>
        <div class="pm-rlab">Advanced settings</div>
        <div class="pm-radv" ${H('run-adv')}><div>${R.adv?.stop ? '☑' : '☐'} Stop run if an error occurs</div><div>${R.adv?.keep ? '☑' : '☐'} Keep variable values</div><div>☐ Persist responses for a session</div></div>`;
    } else if (R.mode === 'schedule') {
      const sc = R.sched || {};
      cfg = `<div class="pm-rlab">Schedule configuration</div>
        <div class="pm-rf"><span>Schedule name</span><div ${H('run-sname')}>${esc(sc.name || '')}</div></div>
        <div class="pm-rf"><span>Run frequency</span><div ${H('run-freq')}>${esc(sc.freq || 'Hourly')} ▾</div></div>
        <div class="pm-rf"><span>Environment</span><div ${H('run-senv')}>${esc(sc.env || 'No environment')} ▾</div></div>
        <div class="pm-rf"><span>Email notifications</span><div ${H('run-notify')}>${esc(sc.notify || '')}</div></div>
        <div style="color:#9a9a9a;font-size:11px;margin-top:6px">☁ Las ejecuciones programadas corren en la nube de Postman.</div>`;
    } else {
      cfg = `<div class="pm-rlab">Run on your CI/CD or terminal</div><pre class="pm-cli" ${H('run-cli')}>${esc(R.cli || '')}</pre>`;
    }
    const btn = (R.mode || 'manual') === 'manual' ? `Run ${esc(R.col || '')}` : R.mode === 'schedule' ? 'Schedule Run' : 'Copy command';
    return `<div class="pm-run" ${H('view')}>
      <div class="pm-runh"><b>▶ Runner</b><span style="color:#9a9a9a">· ${esc(R.col || '')}</span></div>
      <div class="pm-rgrid">
        <div class="pm-rorder" ${H('run-order')}>
          <div class="pm-roh"><b>Run order</b><span>Deselect All · Select All · Reset</span></div>
          ${items.map((it, i) => `<div class="pm-ri ${it.on === false ? 'off' : ''}" ${H('run-item:' + it.name)}><span>${it.on === false ? '☐' : '☑'}</span><span class="g">⋮⋮</span><span class="m m${it.m}">${it.m}</span>${esc(it.name)}</div>`).join('')}
        </div>
        <div class="pm-rcfg">
          <div class="pm-rlab" style="margin-top:0">Choose how to run your collection</div>
          <div class="pm-rmodes" ${H('run-modes')}>${radio('manual', 'Run manually')}${radio('schedule', 'Schedule runs')}${radio('cli', 'Automate runs via CLI')}</div>
          ${cfg}
          <div class="pm-runbtn" ${H('run-btn')}>${btn}</div>
        </div>
      </div></div>`;
  }
  function renderRunResults(s, R) {
    const res = R.results, H = t => `data-t="${t}"`;
    const all = res.iterations.flatMap(it => it.reqs.flatMap(r => r.tests || []));
    const pass = all.filter(t => t[1]).length, fail = all.length - pass;
    return `<div class="pm-run" ${H('view')}>
      <div class="pm-runh"><b>${esc(R.col || '')} - Run results</b><span style="color:#9a9a9a">· ${esc(res.how || 'Ran manually')}</span></div>
      <div class="pm-rsum" ${H('run-sum')}>
        <div><small>Source</small>${esc(res.source || 'Runner')}</div><div><small>Environment</small>${esc(res.env || s.env)}</div>
        <div><small>Iterations</small>${res.iterations.length}</div><div><small>Duration</small>${esc(res.duration || '')}</div>
        <div><small>All tests</small>${all.length}</div><div><small>Avg. Resp. Time</small>${esc(res.avg || '')}</div></div>
      <div class="pm-rtabs2"><span class="on">All Tests</span><span>Passed (${pass})</span><span style="${fail ? 'color:#f79a8e' : ''}">Failed (${fail})</span><span>Skipped (${res.skipped || 0})</span></div>
      <div class="pm-rlist">
        ${res.iterations.map((it, k) => `<div class="pm-rit" ${H('run-it:' + (k + 1))}>Iteration ${k + 1}${it.data ? ` <small style="color:#9a9a9a">· ${esc(it.data)}</small>` : ''}</div>
          ${it.reqs.map((r, j) => `<div class="pm-rq" ${H(`run-req:${k + 1}:${j + 1}`)}><div class="pm-rqh"><span class="m m${r.m}">${r.m}</span><b>${esc(r.name)}</b>
            <span class="pm-rcode ${r.code >= 400 ? 'bad' : ''}">${r.code ? r.code + ' ' + (r.code < 300 ? 'OK' : r.code === 404 ? 'Not Found' : '') : 'skipped'}</span><span style="color:#9a9a9a">${esc(r.ms || '')}</span></div>
            ${(r.tests || []).map(([n, ok, msg]) => `<div class="pm-rt"><span class="${ok ? 'pass' : 'fail'}">${ok ? 'PASS' : 'FAIL'}</span>${esc(n)}${msg ? ` <span style="color:#f7b1a8;font-family:Consolas,monospace;font-size:10.5px">| ${esc(msg)}</span>` : ''}</div>`).join('')}
            ${r.note ? `<div class="pm-rt" style="color:#9a9a9a">${r.note}</div>` : ''}</div>`).join('')}`).join('')}
      </div></div>`;
  }

  function renderMenu(s) {
    const m = s.menu;
    return `<div class="pm-menu" data-t="menu" style="left:${m.x || 240}px;top:${m.y || 120}px">${m.items.map(i => i === '-' ? '<div class="sep"></div>' : `<div data-t="mi:${esc(i[0])}">${esc(i[0])}<small>${esc(i[1] || '')}</small></div>`).join('')}</div>`;
  }

  function renderModal(s) {
    const m = s.modal;
    return `<div class="pm-ov"><div class="pm-modal" data-t="modal"><h4>${m.title}</h4>${m.sub ? `<div class="ms">${m.sub}</div>` : ''}
      ${(m.fields || []).map((f, i) => `<label>${f.label}</label><div class="in" data-t="mf:${i}">${esc(f.value || '')}${s.typing === `modal.fields.${i}.value` ? '<span class="caret"></span>' : ''}</div>`).join('')}
      ${m.opts ? `<div class="opts" style="margin-top:8px">${m.opts.map(o => `<div class="opt ${o.on ? 'on' : ''}" data-t="mo:${esc(o.name)}"><span>${o.on ? '◉' : '○'}</span><div>${esc(o.name)}<small>${esc(o.d || '')}</small></div></div>`).join('')}</div>` : ''}
      ${m.html || ''}
      <div class="mb">${(m.btns || ['Cancel', 'Save']).map((b, i, a) => `<span class="${i === a.length - 1 ? 'p' : ''}" data-t="mb:${esc(b)}">${esc(b)}</span>`).join('')}</div></div></div>`;
  }

  /* ---------- laboratorio paso a paso ---------- */
  function mount(root, cfg) {
    const steps = cfg.steps;
    const states = [];   // estado acumulado después de cada paso
    let acc = merge(clone(BASE), cfg.state || {});
    states.push(clone(acc));
    steps.forEach(st => {
      acc = clone(acc); acc.hl = st.hl || null; acc.typing = null;
      if (st.set) merge(acc, st.set);
      if (st.fn) st.fn(acc);
      states.push(acc);
    });

    root.innerHTML = `<div class="lab">
      <div class="steps"><div class="sh"><b>${cfg.title || 'Paso a paso'}</b><span class="cnt"></span></div>
        <ol>${steps.map((st, i) => `<li data-i="${i + 1}"><span class="n">${i + 1}</span><span>${st.t}</span></li>`).join('')}</ol>
        <div class="ctl"><button class="btn prev">◀</button><button class="btn pri next">Siguiente ▶</button><button class="btn auto" title="Reproducir">▶▶</button><button class="btn fin" title="Ver cómo debe quedar">✓</button></div>
      </div>
      <div><div class="pm"></div><div class="explain"></div></div></div>`;
    const win = root.querySelector('.pm'), exp = root.querySelector('.explain');
    let cur = 0, anim = null, auto = null;

    function paint(s) {
      win.innerHTML = render(s);
      if (s.hl) win.querySelectorAll(`[data-t="${s.hl.replace(/"/g, '\\"')}"]`).forEach(e => { e.classList.add('hl'); e.scrollIntoView?.({ block: 'nearest', inline: 'nearest' }); });
      // scrollIntoView también puede mover la página hacia los lados: la página nunca debe quedar corrida
      if (window.scrollX) window.scrollTo(0, window.scrollY);
      if (win.scrollLeft) win.scrollLeft = 0;
    }
    function ui() {
      root.querySelector('.cnt').textContent = cur ? `${cur} / ${steps.length}` : `0 / ${steps.length}`;
      root.querySelectorAll('.steps li').forEach(li => { const i = +li.dataset.i; li.classList.toggle('done', i < cur); li.classList.toggle('cur', i === cur); });
      root.querySelector('.prev').disabled = cur === 0;
      root.querySelector('.next').disabled = cur === steps.length;
      root.querySelector('.next').textContent = cur === 0 ? 'Empezar ▶' : 'Siguiente ▶';
      const st = steps[cur - 1];
      exp.innerHTML = st ? `<b>Paso ${cur}.</b> ${st.d || ''}` : (cfg.intro || 'Presiona <b>Empezar</b> para recorrer el laboratorio paso a paso.');
      root.querySelector('.cur')?.scrollIntoView({ block: 'nearest' });
    }
    function go(i, animate) {
      clearInterval(anim); anim = null;
      cur = Math.max(0, Math.min(steps.length, i));
      const target = states[cur], st = steps[cur - 1];
      ui();
      if (animate && st && st.type) {
        const full = String(getPath(target, st.type) || ''), prev = String(getPath(states[cur - 1], st.type) || '');
        let startAt = 0;                       // escribir solo desde donde cambia el texto
        while (startAt < prev.length && prev[startAt] === full[startAt]) startAt++;
        let n = startAt; const tmp = clone(target); tmp.typing = st.type;
        const speed = Math.max(1, Math.ceil((full.length - startAt) / 60));
        anim = setInterval(() => {
          n = Math.min(full.length, n + speed); setPath(tmp, st.type, full.slice(0, n));
          paint(tmp);
          if (n >= full.length) { clearInterval(anim); anim = null; tmp.typing = null; paint(target); }
        }, 22);
      } else paint(target);
    }
    function stopAuto() { clearInterval(auto); auto = null; root.querySelector('.auto').textContent = '▶▶'; }
    root.querySelector('.next').onclick = () => { stopAuto(); go(cur + 1, true); };
    root.querySelector('.prev').onclick = () => { stopAuto(); go(cur - 1, false); };
    root.querySelector('.fin').onclick = () => { stopAuto(); go(steps.length, false); };
    root.querySelector('.auto').onclick = () => {
      if (auto) return stopAuto();
      if (cur === steps.length) go(0, false);
      root.querySelector('.auto').textContent = 'Ⅱ';
      go(cur + 1, true);
      auto = setInterval(() => { if (anim) return; if (cur >= steps.length) return stopAuto(); go(cur + 1, true); }, 2600);
    };
    root.querySelectorAll('.steps li').forEach(li => li.onclick = () => { stopAuto(); go(+li.dataset.i, true); });
    go(0, false);
    return { go };
  }

  /* Solo dibujar una ventana fija (sin pasos), útil para tours o ilustraciones */
  function show(el, state) { el.classList.add('pm'); el.innerHTML = render(merge(clone(BASE), state || {})); }

  window.PMLab = { mount, show, render, hlJson };
})();

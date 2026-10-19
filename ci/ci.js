/* =====================================================================
   Parte 4 · utilidades compartidas
   CI.tabs()                       pestañas: <div class="tabs" id="tabs"> + <section class="pane" id="p-xxx">
   CI.terms(SEQ)                   terminales: <div class="steps2" data-term="tId"> con .st[data-s]
                                   y <div class="term" id="tId"><pre></pre></div>
     SEQ = { tId: [ [ [clase, texto], ... ], ... ] }   un arreglo de líneas por paso
     clase 'p' = prompt; la línea 'w' que le sigue se escribe letra por letra
   ===================================================================== */
window.CI = (() => {
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  function tabs(id = 'tabs') {
    const box = $(id); if (!box) return;
    box.onclick = e => {
      const b = e.target.closest('button'); if (!b) return;
      box.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
      document.querySelectorAll('.pane').forEach(p => p.classList.toggle('on', p.id === 'p-' + b.dataset.t));
    };
  }
  const timers = {};
  function play(SEQ, termId, k) {
    const out = $(termId).querySelector('pre'); clearTimeout(timers[termId]);
    document.querySelectorAll(`[data-term="${termId}"] .st`).forEach(s => s.classList.toggle('on', +s.dataset.s === k));
    const lines = SEQ[termId][k]; let i = 0, j = 0, html = '';
    const step = () => {
      if (i >= lines.length) return;
      const [cls, txt] = lines[i]; const isCmd = cls === 'w' && i > 0 && lines[i - 1][0] === 'p';
      const n = isCmd ? Math.min(txt.length, j + 3) : txt.length;
      out.innerHTML = html + `<span class="${cls}">${esc(txt.slice(0, n))}</span>${isCmd && n < txt.length ? '<span class="w">▌</span>' : ''}`;
      out.scrollTop = out.scrollHeight;
      if (n < txt.length) { j = n; timers[termId] = setTimeout(step, 14); return; }
      html += `<span class="${cls}">${esc(txt)}</span>`; i++; j = 0; timers[termId] = setTimeout(step, isCmd ? 300 : 70);
    };
    step();
  }
  function terms(SEQ) {
    document.querySelectorAll('[data-term]').forEach(box => {
      const id = box.dataset.term;
      box.addEventListener('click', e => { const s = e.target.closest('.st'); if (s) play(SEQ, id, +s.dataset.s); });
      $(id).querySelector('pre').innerHTML = '<span class="d">Haz clic en un paso de la izquierda para verlo en la terminal.</span>';
    });
  }
  return { $, esc, tabs, terms };
})();

// Add a grouped reference strip and same-case navigation to the public reader.
(() => {
  const svgNS = 'http://www.w3.org/2000/svg';
  function node(tag, attrs, label) {
    const el = document.createElementNS(svgNS, tag);
    for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, String(value));
    if (label !== undefined) el.textContent = label;
    return el;
  }
  function strip(original, card, c, key) {
    const coordinate = Number(document.getElementById('component').value);
    const groups = new Map();
    const lookup = document.getElementById('case').value;
    const values = card.reference.map((r, i) => {
      let name = String(D.reference[i].group ?? ('Class ' + D.reference[i].label));
      if (!groups.has(name)) groups.set(name, []);
      groups.get(name).push(i);
      return r[coordinate];
    });
    const states = c.components[key].map(r => r[coordinate]);
    const lo = Math.min(...values, ...states), hi = Math.max(...values, ...states);
    const x = v => lo === hi ? 285 : 95 + 380 * (v-lo)/(hi-lo);
    const height = 72 + 24*groups.size;
    const svg = node('svg',{class:'reference-strip',viewBox:'0 0 500 '+height,role:'img','aria-label':'Reference distribution by group for '+lookup+'. Original '+num(states[0])+', edited '+num(states[1])+'.'});
    let y = 41;
    for (const [name, ids] of groups) {
      svg.append(node('text',{x:0,y:y+3},name),node('line',{x1:95,x2:475,y1:y,y2:y,class:'guide-line'}));
      ids.forEach((i,j) => {
        const dot = node('circle',{cx:x(values[i]),cy:y + (j%3-1)*2,r:2.6,class:'ref-dot'});
        const ref = D.reference[i];
        dot.append(node('title',{},(ref.prompt ?? (ref.prefix+ref.suffix))+' · '+num(values[i])));
        svg.append(dot);
      });
      y+=24;
    }
    for (let i = 0; i < 2; i++) {
      const px = x(states[i]);
      svg.append(node('line',{x1:px,x2:px,y1:i===0?11:23,y2:y-15,class:i===0?'original-rule':'edited-rule'}));
      svg.append(i===0?node('circle',{cx:px,cy:10,r:4.5,class:'original-dot'}):node('path',{d:'M'+px+' 14l5 5 -5 5 -5 -5Z',class:'edited-dot'}));
    }
    svg.append(node('text',{x:95,y:height-5},num(lo)),node('text',{x:475,y:height-5,'text-anchor':'end'},num(hi)));
    original.replaceWith(svg);
  }
  let restoreCoordinateFocus = false;
  document.addEventListener('change', event => {
    restoreCoordinateFocus = event.target.id === 'component' && document.activeElement === event.target;
  }, true);
  const cases = document.getElementById('case');
  for (const option of cases.options) {
    const c = D.cases.find(row => row.id === option.value);
    if (c && /^\d+-a[n]?-/.test(c.id)) {
      const stem = c.clean.prompt.replace(/\s+$/, '');
      option.textContent = stem + '… · ' + c.id.split('-').slice(2).join(' ');
    }
  }
  function decorate() {
    const id = document.getElementById('case').value;
    const tool = document.getElementById('tool').value;
    const current = D.cases.find(c=>c.id===id);
    if (current.stimuli) {
      const prompts = document.querySelectorAll('#prompt pre');
      ['clean','donor'].forEach((field,i) => {
        if (!prompts[i]) return;
        const stimulus = current.stimuli[i];
        const im = document.createElement('img');
        im.src = '../../records/three-more/images/' + stimulus + '.png';
        im.alt = stimulus + ' disk layout';
        im.width = 144; im.height = 144;
        prompts[i].textContent = current[field].prompt.split('<|vision_end|>').at(-1).trim();
        prompts[i].before(im);
      });
    }
    for (const link of document.querySelectorAll('.bench-picks a')) {
      link.hash = encodeURIComponent(id) + '/' + encodeURIComponent(link.dataset.method);
      if (link.dataset.method === tool) link.setAttribute('aria-current','true');
      else link.removeAttribute('aria-current');
    }
    const original = document.querySelector('#result svg.points');
    const key = tool==='group' && D.components.brush_door ? 'brush_door' : tool;
    if (original && D.components[key]) strip(original, D.components[key], D.cases.find(c=>c.id===id), key);
    if (restoreCoordinateFocus) {
      document.getElementById('component')?.focus({preventScroll: true});
      restoreCoordinateFocus = false;
    }
  }
  window.addEventListener('hashchange',decorate);
  decorate();
})();

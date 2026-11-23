/* One matched case, with an independently addressable view for each instrument. */
const guide = JSON.parse(document.getElementById('guide').textContent);
const $ = id => document.getElementById(id);
const esc = v => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = n => n.toLocaleString('en-US',{maximumFractionDigits:2,minimumFractionDigits:2});
const sign = n => (n > 0 ? '+' : '') + number(n);
const labelToken = t => t.replace(/^ +/, spaces => '␠'.repeat(spaces.length)).replaceAll('\n','↵');
const href = (tool,component) => '#' + tool + (component == null ? '' : '/' + component);
function state() {
  const [name,axis] = location.hash.slice(1).split('/');
  const tool = guide.tools[name] ? name : guide.start;
  const data = guide.records[tool];
  const ids = data && data.plot && data.plot.ids;
  const selected = ids && axis != null ? ids.indexOf(Number(axis)) : -1;
  return {tool,data,j:selected < 0 ? data?.plot?.selected : selected};
}
function source(record){
  return (record.sources || []).map(([name,url]) => '<a href="'+esc(url)+'">'+esc(name)+'</a>').join(' · ');
}
function table(headers,rows) {
  return '<table class="rank-list"><thead><tr>'+headers.map(v=>'<th scope="col">'+esc(v)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
}
function strip(record,j) {
  const p=record.plot;
  const values=p.reference.map(row=>row[j]), pair=p.pair.map(row=>row[j]);
  const low=Math.min(...values,...pair), high=Math.max(...values,...pair);
  const domain=high-low||1, W=window.matchMedia('(max-width:620px)').matches ? 390 : 820;
  const start=60,end=W-19,x=v=>start+5+(end-start-10)*(v-low)/domain;
  const samples=guide.banks[p.bank], groups=[...new Set(samples.map(v=>v.group))];
  const height=56+groups.length*20;
  const circle=(xx,y)=>'<circle cx="'+xx+'" cy="'+y+'" r="4" fill="#faf8f2" stroke="#425c50" stroke-width="2"/>';
  const diamond=(xx,y)=>'<path d="M'+xx+' '+(y-5)+'l5 5 -5 5 -5 -5Z" fill="#914927"/>';
  const pins=pair.map((v,i)=>'<line x1="'+x(v)+'" x2="'+x(v)+'" y1="14" y2="'+(height-25)+'" stroke="'+(i?'#914927':'#425c50')+'" opacity=".65" stroke-dasharray="2 3"/>'+(i?diamond:circle)(x(v),10)).join('');
  const rows=groups.map((g,i)=>{
    const y=34+i*20;
    return '<text x="1" y="'+(y+4)+'">'+esc(g)+'</text><path d="M'+start+' '+y+'H'+end+'" stroke="#cdc9bc"/>'+samples.map((r,k)=>r.group===g?'<circle r="3.4" cx="'+x(values[k])+'" cy="'+y+'" fill="#514f43" opacity=".56"><title>'+esc(r.prompt)+' · '+number(values[k])+'</title></circle>':'').join('');
  }).join('');
  const rank=values.map((_,i)=>i).sort((a,b)=>values[a]-values[b]);
  const samplesHTML=[['Low end',rank[0]],['Middle',rank[Math.floor(rank.length/2)]],['High end',rank.at(-1)]].map(([tag,i])=>{
    const r=samples[i];const index=(r.end ?? r.prompt.length) - r.token.trimStart().length;
    const snippet=index<0?esc(r.prompt):esc(r.prompt.slice(0,index))+'<mark>'+esc(r.token.trim())+'</mark>'+esc(r.prompt.slice(index+r.token.trim().length));
    return '<div><small>'+tag+' · '+sign(values[i])+'</small><p>'+snippet+'</p></div>';
  }).join('');
  return '<div class="chart-wrap"><div class="twin"><span>○ '+esc(record.labels[0])+' '+sign(pair[0])+'</span><span class="patched">◆ '+esc(record.labels[1])+' '+sign(pair[1])+'</span></div><figure><svg viewBox="0 0 '+W+' '+height+'" role="img" aria-label="'+esc(guide.tools[state().tool].name)+' reference scores grouped by '+esc(p.groupName||'animal')+'">'+rows+pins+'<text class="ticks" x="'+start+'" y="'+(height-6)+'">'+number(low)+'</text><text class="ticks" text-anchor="end" x="'+end+'" y="'+(height-6)+'">'+number(high)+'</text></svg><figcaption>'+values.length+' reference positions · '+esc(p.unit)+' · common scale across rows</figcaption></figure></div><div class="samples">'+samplesHTML+'</div><details><summary>Inspect a reference example</summary><label>Reference <select id="ref-choice">'+samples.map((r,i)=>'<option value="'+i+'">'+esc(r.group)+' · '+(i+1)+'</option>').join('')+'</select></label><p id="ref-detail" aria-live="polite"></p></details>';
}
function render() {
  const restoreAxisFocus=document.activeElement?.id==='axis';
  const {tool,data,j}=state();
  const entry=guide.tools[tool];
  $('tool').value=tool;
  $('title').textContent=entry.name;
  $('kind').textContent=data?.status || 'Awaiting a matched run';
  let body='';
  if(data){
    body='<p class="prose">'+esc(data.caption)+'</p>';
    if(data.plot){
      const p=data.plot;
      if(p.ids.length>1)body+='<label>'+esc(p.control||'Component')+' <select id="axis">'+p.ids.map((n,i)=>'<option value="'+n+'"'+(i===j?' selected':'')+'>'+n+'</option>').join('')+'</select></label>';
      body+=strip(data,j);
    }
    if(data.rows)body+=table(data.headers,data.rows);
    if(data.raw)body+=table(['Rank',...data.labels],data.raw[0].map((t,i)=>[i+1,labelToken(t.token),labelToken(data.raw[1][i].token)]));
    if(data.note)body+='<details><summary>How this was measured</summary><p class="prose">'+esc(data.note)+'</p></details>';
    body+='<p class="credits">'+source(data)+'</p>';
  }else{
    body='<div class="pending"><p>'+esc(entry.question)+'</p><p class="credits">'+esc(guide.waiting)+' '+esc(entry.need)+'</p></div>';
  }
  $('view').innerHTML=body;
  if($('axis')) {
    $('axis').onchange=e=>location.hash=href(tool,e.target.value);
    if(restoreAxisFocus)$('axis').focus({preventScroll:true});
  }
  if($('ref-choice')){
    const describe=()=>{const i=Number($('ref-choice').value),r=guide.banks[data.plot.bank][i]; $('ref-detail').textContent=r.prompt+' · measured token '+labelToken(r.token)+' · '+sign(data.plot.reference[i][j])+' '+data.plot.unit;};
    $('ref-choice').onchange=describe;describe();
  }
  for(const a of document.querySelectorAll('.catalogue a')) if(a.hash===href(tool))a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');
}
$('tool').onchange=e=>{location.hash=href(e.target.value);};
window.addEventListener('hashchange',render);
window.matchMedia('(max-width:620px)').addEventListener('change',render);
render();

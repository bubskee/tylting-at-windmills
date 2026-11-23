'use strict';
const D=JSON.parse(document.getElementById('record').textContent);
const $=id=>document.getElementById(id);
const enc=x=>String(x??'').replace(/[&<>"']/g,v=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[v]));
const num=x=>Number(x).toLocaleString('en-US',{maximumFractionDigits:5});
const pretty=s=>String(s).replace(/^ +/,z=>'␠'.repeat(z.length)).replaceAll('\n','↵');
const word=v=>v?pretty(v.token)+' ['+v.id+']':'';
const table=(head,rows)=>'<table><thead><tr>'+head.map(h=>'<th>'+enc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td>'+enc(x)+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
const pair=(a,b)=>'<div class="pair"><div><small>○ Original</small>'+a+'</div><div><small class="rust">◆ After the edit</small>'+b+'</div></div>';
const pick=(name,values,i,labels)=>'<label>'+enc(name)+'<select id="component">'+values.map((x,n)=>'<option value="'+n+'"'+(n===i?' selected':'')+'>'+enc(labels?labels[n]:x)+'</option>').join('')+'</select></label>';
const det=(title,inside)=>'<details><summary>'+enc(title)+'</summary>'+inside+'</details>';
const tokTable=rr=>table(['Rank','Original','After edit'],rr[0].top.map((v,i)=>[i+1,word(v),word(rr[1].top[i])]));
const caseSel=$('case'),toolSel=$('tool');
for(const c of D.cases)caseSel.add(new Option(c.id,c.id));
for(const [id,label] of Object.entries(D.tool_labels))toolSel.add(new Option(label,id));
const slug=location.pathname.split('/').pop().replace(/\.html$/,'');
$('task').value=slug;$('task').onchange=()=>location.href=$('task').value+'.html';
function go(axis){location.hash=[caseSel.value,toolSel.value,...(axis!=null?[axis]:[])].map(encodeURIComponent).join('/')}
caseSel.onchange=()=>go();toolSel.onchange=()=>go();
$('model').textContent=D.kind+' · '+D.model+' · '+(typeof D.layer==='number'?'block ':'')+D.layer;
function inputs(c){
 const row=(title,s)=>s?'<p><strong>'+enc(title)+'</strong></p><pre>'+enc(s.prompt??('cell '+c.position))+'</pre>'+(s.token!==undefined?'<small>Token '+enc(pretty(s.token))+' · ID '+s.id+' · position '+s.position+'</small>':''):'';
 return row('Receiver',c.clean)+row('Donor',c.donor)+'<p>'+enc(c.intervention??'Insert the released door brush at the selected spatial cell.')+'</p><p><small>Checkpoint revision '+enc(D.revision)+'</small></p>'
}
function graph(card,c,k,idx){
 const max=card.ids.length;const j=Math.max(0,Math.min(max-1,idx??card.selected));
 const vs=card.reference.map(r=>r[j]),p=c.components[k].map(r=>r[j]);
 const lo=Math.min(...vs,...p),hi=Math.max(...vs,...p);const x=v=>18+564*(v-lo)/(hi-lo||1);
 const ref=i=>{const r=D.reference[i];return (r.prompt??(r.prefix+r.suffix))+' · '+pretty(r.token)+' · '+num(vs[i]);};
 const rank=vs.map((v,i)=>i).sort((a,b)=>vs[a]-vs[b]);
 let o=pick('Coordinate',card.ids,j)+pair('<b>'+num(p[0])+'</b>','<b>'+num(p[1])+'</b>')+'<svg class="points" role="img" aria-label="Reference scores with clean and edited markers" viewBox="0 0 600 80"><path d="M18 44 H582" stroke="#b6b0a0"/>';
 o+=vs.map((v,i)=>'<circle cx="'+x(v)+'" cy="'+(34+i%4*5)+'" r="3" fill="#586658" opacity=".55"><title>'+enc(ref(i))+'</title></circle>').join('');
 o+='<circle cx="'+x(p[0])+'" cy="19" r="5" fill="none" stroke="#385847" stroke-width="2"/><path d="M'+x(p[1])+' 5l5 5 -5 5 -5 -5Z" fill="#914927"/><text class="axis" x="16" y="72">'+num(lo)+'</text><text class="axis" x="584" y="72" text-anchor="end">'+num(hi)+'</text></svg><small>'+vs.length+' reference positions · '+enc(card.unit)+(p[0]===p[1]?' · unchanged at stored precision':'')+'</small>';
 o+=table(['Reference','Prompt, marked token and score'],[['Low',ref(rank[0])],['Middle',ref(rank[Math.floor(rank.length/2)])],['High',ref(rank.at(-1))]]);
 return o+det('Every reference position',table(['Example','Class','Prompt · token · score'],vs.map((_,i)=>[i+1,D.reference[i].group??D.reference[i].label,ref(i)])));
}
function outcome(c){
 if(c.clean.image)return pair(...[c.clean,c.edited].map(s=>'<p><img src="images/'+enc(s.image)+'" alt="Church generator output for this condition"></p><small>Mean tile RGB in [−1, 1] '+s.rgb_mean.map(num).join(', ')+'</small>'))+'<p>8 × 8 cell (row, column) '+c.position.join(', ')+'. Whole-image mean absolute channel change '+num(c.mean_absolute_rgb_change)+'.</p>';
 const nativeBoard=s=>'<pre>'+Array.from({length:8},(_,r)=>String.fromCharCode(65+r)+'   '+s.board.slice(8*r,8*r+8).map(x=>({'-1':'○','0':'·','1':'●'}[x])).join(' ')).join('\n')+'\n    1 2 3 4 5 6 7 8</pre>';
 let out=pair(...[c.clean,c.edited].map(s=>'<p><strong>'+enc(s.greedy_line||word(s.top?.[0]))+'</strong></p>'+(s.board?nativeBoard(s):'')));
 if(c.gained)out+='<p>Newly legal '+c.gained.join(', ')+'. Newly illegal '+c.lost.join(', ')+'.</p>'+table(['Probability mass','Original','After edit'],[['Newly legal',num(100*c.clean.gained_mass)+'%',num(100*c.edited.gained_mass)+'%'],['Newly illegal',num(100*c.clean.lost_mass)+'%',num(100*c.edited.lost_mass)+'%']]);
 if(c.routes?.[0].options){const rr=c.routes;out+=table(['Answer option','Original logit','Edited logit'],rr[0].options.map((z,i)=>[z,num(rr[0].option_logits[i]),num(rr[1].option_logits[i])]))}
 if(c.clean.top)out+=det('Unrestricted next-token rankings',tokTable([c.clean,c.edited]));
 return out;
}
function render(){
 const [caseId,key,coord]=location.hash.slice(1).split('/').map(decodeURIComponent);
 const c=D.cases.find(x=>x.id===caseId)||(slug.startsWith('awkward-pause')?D.cases.find(x=>x.id==='05-an-remove'):null)||D.cases[0];
 const k=Object.hasOwn(D.tool_labels,key)?key:slug==='leg-day'?'patchscope':slug==='the-e6-incident'?'probe':slug==='knock-on-sky'?'patch':'ica';
 const ix=coord!==undefined&&/^\d+$/.test(coord)?Number(coord):undefined;
 caseSel.value=c.id;toolSel.value=k;
 $('prompt').innerHTML=inputs(c);$('title').textContent=D.tool_labels[k];$('status').textContent=D.status[k][0]+' · '+c.id;$('desc').textContent=D.status[k][1];
 let body='';let plot=k;
 if(k==='group'&&D.components.brush_door)plot='brush_door';
 if(D.components[plot])body=graph(D.components[plot],c,plot,ix);
 else if(c.lenses?.[k]){
  body=tokTable(c.lenses[k]);
  if(c.lenses[k][0].ranks){const r=c.lenses[k];body+=det('Ranks of named candidates',table(['Word','Original','After edit'],Object.keys(r[0].ranks).map(w=>[w,r[0].ranks[w],r[1].ranks[w]])))}
  if(D.templates?.[k])body+='<p>Unpatched receiver</p><pre>'+enc(D.templates[k].join(''))+'</pre>'+table(['Unpatched rank','Token'],D.receiver_controls[k].map((r,i)=>[i+1,word(r)]));
  if(c.following_token?.lenses[k]){let r=c.following_token;body+=det('Read one token later', '<p>The clean first token '+enc(pretty(r.clean.token))+' is held fixed for both runs. The patch stays on the previous newline. At block '+D.layer+' the two states are identical. Four blocks later the edit can have reached this position.</p>'+tokTable(r.downstream[k]));}
 }else if(k==='attention'&&c.attention){const hw=c.attention;const j=Math.min(ix??0,hw[0].weights.length-1);body=pick('Head',hw[0].weights.map((_,i)=>i),j)+table(['Key position','Key token','Original weight','Edited weight'],hw[0].key_tokens.map((w,i)=>[i,pretty(w),num(hw[0].weights[j][i]),num(hw[1].weights[j][i])]));}
 else if(k==='patch')body=outcome(c);
 else if(k==='oracle'&&c.oracle){const j=Math.min(ix??0,1);body=pick('Question',[0,1],j,D.oracle_questions)+tokTable(c.oracle[j])+table(['Held-out control','Top one','Top ten','Mean token NLL'],Object.entries(D.oracle_checks[j]).map(([k,v])=>[k,v.top1+'/'+v.n,v.top10+'/'+v.n,num(v.nll)]));}
 else if(k==='functions'&&c.routes){const v=D.discovery;body=pair(...c.routes.map(r=>'<p>'+num(r.function_cosine)+'</p>'))+'<p>Block '+v.layer+', head '+v.head+'. The clean demonstrations gave the correct two-choice answer '+v.clean_correct+' of '+v.clean_total+' times. Restoring this head changed the correct-label margin by '+num(v.head_effects[v.head])+' logits on average.</p>'+det('Discovery prompts and corrupted controls',v.examples.map(r=>'<pre>'+enc(r.clean)+'</pre><pre>'+enc(r.corrupt)+'</pre>').join(''));}
 else if(k==='graph'&&(c.routes||c.pixel_paths)){const ids=c.pixel_paths?.ids||c.routes[0].effects.map((_,i)=>i);const p=c.pixel_paths?.pair||c.routes.map(v=>v.effects);const order=ids.map((_,i)=>i).sort((a,b)=>Math.max(Math.abs(p[0][b]),Math.abs(p[1][b]))-Math.max(Math.abs(p[0][a]),Math.abs(p[1][a])));body=table(['Coordinate','Original','Edited'],order.map(i=>[ids[i],num(p[0][i]),num(p[1][i])]));}
 if(k==='rome'&&D.writer_fit?.weight_trial){const t=D.writer_fit.weight_trial;body+=det('Separate weight-edit trial and retention checks','<p>'+enc(t.description)+'</p><p>Effective update Frobenius norm '+num(t.weight_delta_frobenius)+'. Each row gives the top token and the Rome-minus-Paris logit margin.</p>'+table(['Prompt','Original','After weight edit'],t.rows.map(r=>[r.prompt,word(r.original.top[0])+' · '+num(r.original.margin),word(r.edited.top[0])+' · '+num(r.edited.margin)])));}
 $('result').innerHTML=body+(c.archive_note?'<p><strong>Replay discrepancy.</strong> '+enc(c.archive_note)+'</p>':'');
 if($('component'))$('component').onchange=e=>go(e.target.value);
 $('methods').innerHTML='<p>'+enc(D.contrast)+'</p><p>'+D.reference.length+' reference positions. Statistical axes are oriented toward class 1 and scaled in reference standard deviations. Native unit and cosine scores retain their own scales. The initial coordinate has the largest standardized gap on the labelled reference examples.</p><p>ICA '+enc(D.fit.ica_algorithm)+' · '+D.fit.ica_iterations+' iterations · '+(D.fit.ica_converged?'converged.':'iteration limit reached.')+'</p>'+det('Class definitions and gradient target', '<pre>'+enc(JSON.stringify({target_tokens:D.target_tokens,contrast:D.contrast,feature_fve:D.feature_fve},null,2))+'</pre>');
}
window.addEventListener('hashchange',render);render();

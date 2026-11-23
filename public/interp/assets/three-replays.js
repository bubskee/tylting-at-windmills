(() => {
  const byId = id => document.getElementById(id);
  const data = JSON.parse(byId('replays').textContent);
  const sections = new Map();
  for (const row of data.cases) {
    const key = (row.site?row.site+' / ':'') +row.id.slice(0,row.id.lastIndexOf('-'));
    if (!sections.has(key)) sections.set(key,[]);
    sections.get(key).push(row);
  }
  const label = {quality:'Chord quality',root:'Root note',belief:'Mouse’s first search',world:'Biscuit location',shape:'Triangle visible?',count:'Disk count'};
  const modeNames = {full:'Whole state',ica:'ICA',ace:'ACE',means:'Difference of means',pca:'PCA',gradient:'Gradient',gradient_ranked_ica:'Gradient-ranked ICA',random_ica_norm:'Random direction · ICA length',self:'Self-copy control'};
  const isChord = data.slug==='a-minor-adjustment';
  const isMouse = data.slug==='who-let-the-mouse-peek';
  let condition='original',audio;
  const element=(tag,text,cls) => {
    const el=document.createElement(tag);el.textContent=text;
    if(cls)el.className=cls;
    return el;
  };
  const rows=()=>sections.get(byId('eg').value);
  const getLabel=row=>label[row.id.split('-').at(-1)];
  for (const key of sections.keys()) byId('eg').add(new Option(key.replaceAll('-',' · '),key));
  for (const [key,value] of Object.entries(modeNames)) byId('edit-mode').add(new Option(value,key));
  const num=n=>(n>0?'+':'')+Number(n).toLocaleString('en-US',{maximumFractionDigits:5});
  const literal=v=>JSON.stringify(v);
  function play(notes) {
    audio ||= new AudioContext();
    audio.resume();
    const semitones={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
    let prev=-1;
    for(const n of notes){
      let midi=60+semitones[n[0]]+(n[1]==='b'?-1:n[1]==='#'?1:0);
      if(midi<=prev)midi+=12;
      prev=midi;
      const osc=audio.createOscillator(),gain=audio.createGain(),t=audio.currentTime;
      osc.frequency.value=440*Math.pow(2,(midi-69)/12);
      gain.gain.setValueAtTime(0,t);gain.gain.linearRampToValueAtTime(.12,t+.02);gain.gain.exponentialRampToValueAtTime(.001,t+1.25);
      osc.connect(gain);gain.connect(audio.destination);osc.start(t);osc.stop(t+1.3);
    }
  }
  function showStimulus(row) {
    const s=byId('stimulus'),native=condition==='natural'?1:0;s.replaceChildren();
    if(row.pictures){
      const frame=element('div','','church-print'),im=element('img','');
      im.src='records/three-more/images/'+row.pictures[native]+'.png';im.alt=row.pictures[native]+' disk arrangement';
      frame.append(im);
      const box=element('i','','center-cell');box.title='Identical white center cell';frame.append(box);s.append(frame);
    }else if(isChord){
      const notes=row.prompts[native].match(/plays the notes (.+?)\./)[1].split(', ');
      s.append(element('div',notes.join(' · '),'chord-notes'));
      const listen=element('button','Hear this chord');listen.onclick=()=>play(notes);s.append(listen);
    }else{
      s.append(element('p',row.prompts[native].split(/ Where (?:will|is) /)[0],'mouse-story'));
    }
  }
  function links() {
    const row=rows()[Number(byId('inspect').value)||0],container=byId('links');container.replaceChildren();
    for (const key of [...data.tools,'patch']){
      const a=element('a',key==='patch'?'All instruments ↗':data.labels[key]+' ↗');
      a.href='instruments/matched/'+row.reader+'.html#'+encodeURIComponent(row.id)+'/'+key;container.append(a);
    }
  }
  function render(reset=false){
    const selected=rows(),method=byId('edit-mode').value,area=byId('answers');area.replaceChildren();
    showStimulus(selected[0]);
    const site=isChord?(selected[0].site==='middle note'?'middle note of the written chord':'period after the last note'):isMouse?'final story period':'center image token · grid row 4, column 4 (zero-based)';
    byId('edit-site').textContent='Block 15 · '+site;
    byId('condition').textContent=condition==='original'?'Original input and original state.':condition==='natural'?'Donor input, run normally.':'Original input, with the '+modeNames[method].toLowerCase()+' edit.';
    for (const id of ['original','natural','patch']) byId(id).setAttribute('aria-pressed',String(condition===id));
    for (const row of selected) {
      const record=condition==='natural'?row.natural_donor:condition==='patch'?row.edits[method]:row.original;
      const card=element('div','','trial-card');card.append(element('small',getLabel(row)));
      const ans=element('b',record.preferred??'Tie');
      if(condition!=='original' && record.preferred!==row.original.preferred)ans.className='edited';
      card.append(ans,element('span',row.query.answers[1].trim()+' minus '+row.query.answers[0].trim()+' · '+num(record.margin)+' logits'),element('small','Top token '+literal(record.top.token)));
      area.append(card);
    }
    if(reset){byId('inspect').replaceChildren();selected.forEach((r,i)=>byId('inspect').add(new Option(getLabel(r),''+i)));}
    links();
    const sources=document.querySelectorAll('p.credits a');
    if(sources.length===2){
      sources[0].href='records/three-more/'+selected[0].reader+'.json';
      sources[1].href='instruments/matched/data/'+selected[0].reader+'.json';
    }
    const dest=byId('followup');dest.replaceChildren();
    for(const row of selected){
      const t=element('table','');const cap=element('caption',getLabel(row));t.append(cap);
      const h=t.createTHead().insertRow();for(const v of ['Control','Original','Donor input','Whole-state edit'])h.append(element('th',v));
      const body=t.createTBody();
      for(const c of row.controls){
        const tr=body.insertRow();
        for(const v of [c.variant==='wording'?'Second wording':'Second wording + alternate site',num(c.original.margin),num(c.natural_donor.margin),num(c.full.margin)])tr.insertCell().textContent=v;
      }
      dest.append(t);
    }
  }
  byId('eg').onchange=()=>{condition='original';render(true)};
  byId('edit-mode').onchange=()=>{condition='patch';render()};
  for(const id of ['original','natural','patch'])byId(id).onclick=()=>{condition=id;render()};
  byId('inspect').onchange=links;
  render(true);
})();

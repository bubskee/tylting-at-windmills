const byId = id => document.getElementById(id);
const pilot = JSON.parse(byId('pilot').textContent);
let patched = false;
for (const x of pilot.rows[0].patched) byId('layer').add(new Option(x.layer, x.layer));
byId('layer').value = '18';
function render() {
  const row = pilot.rows[Number(byId('couplet').value)];
  const layer = Number(byId('layer').value);
  const edit = row.patched.find(p => p.layer === layer);
  byId('poem').textContent = row.free_prompt.split('\n')[1];
  byId('donor-line').textContent = 'Donor first line · ' + row.donor_prompt.split('\n')[1] + ' Its clean ending was “' + row.donor_last + '”.';
  byId('completion').textContent = patched ? edit.line : row.free_line;
  byId('completion').classList.toggle('edited', patched && edit.line !== row.free_line);
  byId('rstatus').textContent = patched ? ({own:'Patched · a source-listed rhyme', donor:'Patched · a donor-listed rhyme', other:'Patched · outside both rhyme lists'})[edit.label] : 'Clean continuation';
  byId('rsite').textContent = 'Qwen3.5-4B · revision 851bf6e · decoder block ' + layer + ' output at newline token ' + row.site + ' · ' + row.id;
  byId('rpatch').textContent = patched ? 'Undo newline patch' : 'Copy the donor newline';
}
byId('couplet').onchange = () => { patched = false; render(); };
byId('layer').onchange = render;
byId('rpatch').onclick = () => { patched = !patched; render(); };
render();

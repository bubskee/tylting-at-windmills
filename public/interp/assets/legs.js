const byId = id => document.getElementById(id);
const pilot = JSON.parse(byId('pilot').textContent);
const spiderTrials = pilot.trials.filter(t => t.source === 'spider' && t.donor === 'bee');
const promptFor = (animal, question) => pilot.behaviour.find(r => r.animal === animal && r.question === question).prompt;
let ant = false;
let patched = false;
byId('swap').onclick = () => {
  ant = !ant;
  byId('leg-answer').textContent = ant ? '6' : '8';
  byId('leg-answer').classList.toggle('edited', ant);
  byId('animal-state').textContent = ant ? 'Coordinates swapped · ant' : 'Original state · spider';
  byId('swap').textContent = ant ? 'Undo swap' : 'Swap spider for ant';
};
function showLocal() {
  const trial = spiderTrials.find(t => t.patch === byId('leg-site').value);
  byId('local-prompt').textContent = promptFor('spider', 'legs');
  byId('donor-prompt').textContent = 'Donor · ' + promptFor('bee', trial.patch.includes('name') ? 'name' : 'legs');
  byId('local-answer').textContent = patched ? trial.top_by_layer[12] : trial.source_answer;
  byId('local-answer').classList.toggle('edited', patched && trial.top_by_layer[12] !== trial.source_answer);
  byId('bee').textContent = patched ? 'Undo bee patch' : 'Copy the bee state';
}
byId('bee').onclick = () => { patched = !patched; showLocal(); };
byId('leg-site').onchange = showLocal;
showLocal();

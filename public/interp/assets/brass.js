const outcomes = [
  ['relay', 'Jane’s door'],
  ['direct', 'Brass-key owner before handoffs'],
  ['map', 'Map owner']
];
const explanations = {
  base: 'Original text and original state. The next two answers come from separate questions about the setup.',
  patch: 'The text still says brass. Copying the silver state flips the door. The answers about the starting owner and the map stay put.',
  donor: 'Changing the word in the prompt moves both the door and the starting owner. Ella still has the map.'
};
function showStory(state) {
  by('metal').textContent = state === 'donor' ? 'silver' : 'brass';
  by('metal').classList.toggle('new', state === 'donor');
  by('results').replaceChildren();
  for (const [kind, label] of outcomes) {
    const i = data.story.case.qs.findIndex(q => q.k === kind);
    const answers = data.story.answers[i];
    const margin = answers[state];
    const changed = (margin > 0) !== (answers.base > 0);
    const box = document.createElement('div');
    const heading = document.createElement('span');
    heading.className = 'caption';
    heading.textContent = label;
    const answer = document.createElement('strong');
    answer.textContent = data.story.case.qs[i].opts[Number(margin > 0)];
    if (state !== 'base') answer.className = changed ? 'edited' : 'fixed';
    const detail = document.createElement('span');
    detail.className = 'outcome';
    const result = state === 'base' ? 'Original' : changed ? 'Changed' : 'Held';
    detail.textContent = result + ' · lead ' + Math.abs(margin).toFixed(2);
    box.append(heading, answer, detail);
    by('results').append(box);
  }
  by('status').textContent = explanations[state];
  for (const b of document.querySelectorAll('[data-state]')) {
    b.setAttribute('aria-pressed', b.dataset.state === state);
  }
}
for (const b of document.querySelectorAll('[data-state]')) {
  b.onclick = () => showStory(b.dataset.state);
}
showStory('base');

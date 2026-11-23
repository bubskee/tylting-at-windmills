(() => {
  const get = id => document.getElementById(id);
  const cases = JSON.parse(get('field-record').textContent);
  const figure = get('apply').closest('figure');
  let edited = false;
  function drawBoard(board) {
    const square = (content, cls) => '<span class="' + cls + '">' + content + '</span>';
    let grid = square('', 'edge');
    for (let col = 1; col <= 8; col++) grid += square(col, 'edge');
    for (let row = 0; row < 8; row++) {
      grid += square('ABCDEFGH'[row], 'edge');
      for (let col = 0; col < 8; col++) {
        const i = row * 8 + col;
        const piece = board[i] === 1 ? 'dark' : board[i] === -1 ? 'light' : 'empty';
        grid += square('<i class="' + piece + '"></i>', 'square' + (i === 37 ? ' target' : ''));
      }
    }
    get('board').innerHTML = grid;
    get('board').setAttribute('aria-label', edited ? 'Counterfactual rules board with E6 flipped.' : 'Original Othello board with E6 marked.');
  }
  function render() {
    const row = cases[Number(get('scene')?.value || 0)];
    const state = edited ? row.edited : row.clean;
    figure.classList.toggle('has-edit', edited);
    figure.classList.toggle('token-moved', row.clean.token !== row.edited.token);
    const action = get('apply');
    action.textContent = edited ? 'Restore original' : action.dataset.action;
    action.setAttribute('aria-pressed', String(edited));
    let finding;
    if (state.image) {
      get('church').src = '../instruments/matched/images/' + state.image;
      get('church').alt = (edited ? 'Edited' : 'Original') + ' church image, ' + row.id.replace('-', ' ');
      get('cell').style.left = (row.position[1] * 12.5) + '%';
      get('cell').style.top = (row.position[0] * 12.5) + '%';
      finding = edited ? 'Whole-image mean absolute RGB change is ' + row.mean_absolute_rgb_change.toPrecision(3) + '.' : 'The outline marks the cell where the brush will be applied.';
    } else if (state.board) {
      drawBoard(state.board);
      finding = edited ? 'On the rules board, ' + row.gained.join(' and ') + ' become legal. ' + row.lost.join(', ') + ' becomes illegal. The model still ranks ' + state.token + ' first.' : 'The model’s first choice is ' + state.token + '. The outlined disc marks E6.';
    } else {
      get('output-token').textContent = state.token.replace(/^␠+(?=.)/, '');
      get('output-token').title = 'Recorded token: ' + state.token + (state.token.startsWith('␠') ? ' (leading space)' : '');
      const range = Math.max(Math.abs(row.clean.margin), Math.abs(row.edited.margin), 1) * 1.18;
      const percent = value => (50 + 50 * value/range) + '%';
      figure.querySelector('.origin-point').style.left = percent(row.clean.margin);
      figure.querySelector('.edit-point').style.left = percent(row.edited.margin);
      const signed = value => (value > 0 ? '+' : '') + value.toLocaleString('en-US', {maximumFractionDigits: 4});
      get('margin-value').textContent = edited ? signed(row.clean.margin)+' → '+signed(row.edited.margin)+' logits' : signed(row.clean.margin)+' logits';
      const change = row.clean.token === row.edited.token ? 'The top token stayed the same.' : 'The top token changed from ' + row.clean.token.replace(/^␠+(?=.)/, '') + '.';
      finding = (edited ? change + ' ' : '') + 'Top-token logit ' + state.logit.toLocaleString('en-US', {maximumFractionDigits: 5}) + '.';
    }
    get('finding').textContent = finding;
    for (const link of document.querySelectorAll('a[data-method]')) {
      link.hash = encodeURIComponent(row.id) + '/' + encodeURIComponent(link.dataset.method);
    }
  }
  get('apply').onclick = () => { edited = !edited; render(); };
  if (get('scene')) get('scene').onchange = render;
  render();
})();

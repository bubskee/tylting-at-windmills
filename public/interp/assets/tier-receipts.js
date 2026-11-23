const picker = document.getElementById('receipt-picker');
const receipts = [...document.querySelectorAll('.receipt')];
function selectReceipt() {
  const id = location.hash.slice(1);
  const selected = receipts.find(row => row.id === id) || receipts[0];
  for (const row of receipts) row.hidden = row !== selected;
  picker.value = selected.id;
  if (id === selected.id) selected.focus({preventScroll: true});
}
picker.addEventListener('change', () => { location.hash = picker.value; });
window.addEventListener('hashchange', selectReceipt);
selectReceipt();

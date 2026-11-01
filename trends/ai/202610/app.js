const dialog = document.querySelector('#method-dialog');
let dialogTrigger;

document.querySelectorAll('[data-open-method]').forEach(button => {
  button.addEventListener('click', () => {
    dialogTrigger = button;
    dialog.showModal();
    document.body.classList.add('dialog-open');
  });
});
document.querySelector('.close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const box = dialog.getBoundingClientRect();
  if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
});
dialog.addEventListener('close', () => {
  document.body.classList.remove('dialog-open');
  dialogTrigger?.focus();
});

const cards = [...document.querySelectorAll('.trend-card')];
document.querySelectorAll('[data-filter]').forEach(button => {
  button.addEventListener('click', () => {
    const selected = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(filter => {
      const active = filter === button;
      filter.classList.toggle('active', active);
      filter.setAttribute('aria-pressed', String(active));
    });
    cards.forEach(card => { card.hidden = selected !== 'all' && card.dataset.group !== selected; });
    const count = cards.filter(card => !card.hidden).length;
    document.querySelector('.filter-count').textContent = `${count}개 트렌드`;
  });
});

const sections = [...document.querySelectorAll('.detail-section')];
const tocLinks = [...document.querySelectorAll('[data-section]')];
const backTop = document.querySelector('.back-top');
let scheduled = false;
function updatePosition() {
  scheduled = false;
  const reached = sections.filter(section => section.getBoundingClientRect().top <= 170);
  const active = reached.at(-1) || (sections[0].getBoundingClientRect().top < innerHeight ? sections[0] : null);
  tocLinks.forEach(link => {
    const selected = link.dataset.section === active?.id;
    link.classList.toggle('current', selected);
    if (selected) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  backTop.hidden = scrollY < 700;
}
addEventListener('scroll', () => {
  if (!scheduled) { requestAnimationFrame(updatePosition); scheduled = true; }
}, { passive: true });
addEventListener('resize', updatePosition);
addEventListener('hashchange', updatePosition);
updatePosition();

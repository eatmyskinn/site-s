const links = [...document.querySelectorAll('[data-lightbox]')];
const dialog = document.querySelector('dialog');
let active = 0;

function selectPhoto(position) {
  active = (position + links.length) % links.length;
  const link = links[active];
  const image = document.getElementById('large');
  image.src = link.href;
  image.alt = link.querySelector('img').alt;
  document.getElementById('caption').textContent =
    link.parentElement.querySelector('figcaption').textContent;
}
if (typeof dialog.showModal === 'function') {
  links.forEach((link, index) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      selectPhoto(index);
      dialog.showModal();
    });
  });
  document.getElementById('close').onclick = () => dialog.close();
  document.getElementById('prev').onclick = () => selectPhoto(active - 1);
  document.getElementById('next').onclick = () => selectPhoto(active + 1);
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') selectPhoto(active - 1);
    if (event.key === 'ArrowRight') selectPhoto(active + 1);
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
}
if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('appear');
        observer.unobserve(entry.target);
      }
    });
  });
  document
    .querySelectorAll('.section-title,.shots figure,.details>div')
    .forEach((item) => observer.observe(item));
}

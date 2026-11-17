const photographs = [
  {
    file: 'entrance.webp',
    caption: 'Вход в магазин',
    alt: 'Вход в магазин с синей вывеской «Автозапчасти»',
  },
  {
    file: 'address.webp',
    caption: 'Адрес на фасаде',
    alt: 'Адресная табличка «ул. Ибрагимова, 28» и указатель на стене магазина',
  },
];
const photo = document.querySelector('#shop-photo');
const caption = document.querySelector('#caption');
let selectedPhoto = 0;
const controls = document.querySelector('.switch');
controls.hidden = false;
controls.addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  selectedPhoto =
    (selectedPhoto + Number(button.dataset.step) + photographs.length) % photographs.length;
  const item = photographs[selectedPhoto];
  photo.src = 'assets/' + item.file;
  photo.alt = item.alt;
  caption.textContent = '0' + (selectedPhoto + 1) + ' / 02 · ' + item.caption;
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && photo.animate) {
    photo.animate(
      [
        { opacity: 0.75, transform: 'scale(1.025)' },
        { opacity: 1, transform: 'scale(1)' },
      ],
      { duration: 350, easing: 'ease-out' },
    );
  }
});
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('reached');
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.15 },
  );
  observer.observe(document.querySelector('.visit'));
}

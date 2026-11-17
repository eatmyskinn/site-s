const slides = [
  { file: 'lobby', title: 'Холл гостиницы', alt: 'Просторный холл с люстрами и плиточным полом' },
  { file: 'restaurant', title: 'Ресторанный зал', alt: 'Круглые накрытые столы в зале ресторана' },
  { file: 'lounge', title: 'Гостиная', alt: 'Диваны у окон в зоне отдыха' },
  {
    file: 'entrance',
    title: 'Вывеска над входом',
    alt: 'Вход в кафе-ресторан под вывеской «Версаль»',
  },
];
const buttons = document.querySelectorAll('[data-slide]');
const photo = document.getElementById('photo');
const caption = document.getElementById('caption');
buttons.forEach((button) => {
  button.addEventListener('click', () => {
    const slide = slides[Number(button.dataset.slide)];
    buttons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    photo.src = 'images/' + slide.file + '.webp';
    photo.alt = slide.alt;
    caption.textContent = slide.title;
    if (photo.animate && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      photo.animate(
        [
          { opacity: 0.65, transform: 'translateY(4px)' },
          { opacity: 1, transform: 'none' },
        ],
        { duration: 320 },
      );
    }
  });
});

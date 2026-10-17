/* Keep the subtitle's right edge aligned with the first header action. */
(() => {
  const subtitle = document.querySelector('.mast .lede');
  const action = document.querySelector('.mast [data-act="copyview"]');
  const mast = document.querySelector('.mast');
  if (!subtitle || !action || !mast) return;
  const align = () => {
    const button = action.getBoundingClientRect();
    const logo = mast.querySelector('.brand-heading').getBoundingClientRect();
    const width = button.top < logo.bottom ? button.left - subtitle.getBoundingClientRect().left : 0;
    subtitle.style.setProperty('--subtitle-width', width > 240 ? `${width}px` : '100%');
  };
  new ResizeObserver(align).observe(mast);
  window.addEventListener('resize', align, { passive: true });
  if (document.fonts) document.fonts.ready.then(align);
  align();
})();

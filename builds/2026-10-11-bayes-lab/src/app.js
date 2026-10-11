/* Tab router: hash-based, one lesson visible at a time. */
(function (root) {
  'use strict';

  const lessons = root.Lessons;
  const nav = document.querySelector('[data-testid="nav"]');
  const stage = document.querySelector('[data-testid="stage"]');
  const heading = document.querySelector('[data-testid="lesson-title"]');

  function currentId() {
    const id = root.location.hash.replace(/^#\/?/, '');
    return lessons.some((lesson) => lesson.id === id) ? id : lessons[0].id;
  }

  function show() {
    const id = currentId();
    const lesson = lessons.find((item) => item.id === id);
    nav.querySelectorAll('a').forEach((link) => {
      const active = link.dataset.id === id;
      link.setAttribute('aria-current', active ? 'page' : 'false');
    });
    heading.textContent = lesson.title;
    stage.innerHTML = '';
    lesson.render(stage);
    document.title = `${lesson.title} · Bayes Lab`;
  }

  nav.innerHTML = lessons
    .map((lesson, i) => `<a href="#/${lesson.id}" data-id="${lesson.id}" data-testid="tab-${lesson.id}"><span class="idx">${i + 1}</span> ${lesson.title}</a>`)
    .join('');
  root.addEventListener('hashchange', show);
  show();
})(window);

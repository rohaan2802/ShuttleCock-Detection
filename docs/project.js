const root = document.documentElement;
const themeButton = document.querySelector("#project-theme");
const menu = document.querySelector("#project-menu");
const nav = document.querySelector(".project-nav");
function theme(value) {
  root.dataset.theme = value;
  const label = value === "light" ? "Switch to dark theme" : "Switch to light theme";
  themeButton.setAttribute("aria-label", label);
  themeButton.title = label;
}
const preferredTheme = matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
let storedTheme;
try { storedTheme = localStorage.getItem("shuttle-theme"); } catch {}
theme(storedTheme === "light" || storedTheme === "dark" ? storedTheme : preferredTheme);
themeButton.addEventListener("click", () => {
  theme(root.dataset.theme === "light" ? "dark" : "light");
  try { localStorage.setItem("shuttle-theme", root.dataset.theme); } catch {}
});
function openMenu(open) {
  nav.classList.toggle("open", open);
  menu.setAttribute("aria-expanded", String(open));
  menu.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
}
menu.addEventListener("click", () => openMenu(!nav.classList.contains("open")));
nav.addEventListener("click", event => { if (event.target.closest("a")) openMenu(false); });
nav.addEventListener("keydown", event => {
  if (event.key === "Escape") { openMenu(false); menu.focus(); }
});
if (location.protocol === "file:") {
  const status = document.querySelector("#status");
  status.textContent = "For live detection, run python app.py web from the repository folder.";
}
const topButton = document.querySelector("#project-top");
const scrollState = () => { topButton.hidden = scrollY < 450; };
addEventListener("scroll", scrollState, { passive: true });
scrollState();
topButton.addEventListener("click", () => { document.querySelector(".brand").focus({preventScroll:true}); scrollTo({top:0}); });
for (const slider of document.querySelectorAll(".project-slider")) {
  const panel = document.getElementById(slider.getAttribute("aria-controls"));
  function sync() {
    const width = panel.scrollWidth - panel.clientWidth;
    slider.hidden = width < 2;
    slider.max = Math.max(1, width);
    slider.value = panel.scrollLeft;
  }
  slider.addEventListener("input", () => { panel.scrollLeft = Number(slider.value); });
  panel.addEventListener("scroll", sync);
  new ResizeObserver(sync).observe(panel);
}
const cards = [...document.querySelectorAll(".project-gallery figure")];
const search = document.querySelector("#gallery-search");
const category = document.querySelector("#gallery-category");
const visible = () => cards.filter(card => !card.hidden);
function filter() {
  for (const card of cards) {
    card.hidden = (category.value && category.value !== card.dataset.category) ||
      !card.textContent.toLowerCase().includes(search.value.trim().toLowerCase());
  }
  document.querySelector("#gallery-count").textContent = visible().length + " of " + cards.length + " figures";
}
search.addEventListener("input",filter);
category.addEventListener("change",filter);

const viewer = document.querySelector("#project-viewer");
const stage = viewer.querySelector(".project-stage");
const zoom = viewer.querySelector("#figure-zoom");
let index;
let opener;
let touch;
function setZoom(on) {
  stage.classList.toggle("zoom",on);
  zoom.setAttribute("aria-pressed",String(on));
  zoom.textContent = on ? "Fit image" : "Zoom";
  stage.scrollTo(0,0);
}
function show(offset) {
  const figures = visible();
  index = (index + offset + figures.length) % figures.length;
  const card = figures[index];
  const title = card.querySelector("strong").textContent;
  const img = stage.querySelector("img");
  img.src = card.querySelector("a").href;
  img.alt = title;
  viewer.querySelector("h2").textContent = title;
  viewer.querySelector(".viewer-caption").textContent = card.querySelector("figcaption span").textContent;
  setZoom(false);
}
for (const card of cards) {
  const link = card.querySelector("a");
  link.addEventListener("click", event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    opener = link;
    index = visible().indexOf(card);
    show(0);
    viewer.showModal();
  });
}
viewer.querySelector("#figure-prev").addEventListener("click", () => show(-1));
viewer.querySelector("#figure-next").addEventListener("click", () => show(1));
viewer.querySelector("#figure-close").addEventListener("click", () => viewer.close());
zoom.addEventListener("click", () => setZoom(!stage.classList.contains("zoom")));
viewer.addEventListener("close", () => opener?.focus());
viewer.addEventListener("keydown", event => {
  if (event.target === stage && stage.classList.contains("zoom")) return;
  if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
    event.preventDefault();
    show(event.key === "ArrowRight" ? 1 : -1);
  }
});
stage.addEventListener("touchstart", event => { touch = event.changedTouches[0]; }, {passive:true});
stage.addEventListener("touchcancel", () => { touch = undefined; });
stage.addEventListener("touchend", event => {
  if (!touch || stage.classList.contains("zoom")) return;
  const end = event.changedTouches[0], dx = end.clientX - touch.clientX, dy = end.clientY - touch.clientY;
  touch = undefined;
  if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)*1.3) show(dx < 0 ? 1 : -1);
}, {passive:true});

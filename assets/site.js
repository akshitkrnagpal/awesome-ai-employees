"use strict";

const PAGE_SIZE = 18;
// Labels and colors are presentation metadata; company records stay in data/companies.json.
const categoryStyles = {
  "Horizontal AI workforce and automation platforms": [
    "AI workforce",
    "Workforce platforms",
    "#cdd8fa",
    "#2b3f7f",
    "grid",
  ],
  "Sales, SDR, and revenue agents": [
    "Sales & revenue",
    "Sales & revenue",
    "#c7dff4",
    "#264e75",
    "trend",
  ],
  "Marketing, growth, and AI CMO agents": [
    "Marketing & growth",
    "Marketing & growth",
    "#e4daf3",
    "#62437f",
    "spark",
  ],
  "Customer support, CX, and ecommerce agents": [
    "Customer support",
    "Customer support",
    "#d1e9e3",
    "#2b5f55",
    "chat",
  ],
  "Recruiting and HR agents": [
    "Recruiting & HR",
    "Recruiting & HR",
    "#f6e2bd",
    "#715622",
    "people",
  ],
  "Finance, accounting, and back-office agents": [
    "Finance & accounting",
    "Finance & accounting",
    "#d9e4d2",
    "#445938",
    "chart",
  ],
  "Legal and compliance agents": [
    "Legal & compliance",
    "Legal & compliance",
    "#e0def1",
    "#574c78",
    "scale",
  ],
  "Software engineering, IT, and SRE agents": [
    "Engineering & IT",
    "Engineering & IT",
    "#c4d0f2",
    "#374c87",
    "code",
  ],
  "Security and SOC agents": [
    "Security",
    "Security & SOC",
    "#d4e1ec",
    "#435a6f",
    "shield",
  ],
  "Healthcare admin and clinical operations agents": [
    "Health",
    "Healthcare",
    "#f3dcd8",
    "#7e504b",
    "health",
  ],
  "Logistics and supply-chain agents": [
    "Logistics",
    "Logistics & supply chain",
    "#e6e6c9",
    "#606135",
    "box",
  ],
  "Real estate and property operations agents": [
    "Real estate",
    "Real estate",
    "#d7e6e3",
    "#415f5a",
    "home",
  ],
  "Insurance operations agents": [
    "Insurance",
    "Insurance",
    "#e6ddef",
    "#644d78",
    "umbrella",
  ],
  "Procurement and supplier operations agents": [
    "Procurement",
    "Procurement",
    "#f0dfcb",
    "#715636",
    "cart",
  ],
};
const paths = {
  grid: '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="3" y="15" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/>',
  trend: '<path d="m3 17 6-6 4 4 8-10M15 5h6v6"/>',
  spark:
    '<path d="m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6Z"/>',
  chat: '<path d="M20 11a8 8 0 0 1-8 8H4l1.5-4A8 8 0 1 1 20 11Z"/><path d="M8 10h8M8 13h5"/>',
  people:
    '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4v3"/>',
  chart: '<path d="M4 20V4M4 20h17M9 16v-5M14 16V7M19 16v-9"/>',
  scale:
    '<path d="M12 3v18M7 21h10M4 7h16M5 7l-3 7h6L5 7ZM19 7l-3 7h6l-3-7Z"/>',
  code: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
  shield:
    '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  health: '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6V3Z"/>',
  box: '<path d="m12 2 9 5v10l-9 5-9-5V7l9-5ZM3 7l9 5 9-5M12 12v10M7 5l10 5"/>',
  home: '<path d="m3 11 9-8 9 8M5 9v12h14V9M9 21v-8h6v8"/>',
  umbrella: '<path d="M3 12a9 9 0 0 1 18 0H3ZM12 3V1M12 12v7a2 2 0 0 0 4 0"/>',
  cart: '<path d="M3 3h3l3 13h10l3-9H7M10 21h.01M18 21h.01"/>',
};
const $ = (selector) => document.querySelector(selector);
const icon = (name, className = "") =>
  `<svg class="${className}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.grid}</svg>`;
const escapeHTML = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
let companies = [];
let companyIcons = {};
let categories = [];
let activeCategory = "";
let visibleCount = PAGE_SIZE;

function updateURL() {
  const url = new URL(window.location.href);
  for (const [key, value] of [
    ["q", $("#search").value.trim()],
    ["category", activeCategory],
    ["sort", $("#sort").value === "curated" ? "" : $("#sort").value],
  ]) {
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  }
  history.replaceState(null, "", url);
}

function restoreURL() {
  const params = new URLSearchParams(window.location.search);
  $("#search").value = params.get("q") || "";
  activeCategory = categories.some(
    (category) => category.name === params.get("category"),
  )
    ? params.get("category")
    : "";
  $("#sort").value = ["az", "za"].includes(params.get("sort"))
    ? params.get("sort")
    : "curated";
  visibleCount = PAGE_SIZE;
}

// Squarified treemap: tile areas encode company counts, with readable aspect ratios.
function layoutTiles(items) {
  const aspect =
    $("#category-map").clientWidth / $("#category-map").clientHeight;
  const bounds = { x: 0, y: 0, width: 100 * aspect, height: 100 };
  const total = items.reduce((sum, item) => sum + item.count, 0);
  const remaining = items.map((item) => ({
    ...item,
    area: (item.count / total) * 10000 * aspect,
  }));
  const tiles = [];
  const worst = (row, side) => {
    if (!row.length) return Infinity;
    const areas = row.map((item) => item.area);
    const sum = areas.reduce((a, b) => a + b, 0);
    return Math.max(
      (side ** 2 * Math.max(...areas)) / sum ** 2,
      sum ** 2 / (side ** 2 * Math.min(...areas)),
    );
  };
  while (remaining.length) {
    const row = [remaining.shift()];
    const side = Math.min(bounds.width, bounds.height);
    while (
      remaining.length &&
      worst([...row, remaining[0]], side) <= worst(row, side)
    )
      row.push(remaining.shift());
    const area = row.reduce((sum, item) => sum + item.area, 0);
    const vertical = bounds.width >= bounds.height;
    const thickness = area / (vertical ? bounds.height : bounds.width);
    let offset = vertical ? bounds.y : bounds.x;
    for (const item of row) {
      const length = item.area / thickness;
      const rect = vertical
        ? { x: bounds.x, y: offset, width: thickness, height: length }
        : { x: offset, y: bounds.y, width: length, height: thickness };
      tiles.push({
        ...item,
        x: rect.x / aspect,
        y: rect.y,
        width: rect.width / aspect,
        height: rect.height,
      });
      offset += length;
    }
    if (vertical) {
      bounds.x += thickness;
      bounds.width -= thickness;
    } else {
      bounds.y += thickness;
      bounds.height -= thickness;
    }
  }
  return tiles;
}

function renderCategories() {
  const filterButton = (category) =>
    `<button class="category-filter" data-category="${escapeHTML(category.name)}" aria-pressed="false"><span class="category-filter-label">${icon(category.icon)}${escapeHTML(category.sidebar)}</span><span>${category.count}</span></button>`;
  $("#category-filters").innerHTML =
    filterButton({
      name: "",
      sidebar: "All categories",
      icon: "grid",
      count: companies.length,
    }) + categories.map(filterButton).join("");
  $("#mobile-category").innerHTML =
    '<option value="">All categories</option>' +
    categories
      .map(
        (category) =>
          `<option value="${escapeHTML(category.name)}">${escapeHTML(category.sidebar)} (${category.count})</option>`,
      )
      .join("");
  renderMap();
}

function renderMap() {
  $("#category-map").innerHTML = layoutTiles(
    [...categories].sort((a, b) => b.count - a.count),
  )
    .map(
      (tile) =>
        `<button class="map-tile ${tile.count <= 6 ? "compact" : ""} ${tile.count <= 3 ? "micro" : ""}" data-category="${escapeHTML(tile.name)}" title="${escapeHTML(tile.sidebar)}: ${tile.count} companies" aria-label="${escapeHTML(tile.sidebar)}: ${tile.count} companies" aria-pressed="false" style="left:${tile.x}%;top:${tile.y}%;width:${tile.width}%;height:${tile.height}%;--tile-bg:${tile.background};--tile-ink:${tile.foreground}">${icon(tile.icon, "tile-icon")}<span class="tile-number">${tile.count}</span><span class="tile-label">${escapeHTML(tile.short)}</span></button>`,
    )
    .join("");
  $("#category-map")
    .querySelectorAll("[data-category]")
    .forEach((button) => {
      const selected = button.dataset.category === activeCategory;
      button.setAttribute("aria-pressed", String(selected));
      button.classList.toggle("selected", selected);
    });
}

function setCategory(category, scroll = false) {
  activeCategory = category;
  visibleCount = PAGE_SIZE;
  renderResults();
  updateURL();
  if (scroll) {
    $("#directory").scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
    $("#directory-title").setAttribute("tabindex", "-1");
    $("#directory-title").focus({ preventScroll: true });
  }
}

function renderResults() {
  const query = $("#search").value.trim().toLocaleLowerCase();
  const terms = query.split(/\s+/).filter(Boolean);
  let results = companies.filter(
    (company) =>
      (!activeCategory || company.category === activeCategory) &&
      terms.every((term) => company.searchText.includes(term)),
  );
  const direction = $("#sort").value;
  if (direction !== "curated")
    results = [...results].sort((a, b) =>
      direction === "az"
        ? a.company.localeCompare(b.company)
        : b.company.localeCompare(a.company),
    );
  const shown = results.slice(0, visibleCount);
  $("#company-grid").innerHTML = shown
    .map((company) => {
      const category = categories.find(
        (item) => item.name === company.category,
      );
      const initials = company.company
        .replace(/\([^)]*\)/g, "")
        .trim()
        .split(/[\s.]+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("");
      const logo = company.rank % 4;
      const logoColors = [
        ["#eee9fa", "#7051a6"],
        ["#e5ebfc", "#4b62bc"],
        ["#e0ede7", "#396c56"],
        ["#f8ece0", "#8a572c"],
      ][logo];
      const imagePath = companyIcons[company.company]?.path;
      const image = imagePath
        ? `<img class="company-icon" src="${escapeHTML(imagePath)}" width="34" height="34" alt="" loading="lazy" decoding="async">`
        : "";
      return `<article class="company-card"><div class="card-heading"><span class="company-monogram" aria-hidden="true" style="--logo-bg:${logoColors[0]};--logo-ink:${logoColors[1]}">${escapeHTML(initials)}${image}</span><h3 class="card-link"><a href="${escapeHTML(company.link)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHTML(company.company)} (opens in a new tab)">${escapeHTML(company.company)}</a><span aria-hidden="true">↗</span></h3></div><p class="company-description">${escapeHTML(company.ai_employee_angle)}</p><span class="card-category" style="--tag-bg:${category.background}55;--tag-ink:${category.foreground}">${escapeHTML(category.sidebar)}</span></article>`;
    })
    .join("");
  $("#company-grid").setAttribute("aria-busy", "false");
  $("#result-count").innerHTML =
    `<strong>${results.length}</strong> ${results.length === 1 ? "company" : "companies"}${activeCategory ? ` in ${escapeHTML(categories.find((category) => category.name === activeCategory).sidebar)}` : " to explore"}${query ? ` matching “${escapeHTML($("#search").value.trim())}”` : ""}`;
  $("#empty-state").hidden = results.length > 0;
  $("#clear-filters").hidden = !query && !activeCategory;
  $("#curation-badge").hidden = !!query || !!activeCategory;
  $("#load-more").hidden = results.length <= visibleCount;
  $("#shown-count").textContent = results.length
    ? `Showing ${shown.length} of ${results.length} companies`
    : "";
  $("#mobile-category").value = activeCategory;
  document.querySelectorAll("[data-category]").forEach((button) => {
    const selected = button.dataset.category === activeCategory;
    button.setAttribute("aria-pressed", String(selected));
    button.classList.toggle("selected", selected);
  });
}

async function loadDirectory() {
  $("#error-state").hidden = true;
  $("#company-grid").setAttribute("aria-busy", "true");
  $("#result-count").textContent = "Loading the directory…";
  try {
    const [response, icons] = await Promise.all([
      fetch("data/companies.json"),
      fetch("assets/company-icons/manifest.json")
        .then((response) => (response.ok ? response.json() : {}))
        .catch(() => ({})),
    ]);
    if (!response.ok)
      throw new Error(`Directory request failed: ${response.status}`);
    const records = await response.json();
    companyIcons = icons;
    companies = records.map((company) => ({
      ...company,
      searchText:
        `${company.company} ${company.category} ${company.ai_employee_angle}`.toLocaleLowerCase(),
    }));
    categories = [...new Set(companies.map((company) => company.category))].map(
      (name) => {
        const [short, sidebar, background, foreground, categoryIcon] =
          categoryStyles[name] || [name, name, "#dce4fa", "#435a98", "grid"];
        return {
          name,
          short,
          sidebar,
          background,
          foreground,
          icon: categoryIcon,
          count: companies.filter((company) => company.category === name)
            .length,
        };
      },
    );
    document.querySelectorAll("[data-company-count]").forEach((element) => {
      element.textContent = companies.length;
    });
    $("#category-count").textContent = categories.length;
    $("#sidebar-category-count").textContent = categories.length;
    renderCategories();
    restoreURL();
    renderResults();
  } catch (error) {
    $("#company-grid").setAttribute("aria-busy", "false");
    $("#error-state").hidden = false;
    $("#result-count").textContent = "Directory unavailable";
    console.error(error);
  }
}

function resetFilters() {
  $("#search").value = "";
  setCategory("");
  $("#search").focus();
}

$("#search").addEventListener("input", () => {
  visibleCount = PAGE_SIZE;
  renderResults();
  updateURL();
});
$("#sort").addEventListener("change", () => {
  visibleCount = PAGE_SIZE;
  renderResults();
  updateURL();
});
$("#category-filters").addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (button) setCategory(button.dataset.category);
});
$("#category-map").addEventListener("click", (event) => {
  const button = event.target.closest("[data-category]");
  if (button) setCategory(button.dataset.category, true);
});
$("#mobile-category").addEventListener("change", (event) =>
  setCategory(event.target.value),
);
$("#clear-filters").addEventListener("click", resetFilters);
$("#reset-search").addEventListener("click", resetFilters);
$("#retry-load").addEventListener("click", loadDirectory);
// A missing or undecodable image reveals the initials underneath it.
$("#company-grid").addEventListener(
  "error",
  (event) => {
    if (event.target.matches(".company-icon")) event.target.remove();
  },
  true,
);
$("#load-more").addEventListener("click", () => {
  const previousCount = visibleCount;
  visibleCount += PAGE_SIZE;
  renderResults();
  const firstNewLink =
    $("#company-grid").children[previousCount]?.querySelector("a");
  firstNewLink?.focus({ preventScroll: true });
});
document.addEventListener("keydown", (event) => {
  if (
    event.key === "/" &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey &&
    !event.target.closest('input, textarea, select, [contenteditable="true"]')
  ) {
    event.preventDefault();
    $("#search").focus();
  }
});
window.addEventListener("popstate", () => {
  if (companies.length) {
    restoreURL();
    renderResults();
  }
});
new ResizeObserver(() => {
  if (categories.length) renderMap();
}).observe($("#category-map"));
loadDirectory();

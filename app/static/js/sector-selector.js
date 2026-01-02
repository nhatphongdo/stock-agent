// Sector Selector Module

let sectorsData = {};
let sectorSelectorOverlay = null;
let sectorsListContainer = null;
let sectorSearchInput = null;

/**
 * Initialize sector selector DOM elements.
 */
function initSectorSelectorElements() {
  sectorSelectorOverlay = document.getElementById("sector-selector-overlay");
  sectorsListContainer = document.getElementById("sectors-list");
  sectorSearchInput = document.getElementById("sector-search-input");
}

/**
 * Fetch sectors from API.
 */
async function fetchSectors() {
  try {
    const response = await fetch("/sectors");
    if (!response.ok) throw new Error("Failed to fetch sectors");
    const data = await response.json();
    sectorsData = data.sectors || {};
    return sectorsData;
  } catch (error) {
    console.error("Error fetching sectors:", error);
    return {};
  }
}

/**
 * Render sectors list in the popup.
 * @param {Object} sectors - Dictionary of sectors keyed by icbCode
 */
function renderSectorsList(sectors) {
  if (!sectorsListContainer) initSectorSelectorElements();

  const sectorKeys = Object.keys(sectors);
  if (!sectors || sectorKeys.length === 0) {
    sectorsListContainer.innerHTML =
      '<div class="no-results">Không có dữ liệu ngành</div>';
    return;
  }

  const groupTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("sector-group-template")
  );
  const itemTemplate = /** @type {HTMLTemplateElement} */ (
    document.getElementById("sector-item-template")
  );

  // Clear existing content
  sectorsListContainer.innerHTML = "";

  // Iterate over level 1 sectors (groups)
  Object.values(sectors).forEach((group) => {
    const children = Object.values(group.children || {});
    if (children.length === 0) return;

    // Clone group template
    const groupEl = /** @type {HTMLElement} */ (
      /** @type {DocumentFragment} */ (groupTemplate.content.cloneNode(true))
        .firstElementChild
    );
    groupEl.dataset.group = group.icbCode;
    groupEl.querySelector(".sector-group-name").textContent = group.icbName;

    // Iterate over level 2 sectors (children)
    children.forEach((sector) => {
      const name = sector.icbName;
      const code = sector.icbCode;
      // Clone item template
      const itemEl = /** @type {HTMLElement} */ (
        /** @type {DocumentFragment} */ (itemTemplate.content.cloneNode(true))
          .firstElementChild
      );
      itemEl.dataset.code = code;
      itemEl.dataset.name = name;
      itemEl.querySelector(".sector-item-name").textContent = name;
      itemEl.querySelector(".sector-item-code").textContent = code;
      itemEl.addEventListener("click", () => selectSector(code, name));
      groupEl.appendChild(itemEl);
    });

    sectorsListContainer.appendChild(groupEl);
  });

  lucide.createIcons({ root: sectorsListContainer });
}

/**
 * Filter sectors by search query.
 * @param {string} query - Search query
 */
function filterSectors(query) {
  if (!sectorsListContainer) initSectorSelectorElements();

  const normalizedQuery = query.toLowerCase().trim();
  const groups = sectorsListContainer.querySelectorAll(".sector-group");

  groups.forEach((group) => {
    const items = group.querySelectorAll(".sector-item");
    let hasVisibleItem = false;

    items.forEach((item) => {
      const name = item.dataset.name.toLowerCase();
      const code = item.dataset.code.toLowerCase();
      const isMatch =
        !normalizedQuery ||
        name.includes(normalizedQuery) ||
        code.includes(normalizedQuery);

      if (isMatch) {
        item.classList.remove("hidden");
        hasVisibleItem = true;
      } else {
        item.classList.add("hidden");
      }
    });

    // Hide entire group if no visible items
    if (hasVisibleItem) {
      group.classList.remove("hidden");
    } else {
      group.classList.add("hidden");
    }
  });
}

/**
 * Open sector selector popup.
 */
async function openSectorSelector() {
  if (!sectorSelectorOverlay) initSectorSelectorElements();

  // Show overlay
  sectorSelectorOverlay.classList.add("show");
  lucide.createIcons({ root: sectorSelectorOverlay });

  // Clear search
  if (sectorSearchInput) {
    sectorSearchInput.value = "";
    sectorSearchInput.focus();
  }

  // Fetch and render sectors if not already loaded
  if (Object.keys(sectorsData).length === 0) {
    const sectors = await fetchSectors();
    renderSectorsList(sectors);
  } else {
    renderSectorsList(sectorsData);
    // Reset filter
    filterSectors("");
  }
}

/**
 * Close sector selector popup.
 */
function closeSectorSelector() {
  if (!sectorSelectorOverlay) initSectorSelectorElements();
  sectorSelectorOverlay.classList.remove("show");
}

/**
 * Handle sector selection.
 * @param {string} code - ICB sector code
 * @param {string} name - Sector name
 */
function selectSector(code, name) {
  closeSectorSelector();
  // Trigger sector analysis via chat module
  if (typeof analyzeTask === "function") {
    analyzeTask(false, code, name);
  } else {
    console.error("analyzeTask function not found");
  }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initSectorSelectorElements();

  // Close on overlay click (outside modal)
  if (sectorSelectorOverlay) {
    sectorSelectorOverlay.addEventListener("click", (e) => {
      if (e.target === sectorSelectorOverlay) {
        closeSectorSelector();
      }
    });
  }

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "Escape" &&
      sectorSelectorOverlay &&
      sectorSelectorOverlay.classList.contains("show")
    ) {
      closeSectorSelector();
    }
  });
});

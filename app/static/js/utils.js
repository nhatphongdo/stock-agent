/**
 * Sets up symbol autocomplete for an input element.
 * @param {HTMLInputElement | null} inputEl - The input element.
 * @param {HTMLElement | null} suggestionsEl - The suggestions container element.
 * @param {(symbol: string) => void} onSelect - Callback when a symbol is selected.
 */
function sharedSetupSymbolAutocomplete(inputEl, suggestionsEl, onSelect) {
  if (!inputEl || !suggestionsEl) return;

  inputEl.addEventListener("input", () => {
    const query = inputEl.value.trim().toUpperCase();
    if (!query || query.length < 1) {
      suggestionsEl.classList.add("hidden");
      return;
    }

    // Use symbolsMap (filtered for valid stocks only)
    const matches = Object.entries(symbolsMap)
      .filter(([symbol, info]) => {
        const name = typeof info === "object" ? info.name : info;
        return (
          symbol.includes(query) ||
          (name && name.toLowerCase().includes(query.toLowerCase()))
        );
      })
      .slice(0, 10);

    if (matches.length === 0) {
      suggestionsEl.classList.add("hidden");
      return;
    }

    suggestionsEl.innerHTML = matches
      .map(([symbol, info]) => {
        const name = typeof info === "object" ? info.name : info;
        return `
          <div class="px-4 py-2 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer flex justify-between items-center" data-symbol="${symbol}">
            <span class="font-bold text-emerald-600 dark:text-emerald-400">${symbol}</span>
            <span class="text-xs text-slate-500 truncate ml-2">${
              name || ""
            }</span>
          </div>
        `;
      })
      .join("");

    // Add click handlers for suggestions
    suggestionsEl.querySelectorAll("[data-symbol]").forEach((item) => {
      item.addEventListener("click", () => {
        const symbol = item.getAttribute("data-symbol");
        onSelect(symbol);
        suggestionsEl.classList.add("hidden");
      });
    });

    suggestionsEl.classList.remove("hidden");
  });

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const query = inputEl.value.trim().toUpperCase();
      if (query) {
        onSelect(query);
        suggestionsEl.classList.add("hidden");
      }
    }
  });

  // Hide suggestions when clicking outside
  document.addEventListener("click", (e) => {
    const target = /** @type {Node} */ (e.target);
    if (!inputEl.contains(target) && !suggestionsEl.contains(target)) {
      suggestionsEl.classList.add("hidden");
    }
  });
}

/**
 * Gets the initials from a name.
 * @param {string} name - The full name.
 * @returns {string} The initials (e.g., "John Doe" -> "JD").
 */
function getInitials(name) {
  if (!name) return "??";
  const parts = name.split(" ");
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

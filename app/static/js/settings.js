// Settings Variables (Initialized in DOMContentLoaded or lazily)
let settingsOverlay,
  blacklistInput,
  blacklistTagsContainer,
  returnRateInput,
  dividendRateInput,
  profitRateInput,
  saveSettingsBtn;
let whitelistInput, whitelistTagsContainer, whitelistSuggestions;

let tempBlacklist = [];
let tempWhitelist = [];

function initSettingsElements() {
  settingsOverlay = document.getElementById("settings-overlay");
  blacklistInput = document.getElementById("blacklist-input");
  blacklistTagsContainer = document.getElementById("blacklist-tags-container");
  returnRateInput = document.getElementById("return-rate-input");
  dividendRateInput = document.getElementById("dividend-rate-input");
  profitRateInput = document.getElementById("profit-rate-input");
  saveSettingsBtn = document.getElementById("save-settings-btn");

  whitelistInput = document.getElementById("whitelist-input");
  whitelistTagsContainer = document.getElementById("whitelist-tags-container");
  whitelistSuggestions = document.getElementById("whitelist-suggestions");
}

/**
 * Opens the settings modal and initializes values from the current user.
 */
function openSettings() {
  if (!currentUser) return;
  if (!settingsOverlay) initSettingsElements();

  const userMenu = document.getElementById("user-menu");
  if (userMenu) userMenu.classList.remove("show");
  settingsOverlay.classList.add("show");

  tempBlacklist = [...currentUser.black_list];
  tempWhitelist = [...(currentUser.white_list || [])];
  returnRateInput.value = currentUser.return_rate || 0;
  dividendRateInput.value = currentUser.dividend_rate || 0;
  profitRateInput.value = currentUser.profit_rate || 0;
  renderBlacklistTags();
  renderWhitelistTags();
  lucide.createIcons({ root: settingsOverlay });
}

/**
 * Closes the settings modal.
 */
function closeSettings() {
  if (!settingsOverlay) initSettingsElements();
  settingsOverlay.classList.remove("show");
}

/**
 * Renders the blacklist tags in the settings modal.
 */
function renderBlacklistTags() {
  if (!blacklistTagsContainer) initSettingsElements();
  blacklistTagsContainer.innerHTML = "";
  /** @type {HTMLTemplateElement} */
  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("blacklist-tag-template")
  );

  tempBlacklist.forEach((item, index) => {
    const clone = document.importNode(template.content, true);
    const tagLabel = /** @type {HTMLElement} */ (
      clone.querySelector(".js-tag-label")
    );
    const removeBtn = /** @type {HTMLElement} */ (
      clone.querySelector(".js-remove-tag")
    );

    tagLabel.textContent = item;
    removeBtn.onclick = () => removeBlacklistItem(index);

    blacklistTagsContainer.appendChild(clone);
  });
  lucide.createIcons({ root: blacklistTagsContainer });
}

/**
 * Adds an item to the temporary blacklist.
 * @param {string} text - The text to add.
 */
function addBlacklistItem(text) {
  const val = text.trim();
  if (val && !tempBlacklist.includes(val)) {
    tempBlacklist.push(val);
    renderBlacklistTags();
  }
  if (blacklistInput) blacklistInput.value = "";
}

/**
 * Removes an item from the temporary blacklist by index.
 * @param {number} index - The index of the item to remove.
 */
function removeBlacklistItem(index) {
  tempBlacklist.splice(index, 1);
  renderBlacklistTags();
}

// --- Whitelist Functions ---
/**
 * Renders the whitelist tags in the settings modal.
 */
function renderWhitelistTags() {
  if (!whitelistTagsContainer) initSettingsElements();
  whitelistTagsContainer.innerHTML = "";
  /** @type {HTMLTemplateElement} */
  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("whitelist-tag-template")
  );

  tempWhitelist.forEach((item, index) => {
    const clone = document.importNode(template.content, true);
    const tagLabel = /** @type {HTMLElement} */ (
      clone.querySelector(".js-tag-label")
    );
    const removeBtn = /** @type {HTMLElement} */ (
      clone.querySelector(".js-remove-tag")
    );

    tagLabel.textContent = item;
    removeBtn.onclick = () => removeWhitelistItem(index);

    whitelistTagsContainer.appendChild(clone);
  });
  lucide.createIcons({ root: whitelistTagsContainer });
}

/**
 * Adds a ticker symbol to the temporary whitelist.
 * @param {string} ticker - The ticker symbol to add.
 */
function addWhitelistItem(ticker) {
  const val = ticker.trim().toUpperCase();
  if (val && !tempWhitelist.includes(val) && tempWhitelist.length < 30) {
    if (Object.keys(symbolsMap).length === 0 || symbolsMap[val]) {
      tempWhitelist.push(val);
      renderWhitelistTags();
    }
  }
  if (whitelistInput) whitelistInput.value = "";
  if (whitelistSuggestions) whitelistSuggestions.classList.add("hidden");
}

/**
 * Removes an item from the temporary whitelist by index.
 * @param {number} index - The index of the item to remove.
 */
function removeWhitelistItem(index) {
  tempWhitelist.splice(index, 1);
  renderWhitelistTags();
}

/**
 * Saves the temporary settings to the backend.
 * @returns {Promise<void>}
 */
async function saveSettings() {
  if (!currentUser) return;
  if (!saveSettingsBtn) initSettingsElements();

  saveSettingsBtn.disabled = true;
  saveSettingsBtn.innerHTML =
    '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Đang lưu...';
  lucide.createIcons({ root: saveSettingsBtn });

  const body = {
    black_list: tempBlacklist,
    white_list: tempWhitelist,
    return_rate: parseFloat(returnRateInput.value) || 0,
    dividend_rate: parseFloat(dividendRateInput.value) || 0,
    profit_rate: parseFloat(profitRateInput.value) || 0,
  };

  try {
    const response = await fetch(`/users/${currentUser.id}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (response.ok) {
      const updatedUser = await response.json();
      const idx = users.findIndex((u) => u.id === updatedUser.id);
      if (idx !== -1) users[idx] = updatedUser;
      currentUser = updatedUser;

      // Pulse effect
      saveSettingsBtn.classList.remove("bg-premium-gradient");
      saveSettingsBtn.classList.add("bg-emerald-500");
      saveSettingsBtn.innerHTML =
        '<i data-lucide="check" class="w-4 h-4"></i> Đã lưu!';
      lucide.createIcons({ root: saveSettingsBtn });

      setTimeout(() => {
        closeSettings();
        saveSettingsBtn.classList.add("bg-premium-gradient");
        saveSettingsBtn.classList.remove("bg-emerald-500");
        saveSettingsBtn.innerHTML = "Lưu thay đổi";
        lucide.createIcons({ root: saveSettingsBtn });
        saveSettingsBtn.disabled = false;
      }, 1000);
    }
  } catch (error) {
    console.error("Error saving settings:", error);
    saveSettingsBtn.disabled = false;
    saveSettingsBtn.innerHTML = "Lưu thay đổi";
  }
}

// Initialize Settings Autocomplete
document.addEventListener("DOMContentLoaded", () => {
  initSettingsElements();

  if (typeof sharedSetupSymbolAutocomplete === "function") {
    sharedSetupSymbolAutocomplete(
      whitelistInput,
      whitelistSuggestions,
      (symbol) => {
        addWhitelistItem(symbol);
      },
    );
  }

  if (blacklistInput) {
    blacklistInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        addBlacklistItem(blacklistInput.value);
      }
    });
  }
});

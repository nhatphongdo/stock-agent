/**
 * Portfolio Management Module
 */

// --- DOM Elements ---
let portfolioOverlay;
let portfolioList;
let newStockSymbol;
let newStockPrice;
let addStockBtn;
let addStockIcon;
let addStockText;
let cancelEditBtn;

let editingStockId = null;

/**
 * Initialize Portfolio module
 */
function initPortfolio() {
  portfolioOverlay = document.getElementById("portfolio-overlay");
  portfolioList = document.getElementById("portfolio-list");
  newStockSymbol = document.getElementById("new-stock-symbol");
  newStockPrice = document.getElementById("new-stock-price");
  addStockBtn = document.getElementById("add-stock-btn");
  addStockIcon = document.getElementById("add-stock-icon");
  addStockText = document.getElementById("add-stock-text");
  cancelEditBtn = document.getElementById("cancel-edit-btn");

  setupPortfolioSymbolAutocomplete();
}

/**
 * Setup autocomplete for stock symbols in portfolio modal
 */
function setupPortfolioSymbolAutocomplete() {
  const portfolioSymbolSuggestions = document.getElementById(
    "portfolio-symbol-suggestions",
  );
  if (
    typeof sharedSetupSymbolAutocomplete === "function" &&
    newStockSymbol &&
    portfolioSymbolSuggestions
  ) {
    sharedSetupSymbolAutocomplete(
      newStockSymbol,
      portfolioSymbolSuggestions,
      (symbol) => {
        newStockSymbol.value = symbol;
        newStockPrice.focus();
      },
    );
  }
}

/**
 * Open the portfolio modal
 */
function openPortfolio() {
  if (!currentUser) return;
  const userMenu = document.getElementById("user-menu");
  if (userMenu) {
    userMenu.classList.remove("show");
  }
  if (portfolioOverlay) {
    portfolioOverlay.classList.add("show");
    fetchPortfolioStocks();
    lucide.createIcons({ root: portfolioOverlay });
  }
}

/**
 * Close the portfolio modal
 */
function closePortfolio() {
  if (portfolioOverlay) {
    portfolioOverlay.classList.remove("show");
  }
}

/**
 * Fetch stocks for the current user's portfolio
 */
async function fetchPortfolioStocks() {
  if (!currentUser) return;
  try {
    const response = await fetch(`/users/${currentUser.id}/stocks`);
    const stocks = await response.json();
    renderPortfolioTable(stocks);
  } catch (error) {
    console.error("Error fetching portfolio:", error);
  }
}

/**
 * Render the portfolio stocks into the table
 */
function renderPortfolioTable(stocks) {
  if (!portfolioList) return;
  portfolioList.innerHTML = "";
  if (stocks.length === 0) {
    const emptyTemplate = /** @type {HTMLTemplateElement} */ (
      document.getElementById("portfolio-empty-template")
    );
    portfolioList.appendChild(document.importNode(emptyTemplate.content, true));
    return;
  }

  /** @type {HTMLTemplateElement} */
  const template = /** @type {HTMLTemplateElement} */ (
    document.getElementById("portfolio-row-template")
  );

  stocks.forEach((stock) => {
    const clone = document.importNode(template.content, true);
    const symbolEl = /** @type {HTMLElement} */ (
      clone.querySelector(".js-stock-symbol")
    );
    const priceEl = /** @type {HTMLElement} */ (
      clone.querySelector(".js-stock-price")
    );
    const editBtn = /** @type {HTMLElement} */ (
      clone.querySelector(".js-edit-btn")
    );
    const deleteBtn = /** @type {HTMLElement} */ (
      clone.querySelector(".js-delete-btn")
    );

    if (symbolEl) symbolEl.textContent = stock.stock_name;
    if (priceEl)
      priceEl.textContent = `${stock.avg_price.toLocaleString()} VND`;

    if (editBtn) {
      editBtn.onclick = () =>
        editPortfolioStock(stock.id, stock.stock_name, stock.avg_price);
    }
    if (deleteBtn) {
      deleteBtn.onclick = () => removePortfolioStock(stock.id);
    }

    portfolioList.appendChild(clone);
  });
  lucide.createIcons({ root: portfolioList });
}

/**
 * Set the form to edit mode for a specific stock
 */
function editPortfolioStock(id, symbol, price) {
  editingStockId = id;
  if (newStockSymbol) newStockSymbol.value = symbol;
  if (newStockPrice) newStockPrice.value = price;

  // UI feedback
  if (addStockText) addStockText.innerText = "Cập nhật";
  if (addStockIcon) addStockIcon.setAttribute("data-lucide", "check");
  if (cancelEditBtn) cancelEditBtn.classList.remove("hidden");
  if (addStockBtn) lucide.createIcons({ root: addStockBtn });
  if (newStockSymbol) newStockSymbol.focus();
}

/**
 * Cancel the current edit and reset the form
 */
function cancelEditStock() {
  editingStockId = null;
  if (newStockSymbol) newStockSymbol.value = "";
  if (newStockPrice) newStockPrice.value = "";
  if (addStockText) addStockText.innerText = "Thêm vào danh mục";
  if (addStockIcon) addStockIcon.setAttribute("data-lucide", "plus");
  if (cancelEditBtn) cancelEditBtn.classList.add("hidden");
  if (addStockBtn) lucide.createIcons({ root: addStockBtn });
}

/**
 * Add or update a stock in the portfolio
 */
async function addPortfolioStock() {
  const sym = newStockSymbol.value.trim().toUpperCase();
  const prc = parseFloat(newStockPrice.value);

  if (!sym || isNaN(prc)) {
    showAlert("Vui lòng nhập đầy đủ thông tin", { type: "warning" });
    return;
  }

  try {
    const url = editingStockId
      ? `/stocks/${editingStockId}`
      : `/users/${currentUser.id}/stocks`;
    const method = editingStockId ? "PUT" : "POST";

    const response = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stock_name: sym, avg_price: prc }),
    });

    if (response.ok) {
      cancelEditStock();
      fetchPortfolioStocks();
    } else {
      showAlert(
        editingStockId ? "Lỗi khi cập nhật cổ phiếu" : "Lỗi khi thêm cổ phiếu",
        { type: "error" },
      );
    }
  } catch (error) {
    console.error("Error adding/updating stock:", error);
  }
}

/**
 * Remove a stock from the portfolio
 */
async function removePortfolioStock(stockId) {
  const confirmed = await showConfirm(
    "Bạn có chắc muốn xóa mã này khỏi danh mục?",
    {
      type: "danger",
      confirmText: "Xóa",
    },
  );
  if (!confirmed) return;

  try {
    const response = await fetch(`/stocks/${stockId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      fetchPortfolioStocks();
    } else {
      showAlert("Lỗi khi xóa cổ phiếu", { type: "error" });
    }
  } catch (error) {
    console.error("Error removing stock:", error);
  }
}

// --- XLSX Import Functionality ---

/** @type {Array<{symbol: string, avgPrice: number}>} */
let pendingImportData = [];
let importConfirmOverlay = null;

/**
 * Trigger file input for XLSX import
 */
function triggerXLSXImport() {
  const fileInput = /** @type {HTMLInputElement} */ (
    document.getElementById("xlsx-file-input")
  );
  if (fileInput) {
    fileInput.value = ""; // Reset to allow re-selecting same file
    fileInput.click();
  }
}

/**
 * Handle XLSX file selection
 * @param {Event} event
 */
function handleXLSXFileSelected(event) {
  const input = /** @type {HTMLInputElement} */ (event.target);
  const file = input.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(
        /** @type {ArrayBuffer} */ (e.target?.result),
      );
      const workbook = XLSX.read(data, { type: "array" });

      // Try to find "Portfolio" sheet or use first sheet
      let sheetName = workbook.SheetNames.find(
        (name) => name.toLowerCase() === "portfolio",
      );
      if (!sheetName) {
        sheetName = workbook.SheetNames[0];
      }

      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

      // Parse and aggregate data
      const aggregatedStocks = parseXLSXData(jsonData);

      if (aggregatedStocks.length === 0) {
        showAlert("Không tìm thấy dữ liệu hợp lệ trong file XLSX", {
          type: "warning",
        });
        return;
      }

      // Store pending data and show confirmation dialog
      pendingImportData = aggregatedStocks;
      showImportConfirmDialog(file.name, aggregatedStocks);
    } catch (error) {
      console.error("Error parsing XLSX:", error);
      showAlert("Lỗi khi đọc file XLSX. Vui lòng kiểm tra định dạng file.", {
        type: "error",
      });
    }
  };
  reader.readAsArrayBuffer(file);
}

/**
 * Parse XLSX data and aggregate stocks with weighted average
 * Expected columns: A=Symbol, E=Shares, F=Buy Price, M=Status (only "OPEN")
 * @param {Array<Array<any>>} rows
 * @returns {Array<{symbol: string, avgPrice: number}>}
 */
function parseXLSXData(rows) {
  // Map to accumulate: symbol -> { totalValue, totalShares }
  /** @type {Map<string, {totalValue: number, totalShares: number}>} */
  const stockMap = new Map();

  // Skip header row (index 0), start from row 1
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (!row || row.length === 0) continue;

    // Column indices: A=0, E=4, F=5, M=12
    const symbol = String(row[0] || "")
      .trim()
      .toUpperCase();
    const existingSymbol = !!symbolsMap[symbol];
    const shares = parseFloat(row[4]) || 0;
    const buyPrice = parseFloat(row[5]) || 0;
    const status = String(row[12] || "")
      .trim()
      .toUpperCase();

    // Skip if not OPEN or invalid data
    if (
      status !== "OPEN" ||
      !symbol ||
      !existingSymbol ||
      shares <= 0 ||
      buyPrice <= 0
    ) {
      continue;
    }

    // Aggregate
    const existing = stockMap.get(symbol);
    if (existing) {
      existing.totalValue += buyPrice * shares;
      existing.totalShares += shares;
    } else {
      stockMap.set(symbol, {
        totalValue: buyPrice * shares,
        totalShares: shares,
      });
    }
  }

  // Calculate weighted average for each symbol
  /** @type {Array<{symbol: string, avgPrice: number}>} */
  const result = [];
  stockMap.forEach((value, symbol) => {
    const avgPrice = value.totalValue / value.totalShares;
    result.push({ symbol, avgPrice: Math.round(avgPrice) });
  });

  return result;
}

/**
 * Show the import confirmation dialog
 * @param {string} fileName
 * @param {Array<{symbol: string, avgPrice: number}>} stocks
 */
function showImportConfirmDialog(fileName, stocks) {
  importConfirmOverlay = document.getElementById("import-confirm-overlay");
  const fileNameEl = document.getElementById("import-file-name");
  const stockCountEl = document.getElementById("import-stock-count");

  if (fileNameEl) fileNameEl.textContent = fileName;
  if (stockCountEl)
    stockCountEl.innerHTML = `Tìm thấy <strong>${
      stocks.length
    }</strong> mã cổ phiếu: <i>${[
      ...new Set(stocks.map((stock) => stock.symbol)),
    ].join(", ")}</i>`;

  if (importConfirmOverlay) {
    importConfirmOverlay.classList.add("show");
    lucide.createIcons({ root: importConfirmOverlay });
  }
}

/**
 * Cancel the import and close dialog
 */
function cancelImport() {
  pendingImportData = [];
  if (importConfirmOverlay) {
    importConfirmOverlay.classList.remove("show");
  }
}

/**
 * Confirm import with specified mode
 * @param {'append' | 'replace'} mode
 */
async function confirmImport(mode) {
  if (!currentUser || pendingImportData.length === 0) {
    cancelImport();
    return;
  }

  // Close dialog first
  if (importConfirmOverlay) {
    importConfirmOverlay.classList.remove("show");
  }

  try {
    // Get existing stocks to check for duplicates
    const existingResponse = await fetch(`/users/${currentUser.id}/stocks`);
    const existingStocks = await existingResponse.json();

    // Create a map of existing stocks: symbol -> [ids]
    const existingMap = {};
    existingStocks.forEach((stock) => {
      existingMap[stock.stock_name.toUpperCase()] =
        existingMap[stock.stock_name.toUpperCase()] || [];
      existingMap[stock.stock_name.toUpperCase()].push(stock.id);
    });

    let successCount = 0;
    let errorCount = 0;

    for (const stock of pendingImportData) {
      const existing = existingMap[stock.symbol];

      // Add new stock
      const response = await fetch(`/users/${currentUser.id}/stocks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stock_name: stock.symbol,
          avg_price: stock.avgPrice,
        }),
      });
      if (response.ok) successCount++;
      else errorCount++;

      // Remove old portfolio stocks if mode is "replace" and there are old records
      if (existing && existing.length > 0 && mode === "replace") {
        for (const id of existing) {
          await fetch(`/stocks/${id}`, {
            method: "DELETE",
          });
        }
      }
    }

    // Clear pending data
    pendingImportData = [];

    // Refresh portfolio table
    fetchPortfolioStocks();

    // Show result
    showAlert(
      errorCount > 0
        ? `Cập nhật hoàn tất: <strong>${successCount}</strong> thành công, <strong>${errorCount}</strong> lỗi`
        : `Cập nhật hoàn tất: <strong>${successCount}</strong> thành công`,
      {
        type: errorCount > 0 ? "warning" : "success",
      },
    );
  } catch (error) {
    console.error("Error importing stocks:", error);
    showAlert("Lỗi khi cập nhật dữ liệu", { type: "error" });
    pendingImportData = [];
  }
}

// Initialize on DOM content loaded (if scripts are loaded after DOM)
// Or call initPortfolio() manually from index.html
document.addEventListener("DOMContentLoaded", () => {
  initPortfolio();
});

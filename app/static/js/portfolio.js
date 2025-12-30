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
    alert("Vui lòng nhập đầy đủ thông tin");
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
      alert(
        editingStockId ? "Lỗi khi cập nhật cổ phiếu" : "Lỗi khi thêm cổ phiếu",
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
  if (!confirm("Bạn có chắc muốn xóa mã này khỏi danh mục?")) return;

  try {
    const response = await fetch(`/stocks/${stockId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      fetchPortfolioStocks();
    } else {
      alert("Lỗi khi xóa cổ phiếu");
    }
  } catch (error) {
    console.error("Error removing stock:", error);
  }
}

// Initialize on DOM content loaded (if scripts are loaded after DOM)
// Or call initPortfolio() manually from index.html
document.addEventListener("DOMContentLoaded", () => {
  initPortfolio();
});

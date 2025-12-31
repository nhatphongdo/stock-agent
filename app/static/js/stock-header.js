/**
 * Stock Header Module
 * Handles the stock header display and link updates when a stock is selected.
 */

/**
 * Updates the stock header with the given stock information.
 * @param {string} symbol - The stock symbol.
 * @param {string} companyName - The company name.
 * @param {string} exchange - The stock exchange.
 */
function updateStockHeader(symbol, companyName, exchange) {
  const stockHeader = document.getElementById("stock-header");
  if (!stockHeader) return;

  stockHeader.classList.remove("hidden");
  document.getElementById("stock-header-symbol").textContent = symbol;
  document.getElementById("stock-header-name").textContent = companyName;

  // Update header links with correct exchange
  document.getElementById("link-tradingview").href =
    `https://www.tradingview.com/chart/?symbol=${exchange}:${symbol}`;
  // Use Investing.com equities search for Vietnamese stocks
  document.getElementById("link-investing").href =
    `https://vn.investing.com/search?q=${symbol}`;

  lucide.createIcons({ root: stockHeader });
}

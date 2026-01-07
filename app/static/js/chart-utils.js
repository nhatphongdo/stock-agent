/**
 * Chart Utilities - Shared tooltip and chart helper functions
 */

// Common line series options - reduces repetition
const LINE_SERIES_DEFAULTS = {
  lineWidth: 1,
  priceLineVisible: false,
  lastValueVisible: false,
};

// ============================================================================
// INDICATOR RENDERERS
// These renderers work with pre-calculated data from the backend /indicators API
// ============================================================================

/**
 * Render an indicator from API data
 * @param {string} indicatorKey - Indicator key from API
 * @param {Object} apiData - Pre-calculated data from /indicators API
 * @param {Object} ctx - Context with addLineSeries, indicatorValues, candleSeries
 * @returns {Object[]|null}
 */
function renderIndicatorFromAPI(indicatorKey, apiData, ctx) {
  if (!apiData || apiData.error) return null;

  if (apiData.series) {
    const seriesList = [];
    const seriesKeys = Object.keys(apiData.series);
    const priceLines = apiData.priceLines || {};
    const isDark = document.documentElement.classList.contains("dark");
    const colors = (apiData.colors || {})[isDark ? "dark" : "light"];
    const lineStyles = apiData.lineStyles || {};

    ctx.indicatorConfigs[indicatorKey] = {
      colors: apiData.colors,
      lineStyles,
      pane: apiData.pane,
      label: apiData.label,
      valueFormat: apiData.valueFormat,
    };

    let series = null;
    for (const key of seriesKeys) {
      const values = apiData.series[key];
      if (!priceLines[key]) {
        series = ctx.addLineSeries(
          values,
          {
            ...LINE_SERIES_DEFAULTS,
            color: colors[key],
            lineStyle: lineStyles[key],
          },
          apiData.pane,
        );
        seriesList.push({ type: "series", series });

        // Store value for tooltip
        values.forEach(({ time, value }) => {
          ctx.indicatorValues[time] = ctx.indicatorValues[time] || {};
          ctx.indicatorValues[time][indicatorKey] =
            ctx.indicatorValues[time][indicatorKey] || {};
          ctx.indicatorValues[time][indicatorKey][key] = value;
        });
      } else if (typeof values === "number" && !isNaN(values)) {
        series = ctx.candleSeries.createPriceLine({
          ...LINE_SERIES_DEFAULTS,
          price: values,
          color: colors[key],
          axisLabelVisible: true,
          title: priceLines[key],
          pane: apiData.pane,
        });
        seriesList.push({ type: "priceLines", series });
      }
    }

    return seriesList;
  }

  return null;
}

/**
 * Fetch indicators from backend API
 * @param {string} symbol - Stock symbol
 * @param {string} start - Start date (YYYY-MM-DD)
 * @param {string} end - End date (YYYY-MM-DD)
 * @param {string} interval - Data interval (1D, 1H, etc.)
 * @param {string[]} indicators - List of indicator keys to fetch
 * @returns {Promise<Object>} - API response with indicator data
 */
async function fetchIndicatorsFromAPI(
  symbol,
  start,
  end,
  interval,
  indicators,
) {
  try {
    const response = await fetch(
      `/indicators/${symbol}?start=${start}&end=${end}&interval=${interval}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ indicators, series: true }),
      },
    );
    if (!response.ok) {
      console.warn("Failed to fetch indicators:", response.status);
      return null;
    }
    return await response.json();
  } catch (err) {
    console.error("Error fetching indicators:", err);
    return null;
  }
}

/**
 * Fetch available indicators from backend API
 * @returns {Promise<Object>} - API response with indicators list
 */
async function fetchAvailableIndicators() {
  try {
    const response = await fetch("/indicators/available");
    if (!response.ok) {
      console.warn("Failed to fetch available indicators:", response.status);
      return null;
    }
    return await response.json();
  } catch (err) {
    console.error("Error fetching available indicators:", err);
    return null;
  }
}

/**
 * Generate HTML for indicator dropdown from API data
 * @param {Array} indicators - List of indicator objects from API
 * @param {string} prefix - ID prefix for checkboxes (e.g. "analysis" or "chart")
 * @returns {string} - HTML string for the dropdown content
 */
function generateIndicatorDropdownHTML(indicators, prefix = "") {
  if (!indicators || !indicators.length) return "";

  // Get categories from indicators
  const categories = Array.from(
    new Set(
      indicators.sort((a, b) => a.order - b.order).map((ind) => ind.category),
    ),
  );

  // Group by category
  const groups = {};
  indicators.forEach((ind) => {
    const cat = ind.category;
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(ind);
  });

  const isDark = document.documentElement.classList.contains("dark");
  const idPrefix = prefix ? `${prefix}-` : "";

  // Generate only the indicator list content (search box is in HTML template)
  let html = "";

  categories.forEach((catKey) => {
    if (!groups[catKey]) return;

    // Sort indicators in group by "order"
    const groupIndicators = groups[catKey].sort((a, b) => a.order - b.order);

    html += `<div class="indicator-category mb-3" data-category="${catKey}">
      <div class="indicator-category-header text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2 px-1">
        ${catKey}
      </div>
      <div class="space-y-1">`;

    groupIndicators.forEach((ind) => {
      const checkId = `${idPrefix}indicator-${ind.key}`;
      // Fallback styling
      let color = "#3b82f6";
      if (ind.colors) {
        // get first color
        color =
          Object.values(ind.colors[isDark ? "dark" : "light"] ?? {})[0] ||
          color;
      }

      // Include key, label, and description in searchable text
      const searchText = `${ind.key} ${ind.label} ${
        ind.description || ""
      }`.toLowerCase();

      html += `
        <label class="indicator-item flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer group" data-search="${searchText}">
          <input type="checkbox" id="${checkId}" data-key="${ind.key}" class="w-4 h-4 rounded border-slate-300 accent-blue-500 indicator-checkbox" />
          <span class="w-2 h-2 rounded-full" style="background-color: ${color}"></span>
          <span class="text-xs font-medium text-slate-700 dark:text-slate-300">${ind.label}</span>
          <span class="text-[10px] text-slate-400 ml-auto">${ind.description}</span>
        </label>`;
    });

    html += `</div></div>`;
  });

  return html;
}

/**
 * Create a tooltip element for chart
 * @param {HTMLElement} targetContainer - Container to append tooltip to
 * @returns {HTMLDivElement} - Tooltip element
 */
function createChartTooltip(targetContainer) {
  const tooltip = document.createElement("div");
  tooltip.style.cssText = `
    position: absolute;
    z-index: 100;
    font-size: 12px;
    font-family: sans-serif;
    line-height: 1.5;
    padding: 10px 14px;
    border-radius: 8px;
    pointer-events: none;
    display: none;
    white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    backdrop-filter: blur(8px);
  `;
  targetContainer.style.position = "relative";
  targetContainer.appendChild(tooltip);
  return tooltip;
}

/**
 * Apply theme styles to tooltip
 * @param {HTMLDivElement} tooltip - Tooltip element
 */
function applyTooltipTheme(tooltip) {
  const isDark = document.documentElement.classList.contains("dark");
  if (isDark) {
    tooltip.style.background = "rgba(30, 41, 59, 0.95)";
    tooltip.style.color = "#e2e8f0";
    tooltip.style.border = "1px solid rgba(148, 163, 184, 0.2)";
  } else {
    tooltip.style.background = "rgba(255, 255, 255, 0.95)";
    tooltip.style.color = "#1e293b";
    tooltip.style.border = "1px solid rgba(100, 116, 139, 0.2)";
  }
}

/**
 * Update tooltip position to follow crosshair
 * @param {HTMLDivElement} tooltip - Tooltip element
 * @param {HTMLElement} container - Container element
 * @param {Object} param - Crosshair param with point
 */
function updateTooltipPosition(tooltip, container, param) {
  if (!param.point) return;

  const containerRect = container.getBoundingClientRect();
  const tooltipWidth = tooltip.offsetWidth || 200;
  const tooltipHeight = tooltip.offsetHeight || 100;

  let left = param.point.x + 15;
  let top = param.point.y + 15;

  // Keep tooltip within container bounds
  if (left + tooltipWidth > containerRect.width) {
    left = param.point.x - tooltipWidth - 15;
  }
  if (top + tooltipHeight > containerRect.height) {
    top = param.point.y - tooltipHeight - 15;
  }
  if (left < 0) left = 10;
  if (top < 0) top = 10;

  tooltip.style.left = left + "px";
  tooltip.style.top = top + "px";
}

/**
 * Render indicator values for chart on specific pane tooltip
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {Object} configs - Indicator config to use
 * @param {number | string} time - Unix timestamp
 * @param {number} pane - Pane number
 * @returns {string} - HTML string for indicator values
 */
function renderPaneIndicatorsTooltip(indicatorValues, configs, time, pane) {
  const values = indicatorValues[time];
  if (!values) return "";

  const indicatorKeys = Object.keys(values).filter(
    (indicatorKey) => (configs[indicatorKey] || {}).pane === pane,
  );
  if (indicatorKeys.length === 0) return "";

  const isDark = document.documentElement.classList.contains("dark");
  let html =
    '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';

  for (const indicatorKey of indicatorKeys) {
    const indicatorConfig = configs[indicatorKey] || {};
    const color = indicatorConfig.colors || {};
    const fields = Object.keys(values[indicatorKey]);
    for (const field of fields) {
      let value = values[indicatorKey][field];
      switch (indicatorConfig.valueFormat) {
        case "price":
          value = formatPrice(values[indicatorKey][field]);
          break;
        default:
          value = formatNumber(values[indicatorKey][field]);
          break;
      }
      html += `<div><span style="color: ${
        isDark ? color.dark[field] : color.light[field]
      };">${indicatorConfig.label}${
        fields.length > 1 ? ` (${field})` : ""
      }:</span> <strong>${value}</strong></div>`;
    }
  }

  html += "</div>";
  return html;
}

/**
 * Render all indicator values for tooltip (both price and volume)
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {Object} configs - Indicator config to use
 * @param {number | string} time - Unix timestamp
 * @returns {string} - HTML string for indicator values
 */
function renderTooltipIndicators(indicatorValues, configs, time) {
  let html = renderPaneIndicatorsTooltip(indicatorValues, configs, time, 0);
  html += renderPaneIndicatorsTooltip(indicatorValues, configs, time, 1);
  return html;
}

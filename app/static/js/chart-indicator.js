/**
 * Chart Indicator Module - Shared indicator management for charts
 * Handles indicator loading, rendering, and clearing for both main and analysis charts
 */

// Common line series options - reduces repetition
const LINE_SERIES_DEFAULTS = {
  lineWidth: 1,
  priceLineVisible: false,
  lastValueVisible: false,
};

// Track in-flight requests per panel to enable cancellation
const indicatorAbortControllers = new Map();

// ============================================================================
// INDICATOR API FUNCTIONS
// ============================================================================

/**
 * Fetch indicators from backend API
 * @param {string} symbol - Stock symbol
 * @param {string} start - Start date (YYYY-MM-DD)
 * @param {string} end - End date (YYYY-MM-DD)
 * @param {string} interval - Data interval (1D, 1H, etc.)
 * @param {string[]} indicators - List of indicator keys to fetch
 * @param {AbortSignal} [signal] - Optional AbortSignal for cancellation
 * @returns {Promise<Object>} - API response with indicator data
 */
async function fetchIndicatorsFromAPI(
  symbol,
  start,
  end,
  interval,
  indicators,
  signal = null,
) {
  try {
    const fetchOptions = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ indicators, series: true }),
    };
    if (signal) {
      fetchOptions.signal = signal;
    }
    const response = await fetch(
      `/indicators/${symbol}?start=${start}&end=${end}&interval=${interval}`,
      fetchOptions,
    );
    if (!response.ok) {
      console.warn("Failed to fetch indicators:", response.status);
      return null;
    }
    return await response.json();
  } catch (err) {
    // Don't log error if request was aborted
    if (err.name === "AbortError") {
      return null;
    }
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

// ============================================================================
// INDICATOR RENDERING
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

// ============================================================================
// INDICATOR DROPDOWN UI
// ============================================================================

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

// ============================================================================
// TOOLTIP HELPERS
// ============================================================================

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

// ============================================================================
// INDICATOR MANAGEMENT (NEW BATCH PATTERN)
// ============================================================================

/**
 * Create an indicator rendering context
 * @param {Object} chart - LightweightCharts chart instance
 * @param {Object} candleSeries - Candle series instance
 * @param {Object} indicatorValues - Object to store indicator values for tooltip
 * @param {Object} indicatorConfigs - Object to store indicator configs
 * @param {Array} [indicatorSeriesArray] - Optional array to collect series for tracking
 * @returns {Object} - Rendering context
 */
function createIndicatorContext(
  chart,
  candleSeries,
  indicatorValues,
  indicatorConfigs,
  indicatorSeriesArray = null,
) {
  return {
    addLineSeries: (seriesData, options, pane = 0) => {
      const series = chart.addSeries(
        LightweightCharts.LineSeries,
        options,
        pane,
      );
      series.setData(seriesData);
      if (indicatorSeriesArray) {
        indicatorSeriesArray.push(series);
      }
      return series;
    },
    indicatorValues,
    indicatorConfigs,
    candleSeries,
  };
}

/**
 * Clear all indicators from chart
 * @param {Object} chart - LightweightCharts chart instance
 * @param {Map} seriesMap - Map of indicator ID -> series array
 * @param {Object} candleSeries - Candle series instance (for removing price lines)
 * @param {Object} indicatorValues - Object to reset
 * @param {Object} indicatorConfigs - Object to reset
 */
function clearAllIndicators(
  chart,
  seriesMap,
  candleSeries,
  indicatorValues,
  indicatorConfigs,
) {
  if (!chart) return;

  // Remove all series from map
  for (const [indicatorId, stored] of seriesMap) {
    if (!stored) continue;
    stored.forEach((item) => {
      if (item.type === "series") {
        try {
          chart.removeSeries(item.series);
        } catch (e) {
          console.warn("Failed to remove series:", e);
        }
      } else if (item.type === "priceLines" && candleSeries) {
        try {
          candleSeries.removePriceLine(item.series);
        } catch (e) {
          console.warn("Failed to remove price line:", e);
        }
      }
    });
  }

  // Clear maps and objects
  seriesMap.clear();

  // Reset indicator values and configs
  for (const key of Object.keys(indicatorValues)) {
    delete indicatorValues[key];
  }
  for (const key of Object.keys(indicatorConfigs)) {
    delete indicatorConfigs[key];
  }
}

/**
 * Get all selected indicator keys from a dropdown panel
 * @param {string} panelSelector - CSS selector for the dropdown panel
 * @returns {Array<{id: string, key: string}>} - Array of selected indicator info
 */
function getSelectedIndicators(panelSelector) {
  const checkboxes = document.querySelectorAll(
    `${panelSelector} input.indicator-checkbox:checked`,
  );
  const selected = [];
  checkboxes.forEach((c) => {
    const checkbox = /** @type {HTMLInputElement} */ (c);
    const indicatorId = checkbox.id;
    const indicatorKey = checkbox.dataset.key;
    if (indicatorKey) {
      selected.push({ id: indicatorId, key: indicatorKey });
    }
  });
  return selected;
}

/**
 * Handle indicator checkbox change - clears and redraws all indicators
 * @param {Object} options - Same options as loadAllIndicators plus clear params
 * @returns {Promise<void>}
 */
async function handleIndicatorChange(options) {
  const {
    chart,
    candleSeries,
    seriesMap,
    indicatorValues,
    indicatorConfigs,
    indicatorSeriesArray = null,
    symbol,
    start,
    end,
    interval,
    panelSelector,
  } = options;

  if (!chart || !candleSeries || !symbol) return;

  // Cancel any in-flight request for this panel
  const existingController = indicatorAbortControllers.get(panelSelector);
  if (existingController) {
    existingController.abort();
  }

  // Create new AbortController for this request
  const abortController = new AbortController();
  indicatorAbortControllers.set(panelSelector, abortController);

  // Get all selected indicators
  const selected = getSelectedIndicators(panelSelector);

  // If no indicators selected, just clear existing ones
  if (selected.length === 0) {
    clearAllIndicators(
      chart,
      seriesMap,
      candleSeries,
      indicatorValues,
      indicatorConfigs,
    );
    return;
  }

  const indicatorKeys = selected.map((s) => s.key);

  // Fetch indicators first - don't clear until we have new data
  const apiResponse = await fetchIndicatorsFromAPI(
    symbol,
    start,
    end,
    interval,
    indicatorKeys,
    abortController.signal,
  );

  // If API failed or request was aborted, keep existing indicators
  if (!apiResponse || !apiResponse.indicators) {
    // Only warn if not aborted (aborted means user clicked again quickly)
    if (!abortController.signal.aborted) {
      console.warn("Failed to fetch indicators from API, keeping existing");
    }
    return;
  }

  // Clear the controller from map since request completed successfully
  indicatorAbortControllers.delete(panelSelector);

  // API succeeded - now safe to clear existing indicators
  clearAllIndicators(
    chart,
    seriesMap,
    candleSeries,
    indicatorValues,
    indicatorConfigs,
  );

  // Create rendering context
  const ctx = createIndicatorContext(
    chart,
    candleSeries,
    indicatorValues,
    indicatorConfigs,
    indicatorSeriesArray,
  );

  // Render each indicator
  for (const { id, key } of selected) {
    const apiData = apiResponse.indicators[key];
    if (!apiData || apiData.error) {
      console.warn(`Indicator ${key} returned error:`, apiData?.error);
      continue;
    }

    const result = renderIndicatorFromAPI(key, apiData, ctx);
    if (result) {
      seriesMap.set(id, result);
    }
  }
}

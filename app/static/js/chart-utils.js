/**
 * Chart Utilities - Shared tooltip and chart helper functions
 */

/**
 * Shared Indicator Configuration with colors and labels
 * This is the single source of truth for indicator display properties
 */
const SHARED_INDICATOR_CONFIG = {
  // Moving Averages
  ma: { label: "SMA(20)", color: "#3b82f6" },
  ema: { label: "EMA(9)", color: "#f97316" },
  wma: { label: "WMA(20)", color: "#06b6d4" },
  vwap: { label: "VWAP", color: "#8b5cf6" },
  // Bands/Channels
  bb: { label: "BB", color: "#a855f7" },
  atr: { label: "ATR(14)", color: "#ec4899" },
  // Oscillators
  rsi: { label: "RSI(14)", color: "#f59e0b" },
  macd: { label: "MACD", colors: { line: "#3b82f6", signal: "#ef4444" } },
  stoch: { label: "Stoch", colors: { k: "#10b981", d: "#ef4444" } },
  williams: { label: "Will %R", color: "#06b6d4" },
  cci: { label: "CCI(20)", color: "#8b5cf6" },
  roc: { label: "ROC(10)", color: "#f97316" },
  // Trend
  adx: {
    label: "ADX(14)",
    colors: { adx: "#22c55e", plusDI: "#3b82f6", minusDI: "#ef4444" },
  },
  // Volume
  volSma: { label: "Vol SMA(20)", color: "#8b5cf6" },
  obv: { label: "OBV", color: "#06b6d4" },
  mfi: { label: "MFI(14)", color: "#f59e0b" },
  cmf: { label: "CMF(20)", color: "#ec4899" },
};

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
 * Render indicator values for price chart tooltip
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp
 * @param {Object} config - Indicator config to use (INDICATOR_CONFIG or ANALYSIS_INDICATOR_CONFIG)
 * @returns {string} - HTML string for indicator values
 */
function renderPriceIndicatorsTooltip(indicatorValues, time, config) {
  const values = indicatorValues[time];
  if (!values) return "";

  let html =
    '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';
  let count = 0;

  // Moving Averages
  if (values.ma !== undefined) {
    html += `<div><span style="color: ${
      config.ma?.color || SHARED_INDICATOR_CONFIG.ma.color
    }; opacity: 0.8;">SMA(20):</span> <strong>${formatPrice(
      values.ma,
    )}</strong></div>`;
    count++;
  }
  if (values.ema !== undefined) {
    html += `<div><span style="color: ${
      config.ema?.color || SHARED_INDICATOR_CONFIG.ema.color
    }; opacity: 0.8;">EMA(9):</span> <strong>${formatPrice(
      values.ema,
    )}</strong></div>`;
    count++;
  }
  if (values.wma !== undefined) {
    html += `<div><span style="color: ${
      config.wma?.color || SHARED_INDICATOR_CONFIG.wma.color
    }; opacity: 0.8;">WMA(20):</span> <strong>${formatPrice(
      values.wma,
    )}</strong></div>`;
    count++;
  }
  if (values.vwap !== undefined) {
    html += `<div><span style="color: ${
      config.vwap?.color || SHARED_INDICATOR_CONFIG.vwap.color
    }; opacity: 0.8;">VWAP:</span> <strong>${formatPrice(
      values.vwap,
    )}</strong></div>`;
    count++;
  }

  // Bands
  if (values.bbUpper !== undefined) {
    html += `<div><span style="color: ${
      config.bb?.color || SHARED_INDICATOR_CONFIG.bb.color
    }; opacity: 0.8;">BB Upper:</span> <strong>${formatPrice(
      values.bbUpper,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      config.bb?.color || SHARED_INDICATOR_CONFIG.bb.color
    }; opacity: 0.8;">BB Lower:</span> <strong>${formatPrice(
      values.bbLower,
    )}</strong></div>`;
    count++;
  }
  if (values.atr !== undefined) {
    html += `<div><span style="color: ${
      config.atr?.color || SHARED_INDICATOR_CONFIG.atr.color
    }; opacity: 0.8;">ATR(14):</span> <strong>${formatNumber(
      values.atr,
      2,
    )}</strong></div>`;
    count++;
  }

  // Oscillators
  if (values.rsi !== undefined) {
    html += `<div><span style="color: ${
      config.rsi?.color || SHARED_INDICATOR_CONFIG.rsi.color
    }; opacity: 0.8;">RSI(14):</span> <strong>${formatNumber(
      values.rsi,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.macdLine !== undefined) {
    const macdColors =
      config.macd?.colors || SHARED_INDICATOR_CONFIG.macd.colors;
    html += `<div><span style="color: ${
      macdColors.line
    }; opacity: 0.8;">MACD:</span> <strong>${formatNumber(
      values.macdLine,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      macdColors.signal
    }; opacity: 0.8;">Signal:</span> <strong>${formatNumber(
      values.macdSignal,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.stochK !== undefined) {
    const stochColors =
      config.stoch?.colors || SHARED_INDICATOR_CONFIG.stoch.colors;
    html += `<div><span style="color: ${
      stochColors.k
    }; opacity: 0.8;">Stoch %K:</span> <strong>${formatNumber(
      values.stochK,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      stochColors.d
    }; opacity: 0.8;">Stoch %D:</span> <strong>${formatNumber(
      values.stochD,
      2,
    )}</strong></div>`;
    count++;
  }
  // Williams %R - check both possible key names
  if (values.williamsR !== undefined || values.williams !== undefined) {
    const willVal =
      values.williamsR !== undefined ? values.williamsR : values.williams;
    html += `<div><span style="color: ${
      config.williams?.color || SHARED_INDICATOR_CONFIG.williams.color
    }; opacity: 0.8;">Will %R:</span> <strong>${formatNumber(
      willVal,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.cci !== undefined) {
    html += `<div><span style="color: ${
      config.cci?.color || SHARED_INDICATOR_CONFIG.cci.color
    }; opacity: 0.8;">CCI(20):</span> <strong>${formatNumber(
      values.cci,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.roc !== undefined) {
    html += `<div><span style="color: ${
      config.roc?.color || SHARED_INDICATOR_CONFIG.roc.color
    }; opacity: 0.8;">ROC(10):</span> <strong>${formatNumber(
      values.roc,
      2,
    )}%</strong></div>`;
    count++;
  }

  // Trend
  if (values.adx !== undefined) {
    const adxColors = config.adx?.colors || SHARED_INDICATOR_CONFIG.adx.colors;
    html += `<div><span style="color: ${
      adxColors.adx
    }; opacity: 0.8;">ADX:</span> <strong>${formatNumber(
      values.adx,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      adxColors.plusDI
    }; opacity: 0.8;">+DI:</span> <strong>${formatNumber(
      values.plusDI,
      2,
    )}</strong></div>`;
    html += `<div><span style="color: ${
      adxColors.minusDI
    }; opacity: 0.8;">-DI:</span> <strong>${formatNumber(
      values.minusDI,
      2,
    )}</strong></div>`;
    count++;
  }

  html += "</div>";
  return count > 0 ? html : "";
}

/**
 * Render volume indicator values for tooltip
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp or date string
 * @param {Object} config - Indicator config to use
 * @returns {string} - HTML string for volume indicator values
 */
function renderVolumeIndicatorsTooltip(indicatorValues, time, config) {
  const values = indicatorValues[time];
  if (!values) return "";

  let html =
    '<div style="margin-top: 6px; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 4px;">';
  let count = 0;

  if (values.volSma !== undefined) {
    html += `<div><span style="color: ${
      config.volSma?.color || SHARED_INDICATOR_CONFIG.volSma.color
    }; opacity: 0.8;">Vol SMA(20):</span> <strong>${formatNumber(
      values.volSma,
      0,
    )}</strong></div>`;
    count++;
  }
  if (values.obv !== undefined) {
    html += `<div><span style="color: ${
      config.obv?.color || SHARED_INDICATOR_CONFIG.obv.color
    }; opacity: 0.8;">OBV:</span> <strong>${formatNumber(
      values.obv,
      0,
    )}</strong></div>`;
    count++;
  }
  if (values.mfi !== undefined) {
    html += `<div><span style="color: ${
      config.mfi?.color || SHARED_INDICATOR_CONFIG.mfi.color
    }; opacity: 0.8;">MFI(14):</span> <strong>${formatNumber(
      values.mfi,
      2,
    )}</strong></div>`;
    count++;
  }
  if (values.cmf !== undefined) {
    html += `<div><span style="color: ${
      config.cmf?.color || SHARED_INDICATOR_CONFIG.cmf.color
    }; opacity: 0.8;">CMF(20):</span> <strong>${formatNumber(
      values.cmf,
      4,
    )}</strong></div>`;
    count++;
  }

  html += "</div>";
  return count > 0 ? html : "";
}

/**
 * Render all indicator values for tooltip (both price and volume)
 * @param {Object} indicatorValues - Object mapping time -> indicator values
 * @param {number | string} time - Unix timestamp
 * @param {Object} config - Indicator config to use
 * @param {boolean} isVolumeChart - Whether this is for volume chart only
 * @returns {string} - HTML string for indicator values
 */
function renderTooltipIndicators(
  indicatorValues,
  time,
  config,
  isVolumeChart = false,
) {
  if (isVolumeChart) {
    return renderVolumeIndicatorsTooltip(indicatorValues, time, config);
  }
  return renderPriceIndicatorsTooltip(indicatorValues, time, config);
}

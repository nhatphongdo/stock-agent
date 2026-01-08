/**
 * Chart Utilities - Shared tooltip and chart helper functions
 */

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

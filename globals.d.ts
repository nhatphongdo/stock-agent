// Lightweight Charts library v5.1 - https://github.com/tradingview/lightweight-charts
interface ICandleData {
  open: number;
  high: number;
  low: number;
  close: number;
  time?: number;
}

interface IVolumeData {
  value: number;
  time?: number;
  color?: string;
}

interface IPriceScaleApi {
  applyOptions: (options: unknown) => void;
  options: () => { id?: string; visible?: boolean; borderColor?: string };
  width: () => number;
}

interface ISeriesApi {
  setData: (data: unknown[]) => void;
  dataByIndex: (index: number) => unknown;
  priceLines: () => unknown[];
  priceScale: () => IPriceScaleApi;
}

interface ITimeScaleApi {
  subscribeVisibleLogicalRangeChange: (
    handler: (range: unknown) => void,
  ) => void;
  unsubscribeVisibleLogicalRangeChange: (
    handler: (range: unknown) => void,
  ) => void;
  subscribeVisibleTimeRangeChange: (handler: (range: unknown) => void) => void;
  unsubscribeVisibleTimeRangeChange: (
    handler: (range: unknown) => void,
  ) => void;
  setVisibleLogicalRange: (range: unknown) => void;
  fitContent: () => void;
  getVisibleRange: () => unknown;
  getVisibleLogicalRange: () => unknown;
  scrollToPosition: (position: number, animated?: boolean) => void;
  scrollToRealTime: () => void;
}

interface ICrosshairMoveParam {
  time?: number | string;
  point?: { x: number; y: number };
  logical?: number;
  seriesData: Map<ISeriesApi, unknown>;
}

interface IPaneApi {
  setHeight: (height: number) => void;
}

interface IChartApi {
  // v5.1 unified series API
  addSeries: (
    seriesType: unknown,
    options?: unknown,
    paneIndex?: number,
  ) => ISeriesApi;
  panes: () => IPaneApi[];
  timeScale: () => ITimeScaleApi;
  subscribeCrosshairMove: (
    handler: (param: ICrosshairMoveParam) => void,
  ) => void;
  unsubscribeCrosshairMove: (
    handler: (param: ICrosshairMoveParam) => void,
  ) => void;
  setCrosshairPosition: (
    price: unknown,
    time: unknown,
    series: ISeriesApi,
  ) => void;
  clearCrosshairPosition: () => void;
  remove: () => void;
  resize: (width: number, height: number, forceRepaint?: boolean) => void;
  applyOptions: (options: unknown) => void;
  options: () => unknown;
}

declare const LightweightCharts: {
  createChart: (container: HTMLElement, options?: unknown) => IChartApi;
  createSeriesMarkers: (
    series: ISeriesApi,
    markers: unknown[],
    options?: unknown,
  ) => void;
  CrosshairMode: {
    Normal: number;
    Magnet: number;
    Hidden: number;
  };
  LineStyle: {
    Solid: number;
    Dotted: number;
    Dashed: number;
    LargeDashed: number;
    SparseDotted: number;
  };
  PriceScaleMode: {
    Normal: number;
    Logarithmic: number;
    Percentage: number;
    IndexedTo100: number;
  };
  // Series types for addSeries method (v5.1)
  CandlestickSeries: unknown;
  LineSeries: unknown;
  AreaSeries: unknown;
  HistogramSeries: unknown;
  BarSeries: unknown;
  BaselineSeries: unknown;
};

// Marked library - Markdown parser
declare const marked: {
  parse: (markdown: string, options?: unknown) => string;
  setOptions: (options: unknown) => void;
};

// Lucide icons library
declare const lucide: {
  createIcons: (options?: {
    icons?: Record<string, unknown>;
    attrs?: Record<string, string>;
    root?: Element;
  }) => void;
};

declare let selectedStock: string;
declare function selectStock(symbol: string): void;

// SheetJS library - XLSX parser
declare const XLSX: {
  read: (
    data: ArrayBuffer | Uint8Array | string,
    options?: { type?: string },
  ) => {
    SheetNames: string[];
    Sheets: Record<string, unknown>;
  };
  utils: {
    sheet_to_json: <T = unknown[]>(
      worksheet: unknown,
      options?: { header?: number | string[] | "A" },
    ) => T[];
  };
};

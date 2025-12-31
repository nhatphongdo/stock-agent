// Lightweight Charts library - https://github.com/tradingview/lightweight-charts
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

interface ISeriesApi {
  setData: (data: unknown[]) => void;
  dataByIndex: (index: number) => unknown;
}

interface ITimeScaleApi {
  subscribeVisibleLogicalRangeChange: (
    handler: (range: unknown) => void,
  ) => void;
  setVisibleLogicalRange: (range: unknown) => void;
  fitContent: () => void;
}

interface ICrosshairMoveParam {
  time?: number;
  point?: { x: number; y: number };
  logical?: number;
  seriesData: Map<ISeriesApi, unknown>;
}

interface IChartApi {
  addCandlestickSeries: (options?: unknown) => ISeriesApi;
  addHistogramSeries: (options?: unknown) => ISeriesApi;
  addLineSeries: (options?: unknown) => ISeriesApi;
  timeScale: () => ITimeScaleApi;
  subscribeCrosshairMove: (
    handler: (param: ICrosshairMoveParam) => void,
  ) => void;
  setCrosshairPosition: (
    price: unknown,
    time: unknown,
    series: ISeriesApi,
  ) => void;
  remove: () => void;
}

declare const LightweightCharts: {
  createChart: (container: HTMLElement, options?: unknown) => IChartApi;
  CrosshairMode: {
    Normal: number;
    Magnet: number;
  };
  LineStyle: {
    Solid: number;
    Dotted: number;
    Dashed: number;
    LargeDashed: number;
    SparseDotted: number;
  };
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

declare function selectStock(symbol: string): void;

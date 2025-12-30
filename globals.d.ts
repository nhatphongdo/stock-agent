declare var currentUser: any;
declare var users: any[];
declare var symbolsMap: { [key: string]: any };
declare var lucide: any;
declare var fetchUsers: () => Promise<void>;
declare var selectUser: (user: any) => void;
declare var marked: {
  parse: (text: string) => string;
};
declare function selectStock(symbol: string): void;
declare function initAdvancedChart(symbol: string): void;
declare var currentChartSymbol: any;

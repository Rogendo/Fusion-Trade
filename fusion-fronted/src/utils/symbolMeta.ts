export interface SymbolMeta {
  label: string
  decimals: number
  group: string
  tvSymbol: string
}

export interface ModelCoverage {
  lstm: string[]     // available timeframes
  patchtst: string[] // available timeframes
}

// ── Symbol metadata ──────────────────────────────────────────────────────────
// Yahoo Finance symbol → display info
// Sourced from HuggingFace: Rogendo/forex-lstm-models & Rogendo/forex-patchtst-models

const META: Record<string, SymbolMeta> = {
  // FX Majors
  'EURUSD=X': { label: 'EUR/USD', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:EURUSD' },
  'GBPUSD=X': { label: 'GBP/USD', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:GBPUSD' },
  'USDJPY=X': { label: 'USD/JPY', decimals: 3, group: 'FX Majors',    tvSymbol: 'FX:USDJPY' },
  'AUDUSD=X': { label: 'AUD/USD', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:AUDUSD' },
  'USDCHF=X': { label: 'USD/CHF', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:USDCHF' },
  'NZDUSD=X': { label: 'NZD/USD', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:NZDUSD' },
  'USDCAD=X': { label: 'USD/CAD', decimals: 5, group: 'FX Majors',    tvSymbol: 'FX:USDCAD' },
  // EUR Crosses
  'EURJPY=X': { label: 'EUR/JPY', decimals: 3, group: 'EUR Crosses',  tvSymbol: 'FX:EURJPY' },
  'EURAUD=X': { label: 'EUR/AUD', decimals: 5, group: 'EUR Crosses',  tvSymbol: 'FX:EURAUD' },
  'EURCAD=X': { label: 'EUR/CAD', decimals: 5, group: 'EUR Crosses',  tvSymbol: 'FX:EURCAD' },
  'EURGBP=X': { label: 'EUR/GBP', decimals: 5, group: 'EUR Crosses',  tvSymbol: 'FX:EURGBP' },
  // GBP Crosses
  'GBPJPY=X': { label: 'GBP/JPY', decimals: 3, group: 'GBP Crosses',  tvSymbol: 'FX:GBPJPY' },
  'GBPEUR=X': { label: 'GBP/EUR', decimals: 5, group: 'GBP Crosses',  tvSymbol: 'FX:GBPEUR' },
  // AUD Crosses
  'AUDJPY=X': { label: 'AUD/JPY', decimals: 3, group: 'AUD Crosses',  tvSymbol: 'FX:AUDJPY' },
  'AUDNZD=X': { label: 'AUD/NZD', decimals: 5, group: 'AUD Crosses',  tvSymbol: 'FX:AUDNZD' },
  // Exotic
  'USDCNY=X': { label: 'USD/CNY', decimals: 4, group: 'Exotic',       tvSymbol: 'FX:USDCNH' },
  // Commodities
  'GC=F':     { label: 'Gold',    decimals: 2, group: 'Commodities',  tvSymbol: 'TVC:GOLD' },
  // Crypto
  'BTC-USD':  { label: 'BTC/USD', decimals: 0, group: 'Crypto',       tvSymbol: 'BINANCE:BTCUSDT' },
}

// ── Trained model coverage ───────────────────────────────────────────────────
// Verified directly from HuggingFace repos (April 2026):
//
// LSTM → Rogendo/forex-lstm-models
//   File pattern: {SYMBOL}_X_{TF}_model.h5  (e.g. EURUSD_X_1h_model.h5)
//   GC=F file pattern: GC_F_{TF}_model.h5
//   BTC-USD file pattern: BTC-USD_{TF}_model.h5
//   All 18 symbols trained on: 5m, 15m, 30m, 1h, 4h
//
// PatchTST → Rogendo/forex-patchtst-models
//   EURUSD=X: 15m, 1h
//   GC=F: 5m, 15m, 30m, 1h, 4h

const LSTM_TFS = ['5m', '15m', '30m', '1h', '4h']

export const MODEL_COVERAGE: Record<string, ModelCoverage> = {
  // FX Majors — LSTM all 5 TFs
  'EURUSD=X': { lstm: LSTM_TFS, patchtst: ['15m', '1h'] },
  'GBPUSD=X': { lstm: LSTM_TFS, patchtst: [] },
  'USDJPY=X': { lstm: LSTM_TFS, patchtst: [] },
  'AUDUSD=X': { lstm: LSTM_TFS, patchtst: [] },
  'USDCHF=X': { lstm: LSTM_TFS, patchtst: [] },
  'NZDUSD=X': { lstm: LSTM_TFS, patchtst: [] },
  'USDCAD=X': { lstm: LSTM_TFS, patchtst: [] },
  // EUR Crosses
  'EURJPY=X': { lstm: LSTM_TFS, patchtst: [] },
  'EURAUD=X': { lstm: LSTM_TFS, patchtst: [] },
  'EURCAD=X': { lstm: LSTM_TFS, patchtst: [] },
  'EURGBP=X': { lstm: LSTM_TFS, patchtst: [] },
  // GBP Crosses
  'GBPJPY=X': { lstm: LSTM_TFS, patchtst: [] },
  'GBPEUR=X': { lstm: LSTM_TFS, patchtst: [] },
  // AUD Crosses
  'AUDJPY=X': { lstm: LSTM_TFS, patchtst: [] },
  'AUDNZD=X': { lstm: LSTM_TFS, patchtst: [] },
  // Exotic
  'USDCNY=X': { lstm: LSTM_TFS, patchtst: [] },
  // Commodities — LSTM + PatchTST
  'GC=F':     { lstm: LSTM_TFS, patchtst: ['5m', '15m', '30m', '1h', '4h'] },
  // Crypto
  'BTC-USD':  { lstm: LSTM_TFS, patchtst: [] },
}

export const TRAINED_SYMBOLS = Object.keys(MODEL_COVERAGE)

// TopBar quick-access tabs — majors + gold + BTC (most traded)
export const QUICK_SYMBOLS = [
  'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X',
  'USDCHF=X', 'NZDUSD=X', 'USDCAD=X', 'GC=F', 'BTC-USD',
]

// Sidebar groups — all trained symbols, organised by instrument family
export const SYMBOL_GROUPS = [
  {
    group: 'FX Majors',
    symbols: ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCHF=X', 'NZDUSD=X', 'USDCAD=X'],
  },
  {
    group: 'EUR Crosses',
    symbols: ['EURJPY=X', 'EURAUD=X', 'EURCAD=X', 'EURGBP=X'],
  },
  {
    group: 'GBP Crosses',
    symbols: ['GBPJPY=X', 'GBPEUR=X'],
  },
  {
    group: 'AUD Crosses',
    symbols: ['AUDJPY=X', 'AUDNZD=X'],
  },
  {
    group: 'Exotic',
    symbols: ['USDCNY=X'],
  },
  {
    group: 'Commodities',
    symbols: ['GC=F'],
  },
  {
    group: 'Crypto',
    symbols: ['BTC-USD'],
  },
]

export function getSymbolMeta(symbol: string): SymbolMeta {
  return META[symbol] ?? { label: symbol, decimals: 5, group: 'Other', tvSymbol: `FX:${symbol.replace('=X', '')}` }
}

export function getLabel(symbol: string): string {
  return getSymbolMeta(symbol).label
}

export function getTVSymbol(symbol: string): string {
  return getSymbolMeta(symbol).tvSymbol
}

export function getCoverage(symbol: string): ModelCoverage {
  return MODEL_COVERAGE[symbol] ?? { lstm: [], patchtst: [] }
}

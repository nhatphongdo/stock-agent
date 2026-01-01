// ============================================================================
// MOVING AVERAGES
// ============================================================================

// Calculate Simple Moving Average (SMA)
function calculateMA(data, period) {
  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    const slice = arr.slice(i - period + 1, i + 1);
    return slice.reduce((sum, d) => sum + d.c, 0) / period;
  });
}

// Alias for SMA
function calculateSMA(data, period) {
  return calculateMA(data, period);
}

// Calculate Exponential Moving Average (EMA)
function calculateEMA(data, period) {
  const k = 2 / (period + 1);
  const ema = [data[0].c];
  for (let i = 1; i < data.length; i++) {
    ema.push(data[i].c * k + ema[i - 1] * (1 - k));
  }
  // Set first (period-1) values to null for consistency
  return ema.map((v, i) => (i < period - 1 ? null : v));
}

// Calculate Weighted Moving Average (WMA)
function calculateWMA(data, period) {
  const weights = Array.from({ length: period }, (_, i) => i + 1);
  const weightSum = weights.reduce((a, b) => a + b, 0);

  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += arr[i - period + 1 + j].c * weights[j];
    }
    return sum / weightSum;
  });
}

// ============================================================================
// PRICE INDICATORS (from TradingView)
// ============================================================================

// Calculate Median Price: (High + Low) / 2
function calculateMedianPrice(data) {
  return data.map((d) => (d.h + d.l) / 2);
}

// Calculate Average Price: (Open + High + Low + Close) / 4
function calculateAveragePrice(data) {
  return data.map((d) => (d.o + d.h + d.l + d.c) / 4);
}

// Calculate Typical Price: (High + Low + Close) / 3
function calculateTypicalPrice(data) {
  return data.map((d) => (d.h + d.l + d.c) / 3);
}

// Calculate Weighted Close: (Close * weight + High + Low) / (2 + weight)
function calculateWeightedClose(data, weight = 2) {
  return data.map((d) => (d.c * weight + d.h + d.l) / (2 + weight));
}

// Calculate Percent Change
function calculatePercentChange(data) {
  return data.map((d, i) => {
    if (i === 0) return null;
    const prev = data[i - 1].c;
    return prev === 0 ? null : ((d.c - prev) * 100) / prev;
  });
}

// Calculate Momentum: Current Price - Price n periods ago
function calculateMomentum(data, period = 10) {
  return data.map((d, i) => {
    if (i < period) return null;
    return d.c - data[i - period].c;
  });
}

// ============================================================================
// VOLATILITY INDICATORS
// ============================================================================

// Calculate Bollinger Bands
function calculateBB(data, period = 20, stdDev = 2) {
  const ma = calculateMA(data, period);
  return ma.map((mean, i) => {
    if (mean === null) return { upper: null, middle: null, lower: null };
    const slice = data.slice(Math.max(0, i - period + 1), i + 1);
    const variance =
      slice.reduce((sum, d) => sum + Math.pow(d.c - mean, 2), 0) / period;
    const std = Math.sqrt(variance);
    return {
      upper: mean + stdDev * std,
      middle: mean,
      lower: mean - stdDev * std,
    };
  });
}

// Calculate True Range
function calculateTrueRange(data) {
  return data.map((d, i) => {
    if (i === 0) return d.h - d.l;
    const prevClose = data[i - 1].c;
    return Math.max(
      d.h - d.l,
      Math.abs(d.h - prevClose),
      Math.abs(d.l - prevClose),
    );
  });
}

// Calculate Average True Range (ATR) - using Wilder's smoothing
function calculateATR(data, period = 14) {
  const tr = calculateTrueRange(data);
  const atr = new Array(data.length).fill(null);

  if (data.length < period) return atr;

  // First ATR is simple average of TR
  atr[period - 1] = tr.slice(0, period).reduce((a, b) => a + b, 0) / period;

  // Wilder's smoothing for subsequent values
  for (let i = period; i < data.length; i++) {
    atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period;
  }

  return atr;
}

// ============================================================================
// MOMENTUM OSCILLATORS
// ============================================================================

// Calculate RSI (Relative Strength Index) - Wilder's Smoothing
function calculateRSI(data, period = 14) {
  const changes = data.map((d, i) => (i === 0 ? 0 : d.c - data[i - 1].c));
  const gains = changes.map((c) => (c > 0 ? c : 0));
  const losses = changes.map((c) => (c < 0 ? -c : 0));

  let avgGain = gains.slice(1, period + 1).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(1, period + 1).reduce((a, b) => a + b, 0) / period;

  return data.map((_, i) => {
    if (i < period) return null;
    if (i === period) {
      return avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    return avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  });
}

// Calculate MACD (Moving Average Convergence Divergence)
function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  const emaFast = calculateEMAValues(
    data.map((d) => d.c),
    fast,
  );
  const emaSlow = calculateEMAValues(
    data.map((d) => d.c),
    slow,
  );
  const macdLine = emaFast.map((f, i) =>
    i < slow - 1 || f === null || emaSlow[i] === null ? null : f - emaSlow[i],
  );

  // Calculate signal line (EMA of MACD line)
  const validMacd = macdLine.filter((v) => v !== null);
  const k = 2 / (signal + 1);
  const signalLine = [];
  let signalEma = validMacd[0];

  let validIndex = 0;
  for (let i = 0; i < macdLine.length; i++) {
    if (macdLine[i] === null) {
      signalLine.push(null);
    } else {
      if (validIndex === 0) {
        signalLine.push(signalEma);
      } else if (validIndex < signal) {
        signalEma = (macdLine[i] + signalEma * validIndex) / (validIndex + 1);
        signalLine.push(null);
      } else {
        signalEma = macdLine[i] * k + signalEma * (1 - k);
        signalLine.push(signalEma);
      }
      validIndex++;
    }
  }

  const histogram = macdLine.map((m, i) =>
    m === null || signalLine[i] === null ? null : m - signalLine[i],
  );

  return { macdLine, signalLine, histogram };
}

// Helper: Calculate EMA on raw values array
function calculateEMAValues(values, period) {
  const k = 2 / (period + 1);
  const ema = [values[0]];
  for (let i = 1; i < values.length; i++) {
    ema.push(values[i] * k + ema[i - 1] * (1 - k));
  }
  return ema.map((v, i) => (i < period - 1 ? null : v));
}

// Calculate Stochastic Oscillator (%K and %D)
function calculateStochastic(data, kPeriod = 14, dPeriod = 3, smooth = 3) {
  const stochK = [];
  const stochD = [];

  // Calculate raw %K
  for (let i = 0; i < data.length; i++) {
    if (i < kPeriod - 1) {
      stochK.push(null);
      continue;
    }
    const slice = data.slice(i - kPeriod + 1, i + 1);
    const highestHigh = Math.max(...slice.map((d) => d.h));
    const lowestLow = Math.min(...slice.map((d) => d.l));
    const range = highestHigh - lowestLow;
    stochK.push(range === 0 ? 50 : ((data[i].c - lowestLow) / range) * 100);
  }

  // Smooth %K if smooth > 1
  let smoothedK = stochK;
  if (smooth > 1) {
    smoothedK = stochK.map((_, i) => {
      if (i < kPeriod - 1 + smooth - 1) return null;
      const slice = stochK
        .slice(i - smooth + 1, i + 1)
        .filter((v) => v !== null);
      return slice.length === smooth
        ? slice.reduce((a, b) => a + b, 0) / smooth
        : null;
    });
  }

  // Calculate %D (SMA of %K)
  for (let i = 0; i < data.length; i++) {
    if (i < kPeriod - 1 + smooth - 1 + dPeriod - 1) {
      stochD.push(null);
      continue;
    }
    const slice = smoothedK
      .slice(i - dPeriod + 1, i + 1)
      .filter((v) => v !== null);
    stochD.push(
      slice.length === dPeriod
        ? slice.reduce((a, b) => a + b, 0) / dPeriod
        : null,
    );
  }

  return { k: smoothedK, d: stochD };
}

// Calculate Williams %R
function calculateWilliamsR(data, period = 14) {
  return data.map((d, i) => {
    if (i < period - 1) return null;
    const slice = data.slice(i - period + 1, i + 1);
    const highestHigh = Math.max(...slice.map((s) => s.h));
    const lowestLow = Math.min(...slice.map((s) => s.l));
    const range = highestHigh - lowestLow;
    return range === 0 ? -50 : ((highestHigh - d.c) / range) * -100;
  });
}

// Calculate Rate of Change (ROC)
function calculateROC(data, period = 10) {
  return data.map((d, i) => {
    if (i < period) return null;
    const prevPrice = data[i - period].c;
    return prevPrice === 0 ? null : ((d.c - prevPrice) / prevPrice) * 100;
  });
}

// Calculate Commodity Channel Index (CCI)
function calculateCCI(data, period = 20) {
  const tp = calculateTypicalPrice(data);

  return data.map((_, i) => {
    if (i < period - 1) return null;
    const slice = tp.slice(i - period + 1, i + 1);
    const sma = slice.reduce((a, b) => a + b, 0) / period;
    const meanDev = slice.reduce((a, b) => a + Math.abs(b - sma), 0) / period;
    return meanDev === 0 ? 0 : (tp[i] - sma) / (0.015 * meanDev);
  });
}

// ============================================================================
// TREND INDICATORS
// ============================================================================

// Calculate Average Directional Index (ADX)
function calculateADX(data, period = 14) {
  const plusDM = [];
  const minusDM = [];
  const tr = calculateTrueRange(data);

  // Calculate +DM and -DM
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      plusDM.push(0);
      minusDM.push(0);
      continue;
    }
    const upMove = data[i].h - data[i - 1].h;
    const downMove = data[i - 1].l - data[i].l;

    plusDM.push(upMove > downMove && upMove > 0 ? upMove : 0);
    minusDM.push(downMove > upMove && downMove > 0 ? downMove : 0);
  }

  // Smooth TR, +DM, -DM using Wilder's smoothing
  const smoothTR = wilderSmooth(tr, period);
  const smoothPlusDM = wilderSmooth(plusDM, period);
  const smoothMinusDM = wilderSmooth(minusDM, period);

  // Calculate +DI and -DI
  const plusDI = smoothTR.map((tr, i) =>
    tr === null || tr === 0 ? null : (smoothPlusDM[i] / tr) * 100,
  );
  const minusDI = smoothTR.map((tr, i) =>
    tr === null || tr === 0 ? null : (smoothMinusDM[i] / tr) * 100,
  );

  // Calculate DX
  const dx = plusDI.map((pdi, i) => {
    if (pdi === null || minusDI[i] === null) return null;
    const sum = pdi + minusDI[i];
    return sum === 0 ? 0 : (Math.abs(pdi - minusDI[i]) / sum) * 100;
  });

  // Calculate ADX (smoothed DX)
  const adx = wilderSmooth(dx, period);

  return { adx, plusDI, minusDI };
}

// Helper: Wilder's Smoothing
function wilderSmooth(values, period) {
  const result = new Array(values.length).fill(null);

  // Find first valid index
  let firstValidIndex = -1;
  let sum = 0;
  let count = 0;
  for (let i = 0; i < values.length && count < period; i++) {
    if (values[i] !== null) {
      sum += values[i];
      count++;
      if (count === period) {
        firstValidIndex = i;
        result[i] = sum / period;
      }
    }
  }

  if (firstValidIndex === -1) return result;

  // Apply Wilder's smoothing
  for (let i = firstValidIndex + 1; i < values.length; i++) {
    if (values[i] === null) {
      result[i] = result[i - 1];
    } else {
      result[i] = (result[i - 1] * (period - 1) + values[i]) / period;
    }
  }

  return result;
}

// ============================================================================
// VOLUME INDICATORS
// ============================================================================

// Calculate Volume SMA
function calculateVolumeSMA(data, period = 20) {
  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    const slice = arr.slice(i - period + 1, i + 1);
    return slice.reduce((sum, d) => sum + d.v, 0) / period;
  });
}

// Calculate On Balance Volume (OBV)
function calculateOBV(data) {
  let obv = 0;
  return data.map((d, i) => {
    if (i === 0) return 0;
    const priceChange = d.c - data[i - 1].c;
    if (priceChange > 0) {
      obv += d.v;
    } else if (priceChange < 0) {
      obv -= d.v;
    }
    // If price unchanged, OBV stays the same
    return obv;
  });
}

// Calculate Volume Weighted Average Price (VWAP)
// Note: VWAP is typically calculated intraday, resets each day
function calculateVWAP(data) {
  let cumVolume = 0;
  let cumTPV = 0; // Cumulative (Typical Price * Volume)

  return data.map((d) => {
    const tp = (d.h + d.l + d.c) / 3;
    cumVolume += d.v;
    cumTPV += tp * d.v;
    return cumVolume === 0 ? null : cumTPV / cumVolume;
  });
}

// Calculate Money Flow Index (MFI) - Volume-weighted RSI
function calculateMFI(data, period = 14) {
  const tp = calculateTypicalPrice(data);
  const mf = tp.map((t, i) => t * data[i].v); // Money Flow

  const posMF = [];
  const negMF = [];

  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      posMF.push(0);
      negMF.push(0);
      continue;
    }
    if (tp[i] > tp[i - 1]) {
      posMF.push(mf[i]);
      negMF.push(0);
    } else if (tp[i] < tp[i - 1]) {
      posMF.push(0);
      negMF.push(mf[i]);
    } else {
      posMF.push(0);
      negMF.push(0);
    }
  }

  return data.map((_, i) => {
    if (i < period) return null;
    const posSum = posMF
      .slice(i - period + 1, i + 1)
      .reduce((a, b) => a + b, 0);
    const negSum = negMF
      .slice(i - period + 1, i + 1)
      .reduce((a, b) => a + b, 0);
    if (negSum === 0) return 100;
    const mfRatio = posSum / negSum;
    return 100 - 100 / (1 + mfRatio);
  });
}

// Calculate Accumulation/Distribution Line (A/D Line)
function calculateADLine(data) {
  let adLine = 0;
  return data.map((d) => {
    const range = d.h - d.l;
    const mfm = range === 0 ? 0 : (d.c - d.l - (d.h - d.c)) / range;
    const mfv = mfm * d.v;
    adLine += mfv;
    return adLine;
  });
}

// Calculate Chaikin Money Flow (CMF)
function calculateCMF(data, period = 20) {
  return data.map((_, i, arr) => {
    if (i < period - 1) return null;
    const slice = arr.slice(i - period + 1, i + 1);

    let sumMFV = 0;
    let sumVolume = 0;

    for (const d of slice) {
      const range = d.h - d.l;
      const mfm = range === 0 ? 0 : (d.c - d.l - (d.h - d.c)) / range;
      sumMFV += mfm * d.v;
      sumVolume += d.v;
    }

    return sumVolume === 0 ? 0 : sumMFV / sumVolume;
  });
}

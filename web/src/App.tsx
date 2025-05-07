import React, { useEffect, useRef, useState } from 'react';
import {
  createChart,
  UTCTimestamp,
  CandlestickSeriesOptions,
  CandlestickData,
  DeepPartial,
} from 'lightweight-charts';

interface TickData {
  time: number;
  price: number;
  size: number;
}

const App: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState("Connecting...");
  const [last, setLast] = useState<TickData | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        backgroundColor: '#1e1e1e',
        textColor: '#ffffff',
      },
      grid: {
        vertLines: { color: '#444' },
        horzLines: { color: '#444' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    const seriesOptions: DeepPartial<CandlestickSeriesOptions> = {
      upColor: '#4bffb5',
      downColor: '#ff4976',
      borderUpColor: '#4bffb5',
      borderDownColor: '#ff4976',
      wickUpColor: '#4bffb5',
      wickDownColor: '#ff4976',
    };

    const series = chart.addCandlestickSeries(seriesOptions);

    const ws = new WebSocket('ws://localhost:8765/ws');
    ws.onopen = () => setStatus("Connected");

    ws.onmessage = (e) => {
      const tick: TickData = JSON.parse(e.data);
      setLast(tick);

      const candle: CandlestickData = {
        time: tick.time as UTCTimestamp,
        open: tick.price,
        high: tick.price,
        low: tick.price,
        close: tick.price,
      };

      series.update(candle);
    };

    ws.onclose = () => setStatus("Disconnected");
    ws.onerror = () => setStatus("Error");

    const handleResize = () => {
      chart.resize(
        chartContainerRef.current!.clientWidth,
        chartContainerRef.current!.clientHeight
      );
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      ws.close();
      chart.remove();
    };
  }, []);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#1e1e1e' }}>
      <header style={{ padding: 10, background: '#333', color: '#fff', textAlign: 'center' }}>
        <h2>KawaiiTrader Live Chart</h2>
        <p>Status: {status}</p>
        {last && (
          <p>
            Last – {new Date(last.time * 1000).toLocaleTimeString()}, ${last.price.toFixed(2)} ({last.size})
          </p>
        )}
      </header>
      <div ref={chartContainerRef} style={{ flex: 1 }} />
    </div>
  );
};

export default App;

'use client';

import React, { useState } from 'react';

interface ClusterStats {
  name: string;
  color: string;
  size: number;
  avgConsumption: number;
  peakHour: number;
  peakValue: number;
  flatness: number;
  variance: number;
}

const CLUSTERS: ClusterStats[] = [
  {
    name: 'Midday-Peaking',
    color: '#F5A524',
    size: 94,
    avgConsumption: 2450,
    peakHour: 13,
    peakValue: 3200,
    flatness: 0.42,
    variance: 450
  },
  {
    name: 'Flat All-Day',
    color: '#3BC9DE',
    size: 57,
    avgConsumption: 2200,
    peakHour: 19,
    peakValue: 2620,
    flatness: 0.85,
    variance: 220
  },
  {
    name: 'Evening-Peaking',
    color: '#B085F5',
    size: 49,
    avgConsumption: 2100,
    peakHour: 20,
    peakValue: 3800,
    flatness: 0.38,
    variance: 520
  }
];

const METRICS = [
  { key: 'size', label: 'Consumers', unit: '', normalize: (v: number) => v / 94 },
  { key: 'avgConsumption', label: 'Avg Usage', unit: 'kWh', normalize: (v: number) => v / 2450 },
  { key: 'peakValue', label: 'Peak Usage', unit: 'kWh', normalize: (v: number) => v / 3800 },
  { key: 'flatness', label: 'Flatness', unit: '(0-1)', normalize: (v: number) => v },
  { key: 'variance', label: 'Variance', unit: '', normalize: (v: number) => v / 520 }
];

export default function ClusterComparison() {
  const [selectedMetric, setSelectedMetric] = useState<string>('size');
  const metric = METRICS.find(m => m.key === selectedMetric);

  if (!metric) return null;

  return (
    <div className="w-full">
      {/* Metric Selector */}
      <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setSelectedMetric(m.key)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap rounded-lg transition ${
              selectedMetric === m.key
                ? 'bg-[#3BC9DE] text-[#0B0E14]'
                : 'bg-[#141A24] border border-[#262E3D] text-[#8A93A6] hover:border-[#3BC9DE]'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Comparison Chart */}
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-8 mb-6">
        <div className="space-y-6">
          {CLUSTERS.map((cluster, i) => {
            const value = cluster[metric.key as keyof ClusterStats] as number;
            const normalized = metric.normalize(value);
            const percentage = normalized * 100;

            return (
              <div key={i}>
                <div className="flex justify-between items-baseline mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: cluster.color }}
                    />
                    <p className="font-semibold text-[#EAECEF]">{cluster.name}</p>
                  </div>
                  <p className="text-lg font-mono font-semibold text-[#3BC9DE]">
                    {typeof value === 'number' && value < 10 
                      ? value.toFixed(2)
                      : Math.round(value as number)
                    }
                    {metric.unit && <span className="text-xs text-[#8A93A6] ml-1">{metric.unit}</span>}
                  </p>
                </div>
                <div className="w-full bg-[#262E3D] rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: cluster.color,
                      opacity: 0.8
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#262E3D]">
              <th className="text-left py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Cluster</th>
              <th className="text-right py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Size</th>
              <th className="text-right py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Avg Usage</th>
              <th className="text-right py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Peak Hour</th>
              <th className="text-right py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Peak Value</th>
              <th className="text-right py-3 px-4 font-semibold text-[#8A93A6] text-xs uppercase tracking-wider">Flatness</th>
            </tr>
          </thead>
          <tbody>
            {CLUSTERS.map((cluster, i) => (
              <tr key={i} className="border-b border-[#262E3D] hover:bg-[#141A24] transition">
                <td className="py-3 px-4 font-medium">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: cluster.color }}
                    />
                    {cluster.name}
                  </div>
                </td>
                <td className="text-right py-3 px-4 text-[#EAECEF]">{cluster.size}</td>
                <td className="text-right py-3 px-4 text-[#EAECEF]">{cluster.avgConsumption} kWh</td>
                <td className="text-right py-3 px-4 text-[#EAECEF]">{cluster.peakHour}:00</td>
                <td className="text-right py-3 px-4 text-[#EAECEF]">{cluster.peakValue} kWh</td>
                <td className="text-right py-3 px-4 text-[#3BC9DE]">{cluster.flatness.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Insights */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#F5A524] uppercase mb-2">Largest Group</p>
          <p className="text-lg font-semibold text-[#EAECEF]">Midday-Peaking</p>
          <p className="text-sm text-[#8A93A6] mt-1">94 consumers (47%)</p>
        </div>
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#3BC9DE] uppercase mb-2">Flattest Pattern</p>
          <p className="text-lg font-semibold text-[#EAECEF]">Flat All-Day</p>
          <p className="text-sm text-[#8A93A6] mt-1">Flatness: 0.85</p>
        </div>
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#B085F5] uppercase mb-2">Sharpest Peak</p>
          <p className="text-lg font-semibold text-[#EAECEF]">Evening-Peaking</p>
          <p className="text-sm text-[#8A93A6] mt-1">3800 kWh @ 8pm</p>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';

interface DataPoint {
  hour: number;
  consumption: number;
  cluster: 'Midday-Peaking' | 'Flat All-Day' | 'Evening-Peaking';
}

// Generate sample hourly consumption data
const generateDataset = (): DataPoint[] => {
  const data: DataPoint[] = [];
  
  // Midday-Peaking pattern
  for (let h = 0; h < 24; h++) {
    const base = 2000 + (h - 12) * (h - 12) * 10;
    data.push({
      hour: h,
      consumption: Math.max(1500, base + Math.random() * 200),
      cluster: 'Midday-Peaking'
    });
  }

  // Flat All-Day pattern
  for (let h = 0; h < 24; h++) {
    const peak = Math.sin((h - 19) * Math.PI / 6) * 300;
    data.push({
      hour: h,
      consumption: 2200 + peak + Math.random() * 150,
      cluster: 'Flat All-Day'
    });
  }

  // Evening-Peaking pattern
  for (let h = 0; h < 24; h++) {
    const peak = h > 18 ? (h - 18) * 400 : Math.max(500, (18 - h) * 50);
    data.push({
      hour: h,
      consumption: 1000 + peak + Math.random() * 200,
      cluster: 'Evening-Peaking'
    });
  }

  return data;
};

export default function DatasetViewer() {
  const [selectedCluster, setSelectedCluster] = useState<'Midday-Peaking' | 'Flat All-Day' | 'Evening-Peaking'>('Midday-Peaking');
  const dataset = generateDataset();
  const filteredData = dataset.filter(d => d.cluster === selectedCluster);

  const clusterColors = {
    'Midday-Peaking': '#F5A524',
    'Flat All-Day': '#3BC9DE',
    'Evening-Peaking': '#B085F5'
  };

  const maxConsumption = Math.max(...filteredData.map(d => d.consumption));
  const minConsumption = Math.min(...filteredData.map(d => d.consumption));
  const range = maxConsumption - minConsumption;

  return (
    <div className="w-full">
      {/* Cluster Tabs */}
      <div className="flex gap-2 mb-6 border-b border-[#262E3D]">
        {(['Midday-Peaking', 'Flat All-Day', 'Evening-Peaking'] as const).map((cluster) => (
          <button
            key={cluster}
            onClick={() => setSelectedCluster(cluster)}
            className={`px-4 py-3 text-sm font-medium transition border-b-2 ${
              selectedCluster === cluster
                ? 'border-[#3BC9DE] text-[#3BC9DE]'
                : 'border-transparent text-[#8A93A6] hover:text-[#EAECEF]'
            }`}
          >
            {cluster}
          </button>
        ))}
      </div>

      {/* Chart Area */}
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-6 mb-6">
        <div className="h-80 flex flex-col justify-end gap-1">
          <div className="flex items-end justify-between gap-1">
            {filteredData.map((point, i) => {
              const height = ((point.consumption - minConsumption) / range) * 100;
              return (
                <div key={i} className="flex-1 flex flex-col items-center group">
                  <div
                    className="w-full rounded-t transition hover:opacity-80"
                    style={{
                      height: `${Math.max(5, height)}%`,
                      backgroundColor: clusterColors[selectedCluster],
                      opacity: 0.7
                    }}
                  />
                  <span className="text-xs text-[#8A93A6] mt-2 group-hover:text-[#3BC9DE]">
                    {point.hour}h
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#8A93A6] mb-2 uppercase">Peak Hour</p>
          <p className="text-2xl font-semibold text-[#EAECEF]">
            {filteredData.reduce((max, p) => p.consumption > max.consumption ? p : max).hour}h
          </p>
        </div>
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#8A93A6] mb-2 uppercase">Peak Usage</p>
          <p className="text-2xl font-semibold text-[#EAECEF]">
            {Math.round(maxConsumption).toLocaleString()} kWh
          </p>
        </div>
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#8A93A6] mb-2 uppercase">Min Usage</p>
          <p className="text-2xl font-semibold text-[#EAECEF]">
            {Math.round(minConsumption).toLocaleString()} kWh
          </p>
        </div>
        <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
          <p className="text-xs font-mono text-[#8A93A6] mb-2 uppercase">Avg Usage</p>
          <p className="text-2xl font-semibold text-[#EAECEF]">
            {Math.round(filteredData.reduce((sum, p) => sum + p.consumption, 0) / filteredData.length).toLocaleString()} kWh
          </p>
        </div>
      </div>
    </div>
  );
}

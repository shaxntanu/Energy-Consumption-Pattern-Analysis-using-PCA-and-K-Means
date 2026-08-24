'use client';

/**
 * Profile Playback Component
 * Animates hourly consumption patterns across 24 hours
 */

import React, { useState, useEffect, useRef } from 'react';

interface HourData {
  hour: number;
  midday: number;
  flat: number;
  evening: number;
}

// Generate hourly profile data for all three clusters
const generateProfiles = (): HourData[] => {
  const profiles: HourData[] = [];
  
  for (let h = 0; h < 24; h++) {
    // Midday-Peaking: rises through morning to afternoon plateau
    const midday = 2000 + (Math.sin((h - 5) * Math.PI / 14) * 1000);
    
    // Flat All-Day: close to level, weak peak near 7pm
    const flat = 2200 + (Math.sin((h - 19) * Math.PI / 6) * 300);
    
    // Evening-Peaking: quiet by day, sharp peak near 8pm
    const evening = h < 18 ? 1000 + (18 - h) * 50 : 1000 + (h - 18) * 500;

    profiles.push({
      hour: h,
      midday: Math.max(500, midday),
      flat: Math.max(800, flat),
      evening: Math.max(500, evening)
    });
  }

  return profiles;
};

export default function ProfilePlayback() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentHour, setCurrentHour] = useState(0);
  const [speed, setSpeed] = useState(1);
  const animationRef = useRef<any>(null);
  const profiles = generateProfiles();

  useEffect(() => {
    if (!isPlaying) {
      if (animationRef.current) clearInterval(animationRef.current);
      return;
    }

    animationRef.current = setInterval(() => {
      setCurrentHour((prev) => (prev + 1) % 24);
    }, 500 / speed);

    return () => {
      if (animationRef.current) clearInterval(animationRef.current);
    };
  }, [isPlaying, speed]);

  const current = profiles[currentHour];
  const maxValue = Math.max(...profiles.flatMap(p => [p.midday, p.flat, p.evening]));

  const clusterColors = {
    midday: '#F5A524',
    flat: '#3BC9DE',
    evening: '#B085F5'
  };

  const clusterData = [
    { key: 'midday' as const, name: 'Midday-Peaking', value: current.midday },
    { key: 'flat' as const, name: 'Flat All-Day', value: current.flat },
    { key: 'evening' as const, name: 'Evening-Peaking', value: current.evening }
  ];

  return (
    <div className="w-full">
      {/* Hour Display */}
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-8 mb-6 text-center">
        <div className="text-sm font-mono text-[#8A93A6] mb-2 uppercase tracking-wider">
          Current Hour
        </div>
        <div className="text-6xl font-bold text-[#3BC9DE]">
          {String(currentHour).padStart(2, '0')}
          <span className="text-3xl ml-2">:00</span>
        </div>
      </div>

      {/* Playback Controls */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex-1 bg-[#3BC9DE] text-[#0B0E14] px-4 py-3 rounded-lg font-semibold hover:bg-[#2BA8B3] transition"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button
          onClick={() => setCurrentHour(0)}
          className="flex-1 bg-[#141A24] border border-[#262E3D] text-[#EAECEF] px-4 py-3 rounded-lg font-semibold hover:border-[#8A93A6] transition"
        >
          Reset
        </button>
      </div>

      {/* Speed Control */}
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4 mb-6">
        <p className="text-xs font-mono text-[#8A93A6] mb-3 uppercase">Speed: {speed}x</p>
        <input
          type="range"
          min="0.5"
          max="3"
          step="0.5"
          value={speed}
          onChange={(e) => setSpeed(parseFloat(e.target.value))}
          className="w-full h-2 bg-[#262E3D] rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #3BC9DE 0%, #3BC9DE ${(speed - 0.5) / 2.5 * 100}%, #262E3D ${(speed - 0.5) / 2.5 * 100}%, #262E3D 100%)`
          }}
        />
      </div>

      {/* Consumption Chart */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {clusterData.map((cluster) => (
          <div key={cluster.key} className="bg-[#141A24] border border-[#262E3D] rounded-lg overflow-hidden">
            {/* Mini bar chart */}
            <div className="h-40 bg-[#0B0E14] p-3 flex items-end justify-between gap-1">
              {profiles.map((p, i) => {
                const value = p[cluster.key];
                const height = (value / maxValue) * 100;
                const isActive = i === currentHour;
                return (
                  <div
                    key={i}
                    className="flex-1 rounded-t transition"
                    style={{
                      height: `${Math.max(5, height)}%`,
                      backgroundColor: clusterColors[cluster.key],
                      opacity: isActive ? 1 : 0.3,
                      borderTop: isActive ? `2px solid ${clusterColors[cluster.key]}` : 'none'
                    }}
                  />
                );
              })}
            </div>
            {/* Label and value */}
            <div className="p-4 border-t border-[#262E3D]">
              <p className="text-xs font-mono text-[#8A93A6] mb-2 uppercase">{cluster.name}</p>
              <p className="text-2xl font-semibold text-[#EAECEF]">
                {Math.round(cluster.value).toLocaleString()}
              </p>
              <p className="text-xs text-[#8A93A6] mt-1">kWh</p>
            </div>
          </div>
        ))}
      </div>

      {/* Hour Slider */}
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
        <input
          type="range"
          min="0"
          max="23"
          value={currentHour}
          onChange={(e) => setCurrentHour(parseInt(e.target.value))}
          className="w-full h-2 bg-[#262E3D] rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #3BC9DE 0%, #3BC9DE ${(currentHour / 23) * 100}%, #262E3D ${(currentHour / 23) * 100}%, #262E3D 100%)`
          }}
        />
        <div className="flex justify-between mt-3 text-xs font-mono text-[#8A93A6]">
          <span>00:00</span>
          <span>12:00</span>
          <span>23:00</span>
        </div>
      </div>
    </div>
  );
}

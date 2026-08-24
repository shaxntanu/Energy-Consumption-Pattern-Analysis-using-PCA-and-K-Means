'use client';

import React, { useEffect, useState } from 'react';

export default function StreamlitLink() {
  const [streamlitAvailable, setStreamlitAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStreamlit = async () => {
      try {
        const response = await fetch('/api/streamlit-link');
        setStreamlitAvailable(response.ok);
      } catch {
        setStreamlitAvailable(false);
      } finally {
        setLoading(false);
      }
    };

    checkStreamlit();
  }, []);

  if (loading) {
    return (
      <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-6 text-center">
        <p className="text-[#8A93A6]">Checking Streamlit connection...</p>
      </div>
    );
  }

  return (
    <div className="bg-[#141A24] border border-[#262E3D] rounded-lg p-6">
      <p className="text-xs font-mono text-[#3BC9DE] uppercase mb-3">Simulator</p>
      <p className="text-lg font-semibold text-[#EAECEF] mb-4">
        Interactive Dashboard
      </p>
      <p className="text-sm text-[#8A93A6] mb-4">
        Run the Streamlit simulator locally to interactively explore datasets, adjust parameters, and visualize clustering results in real-time.
      </p>
      <a
        href={streamlitAvailable ? 'http://localhost:8501' : '#'}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-block px-6 py-3 rounded-lg font-semibold transition ${
          streamlitAvailable
            ? 'bg-[#3BC9DE] text-[#0B0E14] hover:bg-[#2BA8B3]'
            : 'bg-[#262E3D] text-[#8A93A6] cursor-not-allowed'
        }`}
      >
        {streamlitAvailable ? 'Open Simulator' : 'Simulator Offline'}
      </a>
      {!streamlitAvailable && (
        <p className="text-xs text-[#8A93A6] mt-3">
          Run: <code className="bg-[#0B0E14] px-2 py-1 rounded">streamlit run streamlit_app.py</code>
        </p>
      )}
    </div>
  );
}

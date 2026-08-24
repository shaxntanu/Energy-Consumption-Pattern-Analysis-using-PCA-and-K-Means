import React from 'react';
import ClusterExplorer from './components/ClusterExplorer';
import DatasetViewer from './components/DatasetViewer';
import ProfilePlayback from './components/ProfilePlayback';
import ClusterComparison from './components/ClusterComparison';
import NarrativeCards from './components/NarrativeCards';
import StreamlitLink from './components/StreamlitLink';
import ExportData from './components/ExportData';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0B0E14] via-[#0F1219] to-[#0B0E14]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0B0E14]/90 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3BC9DE] to-[#1E9DB2] flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-lg font-bold text-white">Energy Patterns</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#clusters" className="text-sm text-gray-400 hover:text-white transition-colors">Clusters</a>
              <a href="#explore" className="text-sm text-gray-400 hover:text-white transition-colors">Explore</a>
              <a href="#export" className="text-sm text-gray-400 hover:text-white transition-colors">Export</a>
              <a href="#launch" className="px-4 py-2 bg-gradient-to-r from-[#3BC9DE] to-[#1E9DB2] text-white text-sm font-semibold rounded-lg hover:shadow-lg hover:shadow-[#3BC9DE]/50 transition-all">
                Launch Simulator
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#3BC9DE]/10 border border-[#3BC9DE]/20 mb-8">
            <div className="w-2 h-2 rounded-full bg-[#3BC9DE] animate-pulse" />
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-wider">PCA + K-Means Clustering</span>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            Energy has a{' '}
            <span className="bg-gradient-to-r from-[#3BC9DE] via-[#1E9DB2] to-[#3BC9DE] bg-clip-text text-transparent animate-gradient">
              rhythm
            </span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mb-12 leading-relaxed">
            Two homes can use the same amount of electricity and behave nothing alike.
            One runs flat all day; another barely stirs until the evening. This project
            groups consumers by the <span className="text-white font-semibold">shape of their day</span>,
            not by how much they use.
          </p>

          <div className="flex flex-wrap gap-4">
            <a href="#clusters" className="group px-8 py-4 bg-gradient-to-r from-[#3BC9DE] to-[#1E9DB2] text-white font-semibold rounded-xl hover:shadow-xl hover:shadow-[#3BC9DE]/50 transition-all transform hover:scale-105">
              <span className="flex items-center gap-2">
                Explore Clusters
                <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </span>
            </a>
            <a href="#launch" className="px-8 py-4 bg-white/5 text-white font-semibold rounded-xl border border-white/10 hover:bg-white/10 transition-all">
              View Interactive Demo
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16">
            {[
              { value: '200', label: 'Consumers' },
              { value: '144K', label: 'Data Points' },
              { value: '3', label: 'Clusters Found' },
              { value: '95%', label: 'Variance Explained' }
            ].map((stat, i) => (
              <div key={i} className="p-6 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 backdrop-blur-sm">
                <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">02 · Dataset</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Synthetic, controlled data</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Generated with known patterns to validate the clustering approach
            </p>
          </div>

          <DatasetViewer />
        </div>
      </section>

      {/* Clusters Section */}
      <section id="clusters" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">04 · The Clusters</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Three distinct rhythms</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              The algorithm discovered three clear patterns in how energy is consumed throughout the day
            </p>
          </div>

          <div className="mb-16">
            <ClusterExplorer />
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { 
                name: 'Midday-Peaking', 
                color: '#F5A524', 
                size: 94, 
                peak: '1 PM', 
                desc: 'Consumption rises through morning to a broad afternoon plateau',
                icon: '☀️'
              },
              { 
                name: 'Flat All-Day', 
                color: '#3BC9DE', 
                size: 57, 
                peak: '7 PM', 
                desc: 'Steady consumption with minimal variation and weak evening peak',
                icon: '📊'
              },
              { 
                name: 'Evening-Peaking', 
                color: '#B085F5', 
                size: 49, 
                peak: '8 PM', 
                desc: 'Quiet during day, sharp spike when residents return home',
                icon: '🌙'
              }
            ].map((cluster, i) => (
              <div key={i} className="group p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 hover:border-white/20 transition-all hover:transform hover:scale-105">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">{cluster.icon}</span>
                  <div>
                    <h3 className="text-xl font-bold text-white">{cluster.name}</h3>
                    <p className="text-sm text-gray-400">{cluster.size} consumers · peaks {cluster.peak}</p>
                  </div>
                </div>
                <div className="w-full h-1 rounded-full bg-white/5 mb-4">
                  <div className="h-full rounded-full transition-all duration-1000 group-hover:w-full" style={{ width: '0%', backgroundColor: cluster.color }} />
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">{cluster.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Playback */}
      <section id="explore" className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">05 · Interactive</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Watch the day unfold</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              See how each cluster's consumption changes hour by hour
            </p>
          </div>

          <ProfilePlayback />
        </div>
      </section>

      {/* Comparison */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">06 · Analysis</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Side-by-side comparison</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Compare metrics across all three clusters
            </p>
          </div>

          <ClusterComparison />
        </div>
      </section>

      {/* Narrative */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">07 · Methodology</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">From data to insight</h2>
          </div>

          <NarrativeCards />
        </div>
      </section>

      {/* Export */}
      <section id="export" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">08 · Export</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Download your findings</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Export cluster data in multiple formats
            </p>
          </div>

          <ExportData />
        </div>
      </section>

      {/* Launch */}
      <section id="launch" className="py-20 px-4 sm:px-6 lg:px-8 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <span className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest">09 · Simulator</span>
            <h2 className="text-4xl font-bold text-white mt-4 mb-6">Interactive dashboard</h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
              Run the full Streamlit simulator locally for deeper exploration
            </p>
          </div>

          <StreamlitLink />
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-400 text-sm">
            Built with Next.js, Three.js, and Python · PCA + K-Means Clustering Study
          </p>
          <p className="text-gray-600 text-xs mt-2">
            © 2026 · All rights reserved
          </p>
        </div>
      </footer>
    </div>
  );
}

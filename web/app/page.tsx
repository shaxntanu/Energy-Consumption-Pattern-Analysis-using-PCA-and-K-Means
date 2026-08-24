import React from 'react';
import ClusterExplorer from './components/ClusterExplorer';
import DatasetViewer from './components/DatasetViewer';
import ProfilePlayback from './components/ProfilePlayback';
import ClusterComparison from './components/ClusterComparison';
import NarrativeCards from './components/NarrativeCards';
import StreamlitLink from './components/StreamlitLink';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0B0E14] text-[#EAECEF]">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-black/80 backdrop-blur-lg border-b border-[#262E3D]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="font-bold text-sm tracking-tight">
            <span className="text-[#3BC9DE]">/</span> Load-Shape Study
          </div>
          <div className="hidden md:flex gap-8 items-center">
            <a href="#question" className="text-xs font-mono uppercase tracking-wider text-[#8A93A6] hover:text-[#EAECEF] transition">The question</a>
            <a href="#clusters" className="text-xs font-mono uppercase tracking-wider text-[#8A93A6] hover:text-[#EAECEF] transition">Clusters</a>
            <a href="#validation" className="text-xs font-mono uppercase tracking-wider text-[#8A93A6] hover:text-[#EAECEF] transition">Validation</a>
            <a href="#reading" className="text-xs font-mono uppercase tracking-wider text-[#8A93A6] hover:text-[#EAECEF] transition">References</a>
            <a href="#launch" className="px-4 py-2 bg-[#3BC9DE] text-[#0B0E14] font-semibold rounded-lg text-sm hover:bg-[#1E9DB2] transition">
              Explore the data
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <p className="text-xs font-mono font-semibold uppercase tracking-widest text-[#3BC9DE] mb-6">
            PCA + K-Means · synthetic study
          </p>
          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            Energy has a <span className="text-[#3BC9DE]">rhythm</span>.
          </h1>
          <p className="text-lg md:text-xl text-[#8A93A6] max-w-2xl mb-8 leading-relaxed">
            Two homes can use the same amount of electricity and behave nothing alike.
            One runs flat all day; another barely stirs until the evening. This project
            groups consumers by the <span className="text-[#EAECEF] font-semibold">shape of their day</span>,
            not by how much they use.
          </p>
          
          <div className="flex flex-wrap gap-4 mb-12">
            <a href="#launch" className="px-6 py-3 bg-[#3BC9DE] text-[#0B0E14] font-semibold rounded-lg hover:bg-[#1E9DB2] transition">
              Explore the data
            </a>
            <a href="#question" className="px-6 py-3 border border-[#262E3D] text-[#EAECEF] font-semibold rounded-lg hover:border-[#3BC9DE] transition">
              Read the study
            </a>
          </div>

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#F5A524]/35 bg-[#F5A524]/10">
            <div className="w-2 h-2 rounded-full bg-[#F5A524]" />
            <span className="text-xs font-mono text-[#F5A524] font-semibold uppercase tracking-wider">
              Synthetic data - not real households
            </span>
          </div>
        </div>
      </header>

      {/* Story Sections */}
      <main className="border-t border-[#262E3D]">
        <section id="question" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              01 · THE QUESTION
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Do people differ by when, not just how much?
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed">
              The easy way to sort electricity customers is by size: small, medium, large.
              It is also the least useful, because it says nothing about <em>when</em> demand
              lands on the grid. The question here is whether households fall into distinct
              <strong className="text-[#EAECEF]"> timing patterns</strong> - a daytime shape, an evening shape, a flat
              shape - that survive once you remove the effect of sheer volume.
            </p>
          </div>
        </section>

        <section id="data" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              02 · THE DATA
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              A controlled, synthetic world
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              To ask the question cleanly, the data is generated, not measured. A generator
              draws each consumer from one of four hidden archetypes, then adds amplitude,
              timing jitter, weekday and weekend differences, and noise. That hidden label is
              set aside before any modelling and used only, at the very end, to check the answer.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { value: "200", label: "consumers" },
                { value: "30", label: "days, hourly" },
                { value: "144,000", label: "records" },
                { value: "4", label: "hidden archetypes" }
              ].map((stat, i) => (
                <div key={i} className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
                  <div className="text-2xl font-semibold text-[#EAECEF]">{stat.value}</div>
                  <div className="text-xs font-mono text-[#8A93A6] uppercase tracking-wider mt-2">{stat.label}</div>
                </div>
              ))}
            </div>

            <div className="mt-12">
              <p className="text-xs font-mono text-[#8A93A6] font-semibold uppercase tracking-widest mb-4">
                Explore Patterns
              </p>
              <DatasetViewer />
            </div>
          </div>
        </section>

        <section id="method" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              03 · THE METHOD
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Compress, then group
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              Fifty-one features are correlated, so they are first standardised and passed
              through <strong className="text-[#EAECEF]">PCA</strong>, which keeps the <strong className="text-[#EAECEF]">14 components</strong> that
              together hold <strong className="text-[#EAECEF]">95%</strong> of the variance. K-Means then groups consumers
              in that compressed space, and the number of groups is chosen by a rule fixed in advance.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {[
                { step: "01", title: "Standardise", desc: "Zero mean, unit variance" },
                { step: "02", title: "PCA", desc: "14 components, 95% variance" },
                { step: "03", title: "Sweep K", desc: "K = 2 to 10, four metrics" },
                { step: "04", title: "Select", desc: "Pre-registered rule" },
                { step: "05", title: "Profile", desc: "Real units description" }
              ].map((p, i) => (
                <div key={i} className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
                  <p className="text-xs font-mono text-[#3BC9DE] font-semibold mb-2">{p.step}</p>
                  <p className="font-semibold text-sm mb-1">{p.title}</p>
                  <p className="text-xs text-[#8A93A6]">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="clusters" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              04 · THE CLUSTERS
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Three ways a day is spent
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              The rule settled on <strong className="text-[#EAECEF]">three groups</strong>. They are not big, medium and
              small - they are three different daily rhythms.
            </p>
            
            {/* 3D Cluster Explorer */}
            <div className="mb-12">
              <div className="lazy-load">
                <ClusterExplorer />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { name: "Midday-Peaking", color: "#F5A524", size: 94, peak: 13, desc: "Rises through the morning to a broad afternoon plateau." },
                { name: "Flat All-Day", color: "#3BC9DE", size: 57, peak: 19, desc: "Close to level; a weak nominal peak near 7 pm." },
                { name: "Evening-Peaking", color: "#B085F5", size: 49, peak: 20, desc: "Quiet by day, then a sharp peak near 8 pm." }
              ].map((cluster, i) => (
                <div key={i} className="bg-[#141A24] border-t-4 border border-[#262E3D] rounded-lg p-4" style={{ borderTopColor: cluster.color }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cluster.color }} />
                    <p className="font-semibold">{cluster.name}</p>
                  </div>
                  <p className="text-xs font-mono text-[#8A93A6] mb-2">{cluster.size} consumers · peaks {cluster.peak}:00</p>
                  <p className="text-sm text-[#8A93A6]">{cluster.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="playback" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              05 · PLAYBACK
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Watch a day unfold
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              Play through a 24-hour cycle to see how each cluster's consumption changes hour by hour. Adjust speed to see patterns clearly.
            </p>
            
            <ProfilePlayback />
          </div>
        </section>

        <section id="comparison" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              06 · COMPARISON
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Compare clusters side-by-side
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              Choose a metric to see how the three clusters differ. Explore size, consumption patterns, peak hours, and flatness.
            </p>
            
            <ClusterComparison />
          </div>
        </section>

        <section id="narrative" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-4xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              07 · THE STORY
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-12 max-w-2xl">
              From data to insight
            </h2>
            
            <NarrativeCards />
          </div>
        </section>

        <section id="validation" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              05 · HONEST VALIDATION
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              Stable grouping, modest separation
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              Good practice is to report the awkward number as plainly as the flattering one.
              The clusters are <strong className="text-[#EAECEF]">highly reproducible</strong> across random restarts, and
              they line up moderately with the hidden archetypes. But the <strong className="text-[#EAECEF]">separation is
              modest</strong> - both things are true at once.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { value: "0.312", label: "silhouette @ K=3", sub: "(modest)" },
                { value: "0.988", label: "stability ARI", sub: "(high)" },
                { value: "0.614", label: "agreement with archetypes", sub: "" },
                { value: "20", label: "seeds in robustness check", sub: "" }
              ].map((stat, i) => (
                <div key={i} className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
                  <div className="text-2xl font-semibold text-[#EAECEF]">{stat.value}</div>
                  <div className="text-xs font-mono text-[#8A93A6] uppercase tracking-wider mt-2">{stat.label}</div>
                  {stat.sub && <div className="text-xs text-[#8A93A6] mt-1">{stat.sub}</div>}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="launch" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              Run the instrument
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-6 max-w-2xl">
              The interactive simulator
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-8">
              The full study is a Streamlit application: adjust parameters, watch the analysis recompute,
              explore clusters, and see live charts update.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {[
                { title: "Streamlit Community Cloud", desc: "Deploy straight from the repository." },
                { title: "Render or Docker", desc: "Use the included render.yaml or Dockerfile." },
                { title: "Locally", desc: "Two commands below. No account needed." }
              ].map((opt, i) => (
                <div key={i} className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4">
                  <p className="font-semibold mb-2">{opt.title}</p>
                  <p className="text-sm text-[#8A93A6]">{opt.desc}</p>
                </div>
              ))}
            </div>
            <div className="bg-[#1B2230] border border-[#262E3D] rounded-lg p-4 font-mono text-sm mb-8 overflow-auto">
              <p className="text-[#EAECEF]">py -m pip install -r requirements.txt</p>
              <p className="text-[#EAECEF] mt-2">py -m streamlit run streamlit_app.py</p>
            </div>

            <StreamlitLink />
            <a href="https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means" target="_blank" rel="noopener noreferrer" className="text-[#3BC9DE] hover:text-[#1E9DB2] transition font-mono text-sm">
              View on GitHub →
            </a>
          </div>
        </section>

        <section id="reading" className="py-20 px-6 border-b border-[#262E3D]">
          <div className="max-w-6xl mx-auto">
            <p className="text-xs font-mono text-[#3BC9DE] font-semibold uppercase tracking-widest mb-4">
              The lineage
            </p>
            <h2 className="text-3xl md:text-4xl font-semibold mb-4 max-w-2xl">
              Where the method comes from
            </h2>
            <p className="text-lg text-[#8A93A6] max-w-2xl leading-relaxed mb-12">
              Grouping households by load curve shape is established. These peer-reviewed studies
              shaped our approach. Every entry was checked against Crossref.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { title: "A shape-based clustering method for pattern recognition of residential electricity consumption", authors: "Wen, Zhou, Yang · 2019", venue: "Journal of Cleaner Production", doi: "10.1016/j.jclepro.2018.12.067" },
                { title: "A clustering approach to domestic electricity load profile characterisation using smart metering data", authors: "McLoughlin, Duffy, Conlon · 2015", venue: "Applied Energy", doi: "10.1016/j.apenergy.2014.12.039" },
                { title: "Overview and performance assessment of the clustering methods for electrical load pattern grouping", authors: "Chicco · 2012", venue: "Energy", doi: "10.1016/j.energy.2011.12.031" },
                { title: "Electricity Consumption Clustering Using Smart Meter Data", authors: "Tureczek, Nielsen, Madsen · 2018", venue: "Energies", doi: "10.3390/en11040859" }
              ].map((ref, i) => (
                <a key={i} href={`https://doi.org/${ref.doi}`} target="_blank" rel="noopener noreferrer" className="bg-[#141A24] border border-[#262E3D] rounded-lg p-4 hover:border-[#3BC9DE] transition block">
                  <p className="font-semibold text-sm mb-2 leading-tight">{ref.title}</p>
                  <p className="text-xs text-[#8A93A6] font-mono mb-1">{ref.authors}</p>
                  <p className="text-xs text-[#3BC9DE] font-mono">{ref.doi}</p>
                </a>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#262E3D] py-8 px-6 text-center text-sm text-[#5B657A]">
        <div className="max-w-6xl mx-auto flex justify-between flex-wrap gap-4">
          <span>Synthetic study · PCA + K-Means · run 6dff8faaa470d418</span>
          <span>Grouped by the shape of the day, not the size of the bill.</span>
        </div>
      </footer>
    </div>
  );
}

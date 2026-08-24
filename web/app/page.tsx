export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="space-y-8">
          <div className="inline-block px-4 py-2 bg-cyan/10 border border-cyan/30 rounded-full">
            <span className="text-sm text-cyan font-mono">PCA + K-Means Clustering</span>
          </div>
          
          <h1 className="text-6xl font-bold leading-tight">
            Energy has a <span className="text-cyan">rhythm</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-2xl">
            Two homes can use the same electricity and behave nothing alike. 
            This project groups consumers by the <span className="text-white font-semibold">shape of their day</span>, 
            not how much they use.
          </p>

          <div className="flex gap-4">
            <a 
              href="#clusters" 
              className="px-6 py-3 bg-cyan text-midnight font-semibold rounded-lg hover:bg-cyan/90 transition"
            >
              Explore Clusters
            </a>
            <a 
              href="http://localhost:8501" 
              target="_blank"
              className="px-6 py-3 bg-white/5 border border-white/20 rounded-lg hover:bg-white/10 transition"
            >
              Launch Simulator
            </a>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-16">
          {[
            { value: '200', label: 'Consumers' },
            { value: '144K', label: 'Records' },
            { value: '3', label: 'Clusters' },
            { value: '95%', label: 'Variance' }
          ].map((stat, i) => (
            <div key={i} className="p-6 bg-panel rounded-xl border border-white/10">
              <div className="text-3xl font-bold">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Clusters */}
      <section id="clusters" className="max-w-5xl mx-auto px-6 py-20">
        <div className="space-y-8">
          <div>
            <span className="text-sm text-cyan font-mono">THE CLUSTERS</span>
            <h2 className="text-4xl font-bold mt-2">Three distinct patterns</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                name: 'Midday-Peaking',
                color: 'amber',
                size: 94,
                peak: '1 PM',
                desc: 'Rises through morning to afternoon plateau'
              },
              {
                name: 'Flat All-Day',
                color: 'cyan',
                size: 57,
                peak: '7 PM',
                desc: 'Steady with weak evening peak'
              },
              {
                name: 'Evening-Peaking',
                color: 'violet',
                size: 49,
                peak: '8 PM',
                desc: 'Quiet by day, sharp peak at night'
              }
            ].map((cluster, i) => (
              <div key={i} className="p-6 bg-panel rounded-xl border border-white/10 hover:border-white/30 transition">
                <h3 className={`text-xl font-bold text-${cluster.color} mb-2`}>
                  {cluster.name}
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  {cluster.size} consumers · peaks {cluster.peak}
                </p>
                <p className="text-gray-300">{cluster.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Method */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="space-y-8">
          <div>
            <span className="text-sm text-cyan font-mono">METHODOLOGY</span>
            <h2 className="text-4xl font-bold mt-2">How it works</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '01', title: 'Standardize', desc: 'Zero mean, unit variance' },
              { step: '02', title: 'PCA', desc: '14 components, 95% variance' },
              { step: '03', title: 'K-Means', desc: 'Find optimal K=3 clusters' }
            ].map((item, i) => (
              <div key={i} className="p-6 bg-panel rounded-xl border border-white/10">
                <div className="text-cyan font-mono text-sm mb-2">{item.step}</div>
                <div className="font-bold text-lg mb-2">{item.title}</div>
                <div className="text-gray-400 text-sm">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8">
        <div className="max-w-5xl mx-auto px-6 text-center text-gray-400 text-sm">
          <p>Built with Next.js · PCA + K-Means Study · 2026</p>
        </div>
      </footer>
    </main>
  );
}

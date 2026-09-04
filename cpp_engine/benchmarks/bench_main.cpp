// Standalone C++ benchmark for the engine's own kernels (no Python involved).
//
// Generates deterministic synthetic matrices (seeded RNG), times pca_fit and
// kmeans_fit at a few sizes, and prints a small JSON table to stdout. The
// Python harness (src/run_cpp_benchmark.py) is the fair Python-vs-C++
// comparison; this binary exists to show pure-C++ throughput and to exercise
// the engine without any Python build.
//
// Build:  cmake -S cpp_engine -B build -DENERGY_CPP_BUILD_BENCH=ON
//         cmake --build build --config Release
// Run:    ./build/energy_bench  (or build\\Release\\energy_bench.exe)

#include "kmeans.hpp"
#include "pca.hpp"
#include "utilities.hpp"

#include <cstdio>
#include <string>
#include <vector>

namespace {

// Deterministic synthetic matrix: each column is standard normal (Box-Muller
// over the SplitMix64 stream). Real pipeline matrices are structured, but this
// benchmark is about kernel throughput, and the shapes match the pipeline's
// (51 features; clustering on ~10 PCA scores).
energy::Mat synthetic_mat(std::size_t n, std::size_t d, std::uint64_t seed) {
  energy::Rng rng(seed);
  energy::Mat X(n, d);
  for (std::size_t i = 0; i < n; ++i) {
    for (std::size_t j = 0; j < d; ++j) {
      double u1 = rng.uniform01();
      if (u1 < 1e-12) u1 = 1e-12;
      const double u2 = rng.uniform01();
      const double mag = std::sqrt(-2.0 * std::log(u1));
      X(i, j) = mag * std::cos(2.0 * 3.14159265358979323846 * u2);
    }
  }
  return X;
}

double best_of(const std::vector<double>& ms) {
  double best = ms[0];
  for (double m : ms) best = m < best ? m : best;
  return best;
}

}  // namespace

int main() {
  struct PcaCase {
    const char* name;
    std::size_t n;
    std::size_t d;
  };
  const PcaCase pca_cases[] = {{"small", 200, 51}, {"medium", 2000, 51},
                               {"large", 20000, 51}, {"wide", 2000, 256}};

  struct KmCase {
    const char* name;
    std::size_t n;
    std::size_t d;
    int k;
  };
  const KmCase km_cases[] = {{"small", 200, 10, 4}, {"medium", 2000, 10, 4},
                             {"large", 20000, 10, 4}};

  std::printf("{\n  \"engine\": \"energy_cpp (standalone, C++17)\",\n");
  std::printf("  \"rows\": [\n");

  bool first = true;
  for (const auto& c : pca_cases) {
    const energy::Mat X = synthetic_mat(c.n, c.d, 42);
    // Warm-up, then best-of-3 (min wall time is robust to scheduler noise).
    energy::pca_fit(X, 0.95, 0);
    std::vector<double> times;
    energy::PcaResult last;
    for (int rep = 0; rep < 3; ++rep) {
      energy::Stopwatch sw;
      sw.start();
      last = energy::pca_fit(X, 0.95, 0);
      times.push_back(sw.elapsed_ms());
    }
    if (!first) std::printf(",\n");
    first = false;
    std::printf(
        "    {\"stage\": \"pca\", \"dataset\": \"%s\", \"n_samples\": %zu, "
        "\"n_features\": %zu, \"time_ms\": %.4f, \"n_components\": %d, "
        "\"variance_retained\": %.6f, \"jacobi_sweeps\": %zu}",
        c.name, c.n, c.d, best_of(times), last.n_components,
        last.cumulative_variance[static_cast<std::size_t>(last.n_components) - 1],
        last.jacobi_sweeps);
  }

  for (const auto& c : km_cases) {
    const energy::Mat X = synthetic_mat(c.n, c.d, 7);
    energy::kmeans_fit(X, c.k, 300, 1e-4, 10, true, 42);
    std::vector<double> times;
    energy::KMeansResult last;
    for (int rep = 0; rep < 3; ++rep) {
      energy::Stopwatch sw;
      sw.start();
      last = energy::kmeans_fit(X, c.k, 300, 1e-4, 10, true, 42);
      times.push_back(sw.elapsed_ms());
    }
    std::printf(
        ",\n    {\"stage\": \"kmeans\", \"dataset\": \"%s\", \"n_samples\": %zu, "
        "\"n_features\": %zu, \"k\": %d, \"time_ms\": %.4f, \"inertia\": %.3f, "
        "\"n_iterations\": %d, \"converged\": %s}",
        c.name, c.n, c.d, c.k, best_of(times), last.inertia,
        last.n_iterations, last.converged ? "true" : "false");
  }

  std::printf("\n  ]\n}\n");
  return 0;
}

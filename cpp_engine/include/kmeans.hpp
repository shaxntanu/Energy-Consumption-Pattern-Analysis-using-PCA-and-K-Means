#ifndef ENERGY_CPP_KMEANS_HPP
#define ENERGY_CPP_KMEANS_HPP

// K-Means clustering: Lloyd's algorithm with K-Means++ (or uniform random)
// initialization, configurable restarts, tolerance and iteration cap.
//
// The assignment step is parallelized with OpenMP where the compiler provides
// it (guarded by _OPENMP); the algorithm is identical with or without OpenMP,
// so results are deterministic for a given seed.

#include "utilities.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace energy {

struct KMeansResult {
  std::vector<int> labels;        // per-row cluster id, 0..k-1
  std::vector<double> centroids;  // row-major k x d
  double inertia = 0.0;           // sum of squared distances to assigned centroid
  int n_iterations = 0;           // Lloyd iterations of the winning restart
  int best_init = 0;              // index of the winning restart
  bool converged = false;         // false if the iteration cap was hit
};

// Fit K-Means on X (n x d, row-major). `n_init` restarts are run and the
// lowest-inertia solution is returned. `use_kmeanspp` selects K-Means++ D^2
// sampling; otherwise the first centroids are uniform random rows.
// Throws std::invalid_argument for malformed inputs (k < 2, k > n, empty X).
KMeansResult kmeans_fit(const Mat& X, int k, int max_iter = 300,
                        double tol = 1e-4, int n_init = 10,
                        bool use_kmeanspp = true, std::uint64_t seed = 42);

// Assign each row of X to the nearest centroid (used for predict()).
std::vector<int> kmeans_assign(const std::vector<double>& centroids, int k,
                               const Mat& X);

}  // namespace energy

#endif  // ENERGY_CPP_KMEANS_HPP

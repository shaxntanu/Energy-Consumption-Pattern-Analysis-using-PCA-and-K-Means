#include "kmeans.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace energy {
namespace {

inline double sq_dist(const double* a, const double* b, std::size_t d) {
  double s = 0.0;
  for (std::size_t j = 0; j < d; ++j) {
    const double t = a[j] - b[j];
    s += t * t;
  }
  return s;
}

// Assign every row to its nearest centroid; returns per-row labels and the
// total inertia (sum of squared distances). Serial reference used for the
// final pass so labels/inertia are always consistent with the returned
// centroids.
void assign_all(const Mat& X, const std::vector<double>& centroids, int k,
                std::vector<int>& labels, double& inertia) {
  const std::size_t n = X.rows;
  const std::size_t d = X.cols;
  labels.assign(n, 0);
  inertia = 0.0;
  for (std::size_t i = 0; i < n; ++i) {
    const double* xi = &X.data[i * d];
    int best = 0;
    double best_sq = sq_dist(xi, &centroids[0], d);
    for (int c = 1; c < k; ++c) {
      const double ds = sq_dist(xi, &centroids[static_cast<std::size_t>(c) * d], d);
      if (ds < best_sq) {
        best_sq = ds;
        best = c;
      }
    }
    labels[i] = best;
    inertia += best_sq;
  }
}

// K-Means++ initialization: first centroid uniform, then D^2-weighted
// sampling. Deterministic for a given Rng stream.
void init_kmeanspp(const Mat& X, int k, Rng& rng,
                   std::vector<double>& centroids) {
  const std::size_t n = X.rows;
  const std::size_t d = X.cols;

  const std::size_t first = rng.uniform_int(n);
  for (std::size_t j = 0; j < d; ++j) centroids[j] = X(first, j);

  std::vector<double> min_sq(n, std::numeric_limits<double>::infinity());
  for (int c = 1; c < k; ++c) {
    double total = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
      const double ds = sq_dist(&X.data[i * d], &centroids[static_cast<std::size_t>(c - 1) * d], d);
      if (ds < min_sq[i]) min_sq[i] = ds;
      total += min_sq[i];
    }
    double target = rng.uniform01() * total;
    std::size_t pick = n - 1;
    for (std::size_t i = 0; i < n; ++i) {
      target -= min_sq[i];
      if (target <= 0.0) {
        pick = i;
        break;
      }
    }
    for (std::size_t j = 0; j < d; ++j)
      centroids[static_cast<std::size_t>(c) * d + j] = X(pick, j);
  }
}

// Uniform random initialization.
void init_uniform(const Mat& X, int k, Rng& rng,
                  std::vector<double>& centroids) {
  const std::size_t n = X.rows;
  const std::size_t d = X.cols;
  for (int c = 0; c < k; ++c) {
    const std::size_t pick = rng.uniform_int(n);
    for (std::size_t j = 0; j < d; ++j)
      centroids[static_cast<std::size_t>(c) * d + j] = X(pick, j);
  }
}

// One Lloyd run from given centroids. Returns the result and whether it
// converged within max_iter. The assignment step is parallelized under
// _OPENMP using per-thread accumulation, then a serial merge; the update rule
// is identical with and without OpenMP, and the final labels/inertia are
// recomputed serially so the returned numbers are exact regardless of thread
// count.
KMeansResult lloyd(const Mat& X, int k, std::vector<double> centroids,
                   int max_iter, double tol) {
  const std::size_t n = X.rows;
  const std::size_t d = X.cols;
  const std::size_t kd = static_cast<std::size_t>(k) * d;

  KMeansResult res;
  res.centroids.assign(kd, 0.0);
  res.converged = false;

  std::vector<double> new_centroids(kd, 0.0);
  std::vector<std::size_t> counts(k, 0);
  std::vector<double> sums(kd, 0.0);

  for (int iter = 0; iter < max_iter; ++iter) {
    res.n_iterations = iter + 1;

    // --- assignment: nearest centroid, accumulating per-cluster sums --------
    std::fill(sums.begin(), sums.end(), 0.0);
    std::fill(counts.begin(), counts.end(), 0);

#ifdef _OPENMP
#pragma omp parallel
    {
      std::vector<double> local_sums(kd, 0.0);
      std::vector<std::size_t> local_counts(k, 0);
#pragma omp for schedule(static)
      for (std::int64_t i64 = 0; i64 < static_cast<std::int64_t>(n); ++i64) {
        const std::size_t i = static_cast<std::size_t>(i64);
        const double* xi = &X.data[i * d];
        int best = 0;
        double best_sq = sq_dist(xi, &centroids[0], d);
        for (int c = 1; c < k; ++c) {
          const double ds = sq_dist(xi, &centroids[static_cast<std::size_t>(c) * d], d);
          if (ds < best_sq) {
            best_sq = ds;
            best = c;
          }
        }
        res.labels[i] = best;
        ++local_counts[static_cast<std::size_t>(best)];
        for (std::size_t j = 0; j < d; ++j)
          local_sums[static_cast<std::size_t>(best) * d + j] += xi[j];
      }
#pragma omp critical
      {
        for (std::size_t c = 0; c < kd; ++c) sums[c] += local_sums[c];
        for (int c = 0; c < k; ++c) counts[static_cast<std::size_t>(c)] += local_counts[static_cast<std::size_t>(c)];
      }
    }
#else
    for (std::size_t i = 0; i < n; ++i) {
      const double* xi = &X.data[i * d];
      int best = 0;
      double best_sq = sq_dist(xi, &centroids[0], d);
      for (int c = 1; c < k; ++c) {
        const double ds = sq_dist(xi, &centroids[static_cast<std::size_t>(c) * d], d);
        if (ds < best_sq) {
          best_sq = ds;
          best = c;
        }
      }
      res.labels[i] = best;
      ++counts[static_cast<std::size_t>(best)];
      for (std::size_t j = 0; j < d; ++j)
        sums[static_cast<std::size_t>(best) * d + j] += xi[j];
    }
#endif

    // --- relocate empty clusters -------------------------------------------
    // A cluster that received no points is re-seeded with the point farthest
    // from its assigned centroid (the same strategy sklearn uses), so no mean
    // is ever computed from an empty set. Labels and inertia are recomputed
    // against the final centroids below, so this bookkeeping cannot leak.
    bool any_empty = false;
    for (int c = 0; c < k; ++c) {
      if (counts[static_cast<std::size_t>(c)] == 0) {
        any_empty = true;
        break;
      }
    }
    if (any_empty) {
      std::size_t far_i = 0;
      double far_sq = -1.0;
      for (std::size_t i = 0; i < n; ++i) {
        const double ds = sq_dist(&X.data[i * d],
                                  &centroids[static_cast<std::size_t>(res.labels[i]) * d], d);
        if (ds > far_sq) {
          far_sq = ds;
          far_i = i;
        }
      }
      for (int c = 0; c < k; ++c) {
        if (counts[static_cast<std::size_t>(c)] == 0) {
          for (std::size_t j = 0; j < d; ++j)
            sums[static_cast<std::size_t>(c) * d + j] = X(far_i, j);
          counts[static_cast<std::size_t>(c)] = 1;
          res.labels[far_i] = c;
        }
      }
    }

    // --- mean update -------------------------------------------------------
    double max_shift = 0.0;
    for (int c = 0; c < k; ++c) {
      const double inv = 1.0 / static_cast<double>(counts[static_cast<std::size_t>(c)]);
      for (std::size_t j = 0; j < d; ++j) {
        const double nc = sums[static_cast<std::size_t>(c) * d + j] * inv;
        const double shift = std::abs(nc - centroids[static_cast<std::size_t>(c) * d + j]);
        if (shift > max_shift) max_shift = shift;
        new_centroids[static_cast<std::size_t>(c) * d + j] = nc;
      }
    }
    centroids.swap(new_centroids);

    if (max_shift < tol) {
      res.converged = true;
      res.centroids = centroids;
      assign_all(X, res.centroids, k, res.labels, res.inertia);
      return res;
    }
  }

  res.centroids = centroids;
  assign_all(X, res.centroids, k, res.labels, res.inertia);
  return res;
}

}  // namespace

KMeansResult kmeans_fit(const Mat& X, int k, int max_iter, double tol,
                        int n_init, bool use_kmeanspp, std::uint64_t seed) {
  if (X.rows == 0 || X.cols == 0) {
    throw std::invalid_argument("kmeans_fit: empty input matrix");
  }
  if (k < 2) {
    throw std::invalid_argument("kmeans_fit: k must be at least 2");
  }
  if (static_cast<std::size_t>(k) > X.rows) {
    throw std::invalid_argument("kmeans_fit: k exceeds the number of rows");
  }
  if (max_iter < 1) throw std::invalid_argument("kmeans_fit: max_iter must be >= 1");
  if (n_init < 1) throw std::invalid_argument("kmeans_fit: n_init must be >= 1");

  const std::size_t d = X.cols;
  const std::size_t kd = static_cast<std::size_t>(k) * d;

  KMeansResult best;
  best.inertia = std::numeric_limits<double>::infinity();

  // Each restart gets its own seeded stream so runs are reproducible and
  // independent of one another.
  Rng master(seed);
  for (int init = 0; init < n_init; ++init) {
    Rng rng(master.next_u64());
    std::vector<double> centroids(kd, 0.0);
    if (use_kmeanspp) {
      init_kmeanspp(X, k, rng, centroids);
    } else {
      init_uniform(X, k, rng, centroids);
    }
    KMeansResult res = lloyd(X, k, std::move(centroids), max_iter, tol);
    res.best_init = init;
    if (res.inertia < best.inertia) {
      best = std::move(res);
    }
  }
  return best;
}

std::vector<int> kmeans_assign(const std::vector<double>& centroids, int k,
                               const Mat& X) {
  if (X.cols == 0) throw std::invalid_argument("kmeans_assign: empty X");
  if (centroids.size() != static_cast<std::size_t>(k) * X.cols) {
    throw std::invalid_argument("kmeans_assign: centroids size mismatch");
  }
  std::vector<int> labels;
  double inertia;
  assign_all(X, centroids, k, labels, inertia);
  (void)inertia;
  return labels;
}

}  // namespace energy

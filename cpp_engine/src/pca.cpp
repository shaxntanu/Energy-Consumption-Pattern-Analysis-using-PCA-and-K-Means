#include "pca.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace energy {
namespace {

// Symmetric Jacobi eigendecomposition (cyclic by-row sweeps).
//
// Iteratively zeroes the largest off-diagonal entries with Givens rotations
// until the matrix is diagonal to machine precision. This is the classical
// stable choice for a symmetric matrix of modest dimension (the pipeline's
// feature matrix is d ~ 50); it makes no external LAPACK dependency and
// converges quadratically near the end.
//
// In:  A = symmetric d x d matrix (row-major).
//      V = identity d x d; on return its columns are the orthonormal
//          eigenvectors.
// Out: A's diagonal holds the eigenvalues; A's off-diagonal entries ~ 0.
void jacobi_eigen(std::vector<double>& A, std::vector<double>& V, std::size_t d,
                  std::size_t max_sweeps, std::size_t* sweeps_used) {
  const double eps = 1e-14;
  for (std::size_t sweep = 0; sweep < max_sweeps; ++sweep) {
    // Frobenius norm of the off-diagonal block.
    double off = 0.0;
    for (std::size_t p = 0; p < d; ++p) {
      for (std::size_t q = p + 1; q < d; ++q) {
        const double a = A[p * d + q];
        off += a * a;
      }
    }
    if (std::sqrt(off) <= eps) {
      *sweeps_used = sweep;
      return;
    }
    for (std::size_t p = 0; p + 1 < d; ++p) {
      for (std::size_t q = p + 1; q < d; ++q) {
        double apq = A[p * d + q];
        if (std::abs(apq) < 1e-300) continue;
        const double app = A[p * d + p];
        const double aqq = A[q * d + q];
        // Rotation angle: tan(2theta) = 2*apq / (aqq - app). Solve for t = tan
        // without cancellation using the stable form with tau.
        const double tau = (aqq - app) / (2.0 * apq);
        const double t =
            (tau >= 0 ? 1.0 : -1.0) /
            (std::abs(tau) + std::sqrt(1.0 + tau * tau));
        const double c = 1.0 / std::sqrt(1.0 + t * t);
        const double s = t * c;

        // Rotate rows/columns p and q of A, keeping it symmetric.
        for (std::size_t k = 0; k < d; ++k) {
          if (k == p || k == q) continue;
          const double akp = A[k * d + p];
          const double akq = A[k * d + q];
          const double nkp = c * akp - s * akq;
          const double nkq = s * akp + c * akq;
          A[k * d + p] = nkp;
          A[k * d + q] = nkq;
          A[p * d + k] = nkp;
          A[q * d + k] = nkq;
        }
        const double new_pp = c * c * app - 2 * s * c * apq + s * s * aqq;
        const double new_qq = s * s * app + 2 * s * c * apq + c * c * aqq;
        A[p * d + p] = new_pp;
        A[q * d + q] = new_qq;
        A[p * d + q] = 0.0;
        A[q * d + p] = 0.0;

        // Accumulate the rotation in V (eigenvectors as columns).
        for (std::size_t k = 0; k < d; ++k) {
          const double vkp = V[k * d + p];
          const double vkq = V[k * d + q];
          V[k * d + p] = c * vkp - s * vkq;
          V[k * d + q] = s * vkp + c * vkq;
        }
      }
    }
  }
  *sweeps_used = max_sweeps;
}

}  // namespace

PcaResult pca_fit(const Mat& X, double variance_threshold, int max_components) {
  if (X.rows == 0 || X.cols == 0) {
    throw std::invalid_argument("pca_fit: empty input matrix");
  }
  if (!(variance_threshold > 0.0 && variance_threshold <= 1.0)) {
    throw std::invalid_argument(
        "pca_fit: variance_threshold must be in (0, 1]");
  }

  const std::size_t n = X.rows;
  const std::size_t d = X.cols;

  // Column means.
  std::vector<double> mean(d, 0.0);
  for (std::size_t i = 0; i < n; ++i) {
    for (std::size_t j = 0; j < d; ++j) mean[j] += X(i, j);
  }
  for (std::size_t j = 0; j < d; ++j) mean[j] /= static_cast<double>(n);

  // Covariance matrix C = Xc^T Xc / (n - 1), symmetric.
  std::vector<double> cov(d * d, 0.0);
  for (std::size_t i = 0; i < n; ++i) {
    for (std::size_t p = 0; p < d; ++p) {
      const double xp = X(i, p) - mean[p];
      for (std::size_t q = p; q < d; ++q) {
        cov[p * d + q] += xp * (X(i, q) - mean[q]);
      }
    }
  }
  const double denom = static_cast<double>(n) - 1.0;
  for (std::size_t p = 0; p < d; ++p) {
    for (std::size_t q = p; q < d; ++q) {
      cov[p * d + q] /= denom;
      cov[q * d + p] = cov[p * d + q];
    }
  }

  // Eigendecomposition.
  std::vector<double> V(d * d, 0.0);
  for (std::size_t j = 0; j < d; ++j) V[j * d + j] = 1.0;
  std::size_t sweeps = 0;
  jacobi_eigen(cov, V, d, 200, &sweeps);

  // Eigenvalues (on cov's diagonal) in descending order with their vectors.
  std::vector<std::size_t> order(d);
  for (std::size_t j = 0; j < d; ++j) order[j] = j;
  std::sort(order.begin(), order.end(), [&cov, d](std::size_t a, std::size_t b) {
    return cov[a * d + a] > cov[b * d + b];
  });

  PcaResult result;
  result.jacobi_sweeps = sweeps;
  result.mean = mean;
  result.eigen_values.resize(d);
  result.explained_variance_ratio.resize(d);
  result.cumulative_variance.resize(d);
  std::vector<double> eigvecs(d * d);  // reordered eigenvectors, columns

  double total_variance = 0.0;
  for (std::size_t j = 0; j < d; ++j) total_variance += cov[order[j] * d + order[j]];
  if (total_variance <= 0.0) {
    throw std::runtime_error("pca_fit: zero total variance in input matrix");
  }

  double cum = 0.0;
  for (std::size_t j = 0; j < d; ++j) {
    const double ev = cov[order[j] * d + order[j]];
    result.eigen_values[j] = ev;
    const double ratio = ev / total_variance;
    result.explained_variance_ratio[j] = ratio;
    cum += ratio;
    result.cumulative_variance[j] = cum;
    for (std::size_t i = 0; i < d; ++i) eigvecs[i * d + j] = V[i * d + order[j]];
  }

  // Apply sklearn's svd_flip convention to the reordered eigenvectors, so
  // signs agree with the reference implementation (PCA's components_).
  // Sign is decided by U = Xc V / S (the left singular vectors); sklearn
  // flips a direction so its largest-magnitude U entry is positive and applies
  // the same sign to the corresponding V row.
  std::vector<double> centered_X(n * d);
  for (std::size_t i = 0; i < n; ++i)
    for (std::size_t j = 0; j < d; ++j) centered_X[i * d + j] = X(i, j) - mean[j];

  for (std::size_t j = 0; j < d; ++j) {
    const double ev = std::max(result.eigen_values[j], 1e-300);
    // Find the row of Xc V with the largest magnitude (max |U[i, j]|).
    std::size_t best_i = 0;
    double best_val = -1.0;
    for (std::size_t i = 0; i < n; ++i) {
      double dot = 0.0;
      for (std::size_t k = 0; k < d; ++k)
        dot += centered_X[i * d + k] * eigvecs[k * d + j];
      const double uij = dot / std::sqrt(ev * denom);
      const double mag = std::abs(uij);
      if (mag > best_val) {
        best_val = mag;
        best_i = i;
      }
    }
    // sign of U[best_i, j]
    double sgn = 0.0;
    for (std::size_t k = 0; k < d; ++k)
      sgn += centered_X[best_i * d + k] * eigvecs[k * d + j];
    if (sgn < 0.0) {
      for (std::size_t k = 0; k < d; ++k) eigvecs[k * d + j] = -eigvecs[k * d + j];
    }
  }

  // Retained component count: smallest k with cumulative variance >= threshold.
  int n_components = d;
  for (std::size_t k = 0; k < d; ++k) {
    if (result.cumulative_variance[k] >= variance_threshold) {
      n_components = static_cast<int>(k + 1);
      break;
    }
  }
  if (max_components > 0 && n_components > max_components) {
    n_components = max_components;
  }
  result.n_components = n_components;

  result.components.assign(static_cast<std::size_t>(n_components) * d, 0.0);
  for (int c = 0; c < n_components; ++c) {
    for (std::size_t k = 0; k < d; ++k) {
      result.components[static_cast<std::size_t>(c) * d + k] =
          eigvecs[k * d + static_cast<std::size_t>(c)];
    }
  }

  // Scores: X_centered @ components^T (n x n_components).
  result.scores.assign(static_cast<std::size_t>(n) *
                           static_cast<std::size_t>(n_components),
                       0.0);
  for (std::size_t i = 0; i < n; ++i) {
    for (int c = 0; c < n_components; ++c) {
      double dot = 0.0;
      for (std::size_t k = 0; k < d; ++k)
        dot += centered_X[i * d + k] * eigvecs[k * d + static_cast<std::size_t>(c)];
      result.scores[i * static_cast<std::size_t>(n_components) +
                    static_cast<std::size_t>(c)] = dot;
    }
  }

  return result;
}

Mat pca_transform(const std::vector<double>& mean,
                  const std::vector<double>& components, int n_components,
                  const Mat& X) {
  if (mean.size() != X.cols) {
    throw std::invalid_argument("pca_transform: mean length != X.cols");
  }
  const std::size_t k = static_cast<std::size_t>(n_components);
  if (components.size() != k * X.cols) {
    throw std::invalid_argument("pca_transform: components size mismatch");
  }
  Mat out(X.rows, k, 0.0);
  for (std::size_t i = 0; i < X.rows; ++i) {
    for (std::size_t c = 0; c < k; ++c) {
      double dot = 0.0;
      for (std::size_t j = 0; j < X.cols; ++j) {
        dot += (X(i, j) - mean[j]) *
               components[c * X.cols + j];
      }
      out(i, c) = dot;
    }
  }
  return out;
}

}  // namespace energy

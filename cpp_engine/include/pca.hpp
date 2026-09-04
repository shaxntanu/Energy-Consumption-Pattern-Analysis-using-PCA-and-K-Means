#ifndef ENERGY_CPP_PCA_HPP
#define ENERGY_CPP_PCA_HPP

// Principal Component Analysis via the covariance matrix and a symmetric
// Jacobi eigendecomposition.
//
// The pipeline's reference implementation is scikit-learn (SVD based). This
// engine is a performance-oriented alternative that produces the same
// mathematical result: eigenvalues of the centered covariance matrix are the
// explained variances (S^2 / (n - 1)), and the eigenvectors are the principal
// directions. Component signs are normalized to scikit-learn's `svd_flip`
// convention (each direction's largest-magnitude element positive) so loadings
// and projections line up with the reference up to floating-point error.

#include "utilities.hpp"

#include <cstddef>
#include <vector>

namespace energy {

struct PcaResult {
  int n_components = 0;      // number of retained directions
  std::vector<double> mean;  // per-feature mean of the fitted matrix (d)
  // Retained principal directions, row-major n_components x d, sign-normalized
  // to match sklearn's svd_flip convention.
  std::vector<double> components;
  std::vector<double> eigen_values;    // full spectrum, descending (d)
  std::vector<double> explained_variance_ratio;  // full spectrum (d)
  std::vector<double> cumulative_variance;       // full spectrum (d)
  std::vector<double> scores;                    // centered X projected, n x n_components
  std::size_t jacobi_sweeps = 0;       // sweeps until convergence (diagnostic)
};

// Fit PCA on X (n x d, row-major). The matrix is centered internally (its mean
// is returned). The retained count is the smallest k whose cumulative explained
// variance reaches `variance_threshold`, matching the pipeline's selection rule;
// if the threshold is never reached all d components are kept. When
// `max_components` > 0 the count is capped at that value.
PcaResult pca_fit(const Mat& X, double variance_threshold = 0.95,
                  int max_components = 0);

// Project an n x d matrix onto an existing fit (mean + retained components).
// Returns an n x n_components matrix.
Mat pca_transform(const std::vector<double>& mean,
                  const std::vector<double>& components, int n_components,
                  const Mat& X);

}  // namespace energy

#endif  // ENERGY_CPP_PCA_HPP

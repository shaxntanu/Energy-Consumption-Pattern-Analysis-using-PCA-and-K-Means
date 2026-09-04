// pybind11 bindings for the C++ performance engine.
//
// The module is named `energy_cpp` and exposes three functions:
//
//   pca_fit(X, variance_threshold, max_components)
//       X is a flat, row-major list/array of length n_rows * n_cols.
//   kmeans_fit(X, k, max_iter, tol, n_init, init, seed)
//   compile_info()
//
// Flat lists are used for the matrix input instead of a numpy-array-typed
// binding: it keeps the module free of a numpy build dependency, and the
// conversion cost is negligible next to the algorithms being timed. The Python
// bridge (src/cpp_bridge.py) reshapes results back into arrays.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../include/kmeans.hpp"
#include "../include/pca.hpp"
#include "../include/utilities.hpp"

#include <string>

namespace py = pybind11;

namespace {

py::dict pca_fit_py(const std::vector<double>& X, std::size_t n_rows,
                    std::size_t n_cols, double variance_threshold,
                    int max_components) {
  if (X.size() != n_rows * n_cols) {
    throw std::invalid_argument("pca_fit: X length does not match n_rows*n_cols");
  }
  energy::Mat m(n_rows, n_cols);
  m.data = X;
  const energy::PcaResult r = energy::pca_fit(m, variance_threshold, max_components);

  py::dict out;
  out["n_components"] = r.n_components;
  out["mean"] = r.mean;
  out["components"] = r.components;          // n_components * n_cols
  out["eigen_values"] = r.eigen_values;
  out["explained_variance_ratio"] = r.explained_variance_ratio;
  out["cumulative_variance"] = r.cumulative_variance;
  out["scores"] = r.scores;                  // n_rows * n_components
  out["jacobi_sweeps"] = r.jacobi_sweeps;
  return out;
}

py::dict kmeans_fit_py(const std::vector<double>& X, std::size_t n_rows,
                       std::size_t n_cols, int k, int max_iter, double tol,
                       int n_init, const std::string& init, std::uint64_t seed) {
  if (X.size() != n_rows * n_cols) {
    throw std::invalid_argument("kmeans_fit: X length does not match n_rows*n_cols");
  }
  energy::Mat m(n_rows, n_cols);
  m.data = X;

  bool use_kmeanspp = true;
  if (init == "kmeanspp" || init == "k-means++" || init == "kmeans++") {
    use_kmeanspp = true;
  } else if (init == "random") {
    use_kmeanspp = false;
  } else {
    throw std::invalid_argument("kmeans_fit: init must be 'kmeanspp' or 'random'");
  }

  const energy::KMeansResult r =
      energy::kmeans_fit(m, k, max_iter, tol, n_init, use_kmeanspp, seed);

  py::dict out;
  out["labels"] = r.labels;
  out["centroids"] = r.centroids;   // k * n_cols
  out["inertia"] = r.inertia;
  out["n_iterations"] = r.n_iterations;
  out["best_init"] = r.best_init;
  out["converged"] = r.converged;
  out["k"] = k;
  out["seed"] = seed;
  out["n_init"] = n_init;
  out["init"] = init;
  out["n_components"] = static_cast<int>(n_cols);
  return out;
}

py::dict compile_info_py() {
  py::dict d;
  d["library"] = "energy_cpp";
  d["description"] =
      "C++ performance engine: PCA via symmetric Jacobi eigendecomposition, "
      "K-Means via Lloyd's algorithm with K-Means++ initialization. "
      "The Python/scikit-learn implementation remains the scientific reference.";

#ifdef _OPENMP
  d["openmp"] = true;
  d["openmp_version"] = _OPENMP;
#else
  d["openmp"] = false;
#endif

#ifdef _MSC_VER
  d["compiler"] = "MSVC";
  d["compiler_version"] = std::to_string(_MSC_VER);
#elif defined(__clang__)
  d["compiler"] = "clang";
  d["compiler_version"] = __VERSION__;
#elif defined(__GNUC__)
  d["compiler"] = "gcc";
  d["compiler_version"] = __VERSION__;
#else
  d["compiler"] = "unknown";
  d["compiler_version"] = "unknown";
#endif

  d["cxx_standard"] = std::to_string(__cplusplus);
  return d;
}

}  // namespace

PYBIND11_MODULE(energy_cpp, m) {
  m.doc() = "C++ performance engine for PCA and K-Means (pybind11 bindings).";

  m.def("pca_fit", &pca_fit_py,
        py::arg("X"), py::arg("n_rows"), py::arg("n_cols"),
        py::arg("variance_threshold") = 0.95, py::arg("max_components") = 0,
        "Fit PCA on a flat row-major matrix X (n_rows x n_cols). Returns a "
        "dict with n_components, mean, components, eigen_values, "
        "explained_variance_ratio, cumulative_variance and scores.");

  m.def("kmeans_fit", &kmeans_fit_py,
        py::arg("X"), py::arg("n_rows"), py::arg("n_cols"), py::arg("k"),
        py::arg("max_iter") = 300, py::arg("tol") = 1e-4,
        py::arg("n_init") = 10, py::arg("init") = "kmeanspp",
        py::arg("seed") = 42,
        "Fit K-Means on a flat row-major matrix X (n_rows x n_cols). Returns "
        "a dict with labels, centroids, inertia, n_iterations, best_init and "
        "converged.");

  m.def("compile_info", &compile_info_py,
        "Return a dict describing how this module was compiled (compiler, "
        "C++ standard, OpenMP).");
}

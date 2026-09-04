#ifndef ENERGY_CPP_UTILITIES_HPP
#define ENERGY_CPP_UTILITIES_HPP

// Shared containers and helpers for the C++ performance engine.
//
// The engine deliberately avoids external numeric dependencies: PCA uses a
// symmetric Jacobi eigendecomposition (a classical, numerically stable method,
// not a hand-rolled unstable substitute), and K-Means uses Lloyd's algorithm
// with K-Means++ initialization. Everything here is self-contained so the
// engine builds with any C++17 compiler on any platform.
//
// Layout convention: matrices are row-major, data[i * cols + j], so a flat
// buffer passed in from Python maps directly onto the struct without a copy.

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace energy {

// ---------------------------------------------------------------------------
// Dense row-major matrix
// ---------------------------------------------------------------------------
struct Mat {
  std::size_t rows = 0;
  std::size_t cols = 0;
  std::vector<double> data;

  Mat() = default;
  Mat(std::size_t r, std::size_t c, double fill = 0.0)
      : rows(r), cols(c), data(r * c, fill) {}

  double& operator()(std::size_t i, std::size_t j) { return data[i * cols + j]; }
  const double& operator()(std::size_t i, std::size_t j) const {
    return data[i * cols + j];
  }

  void require_same_layout(const Mat& other, const char* what) const {
    if (rows != other.rows || cols != other.cols) {
      throw std::invalid_argument(std::string(what) +
          ": dimension mismatch (" + std::to_string(rows) + "x" +
          std::to_string(cols) + " vs " + std::to_string(other.rows) + "x" +
          std::to_string(other.cols) + ")");
    }
  }
};

// ---------------------------------------------------------------------------
// Deterministic, seedable RNG (SplitMix64).
// ---------------------------------------------------------------------------
// One engine object per algorithm invocation, seeded by the caller, so every
// K-Means run (and therefore every benchmark) is reproducible bit-for-bit on
// the same platform. SplitMix64 is a small, well-tested generator; it is
// sufficient here because K-Means only needs uniform draws.
class Rng {
 public:
  explicit Rng(std::uint64_t seed) : state_(seed) {}

  std::uint64_t next_u64() {
    state_ += 0x9E3779B97F4A7C15ull;
    std::uint64_t z = state_;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
  }

  // Uniform in [0, 1) with 53 bits of entropy.
  double uniform01() {
    return static_cast<double>(next_u64() >> 11) * (1.0 / 9007199254740992.0);
  }

  // Uniform integer in [0, n). n must be > 0.
  std::size_t uniform_int(std::size_t n) {
    if (n == 0) throw std::invalid_argument("Rng::uniform_int: n must be > 0");
    double r = uniform01() * static_cast<double>(n);
    std::size_t v = static_cast<std::size_t>(r);
    return v < n ? v : n - 1;  // guard against float rounding to exactly n
  }

 private:
  std::uint64_t state_;
};

// ---------------------------------------------------------------------------
// Wall-clock stopwatch (steady clock, immune to system clock jumps).
// ---------------------------------------------------------------------------
class Stopwatch {
 public:
  void start() { start_ = std::chrono::steady_clock::now(); }
  double elapsed_seconds() const {
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration<double>(now - start_).count();
  }
  double elapsed_ms() const { return elapsed_seconds() * 1e3; }

 private:
  std::chrono::steady_clock::time_point start_{};
};

}  // namespace energy

#endif  // ENERGY_CPP_UTILITIES_HPP

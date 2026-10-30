# Benchmark and comparison evidence

## Synthetic representation comparison

The 365-day replication uses 20 independent generator seeds (100–119), 200 consumers per run, and a fixed K=4 comparison. Intervals resample the 20 generator runs; they describe variation under this generator and are not confidence intervals for a real-household population.

| Representation | ARI mean | 95% seed-bootstrap interval | NMI mean | Silhouette mean |
|---|---:|---:|---:|---:|
| Normalized 24-bin profile, no PCA | 0.693 | 0.655–0.732 | 0.719 | 0.331 |
| 24-bin profile + PCA | 0.693 | 0.657–0.729 | 0.718 | 0.346 |
| 51 behavioral features, no PCA | 0.851 | 0.825–0.875 | 0.846 | 0.299 |
| 51 behavioral features + PCA | 0.854 | 0.825–0.880 | 0.848 | 0.321 |

The paired ARI difference between the 51-feature PCA method and the 24-bin no-PCA baseline is 0.161 (95% seed-bootstrap interval 0.125–0.201). When K is selected independently per run, the 51-feature PCA method selects K=3 in 7/20 runs and K=4 in 13/20; its ARI mean is 0.778 (0.719–0.836). This is evidence on the controlled generator only.

**Reproduce:** `python research/run_synthetic_365_replication.py`. Raw runs, summaries, parameters, and figure are under `outputs/research_additions/` and `outputs/figures/research_additions/`.

## Optional Python/C++ kernel benchmark

The repository includes an executed benchmark in `outputs/benchmarks/benchmark_results.md` and machine-readable JSON/CSV sidecars. The recorded run used best-of-three timing after one warmup on identical matrices, Python 3.14.0, Windows 11, MSVC 19.51, and OpenMP. The CPU field records only a generic Intel family/model string, not a retail model or clock; results should not be treated as portable.

| Dataset | Stage | Python (ms) | C++ (ms) | Relative result |
|---|---|---:|---:|---|
| Small (200 × 51) | PCA | 2.10 | 3.20 | C++ slower |
| Small (200 × 10) | K-Means | 24.42 | 4.36 | 5.60× faster in this run |
| Medium (2,000 × 51) | PCA | 9.18 | 11.99 | C++ slower |
| Medium (2,000 × 10) | K-Means | 50.74 | 7.87 | 6.45× faster in this run |
| Large (20,000 × 51) | PCA | 47.04 | 105.67 | C++ slower |
| Large (20,000 × 10) | K-Means | 52.08 | 41.98 | 1.24× faster in this run |
| Wide (2,000 × 128) | PCA | 50.73 | 174.07 | C++ slower |

On the 30-day end-to-end scratch run, Python took 7.00 s and C++ took 5.29 s (1.32× in that run); label ARI was 1.000. PCA matched component counts and had maximum absolute component differences below 3e-13 in the recorded cases. K-Means agreement was high, but the small case had ARI 0.987 and a small inertia difference, so implementations are not asserted to be bit-identical.

These are one machine's archived measurements, not a general speed guarantee. Repeat the benchmark on a named, documented machine before comparing releases. The Python/scikit-learn implementation remains the scientific reference.

**Reproduce:** `python src/run_cpp_benchmark.py` (supports `--quick` and `--e2e`). The optional extension must be built first; the runner records a not-executed state if it is unavailable.

## Interpretation limits

- Silhouette and ARI measure different properties; a higher silhouette is not automatically a better behavioral segmentation.
- The synthetic archetypes are known by construction and may favor the generator's own representation.
- UCI and London are unlabeled measured-data analyses, not benchmarks against household ground truth.
- Archived C++ timings have limited hardware detail and a single environment. Do not generalize them to other machines or workloads.


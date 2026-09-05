# Python (scikit-learn) vs C++ (energy_cpp) benchmark

- Status: **executed**
- Config hash: `99c7a6631340d301`
- Engine: `energy_cpp` (compiler MSVC, OpenMP True)

| dataset | stage | engine | time (ms) |
|---|---|---|---|
| small | pca | python | 2.10 |
| small | pca | cpp | 3.20 |
| small | kmeans | python | 24.42 |
| small | kmeans | cpp | 4.36 |
| medium | pca | python | 9.18 |
| medium | pca | cpp | 11.99 |
| medium | kmeans | python | 50.74 |
| medium | kmeans | cpp | 7.87 |
| large | pca | python | 47.04 |
| large | pca | cpp | 105.67 |
| large | kmeans | python | 52.08 |
| large | kmeans | cpp | 41.98 |
| wide | pca | python | 50.73 |
| wide | pca | cpp | 174.07 |

### Agreement

- `pca_small`: `{'n_components_match': True, 'python_n_components': 10, 'cpp_n_components': 10, 'variance_retained_diff': 2.220446049250313e-16, 'max_abs_component_diff': 2.5590640717609858e-14}`
- `kmeans_small`: `{'ari': 0.9866936870852953, 'ami': 0.9818670131951398, 'inertia_relative_diff': 8.299015625488065e-05, 'python_inertia': 3911.129183290934, 'cpp_inertia': 3911.4537685129885, 'python_n_iterations': 5, 'cpp_n_iterations': 8}`
- `pca_medium`: `{'n_components_match': True, 'python_n_components': 10, 'cpp_n_components': 10, 'variance_retained_diff': 2.220446049250313e-16, 'max_abs_component_diff': 7.19979631469414e-14}`
- `kmeans_medium`: `{'ari': 1.0, 'ami': 1.0, 'inertia_relative_diff': 0.0, 'python_inertia': 39052.16008231073, 'cpp_inertia': 39052.16008231073, 'python_n_iterations': 6, 'cpp_n_iterations': 10}`
- `pca_large`: `{'n_components_match': True, 'python_n_components': 10, 'cpp_n_components': 10, 'variance_retained_diff': 7.771561172376096e-16, 'max_abs_component_diff': 5.96189764223709e-14}`
- `kmeans_large`: `{'ari': 1.0, 'ami': 0.9999999999999999, 'inertia_relative_diff': 4.605600411303781e-15, 'python_inertia': 391792.01996959146, 'cpp_inertia': 391792.01996959327, 'python_n_iterations': 5, 'cpp_n_iterations': 5}`
- `pca_wide`: `{'n_components_match': True, 'python_n_components': 118, 'cpp_n_components': 118, 'variance_retained_diff': 2.220446049250313e-16, 'max_abs_component_diff': 2.9106925203414846e-13}`

### Speedups

- PCA: `{'small': 0.6554244070492165, 'medium': 0.7654820400890608, 'large': 0.4451703145504948, 'wide': 0.2914297168226812}`
- K-Means: `{'small': 5.597749375810483, 'medium': 6.449224005875682, 'large': 1.2408060767266527}`

### End-to-end pipeline

- Python 7.00s vs C++ 5.29s (1.32x), labels ARI 1.0000
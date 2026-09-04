# Python (scikit-learn) vs C++ (energy_cpp) benchmark

- Status: **executed**
- Config hash: `99c7a6631340d301`
- Engine: `energy_cpp` (compiler MSVC, OpenMP True)

| dataset | stage | engine | time (ms) |
|---|---|---|---|
| small | pca | python | 2.93 |
| small | pca | cpp | 7.20 |
| small | kmeans | python | 38.35 |
| small | kmeans | cpp | nan |

### Agreement

- `pca_small`: `{'n_components_match': True, 'python_n_components': 10, 'cpp_n_components': 10, 'variance_retained_diff': 2.220446049250313e-16, 'max_abs_component_diff': 2.5590640717609858e-14}`
- `kmeans_small`: `{'status': 'cpp_crashed', 'note': 'C++ K-Means segfaulted; results not comparable'}`

### Speedups

- PCA: `{'small': 0.4071659891224621}`
- K-Means: `{}`
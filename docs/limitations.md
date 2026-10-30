# Limitations

## Data and sampling

- The flagship benchmark uses generated profiles. Its archetypes and noise model are designed; recovery does not establish validity on real household populations.
- The UCI ElectricityLoadDiagrams data are anonymized client series. Client IDs are not treated as household identities, and behavioral labels are unavailable.
- The London analysis uses 11 complete CSV members from a locally available truncated archive. Its 292 coverage-eligible households are a selected subset, not a representative sample of all source households.
- The selected London K=3 solution contains a singleton cluster. The result is retained as a caveat, not presented as a stable household segment.
- Source schemas, sampling periods, and coverage differ, so UCI and London results are not directly pooled.

## Method and inference

- PCA, K-Means, and profile summaries are descriptive unsupervised methods; they do not identify causal drivers.
- The 51 behavioral features are used to create the partition. Differences in those features after clustering are post-selection descriptions, not independent validation.
- ARI/NMI against archetype labels are available only for synthetic data. Measured-data runs do not have equivalent ground truth.
- Seed-bootstrap intervals in the replication quantify variability across the chosen generator seeds. They do not account for model misspecification or real-world sampling uncertainty.
- The retrospective load-shifting analyses assume a specified flexible fraction and destination time window. They do not measure participant response, causal effects, costs, rebound, or energy savings.
- A simple evening peak reduction can create a higher peak in another time window, as shown in the included counterfactual comparisons.

## Engineering and operations

- The Streamlit application recomputes a research pipeline; it is not an operational utility tool and has no availability or latency SLA.
- The static Vercel app displays committed artifacts. Its content can lag behind the latest analysis until artifacts are regenerated and deployed.
- The optional C++ extension requires a compatible local compiler and ABI. The Python implementation is the supported reference fallback.
- There is no broad performance/load test, formal threat model, or external security audit.
- The project does not include a production data ingestion service, authentication layer, inference API, demand-response control, billing integration, or monitoring system.


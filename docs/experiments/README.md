# Experimental record

These studies are research analyses, not production evaluations. Each report should be read with its script and JSON/CSV sidecars; results are not interchangeable across datasets.

| Study | Question and setup | Evidence |
|---|---|---|
| Synthetic 365-day replication | Does the 51-feature representation recover the generator's archetypes across independent data/model seeds, compared with normalized 24-bin profiles? 20 runs, 200 consumers per run, fixed K=4 plus per-run K selection. | [Report](../../outputs/reports/synthetic_365_seed_study.md), [script](../../research/run_synthetic_365_replication.py), [machine-readable results](../../outputs/research_additions/) |
| UCI load diagrams | How stable are client partitions across restarts and chronological windows for the available 2012 sample? No behavioral labels. | [Report](../../outputs/reports/real_world_uci_load_diagrams_2012.md), [script](../../research/run_uci_load_diagrams_validation.py), [source notes](../../dataset/real%20world/README.md) |
| London households, 2013 | How do coverage-filtered household profiles cluster, and how much do monthly partitions agree with the annual partition? The input was a truncated archive subset. | [Report](../../outputs/reports/london_household_validation_2013.md), [script](../../research/run_london_household_validation.py) |
| UCI load-shift scenario | Under an explicit 10% flexible-load assumption, how does shifting evening energy compare with an equal-energy control? | [Report](../../outputs/reports/demand_response_uci_2012.md), [script](../../research/simulate_demand_response_uci.py) |

## Interpretation rules

- Synthetic recovery metrics are checked against generator labels and say nothing directly about real-household classification.
- UCI/London cluster labels are exploratory; no external labels are available.
- The load-shift outputs are simulated counterfactuals, not observed or causal effects.
- Reports record run settings, input provenance, and limitations. Re-run a study before comparing results after code or data changes.


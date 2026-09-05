# Recommendations

## What this file is

Each row below was produced by comparing one measured cluster metric with the
same metric across all consumers. A row appears only when the cluster sits at
least 15 percent above or below the population value.

Three things this file does not contain:

- Savings figures. The analysis measures when energy is used. It contains no
  information about what would happen if that changed.
- Causal claims. Cluster membership is an observed association, so every action
  below is something to test rather than something known to work.
- Findings about real households. The underlying data is synthetic.

Priority reflects only how far the cluster sits from the population: high is a
deviation of 30 percent or more, medium 15 percent or more.

## Cluster 0: Evening-Peaking

### 1. Weekend (medium priority)

- Observation: This cluster's weekend timing differs more from its weekday timing than is typical.
- Evidence: weekend_shape_distance is 0.088 against a population 0.073, 21% above the population value.
- Cluster value: 0.0880
- Population baseline: 0.0727
- Action: A single fixed daily schedule fits this group poorly. If a time-of-use scheme is applied, evaluate weekday and weekend windows separately.

### 2. Variability (medium priority)

- Observation: Consumption within this cluster varies more from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.623 against a population 0.527, 18% above the population value.
- Cluster value: 0.6232
- Population baseline: 0.5266
- Action: Short-term forecasts for this group will carry more error, so allow for that when sizing reserve or planning storage. Sub-metering would show whether the variation comes from one device or from many.

## Cluster 1: Flat All-Day

### 1. Timing (high priority)

- Observation: This cluster draws an unusually large share of its energy overnight (00:00 to 06:00), when household activity is normally low.
- Evidence: night_share is 20.6% against a population 15.0%, 37% above the population value.
- Cluster value: 0.2061
- Population baseline: 0.1504
- Action: Investigate standing load rather than behaviour. A high overnight share usually points at equipment that runs continuously, which responds to efficiency measures and not to scheduling.

### 2. Peak Management (high priority)

- Observation: This cluster stays close to its own average all day, with a lower peak-to-average ratio than the population.
- Evidence: peak_to_avg_ratio is 3.522 against a population 5.597, 37% below the population value.
- Cluster value: 3.5222
- Population baseline: 5.5966
- Action: There is little peak to manage here. Any reduction has to come from the level of the base load, not from moving it in time.

### 3. Variability (high priority)

- Observation: Consumption within this cluster is steadier from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.278 against a population 0.527, 47% below the population value.
- Cluster value: 0.2780
- Population baseline: 0.5266
- Action: Predictable demand makes this group a reasonable baseline for forecasting and for measuring the effect of any intervention on the other clusters.

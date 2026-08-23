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

## Cluster 1: Flat All-Day

### 1. Timing (high priority)

- Observation: This cluster draws an unusually large share of its energy overnight (00:00 to 06:00), when household activity is normally low.
- Evidence: night_share is 20.7% against a population 15.8%, 31% above the population value.
- Cluster value: 0.2068
- Population baseline: 0.1581
- Action: Investigate standing load rather than behaviour. A high overnight share usually points at equipment that runs continuously, which responds to efficiency measures and not to scheduling.

### 2. Peak Management (high priority)

- Observation: This cluster stays close to its own average all day, with a lower peak-to-average ratio than the population.
- Evidence: peak_to_avg_ratio is 3.525 against a population 5.502, 36% below the population value.
- Cluster value: 3.5249
- Population baseline: 5.5016
- Action: There is little peak to manage here. Any reduction has to come from the level of the base load, not from moving it in time.

### 3. Variability (high priority)

- Observation: Consumption within this cluster is steadier from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.274 against a population 0.511, 46% below the population value.
- Cluster value: 0.2737
- Population baseline: 0.5109
- Action: Predictable demand makes this group a reasonable baseline for forecasting and for measuring the effect of any intervention on the other clusters.

## Cluster 2: Evening-Peaking

### 1. Timing (high priority)

- Observation: A larger share of this cluster's daily energy falls in the evening block (18:00 to 24:00) than for the population.
- Evidence: evening_share is 38.2% against a population 29.1%, 32% above the population value.
- Cluster value: 0.3823
- Population baseline: 0.2906
- Action: Check which evening loads are deferrable, such as water heating, laundry and dishwashing, and test whether a time-of-use signal moves them. Measure the effect on a subset before assuming any change.

### 2. Weekend (high priority)

- Observation: This cluster's weekend timing differs more from its weekday timing than is typical.
- Evidence: weekend_shape_distance is 0.120 against a population 0.071, 68% above the population value.
- Cluster value: 0.1198
- Population baseline: 0.0714
- Action: A single fixed daily schedule fits this group poorly. If a time-of-use scheme is applied, evaluate weekday and weekend windows separately.

### 3. Variability (high priority)

- Observation: Consumption within this cluster varies more from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.668 against a population 0.511, 31% above the population value.
- Cluster value: 0.6677
- Population baseline: 0.5109
- Action: Short-term forecasts for this group will carry more error, so allow for that when sizing reserve or planning storage. Sub-metering would show whether the variation comes from one device or from many.

### 4. Peak Management (medium priority)

- Observation: This cluster reaches a higher peak relative to its own average than the population does.
- Evidence: peak_to_avg_ratio is 7.078 against a population 5.502, 29% above the population value.
- Cluster value: 7.0779
- Population baseline: 5.5016
- Action: This group contributes disproportionately to peak demand, so it is where demand limiting or a capacity-based tariff would have the most effect. Confirm the peaks are coincident with system peak before acting.

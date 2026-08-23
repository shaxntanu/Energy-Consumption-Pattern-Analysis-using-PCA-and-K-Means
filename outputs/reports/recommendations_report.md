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

## Cluster 0: Flat All-Day

### 1. Timing (high priority)

- Observation: This cluster draws an unusually large share of its energy overnight (00:00 to 06:00), when household activity is normally low.
- Evidence: night_share is 20.9% against a population 15.8%, 32% above the population value.
- Cluster value: 0.2091
- Population baseline: 0.1581
- Action: Investigate standing load rather than behaviour. A high overnight share usually points at equipment that runs continuously, which responds to efficiency measures and not to scheduling.

### 2. Peak Management (high priority)

- Observation: This cluster stays close to its own average all day, with a lower peak-to-average ratio than the population.
- Evidence: peak_to_avg_ratio is 3.356 against a population 5.502, 39% below the population value.
- Cluster value: 3.3562
- Population baseline: 5.5016
- Action: There is little peak to manage here. Any reduction has to come from the level of the base load, not from moving it in time.

### 3. Variability (high priority)

- Observation: Consumption within this cluster is steadier from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.253 against a population 0.511, 50% below the population value.
- Cluster value: 0.2535
- Population baseline: 0.5109
- Action: Predictable demand makes this group a reasonable baseline for forecasting and for measuring the effect of any intervention on the other clusters.

## Cluster 1: Evening-Peaking Weekend-Heavy

### 1. Weekend (high priority)

- Observation: This cluster's weekend timing differs more from its weekday timing than is typical.
- Evidence: weekend_shape_distance is 0.102 against a population 0.071, 43% above the population value.
- Cluster value: 0.1019
- Population baseline: 0.0714
- Action: A single fixed daily schedule fits this group poorly. If a time-of-use scheme is applied, evaluate weekday and weekend windows separately.

### 2. Timing (medium priority)

- Observation: A larger share of this cluster's daily energy falls in the evening block (18:00 to 24:00) than for the population.
- Evidence: evening_share is 35.2% against a population 29.1%, 21% above the population value.
- Cluster value: 0.3520
- Population baseline: 0.2906
- Action: Check which evening loads are deferrable, such as water heating, laundry and dishwashing, and test whether a time-of-use signal moves them. Measure the effect on a subset before assuming any change.

### 3. Peak Management (medium priority)

- Observation: This cluster reaches a higher peak relative to its own average than the population does.
- Evidence: peak_to_avg_ratio is 6.467 against a population 5.502, 18% above the population value.
- Cluster value: 6.4665
- Population baseline: 5.5016
- Action: This group contributes disproportionately to peak demand, so it is where demand limiting or a capacity-based tariff would have the most effect. Confirm the peaks are coincident with system peak before acting.

### 4. Weekend (medium priority)

- Observation: This cluster uses more energy on weekend days relative to weekdays than the population does.
- Evidence: weekend_ratio is 1.204 against a population 1.036, 16% above the population value.
- Cluster value: 1.2036
- Population baseline: 1.0363
- Action: Weekend exposure matters for this group, so check whether the tariff in force distinguishes weekends. A weekday-only time-of-use schedule would miss most of their consumption.

### 5. Variability (medium priority)

- Observation: Consumption within this cluster varies more from hour to hour than the population average.
- Evidence: coefficient_of_variation is 0.620 against a population 0.511, 21% above the population value.
- Cluster value: 0.6203
- Population baseline: 0.5109
- Action: Short-term forecasts for this group will carry more error, so allow for that when sizing reserve or planning storage. Sub-metering would show whether the variation comes from one device or from many.

## Cluster 2: Midday-Peaking Weekday-Heavy

### 1. Timing (medium priority)

- Observation: This cluster concentrates its energy in the midday block (12:00 to 18:00).
- Evidence: afternoon_share is 35.0% against a population 29.0%, 21% above the population value.
- Cluster value: 0.3499
- Population baseline: 0.2902
- Action: Midday demand overlaps the hours when rooftop solar generates most, so evaluate on-site generation or a midday tariff for this group before considering load shifting.

### 2. Weekend (medium priority)

- Observation: This cluster uses less energy on weekend days relative to weekdays than the population does.
- Evidence: weekend_ratio is 0.852 against a population 1.036, 18% below the population value.
- Cluster value: 0.8525
- Population baseline: 1.0363
- Action: Consumption is concentrated on weekdays, which is consistent with an occupancy pattern tied to a working week. Weekday-targeted measures reach this group; weekend measures largely do not.

# Dataset Validation Report

## Dataset Overview
- Total consumers: 200
- Total records: 144000
- Time range: 2024-01-01 00:00:00 to 2024-01-30 23:00:00

## Archetype Distribution
- Flat: 9000 consumers
- Evening: 9000 consumers
- Daytime: 9000 consumers
- Weekend: 9000 consumers

## Behavioral Validation

### 1. Distinct Archetype Profiles
Each archetype has a distinct 24-hour load profile:
- Daytime: Peak during business hours (9-17)
- Evening: Peak during evening hours (18-22)
- Flat: Industrial-like flat profile with small variation
- Weekend: Higher on weekends, moderate weekday

### 2. Continuous Within-Archetype Variation
Within each archetype, individual consumers show continuous variation:
- Profile perturbations (15% strength)
- Peak timing shifts (±2 hours)
- Individual amplitude variation (0.8-2.5x)
- Day-specific variation (0.9-1.1x)
- Individual variability (lognormal)
- Occasional realistic spikes (5% chance)

This ensures clusters are not perfectly separated - genuine overlap exists.

### 3. Cross-Archetype Overlap
PCA visualization shows archetypes are not perfectly separated,
demonstrating that clustering must recover structure from noisy data.

### 4. Temperature Consistency
Temperature is derived from actual timestamp, ensuring all consumers
at the same clock time share the same exogenous condition.

### 5. Electrical Consistency
Current is physically derived from energy, voltage, and power factor:
I = P / (V * PF) where P = Energy / Time

## Archetype Statistics

archetype  avg_mean  std_mean   avg_cv   std_cv  avg_max  avg_min
  daytime  0.068267  0.018671 1.104466 0.162793 0.544187 0.010000
  evening  0.078947  0.017372 1.135913 0.200233 0.653630 0.010000
     flat  0.072198  0.020986 1.133712 0.191317 0.568261 0.010009
  weekend  0.072985  0.019206 1.239137 0.172530 0.667934 0.010000

## Conclusion
The dataset contains genuine, independent latent behavioral variation.
Archetypes provide hidden ground truth for validating whether clustering
recovers real structure. The archetype label is NEVER passed to K-Means.
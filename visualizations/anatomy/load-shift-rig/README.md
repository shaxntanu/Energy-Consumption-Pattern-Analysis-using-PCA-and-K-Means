# Anatomy figure: UCI load-shift test bench

This is a **Figure-sized** interactive explainer for one result that a flowchart cannot show clearly: moving evening demand into the afternoon can lower the evening peak while creating a larger peak earlier in the day.

The object is a conceptual profile test bench. Its two rows contain 24 hourly bars copied from the saved 2012 UCI scenario profile. The front row responds to the controls; the back row remains the observed baseline. The dial and slider represent the assumed scenario intensity. They do not represent physical grid controls or actual participant response.

## Accuracy and scope

- The scenario is built from the saved hourly CSV and metadata in `outputs/research_additions/`.
- It includes 104 active anonymized UCI points/clients for calendar year 2012; the source does not establish that each is a household.
- The target scenario assumes 10% of the target cluster's 17:00–21:00 energy moves evenly to 12:00–17:00. The equal-energy comparison shifts the same aggregate energy from the other clusters.
- The slider scales between the stored baseline and 10% endpoint. This is valid for the script's linear reassignment rule; it does not refit PCA or K-Means.
- At the saved 10% endpoint, the evening peak changes by 5.64%, the whole-day peak moves from 18:00 to 16:00 and rises to 185,212.520 kW, and daily energy is preserved by construction.
- No response, flexibility, causality, bill savings, or actual demand reduction was measured.

## Build and check

From the repository root:

```bash
node visualizations/anatomy/load-shift-rig/build.mjs
node --test visualizations/anatomy/load-shift-rig/model.test.mjs
```

The build writes a self-contained interactive page and a static SVG to `web/public/research/`. The page has no runtime dependency on the Anatomy package, Python, or the raw UCI dataset. Its source uses a minimal copy of Anatomy's MIT-licensed SVG kit; see `visualizations/anatomy/LICENSE.anatomy.txt`.

The generated HTML is embedded in the Vercel explorer. The SVG is the static fallback used in the documentation and repository README.

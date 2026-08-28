export const populationShape = [
  0.028466, 0.025474, 0.023935, 0.024028, 0.025785, 0.030453,
  0.036983, 0.043155, 0.044966, 0.045423, 0.044888, 0.045637,
  0.046691, 0.047718, 0.047736, 0.04802, 0.04911, 0.05089,
  0.054461, 0.056868, 0.055341, 0.049191, 0.0408, 0.033981,
];

export const clusterShapes = {
  0: [
    0.023725, 0.021206, 0.020476, 0.020663, 0.022507, 0.027108,
    0.033624, 0.04098, 0.044394, 0.048453, 0.050705, 0.053388,
    0.055371, 0.056751, 0.056546, 0.055765, 0.055298, 0.053719,
    0.053484, 0.052553, 0.04859, 0.042185, 0.034162, 0.028346,
  ],
  1: [
    0.035218, 0.034135, 0.033121, 0.03338, 0.034362, 0.036542,
    0.039599, 0.042354, 0.043681, 0.044724, 0.044386, 0.044549,
    0.044966, 0.045217, 0.044585, 0.044685, 0.045097, 0.045942,
    0.047288, 0.047857, 0.046308, 0.044063, 0.040385, 0.037558,
  ],
  2: [
    0.029707, 0.023587, 0.019885, 0.019604, 0.022098, 0.029788,
    0.040385, 0.048261, 0.047558, 0.040425, 0.034311, 0.032033,
    0.032046, 0.033299, 0.034499, 0.037042, 0.041907, 0.051218,
    0.064677, 0.075627, 0.078799, 0.068595, 0.054018, 0.04063,
  ],
};

export const clusters = [
  {
    id: 0,
    name: "Midday-Peaking",
    color: "#f2b04b",
    size: 94,
    sizeShare: 0.47,
    peakHour: 13,
    morningShare: 0.2715,
    afternoonShare: 0.3335,
    eveningShare: 0.2593,
    nightShare: 0.1357,
    baseLoadShare: 0.4562,
    coefficientOfVariation: 0.5729,
    description: "Rises through the morning and stays busy through a broad afternoon plateau.",
  },
  {
    id: 1,
    name: "Flat All-Day",
    color: "#48d7c2",
    size: 57,
    sizeShare: 0.285,
    peakHour: 19,
    morningShare: 0.2593,
    afternoonShare: 0.2705,
    eveningShare: 0.2635,
    nightShare: 0.2068,
    baseLoadShare: 0.7706,
    coefficientOfVariation: 0.2737,
    description: "Uses energy steadily, with the least hour-to-hour movement of the three groups.",
  },
  {
    id: 2,
    name: "Evening-Peaking",
    color: "#b78cff",
    size: 49,
    sizeShare: 0.245,
    peakHour: 20,
    morningShare: 0.243,
    afternoonShare: 0.23,
    eveningShare: 0.3823,
    nightShare: 0.1447,
    baseLoadShare: 0.4268,
    coefficientOfVariation: 0.6677,
    description: "Stays quieter during the day, then climbs into a sharp evening peak.",
  },
];

export const kMetrics = [
  { k: 2, silhouette: 0.2582, daviesBouldin: 1.1727, selected: false },
  { k: 3, silhouette: 0.3124, daviesBouldin: 1.2541, selected: true },
  { k: 4, silhouette: 0.2916, daviesBouldin: 1.2099, selected: false },
  { k: 5, silhouette: 0.3005, daviesBouldin: 1.3914, selected: false },
  { k: 6, silhouette: 0.2888, daviesBouldin: 1.3912, selected: false },
  { k: 7, silhouette: 0.2726, daviesBouldin: 1.3342, selected: false },
  { k: 8, silhouette: 0.2702, daviesBouldin: 1.3246, selected: false },
  { k: 9, silhouette: 0.2136, daviesBouldin: 1.4585, selected: false },
  { k: 10, silhouette: 0.2179, daviesBouldin: 1.4115, selected: false },
];

export const pcaComponents = [
  { component: 1, explainedVariance: 0.3304, cumulativeVariance: 0.3304 },
  { component: 2, explainedVariance: 0.2711, cumulativeVariance: 0.6014 },
  { component: 3, explainedVariance: 0.1033, cumulativeVariance: 0.7048 },
  { component: 4, explainedVariance: 0.0607, cumulativeVariance: 0.7655 },
  { component: 5, explainedVariance: 0.0466, cumulativeVariance: 0.812 },
  { component: 6, explainedVariance: 0.0386, cumulativeVariance: 0.8506 },
  { component: 7, explainedVariance: 0.0208, cumulativeVariance: 0.8714 },
  { component: 8, explainedVariance: 0.0196, cumulativeVariance: 0.8911 },
  { component: 9, explainedVariance: 0.0148, cumulativeVariance: 0.9059 },
  { component: 10, explainedVariance: 0.0146, cumulativeVariance: 0.9205 },
  { component: 11, explainedVariance: 0.0117, cumulativeVariance: 0.9322 },
  { component: 12, explainedVariance: 0.008, cumulativeVariance: 0.9402 },
  { component: 13, explainedVariance: 0.0067, cumulativeVariance: 0.947 },
  { component: 14, explainedVariance: 0.0057, cumulativeVariance: 0.9526 },
];

export const summaryStats = {
  records: "144,000",
  consumers: "200",
  features: "51",
  pcaComponents: "14",
  clusters: "3",
  silhouette: "0.312",
};

export const references = [
  {
    title: "Systematic literature review of the techniques for household electrical appliance anomaly detections and knowledge extractions",
    meta: "Rauf, S. A. A., & Adekoya, A. F., 2023, Journal of Electrical Systems and Information Technology, 10, 22",
    url: "https://doi.org/10.1186/s43067-023-00086-1",
  },
  {
    title: "Electricity Pattern Analysis by Clustering Domestic Load Profiles Using DWT and PCA",
    meta: "Cen et al., 2022, Energies",
    url: "https://doi.org/10.3390/en15020528",
  },
  {
    title: "Load Shape Clustering Using Residential Smart Meter Data",
    meta: "Jin et al., 2016, Lawrence Berkeley National Laboratory",
    url: "https://eta-publications.lbl.gov/sites/default/files/jin_-_loadshape_paper.pdf",
  },
  {
    title: "A clustering approach to domestic electricity load profile characterisation",
    meta: "McLoughlin, Duffy and Conlon, 2015, Applied Energy",
    url: "https://doi.org/10.1016/j.apenergy.2014.12.039",
  },
  {
    title: "Silhouettes: a graphical aid to the interpretation and validation of cluster analysis",
    meta: "Rousseeuw, 1987, Journal of Computational and Applied Mathematics",
    url: "https://doi.org/10.1016/0377-0427(87)90125-7",
  },
  {
    title: "k-Shape: Efficient and Accurate Clustering of Time Series",
    meta: "Paparrizos and Gravano, 2015, ACM SIGMOD",
    url: "https://doi.org/10.1145/2723372.2737793",
  },
];

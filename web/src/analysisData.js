// Genuine flagship export — config 99c7a6631340d301
// 200 consumers × 365 days (2024-01-01 → 2024-12-30), 1,752,000 records
// K=4 (silhouette 0.328, recovery ARI 0.813), 10 PCA components (0.9505 var)
// Sourced from web/public/data/*.json (contract_version 1.0.0).
// Nothing here is hand-edited: values are copied verbatim from those JSONs.
// Field names match what web/src/main.jsx consumes (cluster.description,
// cluster.coefficientOfVariation, pcaComponents.component/.explainedVariance/
// .cumulativeVariance, references.title/.meta/.url).

export const populationShape = [
  0.4881877035337884, 0.39505240225195296, 0.39704741328393543, 0.6283055719920618,
  0.7020408097855422, 0.6015253473967175, 0.5834131289021202, 0.9377636428104053,
  1.121067525066174, 1.0835203777793464, 1.2849570648014453, 1.6111801330141146,
  1.75535148628834,  1.538171868488744,  1.4836180454691804, 1.2375195776588334,
  1.400284005765318,  1.59101698974863,   2.044741371780356,  2.13292107652072,
  2.0180866122335467, 1.763307040017113,  1.2229442871107743, 0.5390124383147727,
];

export const clusterShapes = {
  // keys "0".."3" → 24h mean load shapes (kWh), copied verbatim from
  // profiles.json cluster_load_shapes
  0: [
    0.31880907119245175, 0.2495800282115527, 0.2601775995102952, 0.5277122858177081,
    0.5569388760656521, 0.5276013986231452, 0.676152681139462, 1.305622146020524,
    1.4576155945882635, 1.6166890255441811, 2.2799004781081066, 2.7234465946052223,
    2.8046857257413996, 2.451277542785306, 2.4610710596385867, 2.046041598311625,
    2.3558664540867397, 1.5564983142005202, 1.752221325040541, 1.9264548782384325,
    1.4046155064708651, 1.142103405758445, 0.8148363073234677, 0.2320266868794544,
  ],
  1: [
    1.0006040769139231, 0.9309376908238879, 0.9401386747383708, 1.0354762364176472,
    1.1350732552601695, 1.0103247638575762, 0.9459005549948564, 1.0802755398195654,
    1.1969519097065887, 1.1132113223638675, 1.1525234517283624, 1.3431181947607004,
    1.4963511447663582, 1.2812880983944227, 1.285472163634449, 1.070863866929923,
    1.1649957796169434, 1.321901213281072, 1.7184900700586377, 1.9151055357597012,
    1.87668305414194, 1.5983683239998864, 1.2794396440628039, 1.1491149028307776,
  ],
  2: [
    0.3987828494651458, 0.30537957209209964, 0.33939899762760686, 0.47979382785999613,
    0.5204645521473764, 0.4713676656650051, 0.46629826085933254, 0.7307079690708869,
    0.9560318572035584, 0.903387760580997, 0.8570253498446504, 1.158086011311974,
    1.2625226779209585, 1.2229671601788731, 1.160195715695422, 0.9049395847761441,
    0.9870454741466461, 1.806933308860577, 2.5854270383429127, 3.172163931512248,
    2.9319499743663585, 2.5261108351014193, 1.756266972045961, 0.2848134171259258,
  ],
  3: [
    0.3369140074476229, 0.27091513549199756, 0.26320911780292427, 0.6138217016451192,
    0.6881115720372456, 0.5412104519158022, 0.45008219576999856, 0.8364920164734937,
    1.0145439145226737, 0.9586587431483173, 1.1398779059165452, 1.4909860115972309,
    1.6523189711283582, 1.4473643831018766, 1.3313328165284539, 1.0889482966836083,
    1.3144481995122008, 1.7272970638513064, 2.057675652044047, 2.4214435199250682,
    1.9254230709725759, 1.6502209580651468, 1.140268584504732, 0.3749910856052422,
  ],
};

export const clusters = [
  // from profiles.json cluster_profiles — sizes, day-period shares, hourly
  // peaks, base-load share, coefficient of variation
  {
    id: "0",
    name: "Midday-Peaking Weekday-Heavy",
    size: 39,
    sizeShare: 0.195,
    color: "#f2b04b",
    peakHour: 13,
    morningShare: 0.305661,
    afternoonShare: 0.356708,
    eveningShare: 0.211790,
    nightShare: 0.125841,
    baseLoadShare: 0.426376,
    coefficientOfVariation: 0.620288,
    description:
      "Rises through the morning into a broad afternoon plateau on weekdays, with subdued evening and weekend use.",
  },
  {
    id: "1",
    name: "Flat All-Day",
    size: 52,
    sizeShare: 0.26,
    color: "#48d7c2",
    peakHour: 19,
    morningShare: 0.261291,
    afternoonShare: 0.271005,
    eveningShare: 0.257569,
    nightShare: 0.210134,
    baseLoadShare: 0.801165,
    coefficientOfVariation: 0.302007,
    description:
      "Uses energy steadily through the day with the least hour-to-hour movement of the four groups.",
  },
  {
    id: "2",
    name: "Evening-Peaking",
    size: 47,
    sizeShare: 0.235,
    color: "#b78cff",
    peakHour: 20,
    morningShare: 0.239540,
    afternoonShare: 0.228785,
    eveningShare: 0.379540,
    nightShare: 0.152134,
    baseLoadShare: 0.449540,
    coefficientOfVariation: 0.705483,
    description: "Quiet by day, then climbs into a sharp evening peak.",
  },
  {
    id: "3",
    name: "Evening-Peaking Weekend-Heavy",
    size: 62,
    sizeShare: 0.31,
    color: "#fb7185",
    peakHour: 19,
    morningShare: 0.242066,
    afternoonShare: 0.309627,
    eveningShare: 0.298662,
    nightShare: 0.149645,
    baseLoadShare: 0.523424,
    coefficientOfVariation: 0.596236,
    description:
      "An evening-peaking rhythm whose weekend profile lifts markedly across the day.",
  },
];

// K sweep from clustering.json metrics_by_k (K=2..10). score is the pipeline's
// composite used to break ties; selected marks the K the evidence chose (K=4).
export const kMetrics = [
  { k: 2, silhouette: 0.24049437098041297, calinski: 124.12287701904728, daviesBouldin: 1.605891220957566, score: 0, selected: false },
  { k: 3, silhouette: 0.2752341497816602, calinski: 119.01405943707387, daviesBouldin: 1.399796538003206, score: 0.8793882016453002, selected: false },
  { k: 4, silhouette: 0.3282866716821562, calinski: 118.81185783099247, daviesBouldin: 1.1691088024250416, score: 0.9444015542811052, selected: true },
  { k: 5, silhouette: 0.2786015955161339, calinski: 112.505797290925, daviesBouldin: 1.293795476409728, score: 0.8209956423863121, selected: false },
  { k: 6, silhouette: 0.20722614437472834, calinski: 109.26091750335465, daviesBouldin: 1.5428354303910471, score: 0.6257102103179557, selected: false },
  { k: 7, silhouette: 0.19165970530673304, calinski: 107.61643996023421, daviesBouldin: 1.596583590495378, score: 0.5839041035730337, selected: false },
  { k: 8, silhouette: 0.18462826433419477, calinski: 100.30569066241396, daviesBouldin: 1.6056956505999157, score: 0.5228538023691557, selected: false },
  { k: 9, silhouette: 0.17462619650348964, calinski: 97.07790524860613, daviesBouldin: 1.6331111270295592, score: 0.47618359644639274, selected: false },
  { k: 10, silhouette: 0.159339506404563, calinski: 93.6491217851902, daviesBouldin: 1.6734790346927285, score: 0.41434208205206175, selected: false },
];

// PCA variance from pca.json variance_curve — 10 components retained, the
// cumulative line settles at 0.9505 (reported as "95.0%").
export const pcaComponents = [
  { component: 1, explainedVariance: 0.33935897022485733, cumulativeVariance: 0.33935897022485733 },
  { component: 2, explainedVariance: 0.12749000107287893, cumulativeVariance: 0.46684897129773626 },
  { component: 3, explainedVariance: 0.10792725210189819, cumulativeVariance: 0.5747762233996344 },
  { component: 4, explainedVariance: 0.09216372254419287, cumulativeVariance: 0.6669399459438274 },
  { component: 5, explainedVariance: 0.0827421964484769, cumulativeVariance: 0.7496821423923042 },
  { component: 6, explainedVariance: 0.06192894263503477, cumulativeVariance: 0.811611085027339 },
  { component: 7, explainedVariance: 0.05608752935752158, cumulativeVariance: 0.8676986143848605 },
  { component: 8, explainedVariance: 0.039088799111869717, cumulativeVariance: 0.9067874134967303 },
  { component: 9, explainedVariance: 0.03173854294375541, cumulativeVariance: 0.9385259564404857 },
  { component: 10, explainedVariance: 0.011967576576465483, cumulativeVariance: 0.9504940204193212 },
];

// Summary band — the 365-day flagship (config 99c7a6631340d301).
export const summaryStats = {
  records: "1,752,000",
  nRecords: 1752000,
  consumers: "200",
  nConsumers: 200,
  features: "51",
  pcaComponents: "10",
  clusters: "4",
  silhouette: "0.328",
  silhouetteRaw: 0.3282866716821562,
  variance: "95.0%",
  varianceRaw: 0.9504940204193212,
  recovery: "0.813",
  recoveryRaw: 0.812671365105634,
  recoveryNmi: "0.828",
  stability: "0.995",
  stabilityRaw: 0.9946825377900362,
  temporalStability: "0.882",
  temporalRaw: 0.8816894746864208,
};

// --- Upstream science highlights: honest availability labels, no invented numbers ---

// Seasonal model — available: true on the 365-day flagship; at 30-day horizons
// the pipeline reports available: false ("no 'season' column with >= 2 distinct
// values"). Sourced from seasonal.json.
export const seasonalStats = {
  available: true,
  reason: null,
  seasons: ["winter", "spring", "summer", "autumn"],
  meanDailyKwhBySeason: { winter: 26.571, spring: 35.167, summer: 38.014, autumn: 29.433 },
  amplitude: 0.2018,
  phaseR: 0.6781,
  phaseAgreement: 0.885,
  nTruthConsumers: 185,
};

// Longitudinal stability — available ≥ 180 days (LONGITUDINAL_MIN_DAYS).
// Sourced from longitudinal.json: four non-overlapping quarterly windows, each
// re-running scaling → PCA → K selection independently; permutation-invariant ARI.
export const longitudinalStats = {
  available: true,
  reason: null,
  nSegments: 4,
  segments: [
    { label: "Q1", ari: 0.8378 },
    { label: "Q2", ari: 0.8924 },
    { label: "Q3", ari: 0.9456 },
    { label: "Q4", ari: 0.8510 },
  ],
  meanStability: 0.8817,
};

// Explainability — SHAP (TreeExplainer on a surrogate RF); honest permutation
// fallback when shap is absent. Sourced from explainability.json.
export const explainabilityStats = {
  available: true,
  reason: null,
  method: "shap",
  cvBalancedAccuracy: 0.9846,
  globalImportance: [
    { feature: "weekend_ratio", value: 0.0902 },
    { feature: "evening_share", value: 0.0548 },
    { feature: "base_load_share", value: 0.0446 },
    { feature: "night_share", value: 0.0311 },
    { feature: "afternoon_share", value: 0.0273 },
    { feature: "peak_hour", value: 0.0239 },
  ],
};

// Real-world ingestion — the audited CASE A demo panel (make_demo_panel()).
// Internal metrics only: the real branch never fabricates NMI/ARI.
export const realWorldStats = {
  available: true,
  meters: 24,
  meterHours: 12096,
  features: 51,
  pcaKept: 5,
  pcaPct: 95.5,
  selectedK: 2,
  silhouette: 0.7194,
  ch: 123.2,
  db: 0.3966,
  seedStability: 1.0,
  temporalStabilityReal: 1.0,
};

// Validation recovery — for the Validation slide's honest caption.
export const validationStats = {
  selectedKAri: 0.8127,
  selectedKNmi: 0.8284,
  bestRecoveryK: 4,
  bestRecoveryAri: 0.8127,
};

export const references = [
  {
    title: "Abdi & Williams (2010)",
    meta: "Principal component analysis. WIREs Computational Statistics.",
    url: "https://doi.org/10.1002/wics.101",
  },
  {
    title: "Jolliffe & Cadima (2016)",
    meta: "Principal component analysis: a review and recent developments. Phil. Trans. R. Soc. A.",
    url: "https://doi.org/10.1098/rsta.2015.0202",
  },
  {
    title: "Rousseeuw (1987)",
    meta: "Silhouettes: a graphical aid to the interpretation and validation of cluster analysis.",
    url: "https://doi.org/10.1016/0377-0427(87)90125-7",
  },
  {
    title: "Davies & Bouldin (1979)",
    meta: "A cluster separation measure. IEEE Trans. Pattern Anal. Mach. Intell.",
    url: "https://doi.org/10.1109/TPAMI.1979.4766909",
  },
  {
    title: "MacQueen (1967)",
    meta: "Some methods for classification and analysis of multivariate observations.",
    url: "https://projecteuclid.org/euclid.bsmsp/1200512992",
  },
  {
    title: "Zephyr Station",
    meta: "Author-built weather station: firmware /api/weather + logging + dashboard. Source of the season column's provenance.",
    url: "https://github.com/shaxntanu/Zephyr-Station",
  },
];

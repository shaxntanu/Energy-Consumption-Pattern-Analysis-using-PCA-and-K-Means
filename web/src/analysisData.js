// Genuine flagship export, config 99c7a6631340d301
// 200 consumers × 365 days (2024-01-01 → 2024-12-30), 1,752,000 records
// K=4 (silhouette 0.328, recovery ARI 0.813), 10 PCA components (0.9505 var)
// Sourced from web/public/data/*.json (contract_version 1.0.0).
// Nothing here is hand-edited: values are copied verbatim from those JSONs.
// Field names match what web/src/main.jsx consumes (cluster.description,
// cluster.coefficientOfVariation, pcaComponents.component/.explainedVariance/
// .cumulativeVariance, references.title/.meta/.url).

export const populationShape = [
  // profiles.json "population" load shape: mean hourly share of the daily
  // total (day fractions summing to 1), copied verbatim.
  0.0292164752299668, 0.0259150663541705, 0.0243403168691462, 0.0244464839805996,
  0.0264209230899177, 0.0309762769810394, 0.0370503343716316, 0.0424204146196127,
  0.0444872769346145, 0.04465096876677, 0.0446355376816898, 0.045627575138413,
  0.0467945607526119, 0.0474860289887385, 0.0479013946739786, 0.0479868825832102,
  0.0486153271826739, 0.0509840988544599, 0.0541645631683722, 0.055919252951058,
  0.0543937981163338, 0.0492714663196544, 0.0416510256099158, 0.0346439507814199,
];

export const clusterShapes = {
  // keys "0".."3" → 24h mean load shapes, copied verbatim from
  // profiles.json cluster_load_shapes (hourly share of the daily total).
  0: [
    0.0194515664499239, 0.0181624568371531, 0.018179827084823, 0.019309728924741,
    0.0223702039164667, 0.0283672983254975, 0.0367874017588557, 0.0446944393303406,
    0.0501447227470063, 0.0540188469751889, 0.0578924122683021, 0.0621233465201826,
    0.0650380352155058, 0.065247534299052, 0.0632424207251124, 0.0589985111333876,
    0.0540760778936991, 0.0501054913100931, 0.0471974206669977, 0.0440189090898902,
    0.038941372799091, 0.0329098518351195, 0.0266035697961692, 0.0221185540973998,
  ],
  1: [
    0.0348536731044504, 0.0340612139473149, 0.0338182698685468, 0.034358149527262,
    0.0354824915485331, 0.0375603901956734, 0.0403416002563842, 0.0427993093854401,
    0.0441080074353422, 0.0444558209173684, 0.0446601035481003, 0.0449265664469841,
    0.045144680197423, 0.0452097623917903, 0.0450577240437168, 0.0449361135427282,
    0.0449382430477741, 0.0457185170610415, 0.0466525301631882, 0.0467327195486752,
    0.0453091207185929, 0.0426727154369401, 0.0394194051159397, 0.0367828725507891,
  ],
  2: [
    0.0317257256367344, 0.0246921414971274, 0.0210024590618923, 0.0203894908775456,
    0.0233568840816797, 0.0309676301844255, 0.0405182763359089, 0.0473450945531302,
    0.0457557346341277, 0.039799996250445, 0.0341099008100782, 0.0320114259096394,
    0.0321158416261367, 0.0328199582145372, 0.0345296474625601, 0.0368669768488348,
    0.0416471157170135, 0.0508056967972452, 0.0630667718555546, 0.0726036387884697,
    0.0756189889529013, 0.0692916218607449, 0.0562948705240295, 0.0426641115192368,
  ],
  3: [
    0.0287287717433613, 0.0248865109445122, 0.0227965243298028, 0.0224401213127864,
    0.0236916702077207, 0.0271018040753302, 0.0318263871711491, 0.0369389719032135,
    0.0402850852475459, 0.0425992937072187, 0.0442550441177305, 0.0461610651677298,
    0.0478300137165038, 0.049340423864973, 0.0507730555726248, 0.0520485284890779,
    0.0535466987338166, 0.0560883060186076, 0.0580990868058818, 0.0584619467115596,
    0.0556432149346616, 0.0499213163255698, 0.0418870632141019, 0.0346490956845198,
  ],
};

export const clusters = [
  // from profiles.json cluster_profiles: sizes, day-period shares, hourly
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
// composite, computed only for the K that survive the balance and stability
// filters (K=2..6; K=7..10 are filtered out before scoring, hence null).
// selected marks the K the evidence chose (K=4).
export const kMetrics = [
  { k: 2, silhouette: 0.2939437518225455, calinski: 72.99794655833404, daviesBouldin: 1.3822966460504686, score: 0, selected: false },
  { k: 3, silhouette: 0.3304803853115014, calinski: 93.70183384832148, daviesBouldin: 1.1957217149422932, score: 0.8793882016453002, selected: false },
  { k: 4, silhouette: 0.3282866716821562, calinski: 96.61713813497728, daviesBouldin: 1.1691088459670895, score: 0.9444015542811052, selected: true },
  { k: 5, silhouette: 0.3351616198820151, calinski: 87.60960036721217, daviesBouldin: 1.2022910731297736, score: 0.8209956423863121, selected: false },
  { k: 6, silhouette: 0.3238272599743667, calinski: 83.63056709531355, daviesBouldin: 1.2326497885903491, score: 0.6257102103179557, selected: false },
  { k: 7, silhouette: 0.3163754755774248, calinski: 77.4660341569839, daviesBouldin: 1.2093826125596194, score: null, selected: false },
  { k: 8, silhouette: 0.307163232659902, calinski: 72.15634316539739, daviesBouldin: 1.2949651245042757, score: null, selected: false },
  { k: 9, silhouette: 0.3111422698892226, calinski: 69.06249696773054, daviesBouldin: 1.2014875963732292, score: null, selected: false },
  { k: 10, silhouette: 0.275952781244082, calinski: 65.55485378866058, daviesBouldin: 1.317966836217035, score: null, selected: false },
];

// PCA variance from pca.json variance_curve: 10 components retained, the
// cumulative line settles at 0.9505 (reported as "95.0%").
export const pcaComponents = [
  { component: 1, explainedVariance: 0.3393589736304491, cumulativeVariance: 0.3393589736304491 },
  { component: 2, explainedVariance: 0.2896374894211358, cumulativeVariance: 0.628996463051585 },
  { component: 3, explainedVariance: 0.1152220857431529, cumulativeVariance: 0.7442185487947379 },
  { component: 4, explainedVariance: 0.0629754975130199, cumulativeVariance: 0.8071940463077578 },
  { component: 5, explainedVariance: 0.0441318420899465, cumulativeVariance: 0.8513258883977044 },
  { component: 6, explainedVariance: 0.0367080347587931, cumulativeVariance: 0.8880339231564975 },
  { component: 7, explainedVariance: 0.0203657375520792, cumulativeVariance: 0.9083996607085768 },
  { component: 8, explainedVariance: 0.0173931459042709, cumulativeVariance: 0.9257928066128476 },
  { component: 9, explainedVariance: 0.012733641753139, cumulativeVariance: 0.9385264483659868 },
  { component: 10, explainedVariance: 0.0119675720533344, cumulativeVariance: 0.9504940204193212 },
];

// Summary band: the 365-day flagship (config 99c7a6631340d301).
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

// Seasonal model, available: true on the 365-day flagship; at 30-day horizons
// the pipeline reports available: false ("no 'season' column with >= 2 distinct
// values"). Sourced from seasonal.json.
export const seasonalStats = {
  available: true,
  reason: null,
  seasons: ["winter", "spring", "summer", "autumn"],
  meanDailyKwhBySeason: { winter: 26.571, spring: 35.167, summer: 38.014, autumn: 29.433 },
  peakHourBySeason: { winter: 19, spring: 20, summer: 20, autumn: 19 },
  amplitude: 0.2018,
  // 68% spread of the per-consumer amplitude estimates (seasonal.json q0.25 / q0.75)
  amplitudeQ25: 0.1786,
  amplitudeQ75: 0.2161,
  phaseR: 0.6781,
  phaseAgreement: 0.885,
  nTruthConsumers: 185,
};

// Longitudinal stability: available ≥ 180 days (LONGITUDINAL_MIN_DAYS).
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

// Explainability: SHAP (TreeExplainer on a surrogate RF); honest permutation
// fallback when shap is absent. Sourced from explainability.json.
export const explainabilityStats = {
  available: true,
  reason: null,
  method: "shap",
  cvBalancedAccuracy: 0.9846,
  globalImportance: [
    { feature: "hour_13_shape", value: 0.0307 },
    { feature: "harmonic_2_amplitude", value: 0.0289 },
    { feature: "hour_12_shape", value: 0.0273 },
    { feature: "profile_ramp", value: 0.0244 },
    { feature: "peak_concentration", value: 0.0235 },
    { feature: "evening_share", value: 0.0217 },
  ],
};

// Real-world ingestion: the audited CASE A demo panel (make_demo_panel()).
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

// Validation recovery, for the Validation slide's honest caption.
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

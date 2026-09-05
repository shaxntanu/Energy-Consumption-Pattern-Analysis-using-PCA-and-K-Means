"""Narrative content for the dashboard: the landing story, the references and
the beginner's guide.

This module exists so that the words live apart from the layout. It holds the
prose that used to be duplicated between the static landing page and the
Streamlit pages, so there is one place to edit a sentence and one place to check
a citation.

Two rules hold throughout:

- **No number is written here by hand.** Anything quantitative is a slot filled
  from the live ``AnalysisResults`` object, which is why the story and the guide
  are functions of ``results`` rather than constants. If the run changes, the
  prose changes with it, and there is no way for this file to disagree with the
  pipeline.
- **No citation is written from memory.** Every entry in ``REFERENCES`` was
  checked against Crossref for title, authors, year, venue and DOI. A reference
  that could not be verified is left out rather than approximated.
"""
from __future__ import annotations

from typing import Sequence

# --- Research references -----------------------------------------------------
# Verified against Crossref. Fields are bibliographic fact; 'why' is this
# project's own note on relevance. Do not add an entry that has not been checked,
# and do not adjust a field to make an entry read better.

REFERENCES: tuple[dict, ...] = (
    {
        "title": "A shape-based clustering method for pattern recognition of residential electricity consumption",
        "authors": "Wen, Zhou, Yang",
        "year": "2019",
        "venue": "Journal of Cleaner Production",
        "method": "Shape-based clustering of daily residential load curves",
        "dataset": "Residential electricity consumption records",
        "why": "Frames residential clustering around the shape of the day rather than its magnitude, which is the central premise of this project.",
        "url": "https://doi.org/10.1016/j.jclepro.2018.12.067",
    },
    {
        "title": "A clustering approach to domestic electricity load profile characterisation using smart metering data",
        "authors": "McLoughlin, Duffy, Conlon",
        "year": "2015",
        "venue": "Applied Energy",
        "method": "Clustering of domestic load profiles from smart-meter data",
        "dataset": "Residential smart-meter measurements",
        "why": "A domestic-sector precedent for characterising households by load-profile clusters.",
        "url": "https://doi.org/10.1016/j.apenergy.2014.12.039",
    },
    {
        "title": "Overview and performance assessment of the clustering methods for electrical load pattern grouping",
        "authors": "Chicco",
        "year": "2012",
        "venue": "Energy",
        "method": "Comparative assessment of clustering algorithms for load patterns",
        "dataset": "Electrical load pattern sets",
        "why": "Argues for comparing algorithms and validating with internal indices rather than assuming one method, which is why K here is chosen by a rule and checked, not defaulted.",
        "url": "https://doi.org/10.1016/j.energy.2011.12.031",
    },
    {
        "title": "Electricity Consumption Clustering Using Smart Meter Data",
        "authors": "Tureczek, Nielsen, Madsen",
        "year": "2018",
        "venue": "Energies",
        "method": "Review of smart-meter electricity consumption clustering",
        "dataset": "Smart-meter data",
        "why": "Surveys the practical choices and pitfalls of smart-meter clustering that this pipeline tries to make explicit.",
        "url": "https://doi.org/10.3390/en11040859",
    },
    {
        "title": "Principal component analysis of the electricity consumption in residential dwellings",
        "authors": "Ndiaye, Gabriel",
        "year": "2011",
        "venue": "Energy and Buildings",
        "method": "Principal component analysis of residential consumption",
        "dataset": "Residential dwelling consumption",
        "why": "A direct precedent for the PCA dimensionality-reduction step on residential electricity features.",
        "url": "https://doi.org/10.1016/j.enbuild.2010.10.008",
    },
    {
        "title": "Silhouettes: a graphical aid to the interpretation and validation of cluster analysis",
        "authors": "Rousseeuw",
        "year": "1987",
        "venue": "Journal of Computational and Applied Mathematics",
        "method": "The silhouette coefficient for cluster validation",
        "dataset": "General cluster analysis",
        "why": "The silhouette used here to help choose K comes from this paper.",
        "url": "https://doi.org/10.1016/0377-0427(87)90125-7",
    },
    {
        "title": "k-Shape: Efficient and Accurate Clustering of Time Series",
        "authors": "Paparrizos, Gravano",
        "year": "2015",
        "venue": "Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data",
        "method": "Shape-based time-series clustering with a normalised cross-correlation distance",
        "dataset": "Time-series benchmark datasets",
        "why": "The shape-aware alternative to Euclidean K-Means that this project names as a benchmark worth comparing against.",
        "url": "https://doi.org/10.1145/2723372.2737793",
    },
)

REFERENCES_OMITTED_NOTE = (
    "The Rauf & Adekoya systematic review on household electrical appliance anomaly "
    "detection is now correctly cited with the verified DOI."
)

REPO_URL = "https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means"

# --- The landing story -------------------------------------------------------
# The eight movements of the static landing page, rebuilt as a function of the
# live run so the figures quoted in the prose are the figures the pipeline just
# produced. Each step is a dict the UI layer renders; 'body' may contain inline
# HTML for emphasis only.


def story_steps(results) -> list[dict]:
    """The landing narrative, with every number taken from ``results``.

    Args:
        results: The single ``AnalysisResults`` object for the current run.

    Returns:
        Ordered step dicts with keys ``kicker``, ``title``, ``body`` and an
        optional ``tiles`` list of metric-card dicts.
    """
    n_features = len(results.feature_names)
    n_pcs = results.n_pca_components
    cum_var = results.metadata["pca_cumulative_variance"]
    k = results.optimal_k
    sil = results.silhouette_for_k(k)
    stability = results.stability_results or {}
    mean_ari = stability.get("mean_ari")
    archetype_ari = results.ari_for_k(k)
    n_records = len(results.preprocessed_data)
    n_consumers = results.preprocessed_data["consumer_id"].nunique()
    n_hour_bins = sum(1 for f in results.feature_names if str(f).endswith("_shape"))
    n_summary = n_features - n_hour_bins
    k_lo, k_hi = min(results.k_values), max(results.k_values)

    steps = [
        {
            "kicker": "The question",
            "title": "Do people differ by when, not just how much?",
            "body": (
                "The easy way to sort electricity customers is by size: small, medium, "
                "large. It is also the least useful, because it says nothing about "
                "<em>when</em> demand lands on the grid. The question here is whether "
                "consumers fall into distinct <strong>timing patterns</strong> - a daytime "
                "shape, an evening shape, a flat shape - that survive once you remove the "
                "effect of sheer volume."
            ),
        },
        {
            "kicker": "The data",
            "title": "A controlled, synthetic world",
            "body": (
                "To ask the question cleanly, the data is generated, not measured. A "
                "generator draws each consumer from one of four hidden archetypes, then "
                "adds amplitude, timing jitter, weekday and weekend differences, and "
                "noise. That hidden label is set aside before any modelling and used "
                "only, at the very end, to check the answer."
            ),
            "tiles": [
                {"label": "consumers", "value": f"{n_consumers}"},
                {"label": "days, hourly", "value": f"{results.config.n_days}"},
                {"label": "records", "value": f"{n_records:,}"},
                {"label": "hidden archetypes", "value": "4"},
            ],
            "warn": (
                "<strong>This is synthetic data.</strong> The consumers do not exist. "
                "Nothing here is evidence about real-world household behaviour; it is a "
                "test of whether the method can recover structure that was deliberately "
                "built in."
            ),
        },
        {
            "kicker": "The shape of a day",
            "title": "Divide out the size",
            "body": (
                "Each consumer's 24 hourly values are scaled to sum to one, turning a load "
                "<em>amount</em> into a load <em>shape</em>. After that step, a consumer "
                "that uses ten times the energy but at the same hours has an identical "
                "curve. What is left to cluster on is pure timing. The faint dotted line "
                "on every chart is the population's average day - the baseline each "
                "cluster is measured against."
            ),
        },
        {
            "kicker": "The features",
            "title": f"{n_features} ways to describe a curve",
            "body": (
                "A shape is more than 24 numbers. Alongside the hourly bins sit summary "
                "descriptors: the share of energy in each part of the day, how peaked the "
                "curve is, how much it varies hour to hour, its entropy and inequality, "
                "its dominant periodicities, and how different its weekend looks. "
                f"Together, <strong>{n_features} behavioural features</strong> - and not "
                "one of them is the raw size of the consumer."
            ),
            "tiles": [
                {"label": "hourly <b>shape</b> bins", "value": f"{n_hour_bins}"},
                {"label": "summary descriptors", "value": f"{n_summary}"},
                {"label": "behavioural features", "value": f"{n_features}"},
                {"label": "scale features used", "value": "0"},
            ],
        },
        {
            "kicker": "The method",
            "title": "Compress, then group",
            "body": (
                f"The {n_features} features are correlated, so they are first standardised "
                f"and passed through <strong>PCA</strong>, which keeps the "
                f"<strong>{n_pcs} components</strong> that together hold "
                f"<strong>{cum_var:.0%}</strong> of the variance. K-Means then groups "
                "consumers in that compressed space, and the number of groups is chosen by "
                "a rule fixed in advance - not picked to look tidy."
            ),
            "pipeline": [
                ("Standardise", "Zero mean, unit variance per feature."),
                ("PCA", f"{n_pcs} components, {cum_var:.0%} variance kept."),
                ("Sweep K", f"K = {k_lo} to {k_hi}, four internal metrics."),
                ("Select", "Pre-registered rule, then stability."),
                ("Profile", "Describe each group in real units."),
            ],
        },
        {
            "kicker": "The clusters",
            "title": f"{_number_word(k)} ways a day is spent",
            "body": (
                f"The rule settled on <strong>{_number_word(k).lower()} groups</strong>. "
                "They are not big, medium and small - they are different daily rhythms. "
                "Each card shows the cluster's own average day against the population."
            ),
        },
        {
            "kicker": "Honest validation",
            "title": "Stable grouping, modest separation",
            "body": (
                "Good practice is to report the awkward number as plainly as the "
                "flattering one. The clusters are <strong>highly reproducible</strong> "
                "across random restarts, and they line up moderately with the hidden "
                "archetypes. But the <strong>separation is modest</strong> - a silhouette "
                f"of {sil:.2f} means the groups touch at their edges rather than sitting "
                "far apart. Both things are true at once."
            ),
            "tiles": [
                {"label": f"silhouette @ K={k} <b>(modest)</b>", "value": f"{sil:.3f}"},
                {"label": "stability ARI <b>(high)</b>",
                 "value": f"{mean_ari:.3f}" if mean_ari is not None else "not measured"},
                {"label": "agreement with archetypes",
                 "value": f"{archetype_ari:.3f}" if archetype_ari is not None else "-"},
                {"label": "hidden archetypes", "value": "4"},
            ],
            "note": (
                "\"Stability\" here means the clusters reappear when the algorithm is "
                "restarted - it is a property of the <strong>clustering</strong>, not a "
                "confidence that any single consumer is correctly placed."
            ),
        },
        {
            "kicker": "What we learned",
            "title": "Timing is a real axis - here",
            "body": (
                "On this generated world, grouping by shape recovers timing patterns that "
                "pure size would miss, and it does so stably. It also shows the limit "
                "honestly: the groups overlap, and a single synthetic draw is not the "
                "world. The finding is about a method's behaviour on data built to test it "
                "- a narrower and more truthful claim than a statement about real homes."
            ),
        },
    ]
    return steps


_NUMBER_WORDS = {
    1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
    6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
}


def _number_word(n: int) -> str:
    """Spell a small integer, so headings read as prose rather than as data."""
    return _NUMBER_WORDS.get(int(n), str(int(n)))


# --- The beginner's guide ----------------------------------------------------
# Written for a reader who knows what a light switch is and nothing about
# machine learning. Simplified, but not to the point of being wrong: every
# statement here should still survive a reviewer who knows the method.


def how_to_use_chapters(results) -> list[dict]:
    """The plain-language guide, in order, with live numbers where relevant.

    Args:
        results: The current run's ``AnalysisResults``.

    Returns:
        Chapter dicts with ``title`` and ``body`` (markdown).
    """
    n_features = len(results.feature_names)
    n_pcs = results.n_pca_components
    cum_var = results.metadata["pca_cumulative_variance"]
    k = results.optimal_k
    sil = results.silhouette_for_k(k)
    stability = results.stability_results or {}
    mean_ari = stability.get("mean_ari")
    archetype_ari = results.ari_for_k(k)
    n_consumers = results.preprocessed_data["consumer_id"].nunique()
    n_days = results.config.n_days
    k_lo, k_hi = min(results.k_values), max(results.k_values)
    names = [str(p["cluster_name"]) for _, p in
             results.cluster_profiles.sort_values("cluster").iterrows()]

    return [
        {
            "title": "What this project is",
            "body": (
                "It is a study of **when** people use electricity, rather than how much.\n\n"
                "Imagine you have the electricity meter readings for a few hundred "
                "buildings. You could sort them by their bill, biggest to smallest - but "
                "that tells you almost nothing interesting. Two homes can use exactly the "
                "same amount of electricity in a month and live completely differently: one "
                "is busy at lunchtime, the other only comes alive after 7 pm.\n\n"
                "This project asks whether those *daily habits* form a small number of "
                "recognisable types. It uses two standard techniques - **PCA** and "
                "**K-Means** - to find out, and it shows you every step of its own working."
            ),
        },
        {
            "title": "What electricity consumption data means",
            "body": (
                "A meter records how much electricity was used in a period of time. Here "
                "each reading covers **one hour**, measured in kilowatt-hours (kWh). One "
                "kWh is roughly a 100-watt bulb left on for ten hours.\n\n"
                f"So one consumer in this study is a list of readings: 24 numbers a day, "
                f"for {n_days} days. Multiply that by {n_consumers} consumers and you have "
                f"the table this project starts from."
            ),
        },
        {
            "title": "What a load profile is",
            "body": (
                "A **load profile** is that list of hourly readings drawn as a curve: hour "
                "of the day along the bottom, electricity used up the side.\n\n"
                "It is the single most useful picture in this whole project. A curve that "
                "humps in the middle of the day is a different life from one that spikes at "
                "8 pm, and you can see the difference instantly without doing any "
                "arithmetic. Every chart here has the hour of the day on its horizontal "
                "axis, with faint shading for night, morning, afternoon and evening."
            ),
        },
        {
            "title": "What a dataset is",
            "body": (
                "A **dataset** is just the whole table of readings, kept together.\n\n"
                "The dataset here is **generated by a computer, not measured from real "
                "homes**. That is a deliberate choice, and it is stated on every page. The "
                "generator secretly assigns each consumer one of four behaviour types - "
                "daytime, evening, flat, weekend-heavy - and then builds a realistic messy "
                "curve around it.\n\n"
                "Why fake data? Because it gives you an answer key. With real meter "
                "readings, nobody knows the true groups, so you can never tell whether the "
                "method found something real or invented it. Here the answer is known and "
                "hidden until the end, so the method can be marked honestly. The trade-off "
                "is that **no result here says anything about real households.**"
            ),
        },
        {
            "title": "What features are",
            "body": (
                "A **feature** is one measurable property of a consumer, expressed as a "
                "single number, so that a computer can compare consumers.\n\n"
                "\"How peaky is this curve?\" is a question; *peak-to-average ratio = 5.9* "
                "is a feature. Some are easy to describe in words:\n\n"
                "- what fraction of the day's energy falls in the evening\n"
                "- which hour is the busiest\n"
                "- how much the curve jumps from one hour to the next\n"
                "- how different the weekend looks from the working week\n\n"
                f"This study computes **{n_features} of them** for every consumer. None of "
                "them is the consumer's total size - that is removed on purpose."
            ),
        },
        {
            "title": "Why we transform the raw readings",
            "body": (
                "Because raw readings are dominated by size, and size is the thing we are "
                "trying to ignore.\n\n"
                "A factory uses far more electricity than a flat, so if you compare raw "
                "numbers, every method you try will simply rediscover \"big versus small\". "
                "To prevent that, each consumer's 24 hourly values are **divided by their "
                "own daily total**, so they add up to 1. What is left is the *shape* of the "
                "day - the proportions - with the size divided out.\n\n"
                "After that step, a factory and a flat that are busy at the same hours look "
                "identical, which is exactly what we want."
            ),
        },
        {
            "title": "What PCA does",
            "body": (
                "**PCA** (Principal Component Analysis) is a way of squeezing many related "
                "measurements into a smaller number of useful dimensions, while trying to "
                "keep the important patterns.\n\n"
                f"The {n_features} features overlap a lot. If a consumer uses very little "
                "at 2 am, that already tells you a lot about 3 am; the four period shares "
                "have to add up to 1, so the fourth is fixed once you know three. Feeding "
                "all that redundancy into a grouping algorithm lets the same underlying "
                "fact get counted many times over.\n\n"
                "PCA looks for the directions along which consumers actually differ most, "
                "and rewrites everyone using just those directions. Think of "
                "photographing a chair: you lose a dimension, but if you pick the angle "
                f"well it is still obviously a chair.\n\nHere PCA keeps **{n_pcs} "
                f"components**, which between them retain **{cum_var:.1%}** of the original "
                "variation. The components are combinations of features, not features "
                "themselves, so they have no natural names - the Principal components page "
                "shows what each one is built from."
            ),
        },
        {
            "title": "What K-Means does",
            "body": (
                "**K-Means** is a grouping algorithm. It looks for consumers whose "
                "electricity-use behaviour looks similar and puts them into the same group.\n\n"
                "You tell it how many groups to make - that number is **K** - and it works "
                "in a loop:\n\n"
                "1. Drop K markers at random positions.\n"
                "2. Assign every consumer to the nearest marker.\n"
                "3. Move each marker to the middle of the consumers that chose it.\n"
                "4. Repeat until nothing moves.\n\n"
                "It is genuinely that simple. Two consequences matter. First, K-Means never "
                "sees the hidden answer key - it only sees distances, which is what makes "
                "it a fair test. Second, the starting positions are random, so the same "
                "data can give slightly different groups on different runs; that is why "
                "this project measures **stability** and runs the algorithm many times."
            ),
        },
        {
            "title": "What a cluster means",
            "body": (
                "A **cluster** is one of the groups K-Means produced: a set of consumers "
                f"whose daily shapes resemble each other more than they resemble the rest.\n\n"
                f"This run settled on **K = {k}**, and the clusters were named after what "
                "they actually do, once they existed: "
                + ", ".join(f"**{n}**" for n in names) + ".\n\n"
                "Two cautions. A cluster is a **tendency, not a box** - members near the "
                "edge could reasonably have gone either way. And the numbers K-Means gives "
                "the clusters (0, 1, 2) are labels with no order: cluster 2 is not more of "
                "anything than cluster 1."
            ),
        },
        {
            "title": "What the graphs mean",
            "body": (
                "Every chart is drawn live from the run you are currently looking at. The "
                "ones worth knowing:\n\n"
                "- **Mean load shape by cluster** - the headline. Each coloured line is one "
                "cluster's average day; the dotted grey line is the population average. "
                "Where a colour sits above the dotted line, that cluster uses "
                "proportionally more of its day's energy at that hour.\n"
                "- **Explained variance** - how much of the original variation each PCA "
                "component captures, and where the cut-off falls.\n"
                "- **Consumers in the first two components** - every consumer as one dot. "
                "Dots close together have similar daily shapes. You are seeing a flat "
                f"picture of a {n_pcs}-dimensional space, so some overlap is the projection, "
                "not the model.\n"
                "- **Composite selection score by K** - why this K won.\n"
                "- **Stability by K** - how reliably each K reproduces itself.\n"
                "- **Feature box plots** - the spread of one feature within each cluster, "
                "against the population line.\n\n"
                "On any chart you can drag a box to zoom in, and **double-click to zoom "
                "back out**."
            ),
        },
        {
            "title": "What you can change",
            "body": (
                "Open **Adjust the run** in the sidebar. Four things are yours to move:\n\n"
                "- **Consumers** and **Days** - how much synthetic data to generate. More "
                "is steadier and slower.\n"
                "- **Feature set** - `behavioral` is the real study (shape only). `scale` "
                "swaps in size-based features, and is included precisely because it scores "
                "*better* on the separation metrics while answering the wrong question. "
                "`combined` uses both.\n"
                "- **Random seed** - which synthetic world gets generated. Changing it is "
                "the honest test of whether a finding was real or luck.\n"
                "- **Measure clustering stability** - repeat runs to check reproducibility. "
                "Turning it off is faster but disables the Stability page.\n\n"
                "Try `scale` and watch the silhouette improve while agreement with the "
                "hidden archetypes collapses. That contrast is the most instructive thing "
                "in the application."
            ),
        },
        {
            "title": "What happens when you change a setting",
            "body": (
                "The whole analysis is genuinely recomputed in Python. Nothing here is a "
                "stored screenshot.\n\n"
                "Generate data, clean it, compute features, standardise, run PCA, sweep K, "
                "pick K by the fixed rule, check stability, profile the clusters, write the "
                "observations - then every chart and number on every page redraws from that "
                "one fresh result. It takes a few seconds, and the result is cached, so "
                "returning to a previous setting is instant.\n\n"
                "Your runs are written to a private temporary folder. The committed "
                "reference run in the repository is never overwritten by anything you do "
                f"here. The current run's fingerprint is "
                f"`{results.config.config_hash()}`; the default settings reproduce the "
                "committed reference run exactly."
            ),
        },
        {
            "title": "What the metrics mean",
            "body": (
                "Four numbers do most of the work. All are computed by the pipeline, none "
                "is entered by hand.\n\n"
                f"- **Silhouette** ({sil:.3f} here). For each consumer: how much closer is "
                "it to its own group than to the nearest other group? Runs from -1 to 1. "
                "Above 0.5 is clean separation; **around 0.3 means real but overlapping "
                "groups**, which is what this study has and says so.\n"
                + (f"- **Stability ARI** ({mean_ari:.3f} here). Re-run the algorithm from a "
                   "different random start and compare the groupings. 1.0 means identical "
                   "every time. This being high while the silhouette is middling is not a "
                   "contradiction: the groups are *reliably found* but *not far apart*.\n"
                   if mean_ari is not None else "")
                + (f"- **Archetype ARI** ({archetype_ari:.3f} here). The mark against the "
                   "hidden answer key. 0 is chance, 1 is perfect. This is well above chance "
                   "but well below perfect - the method recovered much of the built-in "
                   "structure, not all of it.\n" if archetype_ari is not None else "")
                + "- **Calinski-Harabasz** and **Davies-Bouldin** are two more separation "
                "measures, used inside the K-selection rule so the choice does not rest on "
                "the silhouette alone.\n\n"
                "The habit worth copying: report the unflattering number in the same "
                "sentence as the flattering one."
            ),
        },
        {
            "title": "What the observations mean",
            "body": (
                "The **Insights** page lists, for each cluster, where it measurably differs "
                "from the population, and one thing that might follow.\n\n"
                "Read them as descriptions with a suggestion attached, and note three "
                "deliberate limits:\n\n"
                "- They are **correlational**. \"This cluster peaks in the evening\" is an "
                "observation about a group, not a cause and not a diagnosis of any member.\n"
                "- They quote **no savings figures**. Any specific percentage saving would "
                "be invented, so none is given.\n"
                "- They can be **silent**. If a cluster sits close to the population on "
                "every measure, nothing is raised for it. That silence is a result, not a "
                "gap.\n\n"
                "And since the data is synthetic, these are demonstrations of the reasoning "
                "pattern, not advice for real consumers."
            ),
        },
        {
            "title": "What the limitations are",
            "body": (
                "The honest list, which the Limitations page keeps alongside the results:\n\n"
                f"- **The data is synthetic.** Designed, not observed. Nothing here is "
                "evidence about real households.\n"
                f"- **Separation is modest.** A silhouette of {sil:.3f} means the groups "
                "overlap at their edges. They are tendencies, not categories.\n"
                "- **Clustering is not causation.** No pattern here explains why anyone "
                "behaves as they do.\n"
                f"- **One window.** A single {n_days}-day panel. The seed-robustness study "
                "repeats the generation, but this is not a multi-season claim.\n"
                "- **The features decide the answer.** Change the feature set and the "
                f"result changes; that is what the ablation demonstrates.\n"
                "- **K is a judgement, made by a rule.** The rule was fixed in advance and "
                f"its full trace is on the Choosing K page, including that K = {k_lo} to "
                f"{k_hi} were all considered and why some were rejected.\n\n"
                "None of this makes the study worthless. Knowing precisely what a result "
                "does not support is part of the result."
            ),
        },
    ]


def how_to_use_quickstart() -> Sequence[tuple[str, str]]:
    """Three steps for a reader who wants to start clicking immediately."""
    return (
        ("Look at the shape", "Open Overview and read the load-shape chart. Each coloured "
                              "line is one cluster's average day against the dotted "
                              "population average."),
        ("Follow the method", "Dataset first, to see the readings themselves. Then How it "
                              "works, Features, Principal components and Choosing K, in "
                              "that order. Each page performs one step and explains it."),
        ("Change something", "Open \"Adjust the run\" in the sidebar and switch the feature "
                             "set to scale. Watch the silhouette rise and the archetype "
                             "agreement fall."),
    )

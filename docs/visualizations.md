# Technical visualizations

The project uses Mermaid for exact software structure, Anatomy for complementary data-backed and conceptual isometric figures, and ManimGX for a short explanation of its shape-first method.

## ManimGX method animation

The [shape-first explainer](../web/public/animations/shape-first-method.mp4) shows why the pipeline normalizes each consumer's hourly profile by its daily total before building features, applying PCA, and clustering. Its two curves are illustrative rather than measured household data. The same committed MP4 is played on demand in Streamlit and in the Vercel pipeline section; ManimGX is not a runtime dependency for either app. The [static poster](../web/public/animations/shape-first-method-poster.svg) previews it in the Vercel hero and video player.

The editable source is [`visualizations/manimgx/shape_first_method.py`](../visualizations/manimgx/shape_first_method.py). Follow the [rendering guide](../visualizations/manimgx/README.md) to inspect and reproduce the checked-in video.

## PCA and K-Means method instrument

The [interactive dark figure](assets/research-method-instrument.html) is a conceptual instrument for the reference synthetic run: 200 consumers over 365 days, 51 standardized features, 10 PCA components retaining 95.05% variance, and K=4 selected from candidates 2–10. Its output trays draw the saved normalized 24-hour cluster mean profiles. The travelling profile strip is a stage marker, not live inference; synthetic labels remain outside fitting and are used only for post-fit validation.

The [standalone SVG](assets/research-method-instrument.svg) is the README fallback, with a [PNG preview](assets/research-method-instrument.png). Rebuild the figure with `node docs/visualizations/anatomy/build_method_instrument.mjs`; the small vendored SVG kit and its MIT license are under [visualizations/anatomy-vendor/](visualizations/anatomy-vendor/).

## Interactive load-shift test bench

The [interactive test bench](../web/public/research/load-shift-test-rig.html) illustrates the retrospective UCI load-shifting scenario. Its 24 bars come from the saved hourly CSV: one row is the observed aggregate profile and one row is the selected counterfactual. The slider moves between the saved baseline and the saved 10% endpoint. The figure highlights the trade-off: the evening peak drops by 5.64%, while both 10% scenarios create a higher whole-day peak at 16:00. Total daily energy is preserved by construction.

This is a conceptual visualization of software arithmetic, not hardware or evidence of actual demand response. It shows 104 anonymized client points in the UCI sample; it does not assert that they are all households. See the [scenario protocol and limits](../outputs/reports/demand_response_uci_2012.md).

![Static 10% target-cluster scenario in the isometric test bench](assets/load-shift-test-rig.svg)

The static SVG is the offline fallback. The HTML page runs without additional dependencies. To regenerate both from their versioned inputs, run `node visualizations/anatomy/load-shift-rig/build.mjs`.

## Why the visual forms are complementary

The repository's [architecture](architecture.md), [methodology](METHODOLOGY.md), and pipeline page use Mermaid for precise component and evidence flows. Anatomy adds two different explanations: the method instrument is explicitly a software metaphor, while the load-shift bench uses saved UCI profiles to make the peak-time change and energy-conservation assumption visible. Neither depicts deployed hardware or grid control.

Other opportunities were intentionally skipped: software architecture and the synthetic/real evidence split remain Mermaid because they are logical flows; PCA variance, K selection, and temporal stability retain their numeric charts; no hardware, grid-control, or deployment-machine illustration was created because those systems are not implemented here.

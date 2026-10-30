# Technical visualizations

The project uses Mermaid for exact software structure, Anatomy for one data-backed isometric test bench, and ManimGX for a short explanation of its shape-first method.

## ManimGX method animation

The [shape-first explainer](../web/public/animations/shape-first-method.mp4) shows why the pipeline normalizes each consumer's hourly profile by its daily total before building features, applying PCA, and clustering. Its two curves are illustrative rather than measured household data. The same committed MP4 is played on demand in Streamlit and in the Vercel pipeline section; ManimGX is not a runtime dependency for either app. The [static poster](../web/public/animations/shape-first-method-poster.svg) previews it in the Vercel hero and video player.

The editable source is [`visualizations/manimgx/shape_first_method.py`](../visualizations/manimgx/shape_first_method.py). Follow the [rendering guide](../visualizations/manimgx/README.md) to inspect and reproduce the checked-in video.

## Interactive load-shift test bench

The [interactive test bench](../web/public/research/load-shift-test-rig.html) illustrates the retrospective UCI load-shifting scenario. Its 24 bars come from the saved hourly CSV: one row is the observed aggregate profile and one row is the selected counterfactual. The slider moves between the saved baseline and the saved 10% endpoint. The figure highlights the trade-off: the evening peak drops by 5.64%, while both 10% scenarios create a higher whole-day peak at 16:00. Total daily energy is preserved by construction.

This is a conceptual visualization of software arithmetic, not hardware or evidence of actual demand response. It shows 104 anonymized client points in the UCI sample; it does not assert that they are all households. See the [scenario protocol and limits](../outputs/reports/demand_response_uci_2012.md).

![Static 10% target-cluster scenario in the isometric test bench](assets/load-shift-test-rig.svg)

The static SVG is the offline fallback. The HTML page runs without additional dependencies. To regenerate both from their versioned inputs, run `node visualizations/anatomy/load-shift-rig/build.mjs`.

## Why there is only one Anatomy figure

The repository's [architecture](architecture.md), [methodology](METHODOLOGY.md), and pipeline page already use Mermaid for precise component and evidence flows. There is no physical sensor or deployed control system to illustrate, so an isometric hardware scene would invent hardware. The load-shift scenario is a better fit: a moving, data-backed profile makes the change in peak time and the energy-conservation assumption visible at once.

Other opportunities were intentionally skipped: the software architecture and synthetic/real evidence split remain Mermaid because they are logical flows; PCA variance, K selection, cluster profiles, and temporal stability already have data charts that preserve their numeric axes; no hardware, grid-control, or deployment-machine illustration was created because those systems are not implemented here.

# AI skills and specialized tool reference

**Reviewed:** 2026-11-02

This registry records specialist tools named in the supplied repository prompt and its companion token-efficiency guide. It separates local availability from actual project use. A repository appearing here does not mean its code was installed or its skill was invoked. No skill package or additional application dependency was added to the repository for this audit. Python test dependencies were installed only in a task-specific virtual environment.

## Available locally and relevant to this repository

### Anatomy

- **Repository:** [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy)
- **Purpose and domain:** Interactive isometric SVG figures for physical systems and spatial explanations.
- **Trigger:** Use when a physical or spatial concept is hard to understand from a flat flow diagram.
- **Do not use when:** A Mermaid flow or ordinary chart explains the software or data flow more clearly, or when no physical system exists.
- **Availability and use:** Available in the local skill catalog. Anatomy-produced figure sources already exist in this repository. It was not invoked to create new figures during this audit.
- **Installation and invocation:** The local skill is available; no install command was run. Invoke the `anatomy` skill when a suitable figure is needed.
- **Artifacts and validation:** Existing sources include `docs/visualizations/anatomy/build_method_instrument.mjs` and `visualizations/anatomy/load-shift-rig/build.mjs`, with HTML, SVG, and PNG outputs. Their paths and descriptions were checked against `docs/visualizations.md`. No artifact was regenerated in this audit.
- **Notes:** The load-shift figure explains saved software arithmetic. It does not depict physical equipment or observed participant response.

### Diagram Design

- **Repository:** [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)
- **Purpose and domain:** Polished technical diagrams and charts for stable concepts that benefit from deliberate layout.
- **Trigger:** Use when a published architecture or research diagram would explain a complex, stable concept better than text or Mermaid.
- **Do not use when:** The diagram changes often, is simple, or needs to stay easy to diff and maintain as documentation code.
- **Availability and use:** Available in the local skill catalog. It was not invoked in this audit and no new diagram was produced.
- **Installation and invocation:** The skill is already available locally. No install command was run. Invoke the `diagram-design` skill when a suitable figure is identified.
- **Artifacts and validation:** No new artifact. Existing Mermaid architecture and the standalone project pipeline diagram were preserved. The repository evidence and current diagrams were reviewed; no Diagram Design validation command was run.
- **Notes:** No hardware, cloud service, or grid-control topology is represented as implemented.

### Taste Skill

- **Repository:** [leonxlnx/taste-skill](https://github.com/leonxlnx/taste-skill)
- **Purpose and domain:** Art direction, visual review, and responsive refinement for public pages and application screens.
- **Trigger:** Use when creating or materially changing the Vercel site, Streamlit dashboard, or another user-facing interface.
- **Do not use when:** The task changes only backend logic or a written report without an interface.
- **Availability and use:** The `design-taste-frontend` skill is available locally and was used for this audit. The deployed Vercel page was inspected in a browser before editing. The correction preserved the existing dark palette.
- **Installation and invocation:** Already available as `design-taste-frontend`; no install command was run.
- **Artifacts and validation:** No image asset was generated. The SDG content and project technology strip were corrected in `web/src/main.jsx`, `web/src/components/LogoLoop.jsx`, and `web/src/styles.css`. A local browser review, web tests, and production build were used to validate the result.
- **Notes:** Existing research values were preserved. The change corrected their interpretation and removed unrelated stack logos.

### ManimGX

- **Repository and documentation:** [academa-labs/manimgx](https://github.com/academa-labs/manimgx) and its [official documentation index](https://manimgx.academa.ai/llms.txt)
- **Purpose and domain:** Python scene authoring for animated mathematical and technical explanations.
- **Trigger:** Use when motion materially clarifies a process that is difficult to explain with a static chart, Mermaid, or prose.
- **Do not use when:** A static figure is sufficient or animation would add decoration without explanation.
- **Availability and use:** Existing source and renderer requirements are in the repository. The optional renderer is not an application runtime dependency. This audit inspected the existing integration and did not render a new scene.
- **Installation and invocation:** Follow `visualizations/manimgx/README.md` and `visualizations/manimgx/requirements.txt` when reproducing the current video. No installation or render command was run in this audit.
- **Artifacts and validation:** Existing source: `visualizations/manimgx/shape_first_method.py`. Existing video: `web/public/animations/shape-first-method.mp4`, referenced by Streamlit and Vercel. The repository guide documents its render and inspection process. The video was not regenerated here.
- **Notes:** The animation uses illustrative curves, not measured household data. Both interfaces serve the committed video without importing ManimGX at runtime.

## Documentation and writing skills referenced by the prompt

These repositories were referenced as optional writing workflows. They were not installed or invoked as separate skills in this audit. The documentation edits followed the prompt's evidence, accuracy, and traceability requirements directly.

| Skill | Verified source | Purpose and trigger | Availability, use, and validation |
|---|---|---|---|
| `good-readme` | [adewale/good-readme](https://github.com/adewale/good-readme) | Evidence-based README audit or rewrite. Use when restructuring the project entry point. Skip for changes that do not affect documentation. | Not installed or invoked. No skill-generated artifact. The root README was checked against repository files and its new link target. The source documents `npx skills add adewale/good-readme` as an install option. |
| `readme-writing` | [indubitably-ai/indubitably-skills](https://github.com/indubitably-ai/indubitably-skills), `readme-writing/SKILL.md` | README composition and open-source navigation. Use for creating or substantially revising a README. | Not installed or invoked. The prompt's `indubitably-ai/readme-writing` label resolves to this collection and folder. No skill-generated artifact. |
| `readme-generator` | [JayRHa/agent-skills](https://github.com/JayRHa/agent-skills), `readme-generator` | README structure, examples, install steps, and navigation. Use when writing a new README or making a broad rewrite. | Not installed or invoked. No skill-generated artifact. |
| `technical-writer` | [JayRHa/agent-skills](https://github.com/JayRHa/agent-skills), `technical-writer` | Precise developer documentation. Use for API, configuration, workflow, or release documentation. | Not installed or invoked. No skill-generated artifact. |
| `technical-writer` | [riekelt/technical-writer](https://github.com/riekelt/technical-writer) | Evidence-based technical writing and clear implementation boundaries. Use for new technical guides or a substantial documentation review. | Not installed or invoked. No skill-generated artifact. |
| `writing-and-editing` | `matt-riley/writing-and-editing` as named in the prompt | Final editorial review of grammar, clarity, and consistency. | The repository could not be verified from the supplied name during this review. It was not installed or used. No URL is inferred. |
| `readme` | `Shpigford/readme` as named in the prompt | Comprehensive README guidance. Use only for a substantial README overhaul. | The direct GitHub page returned 404 during this review. It was not installed or used. No URL is treated as verified. |
| GitHub profile README | [boffti/github-profile-readme](https://github.com/boffti/github-profile-readme) | Personal GitHub profile presentation. | Not applicable to this project repository. Not installed or used. Do not apply profile conventions to the project's README. |

## Research and source collection

### Crawl4AI

- **Repository:** [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **Purpose and domain:** Web crawling and extraction for multi-page external research.
- **Trigger:** Use when relevant evidence must be collected across a set of public pages.
- **Do not use when:** A small number of primary sources can be checked directly or an external crawler is unnecessary.
- **Availability and use:** The Python package was available in the audit environment, but it is not a project dependency and was not used. Official repository pages were checked directly instead.
- **Installation and invocation:** No install or crawl command was run. No reproducible project command is defined.
- **Artifacts and validation:** None generated. No crawled evidence was added to this repository.
- **Notes:** Keep research citations tied to primary sources and record retrieval limits when a crawler is used.

## Not applicable: KiCad and PCB tools

The prompt says to activate this group only for KiCad schematic or PCB work. This repository contains no KiCad schematic, PCB layout, Gerber, BOM, or hardware design. The tools were not installed or used, and there are no artifacts or validation steps to report.

| Tool named by the prompt | Verified source | Applicability |
|---|---|---|
| `kicad-happy` | [aklofas/kicad-happy](https://github.com/aklofas/kicad-happy) | Not applicable. |
| `AI-PCB-layout` | [ChengminLi/AI-PCB-layout](https://github.com/ChengminLi/AI-PCB-layout) | Not applicable. |
| `kicad-mcp-pro` | [oaslananka/kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) | Not applicable. |
| `KiStack` | [BackplaneWorks/kistack](https://github.com/BackplaneWorks/kistack) | Not applicable. The prompt's American-Embedded link redirects to this repository. |
| `circuit-skills` | [punkfab/circuit-skills](https://github.com/punkfab/circuit-skills) | Not applicable. |

## Project visualization tools

Matplotlib, Plotly, React, and Chart.js are application or visualization libraries, not agent skills. Their dependency declarations and source use are in the repository. Existing figures retain their data provenance and limitations in [`docs/visualizations.md`](visualizations.md). No new visualization dependency was added by this audit.

## Token-efficient agent stack from the companion guide

The five integrations below were not exposed as callable tools or skills in the current Codex session. None was installed, configured, or invoked, and none generated a repository artifact. Their working principles were applied manually with native tools: targeted retrieval, bounded output, reuse of existing code and documentation, and risk-based verification. The repository links were opened, but setup instructions, runtime behavior, and compatibility with other agent clients were not evaluated.

| Tool | Repository | Purpose and trigger | Do not use when |
|---|---|---|---|
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | Reduce unnecessary implementation complexity during code changes and substantial reviews. | Minimization would skip required correctness, safety, accessibility, or validation work. |
| Lean Coding Agent | [JeremyFaubert/lean-coding-agent-skill](https://github.com/JeremyFaubert/lean-coding-agent-skill) | Retrieve repository context just in time and choose checks according to change risk. | Dependencies, callers, or behavior remain unclear and need broader inspection. |
| Serena | [oraios/serena](https://github.com/oraios/serena) | Use semantic symbol lookup and references for non-trivial code navigation or cross-file changes. | A known small file or exact text search can answer the question more cheaply. |
| skill-search | [sowhan/skill-search](https://github.com/sowhan/skill-search) | Discover a specialist skill on demand when the environment supports semantic skill retrieval. | No specialist skill is needed or the available skill catalog is already small and accessible. |
| Token Optimizer MCP | [ooples/token-optimizer-mcp](https://github.com/ooples/token-optimizer-mcp) | Measure or reduce tool-output and context costs when an MCP integration is available and useful. | The task is small or output reduction would hide evidence needed for correctness. |

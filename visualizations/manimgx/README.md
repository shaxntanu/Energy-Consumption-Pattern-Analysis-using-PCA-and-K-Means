# ManimGX method explainer

`shape_first_method.py` animates the project's central preprocessing idea: two illustrative daily load curves can have the same rhythm at different energy scales; normalizing by each consumer's daily total removes that scale before feature construction, PCA, and K-Means.

The curves are illustrative, not measured household data. The final card reflects the documented synthetic reference run (51 features, 10 PCA components, and K = 4). The 10.45-second rendered clip is checked in once at [`web/public/animations/shape-first-method.mp4`](../../web/public/animations/shape-first-method.mp4). Its static preview, [`shape-first-method-poster.svg`](../../web/public/animations/shape-first-method-poster.svg), appears in the Vercel hero and as the video poster. Streamlit reads the same MP4 directly, and Vercel serves it as a public asset. Both players are user-initiated and dark themed.

ManimGX is a documentation/rendering dependency only. Running either application does not install or import it.

## Inspect and render

The rendering environment used for this scene is Python 3.14 with the pinned ManimGX dependency. From the repository root in PowerShell:

```powershell
py -3.14 -m venv visualizations/manimgx/.venv
visualizations/manimgx/.venv/Scripts/python.exe -m pip install -r visualizations/manimgx/requirements.txt
visualizations/manimgx/.venv/Scripts/manimgx.exe inspect visualizations/manimgx/shape_first_method.py
New-Item -ItemType Directory -Force visualizations/manimgx/.build | Out-Null
visualizations/manimgx/.venv/Scripts/manimgx.exe render visualizations/manimgx/shape_first_method.py --output visualizations/manimgx/.build/shape-first-method.mp4
Copy-Item -LiteralPath visualizations/manimgx/.build/shape-first-method.mp4 -Destination web/public/animations/shape-first-method.mp4 -Force
```

The renderer also writes its storyboard into `.build/`. Review the video and storyboard before replacing the checked-in public asset. The `.build/` directory is ignored by Git.

The app UI serves the committed MP4 without rendering it during deployment. In Vercel, it is loaded from `/animations/shape-first-method.mp4`; Streamlit uses the same repository file. Keep this path consistent if the asset is moved.

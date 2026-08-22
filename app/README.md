The Streamlit dashboard lives at the repository root as `streamlit_app.py`.

`app/app.py` was removed on purpose. Vercel treats that path as a Python serverless entrypoint and expects an exported `app`, `application`, or `handler`. Streamlit does not work that way.

Run:

```bash
py -m streamlit run streamlit_app.py
```

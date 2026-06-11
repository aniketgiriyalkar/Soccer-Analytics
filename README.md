# Soccer Analytics

Soccer Analytics is a World Cup modeling and visualization capstone focused on
expected goals, player comparison, and position-based analysis. The notebooks in
this repository show the full workflow from data prep through modeling and final
visuals.

## Quick start

1. Open the repository in Jupyter Notebook or JupyterLab.
2. Point the notebooks to the local `open-data` folder.
3. Run the data-preparation notebooks first, then the exploration and modeling
   notebooks, and finally the comparison notebooks.

## What’s in the repo

- `open-data/` contains the project data source.
- `2018WC-xGModel-Create a preprocessed Pickle file.ipynb` prepares the data.
- `2018WC-xGModel-Data Exploration.ipynb` explores the dataset.
- `2018WC-xGModel-Model Selection.ipynb` compares model options.
- `2018WC-xGModel-Model Application.ipynb` explores how the model behaves.
- `Best Players for each position-avg of top10 features for that position.ipynb`
  and `Best Players for each position-weighted average.ipynb` support player
  ranking and best-XI analysis.
- `WC2018-Player Comparision Visualizations.ipynb` holds the visuals used for
  the report and poster.

## What you should expect

This is a notebook-first analytics project rather than an app. The main outputs
are model comparisons, xG analysis, player comparisons, and presentation-ready
visuals.

## Notes

- The notebook names and folder structure are preserved from the original
  capstone.
- The project is easier to maintain if you keep the data-prep steps reproducible.
- If you only need the highlights, start with the visualization notebook and the
  model-selection notebook.

## Better tech if you revisit it

A strong modernization path would be:

- `Polars` or `Pandas` for data shaping.
- `DuckDB` for fast local analytics.
- `Quarto` or `Jupyter Book` for a polished, reproducible report.
- `Plotly` or `Altair` for interactive charts.
- `Streamlit` for a lightweight shareable dashboard.

That would make the project easier to rerun, easier to navigate, and easier to
present outside of notebook form.


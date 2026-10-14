# Infections by New World Arenaviruses

An interactive dashboard of human cases of three South American hemorrhagic fevers, each caused by a New World arenavirus carried by rodents:

| Virus | Disease | Country | Period |
|---|---|---|---|
| Machupo (MACV) | Bolivian hemorrhagic fever | Bolivia | 1960–2019 |
| Junin (JUNV) | Argentine hemorrhagic fever | Argentina | 2000–2020 |
| Guanarito (GTOV) | Venezuelan hemorrhagic fever | Venezuela | 1989–1997 |

**Live app:** https://YOUR-SUBDOMAIN.streamlit.app <!-- replace after deploying -->

The dashboard is built with [Streamlit](https://streamlit.io) and [Plotly](https://plotly.com/python/). It is a Python port of an earlier R Shiny app (`App_2.R`), with colors and type matched to [AtlasArena](https://atlas-arena.org).

---

## What the dashboard shows

Pick a virus from the **Virus** menu at the top right, and every panel updates. The whole dashboard fits on one screen as a 2 × 2 grid.

| Panel | Machupo | Junin | Guanarito |
|---|:---:|:---:|:---:|
| **Cases by site of infection**: map of cases by province or department | ✓ (all years) | ✓ (one year at a time, chosen with the **Year** slider) | ✓ (all years) |
| **Historical incidence**: cases over time | ✓ (by year) | ✓ (by year) | ✓ (by month) |
| **Cases by month of infection**: seasonality | ✓ | — | ✓ |
| **Cases by sex of patient**: male/female share | ✓ | ✓ | — |

Panels only appear where the data exists. Junin and Guanarito show three panels, so their map fills the left column.

Hover over a chart to see exact case counts. Hover over the **i** next to a panel title to read its notes, for example that Machupo cases are concentrated in El Beni, or that Junin has no province data for 2002.

---

## Repository contents

```
.
├── app.py                  # The Streamlit app
├── requirements.txt        # Python dependencies
├── Arenavirus_2.0.xlsx     # Case data (sheets: Year, Province, Sex, Age)
├── provinces.geojson       # Province/department boundaries for Argentina, Bolivia, Venezuela
├── AALogo.svg              # AtlasArena logo shown in the top-left corner
└── .streamlit/
    └── config.toml         # Theme colors (AtlasArena palette)
```

### Data file layout

`Arenavirus_2.0.xlsx` has these sheets:

- **Year**: one row per virus and time period. Columns include `Virus` (`MACV`, `JUNV`, `GTOV`), `Year`, `Month`, `Date` and `Cases`.
- **Province**: case counts by `name` (province/department) and `Year`. `Year = "TOTAL"` holds all-years totals. Province names must match the Natural Earth names in `provinces.geojson`.
- **Sex**: male and female case counts per year (`MACV_Male`, `MACV_Female`, `JUNV_Male`, `JUNV_Female`), plus a `Total` row and a `Percentage` row. The pie charts use the `Percentage` row.
- **Age**: included in the workbook but not yet shown in the dashboard.

---

## Run it locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/epipandit/atlas-arena-cases-dashboard.git
cd YOUR-REPO
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

---


- **Design:** colors and typography follow [AtlasArena](https://atlas-arena.org) ([source](https://github.com/developmentseed/atlasarena), MIT License, © 2024 Development Seed).

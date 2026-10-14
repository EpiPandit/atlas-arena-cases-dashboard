"""
Infections by New World Arenaviruses: Streamlit port of App_2.R
Single-screen 2 x 2 dashboard, styled after atlas-arena.org.

Run:  streamlit run app.py
Same folder: Arenavirus_2.0.xlsx, provinces.geojson, AALogo.svg (or AALogo.png),
             .streamlit/config.toml
"""

import base64
import io
import json
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Layout knob: height (px) of each chart. Lower it if the bottom row is cut
# off on a small screen; raise it on a large monitor.
# ---------------------------------------------------------------------------
CHART_H = 220
CARD_CHROME = 78   # card padding + title row; used to align the tall map

# ---------------------------------------------------------------------------
# AtlasArena palette (from the site's Chakra theme: src/config/theme.jsx)
# ---------------------------------------------------------------------------
BLUE = {50: "#DAE7F7", 100: "#B3CDF5", 300: "#77A9E5", 500: "#3776ED",
        600: "#3564E5", 700: "#365AD9", 800: "#334BB5", 900: "#2C3F85"}
SECONDARY = {50: "#FCFBF7", 100: "#f3eace", 200: "#e8d69f", 300: "#dcbd6d",
             400: "#d3a74c", 500: "#ca8d36", 700: "#945229"}
GRAY = {200: "#d8d9df", 300: "#b6b7c3", 500: "#707287", 600: "#5a5b6f", 700: "#49495b"}
RED = "#E53E3E"
FONT = "Montserrat, 'Montserrat Variable', sans-serif"
MAP_SCALE = [[0.0, SECONDARY[100]], [0.25, SECONDARY[300]],
             [0.5, BLUE[500]], [1.0, BLUE[900]]]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

APP_DIR = Path(__file__).parent

st.set_page_config(page_title="Infections by New World Arenaviruses",
                   page_icon="🐀", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

html, body, .stApp, .stMarkdown, p, label, input, button, select {{
    font-family: {FONT} !important;
}}
.stApp {{ background-color: {SECONDARY[50]}; }}
[data-testid="stHeader"] {{ background: transparent; }}

/* Use the whole screen */
.block-container {{
    padding: 2.5rem 1.5rem .75rem 1.5rem !important;
    max-width: 100% !important;
}}
[data-testid="stVerticalBlock"] {{ gap: .75rem; }}

/* Header: logo in the top-left corner, then titles */
.aa-header {{ display: flex; align-items: center; gap: .9rem; }}
.aa-header img {{ height: 60px; width: 60px; flex: none; }}
.aa-header .sub {{ color: {GRAY[500]}; font-size: .85rem; font-weight: 500; }}
.aa-header h1 {{
    color: {BLUE[900]}; font-weight: 700; font-size: 1.5rem;
    line-height: 1.2; margin: 0; padding: 0;
}}

/* Card title, like the site's InnerHeading. Notes show on hover over (i). */
.aa-card-title {{
    color: {BLUE[900]}; font-weight: 600; font-size: 1rem;
    border-bottom: 2px solid {BLUE[800]};
    padding-bottom: .25rem; display: inline-block;
}}
.aa-info {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.1rem; height: 1.1rem; margin-left: .4rem; border-radius: 50%;
    background: {SECONDARY[100]}; color: {SECONDARY[700]};
    border: 1px solid {SECONDARY[400]};
    font-size: .7rem; font-weight: 700; cursor: help; vertical-align: 2px;
}}

/* Bordered cards */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: #ffffff; border-color: {GRAY[200]} !important;
    border-radius: 6px;
}}
</style>
""", unsafe_allow_html=True)


def card_title(title: str, note: str | None = None):
    info = ""
    if note:
        safe = note.replace('"', "&quot;")
        info = f'<span class="aa-info" title="{safe}" tabindex="0">i</span>'
    st.markdown(f'<span class="aa-card-title">{title}</span>{info}',
                unsafe_allow_html=True)


def base_layout(fig: go.Figure, height: int = CHART_H, **kwargs) -> go.Figure:
    fig.update_layout(
        height=height,
        font=dict(family=FONT, color=GRAY[700], size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(font_family=FONT),
        margin=dict(l=8, r=8, t=8, b=8),
    )
    fig.update_layout(**kwargs)
    return fig


def style_axes(fig: go.Figure):
    fig.update_xaxes(showgrid=False, linecolor=GRAY[300], ticks="outside",
                     tickcolor=GRAY[300], title=None)
    fig.update_yaxes(gridcolor=SECONDARY[100], zeroline=False,
                     title_text="Cases", title_standoff=6)
    return fig


def show(fig: go.Figure):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Logo
# AALogo.svg is a wrapper around an embedded PNG on a wide canvas, which
# st.logo and some browsers won't draw reliably. Pull out the PNG, trim the
# empty space, and embed it directly. A plain AALogo.png also works.
# ---------------------------------------------------------------------------
@st.cache_data
def load_logo_data_uri() -> str | None:
    png_path, svg_path = APP_DIR / "AALogo.png", APP_DIR / "AALogo.svg"
    img = None
    if png_path.exists():
        img = Image.open(png_path)
    elif svg_path.exists():
        text = svg_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'data:image/(?:png|jpe?g);base64,([^"\']+)', text)
        if m:
            raw = base64.b64decode(re.sub(r"\s", "", m.group(1)))
            img = Image.open(io.BytesIO(raw))
        else:  # a "real" vector SVG: use it as-is
            return ("data:image/svg+xml;base64,"
                    + base64.b64encode(text.encode()).decode())
    if img is None:
        return None
    img = img.convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)
    img.thumbnail((240, 240))   # sharp at 60px on high-DPI screens, small payload
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
DATA_CANDIDATES = [
    APP_DIR / "Arenavirus_2.0.xlsx",
    APP_DIR / "Arenavirus_2_0.xlsx",
    Path.home() / "Desktop" / "Arenavirus_2.0.xlsx",   # where App_2.R looked
]


@st.cache_data
def load_data():
    path = next((p for p in DATA_CANDIDATES if p.exists()), None)
    if path is None:
        return None
    df_year = pd.read_excel(path, sheet_name="Year")
    df_province = pd.read_excel(path, sheet_name="Province")
    df_sex = pd.read_excel(path, sheet_name="Sex")
    df_year["Month"] = pd.Categorical(df_year["Month"], categories=MONTHS,
                                      ordered=True)
    df_province["Year"] = df_province["Year"].astype(str)
    df_sex["Year"] = df_sex["Year"].astype(str)
    return df_year, df_province, df_sex


@st.cache_data
def load_geo():
    with open(APP_DIR / "provinces.geojson", encoding="utf-8") as f:
        geo = json.load(f)
    props = pd.DataFrame([feat["properties"] for feat in geo["features"]])
    return geo, props


data = load_data()
if data is None:
    st.error("Arenavirus_2.0.xlsx was not found. Put it in the same folder as "
             "app.py (or on your Desktop) and reload the page.")
    st.stop()

df_year, df_province, df_sex = data
geojson, geo_props = load_geo()

VIRUSES = {
    "Machupo":   {"code": "MACV", "country": "Bolivia",
                  "title": "Bolivian Hemorrhagic Fever, 1960-2019", "bar": BLUE[800]},
    "Junin":     {"code": "JUNV", "country": "Argentina",
                  "title": "Argentine Hemorrhagic Fever, 2000-2020", "bar": BLUE[800]},
    "Guanarito": {"code": "GTOV", "country": "Venezuela",
                  "title": "Venezuelan Hemorrhagic Fever, 1989-1997", "bar": SECONDARY[700]},
}

# ---------------------------------------------------------------------------
# Header row: logo + titles | virus selector | year slider (Junin only)
# ---------------------------------------------------------------------------
h_title, h_virus, h_year = st.columns([3.2, 1, 1.4], vertical_alignment="bottom")

with h_virus:
    virus = st.selectbox("Virus", list(VIRUSES.keys()))
meta = VIRUSES[virus]
code = meta["code"]

year = None
with h_year:
    if virus == "Junin":
        year = st.slider("Year", min_value=2000, max_value=2020, value=2000,
                         help="Adjust the slider to see cases change by year on "
                              "the map of Argentina. Data is not available for 2002.")

with h_title:
    logo = load_logo_data_uri()
    logo_html = f'<img src="{logo}" alt="AtlasArena logo">' if logo else ""
    st.markdown(
        f'<div class="aa-header">{logo_html}<div>'
        f'<div class="sub">Infections by New World Arenaviruses</div>'
        f'<h1>{meta["title"]}</h1></div></div>',
        unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------
def province_map(country: str, cases: pd.DataFrame, height: int,
                 empty_msg: str | None = None) -> go.Figure:
    shapes = geo_props[geo_props["country"] == country].copy()
    merged = shapes.merge(cases, on="name", how="left")
    with_data = merged.dropna(subset=["CASES"])

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson, featureidkey="properties.id",
        locations=merged["id"], z=[0] * len(merged),
        colorscale=[[0, GRAY[200]], [1, GRAY[200]]], showscale=False,
        marker_line_color="white", marker_line_width=0.8,
        hovertext=merged["name"], hoverinfo="text",
    ))
    if not with_data.empty:
        zmax = with_data["CASES"].max()
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey="properties.id",
            locations=with_data["id"], z=with_data["CASES"],
            zmin=0, zmax=zmax, colorscale=MAP_SCALE,
            marker_line_color="white", marker_line_width=0.8,
            colorbar=dict(title=dict(text="Cases"), thickness=10, len=0.7,
                          outlinewidth=0, tickformat=","),
            customdata=with_data["name"],
            hovertemplate="<b>%{customdata}</b><br>%{z:,} cases<extra></extra>",
        ))
        text_colors = ["white" if v / zmax > 0.45 else BLUE[900]
                       for v in with_data["CASES"]]
        fig.add_trace(go.Scattergeo(
            lon=with_data["lon"], lat=with_data["lat"], mode="text",
            text=[f"{int(v):,}" for v in with_data["CASES"]],
            textfont=dict(family=FONT, size=13, color=text_colors),
            hoverinfo="skip", showlegend=False,
        ))
    if empty_msg:
        fig.add_annotation(text=empty_msg, x=0.5, y=0.02, xref="paper",
                           yref="paper", showarrow=False,
                           font=dict(color=GRAY[500], size=12))
    fig.update_geos(fitbounds="locations", visible=False,
                    bgcolor="rgba(0,0,0,0)", projection_type="mercator")
    return base_layout(fig, height=height, margin=dict(l=0, r=0, t=0, b=0))


def panel_map(height: int):
    if virus == "Junin":
        cases = df_province[(df_province["Virus"] == "JUNV") &
                            (df_province["Year"] == str(year))][["name", "CASES"]]
        title = f"Cases by Site of Infection, {year}"
        note = ("Adjust the year slider to see cases change by year. "
                "Data is not available for 2002.")
    else:
        cases = df_province[(df_province["Virus"] == code) &
                            (df_province["Year"] == "TOTAL")][["name", "CASES"]]
        title = "Cases by Site of Infection"
        note = ("Cases are restricted primarily to the El Beni province."
                if virus == "Machupo" else None)
    empty = f"No province data for {year}" if virus == "Junin" and cases.empty else None
    with st.container(border=True):
        card_title(title, note)
        show(province_map(meta["country"], cases, height, empty))


def panel_history():
    yr = df_year[df_year["Virus"] == code]
    if virus == "Guanarito":
        x, y = yr["Date"], yr["Cases"]
        xaxis = dict(dtick="M12", tickformat="%Y")
        hover = "%{x|%B %Y}: %{y} cases<extra></extra>"
        note = "Graph is reproduced from https://doi.org/10.1086/516299."
    else:
        agg = yr.groupby("Year", as_index=False)["Cases"].sum()
        x, y = agg["Year"], agg["Cases"]
        xaxis = dict(dtick=5)
        hover = "%{x}: %{y:,} cases<extra></extra>"
        note = None
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=meta["bar"],
                           hovertemplate=hover))
    style_axes(base_layout(fig, xaxis=xaxis, bargap=0.15))
    with st.container(border=True):
        card_title("Historical Incidence", note)
        show(fig)


def panel_month():
    yr = df_year[df_year["Virus"] == code].dropna(subset=["Month"])
    by_month = yr.groupby("Month", observed=False, as_index=False)["Cases"].sum()
    fig = go.Figure(go.Bar(
        x=[m[:3] for m in by_month["Month"].astype(str)], y=by_month["Cases"],
        customdata=by_month["Month"].astype(str), marker_color=meta["bar"],
        hovertemplate="%{customdata}: %{y:,} cases<extra></extra>"))
    style_axes(base_layout(fig))
    with st.container(border=True):
        card_title("Cases by Month of Infection",
                   "Arenavirus hemorrhagic fever is seasonal, corresponding "
                   "with agricultural harvests.")
        show(fig)


def panel_sex():
    pct = df_sex[df_sex["Year"] == "Percentage"].iloc[0]
    tot = df_sex[df_sex["Year"] == "Total"].iloc[0]
    fig = go.Figure(go.Pie(
        labels=["Male", "Female"],
        values=[pct[f"{code}_Male"], pct[f"{code}_Female"]],
        customdata=[tot[f"{code}_Male"], tot[f"{code}_Female"]],
        sort=False, direction="clockwise",
        marker=dict(colors=[BLUE[600], RED], line=dict(color="white", width=2)),
        texttemplate="%{label}<br>%{percent:.2%}", textposition="inside",
        textfont=dict(family=FONT, size=14, color="white"),
        hovertemplate="%{label}: %{customdata:,.0f} cases<extra></extra>",
    ))
    base_layout(fig, showlegend=False)
    with st.container(border=True):
        card_title("Cases by Sex of Patient",
                   "Arenavirus hemorrhagic fever burden is heaviest among men "
                   "due to agricultural exposure. Data is not available for "
                   "all years. Male patients are in blue, female patients are in red.")
        show(fig)


# Which panels this virus shows (same rules as App_2.R)
extra = []
if virus in ("Machupo", "Guanarito"):
    extra.append(panel_month)
if virus in ("Machupo", "Junin"):
    extra.append(panel_sex)

if len(extra) == 2:
    # Machupo: full 2 x 2 grid
    top_l, top_r = st.columns(2)
    with top_l:
        panel_map(CHART_H)
    with top_r:
        panel_history()
    bot_l, bot_r = st.columns(2)
    with bot_l:
        extra[0]()
    with bot_r:
        extra[1]()
else:
    # Junin / Guanarito: 3 panels; the map fills the left column (both rows)
    left, right = st.columns(2)
    with left:
        panel_map(2 * CHART_H + CARD_CHROME)
    with right:
        panel_history()
        extra[0]()

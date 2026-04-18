# ==============================================================================
#  EnviroMonitor Pro – Streamlit Edition
#  Full port of ShinyR v6: upload, mapping, TS, stats, exceedances,
#  temporal patterns, wind rose 2×2, polar plots 2×2, Excel export
#
#  INSTALL:
#    pip install streamlit pandas numpy plotly openpyxl xlrd scipy windrose
#                matplotlib requests
#
#  RUN LOCALLY:
#    streamlit run app.py
#
#  DEPLOY (Streamlit Cloud):
#    Push app.py + requirements.txt to GitHub → connect on share.streamlit.io
# ==============================================================================

import warnings, io, re, calendar
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.cm import get_cmap
import streamlit as st
from scipy import stats as scipy_stats

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "EnviroMonitor Pro",
    page_icon   = "🌿",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ==============================================================================
#  THEME / CSS
# ==============================================================================
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700&family=Rajdhani:wght@500;700&display=swap');

html, body, [class*="css"] {
  font-family: 'Exo 2', sans-serif !important;
  background-color: #050d1a !important;
  color: #CFD8DC !important;
}
.main .block-container { padding: 1.2rem 2rem 2rem 2rem; max-width: 100%; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#071525 0%,#0a1f35 100%) !important;
  border-right: 1px solid #00E5FF22;
}
section[data-testid="stSidebar"] * { color: #90CAF9 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stDateInput label,
section[data-testid="stSidebar"] .stNumberInput label { color: #78909C !important; font-size: 12px !important; }

/* Cards / metric */
div[data-testid="metric-container"] {
  background: linear-gradient(135deg,#0d1f3c,#0a1628) !important;
  border: 1px solid #1a3a5c; border-radius: 12px; padding: 14px 18px;
  box-shadow: 0 4px 20px rgba(0,229,255,0.07);
}
div[data-testid="metric-container"] > label {
  color: #78909C !important; font-size: 12px;
}
div[data-testid="metric-container"] > div {
  color: #00E5FF !important; font-family: 'Rajdhani',sans-serif !important;
  font-size: 26px; font-weight: 700;
}

/* Tabs */
button[data-baseweb="tab"] {
  background: #0d1f3c !important; color: #78909C !important;
  border-radius: 8px 8px 0 0 !important;
  font-family: 'Exo 2',sans-serif !important; font-size: 13px !important;
  border: 1px solid #1a3a5c !important; margin-right: 3px;
  transition: all 0.2s;
}
button[data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg,#006064,#00838F) !important;
  color: #E0F7FA !important; border-color: #00E5FF44 !important;
}
div[data-testid="stTabs"] > div { border-bottom: 2px solid #00E5FF22 !important; }

/* Headings */
h1,h2,h3 { font-family: 'Rajdhani',sans-serif !important; color: #E0F7FA !important; }
h1 { font-size: 28px !important; font-weight: 700 !important; letter-spacing: 1px; }
h2 { font-size: 20px !important; color: #00E5FF !important; }
h3 { font-size: 16px !important; color: #90CAF9 !important; }

/* Dividers */
hr { border-color: #1a3a5c !important; margin: 10px 0; }

/* Dataframe */
div[data-testid="stDataFrame"] { background: #0a1628; border-radius: 10px; }
thead tr th { background: #0d2137 !important; color: #00E5FF !important;
              font-family: 'Rajdhani',sans-serif !important; }
tbody tr:nth-child(even) td { background: #0d1f3c !important; }
tbody tr:hover td { background: #00E5FF11 !important; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg,#006064,#00ACC1) !important;
  color: #E0F7FA !important; border: none !important;
  border-radius: 8px !important; font-family:'Exo 2',sans-serif !important;
  font-weight: 600 !important; padding: 8px 20px;
  box-shadow: 0 2px 12px rgba(0,229,255,0.2); transition: all 0.2s;
}
.stButton > button:hover { box-shadow: 0 4px 20px rgba(0,229,255,0.4) !important; transform: translateY(-1px); }

/* Download button */
.stDownloadButton > button {
  background: linear-gradient(135deg,#1B5E20,#388E3C) !important;
  color: #E8F5E9 !important; border: none !important; border-radius: 8px !important;
}

/* Expander */
details { background: #0d1f3c !important; border: 1px solid #1a3a5c !important;
          border-radius: 10px !important; }
summary { color: #00E5FF !important; font-family: 'Rajdhani',sans-serif !important;
          font-weight: 600 !important; }

/* Select, inputs */
div[data-baseweb="select"] { background: #0d2137 !important; border-radius: 8px; }
.stDateInput input, .stNumberInput input, .stTextInput input {
  background: #0d2137 !important; color: #90CAF9 !important;
  border: 1px solid #1a3a5c !important; border-radius: 6px !important;
}

/* Upload */
div[data-testid="stFileUploadDropzone"] {
  background: #0d1f3c !important; border: 2px dashed #00E5FF44 !important;
  border-radius: 12px !important;
}
div[data-testid="stFileUploadDropzone"]:hover { border-color: #00E5FF99 !important; }

/* Section header boxes */
.section-header {
  background: linear-gradient(90deg,#0d2137,#0a2a4a);
  border: 1px solid #00E5FF22; border-radius: 10px;
  padding: 10px 18px; margin-bottom: 14px;
}
.section-header h3 { margin: 0; color: #E0F7FA !important; font-size: 15px !important; }

/* Status pills */
.pill-demo { background: linear-gradient(135deg,#E65100,#FF8F00);
             color:#fff; padding: 3px 12px; border-radius: 20px;
             font-size: 11px; font-weight: 700; font-family:'Rajdhani',sans-serif; }
.pill-user { background: linear-gradient(135deg,#1B5E20,#43A047);
             color:#fff; padding: 3px 12px; border-radius: 20px;
             font-size: 11px; font-weight: 700; }
.pill-err  { background: linear-gradient(135deg,#B71C1C,#E53935);
             color:#fff; padding: 3px 12px; border-radius: 20px; font-size: 11px; }

/* Wide plotly charts */
div[data-testid="stPlotlyChart"] { width: 100% !important; }

/* Alert boxes */
.alert-warn { background:#1c1000; border:1px solid #FF9800; border-radius:8px;
              padding:10px 14px; color:#FFB74D; font-size:13px; }
.alert-ok   { background:#001c00; border:1px solid #4CAF50; border-radius:8px;
              padding:10px 14px; color:#81C784; font-size:13px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ==============================================================================
#  COLOUR PALETTE
# ==============================================================================
PALETTE = [
    "#00E5FF","#FF6B6B","#69FF47","#FFD93D","#C77DFF","#FF9A3C",
    "#00B4D8","#F72585","#4CC9F0","#FFBE0B","#8338EC","#3A86FF",
]
SEASONS   = ["Spring","Summer","Autumn","Winter"]
DOW_ORDER = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
MON_ORDER = list(calendar.month_abbr)[1:]  # Jan … Dec

def site_palette(sites):
    return {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(sorted(sites))}

def hex_rgba(hex_color: str, alpha: float) -> str:
    """Convert a #RRGGBB hex string + alpha (0–1) to 'rgba(r,g,b,a)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ==============================================================================
#  PLOTLY DARK LAYOUT DEFAULTS
# ==============================================================================
PLOTLY_DARK = dict(
    paper_bgcolor = "#0a1628",
    plot_bgcolor  = "#0d1f3c",
    font          = dict(family="'Exo 2', sans-serif", color="#CFD8DC"),
    title_font    = dict(family="'Rajdhani', sans-serif", color="#E0F7FA", size=16),
    legend        = dict(bgcolor="rgba(13,31,60,0.85)", bordercolor="#1a3a5c",
                         font=dict(color="#CFD8DC", size=11),
                         orientation="h", yanchor="bottom", y=-0.28),
    margin        = dict(t=55, b=70, l=65, r=20),
    hovermode     = "x unified",
)

# Axis style dict – applied via update_xaxes/update_yaxes so it never
# collides with custom xaxis= / yaxis= kwargs in update_layout.
DARK_AXIS = dict(color="#90CAF9", gridcolor="#1a3a5c", zerolinecolor="#1a3a5c")

def apply_dark(fig, title="", xlab="", ylab=""):
    """Apply dark theme. Uses update_xaxes/update_yaxes – safe for subplots."""
    fig.update_layout(**PLOTLY_DARK, title_text=title)
    fig.update_xaxes(**DARK_AXIS, title_text=xlab)
    fig.update_yaxes(**DARK_AXIS, title_text=ylab)
    return fig

# ==============================================================================
#  DEMO DATA GENERATOR
# ==============================================================================
@st.cache_data(show_spinner=False)
def make_demo_data():
    rng = np.random.default_rng(42)
    sites  = ["Site_A","Site_B","Site_C"]
    params = ["H2S","Ozone","NOx","WindSpeed","WindDirection"]
    dts    = pd.date_range("2022-01-01","2023-12-31 23:00", freq="h", tz="UTC")
    n      = len(dts)
    doy    = dts.day_of_year.values
    hod    = dts.hour.values
    seas   = np.sin(2*np.pi*(doy-80)/365)
    diur   = np.sin(2*np.pi*(hod-6)/24)
    rows   = []
    offsets = {"Site_A":0,"Site_B":3.5,"Site_C":-2}
    for site in sites:
        so = offsets[site]
        for param in params:
            if param=="H2S":
                v = 5+so*.6+3*seas+2*diur+rng.normal(0,1.8,n)
                sp = rng.random(n)<0.02
                v[sp] += rng.exponential(12,sp.sum())
                v = np.maximum(0,v)
            elif param=="Ozone":
                v = np.maximum(0,42+so*2.5+18*seas+22*diur+rng.normal(0,9,n))
            elif param=="NOx":
                rush = np.isin(hod,[7,8,9,17,18,19]).astype(float)*22
                v = np.maximum(0,38+so*1.8-8*seas-12*diur+rng.normal(0,11,n)+rush)
            elif param=="WindSpeed":
                v = np.maximum(0,3.2+so*.25+1.4*seas+np.abs(rng.normal(0,1.4,n)))
            else:  # WindDirection
                base = {"Site_A":225,"Site_B":205,"Site_C":255}[site]
                v = (base+rng.normal(0,55,n)) % 360
            mask = rng.random(n) < 0.02
            v = v.astype(float); v[mask] = np.nan
            tmp = pd.DataFrame({"Sitename":site,"Parameter":param,
                                "datetime":dts,"value":v})
            rows.append(tmp)
    return pd.concat(rows, ignore_index=True)

DEMO_DATA = make_demo_data()

# ==============================================================================
#  HELPERS
# ==============================================================================
def get_season(s: pd.Series) -> pd.Series:
    m = s.dt.month
    return pd.cut(m,
        bins  = [0,2,5,8,11,12],
        labels= ["Winter","Spring","Summer","Autumn","Winter"],
        ordered=False
    ).astype(str).replace({"nan":"Winter"})

def roll24(s: pd.Series) -> pd.Series:
    return s.rolling(24, min_periods=1).mean()

def describe_stats(df):
    grp = df.groupby("Sitename")["value"]
    out = pd.DataFrame({
        "N"        : grp.count(),
        "Missing"  : df.groupby("Sitename")["value"].apply(lambda x: x.isna().sum()),
        "Pct_Miss" : df.groupby("Sitename")["value"].apply(lambda x: round(100*x.isna().mean(),2)),
        "Mean"     : grp.mean().round(3),
        "SD"       : grp.std().round(3),
        "Median"   : grp.median().round(3),
        "Min"      : grp.min().round(3),
        "P05"      : grp.quantile(0.05).round(3),
        "P25"      : grp.quantile(0.25).round(3),
        "P75"      : grp.quantile(0.75).round(3),
        "P95"      : grp.quantile(0.95).round(3),
        "Max"      : grp.max().round(3),
    }).reset_index()
    return out

# ── datetime auto-parse ───────────────────────────────────────────────────────
DATETIME_FMTS = [
    "%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M",
    "%Y/%m/%d %H:%M:%S","%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d","%d/%m/%Y","%m/%d/%Y",
]

def try_parse_datetime(series, fmt=None):
    if fmt and fmt != "auto":
        try:
            return pd.to_datetime(series, format=fmt, utc=True, errors="coerce")
        except Exception:
            pass
    for f in DATETIME_FMTS:
        try:
            parsed = pd.to_datetime(series, format=f, utc=True, errors="coerce")
            if parsed.notna().mean() > 0.5:
                return parsed
        except Exception:
            pass
    return pd.to_datetime(series, utc=True, errors="coerce", infer_datetime_format=True)

def guess_col(cols, patterns):
    for p in patterns:
        for c in cols:
            if re.search(p, c, re.IGNORECASE):
                return c
    return cols[0]

# ── detect separate date + time columns ──────────────────────────────────────
def detect_and_combine_datetime(df):
    """
    If the file has separate Date and Time columns, combine them.
    Returns (df_modified, combined_col_name, message)
    """
    cols_lower = {c.lower(): c for c in df.columns}
    date_keys  = ["date"]
    time_keys  = ["time"]
    date_col   = next((cols_lower[k] for k in date_keys if k in cols_lower), None)
    time_col   = next((cols_lower[k] for k in time_keys if k in cols_lower), None)

    if date_col and time_col and date_col != time_col:
        combined_name = "datetime_combined"
        try:
            df[combined_name] = pd.to_datetime(
                df[date_col].astype(str).str.strip() + " " +
                df[time_col].astype(str).str.strip(),
                errors="coerce", utc=True, infer_datetime_format=True
            )
            ok = df[combined_name].notna().mean()
            if ok > 0.5:
                return df, combined_name, (
                    f"✅ Combined '{date_col}' + '{time_col}' → '{combined_name}' "
                    f"({ok*100:.0f}% parsed)")
        except Exception as e:
            pass
    return df, None, None

# ==============================================================================
#  SESSION STATE INIT
# ==============================================================================
if "active_data" not in st.session_state:
    st.session_state.active_data = DEMO_DATA.copy()
    st.session_state.data_source = "demo"

# ==============================================================================
#  SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0 6px 0;'>
      <span style='font-family:Rajdhani,sans-serif;font-size:22px;
                   font-weight:700;color:#00E5FF;letter-spacing:2px;'>
        🌿 ENVIROMONITOR
      </span><br>
      <span style='font-size:11px;color:#546E7A;'>PRO · Streamlit Edition</span>
    </div>
    """, unsafe_allow_html=True)

    # Data source badge
    if st.session_state.data_source == "demo":
        st.markdown('<span class="pill-demo">DEMO DATA</span>', unsafe_allow_html=True)
    elif st.session_state.data_source == "user":
        st.markdown(f'<span class="pill-user">USER DATA – {len(st.session_state.active_data):,} rows</span>',
                    unsafe_allow_html=True)

    st.markdown("---")

    ad = st.session_state.active_data
    params = sorted(ad["Parameter"].unique())
    sites  = sorted(ad["Sitename"].unique())

    sel_param = st.selectbox("📌 Parameter", params)
    sel_sites = st.multiselect("🏭 Sites", sites, default=sites)

    dt_min = ad["datetime"].min().date()
    dt_max = ad["datetime"].max().date()
    date_range = st.date_input("📅 Date Range",
        value=(dt_min, dt_max), min_value=dt_min, max_value=dt_max)
    if len(date_range) == 2:
        d1, d2 = pd.Timestamp(date_range[0], tz="UTC"), pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta("23h59m")
    else:
        d1, d2 = pd.Timestamp(dt_min, tz="UTC"), pd.Timestamp(dt_max, tz="UTC") + pd.Timedelta("23h59m")

    st.markdown("---")
    st.markdown('<span style="color:#00E5FF;font-size:12px;font-weight:600;">⚠️ THRESHOLDS</span>',
                unsafe_allow_html=True)
    thresh_1h  = st.number_input("1-hr Average Limit",  value=10.0, min_value=0.0, step=0.5)
    thresh_24h = st.number_input("24-hr Rolling Limit", value=8.0,  min_value=0.0, step=0.5)

# ==============================================================================
#  FILTERED DATA
# ==============================================================================
@st.cache_data(show_spinner=False)
def filter_data(data_json, param, sites_tuple, d1, d2):
    df = pd.read_json(io.StringIO(data_json), orient="records")
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[
        (df["Parameter"] == param) &
        (df["Sitename"].isin(sites_tuple)) &
        (df["datetime"] >= d1) &
        (df["datetime"] <= d2)
    ].sort_values(["Sitename","datetime"]).reset_index(drop=True)

data_json = st.session_state.active_data.to_json(orient="records", date_format="iso")
filt = filter_data(data_json, sel_param, tuple(sorted(sel_sites)), d1, d2)

# Enrich with rolling average + exceedances
def enrich_data(df, t1, t24):
    frames = []
    for site, grp in df.groupby("Sitename"):
        g = grp.sort_values("datetime").copy()
        g["roll24"]  = roll24(g["value"])
        g["exc_1h"]  = g["value"].notna()  & (g["value"]  > t1)
        g["exc_24h"] = g["roll24"].notna() & (g["roll24"] > t24)
        g["hod"]     = g["datetime"].dt.hour
        g["dow"]     = g["datetime"].dt.day_name().str[:3]
        g["mon"]     = g["datetime"].dt.strftime("%b")
        g["season"]  = get_season(g["datetime"])
        frames.append(g)
    return pd.concat(frames, ignore_index=True) if frames else df

enriched = enrich_data(filt, thresh_1h, thresh_24h)
pal = site_palette(sites)

# ==============================================================================
#  PAGE HEADER
# ==============================================================================
st.markdown("""
<div style='background:linear-gradient(90deg,#0d2137,#0a2a4a);
            border:1px solid #00E5FF22;border-radius:14px;
            padding:18px 28px;margin-bottom:18px;'>
  <h1 style='margin:0;font-size:26px;'>🌿 EnviroMonitor Pro</h1>
  <p style='margin:4px 0 0 0;color:#546E7A;font-size:13px;'>
    Environmental Time Series · Exceedance Analysis · Wind Rose · Polar Plots
  </p>
</div>""", unsafe_allow_html=True)

# ==============================================================================
#  TABS
# ==============================================================================
TAB_LABELS = [
    "📂 Data Input","📋 Overview","📈 Time Series","📊 Stats",
    "🎯 Threshold","⚠️ Exceedances","⏰ Temporal",
    "🌬️ Wind Rose","🌀 Polar Plot","⬇️ Export"
]
tabs = st.tabs(TAB_LABELS)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 0  DATA INPUT
# ─────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("### 📂 Upload Your Data File")
    left, right = st.columns([1,1], gap="large")

    with left:
        # ── Upload ──────────────────────────────────────────────────────────
        with st.expander("📁 File Settings", expanded=True):
            uploaded = st.file_uploader(
                "Upload CSV / TSV / TXT / XLSX / XLS",
                type=["csv","tsv","txt","xlsx","xls"])
            c1,c2 = st.columns(2)
            sep_choice = c1.selectbox("Delimiter (text files)",
                ["Comma ,",  "Semicolon ;", "Tab \\t", "Pipe |"])
            SEP_MAP = {"Comma ,": ",", "Semicolon ;": ";", "Tab \\t": "\t", "Pipe |": "|"}
            sep = SEP_MAP[sep_choice]
            has_header = c2.checkbox("First row = header", value=True)
            dt_fmt = st.selectbox("Datetime format",
                ["Auto-detect","%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
                 "%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M",
                 "%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M",
                 "%Y-%m-%dT%H:%M:%S"])
            dt_fmt_val = None if dt_fmt=="Auto-detect" else dt_fmt

        # ── Load buttons ────────────────────────────────────────────────────
        bcol1, bcol2 = st.columns(2)
        if bcol1.button("▶ Use Demo Data", use_container_width=True):
            st.session_state.active_data = DEMO_DATA.copy()
            st.session_state.data_source = "demo"
            st.success("✅ Demo data loaded! Switch to any analysis tab.")
            st.rerun()

        if bcol2.button("✔ Load Uploaded File", use_container_width=True):
            if uploaded is None:
                st.error("❌ No file uploaded yet.")
            else:
                try:
                    ext = uploaded.name.rsplit(".",1)[-1].lower()
                    if ext in ("xlsx","xls"):
                        raw = pd.read_excel(uploaded, header=0 if has_header else None)
                    else:
                        raw = pd.read_csv(uploaded, sep=sep,
                                          header=0 if has_header else None,
                                          na_values=["","NA","N/A","null","NULL"])

                    # ── Detect separate Date + Time columns ──────────────
                    raw, combined_col, comb_msg = detect_and_combine_datetime(raw)
                    if comb_msg:
                        st.info(comb_msg)

                    # Store raw for mapping
                    st.session_state.raw_df       = raw
                    st.session_state.combined_col = combined_col
                    st.success(f"✅ File read: {len(raw):,} rows × {len(raw.columns)} cols")
                except Exception as e:
                    st.error(f"❌ File read error: {e}")

        # ── Column mapping ───────────────────────────────────────────────────
        if "raw_df" in st.session_state:
            raw   = st.session_state.raw_df
            ccols = list(raw.columns)

            st.markdown("#### 🔀 Column Mapping")
            with st.container():
                ma, mb = st.columns(2)
                col_site  = ma.selectbox("Sitename column",  ccols,
                    index=ccols.index(guess_col(ccols,["site","station","location","monitor","name"])))
                col_param = mb.selectbox("Parameter column", ccols,
                    index=ccols.index(guess_col(ccols,["param","pollutant","analyte","variable","species"])))

                # datetime column: prefer combined if detected
                dt_choices = ccols.copy()
                dt_default = st.session_state.combined_col or \
                             guess_col(ccols,["datetime","timestamp","date_time","dt"])
                mc, md = st.columns(2)
                col_dt  = mc.selectbox("Datetime column", dt_choices,
                    index=dt_choices.index(dt_default) if dt_default in dt_choices else 0)
                col_val = md.selectbox("Value column", ccols,
                    index=ccols.index(guess_col(ccols,["value","conc","concentration","measurement","reading","data"])))

            if st.button("🚀 Apply Mapping & Activate", use_container_width=True):
                try:
                    mapped = raw[[col_site, col_param, col_dt, col_val]].copy()
                    mapped.columns = ["Sitename","Parameter","datetime","value"]
                    mapped["Sitename"]  = mapped["Sitename"].astype(str)
                    mapped["Parameter"] = mapped["Parameter"].astype(str)
                    mapped["datetime"]  = try_parse_datetime(mapped["datetime"].astype(str), dt_fmt_val)
                    mapped["value"]     = pd.to_numeric(mapped["value"], errors="coerce")
                    mapped = mapped.dropna(subset=["datetime"]).sort_values(["Sitename","datetime"]).reset_index(drop=True)
                    if len(mapped) == 0:
                        st.error("❌ No valid rows after mapping. Check column assignments or datetime format.")
                    else:
                        st.session_state.active_data = mapped
                        st.session_state.data_source = "user"
                        st.success(f"✅ Activated {len(mapped):,} rows. Switch to any analysis tab!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Mapping error: {e}")

    with right:
        # ── Validation ───────────────────────────────────────────────────────
        st.markdown("#### ✅ Validation Report")
        if "raw_df" not in st.session_state:
            st.info("Upload a file on the left, then validation results appear here.")
        else:
            raw = st.session_state.raw_df
            st.markdown(f'<div class="alert-ok">✅ File read: {len(raw):,} rows, {len(raw.columns)} columns</div>', unsafe_allow_html=True)

            if st.session_state.combined_col:
                st.markdown(f'<div class="alert-ok">✅ Separate Date+Time columns detected & combined</div>', unsafe_allow_html=True)

            # Datetime check
            if "col_dt" in dir():
                sampled = raw[col_dt].astype(str).head(200)
                parsed  = try_parse_datetime(sampled, dt_fmt_val)
                pct_ok  = parsed.notna().mean()
                cls     = "alert-ok" if pct_ok > 0.8 else "alert-warn"
                st.markdown(f'<div class="{cls}">{"✅" if pct_ok>0.8 else "⚠️"} Datetime parse: {pct_ok*100:.0f}% of 200 sample rows OK</div>', unsafe_allow_html=True)

            # Value check
            if "col_val" in dir():
                v = pd.to_numeric(raw[col_val], errors="coerce")
                pna = v.isna().mean()
                cls = "alert-ok" if pna < 0.2 else "alert-warn"
                st.markdown(f'<div class="{cls}">{"✅" if pna<0.2 else "⚠️"} Numeric values: {(1-pna)*100:.0f}% valid, {pna*100:.0f}% NA</div>', unsafe_allow_html=True)

            # Sites/params
            for col_name, pat in [("Sites", ["site","station"]), ("Parameters", ["param","pollutant"])]:
                mapped_col = guess_col(list(raw.columns), pat)
                n_unique = raw[mapped_col].nunique()
                st.markdown(f'<div class="alert-ok">✅ {col_name}: {n_unique} unique values found</div>', unsafe_allow_html=True)

        # ── File preview ─────────────────────────────────────────────────────
        st.markdown("#### 👀 File Preview (first 200 rows)")
        if "raw_df" in st.session_state:
            st.dataframe(st.session_state.raw_df.head(200), use_container_width=True, height=300)
        else:
            st.info("No file uploaded yet.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1  DATA OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### 📋 Data Overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📄 Records",    f"{len(filt):,}")
    c2.metric("🏭 Sites",      filt["Sitename"].nunique())
    c3.metric("📌 Parameter",  sel_param)
    c4.metric("❓ Missing",    int(filt["value"].isna().sum()))

    st.markdown("---")
    show_df = filt.copy()
    show_df["datetime"] = show_df["datetime"].dt.strftime("%Y-%m-%d %H:%M")
    show_df["value"]    = show_df["value"].round(3)
    st.dataframe(show_df[["Sitename","Parameter","datetime","value"]],
                 use_container_width=True, height=500)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2  TIME SERIES
# ─────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### 📈 Time Series")

    def make_ts_fig(y_col, avg_label, threshold, thresh_label):
        fig = go.Figure()
        for site, grp in enriched.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            fig.add_trace(go.Scatter(
                x=grp["datetime"], y=grp[y_col], mode="lines",
                name=site, line=dict(color=col, width=1.2)))
        # Global threshold line
        xmin, xmax = enriched["datetime"].min(), enriched["datetime"].max()
        fig.add_trace(go.Scatter(
            x=[xmin, xmax], y=[threshold, threshold],
            mode="lines", name=thresh_label,
            line=dict(color="#FF6B6B", dash="dash", width=2),
            showlegend=True))
        fig.add_hrect(y0=threshold, y1=enriched[y_col].max(skipna=True)*1.05,
                      fillcolor="#FF6B6B", opacity=0.05, line_width=0)
        return apply_dark(fig, f"{avg_label} – {sel_param}", "Date / Time", sel_param)

    if len(enriched):
        st.plotly_chart(make_ts_fig("value", "Hourly Average", thresh_1h, "1-hr Threshold"),
                        use_container_width=True)
        st.plotly_chart(make_ts_fig("roll24", "24-hr Rolling Average", thresh_24h, "24-hr Threshold"),
                        use_container_width=True)
    else:
        st.warning("No data for selected filters.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3  DESCRIPTIVE STATS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("### 📊 Descriptive Statistics")

    sc1, sc2 = st.columns([1.4, 1])
    agg_by = sc1.radio("Aggregate by", ["Hour of Day","Day of Week","Month","Season"],
                       horizontal=True)
    AGG_MAP = {
        "Hour of Day" : ("hod",  [str(h) for h in range(24)], "Hour of Day"),
        "Day of Week" : ("dow",  DOW_ORDER,                   "Day of Week"),
        "Month"       : ("mon",  MON_ORDER,                   "Month"),
        "Season"      : ("season",SEASONS,                    "Season"),
    }
    grp_col, order, x_label = AGG_MAP[agg_by]

    enriched[grp_col] = enriched[grp_col].astype(str)

    # Stats table
    agg_tbl = (enriched.groupby(["Sitename", grp_col])["value"]
               .agg(N="count", Mean="mean", SD="std",
                    Median="median", P25=lambda x: x.quantile(.25),
                    P75=lambda x: x.quantile(.75), Max="max")
               .round(3).reset_index())
    agg_tbl.columns = ["Site", agg_by, "N","Mean","SD","Median","P25","P75","Max"]

    with st.expander("📋 Aggregated Statistics Table", expanded=False):
        st.dataframe(agg_tbl, use_container_width=True)

    st.markdown("#### Overall Descriptive Stats per Site")
    overall_stats = describe_stats(enriched)
    st.dataframe(overall_stats, use_container_width=True)

    # ── Box plot ──────────────────────────────────────────────────────────────
    st.markdown(f"#### Box Plot – {sel_param} by {agg_by}")
    n_sites = len(sel_sites)
    spread  = 0.55 if n_sites > 1 else 0
    offsets = np.linspace(-spread/2, spread/2, max(n_sites,1))
    off_map = {s: offsets[i] for i, s in enumerate(sorted(sel_sites))}

    def make_box_violin(plot_type="box"):
        fig = go.Figure()
        for site, grp in enriched.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            grp2 = grp.copy()
            grp2["x_lev"] = pd.Categorical(grp2[grp_col], categories=order, ordered=True)
            grp2["x_num"] = grp2["x_lev"].cat.codes + 1 + off_map.get(site, 0)
            if plot_type == "box":
                fig.add_trace(go.Box(
                    x=grp2["x_num"], y=grp2["value"], name=site,
                    marker_color=col, line_color=col, fillcolor=hex_rgba(col, 0.18),
                    width=max(0.12, 0.55/max(n_sites,1)),
                    boxmean="sd",
                    customdata=grp2[grp_col],
                    hovertemplate=f"<b>{site}</b><br>{agg_by}: %{{customdata}}<br>Value: %{{y:.3f}}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Violin(
                    x=grp2["x_num"], y=grp2["value"], name=site,
                    line_color=col, fillcolor=hex_rgba(col, 0.27),
                    width=max(0.20, 0.65/max(n_sites,1)),
                    meanline_visible=True, meanline=dict(color=col, width=2),
                    points=False, opacity=0.80,
                    customdata=grp2[grp_col],
                    hovertemplate=f"<b>{site}</b><br>{agg_by}: %{{customdata}}<br>Value: %{{y:.3f}}<extra></extra>"
                ))
        fig.update_layout(
            **PLOTLY_DARK,
            title_text=f"{'Box' if plot_type=='box' else 'Violin'} Plot – {sel_param} by {agg_by}",
        )
        fig.update_xaxes(
            **DARK_AXIS,
            tickmode="array",
            tickvals=list(range(1, len(order)+1)),
            ticktext=order,
            range=[0.3, len(order)+0.7],
        )
        fig.update_yaxes(**DARK_AXIS, title_text=sel_param)
        return fig

    st.plotly_chart(make_box_violin("box"),    use_container_width=True)
    st.plotly_chart(make_box_violin("violin"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4  THRESHOLD ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("### 🎯 Threshold Analysis")

    def make_thresh_fig(y_col, avg_label, threshold, thresh_label):
        fig = go.Figure()
        ymax = enriched[y_col].max(skipna=True) * 1.05 if len(enriched) else threshold*2
        for site, grp in enriched.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            fig.add_trace(go.Scatter(
                x=grp["datetime"], y=grp[y_col], mode="lines",
                name=site, line=dict(color=col, width=1.2)))
        xmin = enriched["datetime"].min(); xmax = enriched["datetime"].max()
        fig.add_hrect(y0=threshold, y1=ymax,
                      fillcolor="#FF6B6B", opacity=0.06, line_width=0,
                      annotation_text="Exceedance Zone",
                      annotation_font=dict(color="#FF6B6B", size=11))
        fig.add_trace(go.Scatter(
            x=[xmin, xmax], y=[threshold, threshold],
            mode="lines", name=thresh_label,
            line=dict(color="#FF6B6B", dash="dash", width=2.5)))
        return apply_dark(fig, f"{avg_label} – {sel_param} vs Threshold", "Date/Time", sel_param)

    if len(enriched):
        st.plotly_chart(make_thresh_fig("value",  "1-hr Average",         thresh_1h,  "1-hr Threshold"),  use_container_width=True)
        st.plotly_chart(make_thresh_fig("roll24", "24-hr Rolling Average", thresh_24h, "24-hr Threshold"), use_container_width=True)
    else:
        st.warning("No data for selected filters.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5  EXCEEDANCE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### ⚠️ Exceedance Analysis")

    if len(enriched) == 0:
        st.warning("No data."); st.stop()

    # ── Summary table ──────────────────────────────────────────────────────
    exc_rows = []
    for site, grp in enriched.groupby("Sitename"):
        valid_1h  = grp["value"].notna().sum()
        valid_24h = grp["roll24"].notna().sum()
        exc_1h    = grp["exc_1h"].sum()
        exc_24h   = grp["exc_24h"].sum()
        exc_rows.append(dict(
            Site      = site,
            Thresh_1h = thresh_1h, Thresh_24h = thresh_24h,
            Valid_1h  = valid_1h,  Exceed_1h  = exc_1h,
            Pct_1h    = round(100*exc_1h/max(valid_1h,1), 2),
            Valid_24h = valid_24h, Exceed_24h = exc_24h,
            Pct_24h   = round(100*exc_24h/max(valid_24h,1), 2),
        ))
    exc_df = pd.DataFrame(exc_rows)

    ea, eb = st.columns(2)
    ea.markdown("**1-Hour Exceedance Counts**")
    ea.dataframe(exc_df[["Site","Thresh_1h","Valid_1h","Exceed_1h","Pct_1h"]], use_container_width=True)
    eb.markdown("**24-Hour Rolling Exceedance Counts**")
    eb.dataframe(exc_df[["Site","Thresh_24h","Valid_24h","Exceed_24h","Pct_24h"]], use_container_width=True)

    # ── % bar charts ───────────────────────────────────────────────────────
    def pct_bar(col, title):
        fig = px.bar(exc_df, x="Site", y=col, color="Site",
                     color_discrete_map={s: pal.get(s,"#00E5FF") for s in exc_df["Site"]},
                     text=exc_df[col].astype(str)+"%")
        fig.update_traces(textposition="outside")
        return apply_dark(fig, title, "Site", "% Exceedances")

    pc1, pc2 = st.columns(2)
    pc1.plotly_chart(pct_bar("Pct_1h",  "% Exceedances – 1-hr Avg"),  use_container_width=True)
    pc2.plotly_chart(pct_bar("Pct_24h", "% Exceedances – 24-hr Avg"), use_container_width=True)

    st.markdown("---")

    # ── Grouped bar helper ────────────────────────────────────────────────
    def exc_group_bar(grp_col, order, x_label, exc_col, title):
        rows = []
        for site, grp in enriched.groupby("Sitename"):
            for gv, sg in grp.groupby(grp_col):
                rows.append({"Site": site, "Group": str(gv),
                             "Count": int(sg[exc_col].sum())})
        df2 = pd.DataFrame(rows)
        if df2.empty: return go.Figure()
        df2["Group"] = pd.Categorical(df2["Group"], categories=[str(o) for o in order], ordered=True)
        df2 = df2.sort_values("Group")
        fig = px.bar(df2, x="Group", y="Count", color="Site", barmode="group",
                     color_discrete_map={s: pal.get(s,"#00E5FF") for s in df2["Site"]})
        return apply_dark(fig, title, x_label, "# Exceedances")

    # By Hour of Day
    h1,h2 = st.columns(2)
    h1.markdown("**Exceedances by Hour of Day – 1-hr**")
    h1.plotly_chart(exc_group_bar("hod", range(24), "Hour of Day", "exc_1h",
        f"# Exceedances by Hour – 1-hr | {sel_param}"), use_container_width=True)
    h2.markdown("**Exceedances by Hour of Day – 24-hr**")
    h2.plotly_chart(exc_group_bar("hod", range(24), "Hour of Day", "exc_24h",
        f"# Exceedances by Hour – 24-hr | {sel_param}"), use_container_width=True)

    # By Day of Week
    d1c,d2c = st.columns(2)
    d1c.markdown("**Exceedances by Day of Week – 1-hr**")
    d1c.plotly_chart(exc_group_bar("dow", DOW_ORDER, "Day of Week", "exc_1h",
        f"# Exceedances by DoW – 1-hr | {sel_param}"), use_container_width=True)
    d2c.markdown("**Exceedances by Day of Week – 24-hr**")
    d2c.plotly_chart(exc_group_bar("dow", DOW_ORDER, "Day of Week", "exc_24h",
        f"# Exceedances by DoW – 24-hr | {sel_param}"), use_container_width=True)

    # By Month
    m1,m2 = st.columns(2)
    m1.markdown("**Exceedances by Month – 1-hr**")
    m1.plotly_chart(exc_group_bar("mon", MON_ORDER, "Month", "exc_1h",
        f"# Exceedances by Month – 1-hr | {sel_param}"), use_container_width=True)
    m2.markdown("**Exceedances by Month – 24-hr**")
    m2.plotly_chart(exc_group_bar("mon", MON_ORDER, "Month", "exc_24h",
        f"# Exceedances by Month – 24-hr | {sel_param}"), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6  TEMPORAL PATTERNS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("### ⏰ Temporal Patterns")

    def temporal_mean_ribbon(grp_col, order, x_label, title):
        fig = go.Figure()
        for site, grp in enriched.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            agg = grp.groupby(grp_col)["value"].agg(
                Mean="mean", SD="std", P25=lambda x: x.quantile(.25),
                P75=lambda x: x.quantile(.75)).reset_index()
            agg[grp_col] = pd.Categorical(agg[grp_col].astype(str),
                                          categories=[str(o) for o in order], ordered=True)
            agg = agg.sort_values(grp_col)
            # IQR ribbon
            fig.add_trace(go.Scatter(
                x=list(agg[grp_col]) + list(reversed(list(agg[grp_col]))),
                y=list(agg["P75"]) + list(reversed(list(agg["P25"]))),
                fill="toself", fillcolor=hex_rgba(col, 0.13), line=dict(width=0),
                showlegend=False, hoverinfo="skip"))
            # Mean ± SD
            fig.add_trace(go.Scatter(
                x=agg[grp_col], y=agg["Mean"],
                mode="lines+markers", name=site,
                line=dict(color=col, width=2),
                marker=dict(color=col, size=6),
                error_y=dict(array=agg["SD"], visible=True, color=hex_rgba(col, 0.53))))
        fig.update_xaxes(categoryorder="array", categoryarray=[str(o) for o in order])
        return apply_dark(fig, title, x_label, sel_param)

    # Diurnal
    st.markdown("#### 🕛 Diurnal Pattern")
    st.plotly_chart(temporal_mean_ribbon("hod", range(24), "Hour of Day",
        f"Diurnal Pattern – {sel_param} (Mean ± SD, IQR band)"), use_container_width=True)

    # Monthly
    st.markdown("#### 📅 Monthly Pattern")
    st.plotly_chart(temporal_mean_ribbon("mon", MON_ORDER, "Month",
        f"Monthly Pattern – {sel_param} (Mean ± SD, IQR band)"), use_container_width=True)

    # ── Seasonal 4-panel (2×2) ────────────────────────────────────────────
    st.markdown("#### 🍂 Seasonal Diurnal Patterns (2×2 Panel)")
    enriched["season"] = get_season(enriched["datetime"])

    fig_seas = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"<b>{s}</b>" for s in SEASONS],
        shared_yaxes=True, vertical_spacing=0.14, horizontal_spacing=0.08,
    )
    pos = [(1,1),(1,2),(2,1),(2,2)]
    for idx, season in enumerate(SEASONS):
        r, c = pos[idx]
        seas_df = enriched[enriched["season"]==season]
        for site, grp in seas_df.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            agg = grp.groupby("hod")["value"].agg(Mean="mean", SD="std").reset_index()
            agg = agg.sort_values("hod")
            show_legend = (idx == 0)
            fig_seas.add_trace(go.Scatter(
                x=agg["hod"], y=agg["Mean"], mode="lines+markers",
                name=site, legendgroup=site, showlegend=show_legend,
                line=dict(color=col, width=2),
                marker=dict(color=col, size=5),
                error_y=dict(array=agg["SD"], visible=True, color=hex_rgba(col, 0.40))),
                row=r, col=c)

    fig_seas.update_layout(
        **PLOTLY_DARK,
        title_text=f"Seasonal Diurnal Patterns – {sel_param}",
        height=600,
        legend=dict(orientation="h", y=-0.12, bgcolor="rgba(13,31,60,0.85)",
                    font=dict(color="#CFD8DC")),
    )
    for i in range(1,5):
        fig_seas.update_xaxes(
            **DARK_AXIS, title_text="Hour of Day",
            row=(i-1)//2+1, col=(i-1)%2+1)
        fig_seas.update_yaxes(
            **DARK_AXIS,
            title_text=sel_param if (i-1)%2==0 else "",
            row=(i-1)//2+1, col=(i-1)%2+1)
    for ann in fig_seas.layout.annotations:
        ann.font = dict(color="#E0F7FA", family="Rajdhani,sans-serif", size=14)

    st.plotly_chart(fig_seas, use_container_width=True)

    # ── Seasonal monthly 2×2 ──────────────────────────────────────────────
    st.markdown("#### 📆 Seasonal Monthly Patterns (2×2 Panel)")
    fig_smon = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"<b>{s}</b>" for s in SEASONS],
        shared_yaxes=True, vertical_spacing=0.14, horizontal_spacing=0.08,
    )
    for idx, season in enumerate(SEASONS):
        r, c = pos[idx]
        seas_df = enriched[enriched["season"]==season]
        for site, grp in seas_df.groupby("Sitename"):
            col = pal.get(site, "#00E5FF")
            agg = grp.groupby("mon")["value"].agg(Mean="mean", SD="std").reset_index()
            agg["mon"] = pd.Categorical(agg["mon"], categories=MON_ORDER, ordered=True)
            agg = agg.sort_values("mon")
            show_legend = (idx == 0)
            fig_smon.add_trace(go.Scatter(
                x=agg["mon"], y=agg["Mean"], mode="lines+markers",
                name=site, legendgroup=site, showlegend=show_legend,
                line=dict(color=col, width=2),
                marker=dict(color=col, size=5)),
                row=r, col=c)

    fig_smon.update_layout(
        **PLOTLY_DARK,
        title_text=f"Seasonal Monthly Patterns – {sel_param}",
        height=600,
        legend=dict(orientation="h", y=-0.12, bgcolor="rgba(13,31,60,0.85)",
                    font=dict(color="#CFD8DC")),
    )
    for i in range(1,5):
        fig_smon.update_xaxes(**DARK_AXIS, row=(i-1)//2+1, col=(i-1)%2+1)
        fig_smon.update_yaxes(
            **DARK_AXIS,
            title_text=sel_param if (i-1)%2==0 else "",
            row=(i-1)//2+1, col=(i-1)%2+1)
    for ann in fig_smon.layout.annotations:
        ann.font = dict(color="#E0F7FA", family="Rajdhani,sans-serif", size=14)
    st.plotly_chart(fig_smon, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 7  WIND ROSE
# ─────────────────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("### 🌬️ Wind Rose")

    ad = st.session_state.active_data
    all_params = sorted(ad["Parameter"].unique())
    all_sites  = sorted(ad["Sitename"].unique())

    wc1, wc2, wc3 = st.columns(3)
    wr_site    = wc1.selectbox("Site", all_sites, key="wr_site")
    wr_ws_par  = wc2.selectbox("Wind Speed param",
        all_params, index=next((i for i,p in enumerate(all_params)
            if re.search("wind.?speed|wspeed|^ws$",p,re.I)), 0), key="wr_ws_p")
    wr_wd_par  = wc3.selectbox("Wind Direction param",
        all_params, index=next((i for i,p in enumerate(all_params)
            if re.search("wind.?dir|wdir|^wd$|direction",p,re.I)),
            min(1,len(all_params)-1)), key="wr_wd_p")

    gen_wr = st.button("🌬️ Generate Wind Roses", use_container_width=False)

    def build_wind_df(site, d1, d2):
        ad_site = ad[ad["Sitename"]==site]
        ws = ad_site[ad_site["Parameter"]==wr_ws_par][["datetime","value"]].rename(columns={"value":"ws"})
        wd = ad_site[ad_site["Parameter"]==wr_wd_par][["datetime","value"]].rename(columns={"value":"wd"})
        po = ad_site[ad_site["Parameter"]==sel_param][["datetime","value"]].rename(columns={"value":"pollutant"})
        df = ws.merge(wd, on="datetime").merge(po, on="datetime")
        df = df[(df["datetime"]>=d1)&(df["datetime"]<=d2)].dropna()
        df["season"] = get_season(df["datetime"])
        return df

    def plotly_windrose(df_wind, title="Wind Rose", n_spd_bins=6, n_dir_bins=16):
        """Build a Plotly polar bar wind rose from ws/wd columns."""
        if len(df_wind) < 10:
            return go.Figure().update_layout(title_text="Not enough data", **PLOTLY_DARK)

        dir_bins   = np.linspace(0, 360, n_dir_bins+1)
        dir_labels = [f"{v:.0f}°" for v in (dir_bins[:-1]+dir_bins[1:])/2]
        spd_max    = df_wind["ws"].quantile(0.99)
        spd_bins   = np.linspace(0, spd_max, n_spd_bins+1)
        spd_labels = [f"{spd_bins[i]:.1f}–{spd_bins[i+1]:.1f} m/s"
                      for i in range(n_spd_bins)]

        df_wind    = df_wind.copy()
        df_wind["dir_bin"] = pd.cut(df_wind["wd"], bins=dir_bins,
                                    labels=dir_labels, include_lowest=True)
        df_wind["spd_bin"] = pd.cut(df_wind["ws"], bins=spd_bins,
                                    labels=spd_labels, include_lowest=True)

        total   = len(df_wind)
        colors  = px.colors.sequential.YlOrRd[1:]  # warm gradient
        fig     = go.Figure()
        for i, sl in enumerate(spd_labels):
            sub    = df_wind[df_wind["spd_bin"]==sl]
            counts = sub.groupby("dir_bin", observed=True).size().reindex(dir_labels, fill_value=0)
            pct    = (counts / total * 100).values
            fig.add_trace(go.Barpolar(
                r=pct, theta=dir_labels, name=sl,
                marker_color=colors[i % len(colors)],
                marker_line_color="#0a1628", marker_line_width=0.5,
                opacity=0.88))

        fig.update_layout(
            **PLOTLY_DARK,
            title_text=title,
            polar=dict(
                bgcolor="#0d1f3c",
                angularaxis=dict(direction="clockwise", tickfont=dict(color="#90CAF9",size=10),
                                 linecolor="#1a3a5c", gridcolor="#1a3a5c"),
                radialaxis=dict(ticksuffix="%", tickfont=dict(color="#90CAF9",size=9),
                               gridcolor="#1a3a5c", linecolor="#1a3a5c")),
            showlegend=True,
            legend=dict(font=dict(color="#CFD8DC",size=10), bgcolor="rgba(13,31,60,0.8)",
                        title=dict(text="Wind Speed", font=dict(color="#00E5FF"))),
            height=520,
        )
        return fig

    if gen_wr:
        wind_df = build_wind_df(wr_site, d1, d2)
        if len(wind_df) < 10:
            st.error("Not enough wind data for selected filters. Try a wider date range.")
        else:
            # Overall rose
            st.markdown(f"#### Overall Wind Rose – {wr_site}")
            st.plotly_chart(plotly_windrose(wind_df,
                f"Wind Rose – {wr_site} | All Data | n={len(wind_df):,}"),
                use_container_width=True)

            # ── 4-Season 2×2 panel ────────────────────────────────────────
            st.markdown(f"#### Seasonal Wind Roses – {wr_site} (2×2 Panel)")
            fig4 = make_subplots(
                rows=2, cols=2, specs=[[{"type":"polar"}]*2]*2,
                subplot_titles=[f"<b>{s}</b>" for s in SEASONS],
                vertical_spacing=0.12, horizontal_spacing=0.06
            )
            for idx, season in enumerate(SEASONS):
                r, c    = pos[idx]
                sdf     = wind_df[wind_df["season"]==season]
                if len(sdf) < 10:
                    continue
                dir_bins   = np.linspace(0, 360, 17)
                dir_labels = [f"{v:.0f}°" for v in (dir_bins[:-1]+dir_bins[1:])/2]
                spd_max    = sdf["ws"].quantile(0.99)
                n_spd      = 5
                spd_bins   = np.linspace(0, spd_max, n_spd+1)
                spd_labels = [f"{spd_bins[i]:.1f}–{spd_bins[i+1]:.1f}" for i in range(n_spd)]
                sdf = sdf.copy()
                sdf["dir_bin"] = pd.cut(sdf["wd"], bins=dir_bins, labels=dir_labels, include_lowest=True)
                sdf["spd_bin"] = pd.cut(sdf["ws"], bins=spd_bins, labels=spd_labels, include_lowest=True)
                total = len(sdf)
                colors = ["#FFEE58","#FFA726","#EF5350","#B71C1C","#4A148C"]
                for si, sl in enumerate(spd_labels):
                    sub    = sdf[sdf["spd_bin"]==sl]
                    counts = sub.groupby("dir_bin",observed=True).size().reindex(dir_labels,fill_value=0)
                    pct    = (counts/total*100).values
                    show_leg = (idx==0)
                    fig4.add_trace(go.Barpolar(
                        r=pct, theta=dir_labels, name=sl, legendgroup=sl,
                        showlegend=show_leg,
                        marker_color=colors[si % len(colors)],
                        marker_line_color="#0a1628", marker_line_width=0.5,
                        opacity=0.88), row=r, col=c)

            fig4.update_layout(
                **PLOTLY_DARK,
                title_text=f"Seasonal Wind Roses – {wr_site}",
                height=820,
                legend=dict(font=dict(color="#CFD8DC",size=10),
                            bgcolor="rgba(13,31,60,0.8)",
                            title=dict(text="Wind Speed",font=dict(color="#00E5FF"))),
            )
            for i in range(1,5):
                r2,c2 = pos[i-1]
                polar_key = f"polar{'' if i==1 else i}"
                fig4.update_layout(**{
                    polar_key: dict(
                        bgcolor="#0d1f3c",
                        angularaxis=dict(direction="clockwise",
                                         tickfont=dict(color="#90CAF9",size=9),
                                         gridcolor="#1a3a5c"),
                        radialaxis=dict(ticksuffix="%",
                                        tickfont=dict(color="#90CAF9",size=8),
                                        gridcolor="#1a3a5c"))
                })
            for ann in fig4.layout.annotations:
                ann.font = dict(color="#E0F7FA", family="Rajdhani,sans-serif", size=14)
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Configure wind parameters above and click **Generate Wind Roses**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 8  POLAR PLOTS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("### 🌀 Polar Plots (Concentration × Wind Direction × Speed)")

    pc1, pc2, pc3, pc4 = st.columns(4)
    pp_site   = pc1.selectbox("Site", all_sites, key="pp_site_sel")
    pp_stat   = pc2.selectbox("Statistic", ["mean","median","max","p95"], key="pp_stat")
    pp_ws_p   = pc3.selectbox("Wind Speed param", all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search("wind.?speed|wspeed|^ws$",p,re.I)), 0), key="pp_ws_p")
    pp_wd_p   = pc4.selectbox("Wind Direction param", all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search("wind.?dir|wdir|^wd$|direction",p,re.I)),
            min(1,len(all_params)-1)), key="pp_wd_p")

    gen_pp = st.button("🌀 Generate Polar Plots", use_container_width=False)

    STAT_FN = {
        "mean"  : "mean",
        "median": "median",
        "max"   : "max",
        "p95"   : lambda x: x.quantile(0.95),
    }

    def build_polar_df(site_sel, d1, d2):
        if site_sel == "All Sites":
            ad_site = ad
        else:
            ad_site = ad[ad["Sitename"]==site_sel]
        ws = ad_site[ad_site["Parameter"]==pp_ws_p][["datetime","value"]].rename(columns={"value":"ws"})
        wd = ad_site[ad_site["Parameter"]==pp_wd_p][["datetime","value"]].rename(columns={"value":"wd"})
        po = ad_site[ad_site["Parameter"]==sel_param][["datetime","value"]].rename(columns={"value":"pollutant"})
        df = ws.merge(wd, on="datetime").merge(po, on="datetime")
        df = df[(df["datetime"]>=d1)&(df["datetime"]<=d2)].dropna()
        df["season"] = get_season(df["datetime"])
        return df

    def plotly_polar_plot(df, title, stat_fn_key="mean", n_dir=24, n_spd=8):
        """
        Polar concentration plot: mean/median/max pollutant as function of
        wind direction (theta) and wind speed (radius), shown as heat-binned scatter.
        """
        if len(df) < 30:
            return go.Figure().update_layout(title_text="Not enough data", **PLOTLY_DARK)
        stat_fn  = STAT_FN[stat_fn_key]
        dir_bins = np.linspace(0, 360, n_dir+1)
        spd_bins = np.linspace(0, df["ws"].quantile(0.99)+0.01, n_spd+1)

        df2 = df.copy()
        df2["dir_bin"] = pd.cut(df2["wd"], bins=dir_bins, include_lowest=True)
        df2["spd_bin"] = pd.cut(df2["ws"], bins=spd_bins, include_lowest=True)
        agg = df2.groupby(["dir_bin","spd_bin"], observed=True)["pollutant"].agg(stat_fn).reset_index()
        agg.columns = ["dir_bin","spd_bin","stat"]
        agg["dir_mid"] = agg["dir_bin"].apply(lambda b: (b.left+b.right)/2)
        agg["spd_mid"] = agg["spd_bin"].apply(lambda b: (b.left+b.right)/2)
        agg = agg.dropna()

        fig = go.Figure(go.Scatterpolar(
            r     = agg["spd_mid"],
            theta = agg["dir_mid"],
            mode  = "markers",
            marker= dict(
                color     = agg["stat"],
                colorscale= "Jet",
                size      = 10,
                opacity   = 0.85,
                colorbar  = dict(
                    title=dict(text=f"{sel_param}<br>({stat_fn_key})",
                               font=dict(color="#90CAF9",size=11)),
                    tickfont=dict(color="#90CAF9"),
                    bgcolor="#0a1628",
                    bordercolor="#1a3a5c"),
                line=dict(width=0)
            ),
            hovertemplate="Dir: %{theta:.0f}°<br>WS: %{r:.2f} m/s<br>"
                          f"{sel_param}: %{{marker.color:.3f}}<extra></extra>"
        ))
        fig.update_layout(
            **PLOTLY_DARK,
            title_text=title,
            polar=dict(
                bgcolor="#0d1f3c",
                angularaxis=dict(direction="clockwise", rotation=90,
                                 tickfont=dict(color="#90CAF9",size=10),
                                 gridcolor="#1a3a5c"),
                radialaxis=dict(title=dict(text="Wind Speed (m/s)",
                                           font=dict(color="#90CAF9",size=10)),
                               tickfont=dict(color="#90CAF9",size=9),
                               gridcolor="#1a3a5c")),
            height=540,
        )
        return fig

    if gen_pp:
        pp_df = build_polar_df(pp_site, d1, d2)
        if len(pp_df) < 30:
            st.error("Not enough data. Try a wider date range or different site.")
        else:
            # Overall polar
            st.markdown(f"#### Overall Polar Plot – {sel_param} | {pp_site}")
            st.plotly_chart(plotly_polar_plot(pp_df,
                f"Polar Plot – {sel_param} ({pp_stat}) | {pp_site} | All Seasons",
                pp_stat), use_container_width=True)

            # ── 4-Season 2×2 ─────────────────────────────────────────────
            st.markdown(f"#### Seasonal Polar Plots – {sel_param} | {pp_site} (2×2 Panel)")
            fig_pp4 = make_subplots(
                rows=2, cols=2, specs=[[{"type":"polar"}]*2]*2,
                subplot_titles=[f"<b>{s}</b>" for s in SEASONS],
                vertical_spacing=0.14, horizontal_spacing=0.06
            )
            color_scale = px.colors.sequential.Jet
            for idx, season in enumerate(SEASONS):
                r2, c2 = pos[idx]
                sdf    = pp_df[pp_df["season"]==season]
                if len(sdf) < 20:
                    continue
                stat_fn  = STAT_FN[pp_stat]
                dir_bins = np.linspace(0, 360, 25)
                spd_bins = np.linspace(0, sdf["ws"].quantile(0.99)+0.01, 9)
                sdf = sdf.copy()
                sdf["dir_bin"] = pd.cut(sdf["wd"], bins=dir_bins, include_lowest=True)
                sdf["spd_bin"] = pd.cut(sdf["ws"], bins=spd_bins, include_lowest=True)
                agg = sdf.groupby(["dir_bin","spd_bin"],observed=True)["pollutant"].agg(stat_fn).reset_index()
                agg.columns = ["dir_bin","spd_bin","stat"]
                agg["dir_mid"] = agg["dir_bin"].apply(lambda b: (b.left+b.right)/2)
                agg["spd_mid"] = agg["spd_bin"].apply(lambda b: (b.left+b.right)/2)
                agg = agg.dropna()
                show_cb = (idx == 0)
                polar_key = f"polar{'' if idx==0 else idx+1}"
                fig_pp4.add_trace(go.Scatterpolar(
                    r=agg["spd_mid"], theta=agg["dir_mid"],
                    mode="markers",
                    name=season, showlegend=False,
                    marker=dict(
                        color=agg["stat"], colorscale="Jet",
                        size=9, opacity=0.85,
                        showscale=show_cb,
                        colorbar=dict(
                            x=1.02, thickness=12,
                            title=dict(text=f"{sel_param}",
                                       font=dict(color="#90CAF9",size=10)),
                            tickfont=dict(color="#90CAF9",size=8),
                            bgcolor="#0a1628", bordercolor="#1a3a5c")
                        if show_cb else dict(showscale=False)),
                    subplot=polar_key),
                    row=r2, col=c2)

            fig_pp4.update_layout(
                **PLOTLY_DARK,
                title_text=f"Seasonal Polar Plots – {sel_param} ({pp_stat}) | {pp_site}",
                height=860,
            )
            for i in range(1,5):
                polar_key = f"polar{'' if i==1 else i}"
                fig_pp4.update_layout(**{
                    polar_key: dict(
                        bgcolor="#0d1f3c",
                        angularaxis=dict(direction="clockwise", rotation=90,
                                         tickfont=dict(color="#90CAF9",size=8),
                                         gridcolor="#1a3a5c"),
                        radialaxis=dict(tickfont=dict(color="#90CAF9",size=7),
                                        gridcolor="#1a3a5c"))
                })
            for ann in fig_pp4.layout.annotations:
                ann.font = dict(color="#E0F7FA", family="Rajdhani,sans-serif", size=14)
            st.plotly_chart(fig_pp4, use_container_width=True)
    else:
        st.info("Configure parameters above and click **Generate Polar Plots**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 9  EXPORT
# ─────────────────────────────────────────────────────────────────────────────
with tabs[9]:
    st.markdown("### ⬇️ Export Data")

    st.markdown("""
    <div style='background:#0d1f3c;border:1px solid #1a3a5c;border-radius:10px;padding:16px 20px;'>
    <h3 style='color:#00E5FF;margin:0 0 12px 0;'>📄 Excel Report Contents</h3>
    <ul style='color:#90CAF9;line-height:2.1;font-size:13px;margin:0;'>
      <li><b style="color:#E0F7FA">Raw_Data</b> — filtered hourly values</li>
      <li><b style="color:#E0F7FA">Rolling_24h</b> — 24-hr rolling averages</li>
      <li><b style="color:#E0F7FA">Exceedances_1h</b> — 1-hr value > threshold</li>
      <li><b style="color:#E0F7FA">Exceedances_24h</b> — 24-hr avg > threshold</li>
      <li><b style="color:#E0F7FA">Stats_Overall</b> — per-site summary statistics</li>
      <li><b style="color:#E0F7FA">Stats_Hourly</b> — statistics by hour of day</li>
      <li><b style="color:#E0F7FA">Stats_Daily</b> — statistics by day of week</li>
      <li><b style="color:#E0F7FA">Stats_Monthly</b> — statistics by month</li>
      <li><b style="color:#E0F7FA">Stats_Seasonal</b> — statistics by season</li>
      <li><b style="color:#E0F7FA">Exc_Summary</b> — exceedance counts table</li>
      <li><b style="color:#E0F7FA">Thresholds</b> — applied thresholds & metadata</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    @st.cache_data(show_spinner="Building Excel report…")
    def build_excel(data_json, param, sites_tuple, d1_str, d2_str, t1, t24):
        df     = pd.read_json(io.StringIO(data_json), orient="records")
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        fdf    = df[(df["Parameter"]==param) &
                    (df["Sitename"].isin(sites_tuple)) &
                    (df["datetime"]>=pd.Timestamp(d1_str)) &
                    (df["datetime"]<=pd.Timestamp(d2_str))]
        fdf    = fdf.sort_values(["Sitename","datetime"]).reset_index(drop=True)

        frames = []
        for site, grp in fdf.groupby("Sitename"):
            g = grp.copy().sort_values("datetime")
            g["roll24"]  = roll24(g["value"])
            g["exc_1h"]  = g["value"].notna() & (g["value"] > t1)
            g["exc_24h"] = g["roll24"].notna() & (g["roll24"] > t24)
            g["hod"]     = g["datetime"].dt.hour
            g["dow"]     = g["datetime"].dt.day_name().str[:3]
            g["mon"]     = g["datetime"].dt.strftime("%b")
            g["season"]  = get_season(g["datetime"])
            frames.append(g)
        enr = pd.concat(frames, ignore_index=True) if frames else fdf

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:

            def ws(name, df_):
                df_.to_excel(xw, sheet_name=name, index=False)

            raw_out = fdf.copy()
            raw_out["datetime"] = raw_out["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            ws("Raw_Data", raw_out)

            r24 = enr[["Sitename","datetime","value","roll24"]].copy()
            r24.columns = ["Sitename","datetime","Value_1h","RollingAvg_24h"]
            r24["datetime"] = r24["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            r24[["Value_1h","RollingAvg_24h"]] = r24[["Value_1h","RollingAvg_24h"]].round(3)
            ws("Rolling_24h", r24)

            exc1 = enr[enr["exc_1h"]][["Sitename","datetime","value"]].copy()
            exc1.columns = ["Sitename","datetime","Value_1h"]
            exc1["datetime"] = exc1["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            exc1["Threshold_1h"] = t1
            exc1["Exceed_Amt"]   = (exc1["Value_1h"] - t1).round(3)
            ws("Exceedances_1h", exc1)

            exc24 = enr[enr["exc_24h"]][["Sitename","datetime","roll24"]].copy()
            exc24.columns = ["Sitename","datetime","RollingAvg_24h"]
            exc24["datetime"] = exc24["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            exc24["Threshold_24h"] = t24
            exc24["Exceed_Amt"]    = (exc24["RollingAvg_24h"] - t24).round(3)
            ws("Exceedances_24h", exc24)

            ws("Stats_Overall", describe_stats(enr))

            for col, key, col_name in [
                ("hod","Stats_Hourly","HourOfDay"),
                ("dow","Stats_Daily","DayOfWeek"),
                ("mon","Stats_Monthly","Month"),
                ("season","Stats_Seasonal","Season"),
            ]:
                agg = (enr.groupby(["Sitename",col])["value"]
                       .agg(N="count", Mean="mean", SD="std",
                            Median="median",
                            P25=lambda x: x.quantile(.25),
                            P75=lambda x: x.quantile(.75),
                            Min="min", Max="max")
                       .round(3).reset_index()
                       .rename(columns={col: col_name}))
                ws(key, agg)

            exc_rows = []
            for site, grp in enr.groupby("Sitename"):
                v1  = grp["value"].notna().sum()
                v24 = grp["roll24"].notna().sum()
                e1  = grp["exc_1h"].sum()
                e24 = grp["exc_24h"].sum()
                exc_rows.append(dict(
                    Site=site, Threshold_1h=t1, Threshold_24h=t24,
                    Valid_1h=v1, Exceed_1h=e1, Pct_1h=round(100*e1/max(v1,1),2),
                    Valid_24h=v24, Exceed_24h=e24, Pct_24h=round(100*e24/max(v24,1),2)))
            ws("Exc_Summary", pd.DataFrame(exc_rows))

            ws("Thresholds", pd.DataFrame([{
                "Averaging_Period":"1-hr average",  "Threshold":t1,
                "Parameter":param, "Sites":"; ".join(sites_tuple),
                "Date_From":d1_str, "Date_To":d2_str,
            },{
                "Averaging_Period":"24-hr rolling", "Threshold":t24,
                "Parameter":param, "Sites":"; ".join(sites_tuple),
                "Date_From":d1_str, "Date_To":d2_str,
            }]))

        return buf.getvalue()

    ecol1, ecol2 = st.columns(2)
    with ecol1:
        if st.button("🔨 Build Excel Report", use_container_width=True):
            xlsx_bytes = build_excel(
                data_json, sel_param, tuple(sorted(sel_sites)),
                str(d1), str(d2), thresh_1h, thresh_24h)
            st.session_state.xlsx_bytes = xlsx_bytes
            st.success("✅ Excel report ready – click Download below.")

        if "xlsx_bytes" in st.session_state:
            st.download_button(
                label="⬇️ Download Full XLSX Report",
                data=st.session_state.xlsx_bytes,
                file_name=f"EnviroMonitor_{sel_param}_{pd.Timestamp.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    with ecol2:
        csv_bytes = filt.copy()
        csv_bytes["datetime"] = csv_bytes["datetime"].dt.strftime("%Y-%m-%d %H:%M")
        st.download_button(
            label="⬇️ Download Raw Data (CSV)",
            data=csv_bytes.to_csv(index=False).encode(),
            file_name=f"raw_{sel_param}_{pd.Timestamp.now().date()}.csv",
            mime="text/csv",
            use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:18px 0 8px 0;color:#37474F;font-size:12px;'>
  EnviroMonitor Pro · Streamlit Edition ·
  <span style='color:#00E5FF66;'>Environmental Time Series Analysis</span>
</div>""", unsafe_allow_html=True)

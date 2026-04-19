# ==============================================================================
#  EnviroMonitor Pro – Streamlit Edition  (Matplotlib build)
#  All charts: matplotlib → clean transparent PNG/PDF downloads
#  Wind rose / Polar: matplotlib polar axes (openair-style kernel surface)
#
#  INSTALL:
#    pip install streamlit pandas numpy matplotlib scipy openpyxl xlrd
#
#  RUN:  streamlit run app.py
# ==============================================================================

import warnings, io, re, calendar
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from scipy.ndimage import gaussian_filter
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EnviroMonitor Pro",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
#  CSS
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700
             &family=Rajdhani:wght@500;700&display=swap');
html,body,[class*="css"]{font-family:'Exo 2',sans-serif!important;
  background:#050d1a!important;color:#CFD8DC!important;}
.main .block-container{padding:1.2rem 2rem;max-width:100%;}
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#071525,#0a1f35)!important;
  border-right:1px solid #00E5FF22;}
section[data-testid="stSidebar"] *{color:#90CAF9!important;}
h1,h2,h3{font-family:'Rajdhani',sans-serif!important;color:#E0F7FA!important;}
h1{font-size:26px!important;font-weight:700!important;}
h2{font-size:18px!important;color:#00E5FF!important;}
div[data-testid="metric-container"]{
  background:linear-gradient(135deg,#0d1f3c,#0a1628)!important;
  border:1px solid #1a3a5c;border-radius:12px;padding:14px 18px;}
div[data-testid="metric-container"]>label{color:#78909C!important;font-size:12px;}
div[data-testid="metric-container"]>div{color:#00E5FF!important;
  font-family:'Rajdhani',sans-serif!important;font-size:26px;font-weight:700;}
button[data-baseweb="tab"]{background:#0d1f3c!important;color:#78909C!important;
  border-radius:8px 8px 0 0!important;border:1px solid #1a3a5c!important;margin-right:3px;}
button[data-baseweb="tab"][aria-selected="true"]{
  background:linear-gradient(135deg,#006064,#00838F)!important;color:#E0F7FA!important;}
.stButton>button{background:linear-gradient(135deg,#006064,#00ACC1)!important;
  color:#E0F7FA!important;border:none!important;border-radius:8px!important;
  font-family:'Exo 2',sans-serif!important;font-weight:600!important;}
.stDownloadButton>button{background:linear-gradient(135deg,#1B5E20,#388E3C)!important;
  color:#E8F5E9!important;border:none!important;border-radius:8px!important;}
details{background:#0d1f3c!important;border:1px solid #1a3a5c!important;border-radius:10px!important;}
summary{color:#00E5FF!important;font-family:'Rajdhani',sans-serif!important;font-weight:600!important;}
div[data-testid="stFileUploadDropzone"]{background:#0d1f3c!important;
  border:2px dashed #00E5FF44!important;border-radius:12px!important;}
hr{border-color:#1a3a5c!important;}
</style>""", unsafe_allow_html=True)

# ==============================================================================
#  MATPLOTLIB STYLE  – transparent backgrounds, dark text
# ==============================================================================
DARK = "#050d1a"
GRID = "#1a3a5c"
TEXT = "#CFD8DC"
ACC  = "#00E5FF"

plt.rcParams.update({
    "figure.facecolor"    : "none",
    "axes.facecolor"      : "none",
    "axes.edgecolor"      : GRID,
    "axes.labelcolor"     : TEXT,
    "axes.titlecolor"     : "#E0F7FA",
    "axes.grid"           : True,
    "grid.color"          : GRID,
    "grid.linewidth"      : 0.6,
    "grid.alpha"          : 0.5,
    "xtick.color"         : TEXT,
    "ytick.color"         : TEXT,
    "text.color"          : TEXT,
    "legend.facecolor"    : "#0a1628cc",
    "legend.edgecolor"    : GRID,
    "legend.labelcolor"   : TEXT,
    "font.family"         : "DejaVu Sans",
    "font.size"           : 9,
    "axes.titlesize"      : 11,
    "axes.labelsize"      : 9,
    "figure.dpi"          : 110,
    "savefig.transparent" : True,
    "savefig.dpi"         : 200,
    "savefig.bbox"        : "tight",
    "savefig.pad_inches"  : 0.15,
})

PALETTE = ["#00E5FF","#FF6B6B","#69FF47","#FFD93D","#C77DFF",
           "#FF9A3C","#00B4D8","#F72585","#4CC9F0","#FFBE0B"]

def site_pal(sites):
    return {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(sorted(sites))}

# ==============================================================================
#  DOWNLOAD HELPERS
# ==============================================================================
def fig_to_png(fig, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi,
                transparent=True, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def fig_to_pdf(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def dl_row(fig, stem, dpi=200):
    """Show figure then PNG + PDF download buttons side-by-side."""
    png_b = fig_to_png(fig, dpi)
    pdf_b = fig_to_pdf(fig)
    # show the figure (closed already by fig_to_png so re-open from bytes)
    st.image(png_b, width="content")
    c1, c2, _ = st.columns([1, 1, 6])
    c1.download_button("⬇️ PNG", data=png_b,
        file_name=f"{stem}.png", mime="image/png",
        use_container_width=False, key=f"png_{stem}")
    c2.download_button("⬇️ PDF", data=pdf_b,
        file_name=f"{stem}.pdf", mime="application/pdf",
        use_container_width=False, key=f"pdf_{stem}")

# ==============================================================================
#  CONSTANTS / HELPERS
# ==============================================================================
SEASONS   = ["Spring","Summer","Autumn","Winter"]
DOW_ORDER = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
MON_ORDER = list(calendar.month_abbr)[1:]

def get_season(s: pd.Series) -> pd.Series:
    m = s.dt.month
    return np.select(
        [m.isin([3,4,5]), m.isin([6,7,8]), m.isin([9,10,11])],
        ["Spring","Summer","Autumn"], default="Winter")

def roll24(s: pd.Series) -> pd.Series:
    return s.rolling(24, min_periods=1).mean()

def describe_stats(df):
    g = df.groupby("Sitename")["value"]
    return pd.DataFrame({
        "N"     : g.count(),
        "Missing":df.groupby("Sitename")["value"].apply(lambda x: x.isna().sum()),
        "Mean"  : g.mean().round(3),
        "SD"    : g.std().round(3),
        "Median": g.median().round(3),
        "Min"   : g.min().round(3),
        "P05"   : g.quantile(.05).round(3),
        "P25"   : g.quantile(.25).round(3),
        "P75"   : g.quantile(.75).round(3),
        "P95"   : g.quantile(.95).round(3),
        "Max"   : g.max().round(3),
    }).reset_index()

DATETIME_FMTS = [
    "%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S","%m/%d/%Y %H:%M",
    "%Y/%m/%d %H:%M:%S","%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d","%d/%m/%Y",
]

def try_parse_datetime(series, fmt=None):
    if fmt and fmt != "auto":
        try:
            return pd.to_datetime(series, format=fmt, utc=True, errors="coerce")
        except Exception:
            pass
    for f in DATETIME_FMTS:
        try:
            p = pd.to_datetime(series, format=f, utc=True, errors="coerce")
            if p.notna().mean() > 0.5:
                return p
        except Exception:
            pass
    return pd.to_datetime(series, utc=True, errors="coerce",
                          infer_datetime_format=True)

def guess_col(cols, patterns):
    for p in patterns:
        for c in cols:
            if re.search(p, c, re.IGNORECASE):
                return c
    return cols[0]

def detect_and_combine_datetime(df):
    cl = {c.lower(): c for c in df.columns}
    dc = next((cl[k] for k in ["date"] if k in cl), None)
    tc = next((cl[k] for k in ["time"] if k in cl), None)
    if dc and tc and dc != tc:
        try:
            comb = pd.to_datetime(
                df[dc].astype(str).str.strip() + " " +
                df[tc].astype(str).str.strip(),
                errors="coerce", utc=True, infer_datetime_format=True)
            if comb.notna().mean() > 0.5:
                df = df.copy()
                df["datetime_combined"] = comb
                return df, "datetime_combined", \
                    f"✅ Combined '{dc}' + '{tc}' → 'datetime_combined'"
        except Exception:
            pass
    return df, None, None

# ==============================================================================
#  DEMO DATA
# ==============================================================================
@st.cache_data(show_spinner=False)
def make_demo_data():
    rng = np.random.default_rng(42)
    sites  = ["Site_A","Site_B","Site_C"]
    params = ["H2S","Ozone","NOx","WindSpeed","WindDirection"]
    dts    = pd.date_range("2022-01-01","2023-12-31 23:00",freq="h",tz="UTC")
    n      = len(dts)
    doy    = dts.day_of_year.values; hod = dts.hour.values
    seas   = np.sin(2*np.pi*(doy-80)/365)
    diur   = np.sin(2*np.pi*(hod-6)/24)
    rows   = []
    off    = {"Site_A":0,"Site_B":3.5,"Site_C":-2}
    for site in sites:
        so = off[site]
        for param in params:
            if   param=="H2S":
                v = 5+so*.6+3*seas+2*diur+rng.normal(0,1.8,n)
                sp = rng.random(n)<0.02; v[sp]+=rng.exponential(12,sp.sum())
                v  = np.maximum(0,v)
            elif param=="Ozone":
                v = np.maximum(0,42+so*2.5+18*seas+22*diur+rng.normal(0,9,n))
            elif param=="NOx":
                rush = np.isin(hod,[7,8,9,17,18,19]).astype(float)*22
                v    = np.maximum(0,38+so*1.8-8*seas-12*diur+rng.normal(0,11,n)+rush)
            elif param=="WindSpeed":
                v = np.maximum(0,3.2+so*.25+1.4*seas+np.abs(rng.normal(0,1.4,n)))
            else:
                base = {"Site_A":225,"Site_B":205,"Site_C":255}[site]
                v    = (base+rng.normal(0,55,n))%360
            msk = rng.random(n)<0.02; v = v.astype(float); v[msk] = np.nan
            rows.append(pd.DataFrame({"Sitename":site,"Parameter":param,
                                       "datetime":dts,"value":v}))
    return pd.concat(rows,ignore_index=True)

DEMO_DATA = make_demo_data()

# ==============================================================================
#  SESSION STATE
# ==============================================================================
if "active_data" not in st.session_state:
    st.session_state.active_data = DEMO_DATA.copy()
    st.session_state.data_source = "demo"

# ==============================================================================
#  SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:10px 0 6px;'>
      <span style='font-family:Rajdhani,sans-serif;font-size:22px;
                   font-weight:700;color:#00E5FF;letter-spacing:2px;'>
        🌿 ENVIROMONITOR</span><br>
      <span style='font-size:11px;color:#546E7A;'>PRO · Matplotlib Edition</span>
    </div>""", unsafe_allow_html=True)

    src   = st.session_state.data_source
    bc    = "#FF9800" if src=="demo" else ("#4CAF50" if src=="user" else "#E63946")
    lbl   = "DEMO" if src=="demo" else "USER"
    st.markdown(f"<span style='background:{bc};color:#fff;padding:3px 10px;"
                f"border-radius:20px;font-size:11px;font-weight:700;'>{lbl} DATA</span>",
                unsafe_allow_html=True)
    st.markdown("---")

    ad     = st.session_state.active_data
    params = sorted(ad["Parameter"].unique())
    sites  = sorted(ad["Sitename"].unique())

    sel_param = st.selectbox("📌 Parameter", params)
    sel_sites = st.multiselect("🏭 Sites", sites, default=sites)

    dt_min = ad["datetime"].min().date()
    dt_max = ad["datetime"].max().date()
    date_range = st.date_input("📅 Date Range",
        value=(dt_min,dt_max), min_value=dt_min, max_value=dt_max)
    if len(date_range)==2:
        d1 = pd.Timestamp(date_range[0],tz="UTC")
        d2 = pd.Timestamp(date_range[1],tz="UTC")+pd.Timedelta("23h59m")
    else:
        d1 = pd.Timestamp(dt_min,tz="UTC")
        d2 = pd.Timestamp(dt_max,tz="UTC")+pd.Timedelta("23h59m")

    st.markdown("---")
    st.markdown('<span style="color:#00E5FF;font-size:12px;font-weight:600;">'
                '⚠️ THRESHOLDS</span>', unsafe_allow_html=True)
    thresh_1h  = st.number_input("1-hr Limit",  value=10.0,min_value=0.0,step=0.5)
    thresh_24h = st.number_input("24-hr Limit", value=8.0, min_value=0.0,step=0.5)

    st.markdown("---")
    st.markdown('<span style="color:#00E5FF;font-size:12px;font-weight:600;">'
                '🎨 EXPORT</span>', unsafe_allow_html=True)
    fig_dpi = st.select_slider("PNG DPI", [100,150,200,300], value=200)
    fig_w   = st.slider("Figure width (in)", 8, 18, 13)

# ==============================================================================
#  CORE DATA
# ==============================================================================
def get_filt():
    return (ad[(ad["Parameter"]==sel_param) &
               (ad["Sitename"].isin(sel_sites)) &
               (ad["datetime"]>=d1) &
               (ad["datetime"]<=d2)]
            .sort_values(["Sitename","datetime"])
            .reset_index(drop=True))

def enrich(df):
    frames=[]
    for site,grp in df.groupby("Sitename"):
        g = grp.copy().sort_values("datetime")
        g["roll24"]  = roll24(g["value"])
        g["exc_1h"]  = g["value"].notna()  & (g["value"]  > thresh_1h)
        g["exc_24h"] = g["roll24"].notna() & (g["roll24"] > thresh_24h)
        g["hod"]     = g["datetime"].dt.hour
        g["dow"]     = g["datetime"].dt.day_name().str[:3]
        g["mon"]     = g["datetime"].dt.strftime("%b")
        g["season"]  = get_season(g["datetime"])
        frames.append(g)
    return pd.concat(frames,ignore_index=True) if frames else df

filt     = get_filt()
enriched = enrich(filt)
pal      = site_pal(sites)
today    = pd.Timestamp.now().date()

# ==============================================================================
#  HEADER
# ==============================================================================
st.markdown("""
<div style='background:linear-gradient(90deg,#0d2137,#0a2a4a);
            border:1px solid #00E5FF22;border-radius:14px;
            padding:16px 28px;margin-bottom:16px;'>
  <h1 style='margin:0;'>🌿 EnviroMonitor Pro</h1>
  <p style='margin:4px 0 0;color:#546E7A;font-size:13px;'>
    Environmental Analysis · Transparent PNG/PDF Downloads · Map Overlay Ready
  </p>
</div>""", unsafe_allow_html=True)

tabs = st.tabs([
    "📂 Data Input","📋 Overview","📈 Time Series","📊 Stats",
    "🎯 Threshold","⚠️ Exceedances","⏰ Temporal",
    "🌬️ Wind Rose","🌀 Polar Plot","⬇️ Export"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 0 – DATA INPUT
# ─────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("### 📂 Upload Data")
    left, right = st.columns([1,1], gap="large")

    with left:
        with st.expander("📁 File Settings", expanded=True):
            uploaded = st.file_uploader("CSV / TSV / TXT / XLSX / XLS",
                type=["csv","tsv","txt","xlsx","xls"])
            c1,c2 = st.columns(2)
            SEP_MAP = {"Comma ,":","," Semicolon ;":";"," Tab \\t":"\t"," Pipe |":"|"}
            sep = SEP_MAP[c1.selectbox("Delimiter",list(SEP_MAP.keys()))]
            has_header = c2.checkbox("Header row",True)
            dt_fmt = st.selectbox("Datetime format",
                ["Auto-detect","%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M",
                 "%d/%m/%Y %H:%M:%S","%d/%m/%Y %H:%M","%Y-%m-%dT%H:%M:%S"])
            dt_fmt_val = None if dt_fmt=="Auto-detect" else dt_fmt

        b1,b2 = st.columns(2)
        if b1.button("▶ Use Demo Data",use_container_width=False):
            st.session_state.active_data = DEMO_DATA.copy()
            st.session_state.data_source = "demo"
            st.success("✅ Demo data loaded!"); st.rerun()

        if b2.button("✔ Load File",use_container_width=False):
            if not uploaded:
                st.error("No file uploaded.")
            else:
                try:
                    ext = uploaded.name.rsplit(".",1)[-1].lower()
                    raw = (pd.read_excel(uploaded,header=0 if has_header else None)
                           if ext in("xlsx","xls") else
                           pd.read_csv(uploaded,sep=sep,
                               header=0 if has_header else None,
                               na_values=["","NA","N/A","null","NULL"]))
                    raw,combined_col,msg = detect_and_combine_datetime(raw)
                    if msg: st.info(msg)
                    st.session_state.raw_df       = raw
                    st.session_state.combined_col = combined_col
                    st.success(f"✅ {len(raw):,} rows × {len(raw.columns)} cols")
                except Exception as e:
                    st.error(f"❌ {e}")

        if "raw_df" in st.session_state:
            raw   = st.session_state.raw_df
            ccols = list(raw.columns)
            st.markdown("#### 🔀 Column Mapping")
            ma,mb = st.columns(2)
            col_site  = ma.selectbox("Sitename",  ccols,
                index=ccols.index(guess_col(ccols,["site","station","location","monitor"])))
            col_param = mb.selectbox("Parameter", ccols,
                index=ccols.index(guess_col(ccols,["param","pollutant","analyte","variable"])))
            dt_def = st.session_state.combined_col or \
                     guess_col(ccols,["datetime","timestamp","date_time","dt"])
            mc,md = st.columns(2)
            col_dt  = mc.selectbox("Datetime", ccols,
                index=ccols.index(dt_def) if dt_def in ccols else 0)
            col_val = md.selectbox("Value", ccols,
                index=ccols.index(guess_col(ccols,["value","conc","concentration","reading"])))

            if st.button("🚀 Apply & Activate",use_container_width=False):
                try:
                    mp = raw[[col_site,col_param,col_dt,col_val]].copy()
                    mp.columns = ["Sitename","Parameter","datetime","value"]
                    mp["Sitename"]  = mp["Sitename"].astype(str)
                    mp["Parameter"] = mp["Parameter"].astype(str)
                    mp["datetime"]  = try_parse_datetime(mp["datetime"].astype(str),dt_fmt_val)
                    mp["value"]     = pd.to_numeric(mp["value"],errors="coerce")
                    mp = mp.dropna(subset=["datetime"]).sort_values(
                        ["Sitename","datetime"]).reset_index(drop=True)
                    if len(mp)==0:
                        st.error("No valid rows. Check column mapping or datetime format.")
                    else:
                        st.session_state.active_data = mp
                        st.session_state.data_source = "user"
                        st.success(f"✅ Activated {len(mp):,} rows!"); st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

    with right:
        st.markdown("#### ✅ Validation")
        if "raw_df" not in st.session_state:
            st.info("Upload a file to see validation.")
        else:
            raw = st.session_state.raw_df
            st.success(f"File: {len(raw):,} rows, {len(raw.columns)} columns")
            if st.session_state.get("combined_col"):
                st.success("Date + Time columns detected & combined")
        st.markdown("#### 👀 Preview")
        if "raw_df" in st.session_state:
            st.dataframe(st.session_state.raw_df.head(200),
                         use_container_width=False, height=300)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 – DATA OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### 📋 Data Overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📄 Records",   f"{len(filt):,}")
    c2.metric("🏭 Sites",     filt["Sitename"].nunique())
    c3.metric("📌 Parameter", sel_param)
    c4.metric("❓ Missing",   int(filt["value"].isna().sum()))
    st.markdown("---")
    show = filt.copy()
    show["datetime"] = show["datetime"].dt.strftime("%Y-%m-%d %H:%M")
    show["value"]    = show["value"].round(3)
    st.dataframe(show[["Sitename","Parameter","datetime","value"]],
                 use_container_width=False, height=460)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 – TIME SERIES
# ─────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### 📈 Time Series")
    if len(enriched)==0:
        st.warning("No data for selected filters.")
    else:
        def ts_fig(y_col, avg_label, threshold, thresh_label):
            fig, ax = plt.subplots(figsize=(fig_w, 4))
            for site, grp in enriched.groupby("Sitename"):
                ax.plot(grp["datetime"], grp[y_col],
                        color=pal.get(site,PALETTE[0]),
                        lw=0.9, alpha=0.85, label=site)
            ax.axhline(threshold, color="#FF6B6B", lw=1.8,
                       ls="--", label=thresh_label)
            ymax = enriched[y_col].max(skipna=True)*1.05
            if ymax > threshold:
                ax.fill_between(enriched["datetime"],
                    threshold, ymax, color="#FF6B6B", alpha=0.05)
            ax.set_title(f"{avg_label} – {sel_param}")
            ax.set_xlabel("Date / Time"); ax.set_ylabel(sel_param)
            ax.legend(framealpha=0.6, fontsize=8)
            fig.tight_layout()
            return fig

        dl_row(ts_fig("value","Hourly Average",thresh_1h,"1-hr Threshold"),
               f"ts_1h_{sel_param}_{today}", fig_dpi)
        dl_row(ts_fig("roll24","24-hr Rolling Average",thresh_24h,"24-hr Threshold"),
               f"ts_24h_{sel_param}_{today}", fig_dpi)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 – DESCRIPTIVE STATS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("### 📊 Descriptive Statistics")

    AGG_MAP = {
        "Hour of Day" : ("hod",   [str(h) for h in range(24)],"Hour of Day"),
        "Day of Week" : ("dow",   DOW_ORDER,                  "Day of Week"),
        "Month"       : ("mon",   MON_ORDER,                  "Month"),
        "Season"      : ("season",SEASONS,                    "Season"),
    }
    agg_by = st.radio("Aggregate by",list(AGG_MAP.keys()),horizontal=True)
    grp_col, order, x_label = AGG_MAP[agg_by]
    enriched[grp_col] = enriched[grp_col].astype(str)

    with st.expander("📋 Overall stats table"):
        st.dataframe(describe_stats(enriched),use_container_width=False)

    with st.expander("📋 Aggregated table"):
        agg_tbl = (enriched.groupby(["Sitename",grp_col])["value"]
                   .agg(N="count",Mean="mean",SD="std",Median="median",
                        P25=lambda x:x.quantile(.25),
                        P75=lambda x:x.quantile(.75),Max="max")
                   .round(3).reset_index())
        st.dataframe(agg_tbl,use_container_width=False)

    sites_sel = [s for s in sorted(sel_sites) if s in enriched["Sitename"].values]
    n_sites   = len(sites_sel)
    order_v   = [o for o in order if str(o) in enriched[grp_col].values]
    n_cats    = len(order_v)

    def bv_fig(plot_type):
        fig, ax = plt.subplots(figsize=(max(10,n_cats*0.65), 5))
        w = 0.7/max(n_sites,1)
        offsets = np.linspace(-0.35+w/2, 0.35-w/2, max(n_sites,1))
        for si, site in enumerate(sites_sel):
            col  = pal.get(site,PALETTE[si])
            grpd = enriched[enriched["Sitename"]==site]
            data = [grpd[grpd[grp_col]==str(o)]["value"].dropna().values
                    for o in order_v]
            xs   = np.arange(n_cats)+offsets[si]
            if plot_type=="box":
                ax.boxplot(data, positions=xs, widths=w*0.85,
                           patch_artist=True,
                           medianprops=dict(color="#fff",lw=1.5),
                           whiskerprops=dict(color=col,lw=0.8),
                           capprops=dict(color=col,lw=0.8),
                           flierprops=dict(marker=".",color=col,ms=2,alpha=0.4),
                           boxprops=dict(facecolor=col+"44",edgecolor=col,lw=0.9),
                           showfliers=True)
            else:
                for xi, (x, dat) in enumerate(zip(xs,data)):
                    if len(dat)>3:
                        vp = ax.violinplot([dat],positions=[x],widths=w*0.85,
                                           showmedians=True,showextrema=False)
                        for pc in vp["bodies"]:
                            pc.set_facecolor(col+"66")
                            pc.set_edgecolor(col); pc.set_lw(0.8)
                        vp["cmedians"].set_color("#fff")
                        vp["cmedians"].set_lw(1.5)
            ax.bar(0,0,color=col,alpha=0.7,label=site)  # legend proxy
        ax.set_xticks(np.arange(n_cats))
        ax.set_xticklabels(order_v,
            rotation=45 if n_cats>12 else 0,
            ha="right" if n_cats>12 else "center",fontsize=8)
        ax.set_title(f"{'Box' if plot_type=='box' else 'Violin'} – {sel_param} by {agg_by}")
        ax.set_xlabel(x_label); ax.set_ylabel(sel_param)
        ax.legend(framealpha=0.6,fontsize=8)
        fig.tight_layout()
        return fig

    st.markdown(f"#### Box Plot – {sel_param} by {agg_by}")
    dl_row(bv_fig("box"),
           f"box_{sel_param}_{agg_by.replace(' ','_')}_{today}", fig_dpi)

    st.markdown(f"#### Violin Plot – {sel_param} by {agg_by}")
    dl_row(bv_fig("violin"),
           f"violin_{sel_param}_{agg_by.replace(' ','_')}_{today}", fig_dpi)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 – THRESHOLD ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("### 🎯 Threshold Analysis")
    if len(enriched)==0:
        st.warning("No data.")
    else:
        def thresh_fig(y_col, avg_label, threshold, thresh_label):
            fig, ax = plt.subplots(figsize=(fig_w,4))
            for site, grp in enriched.groupby("Sitename"):
                ax.plot(grp["datetime"],grp[y_col],
                        color=pal.get(site,PALETTE[0]),lw=0.9,alpha=0.85,label=site)
            ymax = enriched[y_col].max(skipna=True)*1.05
            ax.axhline(threshold,color="#FF6B6B",lw=2,ls="--",label=thresh_label)
            if ymax>threshold:
                ax.fill_between(enriched["datetime"],
                    threshold,ymax,color="#FF6B6B",alpha=0.07,label="Exceedance zone")
            ax.set_ylim(bottom=0,top=ymax)
            ax.set_title(f"{avg_label} – {sel_param} vs Threshold")
            ax.set_xlabel("Date / Time"); ax.set_ylabel(sel_param)
            ax.legend(framealpha=0.6,fontsize=8)
            fig.tight_layout()
            return fig

        dl_row(thresh_fig("value","1-hr Average",thresh_1h,"1-hr Threshold"),
               f"thresh_1h_{sel_param}_{today}", fig_dpi)
        dl_row(thresh_fig("roll24","24-hr Rolling Average",thresh_24h,"24-hr Threshold"),
               f"thresh_24h_{sel_param}_{today}", fig_dpi)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 – EXCEEDANCE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### ⚠️ Exceedance Analysis")
    if len(enriched)==0:
        st.warning("No data.")
    else:
        exc_rows=[]
        for site,grp in enriched.groupby("Sitename"):
            v1=grp["value"].notna().sum(); v24=grp["roll24"].notna().sum()
            e1=grp["exc_1h"].sum(); e24=grp["exc_24h"].sum()
            exc_rows.append(dict(Site=site,
                Thresh_1h=thresh_1h, Valid_1h=v1, Exceed_1h=e1,
                Pct_1h=round(100*e1/max(v1,1),2),
                Thresh_24h=thresh_24h,Valid_24h=v24,Exceed_24h=e24,
                Pct_24h=round(100*e24/max(v24,1),2)))
        exc_df = pd.DataFrame(exc_rows)
        ea,eb  = st.columns(2)
        ea.markdown("**1-hr Exceedances**")
        ea.dataframe(exc_df[["Site","Thresh_1h","Valid_1h","Exceed_1h","Pct_1h"]],
                     use_container_width=False)
        eb.markdown("**24-hr Exceedances**")
        eb.dataframe(exc_df[["Site","Thresh_24h","Valid_24h","Exceed_24h","Pct_24h"]],
                     use_container_width=False)

        def exc_bar(grp_col, order, x_label, exc_col, title):
            rows=[]
            for site,grp in enriched.groupby("Sitename"):
                for gv,sg in grp.groupby(grp_col):
                    rows.append({"Site":site,"Group":str(gv),
                                 "Count":int(sg[exc_col].sum())})
            if not rows: return plt.figure()
            df2 = pd.DataFrame(rows)
            df2["Group"] = pd.Categorical(df2["Group"],
                categories=[str(o) for o in order],ordered=True)
            df2 = df2.sort_values("Group")
            pivot = df2.pivot(index="Group",columns="Site",values="Count").fillna(0)
            n_s   = len(pivot.columns)
            fig, ax = plt.subplots(figsize=(max(9,len(order)*0.5),4))
            x  = np.arange(len(pivot.index)); w = 0.7/max(n_s,1)
            for si,site in enumerate(pivot.columns):
                off = (si-n_s/2+0.5)*w
                ax.bar(x+off,pivot[site].values,w*0.9,
                       color=pal.get(site,PALETTE[si]),alpha=0.85,label=site)
            ax.set_xticks(x)
            ax.set_xticklabels(pivot.index,
                rotation=45 if len(order)>10 else 0,
                ha="right" if len(order)>10 else "center",fontsize=8)
            ax.set_title(title); ax.set_xlabel(x_label); ax.set_ylabel("# Exceedances")
            ax.legend(framealpha=0.6,fontsize=8)
            fig.tight_layout(); return fig

        def pct_bar(col_y, title):
            fig,ax = plt.subplots(figsize=(6,3.5))
            for i,row in exc_df.iterrows():
                ax.bar(i,row[col_y],color=pal.get(row["Site"],PALETTE[i]),alpha=0.85,label=row["Site"])
                ax.text(i,row[col_y]+0.3,f"{row[col_y]}%",ha="center",va="bottom",fontsize=8,color=TEXT)
            ax.set_xticks(range(len(exc_df))); ax.set_xticklabels(exc_df["Site"])
            ax.set_title(title); ax.set_ylabel("% Exceedances")
            ax.legend(framealpha=0.6,fontsize=8); fig.tight_layout(); return fig

        st.markdown("#### % Exceedances")
        pa,pb = st.columns(2)
        with pa:
            dl_row(pct_bar("Pct_1h","% Exceed – 1-hr"),
                   f"pct_1h_{sel_param}_{today}",fig_dpi)
        with pb:
            dl_row(pct_bar("Pct_24h","% Exceed – 24-hr"),
                   f"pct_24h_{sel_param}_{today}",fig_dpi)

        for label, gc, ord_, xl, sfx in [
            ("Hour of Day","hod",range(24),"Hour",   "hod"),
            ("Day of Week","dow",DOW_ORDER,"Day",    "dow"),
            ("Month",      "mon",MON_ORDER,"Month",  "mon"),
        ]:
            st.markdown(f"#### Exceedances by {label}")
            ca,cb = st.columns(2)
            with ca:
                dl_row(exc_bar(gc,ord_,xl,"exc_1h",f"# Exceed/{label} – 1-hr"),
                       f"exc_{sfx}_1h_{sel_param}_{today}",fig_dpi)
            with cb:
                dl_row(exc_bar(gc,ord_,xl,"exc_24h",f"# Exceed/{label} – 24-hr"),
                       f"exc_{sfx}_24h_{sel_param}_{today}",fig_dpi)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 – TEMPORAL PATTERNS
# ─────────────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("### ⏰ Temporal Patterns")

    def temporal_fig(grp_col, order, x_label, title):
        enriched[grp_col] = enriched[grp_col].astype(str)
        order_s = [str(o) for o in order]
        fig, ax = plt.subplots(figsize=(fig_w, 4.5))
        for site, grp in enriched.groupby("Sitename"):
            col = pal.get(site,PALETTE[0])
            agg = (grp.groupby(grp_col)["value"]
                   .agg(Mean="mean",SD="std",
                        P25=lambda v:v.quantile(.25),
                        P75=lambda v:v.quantile(.75))
                   .reindex(order_s))
            xi = np.arange(len(order_s))
            ax.fill_between(xi,agg["P25"].values,agg["P75"].values,
                            color=col,alpha=0.12)
            ax.errorbar(xi,agg["Mean"].values,yerr=agg["SD"].values,
                        color=col,lw=1.8,marker="o",ms=4,
                        capsize=3,capthick=0.8,elinewidth=0.8,label=site)
        ax.set_xticks(np.arange(len(order_s)))
        ax.set_xticklabels(order_s,
            rotation=45 if len(order_s)>12 else 0,
            ha="right" if len(order_s)>12 else "center",fontsize=8)
        ax.set_title(title); ax.set_xlabel(x_label); ax.set_ylabel(sel_param)
        ax.legend(framealpha=0.6,fontsize=8)
        fig.tight_layout(); return fig

    st.markdown("#### 🕛 Diurnal Pattern")
    dl_row(temporal_fig("hod",range(24),"Hour of Day",
                        f"Diurnal – {sel_param} (Mean±SD, IQR)"),
           f"diurnal_{sel_param}_{today}",fig_dpi)

    st.markdown("#### 📅 Monthly Pattern")
    dl_row(temporal_fig("mon",MON_ORDER,"Month",
                        f"Monthly – {sel_param} (Mean±SD, IQR)"),
           f"monthly_{sel_param}_{today}",fig_dpi)

    # Seasonal 2×2 diurnal
    st.markdown("#### 🍂 Seasonal Diurnal – 2×2")
    enriched["season"] = get_season(enriched["datetime"])
    fig_sd, axes_sd = plt.subplots(2,2,figsize=(fig_w,8),sharey=True)
    fig_sd.suptitle(f"Seasonal Diurnal – {sel_param}",fontsize=13,
                    color="#E0F7FA",fontweight="bold")
    for idx,(season,ax) in enumerate(zip(SEASONS,axes_sd.flat)):
        sdf = enriched[enriched["season"]==season]
        n_s = int(sdf["value"].count())
        for site, grp in sdf.groupby("Sitename"):
            col = pal.get(site,PALETTE[0])
            agg = grp.groupby("hod")["value"].agg(Mean="mean",SD="std").reindex(range(24))
            ax.fill_between(agg.index,(agg["Mean"]-agg["SD"]).values,
                            (agg["Mean"]+agg["SD"]).values,color=col,alpha=0.15)
            ax.plot(agg.index,agg["Mean"].values,color=col,lw=1.6,
                    marker="o",ms=3,label=site)
        ax.set_title(f"{season}  n={n_s:,}",fontsize=10)
        ax.set_xlabel("Hour" if idx>=2 else "")
        ax.set_ylabel(sel_param if idx%2==0 else "")
        ax.set_xticks(range(0,24,3)); ax.legend(framealpha=0.5,fontsize=7)
    fig_sd.tight_layout()
    dl_row(fig_sd,f"seas_diurnal_{sel_param}_{today}",fig_dpi)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 – WIND ROSE
# ─────────────────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("### 🌬️ Wind Rose")

    all_params = sorted(ad["Parameter"].unique())
    all_sites  = sorted(ad["Sitename"].unique())

    wc1,wc2,wc3,wc4,wc5 = st.columns(5)
    wr_site     = wc1.selectbox("Site", all_sites, key="wr_site")
    wr_ws_p     = wc2.selectbox("Wind Speed param", all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search(r"wind.?speed|wspeed|^ws$",p,re.I)),0),key="wr_ws_p")
    wr_wd_p     = wc3.selectbox("Wind Dir param", all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search(r"wind.?dir|wdir|^wd$|direction",p,re.I)),
            min(1,len(all_params)-1)),key="wr_wd_p")
    wr_ws_unit  = wc4.text_input("WS unit","m/s",key="wr_ws_unit")
    wr_n_bins   = wc5.number_input("Speed bins",3,10,5,1,key="wr_n_bins")

    gen_wr = st.button("🌬️ Generate Wind Roses",use_container_width=False)

    def build_wind_df():
        src = ad[ad["Sitename"]==wr_site]
        ws  = src[src["Parameter"]==wr_ws_p][["datetime","value"]].rename(columns={"value":"ws"})
        wd  = src[src["Parameter"]==wr_wd_p][["datetime","value"]].rename(columns={"value":"wd"})
        df  = ws.merge(wd,on="datetime").dropna()
        df  = df[(df["datetime"]>=d1)&(df["datetime"]<=d2)]
        df["season"] = get_season(df["datetime"])
        return df

    def mpl_windrose(ax, df_wr, title="", n_spd=5, n_dir=16, ws_unit="m/s"):
        if len(df_wr)<10:
            ax.set_title(f"{title}\n(insufficient data)",fontsize=9); return
        total     = len(df_wr)
        dir_bins  = np.linspace(0,360,n_dir+1)
        dir_mids  = (dir_bins[:-1]+dir_bins[1:])/2
        spd_max   = df_wr["ws"].quantile(0.99)
        spd_bins  = np.linspace(0,spd_max,n_spd+1)
        spd_labs  = [f"{spd_bins[i]:.2g}–{spd_bins[i+1]:.2g} {ws_unit}"
                     for i in range(n_spd)]
        df_wr = df_wr.copy()
        df_wr["dir_bin"] = pd.cut(df_wr["wd"],bins=dir_bins,
                                  labels=range(n_dir),include_lowest=True).astype(float)
        df_wr["spd_bin"] = pd.cut(df_wr["ws"],bins=spd_bins,
                                  labels=range(n_spd),include_lowest=True).astype(float)
        colors  = plt.cm.YlOrRd(np.linspace(0.2,0.95,n_spd))
        theta   = np.deg2rad(dir_mids)
        width   = 2*np.pi/n_dir*0.9
        bottoms = np.zeros(n_dir)
        for si in range(n_spd):
            cnts = np.array([
                ((df_wr["dir_bin"]==di)&(df_wr["spd_bin"]==si)).sum()
                for di in range(n_dir)])
            pct = cnts/total*100
            ax.bar(theta,pct,width=width,bottom=bottoms,
                   color=colors[si],alpha=0.88,label=spd_labs[si],
                   edgecolor="#0a1628",linewidth=0.4)
            bottoms += pct
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location("N")
        ax.set_xticklabels(["N","NE","E","SE","S","SW","W","NW"],fontsize=7,color=TEXT)
        ax.set_yticklabels([f"{y:.0f}%" for y in ax.get_yticks()],fontsize=6,color=TEXT)
        ax.tick_params(colors=TEXT)
        for sp in ax.spines.values(): sp.set_edgecolor(GRID)
        ax.set_facecolor("none")
        n_cnt = len(df_wr)
        ax.set_title(f"{title}\nn={n_cnt:,}",fontsize=9,color="#E0F7FA",pad=8)

    if gen_wr:
        wind_df = build_wind_df()
        if len(wind_df)<10:
            st.error("Not enough wind data. Try a wider date range.")
        else:
            # Overall
            st.markdown(f"#### Overall Wind Rose – {wr_site}")
            fig_wr,ax_wr = plt.subplots(figsize=(7,7),
                                        subplot_kw=dict(projection="polar"))
            mpl_windrose(ax_wr,wind_df,
                f"Wind Rose – {wr_site} | All Data",
                n_spd=wr_n_bins,ws_unit=wr_ws_unit)
            handles,labels = ax_wr.get_legend_handles_labels()
            fig_wr.legend(handles,labels,loc="lower center",
                          ncol=min(wr_n_bins,3),fontsize=7,
                          title=f"Wind Speed ({wr_ws_unit})",
                          title_fontsize=8,framealpha=0.6,
                          bbox_to_anchor=(0.5,-0.02))
            fig_wr.tight_layout()
            dl_row(fig_wr,f"windrose_{wr_site}_{today}",fig_dpi)

            # Seasonal 2×2
            st.markdown(f"#### Seasonal Wind Roses – {wr_site} (2×2)")
            fig4,axes4 = plt.subplots(2,2,figsize=(fig_w,fig_w*0.85),
                                      subplot_kw=dict(projection="polar"))
            fig4.suptitle(f"Seasonal Wind Roses – {wr_site}  N={len(wind_df):,}",
                          fontsize=13,color="#E0F7FA",fontweight="bold")
            for idx,(season,ax) in enumerate(zip(SEASONS,axes4.flat)):
                sdf = wind_df[wind_df["season"]==season]
                mpl_windrose(ax,sdf,season,n_spd=wr_n_bins,ws_unit=wr_ws_unit)
            handles,labels = axes4.flat[0].get_legend_handles_labels()
            fig4.legend(handles,labels,loc="lower center",
                        ncol=min(wr_n_bins,5),fontsize=8,
                        title=f"Wind Speed ({wr_ws_unit})",
                        title_fontsize=9,framealpha=0.6,
                        bbox_to_anchor=(0.5,-0.01))
            fig4.tight_layout()
            dl_row(fig4,f"windrose_seasonal_{wr_site}_{today}",fig_dpi)
    else:
        st.info("Configure and click **Generate Wind Roses**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 8 – POLAR PLOT  (openair-style)
# ─────────────────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("### 🌀 Polar Plot — openair style")
    st.markdown("<small style='color:#546E7A;'>Kernel-smoothed bivariate concentration "
                "surface — same algorithm as openair::polarPlot() in R.</small>",
                unsafe_allow_html=True)

    ps1,ps2,ps3,ps4,ps5 = st.columns(5)
    pp_site  = ps1.selectbox("Site",all_sites,key="pp_site")
    pp_stat  = ps2.selectbox("Statistic",
        ["mean","median","max","percentile","count","weighted.mean"],key="pp_stat")
    pp_pct   = ps3.number_input("Percentile",5,99,95,5,key="pp_pct")
    pp_ws_p  = ps4.selectbox("Wind Speed",all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search(r"wind.?speed|wspeed|^ws$",p,re.I)),0),key="pp_ws_p")
    pp_wd_p  = ps5.selectbox("Wind Dir",all_params,
        index=next((i for i,p in enumerate(all_params)
            if re.search(r"wind.?dir|wdir|^wd$|direction",p,re.I)),
            min(1,len(all_params)-1)),key="pp_wd_p")

    pu1,pu2,pu3,pu4 = st.columns(4)
    pp_ws_unit   = pu1.text_input("WS unit","m/s",key="pp_ws_unit")
    pp_poll_unit = pu2.text_input(f"{sel_param} unit","ppb",key="pp_poll_unit")
    pp_smooth    = pu3.slider("Smoothing σ",0.5,6.0,2.0,0.5,key="pp_smooth")
    pp_n_grid    = pu4.select_slider("Grid",options=[60,80,100,120,150],
                                     value=100,key="pp_ngrid")

    gen_pp = st.button("🌀 Generate Polar Plots",use_container_width=False)

    def _surface(df_in, n_grid, smooth, stat, pct):
        df2 = df_in.dropna(subset=["ws","wd","pollutant"]).copy()
        if len(df2)<20: return None
        wd_r  = np.deg2rad(df2["wd"].values)
        ws_v  = df2["ws"].values
        poll  = df2["pollutant"].values
        u     = ws_v*np.sin(wd_r); v = ws_v*np.cos(wd_r)
        ws_mx = float(np.quantile(ws_v,0.99))
        cw    = 2.0*ws_mx/n_grid
        ci    = np.clip(((u+ws_mx)/cw).astype(int),0,n_grid-1)
        ri    = np.clip(((v+ws_mx)/cw).astype(int),0,n_grid-1)
        cells   = [[[] for _ in range(n_grid)] for _ in range(n_grid)]
        ws_c    = [[[] for _ in range(n_grid)] for _ in range(n_grid)]
        for k in range(len(u)):
            cells[ri[k]][ci[k]].append(poll[k])
            ws_c[ri[k]][ci[k]].append(ws_v[k])
        Z_num = np.zeros((n_grid,n_grid))
        Z_cnt = np.zeros((n_grid,n_grid))
        FN = {"mean":np.nanmean,"median":np.nanmedian,"max":np.nanmax,
              "percentile":lambda x:np.nanpercentile(x,pct),
              "count":lambda x:float(len(x)),"weighted.mean":None}
        fn = FN[stat]
        for r in range(n_grid):
            for c in range(n_grid):
                vals = cells[r][c]
                if not vals: continue
                Z_cnt[r,c] = len(vals)
                if stat=="weighted.mean":
                    ww = ws_c[r][c]
                    Z_num[r,c] = (np.array(vals)*np.array(ww)).sum()/(np.sum(ww)+1e-9)
                elif stat=="count":
                    Z_num[r,c] = float(len(vals))
                else:
                    Z_num[r,c] = fn(np.array(vals))
        if stat in("count","weighted.mean"):
            Z_sm = gaussian_filter(Z_num,sigma=smooth)
        else:
            sm_n = gaussian_filter(Z_num*Z_cnt,sigma=smooth)
            sm_d = gaussian_filter(Z_cnt,sigma=smooth)
            Z_sm = np.where(sm_d>0.5,sm_n/sm_d,np.nan)
        g1 = np.linspace(-ws_mx,ws_mx,n_grid)
        gx,gy = np.meshgrid(g1,g1)
        Z_sm[np.sqrt(gx**2+gy**2)>ws_mx] = np.nan
        return g1, Z_sm, ws_mx

    def draw_polar_ax(ax, df_in, title="", n_grid=100, smooth=2.0,
                      ws_unit="m/s", poll_unit="", stat="mean", pct=95,
                      cbar_ax=None):
        res = _surface(df_in,n_grid,smooth,stat,pct)
        n_tot = int(df_in["pollutant"].count()) if res else 0
        if res is None:
            ax.text(0.5,0.5,"Insufficient data",ha="center",va="center",
                    transform=ax.transAxes,color=TEXT)
            if title: ax.set_title(title,fontsize=10)
            ax.axis("off"); return None
        g1, Z, ws_mx = res
        im = ax.pcolormesh(g1,g1,Z,cmap="jet",shading="auto",rasterized=True)
        ax.set_aspect("equal")
        tc = np.linspace(0,2*np.pi,300)
        # Speed rings
        n_rng = 4
        for rws in np.linspace(ws_mx/n_rng,ws_mx,n_rng):
            ax.plot(rws*np.sin(tc),rws*np.cos(tc),
                    color=GRID,lw=0.6,ls="--",alpha=0.7)
            ax.text(rws*0.71,rws*0.71,f"{rws:.1f}\n{ws_unit}",
                    fontsize=5,color=TEXT,alpha=0.7,ha="left",va="bottom")
        # Spokes
        for deg in range(0,360,45):
            rd = np.deg2rad(deg)
            ax.plot([0,ws_mx*np.sin(rd)],[0,ws_mx*np.cos(rd)],
                    color=GRID,lw=0.5,alpha=0.5)
        # Compass
        for lbl,deg in [("N",0),("NE",45),("E",90),("SE",135),
                        ("S",180),("SW",225),("W",270),("NW",315)]:
            rd = np.deg2rad(deg)
            ax.text(ws_mx*1.1*np.sin(rd),ws_mx*1.1*np.cos(rd),
                    lbl,ha="center",va="center",fontsize=8,
                    fontweight="bold",color=ACC)
        # N arrow
        ax.annotate("",xy=(0,ws_mx*0.88),xytext=(0,ws_mx*0.62),
                    arrowprops=dict(arrowstyle="->",color=ACC,lw=1.5))
        ax.set_xlim(-ws_mx*1.18,ws_mx*1.18)
        ax.set_ylim(-ws_mx*1.18,ws_mx*1.18)
        ax.axis("off")
        sl  = f"{stat} ({pct}th)" if stat=="percentile" else stat
        usl = f" ({poll_unit})" if poll_unit else ""
        if title:
            ax.set_title(f"{title}\nStat: {sl} | N={n_tot:,}",
                         fontsize=9,color="#E0F7FA",pad=4)
        if cbar_ax is not None:
            cb = plt.colorbar(im,cax=cbar_ax)
            cb.ax.yaxis.set_tick_params(color=TEXT,labelsize=7)
            cb.set_label(f"{sel_param}{usl} – {sl}",color=TEXT,fontsize=8)
            plt.setp(cb.ax.yaxis.get_ticklabels(),color=TEXT)
        return im

    def build_polar_df():
        src = ad if pp_site=="All Sites" else ad[ad["Sitename"]==pp_site]
        ws  = src[src["Parameter"]==pp_ws_p][["datetime","value"]].rename(columns={"value":"ws"})
        wd  = src[src["Parameter"]==pp_wd_p][["datetime","value"]].rename(columns={"value":"wd"})
        po  = src[src["Parameter"]==sel_param][["datetime","value"]].rename(columns={"value":"pollutant"})
        df  = ws.merge(wd,on="datetime").merge(po,on="datetime")
        df  = df[(df["datetime"]>=d1)&(df["datetime"]<=d2)].dropna()
        df["season"] = get_season(df["datetime"])
        return df

    if gen_pp:
        pp_df = build_polar_df()
        if len(pp_df)<30:
            st.error("Not enough data. Try a wider date range.")
        else:
            # Overall
            st.markdown(f"#### Overall Polar Plot – {sel_param} | {pp_site}")
            sz  = min(fig_w, 9)
            fig_pp = plt.figure(figsize=(sz+1.2, sz))
            gs  = fig_pp.add_gridspec(1,2,width_ratios=[sz,0.35],wspace=0.02)
            ax_pp  = fig_pp.add_subplot(gs[0,0])
            cb_ax  = fig_pp.add_subplot(gs[0,1])
            draw_polar_ax(ax_pp,pp_df,
                title=f"Polar Plot – {sel_param} | {pp_site} | All",
                n_grid=pp_n_grid,smooth=pp_smooth,
                ws_unit=pp_ws_unit,poll_unit=pp_poll_unit,
                stat=pp_stat,pct=pp_pct,cbar_ax=cb_ax)
            fig_pp.tight_layout()
            dl_row(fig_pp,f"polar_{sel_param}_{pp_site}_{today}",fig_dpi)

            with st.expander("📊 Dataset statistics"):
                ss = pp_df.groupby("season")["pollutant"].agg(
                    N="count",
                    Mean=lambda x:round(x.mean(),3),
                    Median=lambda x:round(x.median(),3),
                    P95=lambda x:round(x.quantile(.95),3),
                    Max=lambda x:round(x.max(),3)).reset_index()
                st.dataframe(ss,use_container_width=False)

            # Seasonal 2×2
            st.markdown(f"#### Seasonal Polar Plots – {sel_param} | {pp_site} (2×2)")
            fig_s4 = plt.figure(figsize=(fig_w+1.5, fig_w*0.95))
            # 2-row, 3-col gridspec: 2 plot cols + 1 narrow colorbar col, repeated twice
            gs4 = gridspec.GridSpec(2,3,
                width_ratios=[1,1,0.07],
                wspace=0.05, hspace=0.15,
                figure=fig_s4)
            fig_s4.suptitle(
                f"Seasonal Polar Plots – {sel_param} ({pp_stat}) | {pp_site}",
                fontsize=13,color="#E0F7FA",fontweight="bold")
            axes_s4 = [[fig_s4.add_subplot(gs4[r,c]) for c in range(2)] for r in range(2)]
            cb_ax4  = fig_s4.add_subplot(gs4[:,2])
            last_im = None
            for idx,season in enumerate(SEASONS):
                r,c   = idx//2, idx%2
                sdf   = pp_df[pp_df["season"]==season]
                n_s   = int(sdf["pollutant"].count())
                im = draw_polar_ax(axes_s4[r][c],sdf,
                    title=f"{season}  (n={n_s:,})",
                    n_grid=max(60,pp_n_grid-20),smooth=pp_smooth,
                    ws_unit=pp_ws_unit,poll_unit=pp_poll_unit,
                    stat=pp_stat,pct=pp_pct,
                    cbar_ax=None)
                if im is not None: last_im = im
            if last_im is not None:
                cb = plt.colorbar(last_im,cax=cb_ax4)
                sl  = f"{pp_stat} ({pp_pct}th)" if pp_stat=="percentile" else pp_stat
                usl = f" ({pp_poll_unit})" if pp_poll_unit else ""
                cb.set_label(f"{sel_param}{usl} – {sl}",color=TEXT,fontsize=9)
                cb.ax.yaxis.set_tick_params(color=TEXT,labelsize=8)
                plt.setp(cb.ax.yaxis.get_ticklabels(),color=TEXT)
            dl_row(fig_s4,f"polar_seasonal_{sel_param}_{pp_site}_{today}",fig_dpi)
    else:
        st.info("Configure and click **Generate Polar Plots**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 9 – EXPORT
# ─────────────────────────────────────────────────────────────────────────────
with tabs[9]:
    st.markdown("### ⬇️ Export Data")

    st.markdown("""
    <div style='background:#0d1f3c;border:1px solid #1a3a5c;border-radius:10px;
                padding:16px 20px;margin-bottom:16px;'>
    <h3 style='color:#00E5FF;margin:0 0 10px;'>📄 Excel Report Sheets</h3>
    <ul style='color:#90CAF9;line-height:2;font-size:13px;margin:0;'>
      <li><b style="color:#E0F7FA">Raw_Data</b> — filtered hourly values</li>
      <li><b style="color:#E0F7FA">Rolling_24h</b> — 24-hr rolling averages</li>
      <li><b style="color:#E0F7FA">Exceedances_1h / 24h</b> — rows exceeding threshold</li>
      <li><b style="color:#E0F7FA">Stats_Overall / Hourly / Daily / Monthly / Seasonal</b></li>
      <li><b style="color:#E0F7FA">Exc_Summary</b> — per-site exceedance counts</li>
      <li><b style="color:#E0F7FA">Thresholds</b> — applied settings & metadata</li>
    </ul></div>""", unsafe_allow_html=True)

    @st.cache_data(show_spinner="Building Excel…")
    def build_excel(data_json, param, sites_tuple, d1_str, d2_str, t1, t24):
        df = pd.read_json(io.StringIO(data_json),orient="records")
        df["datetime"] = pd.to_datetime(df["datetime"],utc=True)
        fdf = df[(df["Parameter"]==param)&(df["Sitename"].isin(sites_tuple))&
                 (df["datetime"]>=pd.Timestamp(d1_str))&
                 (df["datetime"]<=pd.Timestamp(d2_str))]
        fdf = fdf.sort_values(["Sitename","datetime"]).reset_index(drop=True)
        frames=[]
        for site,grp in fdf.groupby("Sitename"):
            g = grp.copy().sort_values("datetime")
            g["roll24"]  = roll24(g["value"])
            g["exc_1h"]  = g["value"].notna()  & (g["value"]  > t1)
            g["exc_24h"] = g["roll24"].notna() & (g["roll24"] > t24)
            g["hod"]     = g["datetime"].dt.hour
            g["dow"]     = g["datetime"].dt.day_name().str[:3]
            g["mon"]     = g["datetime"].dt.strftime("%b")
            g["season"]  = get_season(g["datetime"])
            frames.append(g)
        enr = pd.concat(frames,ignore_index=True) if frames else fdf
        buf = io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as xw:
            def ws(name,d): d.to_excel(xw,sheet_name=name,index=False)
            ro = fdf.copy(); ro["datetime"] = ro["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            ws("Raw_Data",ro)
            r24 = enr[["Sitename","datetime","value","roll24"]].copy()
            r24.columns = ["Sitename","datetime","Value_1h","RollingAvg_24h"]
            r24["datetime"] = r24["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            r24[["Value_1h","RollingAvg_24h"]] = r24[["Value_1h","RollingAvg_24h"]].round(3)
            ws("Rolling_24h",r24)
            e1 = enr[enr["exc_1h"]][["Sitename","datetime","value"]].copy()
            e1.columns = ["Sitename","datetime","Value_1h"]
            e1["datetime"] = e1["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            e1["Threshold_1h"] = t1; e1["Exceed_Amt"] = (e1["Value_1h"]-t1).round(3)
            ws("Exceedances_1h",e1)
            e24 = enr[enr["exc_24h"]][["Sitename","datetime","roll24"]].copy()
            e24.columns = ["Sitename","datetime","RollingAvg_24h"]
            e24["datetime"] = e24["datetime"].dt.strftime("%Y-%m-%d %H:%M")
            e24["Threshold_24h"] = t24; e24["Exceed_Amt"] = (e24["RollingAvg_24h"]-t24).round(3)
            ws("Exceedances_24h",e24)
            ws("Stats_Overall",describe_stats(enr))
            for col,key,cn in [("hod","Stats_Hourly","HourOfDay"),
                                ("dow","Stats_Daily","DayOfWeek"),
                                ("mon","Stats_Monthly","Month"),
                                ("season","Stats_Seasonal","Season")]:
                agg = (enr.groupby(["Sitename",col])["value"]
                       .agg(N="count",Mean="mean",SD="std",Median="median",
                            P25=lambda x:x.quantile(.25),
                            P75=lambda x:x.quantile(.75),
                            Min="min",Max="max").round(3).reset_index()
                       .rename(columns={col:cn}))
                ws(key,agg)
            er=[]
            for site,grp in enr.groupby("Sitename"):
                v1=grp["value"].notna().sum(); v24=grp["roll24"].notna().sum()
                e1c=grp["exc_1h"].sum(); e24c=grp["exc_24h"].sum()
                er.append(dict(Site=site,Threshold_1h=t1,Threshold_24h=t24,
                    Valid_1h=v1,Exceed_1h=e1c,Pct_1h=round(100*e1c/max(v1,1),2),
                    Valid_24h=v24,Exceed_24h=e24c,
                    Pct_24h=round(100*e24c/max(v24,1),2)))
            ws("Exc_Summary",pd.DataFrame(er))
            ws("Thresholds",pd.DataFrame([
                {"Period":"1-hr","Threshold":t1,"Parameter":param,
                 "Sites":";".join(sites_tuple),"From":d1_str,"To":d2_str},
                {"Period":"24-hr","Threshold":t24,"Parameter":param,
                 "Sites":";".join(sites_tuple),"From":d1_str,"To":d2_str}]))
        return buf.getvalue()

    data_json = st.session_state.active_data.to_json(orient="records",date_format="iso")
    ec1,ec2   = st.columns(2)
    with ec1:
        if st.button("🔨 Build Excel Report",use_container_width=False):
            st.session_state.xlsx_bytes = build_excel(
                data_json, sel_param, tuple(sorted(sel_sites)),
                str(d1), str(d2), thresh_1h, thresh_24h)
            st.success("✅ Ready – click Download below.")
        if "xlsx_bytes" in st.session_state:
            st.download_button("⬇️ Download XLSX",
                data=st.session_state.xlsx_bytes,
                file_name=f"EnviroMonitor_{sel_param}_{today}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False)
    with ec2:
        csv_out = filt.copy()
        csv_out["datetime"] = csv_out["datetime"].dt.strftime("%Y-%m-%d %H:%M")
        st.download_button("⬇️ Download CSV",
            data=csv_out.to_csv(index=False).encode(),
            file_name=f"raw_{sel_param}_{today}.csv",
            mime="text/csv",use_container_width=False)

    st.markdown("---")
    st.markdown("""
    <div style='background:#0d1f3c;border:1px solid #1a3a5c;border-radius:10px;
                padding:14px 18px;'>
    <h3 style='color:#00E5FF;margin:0 0 8px;'>🖼️ Transparent PNG / PDF</h3>
    <p style='color:#90CAF9;font-size:13px;margin:0;'>
    Every chart has <b>⬇️ PNG</b> and <b>⬇️ PDF</b> download buttons directly below it.
    All PNGs are exported with <code>transparent=True</code> — ready to overlay on
    maps in QGIS, ArcGIS, Illustrator or any image editor.<br>
    Use the <b>PNG DPI</b> slider in the sidebar to control resolution (200 dpi default,
    300 dpi for print quality).
    </p></div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center;padding:14px 0 6px;color:#37474F;font-size:12px;'>
  EnviroMonitor Pro · Matplotlib Edition ·
  <span style='color:#00E5FF44;'>Transparent PNG + PDF · Excel Export</span>
</div>""", unsafe_allow_html=True)

"""
Aster Health — Cross-Border Care Intelligence Dashboard
Powered by Snowflake Cortex + dbt
"""

import streamlit as st
import snowflake.connector
import pandas as pd
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

st.set_page_config(
    page_title="Aster Health",
    page_icon="✦",
    layout="wide"
)

# ── connection ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    with open("/Users/juliancharlankelly/.ssh/snowflake_key.p8", "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    pkb = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return snowflake.connector.connect(
        account="rorvdct-mib64142",
        user="JULIANKELLY",
        private_key=pkb,
        database="DBT_CORTEX_LLMS",
        warehouse="CORTEX_WH",
        schema="ANALYTICS",
        role="DBT_ROLE"
    )

@st.cache_data(ttl=300)
def query(sql):
    conn = get_connection()
    df = pd.read_sql(sql, conn)
    df.columns = df.columns.str.upper()
    return df

# ── styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #08101c; }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #f0f6ff; }
    .metric-card {
        background: #0f1929;
        border: 1px solid #1e2d42;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-val { font-size: 28px; font-weight: 700; color: #f0f6ff; }
    .metric-lbl { font-size: 11px; color: #4a6080; text-transform: uppercase; letter-spacing: 1.5px; }
    .finding-card {
        background: #0f1929;
        border: 1px solid #1e2d42;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 8px;
    }
    .sev-critical { color: #fca5a5; }
    .sev-high     { color: #fdba74; }
    .sev-medium   { color: #fde047; }
    .sev-low      { color: #86efac; }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding-bottom:16px; border-bottom:1px solid #1e2d42; margin-bottom:24px;">
    <div style="font-size:22px; font-weight:700; color:#f0f6ff; letter-spacing:-0.5px;">✦ Aster Health</div>
    <div style="font-size:11px; color:#4a6080; letter-spacing:2.5px; text-transform:uppercase; margin-top:2px;">
        Cross-Border Care Intelligence · Snowflake Cortex + dbt
    </div>
</div>
""", unsafe_allow_html=True)

# ── load data ─────────────────────────────────────────────────────────────────
try:
    patients       = query("SELECT * FROM DBT_CORTEX_LLMS.STAGE.PATIENTS")
    care_gaps      = query("SELECT * FROM ANALYTICS.FACT_CARE_GAPS")
    encounters     = query("SELECT * FROM ANALYTICS.FACT_CLINICAL_ENCOUNTERS")
    labs           = query("SELECT * FROM ANALYTICS.FACT_LAB_RESULTS")
    risk_analysis  = query("SELECT * FROM ANALYTICS.ENCOUNTER_RISK_ANALYSIS")
    profiles       = query("SELECT * FROM ANALYTICS.PATIENT_PROFILE_SIGNALS")
    insights       = query("SELECT * FROM ANALYTICS.CLINICAL_INSIGHT_SUMMARIES")
    trends         = query("SELECT * FROM ANALYTICS.CARE_CONTINUITY_TRENDS")
except Exception as e:
    st.error(f"Connection error: {e}")
    st.stop()

# ── summary metrics ───────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
total_patients   = len(patients)
critical_gaps    = len(care_gaps[care_gaps["SEVERITY"] == "CRITICAL"])
high_gaps        = len(care_gaps[care_gaps["SEVERITY"] == "HIGH"])
unaware          = len(care_gaps[care_gaps["US_PROVIDER_AWARE"] == False])
cross_border_enc = len(encounters[encounters["IS_CROSS_BORDER"] == True])

for col, val, lbl in zip(
    [c1, c2, c3, c4, c5],
    [total_patients, critical_gaps, high_gaps, unaware, cross_border_enc],
    ["Patients", "Critical Gaps", "High Gaps", "Provider Unaware", "Cross-Border Enc."]
):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{val}</div>
        <div class="metric-lbl">{lbl}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚠ Care Gaps", "🧬 Patient Profiles", "🏥 Encounters", "🔬 Labs", "📊 Trends"
])

SEV_COLOR = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "MEDIUM": "#ca8a04", "LOW": "#16a34a"}

# ── tab 1: care gaps ──────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Active Care Gaps")
    st.caption("Cortex-analyzed gaps from cross-border record fragmentation, ranked by severity.")

    filter_sev = st.multiselect(
        "Filter by severity",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH"],
        key="gap_sev"
    )
    gap_df = care_gaps[care_gaps["SEVERITY"].isin(filter_sev)] if filter_sev else care_gaps

    for _, row in gap_df.iterrows():
        color = SEV_COLOR.get(row["SEVERITY"], "#4a6080")
        st.markdown(f"""
        <div class="finding-card" style="border-left: 3px solid {color};">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span class="tag" style="background:{color}22; color:{color}; border:1px solid {color}44;">
                    {row['SEVERITY']}
                </span>
                <span class="tag" style="background:#1e2d42; color:#7ba3cc;">
                    {row['GAP_TYPE']}
                </span>
                <span style="color:#f0f6ff; font-size:13px; font-weight:500;">{row['FULL_NAME']}</span>
                <span style="color:#4a6080; font-size:11px; margin-left:auto;">
                    {row['COUNTRY_OF_ORIGIN']} → USA · {row['IDENTIFIED_DATE']}
                </span>
            </div>
            <div style="color:#7ba3cc; font-size:12px; line-height:1.65; margin-bottom:10px;">
                {row['DESCRIPTION']}
            </div>
            <div style="background:#060c16; border-radius:6px; padding:10px; border:1px solid #1e2d42;">
                <div style="font-size:9px; color:#34d399; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">
                    Cortex Analysis
                </div>
                <div style="color:#7ba3cc; font-size:12px; line-height:1.65;">
                    {str(row.get('GAP_ANALYSIS', 'Pending analysis')).replace('<', '&lt;').replace('>', '&gt;')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── tab 2: patient profiles ───────────────────────────────────────────────────
with tab2:
    st.markdown("### Patient Care Continuity Profiles")
    st.caption("Cortex-synthesized profile per patient across all available data.")

    for _, row in profiles.iterrows():
        gaps_hi = int(row.get("HIGH_SEVERITY_GAPS", 0) or 0)
        color   = "#dc2626" if gaps_hi >= 2 else "#ea580c" if gaps_hi == 1 else "#16a34a"
        st.markdown(f"""
        <div class="finding-card" style="border-left: 3px solid {color};">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                <div>
                    <div style="font-size:15px; font-weight:600; color:#f0f6ff;">{row['FULL_NAME']}</div>
                    <div style="font-size:11px; color:#4a6080; margin-top:2px;">
                        {row['COUNTRY_OF_ORIGIN']} · {row['PRIMARY_LANGUAGE']} · {row['INSURANCE_STATUS']} · Arrived {row['IMMIGRATION_YEAR']}
                    </div>
                </div>
                <div style="margin-left:auto; display:flex; gap:16px; text-align:center;">
                    <div><div style="font-size:18px; font-weight:700; color:#f0f6ff;">{int(row.get('TOTAL_ENCOUNTERS',0) or 0)}</div>
                         <div style="font-size:9px; color:#4a6080; text-transform:uppercase; letter-spacing:1px;">Encounters</div></div>
                    <div><div style="font-size:18px; font-weight:700; color:#fdba74;">{int(row.get('TOTAL_GAPS',0) or 0)}</div>
                         <div style="font-size:9px; color:#4a6080; text-transform:uppercase; letter-spacing:1px;">Gaps</div></div>
                    <div><div style="font-size:18px; font-weight:700; color:{color};">{gaps_hi}</div>
                         <div style="font-size:9px; color:#4a6080; text-transform:uppercase; letter-spacing:1px;">High Sev.</div></div>
                </div>
            </div>
            <div style="background:#060c16; border-radius:6px; padding:10px; border:1px solid #1e2d42;">
                <div style="font-size:9px; color:#60a5fa; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">
                    Cortex Profile
                </div>
                <div style="color:#7ba3cc; font-size:12px; line-height:1.75;">
                    {str(row.get('PATIENT_PROFILE', 'Pending')).replace('<', '&lt;').replace('>', '&gt;')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── tab 3: encounters ─────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Clinical Encounters + Risk Analysis")
    st.caption("Encounter-level risk signals from Cortex, highlighting cross-border care gaps.")

    show_cb = st.checkbox("Cross-border encounters only", value=False)
    enc_df  = risk_analysis[risk_analysis["IS_CROSS_BORDER"] == True] if show_cb else risk_analysis

    for _, row in enc_df.iterrows():
        cb_color = "#2563eb" if row.get("IS_CROSS_BORDER") else "#1e2d42"
        cb_tag = "<span class='tag' style='background:rgba(37,99,235,0.15); color:#60a5fa; border:1px solid rgba(37,99,235,0.3);'>Cross-Border</span>" if row.get("IS_CROSS_BORDER") else ""
        risk = str(row.get("RISK_ANALYSIS", "Pending")).replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f'''<div class="finding-card" style="border-left: 3px solid {cb_color};"><div style="display:flex; align-items:center; gap:10px; margin-bottom:8px; flex-wrap:wrap;"><span style="color:#f0f6ff; font-size:13px; font-weight:500;">{row["FULL_NAME"]}</span><span class="tag" style="background:#1e2d42; color:#7ba3cc;">{row["ENCOUNTER_TYPE"]}</span>{cb_tag}<span style="color:#4a6080; font-size:11px; margin-left:auto;">{row["FACILITY"]} &middot; {row["ENCOUNTER_DATE"]}</span></div><div style="color:#7ba3cc; font-size:12px; line-height:1.6; margin-bottom:10px;"><strong style="color:#94a3b8;">Assessment:</strong> {row["ASSESSMENT"]}</div><div style="background:#060c16; border-radius:6px; padding:10px; border:1px solid #1e2d42;"><div style="font-size:9px; color:#a78bfa; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px;">Cortex Risk Analysis</div><div style="color:#7ba3cc; font-size:12px; line-height:1.65;">{risk}</div></div></div>''', unsafe_allow_html=True)

# ── tab 4: labs ───────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Lab Results + Clinical Insights")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("#### Results by Patient")
        flag_colors = {"H": "#fca5a5", "L": "#93c5fd", "N": "#86efac"}
        for _, row in labs.iterrows():
            fc = flag_colors.get(str(row.get("FLAG", "N")).strip(), "#94a3b8")
            st.markdown(f"""
            <div class="finding-card" style="padding:10px 14px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="color:#f0f6ff; font-size:12px; font-weight:500; width:130px;">{row['FULL_NAME']}</span>
                    <span style="color:#94a3b8; font-size:12px; flex:1;">{row['TEST_NAME']}</span>
                    <span style="color:#7ba3cc; font-size:11px;">{row.get('LOINC_CODE','—')}</span>
                    <span style="font-size:13px; font-weight:600; color:{fc};">{row['RESULT_VALUE']} {row.get('UNIT','')}</span>
                    <span class="tag" style="background:{fc}22; color:{fc}; border:1px solid {fc}44;">{row.get('FLAG','N')}</span>
                    <span style="color:#4a6080; font-size:10px;">{row['COUNTRY']} · {row['COLLECTION_DATE']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown("#### Cortex Clinical Insights")
        for _, row in insights.iterrows():
            st.markdown(f"""
            <div class="finding-card">
                <div style="font-size:13px; font-weight:600; color:#f0f6ff; margin-bottom:6px;">{row['FULL_NAME']}</div>
                <div style="font-size:10px; color:#4a6080; margin-bottom:8px;">
                    {int(row.get('ABNORMAL_HIGH',0) or 0)} elevated · {int(row.get('ABNORMAL_LOW',0) or 0)} low
                </div>
                <div style="font-size:12px; color:#7ba3cc; line-height:1.65;">
                    {str(row.get('CLINICAL_INSIGHT','Pending')).replace('<', '&lt;').replace('>', '&gt;')}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── tab 5: trends ─────────────────────────────────────────────────────────────
with tab5:
    st.markdown("### Population-Level Care Continuity Trends")
    st.caption("Cortex-generated systemic risk signals by country of origin and gap type.")

    col_x, col_y = st.columns([1, 1])

    with col_x:
        st.markdown("#### Gap distribution by country")
        country_summary = care_gaps.groupby("COUNTRY_OF_ORIGIN").agg(
            Total=("GAP_ID", "count"),
            Critical=("SEVERITY", lambda x: (x == "CRITICAL").sum()),
            High=("SEVERITY", lambda x: (x == "HIGH").sum()),
        ).reset_index().sort_values("Total", ascending=False)
        st.dataframe(country_summary, use_container_width=True, hide_index=True)

    with col_y:
        st.markdown("#### Gap type breakdown")
        type_summary = care_gaps.groupby("GAP_TYPE").agg(
            Count=("GAP_ID", "count"),
            Unaware=("US_PROVIDER_AWARE", lambda x: (~x).sum())
        ).reset_index().sort_values("Count", ascending=False)
        st.dataframe(type_summary, use_container_width=True, hide_index=True)

    st.markdown("#### Cortex systemic risk signals")
    for _, row in trends.iterrows():
        st.markdown(f"""
        <div class="finding-card">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span class="tag" style="background:#1e2d42; color:#7ba3cc;">{row['ORIGIN_COUNTRY']}</span>
                <span class="tag" style="background:#1e2d42; color:#94a3b8;">{row['GAP_TYPE']}</span>
                <span style="color:#fdba74; font-size:11px;">{row['GAP_COUNT']} gaps · {row.get('PCT_PROVIDER_UNAWARE',0)}% provider unaware</span>
            </div>
            <div style="font-size:12px; color:#7ba3cc; line-height:1.65;">
                {str(row.get('TREND_INSIGHT','Pending')).replace('<', '&lt;').replace('>', '&gt;')}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="margin-top:40px; padding-top:16px; border-top:1px solid #1e2d42; text-align:center; font-size:10px; color:#2d4a6a; letter-spacing:1.5px;">
    ASTER HEALTH · PUBLIC BENEFIT CORP · DEMO — NOT FOR PHI
</div>
""", unsafe_allow_html=True)
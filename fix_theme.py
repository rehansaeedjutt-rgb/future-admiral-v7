"""Fix light theme issues — button text, inputs, radios, selectbox"""
from pathlib import Path

p = Path("app.py")
c = p.read_text(encoding="utf-8")

# 1. Add aggressive CSS overrides AFTER the main style block
old_css_end = '''.stMarkdown, .stText, p, span, label {{ color:{V['text2']}; }}
h1, h2, h3, h4, h5, h6 {{ color:{V['text']}; }}
</style>
"""'''

new_css_end = '''.stMarkdown, .stText, p, span, label {{ color:{V['text2']}; }}
h1, h2, h3, h4, h5, h6 {{ color:{V['text']}; }}

/* ============ AGGRESSIVE OVERRIDES (fix light mode) ============ */

/* Buttons — force white text always */
.stButton > button,
.stButton > button[kind="primary"],
.stButton > button[kind="secondary"],
button[kind="primary"],
button[kind="secondary"] {{
    color: #ffffff !important;
    font-weight: 700 !important;
}}
.stButton > button p,
.stButton > button span,
.stButton > button div {{
    color: #ffffff !important;
}}

/* Download button */
.stDownloadButton > button {{
    background: {V['bg2']} !important;
    color: {V['text']} !important;
    border: 1px solid {V['border2']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
.stDownloadButton > button:hover {{
    background: {V['hover']} !important;
    border-color: {V['accent']} !important;
}}

/* Text inputs */
.stTextInput input,
.stTextInput > div > div > input {{
    background: {V['bg2']} !important;
    color: {V['text']} !important;
    border: 1px solid {V['border2']} !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
}}
.stTextInput input:focus {{
    border-color: {V['accent']} !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] > div {{
    background: {V['bg2']} !important;
    color: {V['text']} !important;
    border: 1px solid {V['border2']} !important;
    border-radius: 8px !important;
}}
.stSelectbox div[data-baseweb="select"] * {{
    color: {V['text']} !important;
    font-weight: 600 !important;
}}
[data-baseweb="popover"] {{
    background: {V['bg2']} !important;
    border: 1px solid {V['border']} !important;
}}
[data-baseweb="menu"] li {{
    background: {V['bg2']} !important;
    color: {V['text']} !important;
}}
[data-baseweb="menu"] li:hover {{
    background: {V['hover']} !important;
}}

/* Radio buttons — clean pill style */
.stRadio > div {{
    display: flex; flex-direction: row; gap: 6px;
    background: {V['bg']}; padding: 4px;
    border: 1px solid {V['border']}; border-radius: 10px;
}}
.stRadio > div > label {{
    padding: 8px 16px !important;
    border-radius: 7px !important;
    background: transparent !important;
    color: {V['muted']} !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    margin: 0 !important;
}}
.stRadio > div > label:hover {{
    background: {V['hover']} !important;
    color: {V['text']} !important;
}}
.stRadio > div > label[data-checked="true"] {{
    background: {V['accent']} !important;
    color: #ffffff !important;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3) !important;
}}
.stRadio > div > label > div:first-child {{
    display: none !important;
}}
.stRadio > div > label > div {{
    color: inherit !important;
}}

/* Checkbox */
.stCheckbox label span,
.stCheckbox label p {{
    color: {V['text2']} !important;
    font-weight: 500 !important;
}}
.stCheckbox input:checked + div {{
    background: {V['accent']} !important;
    border-color: {V['accent']} !important;
}}

/* Streamlit status widget (analysis progress) */
[data-testid="stStatusWidget"] {{
    background: {V['bg2']} !important;
    border: 1px solid {V['border']} !important;
    border-radius: 10px !important;
}}
[data-testid="stStatusWidget"] * {{
    color: {V['text2']} !important;
}}

/* Alert boxes (success/info/warning/error) */
.stAlert {{
    border-radius: 8px !important;
    border: 1px solid {V['border']} !important;
}}
.stAlert * {{
    font-weight: 500 !important;
}}

/* Expander */
.streamlit-expanderHeader,
[data-testid="stExpander"] details summary {{
    background: {V['bg2']} !important;
    color: {V['text']} !important;
    border: 1px solid {V['border']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}}
[data-testid="stExpander"] details summary:hover {{
    background: {V['hover']} !important;
}}

/* Metric widget */
[data-testid="stMetric"] {{
    background: {V['bg2']} !important;
    border: 1px solid {V['border']} !important;
    border-radius: 10px !important;
    padding: 16px !important;
}}
[data-testid="stMetricValue"] {{
    color: {V['text']} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}
[data-testid="stMetricLabel"] {{
    color: {V['muted']} !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    font-size: 10px !important;
}}

/* Dataframe */
.stDataFrame {{
    border: 1px solid {V['border']} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}}

/* JSON viewer */
.stJson {{
    background: {V['bg2']} !important;
    border: 1px solid {V['border']} !important;
    border-radius: 8px !important;
}}

/* Divider */
hr {{
    border-color: {V['border']} !important;
}}

/* Sidebar specific */
section[data-testid="stSidebar"] label {{
    color: {V['muted']} !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
}}

/* Fix for selectbox dropdown arrow */
.stSelectbox svg {{
    fill: {V['text2']} !important;
}}

</style>
"""'''

if old_css_end in c:
    c = c.replace(old_css_end, new_css_end)
    p.write_text(c, encoding="utf-8")
    print("[OK] CSS overrides added")
else:
    print("[WARN] pattern not found — trying alternative")
    # Try simpler replace
    c = c.replace('.stMarkdown, .stText, p, span, label {{ color:{V[\'text2\']}; }}',
                  '.stMarkdown, .stText, p, span, label {{ color:{V[\'text2\']}; }}')
    p.write_text(c, encoding="utf-8")

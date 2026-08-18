# frontend/theme.py
#
# Shared visual identity for the whole app — a navy-and-gold banking
# portal look, deliberately not a generic SaaS dashboard style. This
# module is imported once from app.py (inject_theme() is called before
# any page renders) and its header/account-bar/footer components are
# reused across the login page and all four dashboards, so the look
# stays consistent without duplicating CSS in every file.

import streamlit as st

NAVY = "#0B2545"
NAVY_LIGHT = "#13315C"
GOLD = "#C9A227"
GOLD_LIGHT = "#E0B93A"
BG = "#F4F6F9"
CARD = "#FFFFFF"
TEXT = "#1A1A2E"
TEXT_MUTED = "#5B6472"
BORDER = "#DDE3EC"
SUCCESS = "#1B7A43"
ERROR = "#B3261E"

BANK_NAME = "ElectroBank"
TAGLINE = "Net Banking Portal"


def inject_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', 'Segoe UI', sans-serif;
        color: {TEXT};
    }}

    h1, h2, h3, h4 {{
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        color: {NAVY} !important;
        letter-spacing: -0.01em;
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: {BG};
    }}

    /* Hide Streamlit's default chrome so our own header reads as the top of the page */
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* ---------------- Sidebar (navy, gold accents) ---------------- */
    [data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    [data-testid="stSidebar"] * {{
        color: #E8ECF3 !important;
    }}
    [data-testid="stSidebar"] button {{
        background-color: {GOLD} !important;
        color: {NAVY} !important;
        font-weight: 600 !important;
        border: none !important;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: {GOLD_LIGHT} !important;
    }}

    /* ---------------- Buttons ---------------- */
    .stButton button, .stFormSubmitButton button {{
        background-color: {NAVY};
        color: #FFFFFF;
        border: 1px solid {NAVY};
        border-radius: 4px;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
        transition: background-color 0.15s ease;
    }}
    .stButton button:hover, .stFormSubmitButton button:hover {{
        background-color: {NAVY_LIGHT};
        border-color: {NAVY_LIGHT};
        color: #FFFFFF;
    }}
    .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {{
        background-color: {GOLD};
        border-color: {GOLD};
        color: {NAVY};
    }}
    .stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {{
        background-color: {GOLD_LIGHT};
        border-color: {GOLD_LIGHT};
    }}

    /* ---------------- Tabs — underline style with gold active indicator ---------------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        border-bottom: 1px solid {BORDER};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 44px;
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        color: {TEXT_MUTED};
        background-color: transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: {NAVY} !important;
        font-weight: 600;
        border-bottom: 3px solid {GOLD} !important;
    }}

    /* ---------------- Forms / panels — card look with gold left accent ---------------- */
    [data-testid="stForm"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-left: 4px solid {GOLD};
        border-radius: 6px;
        padding: 1.5rem;
    }}

    /* ---------------- Inputs ---------------- */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {{
        border-radius: 4px !important;
        border: 1px solid {BORDER} !important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTextArea textarea:focus {{
        border-color: {GOLD} !important;
        box-shadow: 0 0 0 1px {GOLD} !important;
    }}

    /* ---------------- Metrics — card look ---------------- */
    [data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-top: 3px solid {NAVY};
        border-radius: 6px;
        padding: 1rem;
    }}
    [data-testid="stMetricValue"] {{
        font-family: 'Inter', sans-serif;
        font-variant-numeric: tabular-nums;
        color: {NAVY};
    }}

    /* ---------------- Dataframes ---------------- */
    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 6px;
    }}

    /* ---------------- Alerts ---------------- */
    [data-testid="stAlert"] {{
        border-radius: 4px;
    }}

    /* ---------------- Our custom components ---------------- */
    .bank-header {{
        background-color: {NAVY};
        margin: -1rem -1rem 1.5rem -1rem;
        padding: 0;
        border-bottom: 3px solid {GOLD};
    }}
    .bank-header-security-strip {{
        background-color: {NAVY_LIGHT};
        color: #C7D2E3;
        font-size: 0.72rem;
        padding: 0.3rem 1.5rem;
        text-align: right;
        letter-spacing: 0.02em;
    }}
    .bank-header-main {{
        padding: 0.9rem 1.5rem;
        display: flex;
        align-items: baseline;
        gap: 0.6rem;
    }}
    .bank-header-name {{
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 1.5rem;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }}
    .bank-header-tagline {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: {GOLD_LIGHT};
        font-weight: 500;
    }}

    .account-bar {{
        background-color: {CARD};
        border: 1px solid {BORDER};
        border-left: 4px solid {NAVY};
        border-radius: 6px;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    .account-bar-welcome {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: {NAVY};
        font-size: 1rem;
    }}
    .account-bar-meta {{
        font-size: 0.82rem;
        color: {TEXT_MUTED};
    }}
    .role-badge {{
        display: inline-block;
        background-color: {NAVY};
        color: {GOLD_LIGHT};
        font-family: 'Poppins', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.2rem 0.6rem;
        border-radius: 3px;
        margin-left: 0.5rem;
    }}

    .bank-footer {{
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid {BORDER};
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        text-align: center;
        line-height: 1.6;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_bank_header():
    """Top navy header with a security strip, shown on every page (login + all dashboards)."""
    st.markdown(f"""
    <div class="bank-header">
        <div class="bank-header-security-strip">🔒 256-bit Encrypted Session &nbsp;·&nbsp; Verified Banking Portal</div>
        <div class="bank-header-main">
            <span class="bank-header-name">🏦 {BANK_NAME}</span>
            <span class="bank-header-tagline">{TAGLINE}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_account_bar(user, role_label):
    """'Welcome back' bar shown at the top of every dashboard, like a real net-banking portal."""
    st.markdown(f"""
    <div class="account-bar">
        <div class="account-bar-welcome">
            Welcome back, {user['full_name']}
            <span class="role-badge">{role_label}</span>
        </div>
        <div class="account-bar-meta">Branch: {user['branch']} &nbsp;·&nbsp; User ID: {user['user_id']}</div>
    </div>
    """, unsafe_allow_html=True)


def render_bank_footer():
    st.markdown(f"""
    <div class="bank-footer">
        {BANK_NAME} is a demo banking portal built as a portfolio project — not affiliated with,
        and not a real product of, any bank.<br>
        Never enter real banking credentials, PINs, or personal identification numbers into this application.
    </div>
    """, unsafe_allow_html=True)
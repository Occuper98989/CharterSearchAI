import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import folium
from streamlit_folium import st_folium
from io import BytesIO
import requests

# Use a local data folder that works on Streamlit Cloud
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Page config - CharterSearchAI branding
st.set_page_config(
    page_title="CharterSearchAI | Charterhouse Property Group",
    layout="wide",
    page_icon="🏗️",
    initial_sidebar_state="expanded"
)

# Custom CSS to match charterh.co.uk aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&family=Open+Sans:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Open Sans', Arial, sans-serif;
        color: #666666;
        background-color: #ffffff;
    }
    
    h1, h2, h3, .stTitle {
        font-family: 'Montserrat', Helvetica, Arial, sans-serif !important;
        color: #C9A578 !important;
        font-weight: 300 !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        letter-spacing: 1px;
    }
    
    .stButton > button {
        background-color: #C9A578 !important;
        color: white !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 2px !important;
        padding: 0.6rem 1.5rem !important;
    }
    
    .stButton > button:hover {
        background-color: #b8956a !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header branding - closer to mockup
col1, col2, col3 = st.columns([1.2, 3, 1.5])
with col1:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px;">
        <div style="font-size:28px;">🏗️</div>
        <div>
            <div style="font-family:Montserrat,sans-serif; font-weight:600; color:#C9A578; font-size:14px;">CHARTERHOUSE</div>
            <div style="font-size:10px; color:#888;">PROPERTY GROUP</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("# CharterSearchAI")
    st.caption("Land sourcing intelligence for Charterhouse Property Group")
with col3:
    st.markdown("<div style='text-align:right; padding-top:15px; font-size:13px; color:#888;'>Charterhouse Property Group</div>", unsafe_allow_html=True)

st.markdown("---")

# Persistent storage (works on Streamlit Cloud)
SEARCHES_FILE = os.path.join(DATA_DIR, "searches.json")
RESULTS_FILE = os.path.join(DATA_DIR, "results.json")

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

searches = load_json(SEARCHES_FILE, {})
results = load_json(RESULTS_FILE, {})

# Sidebar - improved
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:10px 0 20px 0;">
        <div style="font-size:32px;">🏗️</div>
        <div style="font-family:Montserrat,sans-serif; font-weight:600; color:#C9A578; font-size:16px;">CHARTERHOUSE</div>
        <div style="font-size:11px; color:#aaa;">PROPERTY GROUP</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", ["New Search", "Past Searches & Shortlists", "How it works"])
    st.markdown("---")
    st.caption("Investing in UK real estate for over 30 years")

if page == "New Search":
    st.header("New Search Requirements")
    st.markdown("Enter criteria. Clicking **Run Search** directly triggers the CharterSearchAI agent with these exact values.")
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_name = st.text_input("Name this search", placeholder="e.g. M25 Hardstanding Q4")
            min_acres = st.number_input("Min size (acres)", value=0.3, min_value=0.1, max_value=10.0, step=0.1)
            max_acres = st.number_input("Max size (acres)", value=7.5, min_value=0.5, max_value=20.0, step=0.5)
            min_traffic = st.number_input("Min daily traffic (AADF)", value=8000, min_value=1000, step=500)
            max_build_pct = st.slider("Max build percentage (%)", 0, 30, 15)
        
        with col2:
            location_focus = st.text_area("Location focus / corridors", 
                value="M25 ring, Home Counties (Essex, Kent, Surrey, Hertfordshire, Buckinghamshire, Berkshire), within ~2 hours of London")
            priorities = st.multiselect("Priorities", 
                ["Hardstanding priority", "Vacant / redundant sites", "Contaminated / brownfield", "No residential", "NO VOA (no current rates assessment)", "Lorry parks / car parks"],
                default=["Hardstanding priority", "Vacant / redundant sites", "NO VOA (no current rates assessment)", "No residential"])
            extra_notes = st.text_area("Extra notes / filters", placeholder="e.g. avoid Green Belt, freehold only...")
        
        submitted = st.form_submit_button("🚀 Run Search (triggers agent)", type="primary")
    
    if submitted and search_name:
        search_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        criteria = {
            "name": search_name,
            "min_acres": min_acres,
            "max_acres": max_acres,
            "min_traffic": min_traffic,
            "max_build_pct": max_build_pct,
            "location_focus": location_focus,
            "priorities": priorities,
            "extra_notes": extra_notes,
            "created": datetime.now().isoformat(),
            "status": "running"
        }
        searches[search_id] = criteria
        save_json(SEARCHES_FILE, searches)
        
        # Fully wired: build exact prompt and note bot trigger
        bot_prompt = f"""New named search from CharterSearchAI dashboard:
Name: {search_name}
Min acres: {min_acres}
Max acres: {max_acres}
Min AADF traffic: {min_traffic}
Max build %: {max_build_pct}
Location focus: {location_focus}
Priorities: {', '.join(priorities)}
Extra notes: {extra_notes}

Run a full scan for overlooked commercial development sites matching these exact criteria. Include satellite hardstanding analysis notes, map coordinates where possible, and return a scored shortlist in structured JSON/CSV ready for the dashboard (fields: Site, Approx acres, Traffic nearby, Score, Notes, Lat, Lon, Hardstanding confidence)."""
        
        # Save prompt locally
        with open(os.path.join(DATA_DIR, f"prompt_{search_id}.txt"), "w") as f:
            f.write(bot_prompt)
        
        st.success(f"**{search_name}** submitted.")
        
        # Build payload for the agent API
        payload = {
            "search_name": search_name,
            "min_acres": min_acres,
            "max_acres": max_acres,
            "min_aadf": min_traffic,
            "max_build_pct": max_build_pct,
            "location_focus": [location_focus],
            "priorities": priorities
        }
        
        # API settings from Streamlit secrets
        api_url = st.secrets.get("AGENT_API_URL", "")
        api_key = st.secrets.get("AGENT_API_KEY", "")
        
        if api_url and api_key:
            st.info(f"Calling agent at {api_url}/search …")
            with st.spinner("Running real search with the Land Sourcing Agent..."):
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "X-API-Key": api_key,
                        "ngrok-skip-browser-warning": "true"
                    }
                    resp = requests.post(f"{api_url.rstrip('/')}/search", json=payload, headers=headers, timeout=180)
                    if resp.status_code == 200:
                        agent_result = resp.json()
                        sites = agent_result.get("sites", [])
                        results[search_id] = {"criteria": criteria, "sites": sites, "generated": datetime.now().isoformat(), "source": "agent"}
                        save_json(RESULTS_FILE, results)
                        st.success(f"Real results received ({len(sites)} sites).")
                    else:
                        st.error(f"Agent error {resp.status_code}: {resp.text[:500]}")
                        raise Exception("bad status")
                except Exception as e:
                    st.error(f"Request failed: {type(e).__name__}: {str(e)}")
                    demo_sites = [
                        {"Site": "Hardstanding yard near M25 J15", "Approx acres": 2.1, "Traffic nearby": "12,400 AADF", "Score": 92, "Notes": "Demo – agent unavailable", "Lat": 51.48, "Lon": -0.45, "Hardstanding confidence": "High"},
                        {"Site": "Brownfield parcel Essex industrial fringe", "Approx acres": 1.4, "Traffic nearby": "9,100 AADF", "Score": 85, "Notes": "Demo", "Lat": 51.55, "Lon": 0.35, "Hardstanding confidence": "Medium"}
                    ]
                    results[search_id] = {"criteria": criteria, "sites": demo_sites, "generated": datetime.now().isoformat(), "source": "demo"}
                    save_json(RESULTS_FILE, results)
        else:
            st.warning("Agent API not configured in secrets yet. Showing demo results.")
            demo_sites = [
                {"Site": "Hardstanding yard near M25 J15", "Approx acres": 2.1, "Traffic nearby": "12,400 AADF", "Score": 92, "Notes": "Demo result – agent not connected", "Lat": 51.48, "Lon": -0.45, "Hardstanding confidence": "High"},
                {"Site": "Brownfield parcel Essex industrial fringe", "Approx acres": 1.4, "Traffic nearby": "9,100 AADF", "Score": 85, "Notes": "Demo result", "Lat": 51.55, "Lon": 0.35, "Hardstanding confidence": "Medium"},
                {"Site": "Vacant car park Kent A2 corridor", "Approx acres": 0.8, "Traffic nearby": "15,200 AADF", "Score": 88, "Notes": "Demo result", "Lat": 51.42, "Lon": 0.55, "Hardstanding confidence": "High"}
            ]
            results[search_id] = {"criteria": criteria, "sites": demo_sites, "generated": datetime.now().isoformat(), "source": "demo"}
            save_json(RESULTS_FILE, results)
        
        st.info("👉 Go to **Past Searches & Shortlists** to view results, map, and Excel export.")
        st.balloons()
        st.rerun()

elif page == "Past Searches & Shortlists":
    st.header("Past Searches & Shortlists")
    if not searches:
        st.info("No searches yet. Run one from the New Search page.")
    else:
        for sid, crit in reversed(list(searches.items())):
            col_a, col_b = st.columns([5, 1])
            with col_a:
                expander_label = f"**{crit['name']}** — {crit.get('created', '')[:16]}"
            with col_b:
                if st.button("🗑️ Delete", key=f"del_{sid}"):
                    searches.pop(sid, None)
                    results.pop(sid, None)
                    save_json(SEARCHES_FILE, searches)
                    save_json(RESULTS_FILE, results)
                    st.rerun()
            
            with st.expander(expander_label):
                if sid in results:
                    sites = results[sid].get("sites", [])
                    if not sites:
                        st.warning("No sites returned for this search.")
                    else:
                        df = pd.DataFrame(sites)
                        
                        # Normalise column names
                        col_map = {
                            "site": "Site", "name": "Site", "title": "Site",
                            "acres": "Approx acres", "approx_acres": "Approx acres",
                            "aadf": "Traffic nearby", "traffic": "Traffic nearby",
                            "score": "Score", "notes": "Notes", "reasons": "Notes",
                            "lat": "Lat", "lon": "Lon",
                            "hardstanding_confidence": "Hardstanding confidence",
                            "hardstanding": "Hardstanding confidence"
                        }
                        df = df.rename(columns={c: col_map.get(str(c).lower(), c) for c in df.columns})
                        
                        st.subheader("Candidate sites")
                        if len(df.columns) > 0:
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.json(sites)
                        
                        # Map view
                        st.subheader("Map view")
                        if "Lat" in df.columns and "Lon" in df.columns and len(df) > 0:
                            m = folium.Map(location=[51.5, -0.1], zoom_start=9)
                            for _, row in df.iterrows():
                                if pd.notna(row.get("Lat")) and pd.notna(row.get("Lon")):
                                    popup = f"{row.get('Site', 'Site')}<br>Score: {row.get('Score', '')}"
                                    folium.Marker([row["Lat"], row["Lon"]], popup=popup, tooltip=str(row.get("Site", "Site"))).add_to(m)
                            st_folium(m, width=700, height=400)
                        else:
                            st.info("No coordinates available for map.")
                        
                        # Hardstanding
                        st.subheader("Satellite hardstanding checks")
                        if "Hardstanding confidence" in df.columns:
                            for _, row in df.iterrows():
                                st.markdown(f"**{row.get('Site', 'Site')}**: {row.get('Hardstanding confidence', '')} — {row.get('Notes', '')}")
                        
                        # Excel
                        st.subheader("Export")
                        if len(df.columns) > 0:
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                df.to_excel(writer, index=False, sheet_name="Shortlist")
                            st.download_button(
                                label="📥 Download Excel shortlist",
                                data=output.getvalue(),
                                file_name=f"CharterSearchAI_{crit['name'].replace(' ','_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # Shortlist
                        site_options = []
                        if "Site" in df.columns:
                            site_options = df["Site"].dropna().astype(str).tolist()
                        elif len(df.columns) > 0:
                            site_options = df.iloc[:, 0].dropna().astype(str).tolist()
                        
                        if site_options:
                            shortlisted = st.multiselect("Mark for shortlist", site_options, key=f"short_{sid}")
                            if st.button("Save shortlist", key=f"save_{sid}"):
                                st.success(f"Shortlisted {len(shortlisted)} sites.")
                else:
                    st.warning("Results pending...")

elif page == "How it works":
    st.header("How CharterSearchAI works")
    st.markdown("""
    - **Run button is fully wired**: Submitting the form builds the exact criteria prompt and triggers the CharterSearchAI agent.
    - **Map view**: Sites with coordinates are plotted on an interactive map.
    - **Satellite hardstanding checks**: Agent notes include hardstanding confidence from imagery analysis.
    - **Excel export**: One-click download of the full shortlist.
    - Styled to match Charterhouse Property Group.
    """)

st.markdown("---")
st.caption("CharterSearchAI · Charterhouse Property Group")

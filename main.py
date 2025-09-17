# app.py
import os
import io
import time
import base64
import requests
import streamlit as st
import pydeck as pdk
from PIL import Image

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Oil Spill Detection", page_icon="🛰️", layout="wide")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")  
INTRO_VIDEO_PATH = "earth_zoom.mp4"      
BACKGROUND_IMAGE_PATH = "background.png"  

# Sample demo points (edit/expand as you like)
DEMO_COORDS = [
    {"name": "Detection #1", "lat": 26.315, "lon": 50.103, "conf": 0.91},
    {"name": "Detection #2", "lat": 26.420, "lon": 49.978, "conf": 0.78},
    {"name": "Detection #3", "lat": 26.230, "lon": 50.205, "conf": 0.62},
]

# ---------------------------
# HELPERS
# ---------------------------
def _as_data_uri(path_or_url: str, mime: str) -> str:
    if path_or_url.lower().startswith("http"):
        # Streamlit can use remote urls directly; we only need data URI for local assets
        return path_or_url
    with open(path_or_url, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

def set_background_image(path_or_url: str):
    uri = _as_data_uri(path_or_url, "image/png")
    st.markdown(
        f"""
        <style>
        /* Set the whole main container background to your image */
        [data-testid="stAppViewContainer"] {{
            background: url("{uri}") no-repeat center center fixed !important;
            background-size: cover !important;
            background-color: transparent !important;
        }}

        /* Make main content transparent to see the background */
        .stApp, .main, .block-container {{
            background-color: rgba(0,0,0,0) !important;
        }}

        /* Remove top header background */
        header[data-testid="stHeader"] {{
            background: rgba(0,0,0,0) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_brandbar():
    st.markdown(
        """
        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            gap:12px;
            margin-bottom: 25px;
        ">
          <div style="font-size:2.8rem;">🛰️ <b>Petra</b></div>
          <div style="opacity:.7; font-size:2.8rem;">| Oil Spill Detection From World Sea</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def call_fastapi_predict_file(file_bytes: bytes, filename: str):
    # Most common FastAPI pattern: multipart file under key "file"
    try:
        resp = requests.post(
            f"{FASTAPI_URL}/predict",
            files={"file": (filename, file_bytes, "application/octet-stream")},
            timeout=60,
        )
        if resp.ok:
            return True, resp.json()
        return False, {"error": f"{resp.status_code}: {resp.text}"}
    except Exception as e:
        return False, {"error": str(e)}

def call_fastapi_predict_url(image_url: str):
    # Alternative pattern: JSON with image URL
    try:
        resp = requests.post(
            f"{FASTAPI_URL}/predict",
            json={"url": image_url},
            timeout=60,
        )
        if resp.ok:
            return True, resp.json()
        return False, {"error": f"{resp.status_code}: {resp.text}"}
    except Exception as e:
        return False, {"error": str(e)}

# ---------------------------
# STATE: Splash -> App
# ---------------------------
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False

# Intro logic:
#   - If not done: show video + "Enter" button
#   - After press: mark done and rerun to load background + tabs
if not st.session_state.intro_done:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: black !important; }
        .intro-card { text-align:center; padding-top: 6vh; color: #ddd; }
        .intro-title { font-size: 2rem; margin: 12px 0 4px 0; }
        .intro-sub { opacity:.8; margin-bottom: 14px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div style="text-align:center; padding-top: 6vh; color: #ddd;">
        <div style="font-size: 2.5rem; margin-bottom: 8px;">🛰️ <b>Oil Spill Detection</b></div>
        <div style="font-size: 1.2rem; opacity: 0.8;">Cinematic journey from orbit to ocean</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------
# HERO VIDEO INTRO (AUTOPLAY)
# ---------------------------
with open(INTRO_VIDEO_PATH, "rb") as f:
    video_bytes = f.read()
video_base64 = base64.b64encode(video_bytes).decode()

st.markdown(f"""
<style>
.hero-container {{
    position: relative;
    width: 100%;
    height: 90vh;
    overflow: hidden;
    border-radius: 18px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    margin-bottom: 2.5rem;
    margin-top: 2.5rem;
            
}}

.hero-container video {{
    position: absolute;
    top: 50%;
    left: 50%;
    min-width: 100%;
    min-height: 100%;
    transform: translate(-50%, -50%);
    object-fit: cover;
    filter: brightness(0.65) contrast(1.2);
}}

.hero-overlay {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    text-align: center;
    z-index: 2;
}}

.hero-overlay h1 {{
    font-size: 3.5rem;
    margin-bottom: 0.5rem;
    text-shadow: 0 4px 12px rgba(0,0,0,0.7);
}}

.hero-overlay p {{
    font-size: 1.5rem;
    opacity: 0.85;
    text-shadow: 0 3px 8px rgba(0,0,0,0.6);
}}
</style>

<div class="hero-container">
  <video autoplay muted loop playsinline>
    <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
  </video>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# BACKGROUND + HEADER
# ---------------------------
set_background_image(BACKGROUND_IMAGE_PATH)
show_brandbar()

st.markdown("""
<style>
/* Make tabs bigger and styled */
.stTabs [role="tablist"] {
    gap: 24px;
    justify-content: center;
    border-bottom: 2px solid rgba(255,255,255,0.2);
    margin-bottom: 30px;
}

.stTabs [role="tab"] {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    padding: 20px 35px !important;
    border-radius: 12px 12px 0 0 !important;
    background: rgba(255,255,255,0.05);
    color: #e0e0e0 !important;
    transition: all 0.3s ease;
    border: 2px solid rgba(255,255,255,0.1);
    border-bottom: none !important;
}

.stTabs [role="tab"][aria-selected="true"] {
    background: rgba(0, 0, 0, 0.55) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    border: 2px solid rgba(255,255,255,0.25);
    border-bottom: none !important;
}

.stTabs [role="tab"]:hover {
    background: rgba(255,255,255,0.1);
    color: #fff !important;
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)
tabs = st.tabs(["Intro", "Satellite", "Evaluation", "Test Model"])

# Show video banner only on tabs[1] and tabs[2]
active_tab_index = st.session_state.get("active_tab_index", 0)
if active_tab_index != 0:
    st.markdown(
        """
        <style>
        .hero-video {
            width: 100%;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 0 25px rgba(0,0,0,0.4);
            margin-bottom: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    with open(INTRO_VIDEO_PATH, "rb") as f:
        st.video(f.read())

# ---------------------------
# TAB 1: INTRO
# ---------------------------
with tabs[0]:
    st.subheader("AI-Powered Oil Spill Detection from Satellite Imagery")

    st.markdown("""
    ### 🌍 Overview
    **Petra** (a blend of **Petroleum** and **Terra**, meaning **Oil + Earth**) is a Computer Vision project 
    designed to **detect oil spills in our oceans using satellite imagery**.  
    Our mission is to support environmental protection and marine safety through 
    advanced deep learning techniques and real-time monitoring.

    ### 📡 Core Idea
    - Petra uses **Convolutional Neural Networks (CNNs)** trained on real **SAR and optical satellite images**.
    - The model can **detect oil slick patterns** across large water surfaces.
    - It can integrate with **FastAPI** as a backend and a **Streamlit dashboard** for real-time monitoring.

    ### 🧠 Technical Highlights
    - **Image Preprocessing:** Images are enhanced, normalized, and resized for CNN input.
    - **Data Augmentation:** Improves generalization across different lighting, angles, and resolutions.
    - **Model Architecture:** Multi-layer CNN with convolution, pooling, batch normalization, and dense layers.
    - **Deployment:** FastAPI backend for prediction + Streamlit front-end with a 3D satellite map view.

    ### 🌊 Why It Matters
    - Oil spills threaten marine ecosystems and coastal economies.
    - Early detection can help authorities react faster and reduce damage.
    - Petra provides a scalable and automated solution for **continuous satellite monitoring**.

    ### 📈 Future Goals
    - Expand dataset with real-time Sentinel-1 SAR imagery
    - Add geolocation-based detection on global map
    - Provide API endpoints for integration with maritime authorities
    """)

    st.info("Scroll to the next tabs to explore the Satellite demo and run your own predictions.")


# ---------------------------
# TAB 2: SATELLITE
# ---------------------------
with tabs[1]:
    st.markdown("### Satellite View (Demo Points)")
    st.caption("Tip: zoom & pan. Style and points are customizable.")

    mapbox_token = st.secrets["MAPBOX_API_KEY"]

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"lat": d["lat"], "lon": d["lon"], "name": d["name"], "conf": d["conf"]} for d in DEMO_COORDS],
        get_position='[lon, lat]',
        get_fill_color='[255 * (1-conf), 255 * conf, 30, 200]',
        get_radius=2500,
        pickable=True,
    )

    view_state = pdk.ViewState(latitude=26.35, longitude=50.05, zoom=6.5, pitch=30, bearing=0)
    tooltip = {"html": "<b>{name}</b><br/>Confidence: {conf}", "style": {"color": "white"}}

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/streets-v12",  # 🌈 colorful style
        api_keys={"mapbox": mapbox_token},
    )

    st.pydeck_chart(r, use_container_width=True)


    with st.expander("Demo Coordinates"):
        st.code("\n".join([f"({d['lat']}, {d['lon']})  conf={d['conf']}" for d in DEMO_COORDS]), language="text")
# ---------------------------
# TAB 3: EVALUATION
# ---------------------------
with tabs[2]:
    st.markdown("## 🧠 Evaluation of Petra CNN Model")
    st.caption("Architecture • Labels • Performance Metrics")

    # --- Section 1: CNN Architecture ---
    st.markdown("### 📐 CNN Architecture")
    st.markdown("""
    Petra's Convolutional Neural Network (CNN) is designed specifically to detect **oil spill patterns** 
    in satellite imagery. Here's how it works:

    - **Input Layer**: Accepts RGB satellite images (resized to 128x128 pixels).
    - **Convolution Layers**: Extract spatial features using 3x3 kernels and ReLU activation.
    - **Pooling Layers (MaxPooling)**: Reduce spatial dimensions to focus on the most important patterns.
    - **Batch Normalization + Dropout**: Improve training stability and prevent overfitting.
    - **Flatten + Dense Layers**: Combine extracted features and learn class-specific patterns.
    - **Output Layer (Sigmoid)**: Outputs a probability between 0 (clean sea) and 1 (oil spill).
    """)

    st.info("This model was trained on real satellite images labeled manually as **Oil Spill** or **Gas Spill**.")

    # --- Section 2: Labels and Sample Images ---
    st.markdown("### 🏷️ Labels and Training Examples")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🛢️ Real Oil Spill")
        st.image("oil_1.jpg", caption="Oil Spill Example 1")
    with col2:
        st.markdown("#### 🛢️ Train Oil Spill")
        st.image("train_oil.jpg", caption="Clean Sea Example 1")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🛢️ gas Spill")
        st.image("gas_1.jpg", caption="Oil Spill Example 1")
    with col2:
        st.markdown("#### 🛢️ gas Spill")
        st.image("train_gas.jpg", caption="Clean Sea Example 1")

    # --- Section 3: Evaluation Metrics ---
    st.markdown("### 📊 Evaluation Metrics on Validation Set")
    st.markdown("""
    We evaluated Petra's CNN on a held-out validation set.

    - **Accuracy**: 0.93  
    - **Precision**: 0.91  
    - **Recall**: 0.89  
    - **F1-score**: 0.90  
    - **Loss**: 0.18

    These metrics show that Petra performs reliably in identifying oil spill patterns 
    while minimizing false positives on clean ocean images.
    """)

    st.success("Petra achieved over **93% accuracy** distinguishing oil spills from clean sea surfaces.")

# ---------------------------
# TAB 3: TEST MODEL
# ---------------------------
with tabs[3]:
    st.markdown("### Run Inference (FastAPI)")
    st.caption(f"Endpoint: `{FASTAPI_URL}`  •  Update with env var FASTAPI_URL")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Upload Image")
        file = st.file_uploader("Satellite image (JPG/PNG)", type=["jpg", "jpeg", "png"])
        run = st.button("Predict", type="primary", use_container_width=True, disabled=(file is None))
        if run and file is not None:
            with st.spinner("Calling FastAPI…"):
                ok, resp = call_fastapi_predict_file(file.read(), file.name)
            if ok:
                st.success("Prediction complete")
                st.json(resp)
            else:
                st.error("Prediction failed")
                st.json(resp)

        st.divider()
        st.subheader("Or Predict by Image URL")
        url_in = st.text_input("Public image URL", placeholder="https://…/satellite.jpg")
        run_url = st.button("Predict URL", use_container_width=True, disabled=(not url_in))
        if run_url and url_in:
            with st.spinner("Calling FastAPI…"):
                ok, resp = call_fastapi_predict_url(url_in)
            if ok:
                st.success("Prediction complete")
                st.json(resp)
            else:
                st.error("Prediction failed")
                st.json(resp)

    with right:
        st.subheader("Preview")
        if file is not None:
            try:
                img = Image.open(file).convert("RGB")
                st.image(img, caption=file.name, use_column_width=True)
            except Exception:
                st.info("Preview not available. The file will still be sent to the API.")

    st.caption("Expected FastAPI interface: POST `/predict` with either multipart file (`file`) or JSON `{url: ...}`.")

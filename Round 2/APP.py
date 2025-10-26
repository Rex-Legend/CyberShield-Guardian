import streamlit as st
import pandas as pd
import json, hashlib, random, threading, time, io, os
from datetime import datetime
import speech_recognition as sr
from Crypto.Cipher import AES
from streamlit_js_eval import get_geolocation
import qrcode
from playsound import playsound
import folium
from streamlit_folium import st_folium

# ---------- APP CONFIG ----------
st.set_page_config(page_title="CyberShield Guardian", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.stApp {background-color:#000010; color:#00FFFF;}
h1,h2,h3{color:#00FFFF;}
.stButton>button {background-color:#001f3f; color:#00FFFF; border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# ---------- GLOBAL VARIABLES ----------
ALERT_FILE = "alerts_data.json"
ENCRYPTION_KEY = b"cybershield_2025!"
recognizer = sr.Recognizer()
ALERT_SOUND = "alert_sound.mp3"  # Place any alert sound (mp3) in same directory

# ---------- ENCRYPTION ----------
def encrypt_data(data):
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(data).encode())
    return (cipher.nonce + ciphertext).hex()

# ---------- ALERT STORAGE ----------
def save_alert(entry):
    df = load_alerts_df()
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()[:10]
    encrypted = encrypt_data(entry)
    df.loc[len(df)] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), encrypted]
    df.to_json(ALERT_FILE, orient="records")

def load_alerts_df():
    try:
        df = pd.read_json(ALERT_FILE)
    except:
        df = pd.DataFrame(columns=["timestamp", "data"])
    return df

# ---------- BACKGROUND VOICE LISTENER ----------
def background_listener(lat_ref, lon_ref, alert_ref):
    mic = sr.Microphone()
    while True:
        with mic as source:
            print("🎤 Listening (background)...")
            audio = recognizer.listen(source, phrase_time_limit=3)
        try:
            text = recognizer.recognize_google(audio).lower()
            print("Heard:", text)
            if any(x in text for x in ["help", "emergency", "danger", "save me", "alert"]):
                alert_ref["active"] = True
                save_alert({
                    "user": "Thoyeshwar",
                    "status": "SOS_TRIGGER",
                    "details": text,
                    "lat": lat_ref["value"],
                    "lon": lon_ref["value"]
                })
                if os.path.exists(ALERT_SOUND):
                    playsound(ALERT_SOUND)
        except:
            pass
        time.sleep(2)

# ---------- STREAMLIT UI ----------
st.title("🛡️ CyberShield Guardian — Advanced Live Tracking")

# Initialize states
if "listener_active" not in st.session_state:
    st.session_state.listener_active = False
if "lat_ref" not in st.session_state:
    st.session_state.lat_ref = {"value": 0.0}
if "lon_ref" not in st.session_state:
    st.session_state.lon_ref = {"value": 0.0}
if "alert_ref" not in st.session_state:
    st.session_state.alert_ref = {"active": False}

lat_ref = st.session_state.lat_ref
lon_ref = st.session_state.lon_ref
alert_ref = st.session_state.alert_ref

# 1️⃣ Voice Listener
if st.button("🎙️ Start Voice Listener"):
    if not st.session_state.listener_active:
        threading.Thread(target=background_listener, args=(lat_ref, lon_ref, alert_ref), daemon=True).start()
        st.session_state.listener_active = True
        st.info("Voice listener running in background...")

# 2️⃣ Live Location Tracking (Auto-refresh)
st.subheader("🌍 Live Location Tracking (Auto-updating)")
refresh_interval = st.slider("Auto-refresh interval (seconds)", 5, 30, 10)
loc = get_geolocation()

if loc:
    lat_ref["value"] = loc['coords']['latitude']
    lon_ref["value"] = loc['coords']['longitude']

    # Build and show map
    m = folium.Map(location=[lat_ref["value"], lon_ref["value"]], zoom_start=15)
    folium.Marker(
        [lat_ref["value"], lon_ref["value"]],
        popup="Current Position",
        icon=folium.Icon(color="blue", icon="shield")
    ).add_to(m)

    st_folium(m, width=700, height=450, key=str(random.randint(1, 100000)))
    st.success(f"📍 Latitude: {lat_ref['value']:.5f}, Longitude: {lon_ref['value']:.5f}")

    # Auto-refresh timer (use st.rerun safely)
    time.sleep(refresh_interval)
    st.rerun()
else:
    st.warning("Waiting for location access... please allow browser permission.")

# 3️⃣ SOS Alert
if alert_ref["active"]:
    st.error("🚨 SOS DETECTED — Voice Triggered Emergency!")
    st.balloons()

# 4️⃣ QR Code
st.subheader("📱 Project QR Code")
qr_img = qrcode.make("https://github.com/Thoyeshwar/CyberShieldGuardian")
qr_path = "project_qr.png"
qr_img.save(qr_path)
st.image(qr_path, caption="Scan to visit GitHub Repository")

st.markdown("---")
st.markdown("**CyberShield Guardian v3.6 — Real-time Tracking + Emergency Voice Response**")

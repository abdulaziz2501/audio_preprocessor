import streamlit as st
import pandas as pd
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

import wave
import streamlit as st
import base64

def realtime_waveform(audio_path):
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    audio_base64 = base64.b64encode(audio_bytes).decode()

    html = f"""
    <style>
    canvas {{
        width: 100%;
        height: 80px;
    }}
    </style>

    <audio id="audio" controls style="width:100%">
        <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
    </audio>

    <canvas id="waveform"></canvas>

    <script>
    const audio = document.getElementById("audio");
    const canvas = document.getElementById("waveform");
    const ctx = canvas.getContext("2d");

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaElementSource(audio);
    const analyser = audioCtx.createAnalyser();

    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    analyser.fftSize = 2048;
    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {{
        requestAnimationFrame(draw);
        analyser.getByteTimeDomainData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#4F7DF3";
        ctx.beginPath();

        const sliceWidth = canvas.width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {{
            const v = dataArray[i] / 128.0;
            const y = v * canvas.height / 2;

            if (i === 0) {{
                ctx.moveTo(x, y);
            }} else {{
                ctx.lineTo(x, y);
            }}
            x += sliceWidth;
        }}

        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
    }}

    audio.onplay = () => {{
        audioCtx.resume();
        draw();
    }};
    </script>
    """

    st.components.v1.html(html, height=160)

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Audio Dataset Inspector",
    layout="wide"
)
st.title("🎧 Audio Dataset Inspector")

# ======================================================
# USER INPUTS
# ======================================================
metadata_path = st.text_input(
    "📄 metadata.csv path",
    value="output/metadata.csv"
)

audio_root = st.text_input(
    "🎵 Audio root folder (where .wav files are)",
    value="output/long_audio/audio"
)

show_waveform = st.checkbox("🔊 Show waveform (dB energy)")

# ======================================================
# BASIC VALIDATION
# ======================================================
if not os.path.exists(metadata_path):
    st.error("❌ metadata.csv not found")
    st.stop()

if not os.path.exists(audio_root):
    st.error("❌ Audio root folder not found")
    st.stop()

# ======================================================
# LOAD METADATA
# ======================================================
df = pd.read_csv(metadata_path)

required_cols = {"audio_path", "segment"}
if not required_cols.issubset(df.columns):
    st.error("❌ metadata.csv must contain: audio_path, segment")
    st.stop()

# ======================================================
# VISUAL WAVEFORM
# ======================================================
def visualize_waveform_streamlit(path: str, bars: int = 120):
    """
    Compact bar-style waveform for Streamlit
    """

    if not os.path.exists(path):
        st.error("Audio file not found")
        return

    # ===== READ AUDIO (same as your code)
    raw = wave.open(path)
    signal = raw.readframes(-1)
    signal = np.frombuffer(signal, dtype=np.int16)
    raw.close()

    # ===== NORMALIZE
    signal = signal / np.max(np.abs(signal))

    # ===== DOWNSAMPLE FOR COMPACT VIEW
    step = max(1, len(signal) // bars)
    signal_ds = signal[::step][:bars]

    # ===== PLOT (COMPACT)
    fig, ax = plt.subplots(figsize=(6, 2))

    ax.vlines(
        range(len(signal_ds)),
        0,
        signal_ds,
        linewidth=2,
        color="#4F7DF3"
    )

    ax.set_ylim(-1, 1)
    ax.axis("off")

    st.pyplot(fig)


# ======================================================
# PATH RESOLVER
# ======================================================
def resolve_audio_path(original_path: str, audio_root: str):
    """
    1) If original path exists -> use it
    2) Else try audio_root + filename
    """
    if isinstance(original_path, str) and os.path.exists(original_path):
        return original_path

    filename = os.path.basename(str(original_path))
    candidate = os.path.join(audio_root, filename)

    if os.path.exists(candidate):
        return candidate

    return None

df["resolved_audio_path"] = df["audio_path"].apply(
    lambda p: resolve_audio_path(p, audio_root)
)

# Keep only valid audio rows
df = df[df["resolved_audio_path"].notna()].reset_index(drop=True)

if df.empty:
    st.error("❌ No valid audio files found after path resolving")
    st.stop()

# ======================================================
# TABLE DATA (ONLY AUDIO NAME)
# ======================================================
df_table = pd.DataFrame()
df_table["audio"] = df["resolved_audio_path"].apply(
    lambda x: os.path.basename(x)
)

# ======================================================
# AGGRID TABLE
# ======================================================
st.subheader("📂 Click an audio to play")

gb = GridOptionsBuilder.from_dataframe(df_table)
gb.configure_selection("single", use_checkbox=False)
gb.configure_column("audio", header_name="Audio file name", flex=1)

grid_options = gb.build()

grid_response = AgGrid(
    df_table,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    height=350,
    theme="streamlit"
)

# ======================================================
# HANDLE SELECTION (SAFE WAY)
# ======================================================
selected_df = grid_response["selected_rows"]

if isinstance(selected_df, pd.DataFrame) and not selected_df.empty:
    selected_audio_name = selected_df.iloc[0]["audio"]

    row = df[
        df["resolved_audio_path"].apply(
            lambda x: os.path.basename(x)
        ) == selected_audio_name
    ].iloc[0]

    audio_path = row["resolved_audio_path"]
    text = row["segment"]

    # if show_waveform:
    #     visualize_waveform_streamlit(audio_path)
    # ================= AUDIO PLAYER =================
    realtime_waveform(audio_path)
    # ================= WAVEFORM (dB ENERGY) =================
    # ================= TEXT =================
    st.subheader("📝 Transcription")
    st.text_area(
        "",
        value=text,
        height=200
    )



else:
    st.info("👆 Select an audio from the table")

# ======================================================
# DEBUG PANEL
# ======================================================
with st.expander("🛠 Debug info"):
    st.write("Total metadata rows:", len(df))
    st.write("Audio root:", audio_root)
    st.write("Example resolved path:", df["resolved_audio_path"].iloc[0])

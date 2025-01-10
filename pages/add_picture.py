import streamlit as st
import os
from streamlit_float import *
from datetime import datetime  # 修正ポイント
from PIL import Image

# ヘッダー部分に患者情報を固定
header_container = st.container()
with header_container:
    st.header(" SkinSnap")
    st.text(" 患者ID：" + st.session_state["PatientID"])
    st.text(" 患者名：" + st.session_state["PatientName"])

header_css = float_css_helper(width="30rem", right="0rem", top='2.5rem', transition=50,background="rgba(255, 255, 255, 0.35)")
header_container.float(header_css)

st.header("")
st.subheader("")

# Pythonファイルがあるディレクトリを取得
current_directory = os.path.dirname(os.path.abspath(__file__))
picture_directory = os.path.join(current_directory, 'assets', 'Picture')
MRNo_directory = os.path.join(picture_directory, st.session_state.get("PatientID", "default"))

if not os.path.exists(picture_directory):
    os.makedirs(picture_directory)
if not os.path.exists(MRNo_directory):
    os.makedirs(MRNo_directory)

# ファイルアップロード
uploaded_files = st.file_uploader(
    "カメラで写真を撮影またはアップロードしてください",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True  # 複数ファイルの受け入れを有効化
)

if uploaded_files:
    for uploaded_file in uploaded_files:  # 各ファイルを処理
        # ユニークなファイル名を作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(MRNo_directory, unique_filename)

        # 画像を保存
        with Image.open(uploaded_file) as image:
            image.save(file_path)

        st.success(f"写真 {uploaded_file.name} のアップロードに成功しました")


button_container = st.container()
with button_container:
    option_map = {
        0: ":material/arrow_back:",
    }
    selection_left = st.pills(
        "back",
        options=option_map.keys(),
        format_func=lambda option: option_map[option],
        selection_mode="single",
        label_visibility="hidden",
    )
    if selection_left == 0:
        st.switch_page("pages/photo_manager.py")

button_css = float_css_helper(width="1rem", left="2rem", bottom='1rem', transition=0)
button_container.float(button_css)
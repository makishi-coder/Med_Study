import streamlit as st
import os
from streamlit_float import *
import base64
from datetime import datetime  # 修正ポイント
from PIL import Image
from PIL import Image, ExifTags
import utils.func

utils.func.set_tab("#c9daf8")
utils.func.set_header()
# ヘッダー部分に患者情報を固定
# ヘッダーとしてHTMLを使用
header_container = st.container()
with header_container:
    st.text(" 患者ID：" + st.session_state["PatientID"])
    st.text(" 患者名：" + st.session_state["PatientName"])
header_css = float_css_helper(width="10rem", right="3rem", top='0.1rem', transition=50,background="rgba(255, 255, 255, 0)")
header_container.float(header_css)


header_container = st.container()
with header_container:
    img_path = utils.func.get_patient_image_path(st.session_state["PatientID"])
    if img_path is not "":
            # ローカル画像をbase64形式に変換
        with open(img_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode("utf-8")
        # HTMLで丸いアイコンを作成
        html_code = f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            width: 50px;
            height: 50px;
            overflow: hidden;
            border-radius: 50%;  /* 丸くする */
            border: 2px solid #ddd;  /* 枠線を追加 */
        ">
            <img src="data:image/jpeg;base64,{base64_image}" style="width: 100%; height: 100%; object-fit: cover;" />
        </div>
        """

        # StreamlitでHTMLを埋め込む
        st.markdown(html_code, unsafe_allow_html=True)
header_css = float_css_helper(width="10rem", right="6.5rem", top='0.6rem', transition=50,background="rgba(255, 255, 255, 0)")
header_container.float(header_css)


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

button_css = float_css_helper(width="1rem", left="2rem", bottom='3.5rem', transition=0)
button_container.float(button_css)

# Pythonファイルがあるディレクトリを取得
current_directory = os.path.dirname(os.path.abspath(__file__))
picture_directory = os.path.join(current_directory, 'assets', 'Picture')
MRNo_directory = os.path.join(picture_directory, st.session_state.get("PatientID", "default"))
thumbnail_directory = os.path.join(MRNo_directory, 'thumbnail')


if not os.path.exists(picture_directory):
    os.makedirs(picture_directory)
if not os.path.exists(MRNo_directory):
    os.makedirs(MRNo_directory)
if not os.path.exists(thumbnail_directory):
    os.makedirs(thumbnail_directory)

# 初期化
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# ファイルアップロード
uploaded_files = st.file_uploader(
    "カメラで写真を撮影またはアップロードしてください",
    type=["webp", "jpg", "jpeg", "png"],
    accept_multiple_files=True  # 複数ファイルの受け入れを有効化
)

# EXIF回転情報を無視する
def process_image(image):
    # 画像をバイナリで開く
    # EXIF情報の取得と回転処理（必要に応じて修正）
    try:
        # 画像がEXIF情報を持っている場合
        exif = image._getexif()
        if exif is not None:
            # EXIFタグに基づく回転
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
    except Exception as e:
        print(f"EXIFの処理中にエラーが発生しました: {e}")

    return image

if uploaded_files:
    for uploaded_file in uploaded_files:  # 各ファイルを処理
        # ファイルがすでにアップロードリストに含まれていない場合に追加
        if uploaded_file not in st.session_state.uploaded_files:
                        # ユニークなファイル名を作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{datetime.now().microsecond // 1000}"
            unique_filename = f"{timestamp}_{uploaded_file.name}"
            file_path = os.path.join(MRNo_directory, unique_filename)
            thumbnail_path = os.path.join(thumbnail_directory, unique_filename)
            # 画像を保存
            try:
                with Image.open(uploaded_file) as image:
                    image=process_image(image)
                    image.save(file_path)
                    image.thumbnail(size=(100, 100))
                    image.save(thumbnail_path, "WEBP")
                st.success(f"写真 {uploaded_file.name} のアップロードに成功しました")
            except Exception as e:
                print(f"写真 {uploaded_file.name} のアップロードに失敗しました: {e}") 
            st.session_state.uploaded_files.append(uploaded_file)

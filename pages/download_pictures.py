import streamlit as st
import pandas as pd
import os
import sqlite3
import utils.func
import base64
from st_aggrid import GridOptionsBuilder, AgGrid
from st_aggrid.shared import JsCode
import base64
import openai
import time
from datetime import datetime
from streamlit_float import *
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import ComputerVisionOcrErrorException
import io
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from concurrent.futures import ThreadPoolExecutor
import zipfile
from io import BytesIO
import re

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

# 戻るボタン
button_container = st.container()
with button_container:
    option_map = {
        0: ":material/arrow_back:",
    }
    selection_left = st.pills("back",
        options=option_map.keys(),
        format_func=lambda option: option_map[option],
        selection_mode="single",
        label_visibility="hidden",
    )
    if selection_left == 0:
        st.switch_page("pages/photo_manager.py")


button_css = float_css_helper(width="1rem", left="2rem", bottom='3.5rem', transition=0)
button_container.float(button_css)

st.write("")
# 画像をBase64で読み込む関数
def ReadPictureFile(wch_fl):
    try:
        return base64.b64encode(open(wch_fl, 'rb').read()).decode()
    except:
        return ""

# カスタム画像レンダラー
thumbnail_renderer = JsCode("""
    class ThumbnailRenderer {
        init(params) {
            this.eGui = document.createElement('img');
            this.eGui.setAttribute('src', params.value);
            this.eGui.setAttribute('width', 'auto');
            this.eGui.setAttribute('height', 'auto');
            this.eGui.style.objectFit = 'contain';  // 全体を表示
        }
        getGui() {
            return this.eGui;
        }
    }
""")


# 写真ディレクトリから画像パスと撮影日を取得
def get_patient_image_path(patient_id):
    # 現在のスクリプトのディレクトリ
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 画像ディレクトリ
    picture_directory = os.path.join(current_directory, 'assets', 'Picture')
    patient_dir = os.path.join(picture_directory, patient_id)
    thumbnail_dir = os.path.join(patient_dir, 'thumbnail')

    # 許可されている拡張子
    allowed_extensions = [".jpg", ".jpeg", ".png"]

    # サムネイルディレクトリが存在しない場合は空のDataFrameを返す
    if not os.path.exists(patient_dir):
        return pd.DataFrame(columns=["date","file_path"])

    # ファイル一覧を取得しタイムスタンプ順にソート
    image_files = [
        file for file in os.listdir(patient_dir)
        if os.path.splitext(file)[1].lower() in allowed_extensions
    ]

    if not image_files:
        return pd.DataFrame(columns=["date","file_path"])

    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(patient_dir, x)), reverse=True)

    # ファイルパスと最終更新日時をDataFrameに格納
    image_data = []
    for file in image_files:
        file_path = os.path.join(patient_dir, file)
        file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        image_data.append({"download":False,"date": file_date,"file_path": file_path})


    return pd.DataFrame(image_data)

# 画像をBase64エンコードする関数
def encode_image_to_base64(img_path):
    # 空のパスやNoneの場合は処理しない
    if img_path == "" or pd.isna(img_path):
        return None  # 空の場合はNoneを返す
    try:
        with open(img_path, 'rb') as img_file:
            img_data = img_file.read()
        return base64.b64encode(img_data).decode('utf-8')
    except FileNotFoundError:
        return None  # ファイルが見つからない場合はNoneを返す

# 並列で画像をエンコードする関数
def process_images(df):
    img_paths = df['file_path']
    # 並列処理を使って画像を一括でBase64エンコード
    with ThreadPoolExecutor() as executor:
        base64_images = list(executor.map(encode_image_to_base64, img_paths))
        # Base64のデータURLを作成
    df['file_path'] = [
        f"data:image/{path.split('.')[-1]};base64,{img}" if img else "" 
        for path, img in zip(df['file_path'], base64_images)
    ]
    return df


# データフレームを作成
# 検索フォーム

# 一覧表示処理
st.text("ダウンロードしたい写真を一覧から選択してください")
df = get_patient_image_path(st.session_state.PatientID)
df = process_images(df)


# カスタム画像レンダラー
thumbnail_renderer = JsCode("""
    class ThumbnailRenderer {
        init(params) {
            this.eGui = document.createElement('img');
            this.eGui.setAttribute('src', params.value);
            this.eGui.setAttribute('width', 'auto');
            this.eGui.setAttribute('height', 'auto');
            this.eGui.style.objectFit = 'contain';  // 全体を表示
        }
        getGui() {
            return this.eGui;
        }
    }
""")



#gb = GridOptionsBuilder.from_dataframe(df)
#gb.configure_column("date", headerName="撮影日")
#gb.configure_column("file_path", headerName="写真", cellRenderer=thumbnail_renderer)

# セル選択イベントの設定
#gb.configure_selection('multiple', use_checkbox=True)  # 単一選択
#gb.configure_grid_options(checkboxSelection=True,)
#gb.configure_grid_options(rowHeight=100)
#grid_options = gb.build()

# 表の描画
#response = AgGrid(df, gridOptions=grid_options, theme='streamlit', height=400,fit_columns_on_grid_load=True, allow_unsafe_jscode=True)

edited_df = st.data_editor(
    df,
    column_config={
        "download": st.column_config.CheckboxColumn(
            "ダウンロード",
            default=True,
        ),
        "date": st.column_config.TextColumn(
            "日付",
            disabled=True,
        ),
        "file_path": st.column_config.ImageColumn(
            "写真", 
            help="プレビュー画像",
        ),
    },
    hide_index=True,
)



# Base64データ抽出関数
def extract_base64_data(data_uri):
    if data_uri.startswith("data:image/"):
        return data_uri.split(",")[1]
    return data_uri

# ファイル名のサニタイズ関数
def sanitize_filename(filename):
    # 禁止文字の置換
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    return sanitized[:255]  # 長さ制限

# 日時フォーマットを安全な形式に変換
def format_date_time(date_time_str):
    # コロンやスペースを安全な文字に置換
    return date_time_str.replace(":", "-").replace(" ", "_")

# チェックボックスで選択された行をフィルタリング
selected_rows = edited_df[edited_df["download"]]

if not df.empty:
    if not selected_rows.empty:
        # メモリ上にZIPファイルを作成
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for index, row in selected_rows.iterrows():
                # Base64部分を抽出してデコード
                base64_data = extract_base64_data(row["file_path"])
                try:
                    image_data = base64.b64decode(base64_data)
                except base64.binascii.Error as e:
                    st.error(f"Base64デコードに失敗しました: {e}")
                    continue
                
                # ファイル名を設定
                # ファイル名の生成（安全な形式に変換）
                original_filename = f"{row['date']}_photo.png"
                safe_filename = sanitize_filename(format_date_time(original_filename))
    
                # ZIPファイルに追加
                zip_file.writestr(safe_filename, image_data)
        
        # ZIPファイルのポインタを先頭に戻す
        zip_buffer.seek(0)
    
        # ダウンロードボタンを作成
        st.download_button(
            label="選択した写真を一括ダウンロード",
            data=zip_buffer.getvalue(),  # ZIPファイルを取得
            file_name="selected_photos.zip",
            mime="application/zip",
        )
else:
    st.warning("写真が見つかりませんでした。")

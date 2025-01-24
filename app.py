import streamlit as st
import pandas as pd
import os
import sqlite3
import utils.func

from st_aggrid import GridOptionsBuilder, AgGrid
from st_aggrid.shared import JsCode
import base64
import openai
import time
from streamlit_float import *
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import ComputerVisionOcrErrorException
import io
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from concurrent.futures import ThreadPoolExecutor

utils.func.set_tab()
utils.func.set_header_home()

button_container = st.container()
with button_container:
    if st.button("👤✚"):
        st.session_state.ex_id,st.session_state.ex_name = None,None
        st.switch_page("pages/patient_manager.py")

button_css = float_css_helper(width="1rem", right="4rem", bottom='1rem', transition=0)
button_container.float(button_css)


key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")
openai.api_key = os.getenv("OPENAI_API_KEY")

# データベース接続
def get_db_connection():
    conn = sqlite3.connect("patients.db")
    conn.row_factory = sqlite3.Row  # 辞書形式でデータを取得
    return conn

# テーブルの初期化
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

initialize_database()  # 初期化
def list_patient():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print(dict(row))

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
            this.eGui.setAttribute('width', '40');
            this.eGui.setAttribute('height', 'auto');
            this.eGui.style.objectFit = 'contain';  // 全体を表示
        }
        getGui() {
            return this.eGui;
        }
    }
""")

# データベース接続とデータ取得
def fetch_patient_data():
    conn = sqlite3.connect("patients.db")
    query = """
        SELECT id AS PatientID, name AS Name
        FROM patients
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 部分一致検索機能
def search_patient_data(search_text):
    conn = sqlite3.connect("patients.db")
    query = """
        SELECT id AS PatientID, name AS Name
        FROM patients
        WHERE id LIKE ? OR name LIKE ?
    """
    # 検索条件を部分一致形式に変換
    search_pattern = f"%{search_text}%"
    df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern))
    conn.close()
    df["ImgPath"] = df["PatientID"].apply(utils.func.get_patient_image_path)
    return df


# データフレームの作成と画像パスの追加
def create_patient_dataframe():
    df = fetch_patient_data()
    df["ImgPath"] = df["PatientID"].apply(utils.func.get_patient_image_path)
    return df


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
    img_paths = df['ImgPath']
    # 並列処理を使って画像を一括でBase64エンコード
    with ThreadPoolExecutor() as executor:
        base64_images = list(executor.map(encode_image_to_base64, img_paths))
        # Base64のデータURLを作成
    df['ImgPath'] = [
        f"data:image/{path.split('.')[-1]};base64,{img}" if img else "" 
        for path, img in zip(df['ImgPath'], base64_images)
    ]
    return df


# データフレームを作成
# 検索フォーム
if "ex_id" not in st.session_state:
    st.session_state["ex_id"] = None
if "ex_name" not in st.session_state:
    st.session_state["ex_name"] = None

if "camera_image" not in st.session_state:
    st.session_state.camera_image = None
# リクエストのプロトコルを確認
if st.toggle("カメラによる入力"):
    x = st.camera_input(label="診察券の写真をとってください", key="camera_input_file")
    if x is not None:
        st.image(x, use_container_width=True)
        if st.session_state.camera_image != x:
            st.session_state.camera_image = x
            with st.spinner("OCR処理中..."):
                #画像をバイトとして処理
                image_bytes = x.getvalue()
                ocr_result = utils.func.process_image(image_bytes)
                print(ocr_result)
                if ocr_result:
                    st.session_state.ex_id,st.session_state.ex_name = utils.func.extract_medical_id(ocr_result)
                    st.rerun()

search_text = st.text_input("検索",value=st.session_state.ex_id,label_visibility="hidden",placeholder="検索")

# 検索処理
st.text("画像を見たい患者をリストから選択してください")

# データ表示
if search_text:
    df = search_patient_data(search_text)
else:
    df = create_patient_dataframe()
if df.empty:
    st.warning("患者が見つかりませんでした。")
else:
    df=process_images(df)


    # カラム順を「写真」「患者名」「患者ID」に変更
    df = df[['ImgPath', 'Name', 'PatientID']]

    # AgGridの設定
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("ImgPath", headerName="写真", cellRenderer=thumbnail_renderer)
    gb.configure_column("Name", headerName="患者名")
    gb.configure_column("PatientID", headerName="患者ID")

    # セル選択イベントの設定
    gb.configure_selection('single')  # 単一選択
    gb.configure_grid_options(rowHeight=40)
    grid_options = gb.build()

    # 表の描画
    response = AgGrid(df, gridOptions=grid_options, theme='streamlit', height=200,fit_columns_on_grid_load=True, allow_unsafe_jscode=True)
    
    # session_state の初期化
    if "PatientID" not in st.session_state:
        st.session_state["PatientID"] = None
    if "PatientName" not in st.session_state:
        st.session_state["PatientName"] = None

    if response['selected_rows'] is not None:
        st.session_state["PatientID"] = response['selected_rows']['PatientID'].iloc[0]
        st.session_state["PatientName"] = response['selected_rows']['Name'].iloc[0]
        st.session_state.ex_id,st.session_state.ex_name = None,None
        st.switch_page("pages/photo_manager.py")


import streamlit as st
import sqlite3
import openai
import json
import utils.func
import base64
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import ComputerVisionOcrErrorException
import io
import os
import re
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from streamlit_float import *
import time

utils.func.set_tab()
utils.func.set_header()
key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        st.switch_page("app.py")


button_css = float_css_helper(width="1rem", left="2rem", bottom='1rem', transition=0)

button_container.float(button_css)

def register_patient(PatientId,name):
    try:
        # データベース接続
        conn = sqlite3.connect("patients.db")
        cursor = conn.cursor()

        # 既に患者IDが存在するか確認
        cursor.execute("SELECT * FROM patients WHERE id = ?", (PatientId,))
        existing_patient = cursor.fetchone()
        if existing_patient:
            return f"患者ID '{PatientId}' は既に登録されています。"
        else:
            cursor.execute("""
                INSERT INTO patients (id, name)
                VALUES (?, ?)
            """, (PatientId, name))
            conn.commit()
            conn.close()
            return ""
    except sqlite3.Error as e:
        # SQLiteエラーが発生した場合
        return f"データベースエラー: {e}"

def get_from_pic():
    x = st.camera_input(label="診察券の写真をとってください", key="camera_input_file")
    if st.session_state.camera_image == x:
        return None
    if x is not None:
        st.image(x, use_container_width=True)

        with st.spinner("OCR処理中..."):
            #画像をバイトとして処理
            image_bytes = x.getvalue()
            ocr_result = process_image(image_bytes)
            print(ocr_result)
            if ocr_result:
                id,name = extract_medical_id(ocr_result)
                return id,name,x

def process_image(image_bytes):
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
    # 画像をストリームに変換
    try:
        recognize_results = computervision_client.read_in_stream(io.BytesIO(image_bytes), language="ja", raw=True)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        return None

    # 結果を取得するための操作IDを取得
    operation_location_remote = recognize_results.headers["Operation-Location"]
    operation_id = operation_location_remote.split("/")[-1]

    # 結果が利用可能になるまで待つ
    while True:
        get_text_results = computervision_client.get_read_result(operation_id)
        if get_text_results.status not in ["notStarted", "running"]:
            break
        time.sleep(1)

    # テキストの出力
    if get_text_results.status == OperationStatusCodes.succeeded:
        extracted_text = []
        for text_result in get_text_results.analyze_result.read_results:
            for line in text_result.lines:
                extracted_text.append(line.text)

        # 1. 抽出結果を結合して一つの文字列にする
        combined_text = " ".join(extracted_text)
        
        # 2. 特殊文字や改行を削除
        clean_text = re.sub(r"[^\w\s\u4E00-\u9FFF]", "", combined_text)  # 日本語文字（漢字、ひらがな、カタカナ）とスペース、英数字を残す
        clean_text = re.sub(r"\s+", " ", clean_text).strip()  # 不要な空白を削除
        
        return clean_text

    else:
        st.error("OCR処理に失敗しました。")
        return None
########
def extract_medical_id(input_text):
    """
    ChatGPT APIを使用して診療番号を抽出する関数 (新しいAPI対応)
    """
    messages = [
        {"role": "system", "content": "You are an assistant that extracts information from text."},
        {
            "role": "user",
            "content": (
                f"""Extract the patient ID and name from the text below.
                - The ID consists of 4 to 8 digits. It may include hyphens ('-') or spaces, but they should be removed in the result.
                - Exclude IDs that contain any alphabetic characters.
                - Return the result in JSON format like this:
                  {{ "id": "12345678", "name": "John Doe" }}
                Text: {input_text}"""
            ),
        },
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # 最も安価なモデル
            messages=messages,
            max_tokens=30,  # 必要な応答を最小限に抑える
            temperature=0,  # 一貫性のある応答を得る
        )
        answer = response.choices[0].message.content.strip()
        
        # JSONをパース
        data = json.loads(answer)  # JSON形式に変換

        # IDを正規化（ハイフンやスペースを削除）
        patient_id = data.get("id", "").replace("-", "").replace(" ", "")
        patient_name = data.get("name", None)  # nameを取得

        return patient_id, patient_name
    
    except json.JSONDecodeError:
        st.error("API応答をJSONとして解析できませんでした。")
        return None, None
    
    except Exception as e:
        # その他のエラー処理
        st.error(f"エラー: {e}")
        return None, None

ex_id=""
ex_name=""
image = None
if "camera_image" not in st.session_state:
    st.session_state.camera_image = None
if "ex_id" not in st.session_state:
    st.session_state.ex_id = None
if "ex_name" not in st.session_state:
    st.session_state.ex_name = None

invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']


if st.toggle("カメラによる入力"):
    result = get_from_pic()

    if result is not None:
        st.session_state.ex_id, st.session_state.ex_name,st.session_state.camera_image = result

    
id = st.text_input("患者ID", value=st.session_state.ex_id)
name = st.text_input("患者名", value=st.session_state.ex_name)

if st.button("登録",type="primary",use_container_width=True):
    if any(char in id for char in invalid_chars):
        st.error("患者IDには以下の文字を使用できません: \\ / : * ? \" < > |")
    if id == "":
        st.error("患者IDを入力してください。")
    text=register_patient(id,name)
    if text == "":
        st.success(f"患者ID '{id}' が登録されました。")
        st.session_state.ex_id = None
        st.session_state.ex_name = None
        st.switch_page("app.py")
    else:
        st.error(text)

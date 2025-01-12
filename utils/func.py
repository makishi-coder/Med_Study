import streamlit as st
import sqlite3
import openai
import json
from PIL import Image
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
import const

# タブ情報
def set_tab():
    im = Image.open("assets/logo_header.ico")
    st.set_page_config(
        page_title="SkinSnap",
        page_icon=im,
        layout="wide",
    )
# ヘッダー部分に患者情報を固定
# ヘッダーとしてHTMLを使用

def set_header():
    HIDE_ST_STYLE = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                            .appview-container .main .block-container{
                                padding-top: 1rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 1rem;
                            }  
                            .reportview-container {
                                padding-top: 0rem;
                                padding-right: 3rem;
                                padding-left: 3rem;
                                padding-bottom: 0rem;
                            }
                            header[data-testid="stHeader"] {
                                z-index: -1;
                            }
                            div[data-testid="stToolbar"] {
                            z-index: 100;
                            }
                            div[data-testid="stDecoration"] {
                            z-index: 100;
                            }
                    </style>
    """

    st.markdown(const.HIDE_ST_STYLE, unsafe_allow_html=True)


    header_container = st.container()
    with header_container:
        st.image("assets\\logo1.png",width=380)
    header_css = float_css_helper(width="35rem", left="0rem", top='0.0rem', transition=50,background="rgba(255, 255, 255, 1)")
    header_container.float(header_css)
    

key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_from_pic():
    x = st.camera_input(label="診察券の写真をとってください", key="camera_input_file")
    if x is not None:
        st.image(x, use_container_width=True)
        st.session_state.camera_image = False
        with st.spinner("OCR処理中..."):
            #画像をバイトとして処理
            image_bytes = x.getvalue()
            ocr_result = process_image(image_bytes)
            print(ocr_result)
            if ocr_result:
                id,name = extract_medical_id(ocr_result)
                return id,name

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

        st.write(f"ChatGPT APIからの回答: {answer}")
        return patient_id, patient_name

    except json.JSONDecodeError:
        st.error("API応答をJSONとして解析できませんでした。")
        return None, None

    except Exception as e:
        # その他のエラー処理
        st.error(f"エラー: {e}")
        return None, None

import streamlit as st
import os
import base64
import sqlite3
import utils.func
from streamlit_float import *
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from st_clickable_images import clickable_images

utils.func.set_tab()
utils.func.set_header()
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False

# ヘッダー部分に患者情報を固定
# ヘッダーとしてHTMLを使用

header_container = st.container()
with header_container:
    st.text(" 患者ID：" + st.session_state["PatientID"])
    st.text(" 患者名：" + st.session_state["PatientName"])
header_css = float_css_helper(width="10rem", right="0rem", top='1rem', transition=50,background="rgba(255, 255, 255, 0)")
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
        st.switch_page("app.py")


button_css = float_css_helper(width="1rem", left="2rem", bottom='1rem', transition=0)
button_container.float(button_css)


def delete_patient(patient_id):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    print(f"患者ID '{patient_id}' のデータが削除されました。")

def update_patient_db(patient_id, new_name):
    conn = sqlite3.connect("patients.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE patients SET name = ? WHERE id = ?", (new_name, patient_id))
    conn.commit()
    conn.close()

# 患者変更・削除

@st.dialog("削除確認",width="small")
def delete_confirm(id):
    st.text("患者情報を削除します。写真情報も削除されますがよろしいですか？")
    if st.button("削除",type="primary",use_container_width=True):
        delete_patient(id)
        st.session_state.os_pass = None
        st.switch_page("app.py")
    if st.button("キャンセル",use_container_width=True):
        st.rerun()

if st.session_state.delete_confirm  == True:
    st.session_state.delete_confirm  = False
    delete_confirm(st.session_state.PatientID)


@st.dialog("患者情報の変更・削除",width="small")
def update_Patient(id,name):
    with st.container():
        st.text("患者ID：" + id)
        name = st.text_input("患者名",value=name)
        with st.container():
            if st.button("変更",type="primary",use_container_width=True):
                update_patient_db(id,name)
                st.session_state["PatientName"] = name
                st.rerun()
            elif st.button("削除",type="secondary",use_container_width=True):
                st.session_state.delete_confirm  = True
                st.rerun()


button_container3 = st.container()
with button_container3:
    if st.button("👤:material/edit:"):
        update_Patient(st.session_state["PatientID"],st.session_state["PatientName"])
button_css3 = float_css_helper(width="2rem", right="6rem", bottom='1rem', transition=0)
button_container3.float(button_css3)

button_container2 = st.container()
with button_container2:
    option_map = {
        1: ":material/add:",
    }
    selection_right = st.pills("config",
        options=option_map.keys(),
        format_func=lambda option: option_map[option],
        selection_mode="single",
        label_visibility="hidden",
    )
    if selection_right == 1:
        st.switch_page("pages/add_picture.py")
        #st.switch_page("app.py")

button_css2 = float_css_helper(width="2rem", right="1.5rem", bottom='1rem', transition=0)
button_container2.float(button_css2)

PatientID=st.session_state["PatientID"]

# Pythonファイルがあるディレクトリを取得
current_directory = os.path.dirname(os.path.abspath(__file__))
picture_directory = os.path.join(current_directory, 'assets', 'Picture')
MRNo_directory = os.path.join(picture_directory, PatientID)
thumbnail_dir = os.path.join(MRNo_directory, 'thumbnail')

if not os.path.exists(picture_directory):
    os.makedirs(picture_directory)
if not os.path.exists(MRNo_directory):
    os.makedirs(MRNo_directory)
if not os.path.exists(thumbnail_dir):
    os.makedirs(thumbnail_dir)

def get_image_date(image_path):
    try:
        with Image.open(image_path) as img:
            img.thumbnail((10, 10))
            exif_data = img._getexif()
            if exif_data is not None:
                for tag, value in exif_data.items():
                    if TAGS.get(tag) == 'DateTimeOriginal':
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").date()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
    creation_time = os.path.getmtime(image_path)
    return datetime.fromtimestamp(creation_time).date()

# 画像ファイル名を取得
image_files = [f for f in os.listdir(thumbnail_dir) if f.endswith((".webp", ".jpg", ".jpeg", ".png"))]

# 撮影日別に画像を分類
date_groups = {}
for image_file in image_files:
    image_path = os.path.join(thumbnail_dir, image_file)
    date_taken = get_image_date(image_path)
    if date_taken:
        if date_taken not in date_groups:
            date_groups[date_taken] = []
        date_groups[date_taken].append(image_path)

images = []
# 日付とクリックした番号、ディレクトリを紐づける
files_dir = []
for date_taken, item_images in sorted(date_groups.items(), reverse=True):
    formatted_date = date_taken.strftime("%Y/%m/%d") 
    st.subheader(f" {formatted_date}")

    images = []  # リセットして日付ごとの画像を保持する
    for file in item_images:  # item_images はその日付に関連付けられた画像リストファイルパスを組み立てる
        with open(file, "rb") as image:
            encoded = base64.b64encode(image.read()).decode()
            images.append(f"data:image/jpeg;base64,{encoded}")
        files_dir.append([date_taken, file])

    # 各日付の画像を表示
    clicked = clickable_images(
        images,
        titles=[file],
        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap", "overflow": "auto"},
        img_style={"margin": "5px", "height": "80px"},
    )
    # クリックされた場合、選択された画像をセッションステートに保存
    if clicked > -1:
        i = 0
        for dir in files_dir:
            if dir[0] == date_taken:
                if i == clicked:
                    os_pass = dir[1]
                    st.session_state.os_pass = os_pass
                    break
                else:
                    i += 1
        #st.session_state.selected_image = images[clicked]
        #st.session_state.clicked = clicked
        #st.session_state.selected_image_directory = files_dir.replace("\\thumbnail" ,"")
        #st.session_state.clicked_date = date_taken
        st.switch_page("pages/detail_picture.py")

import streamlit as st
import sqlite3
import os
import utils.func
import base64
from io import BytesIO
from pathlib import Path
from streamlit_float import *
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
import numpy as np
import piexif

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

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False 
if "comment_delete" not in st.session_state:
    st.session_state.comment_delete = False 
if "rotate" not in st.session_state:
    st.session_state.rotate = False 
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = False 

pic = st.session_state.os_pass.replace("\\thumbnail" ,"")
if st.session_state.rotate == False: 
    st.image(st.session_state.os_pass.replace("\\thumbnail" ,""))

# コメント削除2
def delete_comment_picdel(photo_name):
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM comments
        WHERE photo_name = ?
    """, (photo_name,))
    conn.commit()
    conn.close()


@st.dialog("menu",width="small")
def menu():
    with st.container():
        if st.button("写真を削除",type="primary",use_container_width=True):
            st.session_state.delete_confirm  = True
            st.rerun()
        if st.button("コメントを編集・削除",use_container_width=True):
            st.session_state.comment_delete  = True
            st.rerun()
        with open(st.session_state.os_pass.replace("\\thumbnail", ""),"rb") as file:
            btn =  st.download_button(
                label="画像をダウンロード",
                data=file,
                file_name=Path(pic).name,
                mime="image/png",
                use_container_width=True,
            )
            if btn:
                st.rerun()
        if st.button("写真を回転",use_container_width=True):
            st.session_state.rotate  = True
            st.rerun()
        if st.button("メラノーマ診断",use_container_width=True):
            st.session_state.diagnosis  = True
            st.rerun()


@st.dialog("削除確認",width="small")
def delete_confirm():
    st.session_state.delete_confirm = False
    st.text("写真を削除します。よろしいですか？")
    if st.button("削除",type="primary",use_container_width=True):
        os.remove(st.session_state.os_pass)
        os.remove(pic)
        delete_comment_picdel(pic)
        st.session_state.selected_image = None
        st.switch_page("pages/photo_manager.py")
    if st.button("キャンセル",use_container_width=True):
        st.rerun()

if st.session_state.delete_confirm == True:
    delete_confirm()


@st.dialog("悪性診断",width="small")
def diagnosis_confirm():
    st.session_state.diagnosis = False

    # モデルの読み込み
    model = load_model("assets\\my_model.h5")
    class_names = ["良性", "悪性"]  # クラス名を手動で入力

    # 画像を読み込んで前処理
    image = load_img(st.session_state.os_pass.replace("\\thumbnail" ,""), target_size=(224, 224))
    input_array = img_to_array(image) / 255.0
    input_array = np.expand_dims(input_array, axis=0)

    # 予測
    predictions = model.predict(input_array)
    predicted_class = class_names[np.argmax(predictions)]
    confidence = np.max(predictions)

    # 結果を表示
    st.write(f"予測されたクラス: {predicted_class}")
    st.write(f"確信度: {confidence:.2f}")
    st.write("注意：適切な診断は皮膚科専門医を受診してください")

    if st.button("OK",use_container_width=True):
        st.rerun()

if st.session_state.diagnosis == True:
    diagnosis_confirm()

if st.session_state.rotate == False: 
    # クローズボタン
    button_container = st.container()
    with button_container:
        option_map = {
            0: ":material/Close:",
        }
        selection_left = st.pills("back",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            label_visibility="hidden",
        )
        if selection_left == 0:
            st.switch_page("pages/photo_manager.py")
    button_css = float_css_helper(width="1rem", left="2rem", top='5.5rem', transition=0)
    button_container.float(button_css)

    # メニューボタン
    button_container2 = st.container()
    with button_container2:

        if st.button(":material/Menu:"):

            menu()

    button_css2 = float_css_helper(width="1rem", right="2.3rem", top='7rem', transition=0)
    button_container2.float(button_css2)
else:
    # メニューボタン
    # 画像を読み込む
    image = Image.open(st.session_state.os_pass.replace("\\thumbnail" ,""))
    image_thumb = Image.open(st.session_state.os_pass)

    # 回転した画像を保存するための状態管理
    if "rotated_image" not in st.session_state:
        st.session_state.rotated_image = image
    if "rotated_image_thumb" not in st.session_state:
        st.session_state.rotated_image_thumb = image_thumb

    # 回転ボタン
    button_container3 = st.container()
    with button_container3:

        if st.button(":material/rotate_right:"):
            # 画像を回転させる
            st.session_state.rotated_image = st.session_state.rotated_image.rotate(-90)  # 90度回転
            st.session_state.rotated_image_thumb = st.session_state.rotated_image_thumb.rotate(-90)  # 90度回転
    button_css3 = float_css_helper(width="1rem", right="12rem", bottom='7rem', transition=0)
    button_container3.float(button_css3)

    # クローズボタン
    button_container4 = st.container()
    with button_container4:
        option_map = {
            0: ":material/Close:",
        }
        selection_left = st.pills("back",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            label_visibility="hidden",
        )
        if selection_left == 0:
            st.session_state.rotate = False
            st.rerun()
    button_css4 = float_css_helper(width="1rem", left="2rem", top='5.5rem', transition=0)
    button_container4.float(button_css4)

    # 保存ボタン
    button_container4 = st.container()
    with button_container4:
        if st.button("保存"):
            st.session_state.rotate = False
            # 回転後の画像を元のファイルに上書き保存
            st.session_state.rotated_image.save(st.session_state.os_pass.replace("\\thumbnail" ,""))
            st.session_state.rotated_image_thumb.save(st.session_state.os_pass)
            st.rerun()
    button_css4 = float_css_helper(width="1rem", right="3rem", top='7rem', transition=0)
    button_container4.float(button_css4)

    # 回転後の画像を再表示
    if st.session_state.rotated_image != image:
        st.image(st.session_state.rotated_image, use_container_width=True)
    else:
        # 画面に画像を表示
        st.image(st.session_state.rotated_image, use_container_width=True)

# コメント用sql処理
# データベース初期化
def init_db():
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            photo_name TEXT,
            comment TEXT,
            created TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP,'localtime'))
        )
    """)
    conn.commit()
    conn.close()

# コメント保存
def save_comment(customer_id, photo_name, comment):
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comments (customer_id, photo_name, comment)
        VALUES (?, ?, ?)
    """, (customer_id, photo_name, comment))
    conn.commit()
    conn.close()

# コメント取得
def get_comments(photo_name):
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT comment, created FROM comments  
        WHERE photo_name = ?
        ORDER BY created DESC
    """, (photo_name,))
    comments = cursor.fetchall()
    conn.close()
    return [(comment, created) for comment, created in comments] 

# コメント削除
def delete_comment(photo_name, created):
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM comments
        WHERE photo_name = ? AND created = ?
    """, (photo_name, created))
    conn.commit()
    conn.close()


# コメント更新
def update_comment(photo_name, created, new_comment):
    conn = sqlite3.connect("comments.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE comments
        SET comment = ?
        WHERE photo_name = ? AND created = ?
    """, (new_comment, photo_name, created))
    conn.commit()
    conn.close()

# 初期化
init_db()

# コメント表示と入力
comments = get_comments(pic)
if st.session_state.comment_delete == False:
    for comment, timestamp in comments:
        with st.chat_message("user"):
            st.write(comment + f"　　(投稿日: {timestamp})")
else:
    st.write("")
    if st.button("コメントの編集・削除を終了"):
        st.session_state.comment_delete = False
        st.rerun()
    i = 0
    for comment, timestamp in comments:
        col1=st.container(border = True)
        with col1:
            with st.chat_message("user"):
                st.write(comment + f"　　(投稿日: {timestamp})")
        #with col2:
            option_map = {
                0: ":material/edit:",
                1: ":material/delete:",
            }
            selection = st.pills("comment_edit",
                options=option_map.keys(),
                format_func=lambda option: option_map[option],
                selection_mode="single",
                label_visibility="hidden",
                key=i,
            )
            if selection == 0:
                # 編集処理
                changed_comment =  st.text_input("コメント編集",value=comment)
                if  comment != changed_comment:
                    update_comment(pic, timestamp, changed_comment)
                    st.session_state.comment_delete = False
                    st.rerun()

            elif selection == 1:
                delete_comment(pic, timestamp)
                st.session_state.comment_delete = False
                st.rerun()
            i += 1

#コメント処理
if st.session_state.comment_delete == False:
    comment = st.chat_input("コメントを追加")
    if comment:
            print(pic)
            save_comment(st.session_state.PatientID, pic, comment)
            st.rerun()
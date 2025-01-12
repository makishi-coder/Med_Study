import streamlit as st
import sqlite3
import os
import utils.func
from streamlit_float import *

utils.func.set_tab()
utils.func.set_header()
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False 
if "comment_delete" not in st.session_state:
    st.session_state.comment_delete = False 

@st.dialog("menu",width="small")
def menu():
    with st.container():
        if st.button("写真を削除",type="primary",use_container_width=True):
            st.session_state.delete_confirm  = True
            st.rerun()
        if st.button("コメントを編集・削除",use_container_width=True):
            st.session_state.comment_delete  = True
            st.rerun()                         
        #if st.button("撮影日時を変更（未実装）",use_container_width=True):
        #    pass
        #if st.button("ダウンロード（未実装）",use_container_width=True):
        #    pass


@st.dialog("削除確認",width="small")
def delete_confirm():
    st.session_state.delete_confirm = False
    st.text("写真を削除します。よろしいですか？")
    if st.button("削除",type="primary",use_container_width=True):
        os.remove(st.session_state.os_pass)
        thumbnail = st.session_state.os_pass.replace(st.session_state["PatientID"] ,st.session_state["PatientID"] +"\\thumbnail")
        print(thumbnail)
        os.remove(thumbnail)
        st.session_state.selected_image = None
        st.switch_page("pages/photo_manager.py")
    if st.button("キャンセル",use_container_width=True):
        st.rerun()

if st.session_state.delete_confirm == True:
    delete_confirm()


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

os_pass =""
#i = 0
#for dir in st.session_state.selected_image_directory:
#    if dir[0] == st.session_state.clicked_date:
#        if i == st.session_state.clicked:
#            os_pass = dir[1]
#            st.session_state.os_pass = os_pass
#            break
#        else:
#            i += 1
st.image(st.session_state.os_pass.replace("\\thumbnail" ,""))

# コメント表示と入力
comments = get_comments(os_pass)
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
                    update_comment(os_pass, timestamp, changed_comment)
                    st.session_state.comment_delete = False
                    st.rerun()

            elif selection == 1:
                delete_comment(os_pass, timestamp)
                st.session_state.comment_delete = False
                st.rerun()
            i += 1

#コメント処理
if st.session_state.comment_delete == False:
    comment = st.chat_input("コメントを追加")
    if comment:
            save_comment(st.session_state.PatientID, os_pass, comment)
            st.rerun()
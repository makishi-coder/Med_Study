import streamlit as st
import os
import base64
import sqlite3
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from streamlit_image_select import image_select
from st_clickable_images import clickable_images
from pathlib import Path

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

# 初期化
init_db()

# Supportive Aid for Needs in Global Operations by Photo management system
st.title("SangoPhoto")

if st.button("診療番号取得"):
    st.text("test1")

def reset_seletection():
    selection = ""

medical_record_no = st.text_input("診療番号を入力してください", value="00000001",on_change=reset_seletection)

# Pythonファイルがあるディレクトリを取得
current_directory = os.path.dirname(os.path.abspath(__file__))

picture_directory = os.path.join(current_directory, 'assets', 'Picture')
if not os.path.exists(picture_directory):
    os.makedirs(picture_directory)

# 診療番号フォルダのパスを取得
MRNo_directory = os.path.join(picture_directory, medical_record_no)
if not os.path.exists(MRNo_directory):
    os.makedirs(MRNo_directory)

if medical_record_no != "":
    # 機能を選択
    options = ["追加", "一覧表示"]
    selection = st.segmented_control(
        "機能を選択してください", options, selection_mode="single")

    if selection == '追加':
        # ファイルアップロード
        uploaded_file = st.file_uploader("カメラで写真を撮影またはアップロードしてください",
                                        type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # ユニークなファイル名を作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{uploaded_file.name}"
            file_path = os.path.join(MRNo_directory, unique_filename)

            # 画像を保存
            with Image.open(uploaded_file) as image:
                image.save(file_path)
            st.success(f"Image saved to {file_path}")
            st.image(file_path, caption="Uploaded Image", use_column_width=True)
            st.empty()

    elif selection == '一覧表示':
            if not os.path.exists(MRNo_directory):
                os.makedirs(MRNo_directory)

            def get_image_date(image_path):
                try:
                    with Image.open(image_path) as img:
                        exif_data = img._getexif()
                        if exif_data is not None:
                            for tag, value in exif_data.items():
                                if TAGS.get(tag) == 'DateTimeOriginal':
                                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").date()
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                creation_time = os.path.getctime(image_path)
                return datetime.fromtimestamp(creation_time).date()

            # 画像ファイル名を取得
            image_files = [f for f in os.listdir(MRNo_directory) if f.endswith((".png", ".jpg", ".jpeg"))]

            # 撮影日別に画像を分類
            date_groups = {}
            for image_file in image_files:
                image_path = os.path.join(MRNo_directory, image_file)
                date_taken = get_image_date(image_path)
                if date_taken:
                    if date_taken not in date_groups:
                        date_groups[date_taken] = []
                    date_groups[date_taken].append(image_path)

            # セッションステートを使用して状態を保持
            if "selected_image" not in st.session_state:
                st.session_state.selected_image = None

            if st.session_state.selected_image is None:
                images = []
                #日付とクリックした番号、ディレクトリを紐づける
                files_dir = []
                for date_taken, item_images in sorted(date_groups.items(), reverse=True):
                    st.subheader(f"日付: {date_taken}")

                    images = []  # リセットして日付ごとの画像を保持する
                    for file in item_images:  # item_images はその日付に関連付けられた画像リストファイルパスを組み立てる
                        with open( file, "rb") as image:
                            encoded = base64.b64encode(image.read()).decode()
                            images.append(f"data:image/jpeg;base64,{encoded}")
                        files_dir.append([date_taken,file])

                    # 各日付の画像を表示
                    clicked = clickable_images(
                        images,
                        titles=[file],
                        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
                        img_style={"margin": "5px", "height": "200px"},
                    )
                    # クリックされた場合、選択された画像をセッションステートに保存
                    if clicked > -1:
                        st.session_state.selected_image = images[clicked]
                        st.session_state.clicked = clicked
                        st.session_state.selected_image_directory = files_dir
                        st.session_state.clicked_date = date_taken
                        st.rerun()

            else:
                #日付の何番目のファイルを処理したか取得し、それに紐づくdirを取得する
                os_pass =""
                for dir in st.session_state.selected_image_directory:
                    i = 0
                    if dir[0] == st.session_state.clicked_date:
                        if i == st.session_state.clicked:
                            os_pass = dir[1]
                            break
                        else:
                            i += 1
                # セッション状態の初期化
                if "delete_confirm" not in st.session_state:
                    st.session_state.delete_confirm = False 
                if "comment_delete" not in st.session_state:
                    st.session_state.comment_delete = False 
                
                # 「戻る」ボタンを表示
                if st.button("写真一覧に戻る"):
                    st.session_state.selected_image = None  # 選択状態をリセット
                    st.rerun()
                st.subheader(f"日付: {st.session_state.clicked_date}")

                @st.dialog("menu",width="small")
                def menu():
                    with st.container():
                        if st.button("写真を削除",type="primary",use_container_width=True):
                            st.session_state.delete_confirm  = True
                            st.rerun()
                        if st.button("コメントを削除",use_container_width=True):
                            st.session_state.comment_delete  = True
                            st.rerun()                         
                        if st.button("撮影日時を変更（未実装）",use_container_width=True):
                            pass
                        if st.button("ダウンロード（未実装）",use_container_width=True):
                            pass

                # ポップアップを開くボタン
                if st.button("menu"):
                    menu()

                @st.dialog("削除確認",width="small")
                def delete_confirm():
                    st.session_state.delete_confirm = False
                    st.text("写真を削除します。よろしいですか？")
                    if st.button("削除",type="primary",use_container_width=True):
                        os.remove(os_pass)
                        st.session_state.selected_image = None
                        st.rerun()
                    if st.button("キャンセル",use_container_width=True):
                        st.rerun()

                if st.session_state.delete_confirm == True:
                    delete_confirm()

                st.markdown(
                    f"""
                    <div style="text-align: center;">
                        <img src="{st.session_state.selected_image}" style="width: 100%; max-width: 100%; height: auto;"/>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # コメント表示と入力
                comments = get_comments(os_pass)
                if st.session_state.comment_delete == False:
                    for comment, timestamp in comments:
                        st.write(f"- {comment} (投稿日: {timestamp})")
                else:
                    i = 0
                    for comment, timestamp in comments:
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            st.write(f"- {comment} (投稿日: {timestamp})")
                        with col2:
                            if st.button("",icon=":material/delete_forever:",key=i):
                                delete_comment(os_pass, timestamp)
                                st.session_state.comment_delete = False
                                st.rerun()
                            i += 1
                #コメント処理
                comment = st.chat_input("コメントを追加")
                if comment:
                        save_comment(medical_record_no, os_pass, comment)
                        st.rerun()
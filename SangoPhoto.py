import streamlit as st
import os
import base64
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from streamlit_image_select import image_select
from st_clickable_images import clickable_images

# Supportive Aid for Needs in Global Operations by Photo management system
st.title("SangoPhoto")

if st.button("診療番号取得"):
    st.text("test1")

medical_record_no = st.text_input("診療番号を入力してください", value="00000001")

# Pythonファイルがあるディレクトリを取得
current_directory = os.path.dirname(os.path.abspath(__file__))
picture_directory = os.path.join(current_directory, 'assets', 'Picture')
if not os.path.exists(picture_directory):
    os.makedirs(picture_directory)

# 診療番号フォルダのパスを取得
MRNo_directory = os.path.join(picture_directory, medical_record_no)
if not os.path.exists(MRNo_directory):
    os.makedirs(MRNo_directory)

# セレクトボックスで機能を選択
option = st.selectbox(
    '機能を選択してください:',
    ['追加', '一覧表示']
)

if option == '追加':
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

elif option == '一覧表示':
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

        # # 撮影日別に画像を表示
        # for date_taken, item_images in sorted(date_groups.items(), reverse=True):
        #     st.subheader(f"日付: {date_taken}")

        #     # 画面幅
        #     container_width = st.container().width
        #     cols = st.columns(5)

        # セッションステートを使用して状態を保持
        if "selected_image" not in st.session_state:
            st.session_state.selected_image = None

        if st.session_state.selected_image is None:
            images = []
            for date_taken, item_images in sorted(date_groups.items(), reverse=True):
                st.subheader(f"日付: {date_taken}")

                images = []  # リセットして日付ごとの画像を保持する
                for file in item_images:  # item_images はその日付に関連付けられた画像リストファイルパスを組み立てる
                    with open( file, "rb") as image:
                        encoded = base64.b64encode(image.read()).decode()
                        images.append(f"data:image/jpeg;base64,{encoded}")

                # 各日付の画像を表示
                clicked = clickable_images(
                    images,
                    titles=[f"Image #{str(i)}" for i in range(len(images))],
                    div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
                    img_style={"margin": "5px", "height": "200px"},
                )
                # クリックされた場合、選択された画像をセッションステートに保存
                if clicked > -1:
                    st.session_state.selected_image = images[clicked]
                    break  # 一つ選択されたらループを抜ける
        else:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <img src="{st.session_state.selected_image}" style="width: 100%; max-width: 100%; height: auto;"/>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # 「戻る」ボタンを表示
            if st.button("戻る"):
                st.session_state.selected_image = None  # 選択状態をリセット

            #st.markdown(f"Image #{clicked} clicked" if clicked > -1 else "No image clicked")

        # for date_taken, item_images in sorted(date_groups.items(), reverse=True):
        #     st.subheader(f"日付: {date_taken}")

        #     for file in image_files:
        #         with open(MRNo_directory +"\\"+ file, "rb") as image:
        #             encoded = base64.b64encode(image.read()).decode()
        #             images.append(f"data:image/jpeg;base64,{encoded}")

        #     clicked = clickable_images(
        #         images,
        #         titles=[f"Image #{str(i)}" for i in range(len(images))],
        #         div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
        #         img_style={"margin": "5px", "height": "200px"},
        #     )

        # st.markdown(f"Image #{clicked} clicked" if clicked > -1 else "No image clicked")
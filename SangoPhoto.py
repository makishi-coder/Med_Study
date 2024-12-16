import streamlit as st
import os
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


# セッション状態に画像が保存されていなければ、アップロードを許可
if 'image' not in st.session_state:
    st.session_state.image = None

# ファイルアップロード
uploaded_file = st.file_uploader("カメラで写真を撮影またはアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.session_state.image = Image.open(uploaded_file)
    
    # ユニークなファイル名を作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(MRNo_directory, unique_filename)

    # 画像を保存
# アップロードされた画像を表示
if st.session_state.image is not None:
    
    with Image.open(uploaded_file) as image:
        image.save(file_path)
    print("AAAA image_saved")
    st.success(f"Image saved to {file_path}")
    # st.image(file_path, caption="Uploaded Image", use_column_width=True)

if st.button("写真一覧表示"):
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

    # 撮影日別に画像を表示
    for date_taken, item_images in sorted(date_groups.items(), reverse=True):
        st.subheader(f"日付: {date_taken}")

        # 画面幅
        container_width = st.container().width
        cols = st.columns(5)

        for i, image_path in enumerate(item_images):
            with cols[i % 5]:
                with Image.open(image_path) as image:
                    # 画像を表示（縦横比を保持）し、最大幅を指定
                    st.image(image, use_container_width=True)

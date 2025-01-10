import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
from st_aggrid.shared import JsCode
import base64
from streamlit_float import *


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

# データフレームの準備
df = pd.DataFrame({
    'PatientID': ['0000001', '0000002', '0000003', '0000004'],  # 患者IDを追加
    'Name': ['Iron Man', 'Walter White', 'Wonder Woman', 'Bat Woman'],
    'ImgLocation': ['Local', 'Local', 'Web', 'Web'],
    'ImgPath': ['assets/Picture/0000001/20250107_155511_image.jpg', 
                'C:\\Users\\Rei Makishi\\github\\Med_Study\\assets\\Picture\\0000001\\20250107_155530_image.jpg', 
                'https://i.pinimg.com/originals/ab/26/c3/ab26c351e435242658c3783710e78163.jpg',
                'https://img00.deviantart.net/85f5/i/2012/039/a/3/batwoman_headshot_4_by_ricber-d4p1y86.jpg']
})

# ローカル画像をBase64に変換
for i, row in df.iterrows():
    if row['ImgLocation'] == 'Local':
        imgExtn = row['ImgPath'][-3:]
        row['ImgPath'] = f"data:image/{imgExtn};base64," + ReadPictureFile(row['ImgPath'])

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
if "PatientID" not in st.session_state:
    st.session_state["PatientName"] = None

if response['selected_rows'] is not None:
    st.session_state["PatientID"] = response['selected_rows']['PatientID'].iloc[0]
    st.session_state["PatientName"] = response['selected_rows']['Name'].iloc[0]
    st.switch_page("pages/photo_manager.py")

button_container = st.container()
with button_container:
    if st.button("👤✚", type="secondary"):
        st.switch_page("app.py")
button_css = float_css_helper(width="2.2rem", right="2rem", bottom='1rem', transition=0)
button_container.float(button_css)

import streamlit as st
from streamlit_quill import st_quill

import arcadians_members.utils as am_utils
from arcadians_members.aws import sdb_write

texts = am_utils.get_texts(__file__)


def notice_diag():
    st.info(texts["info"])
    # "The latest notice is displayed on the main members page, when a new message is added the ")
    # Docs here: https://okld-gallery.streamlit.app/?p=quill-editor
    content = st_quill(placeholder="Only complete if you want to add a new notice.", html=True)
    if len(content) == 0:
        st.stop()

    st.expander("Preview", expanded=True).write(content, unsafe_allow_html=True)
    submitted = st.button("Submit notice")
    if submitted:
        sdb_write("notice", [{"Notice": content}])

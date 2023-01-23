import streamlit as st
from streamlit_quill import st_quill

import arcadians_members.utils as am_utils
from arcadians_members.aws import sdb_write

texts = am_utils.get_texts(__file__)


def notice_diag():
    st.info(texts["info"])
    col_a, col_b = st.columns(2)
    with col_a:
        # Docs here: https://okld-gallery.streamlit.app/?p=quill-editor
        content = st_quill(placeholder="Only complete if you want to add a new notice.", html=True)

        if len(content) >= 1048576:
            st.error(f"Notices have a maximum size of 1MB at this time, photos are generally the cause of this error.")
            st.stop()

    # col_a, col_b = st.columns([5,1])
    with col_b:
        st.expander("Preview", expanded=True).write(content, unsafe_allow_html=True)
        submit_disabled = True
        if content != "<p><br></p>":
            submit_disabled = False

        submitted = col_b.button("Submit notice", disabled=submit_disabled)
        if submitted:
            sdb_write("notice", [{"Notice": content}])

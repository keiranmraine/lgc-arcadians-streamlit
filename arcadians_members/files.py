import streamlit as st

import arcadians_members.utils as am_utils

# texts = am_utils.get_texts(__file__)


def load_existing_sdb(field: str):
    # dummy function until sdb hooked up
    return ["Select...", "Add new performance"]


def file_upload():
    st.write("file upload")
    performance = st.selectbox("Assign files to performance", options=load_existing_sdb("performance"))
    if performance == "Select...":
        st.stop()
    if performance == "Add new performance":
        performance = st.text_input("New name")
    if len(performance) == 0:
        st.stop()
    file_count = st.slider("Number of files to upload", min_value=1, max_value=10)
    (c_ftype, c_part, c_file) = st.columns([1, 2, 4])
    c_ftype.write("Type")
    c_part.write("Description")
    c_file.write("File to upload")
    for i in range(0, file_count):
        (c_ftype, c_part, c_file) = st.columns([1, 2, 4])
        c_ftype.radio("File type", ["null", "Audio", "Score"], label_visibility="hidden", key=f"type_{i}")
        c_part.text_input("Description", label_visibility="hidden", key=f"part_{i}")
        c_file.file_uploader("File to upload", label_visibility="hidden", key=f"file_{i}")

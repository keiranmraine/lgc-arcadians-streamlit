import subprocess

import streamlit as st

import arcadians_members.aws as am_aws
import arcadians_members.utils as am_utils

texts = am_utils.get_texts(__file__)


def build():
    with st.spinner("Pulling notice data"):
        notice_items = am_aws.sdb_content("notice")
    st.write(notice_items)
    st.success("Notice data retrieved")
    with st.spinner("Pulling file data"):
        file_items = am_aws.sdb_content("file")
    st.write(file_items)
    st.success("File data retrieved")
    with st.spinner("Building site"):
        subprocess.run("mkdocs build -d site ")
    st.success("Site has built successfully")
    # spinner for s3 deploy


def generate():
    st.info(texts["intro"])
    if st.button("Deploy"):
        build()

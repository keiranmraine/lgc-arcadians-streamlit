import os
import subprocess
import sys

import streamlit as st
import streamlit.components.v1 as components

import arcadians_members.aws as am_aws
import arcadians_members.site as am_site
import arcadians_members.utils as am_utils

texts = am_utils.get_texts(__file__)


def build():
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.spinner("Pulling notice data"):
            notice_items = am_aws.sdb_content("notice")
        st.success("Notice data retrieved")
    with col_b:
        with st.spinner("Pulling file data"):
            file_items = am_aws.sdb_content("file")
        st.success("File data retrieved")
    with col_c:
        with st.spinner("Building site"):
            am_site.build_site(notice_items, file_items)
            subprocess.run("mkdocs build -d site".split())
        st.success("Site has built successfully")

    st.info(texts["intro"])
    deploy = st.button("Deploy")

    if deploy:
        am_utils.kill_server()
        am_aws.sync()
    else:
        p = subprocess.Popen("python -m http.server -d site 9001".split())
        st.session_state["server_pid"] = p.pid
        components.iframe("http://localhost:9001/", height=1200)

    return deploy


def generate():
    deploy = build()
    if deploy:
        st.write("deploying")

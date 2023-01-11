import os
import subprocess
import sys

import streamlit as st

import arcadians_members.aws as am_aws
import arcadians_members.site as am_site
import arcadians_members.utils as am_utils

texts = am_utils.get_texts(__file__)


def build():
    with st.spinner("Pulling notice data"):
        notice_items = am_aws.sdb_content("notice")
    # st.write(notice_items)
    st.success("Notice data retrieved")
    with st.spinner("Pulling file data"):
        file_items = am_aws.sdb_content("file")
    # st.write(file_items)
    st.success("File data retrieved")
    # st.write(os.getcwd())
    with st.spinner("Building site"):
        am_site.build_site(notice_items, file_items)
        subprocess.run("mkdocs build -d site")
    st.success("Site has built successfully")
    # spinner for s3 deploy

    st.info(texts["intro"])
    deploy = st.button("Deploy")

    if deploy:
        am_utils.kill_server()
    else:
        # output = subprocess.check_output("python -m http.server -d site 9001 >& /dev/null &; echo $!", shell=True)
        p = subprocess.Popen("python -m http.server -d site 9001".split())
        st.session_state["server_pid"] = p.pid
        st.write(
            f'<iframe src="http://localhost:9001/" width=100% height="1200px"></iframe>',
            unsafe_allow_html=True,
        )
    return deploy


def generate():
    deploy = build()
    if deploy:
        st.write("deploying")

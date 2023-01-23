import streamlit as st

import arcadians_members.utils as am_utils
from arcadians_members.files import file_upload
from arcadians_members.notices import notice_diag
from arcadians_members.update import generate

texts = am_utils.get_texts(__file__)

st.set_page_config(page_title="Letchworth Arcadians Admin", layout="wide")
am_utils.inject_css()  # primarily to handle radio-select limitations

st.markdown(texts["intro"])

st.write("Please login to proceed")
col_a, col_b = st.columns(2)
u_n = col_a.text_input("User")
p_w = col_b.text_input("Password", type="password")

if len(u_n) > 0 and len(p_w) > 0:
    if am_utils.validate(u_n, p_w) is False:
        st.error("Invalid user/password")
        st.stop()
else:
    st.stop()

st.markdown("----")

(c1, c2) = st.columns(2)
update_mode = c1.radio("What do you want to do?", ["null", "Add Files", "Add Notice", "Update Site"], horizontal=True)
c2.expander("Help", expanded=False).markdown(texts["mode_help"])

st.markdown("----")

if update_mode == "null":
    am_utils.kill_server()
    st.stop()
if update_mode == "Add Notice":
    am_utils.kill_server()
    notice_diag()
elif update_mode == "Add Files":
    am_utils.kill_server()
    file_upload()
elif update_mode == "Update Site":
    am_utils.kill_server()
    generate()
else:
    st.error(f"Unknown radio button option '{update_mode}'")
    st.stop()

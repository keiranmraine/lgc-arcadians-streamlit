import streamlit as st

import arcadians_members.utils as am_utils
from arcadians_members.files import file_upload
from arcadians_members.notices import notice_diag
from arcadians_members.update import generate

texts = am_utils.get_texts(__file__)

st.set_page_config(page_title="Letchworth Arcadians Admin", layout="wide")
am_utils.inject_css()  # primarily to handle radio-select limitations

st.markdown(texts["intro"])
(c1, c2) = st.columns(2)
update_mode = c1.radio("What do you want to do?", ["null", "Add files", "Add notice", "Update Site"], horizontal=True)
c2.expander("Help", expanded=False).markdown(texts["mode_help"])

st.markdown("----")

if update_mode == "null":
    st.stop()
if update_mode == "Add notice":
    notice_diag()
elif update_mode == "Add files":
    file_upload()
elif update_mode == "Update Site":
    generate()
else:
    st.error(f"Unknown radio button option '{update_mode}'")
    st.stop()

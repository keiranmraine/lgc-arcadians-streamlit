from hashlib import md5

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
    st.markdown("----")
    (c_ftype, c_part, c_file) = st.columns([1, 2, 4])
    c_ftype.write("Type")
    c_part.write("Description")
    c_file.write("File to upload")
    file_map = {}
    for i in range(0, file_count):
        (c_ftype, c_part, c_file) = st.columns([1, 2, 4])
        file_map[f"type_{i}"] = c_ftype.radio(
            "File type", ["null", "Audio", "Score"], label_visibility="hidden", key=f"type_{i}"
        )
        file_map[f"part_{i}"] = c_part.text_input("Description", label_visibility="hidden", key=f"part_{i}")
        file_map[f"file_{i}"] = c_file.file_uploader("File to upload", label_visibility="hidden", key=f"file_{i}")

    clean_map = {}
    md5digests = {}
    md5clash = 0
    if st.button("Check files"):
        for k, v in file_map.items():
            (group, i) = k.split("_")
            i = int(i)
            if i not in clean_map:
                clean_map[i] = {}
            if group == "type":
                if v != "null":
                    clean_map[i][group] = v
            elif group == "part":
                if len(v) > 0:
                    clean_map[i][group] = v
            elif group == "file":
                if v is not None:
                    clean_map[i][group] = v
                    st.write(v)
                    digest = md5(v.getvalue()).hexdigest()
                    if digest in md5digests:
                        md5digests[digest].append(i + 1)
                        md5clash += 1
                    else:
                        md5digests[digest] = [i + 1]  # for ease of display
    else:
        st.stop()

    issues = []
    for row, maps in clean_map.items():
        if len(maps) != 3:
            issues.append(f"- Skipped row {row+1} as a field is blank or no file has been selected")
            continue

    if md5clash > 0:
        for rows in md5digests.values():
            if len(rows) > 1:
                issues.append(f"- Rows '{', '.join(map(str, rows))}' have identical files")

    if len(issues) > 0:
        st.error("Errors have been detected in the above file information:\n\n" + "\n".join(issues))
        st.stop()

    if st.button("Write files"):
        st.write("Upload to S3 here")

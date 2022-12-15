from hashlib import md5
from typing import List

import streamlit as st

import arcadians_members.utils as am_utils
from arcadians_members import aws

# texts = am_utils.get_texts(__file__)


def production_list() -> List[str]:
    base_list = ["Select...", "Add new production..."]
    base_list.extend(aws.sdb_get_uniq("file", "Production"))
    return base_list


def clean(instr: str) -> str:
    return instr.replace(" ", "_").replace("/", "-")


def file_upload():
    production = st.selectbox("Assign files to production", options=production_list())
    if production == "Select...":
        st.stop()
    if production == "Add new production":
        production = st.text_input("New name")
    if len(production) == 0:
        st.stop()
    file_count = st.slider("Number of files to upload", min_value=1, max_value=10)
    st.markdown("----")
    (c_ftype, c_name, c_part, c_file) = st.columns([1, 2, 2, 4])
    c_ftype.write("Type")
    c_name.write("Name")
    c_part.write("Part")
    c_file.write("File to upload")
    file_map = {}
    for i in range(0, file_count):
        (c_ftype, c_name, c_part, c_file) = st.columns([1, 2, 2, 4])
        file_map[f"type_{i}"] = c_ftype.radio(
            "File type", ["null", "Audio", "Score"], label_visibility="hidden", key=f"type_{i}"
        )
        file_map[f"name_{i}"] = c_name.text_input("Name", label_visibility="hidden", key=f"name_{i}")
        file_map[f"part_{i}"] = c_part.text_input("Description", label_visibility="hidden", key=f"part_{i}")
        file_map[f"file_{i}"] = c_file.file_uploader("File to upload", label_visibility="hidden", key=f"file_{i}")

    clean_map = {}
    md5digests = {}
    md5clash = 0
    ignore_clash = st.checkbox("Allow duplicate files?")
    if st.button("Write files"):
        for k, v in file_map.items():
            (group, i) = k.split("_")
            i = int(i)
            if i not in clean_map:
                clean_map[i] = {}
            if group == "type":
                if v != "null":
                    clean_map[i][group] = v
            elif group == "name":
                if len(v) > 0:
                    clean_map[i][group] = v
            elif group == "part":
                if len(v) > 0:
                    clean_map[i][group] = v
            elif group == "file":
                if v is not None:
                    clean_map[i][group] = v
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
        if len(maps) != 4:
            issues.append(f"- Skipped row {row+1} as a field is blank or no file has been selected")
            continue

    warnings = []
    if md5clash > 0:
        for rows in md5digests.values():
            if len(rows) > 1:
                msg = f"- Rows '{', '.join(map(str, rows))}' have identical files"
                if ignore_clash is True:
                    warnings.append(msg)
                else:
                    issues.append(msg)

    if len(issues) > 0:
        extra = ""
        if md5clash > 0:
            extra = "\nIdentical files can be allowed via the checkbox `Allow identical files?`"
        st.error("Errors have been detected in the above file information:\n\n" + "\n".join(issues) + extra)
        st.stop()

    if len(warnings) > 0:
        st.warning(
            "Identical files have been detected but allowed via `Allow identical files?` being selected\n\n"
            + "\n".join(warnings)
        )

    # convert the maps into entries for sdb
    sdb_records = []
    s3_records = []
    for f_map in clean_map.values():
        filename = f"{f_map['part']}.{f_map['file'].name.split('.')[-1]}"
        path = f"files/{clean(production)}/{clean(f_map['name'])}/{clean(filename)}"
        sdb_records.append(
            {
                "Production": production,
                "Type": f_map["type"],
                "Name": f_map["name"],
                "Part": f_map["part"],
                "Path": f"/{path}",  # as will be referenced as root of bucket & site
            }
        )
        s3_records.append({"path": path, "file": f_map["file"]})

    # order is important
    aws.s3_write(s3_records)
    aws.sdb_write("file", sdb_records)

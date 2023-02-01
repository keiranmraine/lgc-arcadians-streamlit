import os
import shutil
from datetime import datetime
from operator import itemgetter
from typing import Dict
from typing import List

import pytz
import streamlit as st
from distutils.dir_util import copy_tree

from arcadians_members.aws import dl_link


def convert_timestamp(ts_in: str) -> str:
    #  2022-12-16/15:33:25 UTC
    utc_dt = datetime.strptime(ts_in, "%Y-%m-%d/%H:%M:%S %Z")
    london_dt = utc_dt.astimezone(pytz.timezone("Europe/London"))
    return london_dt.strftime("%Y-%m-%d/%H:%M:%S")


def order_notices(notices: List[Dict[str, str]]):
    for n in notices:
        n["fmt_ts"] = convert_timestamp(n["Timestamp"])

    return sorted(notices, key=lambda n: n["fmt_ts"], reverse=True)


def notice_as_note(notice: Dict[str, str]) -> str:
    fmt_dt = notice["fmt_ts"]
    formatted = f'!!! note "Latest information <small>(posted: {fmt_dt})</small>"\n'
    for l in notice["Notice"].split("\n"):
        formatted += f"    {l}\n"
    formatted += "\nPlease see the [here](/notice_archive.html) for older messages.\n\n----\n"
    return formatted


def notice_item(notice: Dict[str, str]) -> str:
    fmt_dt = notice["fmt_ts"]
    formatted = notice["Notice"]
    formatted += f"\n<small>(posted: {fmt_dt})</small>"
    return formatted


def populate_notices(notices):
    # order and set correct timezone and format ts
    notices = order_notices(notices)

    with open("./docs/includes/current_notice.md", "w") as curr_notice:
        print(notice_as_note(notices[0]), file=curr_notice)

    with open("./docs/notice_archive.md", "w") as curr_notice:
        print("# Notice archive\n", file=curr_notice)
        first = True
        for notice in notices:
            if first is True:
                first = False
            else:
                print("\n\n----\n", file=curr_notice)
            print(notice_item(notice), file=curr_notice)


def file_tables(files):
    productions = {}
    max_ts = "0000"
    for f in files:
        prod = f["Production"]
        if prod not in productions:
            productions[prod] = []
        fmt_ts = convert_timestamp(f["Timestamp"])
        if fmt_ts > max_ts:
            max_ts = fmt_ts
        f["fmt_ts"] = fmt_ts
        productions[prod].append(f)

    with open(f"./docs/includes/file_info.md", "w") as file_md:
        dt = datetime.strptime(max_ts, "%Y-%m-%d/%H:%M:%S")
        print(f"New files were added: **{dt.strftime('%A %d %B')}**.", file=file_md)

    os.makedirs("./docs/productions/", exist_ok=True)
    for prod in productions.keys():
        with open(f"./docs/productions/{prod}.md", "w") as file_md:
            print(f"# {prod}\n", file=file_md)
            prod_files = sorted(productions[prod], key=lambda p: (p["Name"], p["Part"], p["Type"]))
            print("| Name | Part | Type | File | Added |", file=file_md)
            print("| ---- | ---- | ---- | ---- | ----- |", file=file_md)
            for pf in prod_files:

                print(
                    f"| {pf['Name']} | {pf['Part']} | {pf['Type']} | {dl_link(pf['Path'])} | {pf['fmt_ts']} |",
                    file=file_md,
                )


def build_site(notices, files):
    """
    1. Copy base files from assets/docs into root of project
    2. Add files folder, under this is $production.md
    3. Add notices folder, under this is a $yyyy.md
    """
    shutil.rmtree("site", ignore_errors=True)
    copy_tree("arcadians_members/assets/mkdocs", "./")
    populate_notices(notices)
    file_tables(files)

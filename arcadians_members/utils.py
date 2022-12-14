import os
from pathlib import Path
from typing import Dict

import streamlit as st
import yaml

BASE = Path(__file__).parent.resolve()

BLOCK_FMT_TEXT = os.path.join(BASE, "assets", "text", "{}.yaml")
BLOCK_FMT_DATA = os.path.join(BASE, "assets", "data", "{}.yaml")


def _yaml_to_dict(filename):
    yaml_dict = None
    with open(filename) as yml:
        yaml_dict = yaml.safe_load(yml)
    return yaml_dict


def inject_css():
    """
    Deal with irritating radio-button auto-select
    """
    with open(os.path.join(BASE, "assets", "css", "style.css")) as f:
        st.markdown(f"""<style>{f.read()}</style>""", unsafe_allow_html=True)


# TODO cache
def get_texts(filename) -> Dict[str, str]:
    """
    Get yaml file content with name root matching the page (filename) it corresponds to
    """
    result = Path(filename).stem
    block_text = BLOCK_FMT_TEXT.format(result.lower())
    return _yaml_to_dict(block_text)


# TODO cache
def get_data(filename):
    """
    Get yaml file content with name root matching the page (filename) it corresponds to
    """
    result = Path(filename).stem
    block_text = BLOCK_FMT_DATA.format(result.lower())
    return _yaml_to_dict(block_text)

import streamlit as st
import pyperclip 
import sys
import random
import requests
import yaml
import tempfile
import os
import pathlib
from pathlib import Path
import shutil

import json
import ast


from TextBox_translator import translate_segment_MTUOC
from TextBox_translator import translate
#from MTUOCtranslateDOCX import MTUOCtranslateDOCX
from MTUOC_tikal import Tikal

st.set_page_config(page_title="MTUOC web translator", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

st.image("MTUOC-logo.png", width=180)

text, files, docx, odt = st.tabs(["Text box", "Files", "DOCX files", "ODT files"])

with open("mtSystems.yaml") as stream:
    try:
        mtSystems = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

names = []
IP = {}
port = {}
source_suffix = {}
target_suffix = {}
strategy = {}
for system in mtSystems:
    names.append(system["name"])
    IP[system["name"]] = system["ip"]
    port[system["name"]] = system["port"]
    source_suffix[system["name"]] = system["source_suffix"]
    target_suffix[system["name"]] = system["target_suffix"]
    strategy[system["name"]] = system["strategy"]

# Initialize session state for tracking translation status
if 'file_translated' not in st.session_state:
    st.session_state['file_translated'] = False

if 'uploaded_filename' not in st.session_state:
    st.session_state['uploaded_filename'] = ""

def translate_file(traductor, totranslate, file_ext):
    """Helper function to translate the file and provide a download button."""
    with st.spinner(text="In progress..."):
        traductor.translate(totranslate)
    translated_file_path = totranslate.replace(f".{file_ext}", f".out.{file_ext}")
    translated_file_name = os.path.basename(translated_file_path)
    with open(translated_file_path, 'rb') as f:
        st.download_button('Download translated version', f, translated_file_name)
    st.session_state['file_translated'] = True

with text:
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_text_select")
    ip = IP[mt_engine]
    portMT = port[mt_engine]
    urlMTUOC = "http://" + ip + ":" + str(portMT) + "/translate"
    
    input_text = st.text_area("Enter text:", help="Enter the text you want to translate")
    translation = ""
    
    if st.button("Translate"):
        translation = translate(input_text, urlMTUOC)
    
    st.text_area("Translation:", value=translation, help="The translation will be shown here")

with files:
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_files_select")
    ip = IP[mt_engine]
    portMT = port[mt_engine]
    target_suffixMT = target_suffix[mt_engine]
    strategyT = strategy[mt_engine]
    
    traductor = Tikal()
    traductor.set_path("./okapi-linux/tikal.sh")
    traductor.set_sl(source_suffix[mt_engine])
    traductor.set_tl(target_suffix[mt_engine])
    traductor.set_srx_file("segment.srx")
    traductor.set_ip(ip)
    traductor.set_port(portMT)
    traductor.set_strategy(strategyT)
    
    script_dir = Path(__file__).parent.resolve()
    temp_dir = tempfile.TemporaryDirectory(dir=script_dir)
    
    uploaded_file = st.file_uploader(label="Upload a file", type=['doc', 'docx'], key="mt_engine_files_upload")
    
    if uploaded_file is not None:
        # Check if the uploaded file is new
        if uploaded_file.name != st.session_state['uploaded_filename']:
            st.session_state['file_translated'] = False
            st.session_state['uploaded_filename'] = uploaded_file.name
        
        totranslate = os.path.join(temp_dir.name, uploaded_file.name)
        with open(totranslate, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Only translate if the file has not been translated yet
        if not st.session_state['file_translated']:
            translate_file(traductor, totranslate, 'docx')
        
        shutil.rmtree(temp_dir.name)

with docx:
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_docx_select")
    ip = IP[mt_engine]
    portMT = port[mt_engine]
    target_suffixMT = target_suffix[mt_engine]
    strategyT = strategy[mt_engine]

    traductor = Tikal()
    traductor.set_path("./okapi-linux/tikal.sh")
    traductor.set_sl(source_suffix[mt_engine])
    traductor.set_tl(target_suffix[mt_engine])
    traductor.set_srx_file("segment.srx")
    traductor.set_okf("okf_openxml")
    traductor.set_ip(ip)
    traductor.set_port(portMT)
    traductor.set_strategy(strategyT)

    script_dir = Path(__file__).parent.resolve()
    temp_dir = tempfile.TemporaryDirectory(dir=script_dir)

    uploaded_file = st.file_uploader(label="Upload a file", type=['doc', 'docx'], key="mt_engine_docx_upload")

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state['uploaded_filename']:
            st.session_state['file_translated'] = False
            st.session_state['uploaded_filename'] = uploaded_file.name

        totranslate = os.path.join(temp_dir.name, uploaded_file.name)
        with open(totranslate, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if not st.session_state['file_translated']:
            translate_file(traductor, totranslate, 'docx')

        shutil.rmtree(temp_dir.name)

with odt:
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_odt_select")
    ip = IP[mt_engine]
    portMT = port[mt_engine]
    target_suffixMT = target_suffix[mt_engine]
    strategyT = strategy[mt_engine]

    traductor = Tikal()
    traductor.set_path("./okapi-linux/tikal.sh")
    traductor.set_sl(source_suffix[mt_engine])
    traductor.set_tl(target_suffix[mt_engine])
    traductor.set_srx_file("segment.srx")
    traductor.set_okf("okf_openxml")
    traductor.set_ip(ip)
    traductor.set_port(portMT)
    traductor.set_strategy(strategyT)

    script_dir = Path(__file__).parent.resolve()
    temp_dir = tempfile.TemporaryDirectory(dir=script_dir)

    uploaded_file = st.file_uploader(label="Upload a file", type=['odt', 'odf'], key="mt_engine_odt_upload")

    if uploaded_file is not None:
        if uploaded_file.name != st.session_state['uploaded_filename']:
            st.session_state['file_translated'] = False
            st.session_state['uploaded_filename'] = uploaded_file.name

        totranslate = os.path.join(temp_dir.name, uploaded_file.name)
        with open(totranslate, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if not st.session_state['file_translated']:
            translate_file(traductor, totranslate, 'odt')

        shutil.rmtree(temp_dir.name)

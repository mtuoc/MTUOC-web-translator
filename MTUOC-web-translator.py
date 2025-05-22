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


from TextBox_translator import translate_segment

from MTUOC_tikal_translate import Tikal

from MTUOC_cleanDOCX import DocxCleaner
from MTUOC_cleanODT import OdtCleaner

import platform


# Función auxiliar para intentar abrir un DOCX
def is_valid_docx(filepath):
    try:
        Document(filepath)
        return True
    except Exception:
        return False

# Función auxiliar para intentar abrir un ODT
def is_valid_odt(filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as odt_zip:
            if 'content.xml' in odt_zip.namelist():
                return True
            else:
                return False
    except Exception:
        return False

# Función auxiliar para eliminar todo formato de un DOCX y dejar sólo texto plano
def remove_formatting_docx(input_path, output_path):
    doc_in = Document(input_path)
    doc_out = Document()
    for para in doc_in.paragraphs:
        doc_out.add_paragraph(para.text)
    doc_out.save(output_path)

# Función auxiliar para eliminar todo formato de un ODT y dejar sólo texto plano
def remove_formatting_odt(input_path, output_path):
    # Método simple: convertir ODT -> TXT plano (si quieres hacer algo más complejo avísame)
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extract('content.xml', path='.')
    with open('content.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    # Eliminar etiquetas XML
    import re
    text = re.sub(r'<[^>]+>', '', content)
    # Crear nuevo ODT mínimo
    from odf.opendocument import OpenDocumentText
    from odf.text import P

    newdoc = OpenDocumentText()
    p = P(text=text)
    newdoc.text.addElement(p)
    newdoc.save(output_path)
    os.remove('content.xml')

def translate_file():
    filepath = file_path_entry.get()
    if not filepath or not os.path.exists(filepath):
        messagebox.showinfo("Error", "Please select a valid file path.")
        return

    filedir = os.path.dirname(filepath)
    filename = os.path.splitext(os.path.basename(filepath))[0]
    filextension = os.path.splitext(filepath)[1].lower()

    if filextension == ".docx":
        print("DOCX")
        shutil.copy(filepath, "tempfile.docx")

        cleaner = DocxCleaner()
        cleaner.clean_docx("tempfile.docx", "tempfile.clean.docx")

        traductor.translate("tempfile.clean.docx")

        if not is_valid_docx("tempfile.clean.out.docx"):
            print("Translated DOCX is invalid. Removing formatting and retrying...")
            remove_formatting_docx("tempfile.docx", "tempfile.nofmt.docx")
            cleaner.clean_docx("tempfile.nofmt.docx", "tempfile.clean.docx")
            traductor.translate("tempfile.clean.docx")

        outname = filename + ".out" + filextension
        outpath = os.path.join(filedir, outname)
        shutil.copy("tempfile.clean.out.docx", outpath)

        for temp_file in [
            "tempfile.docx", "tempfile.clean.docx", "tempfile.clean.out.docx", "tempfile.nofmt.docx"
        ]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    elif filextension in [".odt", ".odf"]:
        print("ODT")
        shutil.copy(filepath, "tempfile.odt")

        cleaner = OdtCleaner()
        cleaner.clean_odt("tempfile.odt", "tempfile.clean.odt")

        traductor.translate("tempfile.clean.odt")

        if not is_valid_odt("tempfile.clean.out.odt"):
            print("Translated ODT is invalid. Removing formatting and retrying...")
            remove_formatting_odt("tempfile.odt", "tempfile.nofmt.odt")
            cleaner.clean_odt("tempfile.nofmt.odt", "tempfile.clean.odt")
            traductor.translate("tempfile.clean.odt")

        outname = filename + ".out" + filextension
        outpath = os.path.join(filedir, outname)
        shutil.copy("tempfile.clean.out.odt", outpath)

        for temp_file in [
            "tempfile.odt", "tempfile.clean.odt", "tempfile.clean.out.odt", "tempfile.nofmt.odt"
        ]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    else:
        traductor.translate(filepath)



st.set_page_config(page_title="MTUOC web translator", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

#st.image("MTUOC-logo.png", width=180)

text, files = st.tabs(["Text box", "Files"])


with open("mtSystems.yaml") as stream:
        try:
            mtSystems = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
names=[]        
IP={}
port={}  
source_suffix={}           
target_suffix={}      
server_type={}
for system in mtSystems:
    names.append(system["name"])
    IP[system["name"]]=system["ip"]
    port[system["name"]]=system["port"]
    source_suffix[system["name"]]=system["source_suffix"]
    target_suffix[system["name"]]=system["target_suffix"]
    server_type[system["name"]]=system["server_type"]


with text:
    #st.header("Translate text")
    # Selection list for MT engine
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_text_select")
    ip = IP[mt_engine]
    portMT = port[mt_engine]
    server_type=server_type[mt_engine]
    # Text area for user input
    input_text = st.text_area("Enter text:", help="Enter the text you want to translate")
    # Placeholder for translation
    translation = ""
    # Button to trigger translation
    if st.button("Translate"):
        # Call translation function
        translation = translate_segment(input_text,server_type,ip,portMT)
    # Display translation
    translation_text_area=st.text_area("Translation:", value=translation, help="The translation will be shown here")

with files:
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_files_select")

    ip = IP[mt_engine]
    portMT = port[mt_engine]
    target_suffixMT = target_suffix[mt_engine]
    
    #####
    traductor=Tikal()
    traductor.set_path("./tikalMTUOC.sh")
    traductor.set_sl(source_suffix[mt_engine])
    traductor.set_tl(target_suffix[mt_engine])
    traductor.set_srx_file("segment.srx")
    traductor.set_ip(ip)
    traductor.set_port(portMT)

    os_name = platform.system()
    if os_name=="Linux":
        traductor.set_path("./tikalMTUOC.sh")
    if os_name=="Windows":
        traductor.set_path("tikalWin.bat")
    
    #####
    
    script_dir = Path(__file__).parent.resolve()

    with tempfile.TemporaryDirectory(dir=script_dir) as temp_dir:
        uploaded_file = st.file_uploader(label="Upload a file", key="mt_engine_files_upload")

        if uploaded_file is not None:
            totranslate = os.path.join(temp_dir, uploaded_file.name)
            with open(totranslate, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner(text="In progress..."):
                cwd = os.getcwd()
                #os.chdir(temp_dir)  # CAMBIAMOS al temp_dir
                traductor.translate(totranslate)  # solo el nombre del archivo
                #os.chdir(cwd)  # VOLVEMOS

            translated_file_path = totranslate.replace(".docx", ".out.docx")    
            translated_file_name = os.path.basename(translated_file_path)
            print(translated_file_path,translated_file_name)
            if not os.path.exists(translated_file_path):
                st.error(f"Translated file not found: {translated_file_path}")
            else:
                with open(translated_file_path, 'rb') as f:            
                    st.download_button('Download translated version', f, translated_file_name)

        



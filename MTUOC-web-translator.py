import streamlit as st
import pyperclip 
import sys
import random
import requests
import yaml
import tempfile
import os
import pathlib

import json
import ast


from TextBox_translator import translate_segment_MTUOC
from TextBox_translator import translate
from MTUOCtranslateDOCX import MTUOCtranslateDOCX

st.set_page_config(page_title="MTUOC web translator", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

st.image("MTUOC-logo.png", width=180)

tab1, tab2 = st.tabs(["Text box", "DOCX files"])


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
docxStrategy={}   
for system in mtSystems:
    names.append(system["name"])
    IP[system["name"]]=system["ip"]
    port[system["name"]]=system["port"]
    source_suffix[system["name"]]=system["source_suffix"]
    target_suffix[system["name"]]=system["target_suffix"]
    docxStrategy[system["name"]]=system["docx"]


    




with tab1:
    #st.header("Translate text")
    
    # Selection list for MT engine
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_tab1")

    ip = IP[mt_engine]
    portMT = port[mt_engine]

    urlMTUOC = "http://"+ip+":"+str(portMT)+"/translate"
    
    # Text area for user input
    input_text = st.text_area("Enter text:", help="Enter the text you want to translate")
    
    
    
    # Placeholder for translation
    translation = ""

    # Button to trigger translation
    if st.button("Translate"):
        # Call translation function
        translation = translate(input_text,urlMTUOC)

    # Display translation
    translation_text_area=st.text_area("Translation:", value=translation, help="The translation will be shown here")


with tab2:
    #st.header("Translate DOCX files")
    
    
    
    # Selection list for MT engine
    mt_engine = st.selectbox("Select MT Engine:", names, key="mt_engine_tab2")

    ip = IP[mt_engine]
    portMT = port[mt_engine]
    target_suffixMT = target_suffix[mt_engine]
    docxS=docxStrategy[mt_engine]
    
    
    temp_dir = tempfile.TemporaryDirectory()

    uploaded_file = st.file_uploader(label="Upload a file",type=['doc','docx'])
    if uploaded_file is not None:
        #st.write("filename:", uploaded_file.name)
        with open(os.path.join(pathlib.Path(temp_dir.name),uploaded_file.name),"wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.name.lower().endswith(('.doc', '.docx')):
            with st.spinner(text="In progress..."):
                output_file_path=next(tempfile._get_candidate_names())+".docx"
                #MTUOCtranslateDOCX(ip,portMT,input_path,output_path, translate_tables=True,translate_headers=True,translate_footers=True,translate_text_boxes=True)
                MTUOCtranslateDOCX(ip,portMT,os.path.join(pathlib.Path(temp_dir.name),uploaded_file.name),output_file_path,strategy=docxS)
            
            with open(output_file_path,'rb') as f:
                translated_file_name=uploaded_file.name.replace(".docx","").replace("doc","")+"-"+target_suffixMT+".docx"
                st.download_button('Download translated version', f,translated_file_name)
                
            os.remove(output_file_path)
   

#with tab3:
#   st.header("An owl")
#   st.image("https://static.streamlit.io/examples/owl.jpg", width=200)
import streamlit as st
import pyperclip 
import sys
import random
import requests
import yaml

# Function to translate text using a specific MT engine
def translate_segment_MTUOC(segment,urlMTUOC,id=101,srcLang="en-US",tgtLang="es-ES"):
    translation=""
    #segment=segment.strip()
    try:
        headers = {'content-type': 'application/json'}
        #params = [{ "id" : id},{ "src" : segment},{ "srcLang" : srcLang},{"tgtLang" : tgtLang}]
        params={}
        params["id"]=random.randint(0, 10000)
        params["src"]=segment
        params["srcLang"]=srcLang
        params["tgtLang"]=tgtLang
        response = requests.post(urlMTUOC, json=params, headers=headers)
        
        target = response.json()
        translation=target["tgt"]
    except:
        errormessage="Error retrieving translation from MTUOC: \n"+ str(sys.exc_info()[1])
        print("Error", errormessage, " in segment ", segment)
    return(translation)


def translate(text,urlMTUOC):
    translation=translate_segment_MTUOC(text,urlMTUOC)
    return(translation)

def main():
    # Text area for user input
    input_text = st.text_area("Enter text:", help="Enter the text you want to translate")
    
    with open("mtSystems.yaml") as stream:
        try:
            mtSystems = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    names=[]        
    IP={}
    port={}        
    for system in mtSystems:
        names.append(system["name"])
        IP[system["name"]]=system["ip"]
        port[system["name"]]=system["port"]

    # Selection list for MT engine
    mt_engine = st.selectbox("Select MT Engine:", names)
   
    ip = IP[mt_engine]
    port = port[mt_engine]

    urlMTUOC = "http://"+ip+":"+str(port)+"/translate"
    
    # Placeholder for translation
    translation = ""

    # Button to trigger translation
    if st.button("Translate"):
        # Call translation function
        translation = translate(input_text,urlMTUOC)

    # Display translation
    translation_text_area=st.text_area("Translation:", value=translation, help="The translation will be shown here")

if __name__ == "__main__":
    main()

import streamlit as st
import pyperclip 
import sys
import random
import requests
import yaml

def connect(server_type,server_IP,server_Port):
    if server_type=="MTUOC":
        try:
            global urlMTUOC
            urlMTUOC = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to MTUOC: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage) 
            
            
    elif server_type=="Moses":
        try:
            global proxyMoses
            proxyMoses = xmlrpc.client.ServerProxy("http://"+connecto_E_Server.get().strip()+":"+str(connecto_E_Port.get())+"/RPC2")
        except:
            errormessage="Error connecting to Moses: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)      
            
    elif server_type=="OpenNMT":
        try:
            global urlOpenNMT
            urlOpenNMT = "http://"+server_IP.strip()+":"+str(server_Port)+"/translator/translate"
        except:
            errormessage="Error connecting to OpenNMT: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)   
    elif server_type=="NMTWizard":
        try:
            global urlNMTWizard
            urlNMTWizard = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to NMTWizard: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)           
    elif server_type=="ModernMT":
        try:
            global urlModernMT
            urlModernMT = "http://"+server_IP.strip()+":"+str(server_Port)+"/translate"
        except:
            errormessage="Error connecting to ModernMT: \n"+ str(sys.exc_info()[1])
            messagebox.showinfo("Error", errormessage)
            
   
   
def clear_test():
    test_text_source.delete(1.0,END)
    test_text_target.delete(1.0,END)


def translate_segment_MTUOC(segment,id=101,srcLang="en-US",tgtLang="es-ES",):
    import random
    global urlMTUOC
    translation=""
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
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment_OpenNMT(segment):
    global urlOpenNMT
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params = [{ "src" : segment}]
        response = requests.post(urlOpenNMT, json=params, headers=headers)
        target = response.json()
        translation=target[0][0]["tgt"]
    except:
        errormessage="Error retrieving translation from OpenNMT: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)

    
def translate_segment_NMTWizard(segment):
    global urlNMTWizard
    translation=""
    try:
        headers = {'content-type': 'application/json'}
        params={ "src": [  {"text": segment}]}
        response = requests.post(urlNMTWizard, json=params, headers=headers)
        target = response.json()
        translation=target["tgt"][0][0]["text"]
    except:
        errormessage="Error retrieving translation from NMTWizard: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment_ModernMT(segment):
    global urlModernMT
    params={}
    params['q']=segment
    response = requests.get(urlModernMT,params=params)
    target = response.json()
    translation=target['data']["translation"]
    return(translation)
        
def translate_segment_Moses(segment):

    translation=""
    try:
        param = {"text": segment}
        result = proxyMoses.translate(param)
        translation=result['text']
    except:
        errormessage="Error retrieving translation from Moses: \n"+ str(sys.exc_info()[1])
        messagebox.showinfo("Error", errormessage)
    return(translation)
    
def translate_segment(segment,server_type,server_IP,server_Port):
    connect(server_type,server_IP,server_Port)
    if server_type=="MTUOC":
        translation=translate_segment_MTUOC(segment)
    elif server_type=="OpenNMT":
        translation=translate_segment_OpenNMT(segment)
    elif server_type=="NMTWizard":
        translation=translate_segment_NMTWizard(segment)
    elif server_type=="ModernMT":
        translation=translate_segment_ModernMT(segment)
    elif server_type=="Moses":
        translation=translate_segment_Moses(segment)
    translation=translation.replace("\n"," ")
    return(translation)


def translate_test():
    connect()
    sourcetext=test_text_source.get("1.0",END)
    traduccio=translate_segment(sourcetext)
    test_text_target.delete(1.0,END)
    test_text_target.insert(1.0,traduccio)

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

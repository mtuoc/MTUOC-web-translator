import os
import subprocess
import argparse
import codecs
import sys
import random
import requests
import re
from collections import Counter


class Tikal():
    def __init__(self):
        self.tikal_path=None
        self.sl="en"
        self.tl="es"
        self.segment=False
        self.srx_file=None
        self.okf=None
        
        self.ip="127.0.0.1"
        self.port=8000
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        self.strategy="segments"
        
    def set_path(self, path):
        self.tikal_path=path
        
    def set_sl(self, sl):
        self.sl=sl
        
    def set_tl(self, tl):
        self.tl=tl
        
    def set_srx_file(self, file):
        self.srx_file=file
        self.segment=True
    
    def set_okf(self, okf_filter):
        self.okf=okf_filter
        
    def set_ip(self, ip):
        self.ip=ip
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        
        
    def set_port(self, port):
        self.port=port
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        
        
    def set_strategy(self, strategy):
        self.strategy=strategy
        
    def convert_to_moses(self, input_file):
        try:
            command = [self.tikal_path, '-xm', input_file, '-2',  '-sl', self.sl, '-tl',  self.tl]
            if self.segment:
                extension=['-seg',self.srx_file]
                command.extend(extension)
                
            if not self.okf==None:
                extension=['-fc',self.okf]
                command.extend(extension)
            # Run the command
            subprocess.run(command, check=True)
            output_file=input_file+".xlf"
            #print(f"Successfully converted {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")
        except FileNotFoundError:
            print("Error: Tikal executable not found. Please check the Tikal path.")
            
            
            
    def generate_translation_moses(self, input_file):
        try:
            command = [self.tikal_path, '-lm', input_file, '-sl', self.sl, '-tl',  self.tl, '-totrg']
            if self.segment:
                extension=['-seg',self.srx_file]
                command.extend(extension)
                
            if not self.okf==None:
                extension=['-fc',self.okf]
                command.extend(extension)
            # Run the command
            subprocess.run(command, check=True)
            #print(f"Successfully converted {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")
        except FileNotFoundError:
            print("Error: Tikal executable not found. Please check the Tikal path.")
    def get_tags(self, segment):
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        tags=tagsA.copy()
        tags.extend(tagsB)
        return(tags)
        
    def has_tags(self, segment):
        response=False
        tagsA = re.findall(r'</?.+?/?>', segment)
        tagsB = re.findall(r'\{[0-9]+\}', segment)
        if len(tagsA)>0 or len(tagsB)>0:
            response=True
        return(response)
        
    def get_name(self, tag):
        name=tag.split(" ")[0].replace("<","").replace(">","").replace("/","")
        return(name)
        
    def is_opening_tag(self,tag):
        if tag.startswith("<") and tag.endswith(">"):
            tag_name = tag[1:-1].split()[0]  # Extracting the tag name from the tag
            return not tag_name.startswith("/")
        else:
            return False
            
    def lreplace(self, pattern, sub, string):
        """
        Replaces 'pattern' in 'string' with 'sub' if 'pattern' starts 'string'.
        """
        return re.sub('^%s' % pattern, sub, string)

    def rreplace(self, pattern, sub, string):
        """
        Replaces 'pattern' in 'string' with 'sub' if 'pattern' ends 'string'.
        """
        return re.sub('%s$' % pattern, sub, string)
            
    def create_closing_tag(self,opening_tag):
        if opening_tag.startswith("<") and opening_tag.endswith(">"):
            tag_name = opening_tag[1:-1].split()[0]  # Extracting the tag name from the opening tag
            closing_tag = f"</{tag_name}>"
            return closing_tag
        else:
            raise ValueError("Invalid opening tag format")
    
    def create_starting_tag(self,closing_tag):
        if closing_tag.startswith("</") and closing_tag.endswith(">"):
            tag_name = closing_tag[2:-1].split()[0]  # Extracting the tag name from the closing tag
            starting_tag = f"<{tag_name}>"
            return starting_tag
        else:
            raise ValueError("Invalid closing tag format")
    
    def is_closing_tag(self,tag):
        if tag.startswith("</") and tag.endswith(">"):
            tag_name = tag[2:-1].split()[0]  # Extracting the tag name from the closing tag
            return True
        else:
            return False 
            
    def is_tag(self,tag):
        # Regular expression to match a valid XML tag
        pattern = r'^</?[a-zA-Z_][\w\-.]*(\s+[^<>]*)?\s*/?>$'
        
        # Use re.match to check if the tag matches the pattern
        return re.match(pattern, tag) is not None
        
    def replace_tags(self, segment):
        equil={}
        if self.has_tags(segment):
            tagsA = re.findall(r'</?.+?/?>', segment)
            tagsB = re.findall(r'\{[0-9]+\}', segment)
            tags=tagsA.copy()
            tags.extend(tagsB)
            conttag=0
            for tag in tags:
                if tag.find("</")>-1:
                    tagrep="</tag"+str(conttag)+">"
                else:
                    tagrep="<tag"+str(conttag)+">"
                segment=segment.replace(tag,tagrep,1)
                equil[tagrep]=tag
                if tag in tagsA:
                    tagclose="</"+self.get_name(tag)+">"
                    tagcloserep="</tag"+str(conttag)+">"
                    if segment.find(tagclose)>-1:
                        segment=segment.replace(tagclose,tagcloserep,1)
                        equil[tagcloserep]=tagclose
                        tags.remove(tagclose)
                conttag+=1
                
            return(segment,equil)
            
        else:
            return(segment,equil)
        
    def remove_start_end_tag(self, segment):
        alltags=self.get_tags(segment)
        starttags=[]
        endtags=[]
        while 1:
            trobat=False
            try:
                starttag=re.match("((</?tag[0-9]+>)+)",segment)
                starttag=starttag.group()
            except:            
                starttag=""
            try:
                endtag=re.search("((</?tag[0-9]+>)+)$",segment)
                
                endtag=endtag.group()
            except:
                endtag=""
            
            if starttag:
                todelete=False
                alltagsmod=alltags
                try:
                    alltagsmod.remove(endtag)
                except:
                    pass
                if self.is_opening_tag(starttag) and self.create_closing_tag(starttag)==endtag:
                    todelete=True
                if self.is_opening_tag(starttag) and not self.create_closing_tag(starttag) in alltagsmod:
                    todelete=True
                if self.is_closing_tag(starttag):
                    todelete=True
                
                if todelete:
                    segment=self.lreplace(starttag,"",segment)
                    starttags.append(starttag)
                    trobat=True
                else:
                    starttag=""
            if endtag:
                todelete=False
                alltagsmod=alltags
                if self.is_closing_tag(endtag) and self.create_starting_tag(endtag)==starttag:
                    todelete=True
                if self.is_closing_tag(endtag) and not self.create_starting_tag(endtag) in alltagsmod:
                    todelete=True
                if self.is_opening_tag(endtag):
                    todelete=True
                if todelete:
                    segment=self.rreplace(endtag,"",segment)
                    trobat=True
                    endtags.insert(0,endtag)
                else:
                    endtag=""
            if not trobat: break
        return(segment,"".join(starttags),"".join(endtags))
    
    def repairSpacesTags(self,slsegment,tlsegment,delimiters=[" ",".",",",":",";","?","!"]):
        tlsegmentR=tlsegment
        sltags=self.get_tags(slsegment)
        tltags=self.get_tags(tlsegment)
        commontags= list((Counter(sltags) & Counter(tltags)).elements())
        for tag in commontags:
            try:
                tagaux=tag
                chbfSL=slsegment[slsegment.index(tag)-1]
                chbfTL=tlsegment[tlsegment.index(tag)-1]
                tagmod=tag
                if chbfSL in delimiters and chbfTL not in delimiters:
                    tagmod=" "+tagmod
                if not chbfSL in delimiters and chbfTL in delimiters:
                    tagaux=" "+tagaux
                try:
                    chafSL=slsegment[slsegment.index(tag)+len(tag)]
                except:
                    chafSL=""
                try:
                    chafTL=tlsegment[tlsegment.index(tag)+len(tag)]
                except:
                    chafTL=""
                if chafSL in delimiters and not chafTL in delimiters:
                    tagmod=tagmod+" "
                if not chafSL in delimiters and chafTL in delimiters:
                    tagaux=tagaux+" "
                try:
                    tlsegment=tlsegment.replace(tagaux,tagmod,1)
                    tlsegment=tlsegment.replace("  "+tag," "+tag,1)
                    tlsegment=tlsegment.replace(tag+"  ",tag+" ",1)
                except:
                    pass

                
            except:
                printLOG(3,"ERROR REPAIRING SPACES:".sys.exc_info())
                tlsegmentR=tlsegment
        return(tlsegment)
    

    def get_tag_chunks(self, input_str):
        # Regular expression to match HTML tags or text
        pattern = r'(<[^>]+>|[^<]+)'

        # Use re.findall to extract all matching parts
        parts = re.findall(pattern, input_str)

        return parts
    
    def translate_moses(self, input_file):
        mosesIN=input_file+"."+self.sl
        mosesOUT=input_file+"."+self.tl
        entrada=codecs.open(mosesIN,"r",encoding="utf-8")
        sortida=codecs.open(mosesOUT,"w",encoding="utf-8")
        for segment in entrada:
            segment=segment.rstrip()
            (segmentNormTags,equilTags)=self.replace_tags(segment)
            (segmentNOSE,startTags,endTags)=self.remove_start_end_tag(segmentNormTags)
            if self.strategy=="segments":
                translation=self.translate_segment_MTUOC(segmentNOSE)+" "
            elif self.strategy=="chunks":
                translation=[]
                chunks=self.get_tag_chunks(segmentNOSE)
                for chunk in chunks:
                    if self.is_tag(chunk):
                        translation.append(chunk)
                    else:
                        translation_chunk=self.translate_segment_MTUOC(chunk)
                        translation.append(translation_chunk)
                translation=" ".join(translation)+" "
              
            translation=startTags+translation+endTags
            for et in equilTags:
                translation=translation.replace(et,equilTags[et],1)
            translation=self.repairSpacesTags(segment,translation)
            sortida.write(translation+"\n")
            
    def translate(self, input_file):
        self.convert_to_moses(input_file)
        self.translate_moses(input_file)
        self.generate_translation_moses(input_file)
            
    def translate_segment_MTUOC(self, segment,id=101,srcLang="en-US",tgtLang="es-ES"):
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
            response = requests.post(self.urlMTUOC, json=params, headers=headers)
            
            target = response.json()
            translation=target["tgt"]
        except:
            errormessage="Error retrieving translation from MTUOC: \n"+ str(sys.exc_info()[1])
            print("Error", errormessage, " in segment ", segment)
        return(translation)
        
        
    def convert_to_xliff(self, input_file):
        try:
            command = [self.tikal_path, '-x', input_file, '-sl', self.sl, '-tl',  self.tl]
            if self.segment:
                extension=['-seg',self.srx_file]
                command.extend(extension)
                
            if not self.okf==None:
                extension=['-fc',self.okf]
                command.extend(extension)
            # Run the command
            subprocess.run(command, check=True)
            output_file=input_file+".xlf"
            #print(f"Successfully converted {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")
        except FileNotFoundError:
            print("Error: Tikal executable not found. Please check the Tikal path.")
            
    def convert_to_original(self, input_xliff):
        command = [self.tikal_path, '-m1', input_xliff] 
        # Run the command
        subprocess.run(command, check=True)
        

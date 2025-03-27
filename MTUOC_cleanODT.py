import odfdo
import difflib
import re
from odfdo import Element

class OdtCleaner():
    def __init__(self):
        self.visible_props = ["style:font-name","fo:font-size","fo:font-weight","fo:font-style"]


    def join_visually_identical_adjacent_spans(self, inherited_visible_properties, parent : Element):
        previous_style = None
        offset = 0
        for span_index in range(0,len(parent.children)):
            span = parent.children[span_index-offset]
            # if this is not a text span, we can skip it (can non-text spans have text children?)
            try:
                span_style_properties = self.document.get_style("text",span.style).get_properties()
            except:
                previous_style = None
                continue
            new_inherited_visible_properties = dict(inherited_visible_properties)

            # fill out the missing visible properties in the span
            if span_style_properties is not None and "style:font-name" in span_style_properties:
                if span_style_properties["style:font-name"].rstrip('1234567890') == inherited_visible_properties["style:font-name"].rstrip('1234567890'):
                    span_style_properties["style:font-name"] = inherited_visible_properties["style:font-name"]

            for visible_prop in self.visible_props:
                if span_style_properties is not None:
                    if visible_prop in span_style_properties:
                        if (span_style_properties[visible_prop] != inherited_visible_properties[visible_prop]):
                            new_inherited_visible_properties[visible_prop] = span_style_properties[visible_prop]
                    else:
                        span_style_properties[visible_prop] = self.initial_visible_properties[visible_prop]

            # Run the joining recursively for children
            if span.children:
                parent.replace_element(span,self.join_visually_identical_adjacent_spans(new_inherited_visible_properties, span))
            
            #Check if span visually identical to previous span
            # don't try to join elements with children, too many unclear implications there
            if previous_style and not span.children:
                visually_identical = True
                for visible_prop in self.visible_props:
                    if span_style_properties[visible_prop] != previous_style[visible_prop]:
                        visually_identical = False
                        break
                if visually_identical:            
                    # join this span to the previous span
                    previous_span = parent.children[span_index-1-offset]
                    previous_span.text = previous_span.text + span.text
                    if span.tail:
                        previous_span.tail = span.tail
                        span.tail = ""
                    parent.delete(span)
                    offset += 1                
            else:
                # If the span has a tail, do not try to merge it, as the next tag is not adjacent
                if not span.tail:
                    previous_style = span_style_properties
                else:
                    previous_style = None

        return parent


    # First remove all spans that are visually identical to their parent. Do this recursively, as text spans may be nested
    def strip_visually_identical_spans(self, inherited_visible_properties,parent,level):

        # The amount of children may decrease or increase during the loop, so keep an offset
        offset = 0
        for span_index in range(0,len(parent.children)):
            print("\t"*level + f"spans: {len(parent.children)}, span index: {span_index}, offset: {offset}")
            span = parent.children[span_index-offset]
            print("\t"*level + str(span))
            new_inherited_visible_properties = dict(inherited_visible_properties)
            visually_identical = True

            # if this is not a text span, we can skip it
            try:
                span_style_properties = self.document.get_style("text",span.style).get_properties()
            except:
                continue
            
            # ODT documents contain indexed variants of fonts, which appear to be functionally
            # identical. I'm not sure how/why these are created, but for the purposes of comparing
            # visible properties, we treat them as identical. This might backfire, if there actually 
            # are two really distinct fonts that differ only in trailing number, but it's very unlikely.
            if span_style_properties is not None and "style:font-name" in span_style_properties:
                if span_style_properties["style:font-name"].rstrip('1234567890') == inherited_visible_properties["style:font-name"].rstrip('1234567890'):
                    span_style_properties["style:font-name"] = inherited_visible_properties["style:font-name"]

            for visible_prop in self.visible_props:
                if span_style_properties is not None and visible_prop in span_style_properties:
                    if (span_style_properties[visible_prop] != inherited_visible_properties[visible_prop]):
                        new_inherited_visible_properties[visible_prop] = span_style_properties[visible_prop]
                        visually_identical = False

            #recursively process child elements
            if span.children:
                # is this necessary here? the amount of children won't change when replacing
                children_before = len(parent.children)
                parent.replace_element(span,self.strip_visually_identical_spans(new_inherited_visible_properties,span,level+1))
                children_now = len(parent.children)
                offset += children_before-children_now
                
            if visually_identical:
                children_before = len(parent.children)
                print("\t"*level + "Visually identical")
                parent = parent.strip_elements(span)
                children_now = len(parent.children)
                offset += children_before-children_now

        return parent


    # This is used to validate that the conversion did not add or delete text
    # The final test is whether the texts are identical, when normalized by removing all
    # whitespace, other tests are there for debugging
    @staticmethod
    def compare_odt_files(file1, file2):
        """Compares the text content of two ODT files."""
        def extract_text(odt_path):
            """Extracts plain text from an ODT file."""
            doc = odfdo.Document(odt_path)
            text = doc.get_formatted_text().strip()
            # Normalize the text
            # TODO: Why does this not work consistently? Finish normalization, remove all extra spaces           
            text = re.sub("\t\s*","\t",text,re.MULTILINE)
            return text

        text1 = extract_text(file1)
        text2 = extract_text(file2)
        
        ws_normalized_text1 = re.sub("\s+","",text1)
        ws_normalized_text2 = re.sub("\s+","",text2)

        diff = difflib.unified_diff(text1.split("\n"), text2.split("\n"), fromfile=file1, tofile=file2, lineterm='')
        diff_string = "\n".join(diff)
        print(diff_string or "The documents have the same text content.")
        if ws_normalized_text1 == ws_normalized_text2:
            print("Docs have same content without whitespace")
        else:
            print("Docs are different in addition to whitespace differences")
        return ws_normalized_text1 == ws_normalized_text2

    def clean_odt(self, odt_file_name, cleaned_file_name):
        self.document = odfdo.Document(odt_file_name)
        body = self.document.body
        # Keep a state of the visible significant attributes whilst recursing each paragraph
        for para in body.paragraphs:
            visible_props = ["style:font-name","fo:font-size","fo:font-weight","fo:font-style"]
            print("New paragraph")
            self.initial_visible_properties = {}

            # go up parent styles picking up missing visible properties
            # TODO: if not all properties are filled even after going up to top,
            # get them from default styles (<style:default-style style:family="paragraph">)
            iter_style = self.document.get_style("paragraph",para.style)
            while len(self.initial_visible_properties) < 4:
                iter_style_props = iter_style.get_text_properties()
                for visible_prop in visible_props:
                    if visible_prop in self.initial_visible_properties:
                        continue
                    if visible_prop in iter_style_props:
                        self.initial_visible_properties[visible_prop] = iter_style_props[visible_prop]
                if iter_style.parent_style is not None:
                    iter_style = self.document.get_style("paragraph",iter_style.parent_style)
                else:
                    break

            if len(self.initial_visible_properties) < 4:
                default_style = self.document.styles.get_style("paragraph")
                default_style_props = default_style.get_text_properties()
                for visible_prop in visible_props:
                    if visible_prop in self.initial_visible_properties:
                        continue
                    elif visible_prop in default_style_props:
                        self.initial_visible_properties[visible_prop] = default_style_props[visible_prop]

            # Set defaults for properties that are not found    
            if "fo:font-weight" not in self.initial_visible_properties:
                self.initial_visible_properties["fo:font-weight"] = "normal"
            if "fo:font-style" not in self.initial_visible_properties:
                self.initial_visible_properties["fo:font-style"] = "normal"
            
            new_para = self.strip_visually_identical_spans(self.initial_visible_properties,para,0)

            # Join adjacent spans with same formatting that are missed by the recursive stripping.
            new_para = self.join_visually_identical_adjacent_spans(self.initial_visible_properties, new_para)

            para.parent.replace_element(para,new_para)
        
        #document.save("edited.xml", packaging="xml", pretty=True)
        self.document.save(cleaned_file_name, pretty=True)

        # Verify that the original and the cleaned documents still have the same contents
        if OdtCleaner.compare_odt_files(odt_file_name, cleaned_file_name):
            return True
        else:
            return False

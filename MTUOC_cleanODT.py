import odfdo
import difflib
import re
import os
import argparse
from odfdo import Element

class OdtCleaner():
    """
    A class for merging visually identical spans in ODT documents.

    Motivation: ODT documents accumulate spans when they are being worked,
    which poses problems for localization. In localization,
    visually significant spans (e.g. colors, bold, italic, footnote etc.)
    need to be transferred into the translation in correct places, but the
    presence of other, visually irrelevant spans complicates the process,
    making correct placement of spans in the ttranslation almost impossible.
    This is also a problem in computer-assisted translation, as human
    translators find it impossible to place the spans correctly (tag soup).

    Cause: The main reason for the accumulation of the spans are revision IDs.
    New spans containing styles with revisions IDs (rsid) are generated
    whenever the text of the document is modified. This may lead to tens
    of different spans within a single sentence, where the only real
    difference is the rsid attribute that is included in the automatically
    generated style for that span.

    Description of functionality: This cleaner class works by processing 
    the spans in the document and merging spans that are visually identical, 
    which is defined as not differing in the attributes listed in 
    self.visible_props. Note that the list may not contain some visually
    significant attributes.
    
    There are three separate merging steps in the process:
    
        1. strip_visually_identical_child_spans: This removes spans that are 
        visually identical to their parent, which may be a paragraph or a 
        text span.
        2. join_visually_identical_adjacent_spans_with_children: This merges
        visually identical adjacent spans, which have children, collecting
        the children from all spans under a single span.
        3. join_visually_identical_adjacent_spans: This merges visually
        identical adjacent spans without children.

    The steps need to be performed in this order, as later steps depend on
    structure imposed by the preceding steps. There may be corner cases
    where some superfluous spans remain. 

    To guard against unintended text removal, the class contains a static
    vefification method compare_odt_files, which checks that the original
    and cleaned file have identical text content.
    """  

    def __init__(self):
        self.visible_props = [
            "style:font-name",
            "fo:font-size",
            "fo:font-weight",
            "fo:font-style",
            "style:text-underline-style",
            "fo:color",
            "fo:background-color",
            "style:text-position",
            "style:text-line-through-style"]


    # This applies to spans with children but with no text in them. 
    def join_visually_identical_adjacent_spans_with_children(self, inherited_visible_properties, parent : Element, level):
        previous_span = None
        previous_style = None
        offset = 0
        for span_index in range(0,len(parent.children)):
            
            span = parent.children[span_index-offset]
            
            # skip tags with text, as it complicates things too much (TODO?)
            if span.text or not span.children:
                previous_span = None
                previous_style = None
                continue

            new_inherited_visible_properties = dict(inherited_visible_properties)

            # if this is not a text span, we still need to process its children, e.g.
            # footnote tags have embedded text tags
            try:
                span_style_properties = self.document.get_style("text",span.style).get_properties()
                # text styles are returned as none if they have no properties, change them to empty dict
                # so that they are processed correctly
                if span_style_properties is None:
                    span_style_properties = dict()
            except:
                span_style_properties = None
            

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

            #recursively process child elements
            if span.children:
                # is offset necessary here? the amount of children won't change when replacing
                children_before = len(parent.children)
                parent.replace_element(span,self.join_visually_identical_adjacent_spans_with_children(new_inherited_visible_properties,span,level+1))
                children_now = len(parent.children)
                offset += children_before-children_now

            if previous_span:
                visually_identical = True
                for visible_prop in self.visible_props:
                    if span_style_properties[visible_prop] != previous_style[visible_prop]:
                        visually_identical = False
                        break

                if visually_identical:            
                    # join this span to the previous span
                    # this seems unnecessary, since previous_span is already specified?
                    previous_span = parent.children[span_index-1-offset]
                    for child in span.children:
                        previous_span.append(child)
                    previous_style = span_style_properties

                    # can't join next spans if there is a tail, as there is intervening text
                    # between spans
                    if span.tail:
                        previous_span.tail = span.tail
                        span.tail = ""
                        previous_span = None
                        previous_style = None

                    parent.delete(span)
                    offset += 1
                else:
                    if not span.tail:
                        previous_span = span
                        previous_style = span_style_properties
                    else:
                        previous_span = None
                        previous_style = None
            elif not span.tail:
                previous_span = span
                previous_style = span_style_properties
            else:
                previous_span = None
                previous_style = None
        return parent 

    # This applies to spans with text but no children. 
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
            
            # Check if span visually identical to previous span
            # don't try to join elements with children, too many unclear implications there
            if previous_style and not span.children:
                visually_identical = True
                for visible_prop in self.visible_props:
                    if span_style_properties[visible_prop] != previous_style[visible_prop]:
                        visually_identical = False
                        if not span.tail:
                            previous_style = span_style_properties
                        break
                if visually_identical:            
                    # join this span to the previous span
                    previous_span = parent.children[span_index-1-offset]
                    previous_span.text = previous_span.text + span.text
                    if span.tail:
                        previous_span.tail = span.tail
                        span.tail = ""
                        previous_style = None
                    parent.delete(span)
                    offset += 1                
            else:
                # If the span has a tail, do not try to merge it, as the next tag is not adjacent.
                # Don't try to merge spans with children, as the text merging becomes too complex
                if span.tail or span.children:
                    previous_style = None
                else:
                    previous_style = span_style_properties

        return parent


    # First remove all spans that are visually identical to their parent. Do this recursively, as text spans may be nested
    def strip_visually_identical_child_spans(self, inherited_visible_properties,parent,level):

        # The amount of children may decrease or increase during the loop, so keep an offset
        offset = 0
        for span_index in range(0,len(parent.children)):
            #print("\t"*level + f"spans: {len(parent.children)}, span index: {span_index}, offset: {offset}")
            span = parent.children[span_index-offset]
            #print("\t"*level + str(span))
            new_inherited_visible_properties = dict(inherited_visible_properties)
            visually_identical = True

            # if this is not a text span, we still need to process its children, e.g.
            # footnote tags have embedded text tags
            try:
                span_style_properties = self.document.get_style("text",span.style).get_properties()
            except:
                span_style_properties = None
            
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
                parent.replace_element(span,self.strip_visually_identical_child_spans(new_inherited_visible_properties,span,level+1))
                children_now = len(parent.children)
                offset += children_before-children_now
                
            if span_style_properties is not None and visually_identical:
                children_before = len(parent.children)
                #print("\t"*level + "Visually identical")
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
            return text

        text1 = extract_text(file1)
        text2 = extract_text(file2)
        
        ws_normalized_text1 = re.sub("\s+","",text1)
        ws_normalized_text2 = re.sub("\s+","",text2)

        
        if ws_normalized_text1 == ws_normalized_text2:
            #print("After odt tag cleaning, the docs have same content without whitespaces")
            pass
        else:
            #print("After odt tag cleaning, docs are different in addition to whitespace differences")
            diff = difflib.unified_diff(text1.split("\n"), text2.split("\n"), fromfile=file1, tofile=file2, lineterm='')
            diff_string = "\n".join(diff)
            #print(diff_string)

        return ws_normalized_text1 == ws_normalized_text2

    def clean_odt(self, odt_file_name, cleaned_file_name, debug=False):
        self.document = odfdo.Document(odt_file_name)
        # if debugging, save the original file as xml for comparison
        if debug:
            self.document.save("original_" + odt_file_name, packaging="xml", pretty=True)
            os.rename("original_" + odt_file_name + ".xml", "original_" + odt_file_name.replace(".odt",".fodt"))
        body = self.document.body
        # Keep a state of the visible significant attributes whilst recursing each paragraph
        for para in body.paragraphs:
            #print("New paragraph")
            self.initial_visible_properties = {}

            # go up parent styles picking up missing visible properties
            iter_style = self.document.get_style("paragraph",para.style)
            while len(self.initial_visible_properties) < 4:
                iter_style_props = iter_style.get_text_properties()
                for visible_prop in self.visible_props:
                    if visible_prop in self.initial_visible_properties:
                        continue
                    if visible_prop in iter_style_props:
                        self.initial_visible_properties[visible_prop] = iter_style_props[visible_prop]
                if iter_style.parent_style is not None:
                    iter_style = self.document.get_style("paragraph",iter_style.parent_style)
                else:
                    break

            # if some properties are still missing, get them from the default style
            if len(self.initial_visible_properties) < 4:
                default_style = self.document.styles.get_style("paragraph")
                default_style_props = default_style.get_text_properties()
                for visible_prop in self.visible_props:
                    if visible_prop in self.initial_visible_properties:
                        continue
                    elif visible_prop in default_style_props:
                        self.initial_visible_properties[visible_prop] = default_style_props[visible_prop]

            # Set defaults for properties that are not found    
            if "fo:font-weight" not in self.initial_visible_properties:
                self.initial_visible_properties["fo:font-weight"] = "normal"
            if "fo:font-style" not in self.initial_visible_properties:
                self.initial_visible_properties["fo:font-style"] = "normal"
            
            # TODO: background-color is a bit strange, since it occasionally gets included
            # in the styles even when the same as default color, but does not appear higher up 
            # the document tree. The lines below are an attempt to fix this by setting white as
            # default, but for some reason the fix causes more problems than it solves. Work on
            # this if it becomes an actual problem.  
            #if "fo:background-color" not in self.initial_visible_properties or \
            #    self.initial_visible_properties["fo:background-color"] == "transparent":
            #    self.initial_visible_properties["fo:background-color"] = "#ffffff"
            for visible_prop in self.visible_props:
                if visible_prop not in self.initial_visible_properties:
                    self.initial_visible_properties[visible_prop] = "none"
            
            new_para = self.strip_visually_identical_child_spans(self.initial_visible_properties,para,0)

            # Join adjacent spans with same formatting that are missed by the recursive stripping.
            new_para = self.join_visually_identical_adjacent_spans_with_children(self.initial_visible_properties, new_para,0)
            new_para = self.join_visually_identical_adjacent_spans(self.initial_visible_properties, new_para)

            para.parent.replace_element(para,new_para)
        
        # make it possible to save in plain xml for easier debugging
        if debug:
            self.document.save(cleaned_file_name, packaging="xml", pretty=True)
            os.rename(cleaned_file_name + ".xml", cleaned_file_name.replace(".odt",".fodt"))
        
        self.document.save(cleaned_file_name, pretty=True)

        # Verify that the original and the cleaned documents still have the same contents
        if OdtCleaner.compare_odt_files(odt_file_name, cleaned_file_name):
            return True
        else:
            return False

def main():
    parser = argparse.ArgumentParser(description="Process an input file and save the output to another file.")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("--debug", action="store_true", help="Path to the output file")
    
    args = parser.parse_args()

    cleaner = OdtCleaner()
    #print(cleaner.clean_odt(args.input_file, args.output_file, args.debug))


if __name__ == "__main__":
    main()
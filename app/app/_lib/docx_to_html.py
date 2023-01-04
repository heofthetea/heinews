from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx import Document
import os
from math import ceil, floor
WORKING_DIR = os.getcwd()
#using Pt(font.size)px as font size is way too small. Tweak this value to increase it.
_FONT_SCALING = 2


# full syntax: <link(href)text>
_LINK_KEYWORD = "<link"
_PLACEHOLDER_IMAGE = lambda x : f"__image_{x}__"

def __IMAGE__(html_source: str, user_source: str, description: str, *, id="article-image") -> str:
    # these parantheses are important
    return (
# write your html into that multiline string
# css for that html is currently stored in `articles.css`
f"""
<figure>
    <img src="{html_source}" alt="Bild konnte nicht geladen werden" id="{id}">
    <figcaption id="{id}">
        <i>Quelle: {user_source}</i> - {description}
    </figcaption>
</figure>
"""
)

DEFAULT = {
    "font": "calibri",
    "fontsize": 11,
    "align": "left",
    "color": "#000000"
}

# these variables store how the generated html file surrounding its content looks like.
__BEGINFILE__ = """
{% extends "article.html" %}
{% block title %}{{ db_entry.title }}{% endblock %}
{% block article %}
"""
__ENDFILE__ = """
{% endblock %}
"""


"""
@param doc_source: word document as file or location
@return completely functional html file containing document content
"""
def convert(doc_source) -> str:
    return get_content_as_html(Document(doc_source))


"""
@param content: content of article in html form (without surroundings)
@return: fully functional and stand-alone html file of passed content
"""
def htmlify(content: str):
    return __BEGINFILE__ + content + __ENDFILE__


"""
@param file_content: content of the file that will get checked for link syntax
@return: text given as parameter with the syntax for links replaced with the corresponding html

This has a bit of a bitter taste because it seems like this could and should be able to be done differently. However, this ultimately is what I went 
with, and is up for future work on this project to refactor. Basically what this funtion does: If someone wants to put links into their article, they
have to identify them in the word/text document as such through specific syntax. This function finds occurances of this syntax in the file content and
replaces them with their corresponding html tag.
"""
def replace_links(file_content: str) -> str:
    def get_link_tag(text, start_index):
        tag = ""
        i = start_index
        while text[i] != '>':
            tag += text[i]
            i += 1
        return tag + '>'

    def get_link_href(tag):
        href = ""
        i = len(_LINK_KEYWORD) + 1
        while tag[i] != ')':
            href += tag[i]
            i += 1
        return href

    def get_link_content(tag, href):
        return tag.replace(_LINK_KEYWORD, '').replace(f"({href})", '')[:-1]
    
    while _LINK_KEYWORD in file_content:
        tag = get_link_tag(file_content, file_content.find(_LINK_KEYWORD))
        href = get_link_href(tag)
        file_content = file_content.replace(tag, Tag.link(Tag, href, get_link_content(tag, href)))
    return file_content


"""
@param document: docx.document.Document
@return content of document converted to html

Converts a given word document into html to suit the means of the website. This means excluded are:
    images,
    links
Very basic CSS (text-align, font-size, font-family, color) is recognized.
I decided that since images in documents can't be recognized, the best workaround is to offer to put an image between every paragraph.
"""
def get_content_as_html(document) -> str:
    global DEFAULT

    HTML_CONTENT = ""
    tag = Tag()

    for paragraph in document.paragraphs:
        #stores the content of the current paragraph to pass on to Tag.paragraph(); is already html-formatted
        par_content = ""
        try:
            attr = {
                "font": get_font(paragraph.runs[0].font, handleNone=True),
                "fontsize": get_fontsize(paragraph.runs[0].font.size, handleNone=True),
                "align": get_textalign(paragraph.alignment, handleNone=True),
                "color": get_color(paragraph.runs[0].font.color.rgb.__str__())
            }

        except IndexError:
            attr["fontsize"] = DEFAULT["fontsize"]
            attr["font"] = DEFAULT["font"]
            attr["align"] = DEFAULT["align"]

            par_content = tag.linebreak()

        for run in paragraph.runs:
            font = run.font
            font_size = get_fontsize(font.size)
            # when only one word is coloured (without any additional decoration), it will not be detected as a run, so this is 
            # only effectiveto a certain extend, but still, I tried
            run_color = get_color(font.color.rgb.__str__())
            content = run.text

            #checking for text decorations and surrounding the content accordingly
            if font.italic: content = tag.italic(content, font=font.name, fontsize=font_size, color=run_color)
            if font.bold: content = tag.bold(content, font=font.name,fontsize=font_size, color=run_color)
            if font.underline: content = tag.underline(content, font=font.name, fontsize=font_size, color=run_color)

            if content == "":
                par_content += tag.linebreak()
            else:
                par_content += content
        par_content = tag.paragraph(par_content, font=attr["font"], fontsize=attr["fontsize"], textalign=attr["align"])
        HTML_CONTENT += f"{par_content}\n"

    return HTML_CONTENT


#--------------------------------------------------------------------------------------------------------------------------


# i don't know why i thought this little syntactic sugar was worth an entire own class
class Tag:
    def __init__(self):
        pass

    def header(self, hierarchy: int, content: str, style=()) -> str:
        pass

    #TODO put style definition into its own function
    def paragraph(self, content: str, font=None,  fontsize=None, textalign=None, color=None) -> str:
        style = " style='{0}{1}{2}{3}'".format(self.set_font(font), self.set_fontsize(fontsize),
                                               self.set_textalign(textalign), self.set_color(color))

        #if style looks like this, every style is the same as the default, making specifying it unecessary
        if style == " style=''":
            style = ""
        tag_open = "<p{}>".format(style)
        return "{0}{1}</p>".format(tag_open, content)

    def image(self, source: str) -> str:
        return "<img src='source' alt=''>"

    def link(self, href: str, content: str) -> str:
        return "<a href='{0}'>{1}</a>".format(href, content)

    def linebreak(self) -> str:
        return "<br>"

    def italic(self, content: str, font=None,  fontsize=None, textalign=None, color=None) -> str:
        style = " style='{0}{1}{2}'".format(self.set_font( font), self.set_fontsize(fontsize), self.set_color(color))
        if style == " style=''":
            style = ""
        tag_open = "<i{}>".format(style)
        return "{0}{1}</i>".format(tag_open, content)

    def bold(self, content: str, font=None,  fontsize=None, textalign=None, color=None) -> str:
        style = " style='{0}{1}{2}'".format(self.set_font(font), self.set_fontsize(fontsize), self.set_color(color))
        if style == " style=''":
            style = ""
        tag_open = "<b{}>".format(style)
        return "{0}{1}</b>".format(tag_open, content)

    def underline(self, content: str, font=None,  fontsize=None, textalign=None, color=None) -> str:
        style = " style='{0}{1}{2}'".format(self.set_font(font), self.set_fontsize(fontsize), self.set_color(color))
        if style == " style=''":
            style = ""
        tag_open = "<u{}>".format(style)
        return "{0}{1}</u>".format(tag_open, content)

    #--------------------------------------------------
    #absolutely necessary functions

    def set_font(self, font: str) -> str:
        if not font:
            return ""
        return "font-family: {};".format(font)

    def set_fontsize(self, size: int) -> str:
        if not size:
            return ""
        return "font-size: {}px;".format(size * _FONT_SCALING)

    def set_textalign(self, align: str) -> str:
        if not align:
            return ""
        return "text-align: {};".format(align)

    def set_color(self, color: str) -> str:
        if not color:
            return ""
        return "color: {};".format(color)

    def tab():
        return "&#9"

#--------------------------------------------------------------------------------------------------------------------------

"""
@return: text alignment formatted as CSS
"""
def get_textalign(alignment: WD_ALIGN_PARAGRAPH, default=DEFAULT["align"], handleNone=False) -> str:
    if alignment == WD_ALIGN_PARAGRAPH.CENTER: return "center"
    if alignment == WD_ALIGN_PARAGRAPH.LEFT: return "left"
    if alignment == WD_ALIGN_PARAGRAPH.RIGHT: return "right"
    if handleNone: return default
    return None


def get_font(font, default=DEFAULT["font"], handleNone=False) -> str:
    if not font.name:
        if handleNone:
            return default
        return None
    return font.name.lower()


"""
@param size: run.font.size
@param default: size of the run befor, in case run.font.size is None

run.font.size returns a very high number -> Pt(font.size) returns actual font-size
"""
def get_fontsize(size: int, default=DEFAULT["fontsize"], handleNone=False) -> int:
    if not size:
        if handleNone:
            return default
        return None
    for i in range(64):
        if size == Pt(i):
            return i
    return None


"""
@return color as hex code, if color is None, the default is used
"""
def get_color(hex: str, default=DEFAULT["color"]) -> str:
    if not hex or hex == "None":  # for some reason `font.color.rgb.__str__()` returns "None" instead of actual None
        return default
    return "#{}".format(hex)



#----------------------------------------------------------------------------------------------------------------------------------

"""
@param html_text: pass text generated by get_content_as_html
@param num_images: the number of images to be inserted into the articles

@return: returns the text with image placeholders in place -> can be passed into fill_image_placeholders now
"""
def create_image_placeholders(html : str) -> str:
    tag = Tag()
    br = tag.linebreak()

    i = 0
    while True:
        occ = html.find(br)
        if occ == -1: # if str.find() returns -1, the substring does not exist in parent string
            break
        
        # this essentially inserts the placeholder in between the entire string before and after the occurance
        html = html[:occ] + _PLACEHOLDER_IMAGE(i) + html[(occ + len(br)):]
        i += 1
    return html
    

"""
@param text: htmlifyed text with image placeholders in place
@param sources: a list containing tuples with [0] being the source and [1] the description

@return: parameter text with placeholders replaced through Tag.image 
    -> TODO replace with figure and correct id to make this integratable with articles.css
"""
def fill_image_placeholders(text: str, sources: list[tuple[str, str]]) -> str:
    all_placeholders = create_placeholder_list(text)
    
    to_replace = get_placeholders_to_replace(all_placeholders, num_to_replace=len(sources))

    # OK SERIOUSLY WHAT IN THE GOOD HOLY MARMELADE FUCK AM I DOING HERE
    # it's better now but I'll leave that comment as a motivational quote (19.09.'22)

    for placeholder_id, src in zip(to_replace["to_replace"], sources):
        text = text.replace(_PLACEHOLDER_IMAGE(placeholder_id), __IMAGE__(src[0], src[1], src[2]))
    
    for src in sources[-(to_replace["extra"] - 1):]:
        text += (__IMAGE__(src[0], src[1], src[2]))

    for i in all_placeholders:
        text = text.replace(_PLACEHOLDER_IMAGE(i), Tag().linebreak())

    return text

"""
goes through a text and represents every placeholder found as an integer (index) in a seperate list, since working with an integer list 
is a lot easier than with a huge string.
"""
def create_placeholder_list(text: str) -> list[int]:
    counter = 0
    placeholders = []
    while _PLACEHOLDER_IMAGE(counter) in text:
        placeholders.append(counter)
        counter += 1
    return placeholders


"""
@reurn: dictionary containing list of placeholder ids and how many extra images there are
"""
def get_placeholders_to_replace(placeholders: list, num_to_replace: int) -> dict:
    to_replace = []

    # deals with the number of images being larger than available placeholders. It stores, how many extra there are and simply appends the corresponding
    # (yet nonexistant) indexes after the algorithm runthrough.
    extra = 0
    if num_to_replace > len(placeholders):
        extra = num_to_replace - len(placeholders)
        num_to_replace = len(placeholders)

    # the `+1`s smoothen the result somewhat
    step_1 = (len(placeholders) + 1) / (num_to_replace + 1)
    if not isinstance(step_1, int): # indicates that there is no even split possible
        # since it's not possible to go `.5` steps, uneven splits are solved by taking eg. one full every other iteration (1 / .5 = 2)
        point = step_1 - floor(step_1)
        try:
            big_step_spacing = ceil(1 / point)
        except ZeroDivisionError:
            big_step_spacing = 0
        step_2 = ceil(step_1) # the big step is exactly one larger than the small one
    else:
        step_2 = step_1

    small_step = False 
    i = -1
    n = num_to_replace # declared so that `num_to_replace` still holds the initial value of how many images need inserting
    while n > 0: # a while loop is used here to control the size of the steps manually
        i += floor(step_1 if small_step else step_2)

        # boolean logic in a nutshell
        # essentially deals with the big step control 
        if big_step_spacing != 0:
            if i % big_step_spacing == 0:
                small_step = not small_step
            elif not small_step:
                small_step = not small_step

        to_replace.append(i)
        n -= 1

    for i in range(extra):
        to_replace.append(num_to_replace + i) # "makes up" new indexes to fit extra images, needs to be dealt with later
    return {
        "to_replace": to_replace,
        "extra": extra
    }

#----------------------------------------------------------------------------------------------------------------------------------

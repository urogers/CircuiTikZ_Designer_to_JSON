#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions:
 - convert_tokens_to_json
 - clean_numeric_value
 - clean_coordinates
 - convert_coordinate
 - build_shape_component
 - build_new_wire_component
 - get_coordinate_list
 - parse_shape_size
 - parse_text_for_shape
 - parse_draw_options
 - parse_fill_options
 - parse_rotation
 - scale_dash_pattern

Helper Functions for working around splitting and extracting content that may contain LaTeX math encoding
  - split_options
  - extract_label
   - parse_label_mixed_latex
"""

import re

# ---------------------------------------------------------------------
# TikZ Code to JSON Conversion Dictionaries
# ---------------------------------------------------------------------

ARROW_ALIASES = {
    'stealth': 'stealth',
    'stealth reversed': 'stealthR',
    'latex': 'latex',
    'latex reversed': 'latexR',
    'to': 'to',
    'to reversed': 'toR',
    '|': 'line'
}

LINE_ALIASES = {                        # For TeX to JSON.  These are all normalized to a linewidth = 1.
    'on 1pt off 4pt': 'dotted',
    'on 1pt off 2pt': 'denselydotted',
    'on 1pt off 8pt': 'looselydotted',
    'on 4pt off 4pt': 'dashed',
    'on 4pt off 2pt': 'denselydashed',
    'on 4pt off 8pt': 'looselydashed',
    'on 4pt off 2pt on 1pt off 2pt': 'dashdot',
    'on 4pt off 1pt on 1pt off 1pt': 'denselydashdot',
    'on 4pt off 4pt on 1pt off 4pt': 'looselydashdot',
    'on 4pt off 2pt on 1pt off 2pt on 1pt off 2pt': 'dashdotdot',
    'on 4pt off 1pt on 1pt off 1pt on 1pt off 1pt': 'denselydashdotdot',
    'on 4pt off 4pt on 1pt off 4pt on 1pt off 4pt': 'looselydashdotdot'
}

# LABEL_POSITION_MAP = {
#     'above': 'north',
#     'below': 'south',
#     'left': 'west',
#     'right': 'east',
# }

# ---------------------------------------------------------------------
# Scaling factors from Normalized TikZ units to JSON units
# The following are calculated by comparing CircuiTikZ Designer JSON to TeX.  Interesting Shape is a different scale.
# ---------------------------------------------------------------------
LATEX_TO_JSON_SCALE_X_FACTOR = 37.795286
LATEX_TO_JSON_SCALE_Y_FACTOR = 37.795286
LATEX_TO_JSON_SCALE_SHAPE_FACTOR = 38.88379


# ---------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------


# The key function is next.  It is long, but breaking into the "key" types of tokens, allows for modular code
# that really evolved from 'get something quick' to 'let's support more and more complexity.  While the lines-of-code
# is long, one nice feature is that simple single \\nodes are independent of multi node options

def convert_tokens_to_json(tokens):
    """
    Process the sequence of tokens for each circuit element type and create a JSON entry
    Each circuit element collection of tokens starts with either {'to', 'node', '2node', '3node', 'device' 'wire'}
     and the tokens for each are assumed ordered data. That is tokens[3] has a specific meaning for each type:
    see i_o_library/tokenize_all_draw_contents for details.

    Again: token[0] is only one of these {'to', 'node', '2node', '3node', 'device' 'wire'}
    """

    # Used by all Types
    coord_dict = get_coordinate_list(tokens)
    start_point = coord_dict[0]

    # Process Tokens: Six Cases {'to', 'node', '2node', '3node', 'device' 'wire'}
    if tokens[0] == 'to':
        '''
        Tokens form:       
            [0: 'to', 1: (start coord), 2: [device, options], 3: (end coord)
            
        Example:  ['to', '(9.54, 10.75)', '[cute inductor, l_={$L_1$}]', '(9.54, 9.75)']
        
        There should only be a start and stop coordinate for 'to'.  If not, this ignores the 3rd & higher coordinates
        '''

        end_point = coord_dict[1]

        result = {
            "type": "path",
            "points": coord_dict
        }

        if len(tokens[2].split('$')) > 1:  # This means there is a label
            parts = split_options(tokens[2])
            check = extract_label(parts[-1])

            label_value = {}

            if check[1] is not None:
                label_value["value"] = check[1]
            if check[0]:
                label_value["otherSide"] = 'true'
            label_value["distance"] = "0.12cm"
            result["label"] = label_value

            result = parse_to_mirror_invert(parts, result)

            result["id"] = parts[0]

            # Now check for optional name
            m = re.match(r"name=(.+)", parts[-1])
            if m:
                result["name"] = m.group(1)

        elif len(tokens[2].split(',')) > 1:  # >1 means there are options, but no label (means the split works)
            no_bracket = tokens[2].strip("[]")
            rough_parts = no_bracket.split(',')
            parts = [s.strip() for s in rough_parts]
            result = parse_to_mirror_invert(parts, result)
            result["id"] = parts[0]
        else:  # This means no options and no labels, just the device id
            result["id"] = tokens[2].strip("[]")

        return result

    elif tokens[0] == 'node':
        '''
        Single Node
        Token Form:   [0: 'node', 1: 'shape, options', 2: name, 3: coord1, 4: label1]

        Example:  ['node', 'shape=circle, draw, line width=1pt, minimum width=-0.035cm', None, '(3.5, 8.75)', '']
        '''
        result = parse_shape_size(tokens[1], start_point)

        if tokens[2]:
            result["name"] = tokens[2]

        stroke = parse_draw_options(tokens[1])
        result["stroke"] = stroke  # stroke will never be blank.  At least {"opacity": 0}

        rotation, scale = parse_rotation(tokens[1])
        if rotation is not None:
            result["rotation"] = rotation
        if scale is not None:
            result["scale"] = scale

        return result

    elif tokens[0] == "2node":
        """
        Two node commands
        Tokens form:       
            [0: '2node', 1: '[shape]', 2: name, 3: coord1, 4: label1, 5: [id_anchor]', 6: id_name, 7: id_loc,
             8: id_label]
             
        Example: ['2node',
                 'shape=rectangle, minimum width=1.308cm, minimum height=0.59cm', 'x1', '(6.672, 13)', '',
                 '[anchor=north, align=center, text width=0.991cm, inner sep=5pt]', '', '(6.672, 13.312)', '\\Large A $e_t$']
        
        Note that 2 nodes do not have the 3rd node for a label, so that operation is being ignored (maybe a bug)
        """

        # other_point = coord_dict[1]     # Doesn't appear to be needed

        result = parse_shape_size(tokens[1], start_point)

        if tokens[8] is not None:
            text = parse_text_for_shape(tokens[8])
            result["text"] = text

        if tokens[2] != '':
            result["name"] = tokens[2]

        stroke = parse_draw_options(tokens[1])
        result["stroke"] = stroke  # stroke will never be blank.  At least {"opacity": 0}

        fill = parse_fill_options(tokens[1])
        if fill is not None:
            result["fill"] = fill

        # Now rotation & Scale
        rotation, scale = parse_rotation(tokens[1])
        if rotation is not None:
            result["rotation"] = rotation
        if scale is not None:
            result["scale"] = scale
        # Now rotation

        return result

        # End 2-Node

    # ###############################################
    elif tokens[0] == "3node":
        """
        Three nodes within one TeX command
        Tokens Form is [0: '3node', 1: '[shape]', 2: name, 3: (coord1), 4: label1, 5: [id_anchor]', 6: id_name, 7: (id_loc),
                        8: id_label, 9: [text options / positioning], 10: text_name, 11: (text_loc), 12: [text str]
        
        Example: ['3node',
         '[shape=rectangle, line width=1pt, minimum width=1.762cm, minimum height=1.215cm]', 'my text', '(12.648, 11)', '', 
         '[anchor=south]', '', '([yshift=0.63cm]my text.text)', '$A_{label}$',
         '[anchor=center, align=center, text width=1.444cm, inner sep=5pt]', '', '(12.648, 11)', 
         '\\textcolor{rgb,255:red,255;green,0;blue,128}{\\small $\\,\\boldsymbol{+}$\\  $e_c(t)$  
         $\\frac{a}{b} $ \\ $\\ \\boldsymbol{-}$}']
        
        """

        # text_point = coord_dict[1]    # Need to work this in

        result = parse_shape_size(tokens[1], start_point)

        if tokens[12] is not None:
            text = parse_text_for_shape(tokens[12])
            result["text"] = text

        if tokens[2]:  # This is the component name or TikZ Label
            result["name"] = tokens[2]

        stroke = parse_draw_options(tokens[1])
        result["stroke"] = stroke   # stroke will never be blank.  At least {"opacity": 0}

        fill = parse_fill_options(tokens[1])
        if fill is not None:
            result["fill"] = fill

        # Now Label
        # Do the Label
        if tokens[8] is not None:
            label_array = {}
            labels = parse_label_mixed_latex(tokens[8])
            if labels[0].startswith('\\'):  # Pull out possible fontsize
                m = re.search(r'^\\([a-zA-Z]+)\s*(.*)', labels[0])
                if m:
                    font_size = m.group(1)
                    text["fontsize"] = font_size
                    labels[0] = m.group(2)
                    text2 = ' '.join(
                        labels[1:])  # Concatenate all labels into one text block, excluding 1st fontsize
                else:
                    text2 = ' '.join(labels)  # Concatenate all labels into one text block, as 1st is not a fontsize
            else:
                text2 = ' '.join(labels)  # Concatenate all labels into one text block

            label_array["value"] = text2.strip('$')

            if tokens[5] is not None:
                m = re.search(r"anchor=([^\s,\]]+)", tokens[5])
                if m:
                    label_array["anchor"] = m.group(1)

            if tokens[9] is not None:
                label_array["position"] = 'northeast'  # Hardcode these.  User will just have to move where they want
                label_array["relativeToComponent"] = 'true'
                label_array["distance"] = "0.16cm"

            result["label"] = label_array

        # Now rotation and scale
        rotation, scale = parse_rotation(tokens[1])
        if rotation is not None:
            result["rotation"] = rotation
        if scale is not None:
            result["scale"] = scale

        return result

    # End 3-Node

    elif tokens[0] == "device":
        '''
        tokens form:  [0: 'device', 1: 'device, options', 2: name, 3: (coord1), 4: label1]
        
        Example:    ['device', 'american and port, xscale=0.5, yscale=0.5', None, '(11.386, 13.53)', '']
        '''

        result = {
            "type": "node",
            "position": start_point,
        }

        # label_point = coord_dict[1] # Just hard coding label position, so this is ignored so do not have to parse named anchors
        id_plus_options = tokens[1]
        parts = id_plus_options.split(',')
        if len(parts) == 1:
            id = id_plus_options[:]
            options = ''
        else:
            id = parts[0]
            opts_rough = parts[1:]
            options = [s.strip() for s in opts_rough]

            # Now Pull out the optional parameters like 'photo', xscale, yscale, etc.

            # Check Rotation and Scale
            rotation, scale = parse_rotation(id_plus_options)
            if rotation is not None:
                result["rotation"] = rotation
            if scale is not None:
                result["scale"] = scale
        if len(tokens) > 5:     # Only applies to a multi node.  Simple a single node only has 5 params
            label = {
                "anchor": "default",
                "position": "default",
                "distance": "0.12cm"
            }
        latex_pattern = r'\$(.*)\$'
        if len(tokens) > 5:
            m = re.search(latex_pattern, tokens[8], flags=re.DOTALL)
            if m:
                label["value"] = m.group(1)
            result["label"] = label
        result["options"] = options
        result["id"] = id

        # Can do anchor, as we have token[4], but setting to default for now since it is "close enough"

        return result

    elif tokens[0] == "wire":
        # Do the wire as this is the only option lef
        directions = [t for t in tokens if t in ['--', '-|', '|-']]
        options = tokens[-1]

        result = build_new_wire_component(coord_dict, directions, options)

        stroke = parse_draw_options(tokens[1])
        if not set(stroke.keys()) == {"opacity"} and stroke.get("opacity") == 0:     # This is not good coding.  The parse_draw_options returns opacity=0 as the fall through.  If that changes, this breaks but not critically
           result["stroke"] = stroke

        return result

    else:
        # We should never get here as it should have failed in the Token Creation Process
        print(f"❌ An unknown element has been encountered '{tokens}'.")



def parse_to_mirror_invert(parts, result):
    '''
    Parse a //draw to part (e.g. resistor) and see if it is Mirrored or Inverted as options.  If not, the result dictionary
    is returned unmodified

    :param parts: Comma deliminated options for a \\to part
    :param result: Current JSON dictionary
    :return: result:     Possibly updated JSON dictionary with a "scale" key
    '''

    scale = {}
    if "mirror" in parts:
        if "invert" in parts:
            scale["x"] = -1
            scale["y"] = -1
        else:  # Only Mirror
            scale["x"] = -1
            scale["y"] = 1
        result["scale"] = scale
    elif "invert" in parts:
        scale["x"] = 1
        scale["y"] = -1
        result["scale"] = scale

    return result


def clean_numeric_value(value):
    """
    Clean and normalize a numeric value to avoid anomalies.
    Round to 3 decimals to avoid floating point artifacts
    """
    rounded = round(value, 3)

    # Convert -0.0 to 0.0
    if rounded == 0:
        return 0.0
    return rounded


def clean_coordinates(coords):
    """
    Clean a coordinate dict by removing numeric anomalies.
    Expects coords with keys 'x' and 'y'.
    """
    return {
        "x": clean_numeric_value(coords["x"]),
        "y": clean_numeric_value(coords["y"]),
    }


def convert_coordinate(value, axis):
    """
    Apply a linear transform to a coordinate:
      - multiply by the scale factor
      - invert Y axis if axis == 'y'
    Returns a cleaned numeric value.
    """
    try:
        float_value = float(value)
    except Exception:
        # If conversion fails, return 0.0 as a safe fallback
        float_value = 0.0
    scaled = 0.         # Default value that should never be used, as these are coordinates with # values to get here
    if axis == "x":
        scaled = float_value * LATEX_TO_JSON_SCALE_X_FACTOR
    #scaled = float_value * LATEX_TO_JSON_SCALE_FACTOR
    elif axis == "y":
        scaled = -float_value * LATEX_TO_JSON_SCALE_Y_FACTOR
        # scaled = -1.0 * scaled  # invert Y axis

    return clean_numeric_value(scaled)


# def parse_special_connector(options_str: str) -> Dict[str, Optional[str]]:
#     """
#     Handle special connectors like -o, *-*, o-o, etc.
#     Returns a dict with keys:
#       - is_special: bool
#       - start_node: str | None
#       - end_node: str | None
#     """
#     result = {"is_special": False, "start_node": None, "end_node": None}
#
#     patterns = {
#         r"^short,\s*-o$": {"start": None, "end": "ocirc"},
#         r"^short,\s*o-$": {"start": "ocirc", "end": None},
#         r"^short,\s*o-o$": {"start": "ocirc", "end": "ocirc"},
#         r"^short,\s*\*-\*$": {"start": "circ", "end": "circ"},
#         r"^short,\s*\*-o$": {"start": "circ", "end": "ocirc"},
#         r"^short,\s*o-\*$": {"start": "ocirc", "end": "circ"},
#         r"^-o$": {"start": None, "end": "ocirc"},
#         r"^o-$": {"start": "ocirc", "end": None},
#         r"^o-o$": {"start": "ocirc", "end": "ocirc"},
#         r"^\*-\*$": {"start": "circ", "end": "circ"},
#         r"^\*-o$": {"start": "circ", "end": "ocirc"},
#         r"^o-\*$": {"start": "ocirc", "end": "circ"},
#     }
#
#     trimmed = options_str.strip()
#     for pat, nodes in patterns.items():
#         if re.match(pat, trimmed):
#             result["is_special"] = True
#             result["start_node"] = nodes["start"]
#             result["end_node"] = nodes["end"]
#             break
#
#     return result

def build_shape_component(coord_dict_list, directions, line_width):
    """
    Build a shape JSON object

    Here the coord_dict_list contains lists of processed coordinates in dictionary form
    the [line width= ...] option is supported, but opacity and style are not yet.
    The 'style' looks to be difficult, and opacity not that useful.  Sorry, you get solid dark wires
    """

    # Do not add a wire if all the coordinates are the same
    first = coord_dict_list[0]

    if all(c["x"] == first["x"] and c["y"] == first["y"] for c in coord_dict_list):
        return None

    result = {
            "type": "wire",
            "points": coord_dict_list,
            # "directions": ["-|"]*(len(coord_list)-1),
            "stroke": {"width": line_width},
            "directions": directions,

            # "segments": [{"endPoint": clean_end, "direction": "-|"}],    # Not sure why -|.  Really just doing single wires
        }

    return result

def build_new_wire_component(coord_dict_list, directions, options):
    """
    Build and a wire JSON object
    Here the coord_dict_list contains lists of processed coordinates in dictionary form
    the options includes 'line width' and start/end arrows.  Opacity and style are not yet.
    The 'style' looks to be difficult, and opacity not that useful.  Sorry, you get solid dark wires
    """
    # Do not add a wire if all the coordinates are the same
    first = coord_dict_list[0]
    if all(c["x"] == first["x"] and c["y"] == first["y"] for c in coord_dict_list):
        result = None

    result = {
        "type": "wire",
        "points": coord_dict_list,
        # "directions": ["-|"]*(len(coord_list)-1),
        "directions": directions,
    }
    # Now add optional content
    stroke = {}
    # line_width_pattern = r'line width\s*=\s*([0-9]*\.?[0-9]+pt).*?([A-Za-z]+)-to\s+([A-Za-z]+)'
    line_width_pattern = r'line width=([\d.]+pt)'
    only_arrows_pattern = r'\[([^-]*)-(.*)\]'
    m = re.search(line_width_pattern, options)
    if m:
        stroke["width"] = m.group(1)
        result["stroke"] = stroke

        # With a Path, the 'draw' now appears in the options.  Keeping the code the same as the process tokens so a function can be used
        m_path = re.search(r'draw', options)  # Must support standalone draw with no RGB Color options
        if m_path:
            width_for_style = 1
            stroke = {}
            #  This should be done as a loop iterating over the patterns
            m2 = re.search(r'line width=([\d.]+pt)', options)
            if m2:
                stroke["width"] = m2.group(1)
                width_for_style = float(m2.group(1).replace('pt', ''))

            m2 = re.search(r'draw opacity=([^,]+)', options)
            if m2:
                stroke["opacity"] = m2.group(1)

            m2 = re.search(r'dash pattern=\{([^}]*)\}', options)  # All text between {}
            if m2:  # The mapping between TeX and JSON is hardcoded
                key = scale_dash_pattern(m2.group(1), width_for_style)
                if key in LINE_ALIASES.keys():
                    stroke["style"] = LINE_ALIASES[key]
                else:
                    print(f'⚠️ The pattern', key, 'was not converted. Defaulting to a solid line')
            # Color
            m3 = re.search(r'draw=\{([^}]*)\}', options)  # Now see if rgb options, & pull off {}
            if m3:
                m4 = re.search(r'rgb,255:red,(\d+);green,(\d+);blue,(\d+)', m3.group(1))
                if m4:
                    red, green, blue = m4.groups()
                    stroke["color"] = f'rgb({red},{green},{blue})'
            result["stroke"] = stroke


        m_arrow = re.search(r',\s*([a-zA-Z]+)-([^],]*)', options)
        if m_arrow:
            if m_arrow.group(1):
                if m_arrow.group(1) in ARROW_ALIASES:       # Not letting an error pass silently
                    result["startArrow"] = ARROW_ALIASES[m_arrow.group(1)]
                else:
                    print(f'⚠️ Start Arrow Key Not Supported in ARROW_ALIASES dictionary: ', m_arrow.group(1))
            if m_arrow.group(2):
                if m_arrow.group(2) in ARROW_ALIASES:
                    result["endArrow"] = ARROW_ALIASES[m_arrow.group(2)]
                else:
                    print(f'⚠️ End Arrow Key Not Supported in ARROW_ALIASES dictionary: ', m_arrow.group(2))

    else:       # No Linewidth, but still check arrows
        m = re.search(only_arrows_pattern, options)
        if m:
            if m.group(1):
                if m.group(1) in ARROW_ALIASES:
                    result["startArrow"] = ARROW_ALIASES[m.group(1)]
                else:
                    print(f'⚠️ Start Arrow Key Not Supported in ARROW_ALIASES dictionary: ', m.group(1))
            if m.group(2):
                if m.group(2) in ARROW_ALIASES:
                    result["endArrow"] = ARROW_ALIASES[m.group(2)]
                else:
                    print(f'⚠️ End Arrow Key Not Supported in ARROW_ALIASES dictionary: ', m.group(2))


    return result


def get_coordinate_list(tokens):
    """
    This parses a list of general tokens associated with one line of TeX, pulls out all TikZ coordinates
    of form '(12,3)'  and returns a list of JSON ready coordinates of the form [ [233.37, -27.24], ...]

    Bug:  Need to handle the case of relative positioning.  For Example, a TikZ label of X1 having position
    ([yshift=0.04cm]X1.north east) is simply ignored
    """
    coordinates = [t for t in tokens if t is not None and re.match(r'^\(.*\)$', t)]   # Must start with ( and end with ) & ignore None types
    points = []
    for current_coord in coordinates:
        if re.match(r'\(\s*-?\d*\.?\d+\s*,\s*-?\d*\.?\d+\s*\)', current_coord) is not None:  # Ignore relative positioning
            x_str, y_str = current_coord.strip("()").split(",")
            x_conv = convert_coordinate(float(x_str), "x")
            y_conv = convert_coordinate(float(y_str), "y")
            points.append([x_conv, y_conv])

    coord_dict_list = []
    for pair in points:
        x, y = pair
        coord_dict_list.append(clean_coordinates({"x": x, "y": y}))

    return coord_dict_list


def parse_shape_size(token, location):
    '''
    This parses the token to determine what shape is desired, what size it is.  This needs the location passed in
    :param token:
    :param start_location:
    :return: result:  JSON entry
    '''
    # re patterns for matching strings
    shape_pattern = r'shape=([^,\]]+)'
    min_width_pattern =  r'minimum width=([-+]?\d*\.?\d+)'
    min_height_pattern = r'minimum height=([-+]?\d*\.?\d+)'

    # Shape  (Need error checking in case shape type is new/different)
    m = re.search(shape_pattern, token)
    if m:
        shape_type = m.group(1).strip()
        if shape_type == 'rectangle':
            shape = 'rect'
        else:  # This may be a bug, but the only two options are circle or ellipse and both -> ellipse
            shape = 'ellipse'

    result = {
        "type": shape,
        "position": location
    }

    # Width and Height (Both need to be detected to produce JSON entry)
    m = re.search(min_width_pattern, token)
    if m:
        width = round(float(m.group(1)) * LATEX_TO_JSON_SCALE_SHAPE_FACTOR, 3)
        width = max(0, width)       # Only allow positive #'s if negative then set to zero
        m = re.search(min_height_pattern, token)
        if m:
            height = round(float(m.group(1)) * LATEX_TO_JSON_SCALE_SHAPE_FACTOR, 3)
            result["size"] = {
                "x": width,
                "y": height
            }
        else:
            result["size"] = {
                "x": width,
                "y": width
            }
    return result

def parse_text_for_shape(token):
    '''
    A shape may have a text item associate with it, this parses it, managing fontsize and text with LaTeX math support
    :param token:     Example   '\\small A $e_t$'
    :return text:     Formated as a JSON dictionary with fontsize = small, and the text as 'A $e_t$'
    '''

    # Need routine to parse text configuration.  Hard code part of the "text" key for now, as conversion is convoluted
    text = {
        "align": "1",               # Center Horizontally
        "justify": "0",             # Center Vertically
        "innerSep": "0",            # Textbox separation (most likely)
        "showPlaceholderText": "true"
    }

    pattern_color = r'\\textcolor\{([^}]+)\}(.*)'

    m = re.search(pattern_color, token)
    if m:               # \\textcolor detected
        m_color = re.search(r'rgb,255:red,(\d+);green,(\d+);blue,(\d+)', m.group(1))
        if m_color:
            red, green, blue = m_color.groups()
            text["color"] = f'rgb({red},{green},{blue})'
        pattern_bracket = r'^\{(.*)\}$'         #For removing starting and ending brackets
        m_no_brackets = re.match(pattern_bracket, m.group(2))
        if m_no_brackets:
            token = m_no_brackets.group(1)
        else:
            token = m.group(2)      # Remove the Color parts

    # font_size = None
    if token is not None:
        labels = parse_label_mixed_latex(token)
        if labels[0].startswith('\\'):  # Pull out possible fontsize
            m = re.search(r'^\\([a-zA-Z]+)\s*(.*)', labels[0])
            if m:
                font_size = m.group(1)
                text["fontSize"] = font_size
                labels[0] = m.group(2)
                text2 = ' '.join(labels)  # Concatenate all labels noting fontsize has been removed
            else:
                text2 = ' '.join(labels)  # Concatenate all labels into one text block, as 1st is not a fontsize
        else:
            text2 = ' '.join(labels)  # Concatenate all labels into one text block
        text["text"] = text2
    return text

def parse_draw_options(token):
    '''
    This searches over the options for a TikZ draw object and detects the following parameters
      - Line Width
      - Opacity
      - Line Pattern (dot, dashed, ..)   See LINE_ALIASES dictionary for supported patterns

    :param token:   Draw Option Tokens
    :return: JSON stroke dictionary.  The "fall through" case is opacity = 0 so lines are not drawn around all boxes.
                                      That is coupled to other parts of the code (poorly) and should be refactored
    '''

    m = re.search(r'draw', token)  # Must support standalone draw with no RGB Color options
    stroke = {}
    if m:
        width_for_style = 1
        #  This should be done as a loop iterating over the patterns
        m2 = re.search(r'line width=([\d.]+pt)', token)
        if m2:
            stroke["width"] = m2.group(1)
            width_for_style = float(m2.group(1).replace('pt', ''))

        m2 = re.search(r'draw opacity=([^,]+)', token)
        if m2:
            stroke["opacity"] = m2.group(1)

        m2 = re.search(r'dash pattern=\{([^}]*)\}', token)  # All text between {}
        if m2:  # The mapping between TeX and JSON is hardcoded
            key = scale_dash_pattern(m2.group(1), width_for_style)
            if key in LINE_ALIASES.keys():
                stroke["style"] = LINE_ALIASES[key]
            else:
                print(f'⚠️ The pattern', key, 'was not converted. Defaulting to a solid line')

        # Color.  Need a function to support additional color options vs just RGB
        m3 = re.search(r'draw=\{([^}]*)\}', token)  # Now see if rgb options, & pull off {}
        if m3:
            m4 = re.search(r'rgb,255:red,(\d+);green,(\d+);blue,(\d+)', m3.group(1))
            if m4:
                red, green, blue = m4.groups()
                stroke["color"] = f'rgb({red},{green},{blue})'

    else:  # No Draw parameters, so return a blank stroke
        stroke["opacity"] = 0   # Do NOT change this, it will ripple through the code.  Probably should return 2 params stroke, False if this else or stroke, True for everything else

    return stroke


def parse_fill_options(token):
    '''
    Within the first option token, it is possible to have fill style and colors
    :param token:
    :return: fill JSON opacity and RGB color.  Standard colors like 'red' or 'blue' are not supported
    '''

    #
    fill = None
    m = re.search(r'fill', token)  # Must support standalone fill with no RGB Color options
    fill = {}
    if m:
        m2 = re.search(r'fill opacity=([^,]+)', token)
        if m2:
            fill["opacity"] = m2.group(1)
        m3 = re.search(r'fill=\{([^}]*)\}', token)  # Now see if rgb options, & pull off {}
        if m3:
            m4 = re.search(r'rgb,255:red,(\d+);green,(\d+);blue,(\d+)', m3.group(1))
            if m4:
                red, green, blue = m4.groups()
                fill["color"] = f'rgb({red},{green},{blue})'
    return fill


def parse_rotation(token):
    '''
    Handle the rotation options for the following:  First is TeX, second is JSON.
        y=-1  --> "x"=1, "y"-1  No Rotation
        x=-1  -->  "x"=1, "y"-1  Rotation=-180
        x=-1, y=-1, rotation=-180  -->  "x"=-1, "y"-1  "rotation"=-180
        x = float, y = float  no rotation --> "x" = float, "y"=float  (no rotation)  <--  This is for scaling the object
        It appears that if a rotation is specified in the TeX, then the JSON is exactly replicated.
        The parsing complexity is when no rotation is specified for flipped and mirrored cases shown above

    :param token:       A token that may contain scaling and rotation information
    :return: rotation, scale         rotation is a string for angle.
                                    scale is a dictionary of form: {"x": 1, "y": -1}
    '''
    # re patterns for matching strings
    xscale_pattern = r'xscale=(-?\d*\.?\d+)'
    yscale_pattern = r'yscale=(-?\d*\.?\d+)'
    rotate_pattern = r'rotate=(-?\d*\.?\d+)'

    rotation = None
    scale = None
    m_x = re.search(xscale_pattern, token)
    m_y = re.search(yscale_pattern, token)
    m_rot = re.search(rotate_pattern, token)

    if m_x and m_y and m_rot:                   # This case:  x=-1, y=-1, rotation=-180  -->  "x"=-1, "y"-1  "rotation"=-180
        scale = {
            "x": m_x.group(1),
            "y": m_y.group(1)
        }
        rotation = m_rot.group(1)

    elif m_x and not m_y and not m_rot:           # This case: x=-1  -->  "x"=1, "y"-1  Rotation=-180
        scale = {
            "x": -float(m_x.group(1)),
            "y": -float(m_x.group(1))
        }
        rotation = '-180'

    elif not m_x and m_y and not m_rot:            # This case: y=-1  --> "x"=1, "y"-1  No Rotation
        scale = {
            "x": -float(m_y.group(1)),
            "y": m_y.group(1)
        }

    elif m_rot:
        rotation = m_rot.group(1)

    elif m_x and m_y and not m_rot:                   # This case:  x = float, y = float  no rotation
        scale = {
            "x": m_x.group(1),
            "y": m_y.group(1)
        }

    return rotation, scale


def split_options(s):
    '''
    Remove the outer brackets [] if present, and then split the comma deliminated information, excluding any comma's
    in LaTeX math blocks.

    Example: '[american voltage source, l_={$e(t), a(t)$}]'  --> ['american voltage source', 'l_={$e(t), a(t)$}']

    :param s:   Input string, similar to the example above
    :return: parts    Comma deliminated list of options
    '''

    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1]

    parts = []
    current = []
    depth_brace = 0
    in_dollar = False
    escape = False

    for char in s:
        if escape:
            current.append(char)
            escape = False
            continue

        if char == '\\':
            current.append(char)
            escape = True
            continue

        if char == '$':
            in_dollar = not in_dollar
            current.append(char)
            continue

        if not in_dollar:
            if char == '{':
                depth_brace += 1
            elif char == '}':
                depth_brace -= 1

        # Split only on commas at top level
        if char == ',' and depth_brace == 0 and not in_dollar:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

    # add last part
    if current:
        parts.append(''.join(current).strip())

    return parts


def scale_dash_pattern(dash_pattern, scale_factor):
    '''
    This takes any token option with a Line Width Pattern, removes the line width scaling, so the key matches the
    LINE_ALIAS dictionary for conversion to JSON.

    :param dash_pattern:  The on off pattern pulled from the Option   E.g.  dash pattern={on 2.8pt off 0.7pt on 0.7pt off 0.7pt}
    :param scale_factor:  Line width to remove normalization:  E.g., 0.7  -->  dash pattern / linewidth --> Key

    :return: Key value string  E.g., 'on 4pt off 1pt on 1pt off 1pt'   for this case as a possible Key in the LINE_ALIAS dictionary
    '''

    # Pattern to find number+unit pairs like '1pt', '4pt'
    pattern = r'(\d+\.?\d*)(pt)'

    def scale_match(match):
        number = float(match.group(1))
        unit = match.group(2)
        scaled_number = number / scale_factor
        # Format as integer since all original values are integers
        return f"{int(scaled_number)}{unit}"

    # Replace all number+unit pairs with scaled versions
    scaled_pattern = re.sub(pattern, scale_match, dash_pattern)

    return scaled_pattern


def parse_label_mixed_latex(text):
    '''
    This takes a label that has mixed LaTeX and non LaTeX characters and creates a list
    When the TeX code of \\ is encountered, it is replaced by a JSON newline \n
    those are grouped with the spaces preserved so \n can be inserted properly for stacked math
    :param text: '\\small $\\,\\boldsymbol{+}$  $e_c(t)$  $\\frac{a}{b} $  $\\ \\boldsymbol{-}$'
    :return: ['\\small ', '$\\,\\boldsymbol{+}$  $e_c(t)$  $\\frac{a}{b} $  $\\ \\boldsymbol{-}$']
    '''
    math_pattern = r'(\$(?:\\.|[^$])*\$)'
    parts = [p for p in re.split(math_pattern, text) if p]

    parts_new_line = ['\n' if item.strip() == '\\\\' else item for item in parts]

    return parts_new_line


def extract_label(option):
    """
    Extract label text from l={...} or l_={...}, handling:
    - nested braces outside math mode
    - ignoring braces inside $...$
    - removing outermost $...$ if present
    Returns (is_l_underscore, label_text)
    It does not handle l^, l2_, etc. type of options
    """

    # Detect prefix
    if option.startswith("l_="):
        is_l_ = True
        s = option[3:]
    elif option.startswith("l="):
        is_l_ = False
        s = option[2:]
    else:
        return None, None

    s = s.strip()

    # Must be {...}
    if not (s.startswith("{") and s.endswith("}")):
        return is_l_, None

    body = s[1:-1]

    # --- Parse for nested braces and math mode ---
    result = []
    depth = 0
    in_math = False
    escape = False

    for ch in body:
        if escape:
            result.append(ch)
            escape = False
            continue

        if ch == "\\":
            result.append(ch)
            escape = True
            continue

        if ch == "$":
            in_math = not in_math
            result.append(ch)
            continue

        if not in_math:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1

        result.append(ch)

    out = "".join(result).strip()

    # --- Remove OUTER math delimiters ONLY ---
    # Only remove ONE leading and ONE trailing $
    if out.startswith("$") and out.endswith("$") and len(out) >= 2:
        # Make sure they are matching outermost delimiters,
        # not something like "$a$ + $b$"
        inner = out[1:-1]
        if inner.count("$") % 2 == 0:   # balanced internal $ pairs
            out = inner  # strip the pair

    return is_l_, out
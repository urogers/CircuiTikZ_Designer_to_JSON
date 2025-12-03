#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversion of PHP circuit parsing utilities into Python.
"""

import re


def extract_circuitikz_content(latex_code: str) -> str | None:
    """
    Extracts the entire content of the block \\begin{circuitikz} or \\begin{tikzpicture} to \\end.
    """
    match = re.search(r'\\begin\{(circuitikz|tikzpicture)\}(.*?)\\end\{\1\}', latex_code, re.DOTALL)
    return match.group(2) if match else None


def parse_coordinate_definitions(content: str) -> dict[str, str]:
    """
    Analyzes the text and creates a map of all coordinates defined with \\coordinate.
    """
    coord_map = {}
    pattern = r'\\coordinate\s*\((.*?)\)\s*at\s*\((.*?)\);'
    for name, value in re.findall(pattern, content, re.DOTALL):
        coord_map[name.strip()] = f"({value.strip()})"
    return coord_map

def three_node_parser(tex_str):
    """
    Nodes are as follows:   "[options], (name), at (coord), {text}" where only the [options]  and (coord) are really required
    This could be done recursively, but so far only have three levels deep with 1st, & last node patterns differnt
    :param tex_str:   TeX code of form  '\\node[shape=rectangle, fill={rgb,255:red,255;green,255;blue,128}, fill opacity=0.56, draw={rgb,255:red,0;green,0;blue,160}, draw opacity=0.43, line width=2.2pt, minimum width=1.672cm, minimum height=1.172cm](X1) at (14.125, 7.875){}
                                           node[anchor=south] at ([yshift=0.04cm]X1.north east){$U_1$}
                                           node[anchor=north, align=center, text width=1.242cm, inner sep=7.2pt] at (14.125, 8.5){This is fun, $e_t$};'

    '\\node[shape=rectangle, minimum width=1.308cm, minimum height=0.59cm](x1) at (6.672, 13){}
                                              node[anchor=north, align=center, text width=0.991cm, inner sep=5pt] at (6.672, 13.312){\\Large A $e_t$};'
    :return node_content:   Parsed tokens of form [0: '3node', 1: '[shape]', 2: name, 3: coord1, 4: label1, 5: [id_anchor]', 6: id_name, 7: id_loc,
                                                   8: id_label, 9: [text options / positioning], 10: text_name, 11: text_loc, 12: [text str]
    """

    pattern_1st_node = r'\\node\[([^\]]+)\](?:\(([^)]*)\))?(?:(?:(?!;\s*node\[).)*?)at\s*(\([^)]*\))\s*\{((?:(?!\}\s*node\[).)*)\}(\s*node\[.*)'
    pattern_2nd_node = r'node\[([^\]]+)\](?:\(([^)]*)\))?(?:(?:(?!;\s*node\[).)*?)at\s*(\([^)]*\))\s*\{((?:(?!\}\s*node\[).)*)\}(\s*node\[.*)'
    pattern_last_node = r'node\[([^\]]+)\](?:\(([^)]*)\))?\s*at\s*(\([^)]*\))\s*\{((?:(?!\}\s*;).)*)\}\s*;'
    node_content = None
    m1 = re.search(pattern_1st_node, tex_str, re.VERBOSE | re.DOTALL)
    if m1:
        shape = m1.group(1).strip()
        name = m1.group(2).strip()
        coord1 = m1.group(3).strip()
        label1 = (m1.group(4) or '').strip()
        node_content = ['3node', '[' + shape + ']', name, coord1, label1]

        m2 = re.search(pattern_2nd_node, m1.group(5), re.VERBOSE | re.DOTALL)
        if m2:
            id_anchor = (m2.group(1) or '').strip()
            id_label = (m2.group(2) or '').strip()
            id_loc = (m2.group(3) or '').strip()
            id_text = (m2.group(4) or '').strip()


            node_content += ['[' + id_anchor + ']', id_label, id_loc,  id_text]

        m3 = re.search(pattern_last_node, m2.group(5), re.VERBOSE | re.DOTALL)
        if m3:
            label_anchor = (m3.group(1) or '').strip()
            label_label = (m3.group(2) or '').strip()
            label_loc = (m3.group(3) or '').strip()
            label_text = (m3.group(4) or '').strip()


            node_content += ['[' + label_anchor + ']', label_label, label_loc, label_text]

    return node_content


def two_node_parser(tex_str):
    """
    Nodes are as follows:   "[options], (name), at (coord), {text}" where only the [options]  and (coord) are really required
    This could be done recursively, but so far only have three levels deep with 1st, & last node patterns differnt
    :param tex_str:   TeX shape of form '\\node[shape=rectangle, minimum width=1.308cm, minimum height=0.59cm](x1) at (6.672, 13){}
                                          node[anchor=north, align=center, text width=0.991cm, inner sep=5pt] at (6.672, 13.312){\\Large A $e_t$};'

                     or a devie of form  '\\node[npn, bodydiode, nobase, photo, schottky base, tr circle, rotate=-45, yscale=-1](N1) at (10.75, 7.98){}
                                            node[anchor=north west] at (N1.text){$Q_1$};
    :return node_content:   Parsed tokens of form [0: '2node' or 'device', 1: '[shape]', 2: name, 3: coord1, 4: label1, 5: [id_anchor]', 6: id_name, 7: id_loc,
                                                   8: id_label]
    """

    pattern_1st_node = r'\\node\[([^\]]+)\](?:\(([^)]*)\))?(?:(?:(?!;\s*node\[).)*?)at\s*(\([^)]*\))\s*\{((?:(?!\}\s*node\[).)*)\}(\s*node\[.*)'
    pattern_last_node = r'node\[([^\]]+)\](?:\(([^)]*)\))?\s*at\s*(\([^)]*\))\s*\{((?:(?!\}\s*;).)*)\}\s*;'

    node_content = None

    pattern_shape = r'\\node\s*\[\s*shape\s*='  # Check if form is \\node[shape = ...
    if re.search(pattern_shape, tex_str):
        node_content = ['2node']
    else:
        node_content = ['device']

    m1 = re.search(pattern_1st_node, tex_str, re.VERBOSE | re.DOTALL)
    if m1:
        shape = m1.group(1).strip()
        name = m1.group(2)
        coord1 = m1.group(3).strip()
        label1 = (m1.group(4) or '').strip()
        node_content += [ shape, name, coord1, label1]

        m2 = re.search(pattern_last_node, m1.group(5), re.VERBOSE | re.DOTALL)
        if m2:
            label_anchor = (m2.group(1) or '').strip()
            label_label = (m2.group(2) or '').strip()
            label_loc = (m2.group(3) or '').strip()
            label_text = (m2.group(4) or '').strip()

            node_content += ['[' + label_anchor + ']', label_label, label_loc, label_text]

    return node_content


def tokenize_all_draw_contents(content: str):
    """
    First this extracts ALL \\draw and \\node commands from a corresponding tex string of content.
    Second, for each "type" of circuitikz item, those are tokenized into a list
    The first token in the list is a keyword describing what that list is "to",  "node" for a single node,
    "wire", "shape" for a shape object with text, and "device" for active type of devices NPN, etc.

    Because the content is tokenized, then the tokens in each list are ordered data
    """

    wire_turn_pattern = r"\([^()]*\)|(?:to|node)?\[(?:[^[\]]|\[(?:[^[\]]|\[[^[\]]*\])*\])*\]|--|\-\||\|-"

    clean_content = remove_comments(content)
    all_commands = []


    # Extract \node associated with shapes of form:  \\node[xxx]() at (x, y){label1} node[xxx]() at (x1, y1){label2} ... ;
    # Return order matches the form \node[npn](N1) at (10.75, 7.98){} node[anchor=west] at (N1.text){$Q_1$};
    # {label} extraction supports LaTeX encoding \small $e(t)$, etc. as well as being empty


    # Iterate through all TeX commands, and finds those with nodes
    clean_line = clean_content.split('\n')
    for line in clean_line:
        node_count = len(re.findall(r'node\[', line))       # Count # of 'node[' patterns

        if node_count == 3:
            node_content = three_node_parser(line)
            all_commands.append(node_content)

        elif node_count == 2:
            node_content = two_node_parser(line)      # This supports the \node[shape=...]  \node[device ...] and is not a simple draw node
            all_commands.append(node_content)

        elif node_count == 1:  # This is a device of a simple single node
            pattern_one_node =  r'\\node\[([^\]]+)\](?:\(([^)]*)\))?\s*at\s*(\([^)]*\))\s*\{((?:(?!\}\s*;).)*)\}\s*;'
            pattern_shape = r'\\node\s*\[\s*shape\s*='  # Check if form is \\node[shape = ...
            if re.search(pattern_shape, line):
                node_content = ['node']
            else:
                node_content = ['device']
            m1 = re.search(pattern_one_node, line, re.VERBOSE | re.DOTALL)
            if m1:

                node_type = m1.group(1).strip()
                name = m1.group(2)
                coord1 = m1.group(3).strip()
                label1 = (m1.group(4) or '').strip()

                node_content += [node_type, name, coord1, label1]

                all_commands.append(node_content)

    # Iterate and parse the draw commands, but ignore ones with arrows
    draw_pattern = r'\\draw(\[.*?\])?(.*?);'
    for match in re.finditer(draw_pattern, clean_content, re.VERBOSE | re.DOTALL):
        options = match.group(1) or ''
        cmd_content = match.group(2) or ''
        if re.search(r'\[.*?(<-|->|<->).*?\]', options):
            continue  # skip draws with arrows
        if not options:
            pre_token = (cmd_content.strip())   # No Options Listed
        else:
            pre_token = (cmd_content.strip()+options.strip())

        tokens = re.findall(wire_turn_pattern, pre_token)
        # tokens = [t.strip() for t in rough_tokens if t.strip()]

        # Now do the "to" or "wire"
        if any(t.startswith('to') for t in tokens):
            if tokens[1].startswith("to[") and tokens[1].endswith("]"):  # Remove to, keep the brackets
                tokens[1] = tokens[1][2:]
            node_content = ["to"] + tokens

            all_commands.append(node_content)
        else:  # This is a bug, because if this is not a wire, then it will return "junk"
            node_content =  ["wire"] + tokens
            all_commands.append(node_content)

    # Now parse all \\path lines.  Notice, at this stage, all that should be there is a path, which will be coded as a wire
    # that has at least two segments / right angles
    path_pattern = r'\\path(\[.*?\])?(.*?);'
    for match in re.finditer(path_pattern, clean_content, re.VERBOSE | re.DOTALL):
        options = match.group(1) or ''
        cmd_content = match.group(2) or ''
        if re.search(r'\[.*?(<-|->|<->).*?\]', options):
            continue  # skip draws with arrows

        if not options:
            pre_token = (cmd_content.strip())   # No Options Listed
        else:
            pre_token = (cmd_content.strip()+options.strip())

        tokens = re.findall(wire_turn_pattern, pre_token)
        # tokens = [t.strip() for t in rough_tokens if t.strip()]

        # Now do the "to" or "wire"
        if any(t.startswith('to') for t in tokens):
            if tokens[1].startswith("to[") and tokens[1].endswith("]"):  # Remove to, keep the brackets
                tokens[1] = tokens[1][2:]
            node_content = ["to"] + tokens

            all_commands.append(node_content)
        else:  # This is a bug, because if this is not a wire, then it will return "junk" and pass silently
            node_content =  ["wire"] + tokens
            all_commands.append(node_content)

    return all_commands if all_commands else None


def remove_comments(content: str) -> str:
    """
    Removes LaTeX comments from the content.
    A comment starts with % and continues to the end of the line.

    Find the first unescaped '%' (i.e., a comment), then remove it and everything after it
    """
    return re.sub(r'(?<!\\)%.*', '', content)

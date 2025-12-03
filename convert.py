#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processes all input-*.tex files, extracts CircuiTikZ content from CircuiTikZ Designer, and writes output-*.json.

AI Process to Python from     https://github.com/pierpaolopalazzo/CircuiTikZ-convert

Bugs:
General Shape Function:
\node[shape=rectangle, fill={rgb,255:red,255;green,0;blue,0}, fill opacity=0.56, draw={rgb,255:red,255;green,0;blue,0}, draw opacity=0.43, line width=1.3pt, dash pattern={on 1.3pt off 2.6pt}, minimum width=1.704cm, minimum height=1.204cm]
(X1) at (14.125, 7.875){}
node[anchor=south] at ([yshift=0.04cm]X1.north east){$U_1$}
node[anchor=north, align=center, text width=1.305cm, inner sep=6.3pt] at (14.125, 8.5){This is fun, $e_t$};
Notice the options, name of X1, and anchor can be shared as functions across other devices

Need to handle anchor's, relative positioning etc. in complex 2node and 3node items.    With that, this works well on
the relatively complex test cases.  The default is ver
"""

import json
import glob
import os

from pathlib import Path
from tikz_tokens_2_json import *
from gen_tikz_tokens import *

def initialize_output(filename: str) -> None:
    """
    Check whether the output file exists, delete it and verify deletion.
    Exit the script if there are permission problems.
    """
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception as e:
            raise SystemExit(f"❌ Error: Unable to delete old file '{filename}'. Check permissions. ({e})")
        if os.path.exists(filename):
            raise SystemExit(f"❌ Error: The file '{filename}' was not deleted correctly.")

def main():
    input_files = glob.glob("*.tex")                   # All files with .tex in a directory
    # input_files = glob.glob("a_specific_file.tex")    # Single file name
    # input_files = glob.glob("input-*.tex")            # All files with input-*.tex in a directory

    # Both lines are needed for multiple files.  These are the test vectors
    # filenames = ["./Test_Files/crazy_circuit_test.tex", "./Test_Files/block_diagram_test.tex"]
    # input_files = [f for f in filenames if glob.os.path.exists(f)]

    if not input_files:
        print("❌ Error: No files matching 'input-*.tex' found.")
        return

    print(f"📁 Found {len(input_files)} files to process:")
    for f in input_files:
        print(f"  - {f}")
    print()

    for input_filename in input_files:
        output_filename = input_filename.replace("input-", "output-").replace(".tex", ".json")
        print(f"🔄 Processing: {input_filename} → {output_filename}")

        json_objects = []
        current_position = {"x": 0, "y": 0}
        initialize_output(output_filename)

        if not os.path.exists(input_filename):
            print(f"⚠️  Error: File '{input_filename}' not found, skipping.")
            continue

        with open(input_filename, encoding="utf-8") as f:
            latex_code = f.read()

        circuit_content = extract_circuitikz_content(latex_code)
        if not circuit_content:
            error_data = {"error": "No valid \\begin{circuitikz} block found."}
            Path(output_filename).write_text(json.dumps(error_data, indent=2), encoding='utf-8')
            print(f"❌ Error: No CircuiTikZ block found. Saved details to '{output_filename}'.")
            continue

        # Get \coordinates mapping -- this works, but coordinate mapping is not yet supported later.
        coord_map = parse_coordinate_definitions(circuit_content)

        # Tokenize reach \draw \node line --> list of lists containing , separated tokens for each.
        token_blocks = tokenize_all_draw_contents(circuit_content)

        # Create a JSON Object for each \draw \ node token blocks
        if token_blocks:
            for tokens in token_blocks:
                #  No named coords for CircuiTikZ Designer so will not process them
                # processed = replace_named_coords(block, coord_map)   #<-- That function probably needs to be rewritten
                next_jason_object = convert_tokens_to_json(tokens)
                json_objects.append(next_jason_object)

        data = {"version": "0.1",
                "components": json_objects
                }
        json_output = json.dumps(data, indent=2, ensure_ascii=False)
        Path(output_filename).write_text(json_output, encoding='utf-8')
        print(f"✅ Successfully saved to '{output_filename}'.")

    print("\n🎉 All files processed!\n")

# ==================================================================
if __name__ == "__main__":
    main()
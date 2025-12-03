# CircuiTikZ Designer to JSON
Converts TikZ code developed with CircuiTikZ Designer to JSON for importing back into [CircuiTikZ Designer](https://www.circuit2tikz.tf.fau.de/designer/)

The initial version of this software was an AI port of the PHP code by pierpaolopalazzo in [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) to Python. That port was then modified to support CircuiTikZ Designer at the expense of general CircuiTikZ codes.  

## Functionality
- Convert files of the form  *.tex into a JSON.
- Output file *.json  (same name as the .tex input file)
- Supports complex /node /draw structures with mixed text and LaTeX math
- Supports multi-segment wires, block diagrams, ... (See Example Below)

 
<p align="center">
  <img src="https://raw.githubusercontent.com/urogers/CircuiTikZ_Designer_to_JSON/master/crazy_circuit_test.png" width=50% height=50% alt="Test Circuit Example"/ >
</p>

## Caveat   
- This was not designed to support generic TikZ or CircuiTikZ files.  Those will most likely not work because they are not really supported by CircuiTikZ Designer.  For example, none of the output-*.json files at [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) are currently recognized by CircuitTikZ Designer.
- The software started as a fast-and-dirty way to processing my TikZ codes to JSON, and evolved from there to support complexity.  As such, a refactoring would improve the current release.
- Regular Expression (re) is used throughout.  With re comes "brittle" implementations, but attempts have been made to reduce undesireable behavior. Most of the re patterns were developed using AI and much debugging.

## Requirements
- Python 3.xx
- Packages:  json, glob, re, os

## Project Structure
- `convert.py` — Main conversion code focused on File I/O.
- `gen_tikz_tokens.py` — Parse a .tex file and create a list of tokens for each TikZ line.
- `tikz_tokens_2_json` — Parse the tokens for each line and create a correspoing JSON dictionary

## Usage

1. **Prepare input files**  
   Place the LaTeX files with a \begin{tikzpicture} or \begin{circuitikz} with a pattern `*.tex`.

2. **Run the conversion**  
   - Run the Python code directly (Navigate to the directory containing your *.tex files and the three .py files for this project)
     ```
     python convert.py
     ```
      _or_  
     Use your favorite Python development environment
 
 3. **Change which files are parsed**
    - Use any .py editor to edit `convert.py` file and modify the variable: input_files
    - There are many examples given via commented code near `def main():`

## Test Files
- The [Test Files](Test_Files) directory contains test TeX files that stress various complexities the parser must handle relative to what CircuiTikZ Designer can produce.
- Please ensure you run any bug fixes against those files (e.g., test vectors) and validate your changes.

## Credits
- **CircuiTikZ-Convert**: [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) a PHP starting point for this effort.
- **CircuiTikZ Designer**: [CircuiTikZ Designer](https://circuit2tikz.tf.fau.de/designer/) was used for LaTeX circuit design.
- **CircuiTikZ**: The [CircuiTikZ](https://www.ctan.org/pkg/circuitikz) LaTeX package was essential for circuit creation.

## License
This project is distributed under the [MIT License](LICENSE).

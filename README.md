# CircuiTikZ Designer to JSON
Converts TikZ code developed with CircuiTikZ Designer to JSON for importing back into [CircuiTikZ](https://www.circuit2tikz.tf.fau.de/designer/)

The initial version of this software was an AI port of the PHP code by pierpaolopalazzo in [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) to Python (only because I did not know PHP and it did not support all the features I needed).  

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

## Test Files
- The [Test Files](Test_Files) directory contains test TeX files that stress various complexities the parser must handle.
- Please ensure you run any bug fixes against those files (e.g., test vectors) and validate your changes.

## Credits
- **CircuiTikZ-Convert**: [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) a PHP starting point for this effort.
- **CircuiTikZ Designer**: [CircuiTikZ Designer](https://circuit2tikz.tf.fau.de/designer/) was used for LaTeX circuit design.
- **CircuiTikZ**: The [CircuiTikZ](https://www.ctan.org/pkg/circuitikz) LaTeX package was essential for circuit creation.

## License
This project is distributed under the [MIT License](LICENSE).

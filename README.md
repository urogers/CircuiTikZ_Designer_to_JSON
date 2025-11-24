# CircuiTikZ_Designer_to_JSON
Converts TikZ code developed with CircuiTikZ Designer to JSON for importing back into [CircuiTikZ](https://www.circuit2tikz.tf.fau.de/designer/)

The initial version of this software was an AI port of the PHP code by pierpaolopalazzo in [CircuiTikZ-convert](https://github.com/pierpaolopalazzo/CircuiTikZ-convert) to Python (only because I did not know PHP).  The software as evolved from there, with

## Functionality
- Convert files of the form  *.tex into a JSON.
- Output file *.json  (same name as the .tex input file)
- Supports complex /node /draw structures with mixed LaTeX text
- Supports multi-segment wires, block diagrams, ... (See Examples Below)
- Error handling is currently rudimentary
  
- Note:  This was not designed to support generic TikZ or CircuiTikZ files.  Those may or may not work.

## Requirements
- Python 3.xx
- Packages:  json, glob, re


## Credits
-**CircuiTikZ-Convert**: [CircuiTikZ-convert] (https://github.com/pierpaolopalazzo/CircuiTikZ-convert)
- **CircuiTikZ Designer**: [CircuiTikZ Designer](https://circuit2tikz.tf.fau.de/designer/) was used for LaTeX circuit design.
- **CircuiTikZ**: The [CircuiTikZ](https://www.ctan.org/pkg/circuitikz) LaTeX package was essential for circuit creation. 

# SBOannotator
<img align="right" src="SBOannotator_logo.png" alt="drawing" width="250"/>

**SBOannotator: a Python tool for the automated assignment of Systems Biology Ontology terms**

[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=plastic)](http://opensource.org/licenses/LGPL-3.0)
[![Latest version](https://img.shields.io/badge/Latest_version-3.0.1-brightgreen.svg?style=plastic)](https://github.com/draeger-lab/SBOannotator/releases/)
![Code Size](https://img.shields.io/github/languages/code-size/draeger-lab/SBOannotator.svg?style=plastic)
[![PyPI version](https://badge.fury.io/py/SBOannotator.svg)](https://badge.fury.io/py/SBOannotator)
![PyPI - Format](https://img.shields.io/pypi/format/SBOannotator)
[![PyPI downloads](https://img.shields.io/pypi/dm/SBOannotator.svg)](https://pypistats.org/packages/SBOannotator)
[![DOI](https://img.shields.io/badge/DOI-10.1093%2Fbioinformatics%2Fbtad437-blue.svg?style=plastic)](https://doi.org/10.1093/bioinformatics/btad437)

Developers : [Nantia Leonidou](https://github.com/NantiaL) & Elisabeth Fritze& Jiahui Hu
___________________________________________________________________________________________________________


### Overview
This project transforms SBOannotator from a static, hard-coded tool into a dynamic, intelligent system for annotating Systems Biology Ontology (SBO) terms in SBML models. The enhanced system integrates real-time SBO term retrieval, multiple enzymology data sources, and LLM-assisted annotation—significantly improving accuracy and usability while preserving the core rule-based strengths. A standalone desktop GUI with interactive visualization makes powerful annotation capabilities accessible to a broader community of systems biology researchers.
The system delivers three key innovations:
Automated GitHub integration for real-time SBO file updates;


A three-layer rule-based annotation workflow;


A deep-learning classifier achieving 94% accuracy across 42 biochemical reaction classes.


### Desktop App

+ Mac: download dmg which is saved in the root directory:`sboannotator.dmg`

  If ERROR occurs, input command in terminal to bypass security check: 

   `sudo xattr -r -d com.apple.quarantine /Applications/main.app`
    !But it only can finish rule based annotation be:cause of complex dependencies and direcotory operation with llm.




### Input data
+ an SBML document
+ an sbo terms (.json or obo)(optional)


### Outputs
+ Rule Based Enhanced Annotated libSBML model
+ LLM Annototed libSBML model
+ Uptodate SBO terms (.json) 

### Usage
This tool has the following dependencies:

python >=3.9.6

Packages:

sqlite3
libsbml
collections
requests
json
time

-`pip install -r requirements.txt`

run `python main.py` in the command line within the project folder.

If ERROR occurs, check the current version of Python: 

- `python --version'`
- `conda install python>=3.9.6`

### Exemplary models and results
The folder `models/Customer_Models` contains a  models as it were downloaded from
the BiGG database. 
The annotated models after using the Rule based SBOannotator and target reaction filtered for llm are listed in the folder named `models/Enhanced_Annotated_Models`.
The annotated models after using the LLM recommendationi are listed in the models/LLM_Annotated_Models

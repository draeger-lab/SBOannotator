# SBOannotator
<img align="right" src="SBOannotator_logo.png" alt="drawing" width="200"/>

**SBOannotator: a Python tool for the automated assignment of Systems Biology Ontology terms**

[![License (LGPL version 3)](https://img.shields.io/badge/license-LGPLv3.0-blue.svg?style=plastic)](http://opensource.org/licenses/LGPL-3.0)
[![Latest version](https://img.shields.io/badge/Latest_version-0.9-brightgreen.svg?style=plastic)](https://github.com/draeger-lab/SBOannotator/releases/)
![Code Size](https://img.shields.io/github/languages/code-size/draeger-lab/SBOannotator.svg?style=plastic)
![Downloads of all releases](https://img.shields.io/github/downloads/draeger-lab/SBOannotator/total.svg?style=plastic)
[![DOI](https://img.shields.io/badge/DOI-10.20944%2Fpreprints202012.0296.v1-blue.svg?style=plastic)](https://www.preprints.org/manuscript/202302.0317/v1)

*Authors* : Elisabeth Fritze & [Nantia Leonidou](https://github.com/NantiaL)
___________________________________________________________________________________________________________

### How to cite the SBOannotator?

The online version of the SBOannotator is described in this article: https://www.preprints.org/manuscript/202302.0317/v1

### Overview
The SBOannotator is the first standalone tool that automatically assigns SBO terms to multiple entities of a given SBML model, 
The main focus lies on the reactions, as the correct assignment of precise SBO annotations requires their extensive classification. 
Our implementation does not consider only top-level terms but examines the functionality of the underlying enzymes to 
allocate precise and highly specific ontology terms to biochemical reactions. 
Transport reactions are examined separately and are classified based on the mechanism of molecule transport. 
Pseudo-reactions that serve modeling purposes are given reasonable terms to distinguish between biomass production and the 
import or export of metabolites. Finally, other model entities, such as metabolites and genes, are annotated with appropriate terms. 
Including SBO annotations in the models will enhance the reproducibility, usability, and analysis of biochemical networks.


### Installation
```
pip install SBOannotator
```

### Prerequisites

This tool has the following dependencies:

python >=3.8.5

Packages:
* sqlite3
* libsbml
* collections
* requests
* json
* time

### Input data
+ `doc`: an SBML document
+ `model_libsbml`: SBML model of interest
+ `modelType`: type of modelling framework (see below)
+ `modelAnnotated`: True, if model already includes annotations with EC numbers
+ `database_name`: name of imported database, without extension
+ `new_filename`: file name for output model

Types of modelling framework accepted:
- constraint-based
- logical
- continuous
- discrete
- hybrid
- logical


### Outputs
+ `model_libsbml`: Annotated libsbml model
  

### Usage
To run SBOannotator use the `main.py` script and modify the parameters in the `readSBML` and `sbo_annotator` 
functions as wished.

If ERROR occurs, check the current version of Python: 

- `python --version'`
- `conda install python=3.8.5`

### Exemplary models and Results
The folder `models/BiGG_Models` contains all the tested models as they were downloaded from
the BiGG database. 
The annotated models after using the SBOannotator are listed in the folder named `models/Annotated_Models`.

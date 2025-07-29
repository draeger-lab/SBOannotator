__author__ = 'Nantia Leonidou & Elisabeth Fritze & Enhanced with Unified Provider'

""" SBOannotatorEnhanced Class: Same as original but with unified EC annotation """

import sqlite3
from libsbml import writeSBMLToFile
from collections import Counter
import requests
import json
from tqdm import tqdm
from adapter import callForECAnnotRxnUnified

# Import all original functions
from SBOannotator import *

class SBOannotatorEnhanced:
    """Enhanced SBOannotator class with unified data sources"""
    
    def __init__(self, database_name):
        """Initialize the enhanced SBOannotator"""
        self.database_name = database_name
    
    def sbo_annotator_enhanced(self, doc, model_libsbml, modelType, new_filename):
        """
        Enhanced main function - identical to original except uses callForECAnnotRxnUnified
        
        Inputs:
            doc: SBML document
            model_libsbml (libsbml-model): input model (unannotated)
            modelType (str): type of modelling framework
            new_filename (str): file name for output model
        Output:
            Annotated libsbml model
        """

        # connect to database
        con = sqlite3.connect(self.database_name)
        cur = con.cursor()

        try:
            with open(self.database_name + '.sql') as schema:
                cur.executescript(schema.read())
        except:
            try:
                with open('create_dbs.sql') as schema:
                    cur.executescript(schema.read())
            except:
                print("Warning: Could not load database schema")

        for reaction in model_libsbml.reactions:
            if not addSBOfromDB(reaction, cur):
                # print(reaction.getId())
                reaction.unsetSBOTerm()

                # needs to be checked first
                splitTransportBiochem(reaction)

                checkBiomass(reaction)
                checkSink(reaction)
                checkExchange(reaction)
                checkDemand(reaction)

                # if transporter
                if reaction.getSBOTermID() == 'SBO:0000655':
                    checkPassiveTransport(reaction)
                    checkActiveTransport(reaction)
                    if reaction.getSBOTermID() != 'SBO:0000657':  # if not active
                        checkCoTransport(reaction)
                        if reaction.getSBOTermID() == 'SBO:0000654':  # if not co-transport
                            splitSymAntiPorter(reaction)
                # if metabolic reaction
                if reaction.getSBOTermID() == 'SBO:0000176':
                    addSBOviaEC(reaction, cur)  # use create_dbs.sql
                # if no hit found in db and still annotated as generic biochemical reaction
                if reaction.getSBOTermID() == 'SBO:0000176':
                    checkRedox(reaction)
                    (reaction)
                    checkDecarbonylation(reaction)
                    checkDecarboxylation(reaction)
                    checkDeamination(reaction)
                    checkPhosphorylation(reaction)

        # If rxns still have general SBO term, assign more specific terms via EC numbers
        print('\nAssign SBO terms via E.C. numbers (Enhanced with Unified Provider)... \n')
        for reaction in tqdm(model_libsbml.reactions):

            if reaction.getSBOTermID() == 'SBO:0000176':
                # if EC number exists for reaction, use it to derive SBO term via DB use
                if 'ec-code' in reaction.getAnnotationString():
                    ECNums = getECNums(reaction)
                    multipleECs(reaction, ECNums)
                # Enhanced: if EC number does not exist for reaction, use unified provider
                else:
                    callForECAnnotRxnUnified(reaction)  # The only change!

        addSBOforMetabolites(model_libsbml)

        addSBOforGenes(model_libsbml)

        addSBOforModel(doc, modelType)

        addSBOforGroups(model_libsbml)

        addSBOforParameters(model_libsbml)

        addSBOforCompartments(model_libsbml)

        addSBOforRateLaw(model_libsbml)

        addSBOforEvents(model_libsbml)

        write_to_file(model_libsbml, new_filename)
        print(f'\nEnhanced model with SBO annotations written to {new_filename} ...\n')

        # close database connection
        cur.close()
        con.close()

        return model_libsbml


# Provide the same function interface as the original SBOannotator.py
def sbo_annotator_enhanced(doc, model_libsbml, modelType, database_name, new_filename):
    """
    Enhanced version of sbo_annotator function with unified provider
    Usage is exactly the same as the original sbo_annotator
    """
    annotator = SBOannotatorEnhanced(database_name)
    return annotator.sbo_annotator_enhanced(doc, model_libsbml, modelType, new_filename)
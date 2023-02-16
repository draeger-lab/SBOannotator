import zipfile
from SBOannotator import *
from libsbml import *
import sys
import os

################################################################
# start SBOannotator and annotate all models from BiGG
################################################################
# assign directory
directory = 'models/'

# store console output
sys.stdout = open('SBOannotator_output.log', 'w')

# count models processed
count = 0

# iterate over downloaded models in the directory
for path, subdirs, files in os.walk(directory):
    for name in files:
        if ('.DS_Store' not in name) and ('annotated' not in name):
            count += 1

            # store file name
            file_name = name

            # read model
            doc = readSBML("models/BiGG_Models/" + file_name)
            model = doc.getModel()
            print(file_name, 'is processed ...')

            # count number of SBO terms assigned in the input file
            print("Before SBOannotator:")
            # print exact number of each SBO terms assigned
            print('Exact before: Reactions:', printCounts(model)[0], ',', 'Metabolites:', printCounts(model)[1], ',',
                  'Genes:', printCounts(model)[2], ',', 'Compartments:', printCounts(model)[3])
            # print total number of assigned SBO terms
            print('Total before: Reactions:', len(printCounts(model)[0]), ',', 'Metabolites:', len(printCounts(model)[1]), ',',
                  'Genes:', len(printCounts(model)[2]), ',', 'Compartments:', len(printCounts(model)[3]))

            # run SBOannotator
            sbo_annotator(doc, model, 'constraint-based', True, 'create_dbs', 'models/Annotated_Models/'+model.getId()+'_SBOannotated.xml')

            print('-----------------------------')
            print('After SBOannotator:')
            # print exact number of each SBO terms assigned
            print('Exact after: Reactions:', printCounts(model)[0], ',', 'Metabolites:', printCounts(model)[1], ',',
                  'Genes:', printCounts(model)[2], ',', 'Compartments:', printCounts(model)[3])
            # print total number of assigned SBO terms
            print('Total after: Reactions:', len(printCounts(model)[0]), ',', 'Metabolites:', len(printCounts(model)[1]), ',',
                  'Genes:', len(printCounts(model)[2]), ',', 'Compartments:', len(printCounts(model)[3]))
            print("\n")

print(count, 'models processed')
sys.stdout.close()

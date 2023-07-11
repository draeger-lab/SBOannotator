from SBOannotator import *
from libsbml import *
import sys
import os
import time

""" Main function created to be used by the webpage app only! """

start = time.time()

def wrapper(file):
    # store file path
    file_path = os.path.join('uploads', file)
    doc = readSBML(file_path)
    model = doc.getModel()

    print('-----------------------------')
    print('SBO before: ')
    print('-----------------------------')
    print(f'Reactions: {printCounts(model)[0]}')
    print(f'\nMetabolites: {printCounts(model)[1]}')
    print(f'\nGenes: {printCounts(model)[2]}')
    print(f'\nCompartments: {printCounts(model)[3]}')

    sbo_annotator(doc, model, 'constraint-based', True, 'create_dbs',
                  'models/Annotated_Models/' + model.getId() + '_SBOannotated.xml')

    print('-----------------------------')
    print('SBO after: ')
    print('-----------------------------')
    print(f'Reactions: {printCounts(model)[0]}')
    print(f'\nMetabolites: {printCounts(model)[1]}')
    print(f'\nGenes: {printCounts(model)[2]}')
    print(f'\nCompartments: {printCounts(model)[3]}')

    # counter-check which reactions remained without SBO annotation
    for r in model.reactions:
        if r.isSetSBOTerm() is False:
            print('\n*********************')
            print(f'No SBO set for reactions: {r.getId()}')
            print('\n*********************')


if __name__ == '__main__':
    # The file name is passed as a command-line argument
    file = sys.argv[1]
    wrapper(file)

end = time.time()
print(f'SBOannotator done after:  {end - start}s')

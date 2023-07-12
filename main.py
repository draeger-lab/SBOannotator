__author__ = 'Nantia Leonidou'

from SBOannotator import *
from libsbml import *
import time

start = time.time()

doc = readSBML('models/BiGG_Models/RECON1.xml')
model = doc.getModel()

print('-----------------------------')
print('SBO before: ')
print('-----------------------------')
print(f'Reactions: {printCounts(model)[0]}')
print(f'\nMetabolites: {printCounts(model)[1]}')
print(f'\nGenes: {printCounts(model)[2]}')
print(f'\nCompartments: {printCounts(model)[3]}')


sbo_annotator(doc, model, 'constraint-based', True, 'create_dbs', 'models/Annotated_Models/'+model.getId()+'_SBOannotated.xml')

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

end = time.time()
print(f'SBOannotator done after:  {end - start}s')
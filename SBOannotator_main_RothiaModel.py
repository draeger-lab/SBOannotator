__author__ = 'Nantia Leonidou'

from SBOannotator import *
from libsbml import *
import time

start = time.time()

doc = readSBML('/Users/leonidou/Nextcloud/Belgium_internship_Rothia_mucilaginosa/Computer_modeling/05_after_MCC.xml')
model = doc.getModel()

print('-----------------------------')
print('SBO before: ')
print('-----------------------------')
print(f'Reactions: {printCounts(model)[0]}')
print(f'\nMetabolites: {printCounts(model)[1]}')
print(f'\nGenes: {printCounts(model)[2]}')
print(f'\nCompartments: {printCounts(model)[3]}')


sbo_annotator(doc, model, 'constraint-based', True, 'create_dbs', '/Users/leonidou/Nextcloud/Belgium_internship_Rothia_mucilaginosa/Computer_modeling/SBOannotator_output/'+model.getId()+'_SBOannotated.xml')

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

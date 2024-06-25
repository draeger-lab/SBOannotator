__author__ = 'Nantia Leonidou'

from SBOannotator import *
from libsbml import *
import time

start = time.time()

doc = readSBML('../../models/BiGG_Models/iYO844.xml')
model = doc.getModel()

print('--------------------------------------------------------------------------------------------------------')
print("➡️ \033[32;40m SBO Terms – Before:\033[0m")
print('--------------------------------------------------------------------------------------------------------')
print(f'Reactions: {printCounts(model)[0]}')
print(f'\nMetabolites: {printCounts(model)[1]}')
print(f'\nGenes: {printCounts(model)[2]}')
print(f'\nCompartments: {printCounts(model)[3]}')
print('--------------------------------------------------------------------------------------------------------')

sbo_annotator(doc, model, 'constraint-based','create_dbs', '../../models/Annotated_Models/'+model.getId()+'_SBOannotated.xml')

print('--------------------------------------------------------------------------------------------------------')
print("➡️ \033[32;40m SBO Terms – After:\033[0m")
print('--------------------------------------------------------------------------------------------------------')
print(f'Reactions: {printCounts(model)[0]}')
print(f'\nMetabolites: {printCounts(model)[1]}')
print(f'\nGenes: {printCounts(model)[2]}')
print(f'\nCompartments: {printCounts(model)[3]}\n')
print('--------------------------------------------------------------------------------------------------------')

# counter-check which reactions remained without SBO annotation
for r in model.reactions:
    if r.isSetSBOTerm() is False:
        print('\n*********************')
        print(f'No SBO set for reactions: {r.getId()}')
        print('\n*********************')

end = time.time()
print(f'\n🕑\033[31;40m SBOannotator done after:  {end - start} sec \033[0m')

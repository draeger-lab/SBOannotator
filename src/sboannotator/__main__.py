__author__ = 'Nantia Leonidou'

#from sboannotator import *
from SBOannotator import *
from libsbml import *
import time

start = time.time()

doc = readSBML('../../models/BiGG_Models/RECON1.xml')
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
print(f'\n🕑\033[32;40m SBOannotator done after:  {end - start} sec \033[0m')






#from sboannotator import *
from SBOannotatorEnhancedClass import *

start_enhanced= time.time()

# Load a fresh model for enhanced annotator to ensure fair comparison
doc2 = readSBML('../../models/BiGG_Models/RECON1.xml')
model2 = doc2.getModel()

print('--------------------------------------------------------------------------------------------------------')
print("➡️ \033[32;40m SBO Terms – Before (Enhanced):\033[0m")
print('--------------------------------------------------------------------------------------------------------')
print(f'Reactions: {printCounts(model2)[0]}')
print(f'\nMetabolites: {printCounts(model2)[1]}')
print(f'\nGenes: {printCounts(model2)[2]}')
print(f'\nCompartments: {printCounts(model2)[3]}')
print('--------------------------------------------------------------------------------------------------------')

sbo_annotator_enhanced(doc2, model2, 'constraint-based','create_dbs', '../../models/Annotated_Models/'+model2.getId()+'_SBOannotated_enhanced.xml')

print('--------------------------------------------------------------------------------------------------------')
print("➡️ \033[32;40m SBO Terms – After (Enhanced):\033[0m")
print('--------------------------------------------------------------------------------------------------------')
print(f'Reactions: {printCounts(model2)[0]}')
print(f'\nMetabolites: {printCounts(model2)[1]}')
print(f'\nGenes: {printCounts(model2)[2]}')
print(f'\nCompartments: {printCounts(model2)[3]}\n')
print('--------------------------------------------------------------------------------------------------------')

# counter-check which reactions remained without SBO annotation
for r in model2.reactions:
    if r.isSetSBOTerm() is False:
        print('\n*********************')
        print(f'No SBO set for reactions: {r.getId()}')
        print('\n*********************')

end_enhanced = time.time()
print(f'\n🕑\033[32;40m Enhanced SBOannotator done after:  {end_enhanced - start_enhanced} sec \033[0m')
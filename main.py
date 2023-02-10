from SBOannotator import *
from libsbml import *

doc = readSBML("models/iCGB21FR.xml")
model = doc.getModel()

print('-----------------------------')
print('SBO before: ')
print('-----------------------------')
print('Reactions:', printCounts(model)[0])
print('\nMetabolites:', printCounts(model)[1])
print('\nGenes:', printCounts(model)[2])
print('\nCompartments:', printCounts(model)[3])

sbo_annotator(doc, model, 'constraint-based', True, 'create_dbs', 'models/'+model.getId()+'_SBOannotated.xml')

print('-----------------------------')
print('SBO after: ')
print('-----------------------------')
print('Reactions:', printCounts(model)[0])
print('\nMetabolites:', printCounts(model)[1])
print('\nGenes:', printCounts(model)[2])
print('\nCompartments:', printCounts(model)[3])


# counter-check which reactions remained without SBO annotation
for r in model.reactions:
    if r.isSetSBOTerm() is False:
        print('\n*********************')
        print('No SBO set for reactions: ', r.getId())
        print('\n*********************')

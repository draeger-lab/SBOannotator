from SBOannotator import *
from libsbml import *

doc = readSBML("RECON1.xml")
model = doc.getModel()

print('-----------------------------')
print('SBO before: ')
print('-----------------------------')
print('Reactions:', printCounts(model)[0])
print('\nMetabolites:', printCounts(model)[1])
print('\nGenes:', printCounts(model)[2])

sbo_annotator(model, 'create_dbs', model.getId()+'_annotated.xml')

print('-----------------------------')
print('SBO after: ')
print('-----------------------------')
print('Reactions:', printCounts(model)[0])
print('\nMetabolites:', printCounts(model)[1])
print('\nGenes:', printCounts(model)[2])

# counter-check which reactions remained without SBO annotation
for r in model.reactions:
    if r.isSetSBOTerm() is False:
        print('No SBO set for reactions: ', r.getId())

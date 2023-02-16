from collections import Counter
from libsbml import*
import pandas as pd
import os

##################################################################
# Compare assigned SBOs before and after our tool
##################################################################
# create empty dataframe
df = pd.DataFrame()

model_names, rxns_total_before, rxns_total_after = [], [], []
for line in open('SBOannotator_output.log'):
    if 'processed' in line:
        model_names.append(line.split(' ')[0].replace('.xml','').strip())

    if 'Total before:' in line:
        rxns_total_before.append(line.split('Total before:')[1].split(',')[0].split(':')[1].strip())

    if 'Total after:' in line:
            rxns_total_after.append(line.split('Total after:')[1].split(',')[0].split(':')[1].strip())

# add columns to empty dataframe
df['Model'] = model_names
df['Before'] = rxns_total_before
df['After'] = rxns_total_after
# set index
df.set_index('Model', inplace=True)

print(df)
# save results in csv
df.to_csv("/Users/leonidou/Nextcloud/SBOannotator_Publication/Reactions_SBO_beforeANDafter.csv")

##################################################################
# Save counts of terms before and after
##################################################################
# iterate over downloaded models in the directory
sbo_terms_before, sbo_terms_after = [],[]
for path, subdirs, files in os.walk('models/'):
    for name in files:
        if ('.DS_Store' not in name) and ('annotated' in name):

            doc = readSBML("models/Annotated_Models/" + name)
            model = doc.getModel()

            for r in model.reactions:
                sbo_terms_after.append(r.getSBOTerm())

        if ('.DS_Store' not in name) and ('annotated' not in name):
            doc = readSBML("models/BiGG_Models/" + name)
            model = doc.getModel()

            for r in model.reactions:
                sbo_terms_before.append(r.getSBOTerm())

print(Counter(sbo_terms_before))
print(Counter(sbo_terms_after))

# save as table
df_before = pd.DataFrame.from_dict(Counter(sbo_terms_before), orient='index').reset_index()
df_after = pd.DataFrame.from_dict(Counter(sbo_terms_after), orient='index').reset_index()
# store files
df_before.to_csv('/Users/leonidou/Nextcloud/SBOannotator_Publication/count_SBO_before.csv')
df_after.to_csv('/Users/leonidou/Nextcloud/SBOannotator_Publication/count_SBO_after.csv')

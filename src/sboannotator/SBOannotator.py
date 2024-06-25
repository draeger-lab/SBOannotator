__author__ = 'Nantia Leonidou & Elisabeth Fritze'

""" SBOannotator: a Python tool for the automated assignment of Systems Biology Ontology terms """

import sqlite3
from libsbml import writeSBMLToFile
from collections import Counter
import requests
import json
from tqdm import tqdm

# define globals
DEMAND_IDS = ['_DM_', '_DEMAND_', '_demand_', 'Demand_']
SINK_IDS = ['_SK_', '_SINK_', '_sink_', 'Sink_']
EXCHANGE_IDS = ['_EX_', '_EXCHANGE_', '_exchange_', 'Exchange_']
BIOMASS_IDS = ['BIOMASS', 'biomass', 'growth', 'GROWTH', 'Growth']
RXN_BOUND_PARAMETERS = ["cobra_default_lb", "cobra_default_ub", "cobra_0_bound", "minus_inf", "plus_inf"]


def getCompartmentlessSpeciesId(speciesReference):
    speciesId = speciesReference.getSpecies()
    species = speciesReference.getModel().getSpecies(speciesId)
    compartment = species.getCompartment()
    wasteStringLen = len(compartment) + 1
    return speciesId[:-wasteStringLen]


def getCompartmentFromSpeciesRef(speciesReference):
    speciesId = speciesReference.getSpecies()
    species = speciesReference.getModel().getSpecies(speciesId)
    compartment = species.getCompartment()
    return compartment


def returnCompartment(identifier):
    return identifier[-1]


def getReactantIds(react):
    lst = []
    for metabolite in react.getListOfReactants():
        lst.append(metabolite.getSpecies())
    return lst


def getCompartmentlessReactantIds(react):
    lst = []
    for metabolite in react.getListOfReactants():
        lst.append(getCompartmentlessSpeciesId(metabolite))
    return lst


def getProductIds(react):
    lst = []
    for metabolite in react.getListOfProducts():
        lst.append(metabolite.getSpecies())
    return lst


def getCompartmentlessProductIds(react):
    lst = []
    for metabolite in react.getListOfProducts():
        lst.append(getCompartmentlessSpeciesId(metabolite))
    return lst


def getListOfMetabolites(react):
    lst = []
    for reactant in react.getListOfReactants():
        lst.append(reactant)
    for product in react.getListOfProducts():
        lst.append(product)
    return lst


def getMetaboliteIds(reac):
    return getReactantIds(reac) + getProductIds(reac)


# def getCompartmentlessMetaboliteIds(react):
#     return getCompartmentlessReactantIds(react) + getCompartmentlessProductIds(react)

def getReactantCompartmentList(react):
    compartments = []
    for metabolite in react.getListOfReactants():
        compartment = getCompartmentFromSpeciesRef(metabolite)
        compartments.append(compartment)
    return set(compartments)


def getProductCompartmentList(react):
    compartments = []
    for metabolite in react.getListOfProducts():
        compartment = getCompartmentFromSpeciesRef(metabolite)
        compartments.append(compartment)
    return set(compartments)


def getCompartmentList(react):
    metabolites = getListOfMetabolites(react)
    compartments = []
    for metabolite in metabolites:
        compartments.append(getCompartmentFromSpeciesRef(metabolite))
    return set(compartments)


def getCompartmentDict(react):
    compartmentDict = {}
    for compartment in getCompartmentList(react):
        compartmentDict[compartment] = []
        for metabolite in getListOfMetabolites(react):
            if '_' + compartment in metabolite.getSpecies():
                compartmentDict[compartment].append(getCompartmentlessSpeciesId(metabolite))
    return compartmentDict


def moreThanTwoCompartmentTransport(react):
    return len(getCompartmentList(react)) > 2


def isProtonTransport(react):
    reactants = react.getListOfReactants()
    products = react.getListOfProducts()
    protonTransport = False
    if len(products) == len(reactants) == 1:
        if len(getCompartmentList(react)) == 2:
            reactant = getCompartmentlessSpeciesId(reactants[0])
            product = getCompartmentlessSpeciesId(products[0])
            protonTransport = reactant == product == 'M_h'
    return protonTransport


def soleProtonTransported(react):
    compDict = getCompartmentDict(react)
    soleProton = False
    for compartment in compDict:
        if len(compDict[compartment]) == 1:
            soleProton = soleProton or compDict[compartment][0] == 'M_h'
    return soleProton and not isProtonTransport(react) and not moreThanTwoCompartmentTransport(react)


def getECNums(react):
    lines = react.getAnnotationString().split('\n')
    ECNums = []
    for line in lines:
        if 'ec-code' in line:
            ECNums.append(line.split('ec-code/')[1][:-3])
    return ECNums


def multipleECs(react, ECNums):
    # store first digits of all annotated EC numbers
    lst = []
    for ec in ECNums:
        lst.append(ec.split('.')[0])

    # if ec numbers are from different enzyme classes, based on first digit
    # no ambiguous classification possible
    if len(set(lst)) > 1:
        react.setSBOTerm('SBO:0000176')  # metabolic rxn

    # if ec numbers are from the same enzyme classes,
    # assign parent SBO term based on first digit in EC number
    else:

        # Oxidoreductases
        if '1' in set(lst):
            react.setSBOTerm('SBO:0000200')
        # Transferase
        elif '2' in set(lst):
            react.setSBOTerm('SBO:0000402')
        # Hydrolases
        elif '3' in set(lst):
            react.setSBOTerm('SBO:0000376')
        # Lyases
        elif '4' in set(lst):
            react.setSBOTerm('SBO:0000211')
        # Isomerases
        elif '5' in set(lst):
            react.setSBOTerm('SBO:0000377')
        # Ligases
        elif '6' in set(lst):
            react.setSBOTerm('SBO:0000695')
        # Translocases
        elif '7' in set(lst):
            react.setSBOTerm('SBO:0000185')
        # Metabolic reactions
        else:
            react.setSBOTerm('SBO:0000176')


def handleMultipleOrNoECs(react, ECNums):
    # note: this step may take longer if input model does not contain any annotations at all or no EC numbers for particular rxns.
    if len(ECNums) == 0:
        react.setSBOTerm('SBO:0000176')
    # if multiple EC numbers annotated in model
    else:
        multipleECs(react, ECNums)


def callForECAnnotRxn(rxn):
    """ API call to obtain EC number of a single reaction"""

    ECNums = []
    try:
        res = requests.get('http://bigg.ucsd.edu/api/v2/universal/reactions/' + rxn.getId()[2:])
        bigg_json = res.content.decode('utf-8')
        info = json.loads(bigg_json)

        for link in info['database_links']['EC Number']:
            ECNums.append(link['id'])

        multipleECs(rxn, ECNums)

    except:
        rxn.setSBOTerm('SBO:0000176')


def splitTransportBiochem(react):
    """" Classify between transport reactions and biochemical reactions """
    if len(getCompartmentList(react)) > 1 and not soleProtonTransported(react):
        react.setSBOTerm('SBO:0000655')
    else:
        react.setSBOTerm('SBO:0000176')


def checkSink(react):
    if any(prefix in react.getId() for prefix in SINK_IDS):
        react.setSBOTerm('SBO:0000632')


def checkExchange(react):
    if any(prefix in react.getId() for prefix in EXCHANGE_IDS):
        react.setSBOTerm('SBO:0000627')


def checkDemand(react):
    if any(prefix in react.getId() for prefix in DEMAND_IDS):
        react.setSBOTerm('SBO:0000628')


def checkBiomass(react):
    if any(prefix in react.getId() for prefix in BIOMASS_IDS):
        react.setSBOTerm('SBO:0000629')


def checkPassiveTransport(react):
    reactants = react.getListOfReactants()
    products = react.getListOfProducts()
    if len(reactants) == len(products) == 1:
        reactant = reactants[0].getSpecies()
        product = products[0].getSpecies()
        if returnCompartment(reactant) != returnCompartment(product):
            react.setSBOTerm('SBO:0000658')


def checkActiveTransport(react):
    reactantIds = []
    for metabolite in react.getListOfReactants():
        reactantIds.append(metabolite.getSpecies())
    if 'M_atp_c' in reactantIds or 'M_pep_c' in reactantIds:
        react.setSBOTerm('SBO:0000657')
        if react.getReversible():
            print(f'Active reaction but reversible {react.getId()}')


def checkCoTransport(react):
    reactants = react.getListOfReactants()
    if len(reactants) > 1:
        react.setSBOTerm('SBO:0000654')


def splitSymAntiPorter(react):
    if len(getCompartmentList(react)) > 2:
        pass
    elif 1 == len(getReactantCompartmentList(react)) == len(getProductCompartmentList(react)):
        react.setSBOTerm('SBO:0000659')
    else:
        react.setSBOTerm('SBO:0000660')


def checkPhosphorylation(react):
    name = react.getName()
    atpIsReactant = 'M_atp_c' in getReactantIds(react)
    adpIsProduct = 'M_adp_c' in getProductIds(react)
    if 'phosphorylase' in name or 'kinase' in name:
        react.setSBOTerm('SBO:0000216')


def hasReactantPair(reaction, met1, met2):
    reactants = getCompartmentlessReactantIds(reaction)
    products = getCompartmentlessProductIds(reaction)
    return (met1 in reactants and met2 in products) or (met2 in reactants and met1 in products)


def checkRedox(react):
    isRedox = False
    isRedox = isRedox or hasReactantPair(react, 'M_pyr', 'M_lac_L')
    isRedox = isRedox or hasReactantPair(react, 'M_pyr', 'M_lac_D')
    isRedox = isRedox or hasReactantPair(react, 'M_pyr', 'M_lac__L')
    isRedox = isRedox or hasReactantPair(react, 'M_pyr', 'M_lac__D')
    isRedox = isRedox or hasReactantPair(react, 'M_nad', 'M_nadh')
    isRedox = isRedox or hasReactantPair(react, 'M_nadp', 'M_nadph')
    isRedox = isRedox or hasReactantPair(react, 'M_fad', 'M_fadh2')
    isRedox = isRedox or hasReactantPair(react, 'M_h20', 'M_h2o2')
    if isRedox:
        react.setSBOTerm('SBO:0000200')


def checkGlycosylation(react):
    isGlycosylation = False
    isGlycosylation = isGlycosylation or hasReactantPair(react, 'M_ppi', 'M_prpp')
    isGlycosylation = isGlycosylation or hasReactantPair(react, 'M_udpglcur', 'M_udp')
    if isGlycosylation:
        react.setSBOTerm('SBO:0000217')


def checkDecarbonylation(react):
    if not react.getReversible():
        if 'M_co' in getCompartmentlessProductIds(react):
            react.setSBOTerm('SBO:0000400')


def checkDecarboxylation(react):
    if not react.getReversible():
        if 'M_co2' in getCompartmentlessProductIds(react):
            react.setSBOTerm('SBO:0000399')


def checkDeamination(react):
    if not react.getReversible():
        waterAdded = 'M_h2o' in getCompartmentlessReactantIds(react)
        nh4Removed = 'M_nh4' in getCompartmentlessProductIds(react)
        if waterAdded and nh4Removed:
            react.setSBOTerm('SBO:0000401')


def addSBOviaEC(react, cur):
    # cur.execute(): case insensitive
    if len(getECNums(react)) == 1:
        ECnum = getECNums(react)[0]
        splittedEC = ECnum.split('.')
        if len(splittedEC) == 4:
            ECpos1 = splittedEC[0]
            ECpos1to2 = ECpos1 + '.' + splittedEC[1]
            ECpos1to3 = ECpos1to2 + '.' + splittedEC[2]
            query4 = cur.execute("""SELECT sbo_term
                                     FROM ec_to_sbo 
                                    WHERE ecnum = ?""", [ECnum])
            result4 = cur.fetchone()
            if result4 is not None:
                sbo4 = result4[0]
                react.setSBOTerm(sbo4)
            else:
                query3 = cur.execute("""SELECT sbo_term
                                          FROM ec_to_sbo 
                                         WHERE ecnum = ?""", [ECpos1to3])
                result3 = cur.fetchone()
                if result3 is not None:
                    sbo3 = result3[0]
                    react.setSBOTerm(sbo3)
                else:
                    query2 = cur.execute("""SELECT sbo_term
                                              FROM ec_to_sbo
                                             WHERE ecnum = ?""", [ECpos1to2])
                    result2 = cur.fetchone()
                    if result2 is not None:
                        sbo2 = result2[0]
                        react.setSBOTerm(sbo2)
                    else:
                        query1 = cur.execute("""SELECT sbo_term
                                                  FROM ec_to_sbo 
                                                 WHERE ecnum = ?""", [ECpos1])
                        result1 = cur.fetchone()
                        if result1 is not None:
                            sbo1 = result1[0]
                            react.setSBOTerm(sbo1)
    else:
        handleMultipleOrNoECs(react, getECNums(react))


def addSBOfromDB(react, cur):
    """ Uses BiGG identifiers to assign SBO terms from DB """
    reactID = react.getId()
    query = cur.execute("""SELECT sbo_term 
                        FROM bigg_to_sbo 
                        WHERE  bigg_reactionid = ?""", [reactID])
    result = cur.fetchone()
    if result is not None:
        sbo_term = result[0]
        react.setSBOTerm(sbo_term)
        return True  # if SBO term was updated
    else:
        return False


def addSBOforMetabolites(model):
    # add metabolites SBO
    for met in model.species:
        met_id = met.getId()
        model.getSpecies(met_id).setSBOTerm('SBO:0000247')


def addSBOforGenes(model):
    # add genes SBO
    model_fbc = model.getPlugin('fbc')
    # if model has genes, not always given
    if model_fbc is not None:
        for gene in model_fbc.getListOfGeneProducts():
            gene.setSBOTerm('SBO:0000243')


def addSBOforModel(doc, modelType):
    'Add SBO Term to define the underlying modelling framework'
    if modelType == 'constraint-based':
        doc.setSBOTerm('SBO:0000693')
    elif modelType == 'logical':
        doc.setSBOTerm('SBO:0000234')
    elif modelType == 'continuous':
        doc.setSBOTerm('SBO:0000062')
    elif modelType == 'discrete':
        doc.setSBOTerm('SBO:0000063')
    elif modelType == 'hybrid':
        doc.setSBOTerm('SBO:0000681')
    else:
        doc.setSBOTerm('SBO_0000004')


def addSBOforGroups(model):
    mplugin = model.getPlugin('groups')
    # if groups are in model defined
    if mplugin is not None:
        for grp in mplugin.getListOfGroups():
            grp.setSBOTerm('SBO:0000633')


def addSBOforParameters(model):
    for param in model.getListOfParameters():
        # reaction bounds
        if 'R_' in param.getId():
            param.setSBOTerm('SBO:0000625')
        # default values for bounds
        elif param.getId() in RXN_BOUND_PARAMETERS:
            param.setSBOTerm('SBO:0000626')
        # length
        elif 'length' in param.getId() or 'Length' in param.getId():
            param.setSBOTerm('SBO:0000466')
        # area
        elif 'area' in param.getId() or 'Area' in param.getId():
            param.setSBOTerm('SBO:0000467')
        # volume
        elif 'volume' in param.getId() or 'Volume' in param.getId():
            param.setSBOTerm('SBO:0000468')
        # any parameter
        else:
            param.setSBOTerm('SBO: 0000545')


def addSBOforCompartments(model):
    for cmp in model.getListOfCompartments():
        cmp.setSBOTerm('SBO:0000290')


def addSBOforRateLaw(model):
    for r in model.reactions:
        if r.getKineticLaw():
            r.getKineticLaw().setSBOTerm('SBO:0000001')


def addSBOforEvents(model):
    if model.getListOfEvents() is not None:
        for event in model.getListOfEvents():
            event.setSBOTerm('SBO:0000231')
            if event.getTrigger() is not None:
                event.getTrigger().setSBOTerm('SBO:0000171')
            if event.getDelay() is not None:
                event.getDelay().setSBOTerm('SBO:0000225')


def write_to_file(model, new_filename):
    new_document = model.getSBMLDocument()
    writeSBMLToFile(new_document, new_filename)


def sbo_annotator(doc, model_libsbml, modelType, database_name, new_filename):
    """
    Main function to run SBOannotator

    Inputs:
        doc: SBML document
        model_libsbml (libsbml-model): input model (unannotated)
        modelType (str): type of modelling framework
        database_name (str): name of imported database, without extension
        new_filename (str): file name for output model
    Output:
        Annotated libsbml model
    """

    # connect to database
    con = sqlite3.connect(database_name)
    cur = con.cursor()

    with open(database_name + '.sql') as schema:
        cur.executescript(schema.read())

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
                checkGlycosylation(reaction)
                checkDecarbonylation(reaction)
                checkDecarboxylation(reaction)
                checkDeamination(reaction)
                checkPhosphorylation(reaction)

    # If rxns still have general SBO term, assign more specific terms via EC numbers
    print('\nAssign SBO terms via E.C. numbers: \n')
    for reaction in tqdm(model_libsbml.reactions):

        if reaction.getSBOTermID() == 'SBO:0000176':
            # if EC number exists for reaction, use it to derive SBO term via DB use
            if 'ec-code' in reaction.getAnnotationString():
                ECNums = getECNums(reaction)
                multipleECs(reaction, ECNums)
            # if EC number does not exist for reaction, use it to derive SBO term via API call
            else:
                callForECAnnotRxn(reaction)

    addSBOforMetabolites(model_libsbml)

    addSBOforGenes(model_libsbml)

    addSBOforModel(doc, modelType)

    addSBOforGroups(model_libsbml)

    addSBOforParameters(model_libsbml)

    addSBOforCompartments(model_libsbml)

    addSBOforRateLaw(model_libsbml)

    addSBOforEvents(model_libsbml)

    write_to_file(model_libsbml, new_filename)
    print(f'\nModel with SBO annotations written to {new_filename} ...\n')

    # close database connection
    cur.close()
    con.close()

    return model_libsbml


def printCounts(model_sbml):
    model_fbc = model_sbml.getPlugin('fbc')

    # count assigned SBO
    SBO_rxns = [r.getSBOTermID() for r in model_sbml.reactions]
    SBO_mets = [m.getSBOTermID() for m in model_sbml.species]
    SBO_genes = [g.getSBOTermID() for g in model_fbc.getListOfGeneProducts() if model_fbc is not None]
    SBO_comps = [c.getSBOTermID() for c in model_sbml.compartments]

    return Counter(SBO_rxns), Counter(SBO_mets), Counter(SBO_genes), Counter(SBO_comps)

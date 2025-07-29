# 1. Abstract interface definition: All database adapters need to implement these two methods
from abc import ABC, abstractmethod
from typing import List

from sboannotator.SBOannotator import multipleECs


class EnzymeDataAdapter(ABC):
    @abstractmethod
    def extract_ids_from_annotation(self, annotation_string: str) -> List[str]:
        """Extract database IDs from annotation"""
        pass

    @abstractmethod
    def query_ec_numbers(self, database_id: str) -> List[str]:
        """Query API based on database ID to get EC numbers"""
        pass


# 2. KEGG database adapter implementation
class KEGGAdapter(EnzymeDataAdapter):
    def extract_ids_from_annotation(self, annotation_string: str) -> List[str]:
        """Extract KEGG reaction ID from annotation, e.g. R10747"""
        import re
        pattern = r'kegg\.reaction/([R]\d+)'
        return re.findall(pattern, annotation_string)

    def query_ec_numbers(self, kegg_reaction_id: str) -> List[str]:
        """Use KEGG REST API to query EC numbers"""
        import requests
        try:
            url = f"http://rest.kegg.jp/get/rn:{kegg_reaction_id}"
            response = requests.get(url)

            if response.status_code == 200:
                ec_numbers = []
                for line in response.text.split('\n'):
                    if line.startswith('ENZYME'):
                        # Example line: ENZYME      1.1.1.1
                        ec_num = line.split()[1]
                        ec_numbers.append(ec_num)
                return ec_numbers
        except:
            pass
        return []


# 3. BiGG database adapter implementation
class BiGGAdapter(EnzymeDataAdapter):
    def extract_ids_from_annotation(self, annotation_string: str) -> List[str]:
        """Extract BiGG reaction ID from annotation, get through reaction object ID"""
        # BiGG adapter does not extract ID from annotation, but directly uses reaction ID
        return []
    
    def query_ec_numbers(self, reaction_id: str) -> List[str]:
        """Use BiGG API to query EC numbers"""
        import requests
        import json
        
        try:
            # Remove reaction ID prefix 'R_' if exists
            clean_id = reaction_id[2:] if reaction_id.startswith('R_') else reaction_id
            url = f"http://bigg.ucsd.edu/api/v2/universal/reactions/{clean_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                info = response.json()
                ec_numbers = []
                if 'database_links' in info and 'EC Number' in info['database_links']:
                    for link in info['database_links']['EC Number']:
                        ec_numbers.append(link['id'])
                return ec_numbers
        except:
            pass
        return []

# 4. Reactome database adapter implementation (return parsing not yet implemented)
# class ReactomeAdapter(EnzymeDataAdapter):
#     def extract_ids_from_annotation(self, annotation_string: str) -> List[str]:
#         """Extract Reactome reaction ID from annotation, e.g. R-ATH-71850"""
#         import re
#         pattern = r'reactome\.reaction/(R-\w+-\d+)'
#         return re.findall(pattern, annotation_string)
#
#     def query_ec_numbers(self, reactome_id: str) -> List[str]:
#         """Use Reactome REST API to query EC numbers (to be completed)"""
#         import requests
#         try:
#             url = f"https://reactome.org/ContentService/data/query/{reactome_id}"
#             response = requests.get(url)
#
#             if response.status_code == 200:
#                 data = response.json()
#                 # TODO: Parse JSON data, extract EC numbers (depending on specific structure)
#                 return []
#         except:
#             pass
#         return []


# 5. Unified provider: Integrate all Adapters, unified access to EC numbers
class UnifiedEnzymeDataProvider:
    def __init__(self):
        self.bigg_adapter = BiGGAdapter()
        self.kegg_adapter = KEGGAdapter()
        # self.reactome_adapter = ReactomeAdapter()

    def get_ec_numbers_from_reaction(self, reaction) -> List[str]:
        """Get EC numbers from all data sources in the reaction object"""
        all_ec_numbers = []
        annotation_string = reaction.getAnnotationString()
        
        # 1. First try BiGG API
        bigg_ecs = self.bigg_adapter.query_ec_numbers(reaction.getId())
        all_ec_numbers.extend(bigg_ecs)
        
        # 2. Then try KEGG
        kegg_ids = self.kegg_adapter.extract_ids_from_annotation(annotation_string)
        for kegg_id in kegg_ids:
            kegg_ecs = self.kegg_adapter.query_ec_numbers(kegg_id)
            all_ec_numbers.extend(kegg_ecs)
        
        # # 3. Try Reactome (if needed)
        # reactome_ids = self.reactome_adapter.extract_ids_from_annotation(annotation_string)
        # for reactome_id in reactome_ids:
        #     reactome_ecs = self.reactome_adapter.query_ec_numbers(reactome_id)
        #     all_ec_numbers.extend(reactome_ecs)

        return list(set(all_ec_numbers))  # Return after deduplication


# 6. New unified EC query function
def callForECAnnotRxnUnified(rxn):
    """
    Use unified provider to get EC numbers from data sources like BiGG and KEGG,
    and call multipleECs function to process results
    """
    provider = UnifiedEnzymeDataProvider()
    ECNums = provider.get_ec_numbers_from_reaction(rxn)

    if ECNums:
        from sboannotator.SBOannotator import multipleECs
        multipleECs(rxn, ECNums)
    else:
        rxn.setSBOTerm('SBO:0000176')  # If no EC number found, still annotate as metabolic reaction

# doc = readSBML('../../models/BiGG_Models/iYO844.xml')
# model = doc.getModel()
#!/usr/bin/env python3

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sboannotator.adapter import ReactomeAdapter

class TestReactomeAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = ReactomeAdapter()

    def test_annotation_to_ec_workflow_R_CEL_191983(self):
        """Test full workflow from R-CEL-191983 annotation to EC number 1.-.-.-"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-CEL-191983"/>'

        # Step 1: Extract Reactome ID
        reactome_ids = self.adapter.extract_ids_from_annotation(annotation)
        print(f"Extracted IDs from annotation: {reactome_ids}")
        self.assertEqual(reactome_ids, ['R-CEL-191983'], f"Expected ['R-CEL-191983'] but got {reactome_ids}")

        # Step 2: Query EC numbers
        ec_numbers = self.adapter.query_ec_numbers('R-CEL-191983')
        print(f"EC numbers for R-CEL-191983: {ec_numbers}")

        # Step 3: Verify expected EC number
        expected_ec = '1.-.-.-'
        self.assertIn(expected_ec, ec_numbers, f"Expected EC {expected_ec} but got {ec_numbers}")

    def test_annotation_to_ec_workflow_R_CFA_191983_empty(self):
        """Test full workflow from R-CFA-191983 annotation should return empty EC numbers"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-CFA-191983"/>'

        # Step 1: Extract Reactome ID
        reactome_ids = self.adapter.extract_ids_from_annotation(annotation)
        print(f"Extracted IDs from annotation: {reactome_ids}")
        self.assertEqual(reactome_ids, ['R-CFA-191983'], f"Expected ['R-CFA-191983'] but got {reactome_ids}")

        # Step 2: Query EC numbers (should be empty)
        ec_numbers = self.adapter.query_ec_numbers('R-CFA-191983')
        print(f"EC numbers for R-CFA-191983: {ec_numbers}")

        # Step 3: Verify empty result
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")

    def test_annotation_to_ec_workflow_R_MMU_191983(self):
        """Test full workflow from R-MMU-191983 annotation to EC number 1.-.-.-"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-MMU-191983"/>'

        # Step 1: Extract Reactome ID
        reactome_ids = self.adapter.extract_ids_from_annotation(annotation)
        print(f"Extracted IDs from annotation: {reactome_ids}")
        self.assertEqual(reactome_ids, ['R-MMU-191983'], f"Expected ['R-MMU-191983'] but got {reactome_ids}")

        # Step 2: Query EC numbers
        ec_numbers = self.adapter.query_ec_numbers('R-MMU-191983')
        print(f"EC numbers for R-MMU-191983: {ec_numbers}")

        # Step 3: Verify expected EC number
        expected_ec = '1.-.-.-'
        self.assertIn(expected_ec, ec_numbers, f"Expected EC {expected_ec} but got {ec_numbers}")

    def test_get_ec_numbers_from_api_GO_0008395_complete(self):
        """Test if GO:0008395/complete endpoint returns EC number 1.-.-.-"""
        api_url = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/GO:0008395/complete"
        ec_numbers = self.adapter._get_ec_numbers_from_api(api_url)
        print(f"EC numbers returned from {api_url}: {ec_numbers}")

        # Check if the expected EC number is in the results
        expected_ec = "1.-.-.-"
        self.assertIn(expected_ec, ec_numbers,
                      f"Expected EC {expected_ec} but got {ec_numbers}")

    def test_get_activity_links_from_reactome_R_CEL_191983(self):
        """Test if R-CEL-191983 page returns QuickGO link for GO:0008395"""
        reactome_url = "https://reactome.org/content/detail/R-CEL-191983"
        activity_links = self.adapter._get_activity_links_from_reactome(reactome_url)
        print(f"Activity links found for R-CEL-191983: {activity_links}")

        # Check if the expected QuickGO link is in the results
        expected_link = "https://www.ebi.ac.uk/QuickGO/term/GO:0008395"
        self.assertIn(expected_link, activity_links,
                     f"Expected {expected_link} in activity links but got {activity_links}")


    
    def test_extract_ids_from_annotation_reactome(self):
        """Test extraction of Reactome reaction ID from annotation string"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-RNO-70938"/>'
        ids = self.adapter.extract_ids_from_annotation(annotation)
        self.assertEqual(ids, ['R-RNO-70938'])

    def test_extract_ids_from_annotation_R_CEL_191983(self):
        """Test extraction of R-CEL-191983 from annotation string"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-CEL-191983"/>'
        ids = self.adapter.extract_ids_from_annotation(annotation)
        self.assertEqual(ids, ['R-CEL-191983'])

    def test_extract_ids_from_annotation_metanetx(self):
        """Test that MetaNetX annotation returns empty list"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/metanetx.reaction/MNXR104238"/>'
        ids = self.adapter.extract_ids_from_annotation(annotation)
        self.assertEqual(ids, [], f"MetaNetX should not be extracted by ReactomeAdapter, got {ids}")

    def test_query_ec_numbers_R_RNO_70938(self):
        """Test if R-RNO-70938 returns EC number 1.5.1.8"""
        ec_numbers = self.adapter.query_ec_numbers('R-RNO-70938')
        print(f"EC numbers returned for R-RNO-70938: {ec_numbers}")
        self.assertIn('1.5.1.8', ec_numbers, f"Expected EC 1.5.1.8 but got {ec_numbers}")

    def test_query_ec_numbers_R_ATH_70938_empty(self):
        """Test if R-ATH-70938 returns empty EC numbers"""
        ec_numbers = self.adapter.query_ec_numbers('R-ATH-70938')
        print(f"EC numbers returned for R-ATH-70938: {ec_numbers}")
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")

    def test_query_ec_numbers_R_DDI_70938(self):
        """Test if R-DDI-70938 returns EC number 1.5.1.8"""
        ec_numbers = self.adapter.query_ec_numbers('R-DDI-70938')
        print(f"EC numbers returned for R-DDI-70938: {ec_numbers}")
        self.assertIn('1.5.1.8', ec_numbers, f"Expected EC 1.5.1.8 but got {ec_numbers}")

    def test_query_ec_numbers_R_CEL_191983(self):
        """Test if R-CEL-191983 returns EC number 1.-.-.-"""
        ec_numbers = self.adapter.query_ec_numbers('R-CEL-191983')
        print(f"EC numbers returned for R-CEL-191983: {ec_numbers}")
        self.assertIn('1.-.-.-', ec_numbers, f"Expected EC 1.-.-.- but got {ec_numbers}")

    def test_convert_to_api_url(self):
        """Test QuickGO URL conversion"""
        quickgo_url = "https://www.ebi.ac.uk/QuickGO/term/GO:0047130"
        expected_api_url = "https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/GO:0047130/complete"

        print(f"\n输入 QuickGO URL: {quickgo_url}")
        api_url = self.adapter._convert_to_api_url(quickgo_url)
        print(f"转换后的 API URL: {api_url}")
        print(f"期望的 API URL: {expected_api_url}")

        self.assertEqual(api_url, expected_api_url)
        print("✅ URL转换成功！")





if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sboannotator.adapter import SEEDAdapter

class TestSEEDAdapter(unittest.TestCase):
    
    def setUp(self):
        self.adapter = SEEDAdapter()
    
    def test_extract_ids_from_annotation(self):
        """Test extraction of SEED reaction ID from annotation string"""
        annotation = '<rdf:li rdf:resource="http://identifiers.org/seed.reaction/rxn00753"/>'
        ids = self.adapter.extract_ids_from_annotation(annotation)
        self.assertEqual(ids, ['rxn00753'])


    
    def test_query_ec_numbers_rxn00753(self):
        """Test if rxn00753 returns EC number 2.3.1.6"""
        ec_numbers = self.adapter.query_ec_numbers('rxn00753')
        print(f"EC numbers returned for rxn00753: {ec_numbers}")
        self.assertIn('2.3.1.6', ec_numbers, f"Expected EC 2.3.1.6 but got {ec_numbers}")

    def test_query_ec_numbers_rxn08094(self):
        """Test if rxn00753 returns EC number 1.2.1.M9"""
        ec_numbers = self.adapter.query_ec_numbers('rxn08094')
        print(f"EC numbers returned for rxn00753: {ec_numbers}")
        self.assertIn('1.2.1.M9', ec_numbers, f"Expected EC 1.2.1.M9 but got {ec_numbers}")
    def test_query_ec_numbers_rxn11326_empty(self):
        """Test if rxn11326 returns empty EC numbers"""
        ec_numbers = self.adapter.query_ec_numbers('rxn11326')
        print(f"EC numbers returned for rxn11326: {ec_numbers}")
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")
    
    def test_query_ec_numbers_rxn08028_empty(self):
        """Test if rxn08028 returns empty EC numbers"""
        ec_numbers = self.adapter.query_ec_numbers('rxn08028')
        print(f"EC numbers returned for rxn08028: {ec_numbers}")
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")
    
    def test_query_ec_numbers_rxn09795_empty(self):
        """Test if rxn09795 returns empty EC numbers"""
        ec_numbers = self.adapter.query_ec_numbers('rxn09795')
        print(f"EC numbers returned for rxn09795: {ec_numbers}")
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")
    
    def test_query_ec_numbers_rxn10171_empty(self):
        """Test if rxn10171 returns empty EC numbers"""
        ec_numbers = self.adapter.query_ec_numbers('rxn10171')
        print(f"EC numbers returned for rxn10171: {ec_numbers}")
        self.assertEqual(ec_numbers, [], f"Expected empty list but got {ec_numbers}")
    
    def test_query_ec_numbers_rxn09476(self):
        """Test if rxn09476 returns EC number 1.3.3.6"""
        ec_numbers = self.adapter.query_ec_numbers('rxn09476')
        print(f"EC numbers returned for rxn09476: {ec_numbers}")
        self.assertIn('1.3.3.6', ec_numbers, f"Expected EC 1.3.3.6 but got {ec_numbers}")
    
    def test_query_ec_numbers_rxn08762(self):
        """Test if rxn08762 returns EC number 3.6.3.10"""
        ec_numbers = self.adapter.query_ec_numbers('rxn08762')
        print(f"EC numbers returned for rxn08762: {ec_numbers}")
        self.assertIn('3.6.3.10', ec_numbers, f"Expected EC 3.6.3.10 but got {ec_numbers}")

    def test_query_ec_numbers_rxn08767(self):
        """Test that rxn08767 returns EC 2.3.1.16"""
        adapter = SEEDAdapter()
        results = adapter.query_ec_numbers("rxn08767")

        print(f"Results for rxn08767: {results}")

        # Should return ['2.3.1.16'] for this thiolase reaction
        self.assertEqual(results, ['2.3.1.16'])
if __name__ == '__main__':
    unittest.main()
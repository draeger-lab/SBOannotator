import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sboannotator.adapter import (
    ReactomeAdapter,
    BiGGAdapter,
    KEGGAdapter,
    SEEDAdapter,
    UnifiedEnzymeDataProvider,
    callForECAnnotRxnUnified,
    callForECAnnotRxnUnified_Simple
)


def test_annotation_function():
    import libsbml
    import sqlite3

    # Load model and reaction
    doc = libsbml.readSBML('../../models/BiGG_Models/iAF1260b.xml')
    model = doc.getModel()
    rxn = model.getReaction("R_3HAD100")

    # Setup cursor - using your format
    database_name = '../../src/sboannotator/create_dbs'
    con = sqlite3.connect(database_name)
    cur = con.cursor()

    with open(database_name + '.sql') as schema:
        cur.executescript(schema.read())

    # Test
    print(f"\nTesting R_3HAD100:")
    print(f"Initial SBO: {rxn.getSBOTermID()}")

    result = callForECAnnotRxnUnified(rxn, cur)

    print(f"Final SBO: {result['final_sbo']}")
    print(f"Success: {result['success']}")
    print(f"All ECs: {result['all_unique_ecs']}")
    print(f"Databases: {result['queried_databases']}")
    print(f"Stopped at: {result['stopped_at_database']}")
    print(f"Database results: {result['database_results']}")

    con.close()

def test_callForECAnnotRxnUnified_Simple():
    import libsbml
    import sqlite3

    # Load model and reaction
    doc = libsbml.readSBML('../../models/BiGG_Models/iAF1260b.xml')
    model = doc.getModel()
    rxn = model.getReaction("R_3HAD100")

    # Setup cursor - using your format
    database_name = '../../src/sboannotator/create_dbs'
    con = sqlite3.connect(database_name)
    cur = con.cursor()

    with open(database_name + '.sql') as schema:
        cur.executescript(schema.read())

    # Test
    print(f"\nTesting R_3HAD100:")
    print(f"Initial SBO: {rxn.getSBOTermID()}")

    result = callForECAnnotRxnUnified_Simple(rxn)

    print(f"reaction_id: {result['reaction_id']}")
    print(f"All ECs: {result['unique_ec_numbers']}")
    print(f"Database results: {result['database_results']}")
    print(f"final_sbo: {result['final_sbo']}")


    con.close()

def test_annotation_function_R_HKt():
    import libsbml
    import sqlite3

    # Load model and reaction
    doc = libsbml.readSBML('../../models/BiGG_Models/RECON1.xml')
    model = doc.getModel()
    rxn = model.getReaction("R_HKt")

    rxn.setSBOTerm("SBO:0000176")

    # Setup cursor - using your format
    database_name = '../../src/sboannotator/create_dbs'
    con = sqlite3.connect(database_name)
    cur = con.cursor()

    with open(database_name + '.sql') as schema:
        cur.executescript(schema.read())

    # Test
    print(f"\nTesting R_3HAD100:")
    print(f"Initial SBO: {rxn.getSBOTermID()}")

    result = callForECAnnotRxnUnified(rxn, cur)

    print(f"Final SBO: {result['final_sbo']}")
    print(f"Success: {result['success']}")
    print(f"All ECs: {result['all_unique_ecs']}")
    print(f"Databases: {result['queried_databases']}")
    print(f"Stopped at: {result['stopped_at_database']}")
    print(f"Database results: {result['database_results']}")

    con.close()



# class MockReaction:
#     """模拟反应对象"""
#
#     def __init__(self, reaction_id, name, annotation_string):
#         self.reaction_id = reaction_id
#         self.name = name
#         self.annotation_string = annotation_string
#         self.sbo_term = None
#
#     def getId(self):
#         return self.reaction_id
#
#     def getName(self):
#         return self.name
#
#     def getAnnotationString(self):
#         return self.annotation_string
#
#     def setSBOTerm(self, sbo_term):
#         self.sbo_term = sbo_term
#         print(f"✅ 反应 {self.reaction_id} 设置 SBO Term: {sbo_term}")
#
#
# def create_CH25H_reaction():
#     """创建您提供的 CH25H 反应对象"""
#     annotation_string = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
#       <rdf:Description rdf:about="#R_CH25H">
#         <bqbiol:is xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
#           <rdf:Bag>
#             <rdf:li rdf:resource="http://identifiers.org/bigg.reaction/CH25H"/>
#             <rdf:li rdf:resource="http://identifiers.org/metanetx.reaction/MNXR96660"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-CFA-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-GGA-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-BTA-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-TGU-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-CEL-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-SCE-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-SSC-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-DRE-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-RNO-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-XTR-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-MMU-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/reactome.reaction/R-HSA-191983"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/46135"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/46134"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/46133"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/46132"/>
#           </rdf:Bag>
#         </bqbiol:is>
#       </rdf:Description>
#     </rdf:RDF>"""
#
#     return MockReaction("R_CH25H", "Cholesterol 25-hydroxylase", annotation_string)
#
#
# def create_ACACT8p_reaction():
#     """创建 ACACT8p 反应对象"""
#     annotation_string = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
#       <rdf:Description rdf:about="#R_ACACT8p">
#         <bqbiol:is xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
#           <rdf:Bag>
#             <rdf:li rdf:resource="http://identifiers.org/bigg.reaction/ACACT8p"/>
#             <rdf:li rdf:resource="http://identifiers.org/metanetx.reaction/MNXR95204"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35282"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35280"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35279"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35281"/>
#             <rdf:li rdf:resource="http://identifiers.org/seed.reaction/rxn08767"/>
#           </rdf:Bag>
#         </bqbiol:is>
#       </rdf:Description>
#     </rdf:RDF>"""
#
#     return MockReaction("R_ACACT8p", "Acetyl CoA acyltransferase hexadecanoyl CoA peroxisomal", annotation_string)
#
#
# class TestCH25HReaction(unittest.TestCase):
#
#     def setUp(self):
#         """初始化测试"""
#         self.test_reaction = create_CH25H_reaction()
#
#     def test_CH25H_callForECAnnotRxnUnified(self):
#         """测试您提供的 CH25H 反应"""
#         print("\n" + "=" * 80)
#         print("测试 CH25H 反应 - Cholesterol 25-hydroxylase")
#         print("=" * 80)
#
#         print(f"反应ID: {self.test_reaction.getId()}")
#         print(f"反应名称: {self.test_reaction.getName()}")
#         print(f"初始 SBO Term: {self.test_reaction.sbo_term}")
#
#         # 调用您的函数
#         print(f"\n🚀 开始调用 callForECAnnotRxnUnified...")
#         callForECAnnotRxnUnified(self.test_reaction)
#
#         print(f"🎯 最终 SBO Term: {self.test_reaction.sbo_term}")
#
#         # 验证结果
#         self.assertEqual(self.test_reaction.sbo_term, 'SBO:0000200',
#                          "CH25H 反应应该设置为酶催化反应 (SBO:0000200)")
#
#         print("✅ 测试通过！CH25H 反应正确设置为 SBO:0000200")
#
#     def test_CH25H_detailed_analysis(self):
#         """详细分析 CH25H 反应各个适配器的结果"""
#         print("\n" + "=" * 80)
#         print("CH25H 反应详细分析 - 各适配器结果")
#         print("=" * 80)
#
#         provider = UnifiedEnzymeDataProvider()
#         results = provider.get_ec_numbers_from_reaction(self.test_reaction)
#
#         print(f"\n📊 各适配器查询结果:")
#         print(f"BiGG 结果: {results.get('bigg', [])}")
#         print(f"KEGG 结果: {results.get('kegg', [])}")
#         print(f"Reactome 结果: {results.get('reactome', [])}")
#         print(f"所有唯一EC号: {results.get('all_unique', [])}")
#
#         # 验证结果结构
#         self.assertIn('bigg', results, "结果应包含BiGG字段")
#         self.assertIn('kegg', results, "结果应包含KEGG字段")
#         self.assertIn('reactome', results, "结果应包含Reactome字段")
#         self.assertIn('all_unique', results, "结果应包含all_unique字段")
#
#         # 分析结果
#         all_unique = results.get('all_unique', [])
#         print(f"\n💡 结果分析:")
#         if not all_unique:
#             print("   - 所有适配器都没有返回EC号")
#         else:
#             print(f"   - 找到 {len(all_unique)} 个唯一EC号")
#             for ec in all_unique:
#                 if '.-.' in str(ec):
#                     print(f"   - {ec} (不完整格式)")
#                 else:
#                     print(f"   - {ec} (完整格式)")
#
#         print(f"\n🎯 预期最终结果: SBO:0000200")
#
#
# def create_ACACT8p_reaction():
#     """创建 ACACT8p 反应对象"""
#     annotation_string = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
#       <rdf:Description rdf:about="#R_ACACT8p">
#         <bqbiol:is xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
#           <rdf:Bag>
#             <rdf:li rdf:resource="http://identifiers.org/bigg.reaction/ACACT8p"/>
#             <rdf:li rdf:resource="http://identifiers.org/metanetx.reaction/MNXR95204"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35282"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35280"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35279"/>
#             <rdf:li rdf:resource="http://identifiers.org/rhea/35281"/>
#             <rdf:li rdf:resource="http://identifiers.org/seed.reaction/rxn08767"/>
#           </rdf:Bag>
#         </bqbiol:is>
#       </rdf:Description>
#     </rdf:RDF>"""
#
#     return MockReaction("R_ACACT8p", "Acetyl CoA acyltransferase hexadecanoyl CoA peroxisomal", annotation_string)
#
#
# class TestSEEDAdapter(unittest.TestCase):
#
#     def test_query_ec_numbers_rxn08767(self):
#         """Test that rxn08767 returns EC 2.3.1.16"""
#         adapter = SEEDAdapter()
#         results = adapter.query_ec_numbers("rxn08767")
#
#         print(f"Results for rxn08767: {results}")
#
#         # Should return ['2.3.1.16'] for this thiolase reaction
#         self.assertEqual(results, ['2.3.1.16'])
#
#     def test_ACACT8p_detailed_analysis(self):
#         """详细分析 ACACT8p 反应各个适配器的结果"""
#         print("\n" + "=" * 80)
#         print("ACACT8p 反应详细分析 - 各适配器结果")
#         print("=" * 80)
#
#         reaction = create_ACACT8p_reaction()
#         provider = UnifiedEnzymeDataProvider()
#         results = provider.get_ec_numbers_from_reaction(reaction)
#
#         print(f"\n📊 各适配器查询结果:")
#         print(f"BiGG 结果: {results.get('bigg', [])}")
#         print(f"KEGG 结果: {results.get('kegg', [])}")
#         print(f"Reactome 结果: {results.get('reactome', [])}")
#         print(f"SEED 结果: {results.get('seed', [])}")
#         print(f"所有唯一EC号: {results.get('all_unique', [])}")
#
#         # 验证结果结构
#         self.assertIn('bigg', results, "结果应包含BiGG字段")
#         self.assertIn('kegg', results, "结果应包含KEGG字段")
#         self.assertIn('reactome', results, "结果应包含Reactome字段")
#         self.assertIn('all_unique', results, "结果应包含all_unique字段")
#
#         # 分析结果
#         all_unique = results.get('all_unique', [])
#         print(f"\n💡 结果分析:")
#         if not all_unique:
#             print("   - 所有适配器都没有返回EC号")
#         else:
#             print(f"   - 找到 {len(all_unique)} 个唯一EC号")
#             for ec in all_unique:
#                 if '.-.' in str(ec):
#                     print(f"   - {ec} (不完整格式)")
#                 else:
#                     print(f"   - {ec} (完整格式)")
#
#         print(f"\n🎯 预期EC号: 2.3.1.16 (thiolase)")
#         print(f"🎯 预期最终SBO结果: SBO:0000402")
#
#         # 检查是否包含期望的EC号
#         ECNums = results['all_unique']
#         self.assertIn('2.3.1.16', ECNums, f"应该包含EC 2.3.1.16，实际得到: {ECNums}")
#
#     def test_ACACT8p_full_annotation(self):
#         """测试 ACACT8p 反应的完整注释过程"""
#         from sboannotator.adapter import callForECAnnotRxnUnified
#
#         reaction = create_ACACT8p_reaction()
#         print(f"\n反应ID: {reaction.getId()}")
#         print(f"反应名称: {reaction.getName()}")
#         print(f"初始 SBO Term: {reaction.sbo_term}")
#
#         # 调用完整的注释函数
#         callForECAnnotRxnUnified(reaction)
#
#         print(f"最终 SBO Term: {reaction.sbo_term}")
#
#         # 验证最终的SBO term
#         self.assertEqual(reaction.sbo_term, 'SBO:0000402',
#                          f"ACACT8p 反应应该设置为 SBO:0000402，实际得到: {reaction.sbo_term}")
#
def test_seed_adapter():
    # 创建适配器实例
    adapter = SEEDAdapter()

    # 测试 rxn08762
    print("Testing rxn08762...")
    ec_numbers = adapter.query_ec_numbers("rxn08762")
    print(f"EC numbers for rxn08762: {ec_numbers}")
    print(f"Number of EC numbers found: {len(ec_numbers)}")
    print()

    # 可以测试更多反应ID
    test_reactions = ["rxn08762", "rxn00001", "rxn00062", "rxn00257"]

    print("Testing multiple reactions:")
    for rxn_id in test_reactions:
        ec_nums = adapter.query_ec_numbers(rxn_id)
        print(f"{rxn_id:10} -> {ec_nums}")




if __name__ == '__main__':
    # 运行测试时显示详细输出
    unittest.main(verbosity=2)
import unittest
from knowledge_structure_metrics import AccessedNode,tree_locality,level_recall
class TestKnowledgeStructureMetrics(unittest.TestCase):
 def test_tree_locality_measures_cross_subtree_without_rewriting_tree(self):
  xs=[AccessedNode('a',('network','routing','ospf')),AccessedNode('b',('network','routing','bgp')),AccessedNode('c',('software','tests','unit'))]
  m=tree_locality(xs,subtree_depth=1); self.assertEqual(m['transitions'],2); self.assertEqual(m['cross_subtree'],1); self.assertEqual(m['cross_subtree_rate'],.5)
 def test_level_recall_compares_direct_and_descent(self):
  m=level_recall(gold_leaf_ids={'a','b','c'},direct_retrieved={'a','b','c'},descent_retrieved={'a','b'})
  self.assertEqual(m['direct_recall'],1.0); self.assertAlmostEqual(m['descent_recall'],2/3); self.assertGreater(m['delta_direct_minus_descent'],0)
 def test_empty_gold_is_not_reported_as_failure(self):
  self.assertEqual(level_recall(gold_leaf_ids=set(),direct_retrieved=set(),descent_retrieved=set())['direct_recall'],1.0)
if __name__=='__main__': unittest.main()

import unittest
from context_preorchestrator import ContextCandidate,ContextPreOrchestrator,ExecutorProfile
CATALOG=[
 ContextCandidate('dev','skill',('software_engineering','algorithm_design'),1800,.9),
 ContextCandidate('algo-perf','skill',('algorithm_design','performance'),1500,.8),
 ContextCandidate('docs-science','skill',('documentation','algorithm_design'),1200,.6),
 ContextCandidate('game-perf','skill',('performance','game_development'),1700,.7),
 ContextCandidate('agent-control','project_skill',('agent_orchestration','context_management'),1900,1.0),
 ContextCandidate('sglang-runtime','tool',('runtime_inference','performance'),900,.8)]
class TestContextPreOrchestrator(unittest.TestCase):
 def setUp(self): self.router=ContextPreOrchestrator(CATALOG)
 def test_4b_16k(self):
  p=ExecutorProfile('local-4b','local',16384,16384,reserve_tokens=3072,capability_source='runtime')
  e=self.router.build('Implementar algoritmo de otimização e analisar desempenho',p)
  self.assertEqual(e.strategy,'microcontext_serial'); ids={x.id for x in e.selected}
  self.assertIn('dev',ids); self.assertIn('algo-perf',ids); self.assertNotIn('game-perf',ids)
  self.assertLessEqual(sum(x.estimated_tokens for x in e.selected),int(e.token_budget*.34))
 def test_large(self):
  p=ExecutorProfile('remote-large','virtual_remote',272000,220000,reserve_tokens=16000,capability_source='public_declared')
  e=self.router.build('Planejar agentes, contexto, ontologia e runtime SGLang',p)
  self.assertEqual(e.strategy,'sequential_hats_wide_memory'); self.assertEqual(e.expansion_policy['global_catalog'],'allowed')
 def test_pressure(self):
  self.assertLess(ExecutorProfile('x',active_sessions=6).usable_tokens(),ExecutorProfile('x').usable_tokens())
 def test_depth_is_derived_from_executor_budget(self):
  costs=(2000,4000,8000,12000,18000)
  r=ContextPreOrchestrator(CATALOG,hierarchy_level_costs=costs)
  small=r.build('contexto e ontologia',ExecutorProfile('small','local',16384,16384,reserve_tokens=3072))
  large=r.build('contexto e ontologia',ExecutorProfile('large','remote',131072,100000,reserve_tokens=8000))
  self.assertLess(small.expansion_policy['derived_max_depth'],large.expansion_policy['derived_max_depth'])
  self.assertEqual(small.expansion_policy['depth_source'],'executor_budget+declared_level_costs')
 def test_depth_is_undeclared_without_level_costs(self):
  e=self.router.build('contexto',ExecutorProfile('x'))
  self.assertIsNone(e.expansion_policy['derived_max_depth']); self.assertEqual(e.expansion_policy['depth_source'],'undeclared')
 def test_escape(self):
  e=self.router.build('tarefa desconhecida',ExecutorProfile('x'))
  self.assertEqual(e.expansion_policy['levels'][-1],'global_catalog'); self.assertIn('insufficient_evidence',e.expansion_policy['trigger'])
if __name__=='__main__': unittest.main()

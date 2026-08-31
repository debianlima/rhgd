import unittest
from pgh_context_preorchestrator import ContextCandidate,ContextPreOrchestrator,ExecutorProfile
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
 def test_escape(self):
  e=self.router.build('tarefa desconhecida',ExecutorProfile('x'))
  self.assertEqual(e.expansion_policy['levels'][-1],'global_catalog'); self.assertIn('insufficient_evidence',e.expansion_policy['trigger'])
if __name__=='__main__': unittest.main()

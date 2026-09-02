# Políticas consolidadas para RHGD Fase 0

## PGA — autogovernança
1. Política e autoridade chegam por snapshot imutável, versionado e com hash.
2. Agente não autoexpande autoridade nem altera política silenciosamente.
3. Evolução segue: evidência -> EvolutionProposal -> ImpactStudy -> plano aprovado -> candidato -> gates congelados -> validação -> homologação.
4. Feedback humano entra como `HumanPreferenceEvidence`; não altera skill/política diretamente.
5. Prioridade estratégica não é scheduler runtime.

Gates herdados: `POLICY_SNAPSHOT_IMMUTABLE`, `AUTHORITY_PROVENANCE_COMPLETE`, `NO_SILENT_POLICY_MUTATION`, `NO_SELF_AUTHORITY_EXPANSION`, `EVOLUTION_PLAN_APPROVED_BEFORE_RESULTS`, `GATES_FROZEN_BEFORE_VALIDATION`, `ROLLBACK_OR_DEPRECATION_DEFINED`.

## PGH — conhecimento/contexto/autorização
1. `KnowledgeScope` governa proprietário, tenant, ambiente, classificação, visibilidade e compartilhamento.
2. `GovernanceContextBinding` referencia snapshot PGA; PGH não reimplementa política.
3. `AuthorizationGrant` é semântico e não equivale a lease runtime.
4. Resultado PGD/RHGD retorna como evidência `observed`; homologação exige gates PGH.
5. Contexto padrão é mínimo suficiente; expansão é progressiva e justificável.
6. `ContextSelectionSnapshot` registra o que foi realmente carregado.

## PGD — execução distribuída
1. PGH autoriza; PGD executa.
2. Estado vivo de execução, `ExecutionQueue`, DAG, workers, heartbeat, ResourceLease, retry, checkpoint, relocation e recovery pertencem a PGD. A `EnvelopeTransportQueue` RHGD não é fila de execução.
3. Permissão operacional nunca excede autorização PGH/PGA.
4. Efeito verificado não é sinônimo de process exit.
5. Outcome retorna observado, com sessão e proveniência.

Gates herdados: `PGH_AUTHORIZATION_REQUIRED`, `RESOURCE_STATE_OWNED_BY_PGD`, `OPERATIONAL_PERMISSION_WITHIN_AUTHORIZATION`, `OUTCOME_EVIDENCE_OBSERVED_ONLY`, `SESSION_PROVENANCE_COMPLETE`, `NO_SECRET_IN_SESSION_STREAM`, `EFFECT_VERIFICATION_NE_PROCESS_EXIT`.

## RHGD — políticas novas
1. `SEMANTIC_WORK_BEFORE_NUMERIC_DISTRIBUTION`: padrão é WorkUnit autocontida, não tensor-parallel remoto.
2. `NO_DUPLICATE_PGD_RUNTIME`: RHGD não cria scheduler/`ExecutionQueue`/lease concorrente; sua `EnvelopeTransportQueue` é exclusivamente de transporte de ContextEnvelope.
3. `SOVEREIGN_LOCAL_FINALIZATION`: nó originador mantém autoridade sobre reconciliação/finalização salvo delegação explícita.
4. `DELEGATION_NE_AUTHORITY_EXPANSION`: recursão reduz ou preserva escopo; nunca amplia.
5. `PRIVACY_CLASS_ENFORCED`: P0..P4 limita onde WorkUnit pode executar.
6. `KNOWLEDGE_VISIBILITY_ENFORCED`: PRIVATE/TENANT/FEDERATED/PUBLIC é preservado em anúncio, cache e execução.
7. `REMOTE_EXECUTION_MINIMIZATION`: enviar apenas contexto semanticamente necessário.
8. `DISSENT_AND_PROVENANCE_PRESERVED`: redução não pode apagar dissenso/evidência relevante.
9. `CAPABILITY_EVIDENCE_REQUIRED`: anúncio de capacidade tem fonte, validade e confiança.
10. `BLOCKCHAIN_OFF_CRITICAL_PATH`: prompts, respostas, `ExecutionQueue`, `EnvelopeTransportQueue` e telemetria não dependem de consenso on-chain na Fase 0.
11. `SETTLEMENT_ADAPTER_ONLY`: Bitcoin/Lightning/RGB/EVM são adapters futuros, não autoridade cognitiva.
12. `NO_SECRET_IN_ADVERTISEMENT`: anúncios nunca carregam credenciais ou conhecimento privado bruto.
13. `ASYMMETRIC_CONTEXT_ENVELOPE_TRANSPORT`: RHGD mantém ingress/egress independentes, ordem monotônica por peer e remoção condicionada a ACK/consumo; cada frame exige `authorization_ref` e `pgd_assignment_ref` e não concede lease.

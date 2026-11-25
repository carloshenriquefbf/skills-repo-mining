# Resultados preliminares da API do GitHub

Coleta: 2026-11-25. Consultas: `filename:SKILL.md pytest`

Particoes da busca: 10 (truncadas no teto de 1000: 0).

## Funil de selecao (Anexo C)

| Etapa | N |
|---|---:|
| Arquivos SKILL.md unicos (repo, caminho) retornados pela busca | 974 |
| Repositorios distintos | 578 |
| Repositorios com metadados obtidos | 596 |
| ... nao fork / nao mirror | 596 |
| ... linguagem principal Python | 364 |
| ... com >=1 SKILL.md com indicio de teste (triagem, pre-codebook) | 207 |
| ... t0 identificado | 207 |
| ... t0 diferente do commit inicial | 167 |
| ... janela pos completa ate a coleta (C=0d) | 137 |
| ... >= 20 commits em cada janela e nao arquivado | 75 |
| ... sem sinal de colecao/catalogo de skills (verificar manualmente) | 64 |

## M1 preliminar

Repositorios Python com SKILL.md com indicio de teste: **207** (triagem por palavra-chave; o M1 final depende do codebook).

Pre-elegiveis para G2: **64** (regra de contingencia: N >= 30 para analise confirmatoria).

## M3 preliminar: t0 por mes

| Mes | Repositorios |
|---|---:|
| 2025-10 | 3 |
| 2025-11 | 6 |
| 2025-12 | 4 |
| 2026-01 | 15 |
| 2026-02 | 22 |
| 2026-03 | 19 |
| 2026-04 | 30 |
| 2026-05 | 22 |
| 2026-06 | 18 |
| 2026-07 | 19 |
| 2026-08 | 16 |
| 2026-09 | 15 |
| 2026-10 | 13 |
| 2026-11 | 5 |

## Onde as skills ficam (pasta raiz)

| Pasta | SKILL.md |
|---|---:|
| `skills` | 218 |
| `data` | 99 |
| `(raiz)` | 96 |
| `.claude/skills` | 51 |
| `.agents/skills` | 27 |
| `testing` | 14 |
| `skills_omni` | 12 |
| `other` | 11 |
| `skills/data` | 5 |
| `bash` | 5 |
| `development` | 5 |
| `.skills` | 4 |
| `.codex/skills` | 4 |
| `.agent/skills` | 3 |
| `bundled-skills` | 3 |

## Termos de teste na descricao (triagem)

| Termo | Skills |
|---|---:|
| test | 149 |
| tests | 148 |
| pytest | 129 |
| testing | 116 |
| coverage | 46 |
| fixtures | 39 |
| tdd | 38 |
| e2e | 18 |
| end-to-end | 14 |
| fixture | 14 |
| playwright | 13 |
| qa | 10 |
| unittest | 4 |
| end to end | 4 |
| selenium | 3 |
| mutation | 2 |
| hypothesis | 2 |

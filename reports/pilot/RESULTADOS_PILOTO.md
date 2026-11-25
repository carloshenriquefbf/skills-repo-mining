# Resultados do piloto de descoberta via API do GitHub

Protocolo v0.4, semana 1 (secao 7.1). Este arquivo e escrito a mao e interpreta
os dados do piloto. O `summary.md` e o `funnel.csv` desta pasta sao gerados pelo
`python -m gm report --pilot` e sao sobrescritos a cada execucao.

## 1. Execucao

| Item | Valor |
|---|---|
| Data da coleta | 25/11/2026, busca entre 14:11 e 14:12 UTC |
| Comando | `python -m gm all --pilot` |
| Consulta | `filename:SKILL.md pytest` (146.176 resultados no `count`) |
| Amostragem | 1 pagina (100 resultados) em cada uma de 10 faixas de tamanho de arquivo |
| Janelas | 90 dias pre e pos; carencia C = 0 (provisoria) |
| Minimo de commits por janela | 20 |
| Duracao total | ~25 min, quase todo na etapa `adoption` |
| Dados | `data/pilot/` |

### Decisoes registradas antes do piloto (via `count`, 25/11/2026)

| Consulta | Resultados | Decisao |
|---|---:|---|
| `filename:SKILL.md pytest` | 146.176 | mantida (ancora Python) |
| `filename:SKILL.md test` | 4.071.424 | descartada: ~70 h de coleta e faixas saturadas |
| `filename:SKILL.md unittest` | 35.072 | candidata |
| `filename:SKILL.md tdd` | 165.632 | candidata |
| `filename:SKILL.md "test-driven"` | 67.968 | candidata |
| `filename:SKILL.md coverage` | 865.280 | candidata; custo alto (~16,6 h) e termo ambiguo |

## 2. Distribuicao da busca por faixa de tamanho

| Faixa | Tamanho (bytes) | Resultados na faixa | Coletados |
|---:|---|---:|---:|
| 1 | 0..2000 | 9.856 | 100 |
| 2 | 2001..4000 | 20.128 | 100 |
| 3 | 4001..6000 | 22.784 | 100 |
| 4 | 6001..8000 | 19.552 | 100 |
| 5 | 8001..10000 | 17.664 | 100 |
| 6 | 10001..12000 | 13.248 | 100 |
| 7 | 12001..14000 | 11.104 | 100 |
| 8 | 14001..16000 | 7.240 | 100 |
| 9 | 16001..18000 | 5.520 | 100 |
| 10 | 18001..400000 | 24.544 | 100 |
| | **Total** | **151.640** | **1.000** |

A soma das faixas (151.640) fica proxima do total da consulta sem particao
(146.176). Isso indica que as faixas cobrem a consulta inteira; o `total_count`
da API e aproximado. Nenhuma resposta veio com `incomplete_results`.

## 3. Funil de selecao (Anexo C, preliminar)

| Etapa | N |
|---|---:|
| Resultados coletados | 1.000 |
| ... com nome exato `SKILL.md` | 974 |
| Repositorios distintos em todos os resultados | 596 |
| ... com metadados obtidos | 596 |
| ... nao fork / nao mirror | 596 |
| ... linguagem principal Python | 364 |
| ... com >= 1 `SKILL.md` com indicio de teste (triagem) | 207 |
| ... t0 identificado | 207 |
| ... t0 diferente do commit inicial | 167 |
| ... janela pos encerrada ate a coleta | 137 |
| ... >= 20 commits em cada janela e nao arquivado | 75 |
| ... sem sinal de catalogo de skills | **64** |

Notas:
- 26 resultados tinham nome parecido, mas nao exato (`skill.md` 18, `WIKISKILL.md`,
  `pytest-skill.md`...), e foram descartados nas etapas seguintes.
- O `funnel.csv` gerado mostra "Repositorios distintos: 578" antes de "com
  metadados: 596". O 578 conta so repositorios com nome exato `SKILL.md`; o 596
  conta todos. Esta tabela usa a mesma base nas duas linhas. **O `report.py`
  precisa ser corrigido.**
- Nenhum fork apareceu: a busca de codigo ja exclui forks por padrao.
- Linguagem principal dos 596 repositorios: Python 364, Shell 54, TypeScript 47,
  JavaScript 40, sem linguagem 27, Rust 21, outras 43.
- Dos 137 com janela pos encerrada, 46 tinham < 20 commits na janela pre e 40
  tinham < 20 na pos (um mesmo repositorio pode falhar nos dois). Nenhum estava
  arquivado.

## 4. Metricas preliminares

**M1 (triagem, antes do codebook):** 207 repositorios Python com ao menos um
`SKILL.md` com indicio de teste (310 de 629 `SKILL.md` baixados). 603 dos 629
tem cabecalho com `name`/`description`.

**M3: t0 por mes (207 repositorios)**

| Mes | N | Mes | N |
|---|---:|---|---:|
| 2025-10 | 3 | 2026-05 | 22 |
| 2025-11 | 6 | 2026-06 | 18 |
| 2025-12 | 4 | 2026-07 | 19 |
| 2026-01 | 15 | 2026-08 | 16 |
| 2026-02 | 22 | 2026-09 | 15 |
| 2026-03 | 19 | 2026-10 | 13 |
| 2026-04 | 30 | 2026-11 | 5 |

As adocoes comecam em outubro de 2025, junto com o lancamento do formato Agent
Skills, e tem pico em abril de 2026. Com janela de 90 dias, so entram adotantes
com t0 ate 26/08/2026 (o t0 mais recente com janela pos encerrada).

**Atividade nas janelas (207 repositorios):** mediana de 24 commits na pre e
42 na pos. Essas contagens incluem merges e bots.

## 5. Interpretacao

### 5.1 Viabilidade

Com 0,7% dos resultados da consulta `pytest`, o piloto ja encontrou 64
repositorios pre-elegiveis, acima do N minimo de 30 da regra de contingencia
(secao 5.7). A coleta completa deve aumentar esse numero, ainda que com
sobreposicao de repositorios entre faixas. **Pelo criterio de N, o estudo e
viavel.** Os outros dois criterios de prosseguimento da secao 8 ainda nao foram
avaliados: kappa >= 0,70 e extracao de M4-M6 sem intervencao em 9 de 10
repositorios.

### 5.2 O N de 64 e um limite superior

Dois pontos reduzem o N efetivo e pedem decisao do grupo:

**a) Onde a skill esta.** Pasta do `SKILL.md` que define o t0 nos 64 repositorios:

| Pasta | N | Leitura |
|---|---:|---|
| Pasta de harness (`.claude/skills`, `.agents/skills`, `.codex/skills`...) | 24 | uso no proprio projeto, quase certamente |
| Outra pasta (`skills/`, `core/skills/`...) | 37 | ambiguo: skill distribuida aos usuarios da biblioteca ou skill de desenvolvimento |
| Raiz do repositorio | 3 | o repositorio e a propria skill |

Exemplos ambiguos: `ArchiveBox/abxpkg` (`skills/abxpkg/SKILL.md`, provavelmente
ensina a usar a biblioteca) e `NVIDIA-NeMo/Megatron-Bridge`
(`skills/testing/SKILL.md`, provavelmente desenvolvimento do proprio projeto).

**b) Historico curto antes da adocao.** A mediana de historico antes do t0 e de
so 27 dias. 132 dos 207 repositorios adotaram a skill com menos de 90 dias de
vida, e muitos parecem ter nascido ja com agentes. Entre os 64 pre-elegiveis,
**28 tem janela pre truncada** (< 90 dias de historico) e 36 tem a janela
completa. O protocolo preve a "duracao efetiva da janela" como covariavel
(secao 5.2), mas nao diz se a janela pre truncada e aceitavel.

**Combinando os dois criterios mais estritos** (pasta de harness e janela pre
completa): **18 repositorios**. Isso fica abaixo de 30 no piloto, mas a coleta
completa deve multiplicar o numero.

### 5.3 Catalogos de skills

Catalogos dominam algumas pastas. As 99 skills em `data/` vem de 2
repositorios (`majiayu000/claude-skill-registry-data` sozinho tem 87), e
`diegosouzapw/awesome-omni-skills` tem 21 em `skills/`. O filtro automatico
(>= 10 `SKILL.md` na amostra ou "skill" no nome) pega os maiores, mas deixa
passar catalogos com poucas skills na amostra. Os 64 precisam de verificacao
manual.

## 6. Limitacoes do piloto

- A amostra nao e aleatoria (ordenacao "best match" dentro de cada faixa).
  Extrapolar para a consulta inteira vale so como ordem de grandeza, e o `report`
  ainda nao pondera pelas faixas.
- `test_hint` e triagem por palavra-chave, nao o codebook.
- t0 via `commits?path=` nao segue renomeacoes: se a skill foi movida, t0 e a
  data de chegada ao caminho atual.
- As contagens por janela incluem merges e bots.
- O filtro de catalogo e heuristico.

## 7. Decisoes pendentes para o grupo

1. Exigir que a skill esteja em pasta de harness (leitura estrita de "caminho
   compativel com o formato Agent Skills", secao 5.3.1)?
2. Aceitar janela pre truncada (< 90 dias de historico) ou exigir historico
   minimo antes do t0?
3. Quais consultas entram na coleta completa (`pytest` mais `unittest`, `tdd`,
   `"test-driven"`?) e o registro disso na secao 5.3.4 e na ameaca a validade
   da secao 5.8.
4. Valor da carencia C.

## 8. Proximos passos

1. Inspecao manual dos 64 pre-elegiveis: e catalogo? a skill serve ao proprio
   projeto? e de teste?
2. Calibracao do codebook: 20 `SKILL.md` codificados por 2 integrantes, kappa
   >= 0,70.
3. Regras do Anexo B e piloto de extracao de M4-M6 por clone em 10 repositorios.
4. Corrigir a base das duas primeiras linhas do funil no `report.py`.

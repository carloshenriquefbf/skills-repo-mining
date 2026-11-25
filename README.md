# CPS820 Grupo 4 - Skills agenticas de teste (MSR)

Pacote de coleta do protocolo v0.4. Parametros em `config.toml`.

## Requisitos
- [uv](https://docs.astral.sh/uv/) (usa Python >= 3.11; sem dependencias externas na coleta)
- `GITHUB_TOKEN`: token *fine-grained* somente leitura, acesso a repositorios publicos.

## Execucao
```sh
export GITHUB_TOKEN=github_pat_...
uv run python -m gm count       # tamanho de cada consulta (piloto da cobertura, 5.3.4)
uv run python -m gm discover    # busca de codigo, particionada por tamanho
uv run python -m gm metadata    # GraphQL: linguagem, fork, arquivado, idade...
uv run python -m gm skills      # baixa SKILL.md + triagem por palavra-chave
uv run python -m gm adoption    # t0 e commits nas janelas pre/pos
uv run python -m gm report      # reports/summary.md e reports/funnel.csv
```
A descoberta e retomavel: particoes concluidas ficam em `data/raw/search_log.jsonl`.

### Piloto
```sh
python -m gm all --pilot   # ~10 requisicoes de busca; tudo em data/pilot/ e reports/pilot/
```
Coleta 1 pagina (100 resultados) por faixa de tamanho de arquivo, por consulta
(`pilot_band_bytes` e `pilot_bands` em `config.toml`). As etapas tambem podem ser
rodadas uma a uma com `--pilot` (ex.: `python -m gm report --pilot`).
Atencao: a opcao precisa ser exatamente `--pilot`; com outra grafia o piloto e
ignorado e roda a coleta completa (~3 h).

- **Para que serve:** estimar a taxa de aproveitamento (quantos arquivos viram
  repositorios pre-elegiveis) e o N provavel antes da coleta completa. Esse e o
  criterio de prosseguimento da secao 8 do protocolo (N compativel com a regra de
  contingencia, N >= 30).
- **Por que faixas de tamanho:** a busca ordena os resultados por relevancia
  ("best match"). As primeiras paginas de uma unica consulta dariam uma amostra
  concentrada no topo do ranking. Uma pagina por faixa espalha a amostra.
- **Peso de cada faixa:** o `total_count` de cada faixa fica em
  `data/pilot/raw/search_log.jsonl` e cada arquivo coletado leva a coluna `band`.
  Com isso o aproveitamento do piloto pode ser ponderado para a consulta inteira.
  (O `report` ainda nao faz essa ponderacao.)
- **O que o piloto nao responde:** a amostra nao e aleatoria, entao a
  extrapolacao vale so como ordem de grandeza. A cobertura e o truncamento da
  busca completa so aparecem rodando a coleta completa.

## Saidas
| Arquivo | Conteudo |
|---|---|
| `data/raw/skill_files.jsonl` | resultado bruto da busca (1 linha por arquivo x consulta) |
| `data/repos.csv` | metadados por repositorio |
| `data/skills.csv` | 1 linha por SKILL.md candidato; base para a codificacao (Anexo A) |
| `data/adoption.csv` | t0, commit inicial, commits nas janelas, pre-elegibilidade |
| `reports/funnel.csv` | funil de selecao (Anexo C) |

## Como a pipeline funciona

Cada etapa le apenas as saidas da etapa anterior, entao qualquer uma pode ser
rodada de novo isoladamente. Todos os parametros vem de `config.toml`.

```
count      (opcional) so mede o tamanho de cada consulta; nao coleta nada
  |
1 discover   API de busca de codigo (/search/code)
  |            -> data/raw/skill_files.jsonl, data/raw/search_log.jsonl
2 metadata   API GraphQL, lotes de 40 repositorios
  |            -> data/repos.csv
3 skills     raw.githubusercontent.com (nao gasta cota da API)
  |            -> data/skills/ (copias dos SKILL.md), data/skills.csv
4 adoption   API REST de commits
  |            -> data/adoption.csv
5 report     sem rede
               -> reports/summary.md, reports/funnel.csv
```

1. **discover** busca arquivos `SKILL.md` com cada consulta de `queries`. A API
   devolve no maximo 1000 resultados por consulta, entao a coleta completa divide
   a consulta por tamanho de arquivo (`size:0..400000` vira `0..200000` e
   `200001..400000`, e assim por diante) ate cada parte ter ate 1000 resultados.
   No modo `--pilot`, pega so a 1a pagina (100 resultados) de 10 faixas fixas de
   tamanho. Cada parte concluida fica registrada em `search_log.jsonl`, o que
   permite retomar a coleta e medir a cobertura da busca.
2. **metadata** consulta os repositorios encontrados: linguagem principal,
   proporcao de bytes em Python, fork, mirror, arquivado, datas, estrelas, ramo
   padrao, numero de commits e topicos.
3. **skills** considera so os repositorios candidatos (linguagem principal
   Python, nao fork, nao mirror) e so arquivos com nome exato `SKILL.md`. Baixa
   cada arquivo, le `name` e `description` do cabecalho e marca `test_hint`
   quando a descricao bate com `test_regex`. Essa marcacao e triagem, nao o codebook.
4. **adoption** processa os repositorios com ao menos uma skill com `test_hint`
   (ou todas, com `--all`). Para cada uma, calcula:
   - **t0**: data do commit mais antigo, no ramo padrao, que toca o caminho do
     `SKILL.md`. Com varias skills de teste, vale a mais antiga.
   - o primeiro commit do repositorio;
   - commits na janela pre `[t0 - 90d, t0]` e na janela pos `[t0 + C, t0 + C + 90d]`;
   - `eligible_prescreen`: >= 20 commits em cada janela, janela pos ja encerrada,
     t0 diferente do commit inicial e repositorio nao arquivado.
5. **report** monta o funil de selecao, o M1 e o M3 preliminares e as tabelas
   de apoio. Marca como possivel catalogo de skills o repositorio com >= 10
   `SKILL.md` encontrados ou com "skill" no nome. Essa marcacao exige verificacao
   manual.

**Robustez.** O cliente espera sozinho quando a cota da API acaba e tenta de
novo apos erros de rede ou do servidor. `discover` pula as partes ja coletadas e
`skills` reaproveita os arquivos ja baixados. `metadata`, `adoption` e `report`
recalculam tudo e sobrescrevem a saida.

**Custo aproximado (piloto, 1000 arquivos):** discover 10 requisicoes de busca
(~1-2 min); metadata ~15 consultas GraphQL (~2 min); skills ~600 downloads
(~7 min); adoption ~5 requisicoes por repositorio (~15 min para ~200 repositorios).

## Arquivos do codigo (`gm/`)

| Arquivo | O que faz |
|---|---|
| `__main__.py` | Linha de comando (`python -m gm <etapa>`). Le a etapa e as opcoes `--pilot` e `--all`. `--pilot` precisa ser tratado antes de importar os outros modulos, porque muda as pastas de dados. |
| `common.py` | Codigo compartilhado: pastas de dados (`data/` ou `data/pilot/`), leitura do `config.toml`, leitura e escrita de CSV/JSONL, `skills_root` (pasta que contem as skills) e `parse_frontmatter` (le o cabecalho YAML do `SKILL.md` sem bibliotecas externas). |
| `gh.py` | Cliente da API do GitHub, so com a biblioteca padrao. Pega o token de `GITHUB_TOKEN`, `GH_TOKEN` ou `.env`; respeita os limites de taxa; tenta de novo em caso de falha. Funcoes: `get` (REST), `graphql`, `raw_file` (download sem cota), `count` (conta itens de uma lista pelo cabecalho de paginacao, com 1 requisicao) e `oldest` (item mais antigo de uma lista, usado para achar o primeiro commit). |
| `discover.py` | Etapa 1. `run` faz a coleta completa com divisao por tamanho; `pilot` faz a coleta por faixas; `count_only` implementa o comando `count`. |
| `metadata.py` | Etapa 2. Monta consultas GraphQL com varios repositorios por chamada e achata o resultado em `repos.csv`. |
| `skills.py` | Etapa 3. `candidate_repos` aplica os filtros de linguagem, fork e mirror (tambem usada pelo `adoption.py`); `run` baixa os `SKILL.md` e faz a triagem. |
| `adoption.py` | Etapa 4. Calcula t0, primeiro commit, commits por janela e pre-elegibilidade. |
| `report.py` | Etapa 5. Gera o funil e as tabelas do relatorio. |
| `__init__.py` | Vazio; marca `gm/` como pacote Python. |

## Limitacoes da triagem via API (resolvidas na extracao por clone)
- `test_hint` e triagem por palavra-chave, nao o codebook.
- t0 via `commits?path=` nao segue renomeacoes.
- Contagens por janela incluem merges e bots; M4-M6 serao extraidas do clone.
- Busca de codigo cobre apenas o ramo padrao e arquivos < 384 KB.

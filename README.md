# Analisador Sintático — Linguagem Arjanov (Compiladores, Parte 2)

Analisador sintático **SLR(1)** (bottom-up) para a linguagem Arjanov, construído
sobre o analisador léxico da Parte 1. A tabela de análise ACTION/GOTO é gerada
por código próprio (sem yacc/bison), a partir da gramática em `src/grammar.py`.

## Requisitos

- Python 3.10+ (desenvolvido/testado com 3.13). Sem dependências externas.

## Estrutura do projeto

```
analisador-sintatico/
├── README.md                    # este arquivo
├── run.py                       # atalho de execução (raiz)
├── src/                         # código-fonte
│   ├── token.py                 # TokenType, Token, KEYWORDS (léxico, Parte 1)
│   ├── lexer.py                 # analisador léxico (Parte 1, ajustado)
│   ├── grammar.py               # GLC simplificada (dados)
│   ├── slr.py                   # construção da tabela SLR(1)
│   ├── parser.py                # parser shift/reduce + modo pânico
│   └── main.py                  # pipeline CLI
├── exemplos/
│   ├── ExemploArjanov.arj       # entrada com TODAS as primitivas (entrega)
│   └── erros.arj                # entrada com erros (demonstra modo pânico)
└── docs/
    ├── DECISOES.md              # registro de todas as decisões de projeto
    ├── GLC.md                   # gramática final (exportar para PDF)
    ├── trabalho_parte2.pdf      # enunciado
    └── GLC_Arjanov_SLR.pdf      # GLC original (re-adicionar do Teams, se faltar)
```

## Como executar

A partir da **pasta raiz do projeto**. Duas formas equivalentes:

```bash
# via atalho na raiz
python3 run.py exemplos/ExemploArjanov.arj     # analisa (ACEITO)
python3 run.py exemplos/erros.arj              # demonstra o modo pânico (REJEITADO)
python3 run.py --demo                          # programa embutido

# ou executando o módulo diretamente
python3 src/main.py exemplos/ExemploArjanov.arj
```

> Nota técnica: `src/token.py` precisa ter prioridade sobre o módulo `token` da
> biblioteca padrão. Rodar `python3 src/main.py ...` já garante isso (o diretório
> do script entra no início do `sys.path`); o `run.py` faz o mesmo ajuste.

Flags:

| Flag | Efeito |
|------|--------|
| `--acoes` | imprime também o traço completo de ações shift/reduce |
| `--tokens` | imprime também a tabela de tokens do léxico |
| `--help` | ajuda |

Códigos de saída: `0` = ACEITO, `1` = erros léxicos/sintáticos, `2` = erro de
argumentos/E-S.

Verificar que a gramática é SLR(1) (0 conflitos) e ver estatísticas da tabela:

```bash
python3 src/slr.py
```

## Método e recuperação de erros

- **SLR(1) bottom-up.** A tabela é montada em `src/slr.py` a partir da coleção
  canônica de itens LR(0) e dos conjuntos FOLLOW (o "S" de SLR). A montagem
  detecta conflitos; a gramática atual gera **0 conflitos** (125 estados).
- **Modo pânico ("método do Dragão"):** ao encontrar um erro (ou um token
  `ERRO` do léxico), o parser desempilha estados até um estado com GOTO sobre um
  não-terminal de recuperação — prioridade global `comando` → `bloco` →
  `funcao` —, descarta tokens de entrada até um símbolo em FOLLOW desse
  não-terminal, e retoma. A preferência por `comando` faz o parser descartar o
  statement inteiro que contém o erro e resincronizar no próximo, evitando
  cascatas de erros.

Detalhes e justificativas de cada escolha: `docs/DECISOES.md`. Gramática final:
`docs/GLC.md`.

## Status (para continuidade)

Implementação **completa e funcional**:

- [x] Léxico copiado + ajuste do token `ERRO` em string não terminada.
- [x] GLC simplificada (`src/grammar.py`) — SLR(1), 0 conflitos, 125 estados.
- [x] Gerador de tabela SLR(1) (`src/slr.py`) com detecção de conflitos.
- [x] Parser shift/reduce + recuperação em modo pânico + árvore + traço.
- [x] `src/main.py` (pipeline, flags, códigos de saída) + `run.py`.
- [x] `exemplos/ExemploArjanov.arj` cobre todas as primitivas → **ACEITO**.
- [x] `exemplos/erros.arj` demonstra recuperação → 4 erros sintáticos + 1 léxico, sem cascata.
- [x] `docs/GLC.md` para exportar em PDF.

Pendências de **entrega** (não de código):

- [ ] Exportar `docs/GLC.md` → PDF e atualizar/substituir o `GLC_Arjanov_SLR.pdf`.
- [ ] Compactar e enviar via Teams (prazo 05/08/2026): GLC (PDF), código-fonte,
      e `.arj` de entrada com todas as primitivas.

# Analisador Sintático — Linguagem Arjanov (Compiladores, Parte 2)

Analisador sintático **SLR(1)** (bottom-up) para a linguagem Arjanov, construído
sobre o analisador léxico da Parte 1. A tabela de análise ACTION/GOTO é gerada
por código próprio (sem yacc/bison), a partir da gramática em `grammar.py`.

## Requisitos

- Python 3.10+ (desenvolvido/testado com 3.13). Sem dependências externas.

## Como executar

Execute a partir da pasta do projeto (o `token.py` local precisa ter prioridade
sobre o módulo `token` da biblioteca padrão):

```bash
python3 main.py ExemploArjanov.arj     # analisa o programa completo (ACEITO)
python3 main.py erros.arj              # demonstra o modo pânico (REJEITADO)
python3 main.py --demo                 # programa embutido
```

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
python3 slr.py
```

## Arquivos

| Arquivo | Papel |
|---------|-------|
| `token.py` | `TokenType`, `Token`, `KEYWORDS` (léxico, Parte 1). |
| `lexer.py` | Analisador léxico (Parte 1, com ajuste: string não terminada emite `ERRO`). |
| `grammar.py` | GLC simplificada (produções, terminais, NTs de recuperação, mapeamento `Token`→terminal). |
| `slr.py` | Construção SLR(1): itens LR(0), CLOSURE/GOTO, coleção canônica, FIRST/FOLLOW, ACTION/GOTO, conflitos. |
| `parser.py` | Autômato shift/reduce, recuperação em modo pânico, árvore + traço. |
| `main.py` | Pipeline CLI: arquivo → léxico → parser → relatório. |
| `GLC.md` | Gramática final (exportar para PDF na entrega). |
| `ExemploArjanov.arj` | Entrada com **todas as primitivas** da linguagem (entrega). |
| `erros.arj` | Entrada com erros sintáticos/léxicos (demonstra modo pânico). |
| `DECISOES.md` | Registro de todas as decisões de projeto (para continuidade). |

## Método e recuperação de erros

- **SLR(1) bottom-up.** A tabela é montada em `slr.py` a partir da coleção
  canônica de itens LR(0) e dos conjuntos FOLLOW (o "S" de SLR). A montagem
  detecta conflitos; a gramática atual gera **0 conflitos**.
- **Modo pânico ("método do Dragão"):** ao encontrar um erro (ou um token
  `ERRO` do léxico), o parser desempilha estados até um estado com GOTO sobre um
  não-terminal de recuperação — prioridade `comando` → `bloco` → `funcao` —,
  descarta tokens de entrada até um símbolo em FOLLOW desse não-terminal, e
  retoma. A preferência por `comando` faz o parser descartar o statement inteiro
  que contém o erro e resincronizar no próximo, evitando cascatas de erros.

## Status (para continuidade)

Implementação **completa e funcional**:

- [x] Léxico copiado + ajuste do token `ERRO` em string não terminada.
- [x] GLC simplificada (`grammar.py`) — SLR(1), 0 conflitos, 125 estados.
- [x] Gerador de tabela SLR(1) (`slr.py`) com detecção de conflitos.
- [x] Parser shift/reduce + recuperação em modo pânico + árvore + traço.
- [x] `main.py` (pipeline, flags, códigos de saída).
- [x] `ExemploArjanov.arj` cobre todas as primitivas → **ACEITO**.
- [x] `erros.arj` demonstra recuperação → 4 erros sintáticos + 1 léxico, sem cascata.
- [x] `GLC.md` para exportar em PDF.

Pendências de **entrega** (não de código):

- [ ] Exportar `GLC.md` → PDF e substituir/atualizar o `GLC_Arjanov_SLR.pdf`.
- [ ] Compactar e enviar via Teams (prazo 05/08/2026): GLC (PDF), código-fonte,
      e `.arj` de entrada com todas as primitivas.

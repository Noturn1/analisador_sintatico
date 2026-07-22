# Decisões de Projeto — Analisador Sintático (Parte 2)

> Documento de referência para continuidade. Registra **todas** as decisões
> tomadas com o autor antes da implementação, para que qualquer sessão futura
> (humana ou assistida) consiga continuar sem reabrir discussões.

## Contexto

- **Disciplina:** Compiladores. Trabalho — Parte 2: Análise Sintática.
- **Linguagem-alvo:** Arjanov (definida na Parte 1 — analisador léxico).
- **Entrega (Teams, prazo 05/08/2026):**
  1. Gramática livre de contexto (PDF);
  2. Código-fonte do compilador;
  3. Executável (se for o caso — não se aplica, é Python/CLI);
  4. Código-fonte de entrada `.arj` contendo **todas as primitivas** da linguagem.
- **Restrição:** proibido usar geradores automáticos (yacc/bison). Podemos
  ainda alterar/corrigir o léxico da Parte 1.
- O que o analisador deve fazer: receber a lista de tokens do léxico, fazer a
  análise sintática pelo método sorteado, e **tratar erros em modo pânico**
  (sem parar no primeiro erro).

## Decisões fechadas com o autor

| # | Tema | Decisão |
|---|------|---------|
| 1 | **Método** | Bottom-up **SLR(1)** (sorteio; coerente com a GLC recursiva à esquerda e o nome `GLC_Arjanov_SLR.pdf`). |
| 2 | **Tabela ACTION/GOTO** | **Gerada em código** a partir da GLC: coleção canônica LR(0), FIRST/FOLLOW, e montagem de ACTION/GOTO com **detecção de conflitos** (valida que a gramática é SLR(1)). Não é gerador tipo yacc — é o algoritmo implementado por nós. |
| 3 | **Operadores léxico × GLC** | **Simplificar a GLC** para usar os terminais *agrupados* do léxico (`OP_RELACIONAL`, `OP_ADITIVO`, `OP_MULTIPLICATIVO`, `OP_POTENCIA`, `OP_AND`, `OP_OR`, `OP_XOR`). Assim o alfabeto de terminais do parser = os próprios `TokenType`. |
| 4 | **Saída do parser** | Aceita/rejeita + **lista de erros sintáticos** (modo pânico) + **derivação**: traço de ações shift/reduce e **árvore sintática** indentada. |
| 5 | **Recuperação de erro** | **Modo pânico "método do Dragão"** para LR: desempilha estados até um com GOTO sobre um não-terminal de recuperação; descarta entrada até um token em FOLLOW dele; empilha o GOTO e retoma. NTs de recuperação por **prioridade global**: `comando` → `bloco` → `funcao` (statement-level primeiro). *Refinamento pós-implementação: `expressao` foi removido do conjunto e a busca passou a ser por prioridade global — sincronizar em nível de comando evita cascatas de erros espúrios.* |
| 6 | **Estrutura** | Python 3.13. **Copiar** `token.py`/`lexer.py` da Parte 1 para dentro de `analisador-sintatico/` (zip autocontido). Sem executável empacotado; roda com `python main.py arquivo.arj`. |
| 7 | **GLC entregue** | O PDF antigo fica desatualizado pela simplificação. A GLC final vai em `GLC.md` (numerada + mapeamento de terminais); autor reexporta para PDF. |
| 8 | **Arquivos de teste** | Estender `ExemploArjanov.arj` para cobrir 100% das primitivas (entrega) e criar `erros.arj` com erros sintáticos propositais para demonstrar o modo pânico. |
| 9 | **Ajuste no léxico** | `ERRO` do léxico **não** é símbolo da gramática: dispara direto a recuperação do parser. Ajuste: em "string não terminada" o léxico passa a **emitir também um token `ERRO`** (antes só registrava o erro), mantendo a sincronia posicional. |

## Arquitetura de arquivos

| Arquivo | Papel |
|---------|-------|
| `token.py` | Definições de `TokenType`, `Token`, `KEYWORDS` (copiado da Parte 1). |
| `lexer.py` | Analisador léxico (copiado; com o ajuste #9). |
| `grammar.py` | GLC simplificada como dado: produções numeradas, terminais, não-terminais, símbolo inicial, NTs de recuperação, mapeamento `Token`→terminal. |
| `slr.py` | Construção SLR(1): itens LR(0), `closure`/`goto`, coleção canônica, FIRST/FOLLOW, tabelas ACTION/GOTO, detecção de conflitos. |
| `parser.py` | Autômato de pilha shift/reduce, recuperação em modo pânico, construção da árvore e do traço. |
| `main.py` | Pipeline CLI: arquivo → léxico → tokens → parser → relatório. |
| `GLC.md` | Gramática final para exportar em PDF. |
| `ExemploArjanov.arj` | Entrada completa (todas as primitivas). |
| `erros.arj` | Entrada com erros sintáticos (demonstra modo pânico). |
| `README.md` | Como executar + nota sobre a simplificação da GLC. |

## Mapeamento terminal (GLC ↔ léxico)

Terminais genéricos que carregam lexema: `IDENTIFICADOR` (id), `INTEIRO`
(num_int), `DECIMAL` (num_dec), `STRING` (cadeia). Fim de entrada: token `EOF`
→ símbolo `$`. Os demais terminais são os próprios `TokenType` (palavras
reservadas, pontuação e os operadores agrupados). Token `ERRO` → não é símbolo;
dispara recuperação.

## Estado / progresso

**Implementação concluída e testada.** Ver a seção "Status" do `README.md`.

- `slr.py`: 125 estados, **0 conflitos** → gramática é SLR(1).
- `ExemploArjanov.arj`: **ACEITO** (cobre todas as primitivas / todas as produções).
- `erros.arj`: **REJEITADO** com 4 erros sintáticos + 1 léxico, recuperação
  localizada (sem cascata); `if`/`return` válidos após os erros são analisados.
- Códigos de saída verificados: 0 (aceito) / 1 (erros) / 2 (E-S).

Pendências são apenas de **entrega** (não de código): exportar `GLC.md` → PDF e
compactar via Teams (prazo 05/08/2026).

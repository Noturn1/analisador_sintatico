# Gramática Livre de Contexto — Arjanov (Parte 2, versão SLR simplificada)

> Esta é a gramática **efetivamente implementada** pelo analisador sintático
> SLR(1). Difere da `GLC_Arjanov_SLR.pdf` original apenas nas produções de
> expressão: os operadores foram agrupados nos terminais que o analisador
> léxico já produz (`OP_RELACIONAL`, `OP_ADITIVO`, `OP_MULTIPLICATIVO`,
> `OP_POTENCIA`, `OP_AND`, `OP_OR`, `OP_XOR`). Assim o alfabeto de terminais do
> parser coincide com os `TokenType` do léxico. A hierarquia de precedência
> (menor → maior) é preservada pela estrutura das produções.
>
> **Exportar para PDF antes de entregar** (requisito da Parte 2).

## Produções

```
 0)  programa'       → programa

 1)  programa        → lista_funcoes

 2)  lista_funcoes   → lista_funcoes funcao
 3)  lista_funcoes   → funcao

 4)  funcao          → func nome_funcao ( parametros ) bloco

 5)  nome_funcao     → id
 6)  nome_funcao     → main

 7)  parametros      → lista_ids
 8)  parametros      → ε

 9)  lista_ids       → lista_ids , id
10)  lista_ids       → id

11)  bloco           → { lista_comandos }

12)  lista_comandos  → lista_comandos comando
13)  lista_comandos  → ε

14)  comando         → declaracao ;
15)  comando         → atribuicao ;
16)  comando         → chamada ;
17)  comando         → retorno ;
18)  comando         → cmd_if
19)  comando         → cmd_while
20)  comando         → cmd_for
21)  comando         → cmd_switch

22)  declaracao      → tipo id
23)  declaracao      → tipo id = expressao

24)  tipo            → int
25)  tipo            → float
26)  tipo            → str
27)  tipo            → bool

28)  atribuicao      → id = expressao

29)  chamada         → nome_chamada ( argumentos )

30)  nome_chamada    → id
31)  nome_chamada    → puts
32)  nome_chamada    → input

33)  argumentos      → lista_expr
34)  argumentos      → ε

35)  lista_expr      → lista_expr , expressao
36)  lista_expr      → expressao

37)  retorno         → return expressao
38)  retorno         → return

39)  cmd_if          → if ( expressao ) bloco senao

40)  senao           → else bloco
41)  senao           → ε

42)  cmd_while       → while ( expressao ) bloco

43)  cmd_for         → for ( for_ini ; expressao ; atribuicao ) bloco

44)  for_ini         → declaracao
45)  for_ini         → atribuicao

46)  cmd_switch      → switch ( expressao ) { lista_casos }

47)  lista_casos     → lista_casos caso
48)  lista_casos     → ε

49)  caso            → case expressao : lista_comandos

--- Expressões: precedência embutida (menor → maior) ---

50)  expressao       → expr_or

51)  expr_or         → expr_or  OP_OR  expr_xor
52)  expr_or         → expr_xor

53)  expr_xor        → expr_xor  OP_XOR  expr_and         (XOR e XNOR)
54)  expr_xor        → expr_and

55)  expr_and        → expr_and  OP_AND  expr_rel
56)  expr_and        → expr_rel

57)  expr_rel        → expr_rel  OP_RELACIONAL  expr_ad   (== != < > <= >=)
58)  expr_rel        → expr_ad

59)  expr_ad         → expr_ad  OP_ADITIVO  expr_mul      (+ -)
60)  expr_ad         → expr_mul

61)  expr_mul        → expr_mul  OP_MULTIPLICATIVO  expr_pot   (* / %)
62)  expr_mul        → expr_pot

63)  expr_pot        → expr_prim  OP_POTENCIA  expr_pot   (^, assoc. à direita)
64)  expr_pot        → expr_prim

65)  expr_prim       → ( expressao )
66)  expr_prim       → chamada
67)  expr_prim       → id
68)  expr_prim       → num_int
69)  expr_prim       → num_dec
70)  expr_prim       → cadeia
71)  expr_prim       → true
72)  expr_prim       → false
```

## Terminais e mapeamento com o léxico

Os terminais da gramática são os `TokenType` produzidos pelo analisador léxico
da Parte 1. Os quatro terminais genéricos carregam o lexema; os demais casam
diretamente com o `TokenType` correspondente.

| Terminal na GLC | Token (léxico) | Descrição |
|---|---|---|
| `id` | `IDENTIFICADOR` | Nome de variável ou função |
| `num_int` | `INTEIRO` | Literal inteiro (ex.: `42`) |
| `num_dec` | `DECIMAL` | Literal decimal (ex.: `3.14`) |
| `cadeia` | `STRING` | Literal entre aspas simples |
| `func main if else for while switch case return int float str bool true false puts input` | (keywords) | Palavras reservadas |
| `( ) { } ; , : =` | (pontuação) | Delimitadores e atribuição |
| `OP_ADITIVO` | `OP_ADITIVO` | `+` `-` |
| `OP_MULTIPLICATIVO` | `OP_MULTIPLICATIVO` | `*` `/` `%` |
| `OP_POTENCIA` | `OP_POTENCIA` | `^` |
| `OP_RELACIONAL` | `OP_RELACIONAL` | `==` `!=` `<` `>` `<=` `>=` |
| `OP_AND` `OP_OR` `OP_XOR` | idem | `AND` / `OR` / `XOR`,`XNOR` |
| `$` | `EOF` | Marca o fim da entrada |

O token `ERRO`, emitido pelo léxico para caracteres inválidos (e strings não
terminadas), **não** é símbolo da gramática: ele dispara diretamente a rotina de
tratamento de erros do parser (recuperação em modo pânico).

> Observação: no léxico, `XOR` e `XNOR` são mapeados ao mesmo `TokenType`
> (`OP_XOR`), então as produções 53 e 54 originais colapsam em uma só.
> Analogamente, os seis relacionais colapsam em `OP_RELACIONAL`, os aditivos em
> `OP_ADITIVO` e os multiplicativos em `OP_MULTIPLICATIVO`.

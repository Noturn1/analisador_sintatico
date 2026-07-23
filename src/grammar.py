"""
grammar.py - Gramática Livre de Contexto da linguagem Arjanov (Parte 2)

Esta é a versão **simplificada** da GLC (ver docs/DECISOES.md #3): as produções
de expressão usam os terminais *agrupados* do analisador léxico
(OP_RELACIONAL, OP_ADITIVO, OP_MULTIPLICATIVO, OP_POTENCIA, OP_AND, OP_OR,
OP_XOR) em vez de um terminal por operador. Assim, o alfabeto de terminais do
parser coincide com os TokenType do léxico.

Representação:
  - Cada símbolo é uma string.
  - Terminais são os NOMES de TokenType (ex.: "IDENTIFICADOR", "OP_ADITIVO",
    "PAREN_ESQ", ...) mais "$" (fim de entrada).
  - Não-terminais são nomes em minúsculas (ex.: "programa", "expressao", ...),
    além do símbolo inicial aumentado "programa'".
  - Uma produção é um par (cabeca, corpo), onde corpo é uma tupla de símbolos.
    O corpo vazio () representa ε.

A ordem das produções em PRODUCOES define seus números (0..N-1), usados na
saída de reduções.
"""

from token import TokenType

# Símbolo inicial aumentado (produção 0) e símbolo inicial da linguagem.
SIMBOLO_INICIAL_AUMENTADO = "programa'"
SIMBOLO_INICIAL = "programa"

# Marcador de fim de entrada.
FIM = "$"

# ε é representado por corpo vazio.
EPSILON = ()


# ---------------------------------------------------------------------------
# Produções (numeradas pela posição na lista)
# ---------------------------------------------------------------------------
# Convenção de leitura: (cabeca, (simbolo, simbolo, ...))
PRODUCOES: list[tuple[str, tuple[str, ...]]] = [
    # 0 — produção aumentada
    ("programa'", ("programa",)),

    # 1
    ("programa", ("lista_funcoes",)),

    # 2..3 — lista de funções (recursão à esquerda)
    ("lista_funcoes", ("lista_funcoes", "funcao")),
    ("lista_funcoes", ("funcao",)),

    # 4 — função
    ("funcao", ("FUNC", "nome_funcao", "PAREN_ESQ", "parametros", "PAREN_DIR", "bloco")),

    # 5..6
    ("nome_funcao", ("IDENTIFICADOR",)),
    ("nome_funcao", ("MAIN",)),

    # 7..8 — parâmetros
    ("parametros", ("lista_ids",)),
    ("parametros", EPSILON),

    # 9..10 — lista de ids
    ("lista_ids", ("lista_ids", "VIRGULA", "IDENTIFICADOR")),
    ("lista_ids", ("IDENTIFICADOR",)),

    # 11 — bloco
    ("bloco", ("CHAVE_ESQ", "lista_comandos", "CHAVE_DIR")),

    # 12..13 — lista de comandos
    ("lista_comandos", ("lista_comandos", "comando")),
    ("lista_comandos", EPSILON),

    # 14..21 — comandos
    ("comando", ("declaracao", "PONTO_VIRGULA")),
    ("comando", ("atribuicao", "PONTO_VIRGULA")),
    ("comando", ("chamada", "PONTO_VIRGULA")),
    ("comando", ("retorno", "PONTO_VIRGULA")),
    ("comando", ("cmd_if",)),
    ("comando", ("cmd_while",)),
    ("comando", ("cmd_for",)),
    ("comando", ("cmd_switch",)),

    # 22..23 — declaração
    ("declaracao", ("tipo", "IDENTIFICADOR")),
    ("declaracao", ("tipo", "IDENTIFICADOR", "ATRIBUICAO", "expressao")),

    # 24..27 — tipos
    ("tipo", ("INT",)),
    ("tipo", ("FLOAT",)),
    ("tipo", ("STR",)),
    ("tipo", ("BOOL",)),

    # 28 — atribuição
    ("atribuicao", ("IDENTIFICADOR", "ATRIBUICAO", "expressao")),

    # 29 — chamada
    ("chamada", ("nome_chamada", "PAREN_ESQ", "argumentos", "PAREN_DIR")),

    # 30..32
    ("nome_chamada", ("IDENTIFICADOR",)),
    ("nome_chamada", ("PUTS",)),
    ("nome_chamada", ("INPUT",)),

    # 33..34 — argumentos
    ("argumentos", ("lista_expr",)),
    ("argumentos", EPSILON),

    # 35..36 — lista de expressões
    ("lista_expr", ("lista_expr", "VIRGULA", "expressao")),
    ("lista_expr", ("expressao",)),

    # 37..38 — retorno
    ("retorno", ("RETURN", "expressao")),
    ("retorno", ("RETURN",)),

    # 39 — if
    ("cmd_if", ("IF", "PAREN_ESQ", "expressao", "PAREN_DIR", "bloco", "senao")),

    # 40..41
    ("senao", ("ELSE", "bloco")),
    ("senao", EPSILON),

    # 42 — while
    ("cmd_while", ("WHILE", "PAREN_ESQ", "expressao", "PAREN_DIR", "bloco")),

    # 43 — for
    ("cmd_for", ("FOR", "PAREN_ESQ", "for_ini", "PONTO_VIRGULA", "expressao",
                 "PONTO_VIRGULA", "atribuicao", "PAREN_DIR", "bloco")),

    # 44..45
    ("for_ini", ("declaracao",)),
    ("for_ini", ("atribuicao",)),

    # 46 — switch
    ("cmd_switch", ("SWITCH", "PAREN_ESQ", "expressao", "PAREN_DIR",
                    "CHAVE_ESQ", "lista_casos", "CHAVE_DIR")),

    # 47..48 — lista de casos
    ("lista_casos", ("lista_casos", "caso")),
    ("lista_casos", EPSILON),

    # 49 — caso
    ("caso", ("CASE", "expressao", "DOIS_PONTOS", "lista_comandos")),

    # 50 — expressão (raiz da cadeia de precedência)
    ("expressao", ("expr_or",)),

    # 51..52 — OR
    ("expr_or", ("expr_or", "OP_OR", "expr_xor")),
    ("expr_or", ("expr_xor",)),

    # 53..54 — XOR/XNOR (ambos mapeados a OP_XOR pelo léxico)
    ("expr_xor", ("expr_xor", "OP_XOR", "expr_and")),
    ("expr_xor", ("expr_and",)),

    # 55..56 — AND
    ("expr_and", ("expr_and", "OP_AND", "expr_rel")),
    ("expr_and", ("expr_rel",)),

    # 57..58 — relacionais (== != < > <= >=  ->  OP_RELACIONAL)
    ("expr_rel", ("expr_rel", "OP_RELACIONAL", "expr_ad")),
    ("expr_rel", ("expr_ad",)),

    # 59..60 — aditivos (+ -  ->  OP_ADITIVO)
    ("expr_ad", ("expr_ad", "OP_ADITIVO", "expr_mul")),
    ("expr_ad", ("expr_mul",)),

    # 61..62 — multiplicativos (* / %  ->  OP_MULTIPLICATIVO)
    ("expr_mul", ("expr_mul", "OP_MULTIPLICATIVO", "expr_pot")),
    ("expr_mul", ("expr_pot",)),

    # 63..64 — potência (^  ->  OP_POTENCIA, associativa à direita)
    ("expr_pot", ("expr_prim", "OP_POTENCIA", "expr_pot")),
    ("expr_pot", ("expr_prim",)),

    # 65..72 — primários
    ("expr_prim", ("PAREN_ESQ", "expressao", "PAREN_DIR")),
    ("expr_prim", ("chamada",)),
    ("expr_prim", ("IDENTIFICADOR",)),
    ("expr_prim", ("INTEIRO",)),
    ("expr_prim", ("DECIMAL",)),
    ("expr_prim", ("STRING",)),
    ("expr_prim", ("TRUE",)),
    ("expr_prim", ("FALSE",)),
]


# ---------------------------------------------------------------------------
# Terminais e não-terminais derivados das produções
# ---------------------------------------------------------------------------

def _coletar_simbolos():
    """Separa símbolos das produções em não-terminais e terminais."""
    nao_terminais = {cabeca for cabeca, _ in PRODUCOES}
    simbolos = set()
    for _, corpo in PRODUCOES:
        simbolos.update(corpo)
    terminais = (simbolos - nao_terminais) | {FIM}
    return nao_terminais, terminais


NAO_TERMINAIS, TERMINAIS = _coletar_simbolos()


# Não-terminais escolhidos como pontos de sincronização na recuperação de erro
# (modo pânico, "método do Dragão"). Ordem = PRIORIDADE GLOBAL: procuramos na
# pilha, do topo para baixo, um estado com GOTO sobre 'comando' (recuperação em
# nível de comando/statement — a que melhor localiza o erro); só se não houver,
# recuamos para 'bloco' e por fim 'funcao'. Sincronizar em nível de comando faz
# o parser descartar o statement inteiro que contém o erro e retomar limpo no
# próximo statement, evitando cascatas de erros espúrios.
NAO_TERMINAIS_RECUPERACAO = ("comando", "bloco", "funcao")


def simbolo_do_token(token) -> str:
    """
    Traduz um Token (produzido pelo léxico) para o símbolo terminal
    correspondente na gramática.

    - EOF  -> "$"
    - demais -> o próprio nome do TokenType (ex.: OP_ADITIVO, IDENTIFICADOR)

    O token ERRO NÃO é símbolo da gramática; ele é tratado à parte pelo parser
    (dispara a recuperação). Ainda assim retornamos seu nome para diagnósticos.
    """
    if token.tipo == TokenType.EOF:
        return FIM
    return token.tipo.name


def formatar_producao(indice: int) -> str:
    """Formata uma produção como 'cabeca -> s1 s2 ...' (ε para corpo vazio)."""
    cabeca, corpo = PRODUCOES[indice]
    direita = " ".join(corpo) if corpo else "ε"
    return f"{cabeca} -> {direita}"


def validar_gramatica() -> list[str]:
    """
    Verificações básicas de sanidade (não é análise SLR — isso é papel de slr.py).
    Retorna lista de problemas encontrados (vazia se tudo ok).
    """
    problemas = []
    # Toda cabeça de produção deve ser alcançável e todo NT usado deve produzir.
    usados = set()
    for _, corpo in PRODUCOES:
        for s in corpo:
            if s in NAO_TERMINAIS:
                usados.add(s)
    definidos = {c for c, _ in PRODUCOES}
    for nt in usados:
        if nt not in definidos:
            problemas.append(f"Não-terminal usado mas não definido: {nt}")
    for nt in NAO_TERMINAIS_RECUPERACAO:
        if nt not in NAO_TERMINAIS:
            problemas.append(f"NT de recuperação inexistente: {nt}")
    return problemas

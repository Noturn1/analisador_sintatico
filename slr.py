"""
slr.py - Construção da tabela de análise sintática SLR(1)

Implementa, "na mão" (sem yacc/bison), o algoritmo clássico de construção de um
analisador SLR(1) a partir da gramática de grammar.py:

  1. Itens LR(0)  ............ (indice_producao, posicao_do_ponto)
  2. CLOSURE / GOTO  ......... fecho de conjuntos de itens e transições
  3. Coleção canônica  ...... conjunto de estados (autômato LR(0))
  4. FIRST / FOLLOW  ......... conjuntos para decidir reduções (o "S" de SLR)
  5. ACTION / GOTO  ......... tabelas de decisão do parser
  6. Detecção de conflitos  . valida que a gramática é de fato SLR(1)

As ações em ACTION são tuplas:
    ("shift", estado)
    ("reduce", indice_producao)
    ("accept",)

GOTO[estado][nao_terminal] = estado.
"""

from grammar import (
    PRODUCOES,
    NAO_TERMINAIS,
    TERMINAIS,
    SIMBOLO_INICIAL_AUMENTADO,
    FIM,
    EPSILON,
    formatar_producao,
)


# ---------------------------------------------------------------------------
# Itens LR(0)
# ---------------------------------------------------------------------------
# Um item é o par (i, ponto): produção i com o ponto antes da posição 'ponto'
# do corpo. Item completo => ponto == len(corpo).


def _corpo(i: int) -> tuple:
    return PRODUCOES[i][1]


def _cabeca(i: int) -> str:
    return PRODUCOES[i][0]


def _simbolo_apos_ponto(item):
    """Retorna o símbolo imediatamente após o ponto, ou None se item completo."""
    i, ponto = item
    corpo = _corpo(i)
    if ponto < len(corpo):
        return corpo[ponto]
    return None


# Pré-indexa as produções por cabeça (para CLOSURE ser rápida).
_PRODUCOES_POR_CABECA: dict[str, list[int]] = {}
for _i, (_cab, _corp) in enumerate(PRODUCOES):
    _PRODUCOES_POR_CABECA.setdefault(_cab, []).append(_i)


def closure(itens: frozenset) -> frozenset:
    """
    CLOSURE de um conjunto de itens LR(0).

    Enquanto houver [A -> α . B β] no conjunto e B for não-terminal, adiciona
    [B -> . γ] para toda produção B -> γ.
    """
    fechamento = set(itens)
    pilha = list(itens)
    while pilha:
        item = pilha.pop()
        B = _simbolo_apos_ponto(item)
        if B is not None and B in NAO_TERMINAIS:
            for j in _PRODUCOES_POR_CABECA.get(B, ()):
                novo = (j, 0)
                if novo not in fechamento:
                    fechamento.add(novo)
                    pilha.append(novo)
    return frozenset(fechamento)


def goto(itens: frozenset, simbolo: str) -> frozenset:
    """
    GOTO(I, X): fecho do conjunto dos itens [A -> α X . β] tais que
    [A -> α . X β] pertence a I.
    """
    movidos = set()
    for (i, ponto) in itens:
        corpo = _corpo(i)
        if ponto < len(corpo) and corpo[ponto] == simbolo:
            movidos.add((i, ponto + 1))
    return closure(frozenset(movidos)) if movidos else frozenset()


def colecao_canonica():
    """
    Constrói a coleção canônica de conjuntos de itens LR(0) e as transições.

    Retorna:
      estados     : lista de frozenset (índice = número do estado)
      transicoes  : dict {(estado, simbolo): estado}
    """
    inicial = closure(frozenset({(0, 0)}))  # produção 0 = S' -> . programa
    estados = [inicial]
    indice_de = {inicial: 0}
    transicoes: dict[tuple[int, str], int] = {}

    # Símbolos que aparecem após um ponto em algum item (ordem determinística).
    todos_simbolos = list(TERMINAIS - {FIM}) + list(NAO_TERMINAIS)

    fila = [inicial]
    while fila:
        I = fila.pop(0)
        i_idx = indice_de[I]
        for X in todos_simbolos:
            J = goto(I, X)
            if not J:
                continue
            if J not in indice_de:
                indice_de[J] = len(estados)
                estados.append(J)
                fila.append(J)
            transicoes[(i_idx, X)] = indice_de[J]
    return estados, transicoes


# ---------------------------------------------------------------------------
# FIRST / FOLLOW
# ---------------------------------------------------------------------------


def calcular_first() -> dict[str, set]:
    """
    FIRST de cada símbolo. Para terminais, FIRST(t) = {t}.
    ε é representado pela string vazia "" dentro dos conjuntos.
    """
    first: dict[str, set] = {t: {t} for t in TERMINAIS}
    for nt in NAO_TERMINAIS:
        first[nt] = set()

    mudou = True
    while mudou:
        mudou = False
        for cabeca, corpo in PRODUCOES:
            antes = len(first[cabeca])
            if corpo == EPSILON:
                first[cabeca].add("")
            else:
                # Percorre o corpo enquanto os símbolos derivarem ε.
                todos_epsilon = True
                for s in corpo:
                    first[cabeca].update(first[s] - {""})
                    if "" not in first[s]:
                        todos_epsilon = False
                        break
                if todos_epsilon:
                    first[cabeca].add("")
            if len(first[cabeca]) != antes:
                mudou = True
    return first


def first_de_sequencia(seq, first) -> set:
    """FIRST de uma sequência de símbolos (para o cálculo de FOLLOW)."""
    resultado = set()
    todos_epsilon = True
    for s in seq:
        resultado.update(first[s] - {""})
        if "" not in first[s]:
            todos_epsilon = False
            break
    if todos_epsilon:
        resultado.add("")
    return resultado


def calcular_follow(first) -> dict[str, set]:
    """
    FOLLOW de cada não-terminal. FOLLOW(S') recebe {$}.
    """
    follow: dict[str, set] = {nt: set() for nt in NAO_TERMINAIS}
    follow[SIMBOLO_INICIAL_AUMENTADO].add(FIM)

    mudou = True
    while mudou:
        mudou = False
        for cabeca, corpo in PRODUCOES:
            for k, B in enumerate(corpo):
                if B not in NAO_TERMINAIS:
                    continue
                antes = len(follow[B])
                beta = corpo[k + 1:]
                primeiros_beta = first_de_sequencia(beta, first)
                follow[B].update(primeiros_beta - {""})
                if "" in primeiros_beta:  # β deriva ε (ou é vazio)
                    follow[B].update(follow[cabeca])
                if len(follow[B]) != antes:
                    mudou = True
    return follow


# ---------------------------------------------------------------------------
# Tabelas ACTION / GOTO
# ---------------------------------------------------------------------------


class ConflitoSLR:
    """Descreve um conflito encontrado ao montar a tabela (shift/reduce ou reduce/reduce)."""

    def __init__(self, estado, terminal, acao_existente, acao_nova):
        self.estado = estado
        self.terminal = terminal
        self.acao_existente = acao_existente
        self.acao_nova = acao_nova

    def __repr__(self):
        return (
            f"[Conflito] estado {self.estado}, terminal '{self.terminal}': "
            f"{self.acao_existente} vs {self.acao_nova}"
        )


class TabelaSLR:
    """
    Reúne tudo o que o parser precisa: número de estados, ACTION, GOTO e a lista
    de conflitos (vazia se a gramática for SLR(1)).
    """

    def __init__(self):
        self.estados, self.transicoes = colecao_canonica()
        self.first = calcular_first()
        self.follow = calcular_follow(self.first)
        self.action: dict[tuple[int, str], tuple] = {}
        self.goto: dict[tuple[int, str], int] = {}
        self.conflitos: list[ConflitoSLR] = []
        self._montar()

    def _por_action(self, estado, terminal, acao):
        """Registra uma ação em ACTION, detectando conflitos."""
        chave = (estado, terminal)
        existente = self.action.get(chave)
        if existente is not None and existente != acao:
            # Registra o conflito; mantém a ação já existente (shift tende a vir
            # primeiro, mas para SLR "puro" qualquer conflito invalida a tabela).
            self.conflitos.append(ConflitoSLR(estado, terminal, existente, acao))
            return
        self.action[chave] = acao

    def _montar(self):
        for i, I in enumerate(self.estados):
            for item in I:
                simbolo = _simbolo_apos_ponto(item)
                if simbolo is None:
                    # Item completo: reduzir ou aceitar.
                    idx_prod = item[0]
                    if _cabeca(idx_prod) == SIMBOLO_INICIAL_AUMENTADO:
                        # S' -> programa .  => aceitar em '$'
                        self._por_action(i, FIM, ("accept",))
                    else:
                        for a in self.follow[_cabeca(idx_prod)]:
                            self._por_action(i, a, ("reduce", idx_prod))
                elif simbolo in TERMINAIS:
                    # Item com terminal após o ponto: shift.
                    destino = self.transicoes.get((i, simbolo))
                    if destino is not None:
                        self._por_action(i, simbolo, ("shift", destino))
            # GOTO para não-terminais.
            for nt in NAO_TERMINAIS:
                destino = self.transicoes.get((i, nt))
                if destino is not None:
                    self.goto[(i, nt)] = destino

    # -- consultas usadas pelo parser --------------------------------------

    def obter_action(self, estado, terminal):
        return self.action.get((estado, terminal))

    def obter_goto(self, estado, nao_terminal):
        return self.goto.get((estado, nao_terminal))

    def tem_goto_sobre(self, estado, nao_terminal) -> bool:
        return (estado, nao_terminal) in self.goto

    # -- diagnósticos -------------------------------------------------------

    def resumo(self) -> str:
        linhas = [
            f"Estados (itens LR(0)): {len(self.estados)}",
            f"Entradas em ACTION:    {len(self.action)}",
            f"Entradas em GOTO:      {len(self.goto)}",
            f"Conflitos:             {len(self.conflitos)}",
        ]
        return "\n".join(linhas)


if __name__ == "__main__":
    # Execução direta: mostra estatísticas e eventuais conflitos.
    tabela = TabelaSLR()
    print(tabela.resumo())
    if tabela.conflitos:
        print("\nCONFLITOS ENCONTRADOS (gramática não é SLR(1) como está):")
        for c in tabela.conflitos:
            print("  ", c)
            print("     ação nova refere-se a:", end=" ")
            if c.acao_nova[0] == "reduce":
                print(formatar_producao(c.acao_nova[1]))
            else:
                print(c.acao_nova)
    else:
        print("\nOK: a gramática é SLR(1) (nenhum conflito na tabela).")

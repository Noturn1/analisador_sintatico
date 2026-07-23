"""
parser.py - Analisador Sintático SLR(1) da linguagem Arjanov

Autômato de pilha dirigido pelas tabelas ACTION/GOTO de slr.py:

  - shift   : empilha estado + folha da árvore, consome o token
  - reduce  : desempilha |corpo| símbolos, cria nó da árvore, empilha GOTO
  - accept  : entrada reconhecida

Recuperação de erros em MODO PÂNICO ("método do Dragão" para LR, ver
docs/DECISOES.md #5):
  1. desempilha estados até um estado s com GOTO sobre um não-terminal de
     recuperação A (prioridade global: comando, depois bloco, depois funcao);
  2. descarta tokens de entrada até um símbolo que possa seguir A (FOLLOW(A))
     ou o fim de entrada;
  3. empilha GOTO[s, A] (com um nó-marcador de erro) e retoma a análise.

O token ERRO produzido pelo léxico não é símbolo da gramática: ele dispara
diretamente a recuperação (também ver docs/DECISOES.md #9).

Saída (ver docs/DECISOES.md #4): aceita/rejeita, lista de erros sintáticos, o
traço de ações shift/reduce e a árvore sintática.
"""

from token import Token, TokenType
from grammar import (
    PRODUCOES,
    NAO_TERMINAIS_RECUPERACAO,
    FIM,
    simbolo_do_token,
    formatar_producao,
)
from slr import TabelaSLR


# Nomes legíveis para mensagens de erro (terminais "simbólicos").
SIMBOLO_LEGIVEL = {
    "PAREN_ESQ": "'('",
    "PAREN_DIR": "')'",
    "CHAVE_ESQ": "'{'",
    "CHAVE_DIR": "'}'",
    "PONTO_VIRGULA": "';'",
    "VIRGULA": "','",
    "DOIS_PONTOS": "':'",
    "ATRIBUICAO": "'='",
    "OP_ADITIVO": "operador aditivo (+ -)",
    "OP_MULTIPLICATIVO": "operador multiplicativo (* / %)",
    "OP_POTENCIA": "'^'",
    "OP_RELACIONAL": "operador relacional (== != < > <= >=)",
    "OP_AND": "'AND'",
    "OP_OR": "'OR'",
    "OP_XOR": "'XOR'/'XNOR'",
    "IDENTIFICADOR": "identificador",
    "INTEIRO": "literal inteiro",
    "DECIMAL": "literal decimal",
    "STRING": "literal string",
    FIM: "fim de arquivo",
}


def _legivel(simbolo: str) -> str:
    return SIMBOLO_LEGIVEL.get(simbolo, f"'{simbolo.lower()}'" if simbolo.isupper() else simbolo)


class NoArvore:
    """
    Nó da árvore sintática.

    - Folha (terminal): 'token' preenchido, 'filhos' vazio.
    - Interno (não-terminal): 'filhos' preenchido, 'token' None.
    - 'erro' marca nós-marcadores criados durante a recuperação.
    """

    def __init__(self, simbolo: str, token: Token = None, filhos=None, erro=False):
        self.simbolo = simbolo
        self.token = token
        self.filhos = filhos or []
        self.erro = erro

    def eh_folha(self) -> bool:
        return self.token is not None


class ErroSintatico:
    """Erro sintático acumulado (modo pânico não interrompe a análise)."""

    def __init__(self, mensagem: str, linha: int, coluna: int):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return f"[Erro Sintático] Linha {self.linha}, Coluna {self.coluna}: {self.mensagem}"


class ResultadoParser:
    """Agrega tudo o que o parser produz para o relatório final."""

    def __init__(self):
        self.aceito = False
        self.erros: list[ErroSintatico] = []
        self.acoes: list[str] = []
        self.arvore: NoArvore | None = None


class Parser:
    """Analisador sintático SLR(1) com recuperação em modo pânico."""

    # Limite de segurança: recuperações consecutivas sem um shift antes de
    # forçar o descarte de um token (garante terminação).
    LIMITE_RECUPERACAO = 3

    def __init__(self, tokens: list[Token], tabela: TabelaSLR = None):
        # Ignora tokens irrelevantes? Não — todos os tokens do léxico entram.
        self.tokens = tokens
        self.tabela = tabela if tabela is not None else TabelaSLR()

        self.i = 0  # índice do token corrente
        self.pilha_estados = [0]
        self.pilha_nos: list[NoArvore] = []

        self.resultado = ResultadoParser()
        self._pos_ultima_recuperacao = -1

    # -- utilidades de posição ---------------------------------------------

    def _token(self) -> Token:
        return self.tokens[self.i]

    def _fim_entrada(self) -> bool:
        return self._token().tipo == TokenType.EOF

    def _descartar_um(self):
        """Descarta o token corrente, se não for o EOF."""
        if not self._fim_entrada():
            self.i += 1

    # -- laço principal -----------------------------------------------------

    def analisar(self) -> ResultadoParser:
        while True:
            estado = self.pilha_estados[-1]
            tok = self._token()

            # Token inválido vindo do léxico: dispara recuperação direta.
            if tok.tipo == TokenType.ERRO:
                self._registrar_erro(
                    f"token inválido do léxico: {tok.lexema!r}", tok
                )
                if not self._recuperar():
                    break
                continue

            simbolo = simbolo_do_token(tok)
            acao = self.tabela.obter_action(estado, simbolo)

            if acao is None:
                self._registrar_erro_sintatico(estado, tok, simbolo)
                if not self._recuperar():
                    break
                continue

            tipo = acao[0]
            if tipo == "shift":
                self.pilha_estados.append(acao[1])
                self.pilha_nos.append(NoArvore(simbolo, token=tok))
                self.resultado.acoes.append(
                    f"SHIFT  {simbolo} {tok.lexema!r}  -> estado {acao[1]}"
                )
                self.i += 1
                self._pos_ultima_recuperacao = -1  # houve progresso real

            elif tipo == "reduce":
                self._reduzir(acao[1])

            elif tipo == "accept":
                self.resultado.acoes.append("ACCEPT")
                self.resultado.aceito = len(self.resultado.erros) == 0
                if self.pilha_nos:
                    self.resultado.arvore = self.pilha_nos[-1]
                break

        return self.resultado

    def _reduzir(self, indice_producao: int):
        cabeca, corpo = PRODUCOES[indice_producao]
        n = len(corpo)
        filhos = []
        for _ in range(n):
            self.pilha_estados.pop()
            filhos.append(self.pilha_nos.pop())
        filhos.reverse()

        no = NoArvore(cabeca, filhos=filhos)
        topo = self.pilha_estados[-1]
        destino = self.tabela.obter_goto(topo, cabeca)
        # destino sempre existe numa tabela SLR bem-formada após uma redução válida.
        self.pilha_estados.append(destino)
        self.pilha_nos.append(no)
        self.resultado.acoes.append(
            f"REDUCE {indice_producao}: {formatar_producao(indice_producao)}"
        )

    # -- registro de erros --------------------------------------------------

    def _registrar_erro(self, mensagem: str, tok: Token):
        self.resultado.erros.append(ErroSintatico(mensagem, tok.linha, tok.coluna))

    def _registrar_erro_sintatico(self, estado: int, tok: Token, simbolo: str):
        esperados = self._terminais_esperados(estado)
        encontrado = _legivel(simbolo)
        if tok.lexema:
            encontrado += f" ({tok.lexema!r})"
        if esperados:
            lista = ", ".join(_legivel(s) for s in esperados)
            msg = f"encontrado {encontrado}; esperado um de: {lista}"
        else:
            msg = f"token inesperado: {encontrado}"
        self._registrar_erro(msg, tok)

    def _terminais_esperados(self, estado: int) -> list[str]:
        """Terminais para os quais o estado tem alguma ação (para diagnóstico)."""
        esperados = [
            s for (e, s), _ in self.tabela.action.items() if e == estado
        ]
        return sorted(set(esperados))

    # -- recuperação em modo pânico ----------------------------------------

    def _recuperar(self) -> bool:
        """
        Executa uma rodada de recuperação em modo pânico.
        Retorna True se conseguiu sincronizar/retomar, False se deve encerrar.
        """
        # Guarda de progresso: se estamos re-errando exatamente no mesmo token
        # de uma recuperação anterior, força o descarte de um token.
        if self.i == self._pos_ultima_recuperacao:
            if self._fim_entrada():
                return False  # nada a descartar; encerra
            self._descartar_um()

        # 1. Procura um estado na pilha com GOTO sobre um não-terminal de
        #    recuperação, respeitando a PRIORIDADE GLOBAL de
        #    NAO_TERMINAIS_RECUPERACAO: primeiro tenta 'comando' (nível de
        #    statement) em toda a pilha; só recua para 'bloco'/'funcao' se não
        #    houver estado que sincronize em 'comando'. Para cada não-terminal,
        #    escolhe o estado mais ao topo (recuperação mais próxima do erro).
        escolhido = None  # (posicao_na_pilha, estado, nao_terminal)
        for A in NAO_TERMINAIS_RECUPERACAO:
            for pos in range(len(self.pilha_estados) - 1, -1, -1):
                if self.tabela.tem_goto_sobre(self.pilha_estados[pos], A):
                    escolhido = (pos, self.pilha_estados[pos], A)
                    break
            if escolhido:
                break

        if escolhido is None:
            # Impossível sincronizar: descarta o resto e encerra.
            while not self._fim_entrada():
                self.i += 1
            self._pos_ultima_recuperacao = self.i
            return False

        pos, estado, A = escolhido
        follow_A = self.tabela.follow[A]

        # 2. Descarta tokens de entrada até um símbolo em FOLLOW(A) (ou EOF).
        while not self._fim_entrada():
            tok = self._token()
            if tok.tipo == TokenType.ERRO:
                self.i += 1  # ignora tokens de erro do léxico durante o descarte
                continue
            if simbolo_do_token(tok) in follow_A:
                break
            self.i += 1

        # 3. Sincroniza a pilha: mantém estados[0..pos] e nós[0..pos-1],
        #    empilha GOTO[estado, A] com um nó-marcador de erro.
        del self.pilha_estados[pos + 1:]
        del self.pilha_nos[pos:]
        destino = self.tabela.obter_goto(estado, A)
        self.pilha_estados.append(destino)
        self.pilha_nos.append(NoArvore(A, erro=True))

        self.resultado.acoes.append(
            f"** RECUPERAÇÃO: sincroniza em '{A}', retoma antes de "
            f"{_legivel(simbolo_do_token(self._token()))}"
        )
        self._pos_ultima_recuperacao = self.i
        return True


# ---------------------------------------------------------------------------
# Impressão da árvore sintática
# ---------------------------------------------------------------------------


def formatar_arvore(no: NoArvore, prefixo: str = "", linhas: list[str] = None) -> list[str]:
    """Serializa a árvore em linhas indentadas."""
    if linhas is None:
        linhas = []
    if no is None:
        return linhas

    if no.eh_folha():
        rotulo = f"{no.simbolo}"
        if no.token.lexema:
            rotulo += f" {no.token.lexema!r}"
        linhas.append(prefixo + rotulo)
    else:
        rotulo = no.simbolo + ("  [recuperado]" if no.erro else "")
        linhas.append(prefixo + rotulo)
        for filho in no.filhos:
            formatar_arvore(filho, prefixo + "  ", linhas)
    return linhas

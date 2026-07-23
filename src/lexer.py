# Trabalho Analisador Léxico - Compiladores

"""
lexer.py - Analisador Léxico da linguagem Arjanov

  1. Separa a string de entrada em uma sequência de tokens
  2. Classifica cada token (tipo, lexema, posição)
  3. Ignora espaços em branco
  4. Detecta e reporta erros léxicos com recuperação em modo pânico

Observação sobre importação:
  O arquivo token.py existe no mesmo diretório. Python prioriza o
  diretório do script sobre a biblioteca padrão (que também possui
  um módulo chamado 'token'), então a importação abaixo funciona
  desde que lexer.py seja executado a partir da pasta do projeto.

Ajuste da Parte 2 (ver docs/DECISOES.md #9):
  Em "string não terminada" o léxico agora emite também um token ERRO
  (antes apenas registrava o erro). Isso mantém a sincronia posicional
  para o analisador sintático, que trata ERRO disparando sua rotina de
  recuperação em modo pânico.
"""

from token import Token, TokenType, lookup_keyword

# Erro Léxico


class LexerError:
    """
    Representa um erro léxico acumulado durante a varredura.

    Não é uma exceção Python porque não queremos interromper a análise
    ao primeiro erro — queremos reportar todos os erros do arquivo.
    """

    def __init__(self, mensagem: str, linha: int, coluna: int):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def __repr__(self) -> str:
        return (
            f"[Erro Léxico] Linha {self.linha}, Coluna {self.coluna}: {self.mensagem}"
        )


# Classe Lexer


class Lexer:
    """
    Analisador Léxico da linguagem Arjanov.
    """

    def __init__(self, codigo_fonte: str):
        """
        codigo_fonte : str
            Texto completo do programa a ser analisado.
        """
        self.codigo = codigo_fonte

        # Estado da varredura
        self.pos = 0  # índice do próximo caractere a consumir
        self.linha = 1  # linha atual (1-based, para mensagens ao usuário)
        self.coluna = 1  # coluna atual (1-based, para mensagens ao usuário)

        # Saídas acumuladas
        self.tokens: list[Token] = []
        self.erros: list[LexerError] = []

    # Helpers do lexer

    def _fim(self) -> bool:
        """True se já consumimos todos os caracteres do código-fonte."""
        return self.pos >= len(self.codigo)

    def _atual(self) -> str:
        """
        Caractere sob o cursor (lookahead = 0), sem consumir.
        Retorna '\\0' após o fim do arquivo.
        """
        return self.codigo[self.pos] if not self._fim() else "\0"

    def _proximo(self) -> str:
        """
        Caractere imediatamente após o cursor (lookahead = 1), sem consumir.
        """
        return self.codigo[self.pos + 1] if self.pos + 1 < len(self.codigo) else "\0"

    def _avancar(self) -> str:
        """
        Consome o caractere atual, atualiza linha/coluna e retorna o caractere.
        """
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _casar(self, esperado: str) -> bool:
        """
        Se o caractere atual for 'esperado', consome e retorna True.
        Caso contrário, não mexe no cursor e retorna False.

        Usado para operadores de 2 caracteres:
            ==   !=   <=   >=
        """
        if self._fim() or self._atual() != esperado:
            return False
        self._avancar()
        return True

    # Laço principal do analisador

    def analisar(self) -> list[Token]:
        """
        Executa a análise léxica completa sobre self.codigo.
        Retorna a lista de tokens (sempre terminada com EOF).
        Erros ficam acumulados em self.erros.
        """
        while not self._fim():
            self._pular_espacos()
            if self._fim():
                break
            self._proximo_token()

        # Token usado para saber que a entrada acabou
        self.tokens.append(Token(TokenType.EOF, "", self.linha, self.coluna))
        return self.tokens

    def _pular_espacos(self):
        """
        Consome caracteres brancos: espaço, tab, CR, LF.
        """
        while not self._fim() and self._atual() in " \t\r\n":
            self._avancar()

    # Decide qual reconhecedor chamar com base no estado inicial (1o caractere)

    def _proximo_token(self):
        # Inicializa no começo
        linha_ini = self.linha
        col_ini = self.coluna
        c = self._atual()

        # Dígito => número (inteiro ou decimal)
        if c.isdigit():
            self._ler_numero(linha_ini, col_ini)
            return

        # Letra ou '_' => identificador ou palavra reservada
        if c.isalpha() or c == "_":
            self._ler_identificador(linha_ini, col_ini)
            return

        # Aspa simples => literal string
        if c == "'":
            self._ler_string(linha_ini, col_ini)
            return

        # Qualquer outro caractere: operador, delimitador, ou erro
        self._ler_simbolo(linha_ini, col_ini)

    # Reconhecedores específicos

    def _ler_numero(self, linha: int, coluna: int):
        """
        Reconhece números inteiros e decimais.

        Obs: só consumimos o '.' se houver um dígito depois.
        """
        inicio = self.pos

        # parte inteira (sempre existe, pois só entramos aqui se c.isdigit())
        while not self._fim() and self._atual().isdigit():
            self._avancar()

        tipo = TokenType.INTEIRO

        # parte fracionária (opcional; precisa de '.' + pelo menos um dígito)
        if self._atual() == "." and self._proximo().isdigit():
            self._avancar()  # consome o '.'
            while not self._fim() and self._atual().isdigit():
                self._avancar()
            tipo = TokenType.DECIMAL

        lexema = self.codigo[inicio : self.pos]
        self.tokens.append(Token(tipo, lexema, linha, coluna))

    def _ler_identificador(self, linha: int, coluna: int):
        """
        Reconhece identificadores e palavras reservadas.

        Definição regular:
            letra         = [a-zA-Z_]
            digito        = [0-9]
            identificador = letra (letra | digito)*

        "Quando há impasse entre identificador e palavra reservada,
         opta-se pela palavra reservada". Fazemos isso consultando
         KEYWORDS via lookup_keyword no FIM da leitura.
        """
        inicio = self.pos

        # Primeiro caractere já validado pelo despachante.
        # Continuamos enquanto for alfanumérico ou '_'.
        while not self._fim() and (self._atual().isalnum() or self._atual() == "_"):
            self._avancar()

        lexema = self.codigo[inicio : self.pos]
        tipo = lookup_keyword(lexema)  # devolve identificador se não for reservada
        self.tokens.append(Token(tipo, lexema, linha, coluna))

    def _ler_string(self, linha: int, coluna: int):
        """
        Reconhece literais string delimitados por aspa simples.

        Definição regular (simplificada, sem sequências de escape):
            string = ' [^'\\n]* '

        Comportamento em erro (string não terminada):
            - '\\n' antes do fechamento => erro, cursor fica no '\\n'
              para que a próxima iteração do laço principal conte a
              quebra de linha corretamente.
            - EOF antes do fechamento => erro.

        Em ambos os casos, além de registrar o erro léxico, emitimos um
        token ERRO (ver docs/DECISOES.md #9) para preservar a sincronia
        posicional com o analisador sintático.

        O lexema armazenado (no caso de sucesso) é o CONTEÚDO da string
        (sem as aspas).
        """
        self._avancar()  # consome a aspa de abertura "'"
        inicio = self.pos

        while not self._fim() and self._atual() != "'" and self._atual() != "\n":
            self._avancar()

        if self._fim() or self._atual() == "\n":
            self.erros.append(
                LexerError(
                    "String não terminada (esperado aspa simples de fechamento)",
                    linha,
                    coluna,
                )
            )
            # Emite token ERRO com o conteúdo consumido para o parser
            # disparar sua recuperação em modo pânico sem perder a posição.
            parcial = self.codigo[inicio : self.pos]
            self.tokens.append(Token(TokenType.ERRO, parcial, linha, coluna))
            return  # panic mode: aborta este token, mas não derruba o lexer

        lexema = self.codigo[inicio : self.pos]
        self._avancar()  # consome a aspa de fechamento
        self.tokens.append(Token(TokenType.STRING, lexema, linha, coluna))

    def _ler_simbolo(self, linha: int, coluna: int):
        """
        Reconhece operadores, delimitadores e pontuação.

        Usa lookahead de 1 caractere para desambiguar operadores de
        2 caracteres.
        """
        c = self._avancar()  # já consome o primeiro caractere

        #  Atribuição vs relacional '=='
        if c == "=":
            if self._casar("="):
                self.tokens.append(Token(TokenType.OP_RELACIONAL, "==", linha, coluna))
            else:
                self.tokens.append(Token(TokenType.ATRIBUICAO, "=", linha, coluna))
            return

        #  '!=' (o '!' sozinho é inválido)
        if c == "!":
            if self._casar("="):
                self.tokens.append(Token(TokenType.OP_RELACIONAL, "!=", linha, coluna))
            else:
                self.erros.append(
                    LexerError("Caractere '!' só é válido na forma '!='", linha, coluna)
                )
                self.tokens.append(Token(TokenType.ERRO, "!", linha, coluna))
            return

        #  Relacionais '<' e '<='
        if c == "<":
            if self._casar("="):
                self.tokens.append(Token(TokenType.OP_RELACIONAL, "<=", linha, coluna))
            else:
                self.tokens.append(Token(TokenType.OP_RELACIONAL, "<", linha, coluna))
            return

        #  Relacionais '>' e '>='
        if c == ">":
            if self._casar("="):
                self.tokens.append(Token(TokenType.OP_RELACIONAL, ">=", linha, coluna))
            else:
                self.tokens.append(Token(TokenType.OP_RELACIONAL, ">", linha, coluna))
            return

        #  Operadores aritméticos (agrupados por precedência)
        if c in ("+", "-"):
            self.tokens.append(Token(TokenType.OP_ADITIVO, c, linha, coluna))
            return

        if c in ("*", "/", "%"):
            self.tokens.append(Token(TokenType.OP_MULTIPLICATIVO, c, linha, coluna))
            return

        if c == "^":
            self.tokens.append(Token(TokenType.OP_POTENCIA, c, linha, coluna))
            return

        #  Delimitadores e pontuação
        delimitadores = {
            "(": TokenType.PAREN_ESQ,
            ")": TokenType.PAREN_DIR,
            "{": TokenType.CHAVE_ESQ,
            "}": TokenType.CHAVE_DIR,
            ";": TokenType.PONTO_VIRGULA,
            ",": TokenType.VIRGULA,
            ":": TokenType.DOIS_PONTOS,
        }
        if c in delimitadores:
            self.tokens.append(Token(delimitadores[c], c, linha, coluna))
            return

        #  Caractere não reconhecido: modo pânico
        # Registra a mensagem, emite um token ERRO para o parser saber
        # que algo apareceu ali (mantém sincronia posicional), e segue.
        self.erros.append(
            LexerError(f"Caractere não reconhecido: {c!r}", linha, coluna)
        )
        self.tokens.append(Token(TokenType.ERRO, c, linha, coluna))

    # Utilitário


def imprimir_tokens(tokens):
    """Imprime a lista de tokens em formato tabular."""
    print(f"{'TIPO':<22} {'LEXEMA':<30} {'POSIÇÃO':<10}")
    print("-" * 64)
    for t in tokens:
        lex = repr(t.lexema) if t.lexema else ""
        print(f"{t.tipo.name:<22} {lex:<30} {t.linha}:{t.coluna}")

"""
Módulo de definição de tokens - Arjanov

São definidos:
1. TokenType(enum): todos os tipos de tokens reconhecidos pela linguagem
2. Token(classe): representa token individual com tipo, lexema e posição
3. KEYWORDS(dict): mapeamento de palavras reservadas

A linguagem Arjanov suporta:
  - Tipos de dados: int, float, str, bool
  - Operadores aritméticos: + - * / % ^
  - Operadores lógicos: AND, OR, XOR, XNOR
  - Operadores relacionais: == != < > <= >=
  - Estruturas: if, else, for, while, switch, case
  - Funções: func, return
  - E/S: input, puts
  - Literais: inteiros, decimais, strings (entre aspas simples), booleanos (true, false)

  Os operadores são agrupados por nível de precedência (do menor para o maior):
      Nível 1 - OP_OR:              OR
      Nível 2 - OP_XOR:             XOR, XNOR
      Nível 3 - OP_AND:             AND
      Nível 4 - OP_RELACIONAL:      ==  !=  <  >  <=  >=
      Nível 5 - OP_ADITIVO:         +  -
      Nível 6 - OP_MULTIPLICATIVO:  *  /  %
      Nível 7 - OP_POTENCIA:        ^

  O operador específico dentro de cada grupo é identificado pelo lexema.
"""

from enum import Enum, auto


class TokenType(Enum):
    """Enumeração de todos os tipos de token reconhecidos"""

    # Literais e identificadores
    INTEIRO = auto()
    DECIMAL = auto()
    STRING = auto()

    IDENTIFICADOR = auto()

    # Palavras reservadas
    INT = auto()
    FLOAT = auto()
    STR = auto()
    BOOL = auto()

    # Booleanos
    TRUE = auto()
    FALSE = auto()

    # Estruturas de controle
    IF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    SWITCH = auto()
    CASE = auto()

    # Funções
    FUNC = auto()
    MAIN = auto()
    RETURN = auto()

    # Entrada e saída
    INPUT = auto()
    PUTS = auto()

    # Operadores
    OP_OR = auto()  # OR                   (precedência 1 - menor)
    OP_XOR = auto()  # XOR, XNOR            (precedência 2)
    OP_AND = auto()  # AND                  (precedência 3)
    OP_RELACIONAL = auto()  # ==  !=  <  >  <=  >= (precedência 4)
    OP_ADITIVO = auto()  # +  -                 (precedência 5)
    OP_MULTIPLICATIVO = auto()  # *  /  %              (precedência 6)
    OP_POTENCIA = auto()  # ^                    (precedência 7 - maior)

    # Atribuição
    ATRIBUICAO = auto()

    # Delimitadores / Pontuação
    PAREN_ESQ = auto()
    PAREN_DIR = auto()
    CHAVE_ESQ = auto()
    CHAVE_DIR = auto()
    PONTO_VIRGULA = auto()
    VIRGULA = auto()
    DOIS_PONTOS = auto()

    # Especiais
    EOF = auto()
    ERRO = auto()


KEYWORDS = {
    # Tipos de dados
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "str": TokenType.STR,
    "bool": TokenType.BOOL,
    # Valores booleanos
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    # Estruturas de controle
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "switch": TokenType.SWITCH,
    "case": TokenType.CASE,
    # Funções
    "func": TokenType.FUNC,
    "main": TokenType.MAIN,
    "return": TokenType.RETURN,
    # Entrada e saída
    "input": TokenType.INPUT,
    "puts": TokenType.PUTS,
    # Operadores lógicos (escritos em maiúsculas no código-fonte)
    "AND": TokenType.OP_AND,
    "OR": TokenType.OP_OR,
    "XOR": TokenType.OP_XOR,
    "XNOR": TokenType.OP_XOR,
}


class Token:
    """
    Representa um token individual reconhecido pelo analisador.

    Cada token carrega quatro informações:
    1. tipo (TokenType): classe/categoria do token
    2. lexema (str): sequência exata de caracteres que originou o token
    3. linha (int): número da linha do código-fonte em que o token aparece (mensagens de erro)
    4. coluna (int): número da coluna em que token começa
    """

    def __init__(self, tipo: TokenType, lexema: str, linha: int, coluna: int):
        # Cria novo token

        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna

    def __repr__(self) -> str:
        # Representação de token para depuração
        return f"Token({self.tipo.name}, '{self.lexema}', {self.linha}:{self.coluna})"

    def __eq__(self, other) -> bool:
        # Compara dois tokens por tipo e lexema (para testes)
        if not isinstance(other, Token):
            return False
        return self.tipo == other.tipo and self.lexema == other.lexema


def lookup_keyword(lexema: str) -> TokenType:
    # Consulta se lexema é reservado ou identificador

    return KEYWORDS.get(lexema, TokenType.IDENTIFICADOR)

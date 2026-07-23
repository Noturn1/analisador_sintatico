"""
main.py - Compilador Arjanov (Parte 2): pipeline léxico + sintático

Uso (a partir da pasta do projeto):
    python3 src/main.py <arquivo-fonte>       Analisa o arquivo informado
    python3 src/main.py --demo                Analisa um programa embutido
    python3 src/main.py <arquivo> --acoes     Também imprime o traço shift/reduce
    python3 src/main.py <arquivo> --tokens    Também imprime a tabela de tokens
    python3 src/main.py --help                Exibe esta ajuda

Alternativa: use o atalho `python3 run.py <arquivo>` na raiz do projeto.

Pipeline: arquivo -> Lexer (tokens) -> Parser SLR(1) -> relatório.

Códigos de saída:
    0 : análise sintática concluída sem erros (programa ACEITO)
    1 : foram detectados erros léxicos e/ou sintáticos
    2 : erro de argumentos ou de E/S (arquivo não encontrado etc.)
"""

import sys
from pathlib import Path

from token import Token
from lexer import Lexer, LexerError
from parser import Parser, formatar_arvore
from slr import TabelaSLR


CODIGO_DEMO = """func calcula_media(num1, num2) {
    float media = (num1 + num2) / 2;
    return media;
}

func main() {
    int contador = 0;
    bool ativo = true AND false;
    puts('Media: ');
    input(contador);

    for (int i = 0; i < contador; i = i + 1) {
        puts(i);
    }

    switch (contador) {
        case 0:
            puts('zero');
        case 1:
            puts('um');
    }

    return 0;
}
"""


# Impressão auxiliar


def cabecalho(titulo: str):
    linha = "=" * 72
    print(linha)
    print(titulo)
    print(linha)


def imprimir_tokens(tokens: list[Token]):
    print(f"{'#':>4}  {'TIPO':<22} {'LEXEMA':<30} {'POSIÇÃO':<10}")
    print("-" * 72)
    for i, t in enumerate(tokens, start=1):
        lex = repr(t.lexema) if t.lexema else "''"
        print(f"{i:>4}  {t.tipo.name:<22} {lex:<30} {t.linha}:{t.coluna}")


def imprimir_erros_lexicos(erros: list[LexerError]):
    cabecalho(f"Erros Léxicos: {len(erros)}")
    for e in erros:
        print(f"  Linha {e.linha}, Coluna {e.coluna}: {e.mensagem}")


def imprimir_erros_sintaticos(erros):
    cabecalho(f"Erros Sintáticos: {len(erros)}")
    for e in erros:
        print(f"  Linha {e.linha}, Coluna {e.coluna}: {e.mensagem}")


# Pipeline principal


def analisar(codigo: str, origem: str, mostrar_acoes: bool, mostrar_tokens: bool) -> int:
    # 1. Análise léxica
    lexer = Lexer(codigo)
    tokens = lexer.analisar()

    cabecalho(f"Compilador Arjanov — {origem}")

    if mostrar_tokens:
        imprimir_tokens(tokens)
        print()

    # 2. Análise sintática (SLR(1))
    tabela = TabelaSLR()
    if tabela.conflitos:
        # Não deveria acontecer (a gramática é SLR(1)); avisa se acontecer.
        print("AVISO: a tabela SLR possui conflitos:")
        for c in tabela.conflitos:
            print("  ", c)
        print()

    parser = Parser(tokens, tabela)
    resultado = parser.analisar()

    # 3. Relatório
    if mostrar_acoes:
        cabecalho(f"Traço de Ações (shift/reduce): {len(resultado.acoes)}")
        for passo, acao in enumerate(resultado.acoes, start=1):
            print(f"  {passo:>4}  {acao}")
        print()

    cabecalho("Árvore Sintática")
    if resultado.arvore is not None:
        for linha in formatar_arvore(resultado.arvore):
            print(linha)
    else:
        print("  (não foi possível construir a árvore)")
    print()

    if lexer.erros:
        imprimir_erros_lexicos(lexer.erros)
        print()
    if resultado.erros:
        imprimir_erros_sintaticos(resultado.erros)
        print()

    # 4. Veredito
    total_erros = len(lexer.erros) + len(resultado.erros)
    cabecalho("Resultado")
    if resultado.aceito and total_erros == 0:
        print("  ACEITO — programa sintaticamente válido.")
        print(f"  ({len(resultado.acoes)} ações; sem erros)")
        return 0
    else:
        print("  REJEITADO — foram encontrados erros.")
        print(
            f"  Léxicos: {len(lexer.erros)} | "
            f"Sintáticos: {len(resultado.erros)}"
        )
        if not mostrar_acoes:
            print("  (use --acoes para ver o traço shift/reduce completo)")
        return 1


def mostrar_ajuda():
    print(__doc__)


def main(argv: list[str]) -> int:
    args = argv[1:]

    if not args or args[0] in ("-h", "--help"):
        mostrar_ajuda()
        return 0 if args else 2

    mostrar_acoes = "--acoes" in args
    mostrar_tokens = "--tokens" in args
    posicionais = [a for a in args if not a.startswith("--")]

    if "--demo" in args:
        return analisar(CODIGO_DEMO, "<demo embutido>", mostrar_acoes, mostrar_tokens)

    if not posicionais:
        print("Erro: informe um arquivo-fonte ou use --demo.", file=sys.stderr)
        return 2

    caminho = Path(posicionais[0])
    if not caminho.exists():
        print(f"Erro: arquivo '{caminho}' não encontrado.", file=sys.stderr)
        return 2
    if not caminho.is_file():
        print(f"Erro: '{caminho}' não é um arquivo regular.", file=sys.stderr)
        return 2

    try:
        codigo = caminho.read_text(encoding="latin-1")
    except OSError as e:
        print(f"Erro ao ler '{caminho}': {e}", file=sys.stderr)
        return 2

    return analisar(codigo, str(caminho), mostrar_acoes, mostrar_tokens)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

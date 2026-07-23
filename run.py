#!/usr/bin/env python3
"""
run.py - Atalho para executar o compilador a partir da raiz do projeto.

Uso:
    python3 run.py exemplos/ExemploArjanov.arj
    python3 run.py exemplos/erros.arj --acoes
    python3 run.py --demo

Delega para src/main.py. Insere `src/` no início do sys.path para que o
`src/token.py` local tenha prioridade sobre o módulo `token` da biblioteca
padrão do Python (mesmo requisito do léxico da Parte 1).
"""

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, _SRC)

from main import main  # noqa: E402  (import após ajuste de sys.path)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

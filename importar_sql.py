import sqlite3
import sys
from contextlib import closing
from pathlib import Path

BANCO = Path(__file__).with_name("marketplace.db")

if len(sys.argv) != 2:
    sys.exit("Uso: python importar_sql.py produtos_para_o_site.txt")

texto = Path(sys.argv[1]).read_text(encoding="utf-8-sig")

try:
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.executescript(texto)
        total = conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
except sqlite3.OperationalError as erro:
    sys.exit(f"Erro: {erro}. Rode o app uma vez (python app.py) para criar a tabela.")

print(f"Importado! A tabela produtos tem {total} produto(s).")
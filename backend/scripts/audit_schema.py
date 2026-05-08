import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

DB_PATH = BASE_DIR / "backend.db"

def inspect_db():
    """_summary_: inspeciona o banco de dados SQLite, listando as tabelas, colunas, tipos de dados, chaves primárias, chaves estrangeiras e índices, além de contar o número de registros em cada tabela, para fornecer uma visão geral da estrutura do banco e ajudar na auditoria do schema
    """
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"=== DATABASE SCHEMA ===")
    print(f"Database: {DB_PATH}")
    print(f"Tables found: {len(tables)}")
    print()
    
    for table_name in tables:
        table = table_name[0]
        print(f"TABLE: {table}")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        print(f"  Rows: {row_count}")
        
        print(f"  Columns:")
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            pk_marker = " [PK]" if pk else ""
            nullable = "" if notnull else " [NULLABLE]"
            print(f"    - {name}: {type_}{nullable}{pk_marker}")
        
        # Get constraints
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            print(f"  Foreign Keys:")
            for fk in fks:
                print(f"    - {fk}")
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        if indexes:
            print(f"  Indexes:")
            for idx in indexes:
                print(f"    - {idx}")
        
        print()
    
    conn.close()

if __name__ == "__main__":
    inspect_db()

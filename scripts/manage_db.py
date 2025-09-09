"""
Scripts utilitários para gerenciamento do banco de dados.
"""
import os
import subprocess
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(command: str, description: str):
    """Executa um comando e mostra o resultado."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} concluído!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {description}: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def create_migration(message: str = "Auto migration"):
    """Cria uma nova migração."""
    command = f'alembic revision --autogenerate -m "{message}"'
    return run_command(command, f"Criando migração: {message}")

def upgrade_database(revision: str = "head"):
    """Aplica migrações pendentes."""
    command = f"alembic upgrade {revision}"
    return run_command(command, f"Aplicando migrações até {revision}")

def downgrade_database(revision: str = "-1"):
    """Reverte migrações."""
    command = f"alembic downgrade {revision}"
    return run_command(command, f"Revertendo migração: {revision}")

def show_status():
    """Mostra o status das migrações."""
    command = "alembic current"
    return run_command(command, "Verificando status das migrações")

def show_history():
    """Mostra o histórico de migrações."""
    command = "alembic history"
    return run_command(command, "Mostrando histórico de migrações")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python manage_db.py <comando> [argumentos]")
        print("Comandos disponíveis:")
        print("  migrate [mensagem]  - Criar nova migração")
        print("  upgrade [revisão]   - Aplicar migrações")
        print("  downgrade [revisão] - Reverter migrações")
        print("  status              - Ver status atual")
        print("  history             - Ver histórico")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "migrate":
        message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
        create_migration(message)
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade_database(revision)
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        downgrade_database(revision)
    elif command == "status":
        show_status()
    elif command == "history":
        show_history()
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

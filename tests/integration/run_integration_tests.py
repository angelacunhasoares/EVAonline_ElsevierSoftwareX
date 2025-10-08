"""
Script para executar testes de integração de forma conveniente.

Uso:
    python tests/integration/run_integration_tests.py
    python tests/integration/run_integration_tests.py --quick
    python tests/integration/run_integration_tests.py --verbose
"""

import subprocess
import sys
from pathlib import Path


def run_tests(quick: bool = False, verbose: bool = False):
    """
    Executa os testes de integração.
    
    Args:
        quick: Se True, executa apenas testes rápidos
        verbose: Se True, mostra output detalhado
    """
    # Caminho para o diretório de testes
    test_dir = Path(__file__).parent
    test_file = test_dir / "test_infrastructure_integration.py"
    
    # Construir comando pytest
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file)
    ]
    
    # Adicionar opções
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    # Filtros de teste
    if quick:
        # Apenas testes de conectividade e cache
        cmd.extend([
            "-k",
            "TestConnectivity or TestRedisCache"
        ])
        print("🚀 Executando testes RÁPIDOS de integração...")
    else:
        print("🚀 Executando TODOS os testes de integração...")
    
    print(f"📝 Comando: {' '.join(cmd)}\n")
    
    # Executar testes
    try:
        result = subprocess.run(cmd, cwd=test_dir.parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
        return 1
    except Exception as e:
        print(f"\n❌ Erro ao executar testes: {e}")
        return 1


def main():
    """Ponto de entrada do script."""
    # Parse argumentos simples
    quick = "--quick" in sys.argv or "-q" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    # Banner
    print("="*70)
    print("🧪 TESTES DE INTEGRAÇÃO - EVAonline Infrastructure")
    print("="*70)
    print()
    
    # Verificar pré-requisitos
    print("📋 Verificando pré-requisitos...")
    
    # Verificar se pytest está instalado
    try:
        import pytest
        print(f"   ✅ pytest {pytest.__version__}")
    except ImportError:
        print("   ❌ pytest não encontrado")
        print("   💡 Instale com: pip install pytest")
        return 1
    
    # Verificar Redis (tentativa)
    try:
        import redis
        print(f"   ✅ redis-py instalado")
    except ImportError:
        print("   ⚠️  redis-py não encontrado (alguns testes podem falhar)")
    
    # Verificar SQLAlchemy
    try:
        import sqlalchemy
        print(f"   ✅ sqlalchemy {sqlalchemy.__version__}")
    except ImportError:
        print("   ⚠️  sqlalchemy não encontrado")
    
    print()
    
    # Executar testes
    exit_code = run_tests(quick=quick, verbose=verbose)
    
    # Resultado final
    print()
    print("="*70)
    if exit_code == 0:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("="*70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

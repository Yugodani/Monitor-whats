import os
from pathlib import Path

print("🔍 Diagnóstico de ambiente")
print("=" * 50)

# Verificar diretório atual
print(f"📁 Diretório atual: {Path.cwd()}")

# Verificar se .env existe
env_file = Path('.env')
if env_file.exists():
    print(f"✅ Arquivo .env encontrado")
    print(f"📄 Conteúdo do .env:")
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key = line.split('=')[0].strip()
                print(f"   - {key}=***")
else:
    print(f"❌ Arquivo .env NÃO encontrado em {Path.cwd()}")
    print(f"   Crie o arquivo .env neste diretório")

# Tentar ler com python-decouple
try:
    from decouple import config
    secret = config('SECRET_KEY', default=None)
    if secret:
        print(f"✅ python-decouple: SECRET_KEY encontrada")
    else:
        print(f"❌ python-decouple: SECRET_KEY não encontrada")
except Exception as e:
    print(f"❌ Erro ao usar python-decouple: {e}")

# Tentar ler com os.environ
secret_env = os.environ.get('SECRET_KEY')
if secret_env:
    print(f"✅ os.environ: SECRET_KEY encontrada")
else:
    print(f"❌ os.environ: SECRET_KEY não encontrada")

# Tentar ler manualmente
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SECRET_KEY'):
                print(f"✅ Leitura manual: SECRET_KEY encontrada no .env")
                break
except:
    pass

print("=" * 50)
print("\n💡 Soluções:")
print("1. Certifique-se que o arquivo .env está na raiz do projeto")
print("2. Verifique se o formato está correto: SECRET_KEY=valor (sem espaços)")
print("3. Execute: pip install python-decouple")
print("4. Reinicie o terminal/IDE")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para demonstrar a nova funcionalidade de divisão de arquivos SQL
"""

import os
from pathlib import Path

def testar_divisao_sql():
    """
    Testa a nova funcionalidade de divisão de arquivos SQL
    """
    
    print("🧪 TESTE DA NOVA FUNCIONALIDADE DE DIVISÃO SQL")
    print("=" * 60)
    
    # Verificar se existem arquivos CSV para testar
    pasta_csv_setor = Path("dados_com_geometria_setor_csv")
    pasta_csv_municipal = Path("dados_com_geometria_csv")
    
    if not pasta_csv_setor.exists():
        print(f"❌ Pasta não encontrada: {pasta_csv_setor}")
        return
    
    # Encontrar um arquivo para testar
    arquivos_csv = list(pasta_csv_setor.glob("*_com_geometria.csv"))
    if not arquivos_csv:
        print(f"❌ Nenhum arquivo CSV encontrado em {pasta_csv_setor}")
        return
    
    arquivo_teste = arquivos_csv[0]
    print(f"📁 Arquivo de teste: {arquivo_teste.name}")
    
    # Importar e testar a função
    try:
        from csv_para_sql_setor import csv_para_sql_setor_arquivo
        
        print(f"\n🔧 Testando com 500 registros por lote...")
        resultado = csv_para_sql_setor_arquivo(
            str(arquivo_teste), 
            pasta_saida="teste_sql_dividido",
            registros_por_lote=500
        )
        
        if resultado:
            print(f"\n✅ Teste concluído com sucesso!")
            
            # Verificar arquivos gerados
            pasta_teste = Path("teste_sql_dividido")
            if pasta_teste.exists():
                arquivos_gerados = list(pasta_teste.glob("*.sql"))
                print(f"\n📋 Arquivos gerados:")
                for arquivo in arquivos_gerados:
                    tamanho_mb = arquivo.stat().st_size / 1024 / 1024
                    print(f"  - {arquivo.name} ({tamanho_mb:.1f} MB)")
                
                # Limpar arquivos de teste
                print(f"\n🧹 Limpando arquivos de teste...")
                for arquivo in arquivos_gerados:
                    arquivo.unlink()
                pasta_teste.rmdir()
                print(f"✅ Limpeza concluída!")
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

def mostrar_instrucoes():
    """
    Mostra instruções de uso da nova funcionalidade
    """
    
    print("\n📖 INSTRUÇÕES DE USO")
    print("=" * 60)
    
    print("""
🎯 NOVA FUNCIONALIDADE: DIVISÃO DE ARQUIVOS SQL

✅ PROBLEMA RESOLVIDO:
- Arquivos SQL muito grandes demoravam mais de 5 minutos para inserir
- Agora cada arquivo é dividido em duas partes para melhor performance

📁 ESTRUTURA DOS ARQUIVOS GERADOS:
- arquivo_parte1.sql: CREATE TABLE + primeiros registros (padrão: 1000)
- arquivo_parte2.sql: Registros restantes

⚡ BENEFÍCIOS:
- Primeira parte: Cria tabela e insere primeiros registros rapidamente
- Segunda parte: Insere o restante dos dados
- Melhor gerenciamento de memória e transações
- Redução significativa no tempo de inserção

🔧 COMO USAR:

1. Para setores (padrão: 1000 registros por lote):
   python csv_para_sql_setor.py

2. Para municípios (padrão: 1000 registros por lote):
   python csv_para_sql_municipal.py

3. Personalizar número de registros por lote:
   python csv_para_sql_setor.py --registros-por-lote 500

4. Processar arquivo específico:
   python csv_para_sql_setor.py --arquivo dados_com_geometria_setor_csv/arquivo.csv --registros-por-lote 2000

📊 EXEMPLO DE SAÍDA:
✅ Arquivo SQL parte 1 gerado: geodata_icv_pcv_pop_psi_por_setor_2016_parte1.sql
📊 Registros na parte 1: 1000
📋 Tamanho do arquivo: 2.3 MB

✅ Arquivo SQL parte 2 gerado: geodata_icv_pcv_pop_psi_por_setor_2016_parte2.sql
📊 Registros na parte 2: 847
📋 Tamanho do arquivo: 1.9 MB

🚀 ORDEM DE EXECUÇÃO:
1. Execute primeiro o arquivo _parte1.sql
2. Depois execute o arquivo _parte2.sql
3. Ambos os arquivos devem ser executados no mesmo banco de dados

💡 DICAS:
- Para arquivos pequenos (< 1000 registros), apenas a parte 1 será gerada
- Ajuste o --registros-por-lote conforme a capacidade do seu servidor
- Valores menores = arquivos menores = inserção mais rápida
- Valores maiores = menos arquivos = menos gerenciamento
""")

if __name__ == "__main__":
    testar_divisao_sql()
    mostrar_instrucoes()

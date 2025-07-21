#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para converter arquivos CSV de setores com geometria para formato SQL
Inclui AddGeometryColumn para a coluna de geometria
Geometria em formato WKB (Well-Known Binary)
"""

import pandas as pd
import os
from pathlib import Path
import re
import argparse

def detectar_tipos_colunas(df):
    """
    Detecta automaticamente os tipos SQL para cada coluna
    
    Args:
        df (DataFrame): DataFrame pandas
        
    Returns:
        dict: Dicionário com nome da coluna e tipo SQL
    """
    tipos_sql = {}
    
    # Lista de códigos do IBGE que devem ser VARCHAR
    codigos_ibge = ['cd_mun', 'nm_mun', 'cd_setor', 'cd_rgint', 'nm_rgint', 'cd_rgi', 'nm_rgi', 'cd_uf', 'nm_uf', 'sigla_uf']
    
    for col in df.columns:
        if col == 'geometry':
            continue
            
        # Verificar se é um código do IBGE
        if col in codigos_ibge:
            tipos_sql[col] = 'VARCHAR'
        # Verificar se é numérico
        elif df[col].dtype in ['int64', 'int32']:
            tipos_sql[col] = 'INTEGER'
        elif df[col].dtype in ['float64', 'float32']:
            tipos_sql[col] = 'NUMERIC'
        elif df[col].dtype == 'object':
            # Verificar se é string ou pode ser convertido para número
            try:
                pd.to_numeric(df[col], errors='raise')
                tipos_sql[col] = 'NUMERIC'
            except:
                # Verificar tamanho máximo da string
                max_length = df[col].astype(str).str.len().max()
                if pd.isna(max_length) or max_length <= 255:
                    tipos_sql[col] = 'VARCHAR(255)'
                else:
                    tipos_sql[col] = f'VARCHAR({min(max_length * 2, 1000)})'
        else:
            tipos_sql[col] = 'VARCHAR(255)'
    
    return tipos_sql

def csv_para_sql_setor_arquivo(arquivo_csv, pasta_saida="dados_sql_setor", nome_tabela=None, srid=31983, tipo_geometria='MULTIPOLYGON'):
    """
    Converte um arquivo CSV de setores com geometria para formato SQL
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV
        pasta_saida (str): Pasta onde salvar o arquivo SQL
        nome_tabela (str): Nome da tabela (se None, usa o nome do arquivo)
        srid (int): SRID para a geometria (padrão: 31983)
        tipo_geometria (str): Tipo de geometria (padrão: MULTIPOLYGON)
    """
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo_csv):
        print(f"❌ Arquivo CSV não encontrado: {arquivo_csv}")
        return False
    
    # Criar pasta de saída
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(exist_ok=True)
    
    print(f"Processando arquivo: {arquivo_csv}")
    
    # Carregar dados CSV
    df = pd.read_csv(arquivo_csv)
    
    # Verificar se tem coluna de geometria
    if 'geometry' not in df.columns:
        print(f"❌ Coluna 'geometry' não encontrada em {arquivo_csv}")
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        return False
    
    # Gerar nome da tabela se não fornecido
    if nome_tabela is None:
        nome_arquivo = Path(arquivo_csv).stem
        # Remover sufixos comuns
        nome_arquivo = re.sub(r'_com_geometria$', '', nome_arquivo)
        nome_tabela = nome_arquivo.replace('-', '_').replace(' ', '_')
    
    # Gerar nome do arquivo SQL
    arquivo_sql = pasta_saida / f"{nome_tabela}.sql"
    
    # Detectar tipos de colunas automaticamente
    tipos_colunas = detectar_tipos_colunas(df)
    
    # Criar conteúdo SQL
    sql_content = []
    
    # Adicionar cabeçalho
    sql_content.append("-- =============================================")
    sql_content.append(f"-- Tabela: {nome_tabela}")
    sql_content.append(f"-- Arquivo fonte: {Path(arquivo_csv).name}")
    sql_content.append(f"-- Total de registros: {len(df)}")
    sql_content.append(f"-- SRID: {srid}")
    sql_content.append(f"-- Tipo geometria: {tipo_geometria}")
    sql_content.append("-- Geometria: WKB (Well-Known Binary)")
    sql_content.append("-- =============================================")
    sql_content.append("")
    
    # Criar tabela
    sql_content.append(f"CREATE TABLE public.{nome_tabela} (")
    sql_content.append("    id SERIAL PRIMARY KEY,")
    
    # Adicionar colunas (exceto geometry)
    colunas_sql = []
    colunas_para_adicionar = [col for col in df.columns if col != 'geometry']
    
    for i, col in enumerate(colunas_para_adicionar):
        tipo_sql = tipos_colunas.get(col, 'VARCHAR(255)')
        # Adicionar vírgula apenas se não for a última coluna
        if i < len(colunas_para_adicionar) - 1:
            colunas_sql.append(f"    {col} {tipo_sql},")
        else:
            colunas_sql.append(f"    {col} {tipo_sql}")
    
    sql_content.extend(colunas_sql)
    sql_content.append(");")
    sql_content.append("")
    
    # Adicionar coluna de geometria
    sql_content.append(f"SELECT AddGeometryColumn('public','{nome_tabela}','wkb_geometry',{srid},'{tipo_geometria}',2);")
    sql_content.append("")
    
    # Inserir dados
    sql_content.append("-- Inserir dados")
    sql_content.append(f"INSERT INTO public.{nome_tabela} (")
    
    # Lista de colunas para INSERT
    colunas_insert = [col for col in df.columns if col != 'geometry']
    colunas_insert.append('wkb_geometry')
    sql_content.append("    " + ", ".join(colunas_insert))
    sql_content.append(") VALUES")
    
    # Processar cada linha
    valores = []
    for idx, row in df.iterrows():
        # Preparar valores para cada coluna
        linha_valores = []
        
        for col in df.columns:
            if col != 'geometry':
                valor = row[col]
                
                # Tratar valores nulos
                if pd.isna(valor):
                    linha_valores.append("NULL")
                # Tratar strings
                elif isinstance(valor, str):
                    # Escapar aspas simples
                    valor_escaped = valor.replace("'", "''")
                    linha_valores.append(f"'{valor_escaped}'")
                # Tratar números
                else:
                    linha_valores.append(str(valor))
        
        # Adicionar geometria WKB
        geometria = row['geometry']
        if pd.isna(geometria):
            linha_valores.append("NULL")
        else:
            # Converter WKB hex para formato PostGIS e garantir MULTIPOLYGON
            linha_valores.append(f"ST_Multi(ST_GeomFromWKB('\\x{geometria}', {srid}))")
        
        valores.append("(" + ", ".join(linha_valores) + ")")
        
        # Adicionar quebra de linha a cada 100 registros para legibilidade
        if (idx + 1) % 100 == 0:
            valores.append("")
    
    sql_content.append(",\n".join(valores))
    sql_content.append(";")
    sql_content.append("")
    
    # Adicionar comentários finais
    sql_content.append("-- =============================================")
    sql_content.append(f"-- Fim da inserção para {nome_tabela}")
    sql_content.append(f"-- Total de registros inseridos: {len(df)}")
    sql_content.append("-- Geometria em formato WKB")
    sql_content.append("-- =============================================")
    
    # Salvar arquivo SQL
    with open(arquivo_sql, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_content))
    
    print(f"✅ Arquivo SQL gerado: {arquivo_sql}")
    print(f"📊 Registros processados: {len(df)}")
    print(f"📋 Tamanho do arquivo: {arquivo_sql.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"🔧 Formato geometria: WKB")
    print(f"🗂️  Colunas detectadas: {len(df.columns)}")
    
    return True

def csv_para_sql_setor_pasta(pasta_csv="dados_com_geometria_setor_csv", padrao="*_com_geometria.csv", pasta_saida="dados_sql_setor", srid=31983, tipo_geometria='MULTIPOLYGON'):
    """
    Converte todos os arquivos CSV de setores com geometria em uma pasta para formato SQL
    
    Args:
        pasta_csv (str): Pasta com os arquivos CSV
        padrao (str): Padrão para encontrar arquivos CSV
        pasta_saida (str): Pasta onde salvar os arquivos SQL
        srid (int): SRID para a geometria
        tipo_geometria (str): Tipo de geometria
    """
    
    pasta_csv = Path(pasta_csv)
    if not pasta_csv.exists():
        print(f"❌ Pasta não encontrada: {pasta_csv}")
        return
    
    # Listar todos os arquivos CSV que seguem o padrão
    arquivos_csv = list(pasta_csv.glob(padrao))
    arquivos_csv.sort()
    
    if not arquivos_csv:
        print(f"❌ Nenhum arquivo CSV encontrado com o padrão: {padrao}")
        return
    
    print(f"Encontrados {len(arquivos_csv)} arquivos para converter:")
    for arquivo in arquivos_csv:
        print(f"  - {arquivo.name}")
    
    # Processar cada arquivo
    sucessos = 0
    for arquivo_csv in arquivos_csv:
        print(f"\n{'='*60}")
        if csv_para_sql_setor_arquivo(str(arquivo_csv), pasta_saida, srid=srid, tipo_geometria=tipo_geometria):
            sucessos += 1
    
    print(f"\n🎉 Conversão concluída!")
    print(f"📁 Arquivos SQL gerados na pasta: {pasta_saida}")
    print(f"📋 Total de arquivos processados: {len(arquivos_csv)}")
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {len(arquivos_csv) - sucessos}")

def main():
    """
    Função principal que permite usar o script de diferentes formas
    """
    parser = argparse.ArgumentParser(description='Converter arquivos CSV de setores com geometria para SQL')
    parser.add_argument('--arquivo', type=str, help='Arquivo CSV específico para processar')
    parser.add_argument('--pasta-csv', type=str, default="dados_com_geometria_setor_csv",
                       help='Pasta com os arquivos CSV (padrão: dados_com_geometria_setor_csv)')
    parser.add_argument('--padrao', type=str, default="*_com_geometria.csv",
                       help='Padrão para encontrar arquivos CSV (padrão: *_com_geometria.csv)')
    parser.add_argument('--pasta-saida', type=str, default="dados_sql_setor",
                       help='Pasta onde salvar os arquivos SQL (padrão: dados_sql_setor)')
    parser.add_argument('--nome-tabela', type=str, help='Nome da tabela (se não fornecido, usa o nome do arquivo)')
    parser.add_argument('--srid', type=int, default=31983, help='SRID para a geometria (padrão: 31983)')
    parser.add_argument('--tipo-geometria', type=str, default='MULTIPOLYGON',
                       help='Tipo de geometria (padrão: MULTIPOLYGON)')
    
    args = parser.parse_args()
    
    if args.arquivo:
        # Processar arquivo específico
        csv_para_sql_setor_arquivo(args.arquivo, args.pasta_saida, args.nome_tabela, args.srid, args.tipo_geometria)
    else:
        # Processar todos os arquivos que seguem o padrão
        csv_para_sql_setor_pasta(args.pasta_csv, args.padrao, args.pasta_saida, args.srid, args.tipo_geometria)

if __name__ == "__main__":
    # Se não houver argumentos, usar o comportamento padrão
    import sys
    if len(sys.argv) == 1:
        csv_para_sql_setor_pasta()
    else:
        main() 
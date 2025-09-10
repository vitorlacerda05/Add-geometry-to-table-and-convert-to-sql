#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script genérico para converter arquivos CSV com geometria para formato SQL
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
    
    # Lista de colunas que devem ser FLOAT8 (mais leve para valores com 2 casas decimais)
    colunas_float8 = ['pcv', 'psi', 'icv', 'pop']
    
    for col in df.columns:
        if col == 'geometry':
            continue
            
        # Verificar se é um código do IBGE
        if col in codigos_ibge:
            tipos_sql[col] = 'VARCHAR'
        # Verificar se é uma das colunas que devem ser FLOAT8
        elif col in colunas_float8:
            tipos_sql[col] = 'FLOAT8'
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

def csv_para_sql_arquivo(arquivo_csv, pasta_saida="dados_sql", nome_tabela=None, srid=31983, tipo_geometria='MULTIPOLYGON', registros_por_lote=1000):
    """
    Converte um arquivo CSV com geometria para formato SQL
    Divide em dois arquivos para melhor performance de inserção
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV
        pasta_saida (str): Pasta onde salvar o arquivo SQL
        nome_tabela (str): Nome da tabela (se None, usa o nome do arquivo)
        srid (int): SRID para a geometria (padrão: 31983)
        tipo_geometria (str): Tipo de geometria (padrão: MULTIPOLYGON)
        registros_por_lote (int): Número de registros por lote no primeiro arquivo
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
    
    # Gerar nomes dos arquivos SQL
    arquivo_sql_1 = pasta_saida / f"{nome_tabela}_parte1.sql"
    arquivo_sql_2 = pasta_saida / f"{nome_tabela}_parte2.sql"
    
    # Detectar tipos de colunas automaticamente
    tipos_colunas = detectar_tipos_colunas(df)
    
    # Calcular divisão dos dados
    total_registros = len(df)
    registros_primeira_parte = min(registros_por_lote, total_registros)
    registros_segunda_parte = total_registros - registros_primeira_parte
    
    print(f"📊 Total de registros: {total_registros}")
    print(f"📁 Primeira parte: {registros_primeira_parte} registros")
    print(f"📁 Segunda parte: {registros_segunda_parte} registros")
    
    # ============================================
    # CRIAR PRIMEIRO ARQUIVO (CREATE TABLE + primeiros INSERTs)
    # ============================================
    
    sql_content_1 = []
    
    # Adicionar cabeçalho
    sql_content_1.append("-- =============================================")
    sql_content_1.append(f"-- Tabela: {nome_tabela}")
    sql_content_1.append(f"-- Arquivo fonte: {Path(arquivo_csv).name}")
    sql_content_1.append(f"-- PARTE 1: CREATE TABLE + primeiros {registros_primeira_parte} registros")
    sql_content_1.append(f"-- Total de registros: {total_registros}")
    sql_content_1.append(f"-- SRID: {srid}")
    sql_content_1.append(f"-- Tipo geometria: {tipo_geometria}")
    sql_content_1.append("-- Geometria: WKB (Well-Known Binary)")
    sql_content_1.append("-- =============================================")
    sql_content_1.append("")
    
    # Criar tabela
    sql_content_1.append(f"CREATE TABLE public.{nome_tabela} (")
    sql_content_1.append("    id SERIAL PRIMARY KEY,")
    
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
    
    sql_content_1.extend(colunas_sql)
    sql_content_1.append(");")
    sql_content_1.append("")
    
    # Adicionar coluna de geometria
    sql_content_1.append(f"SELECT AddGeometryColumn('public','{nome_tabela}','wkb_geometry',{srid},'{tipo_geometria}',2);")
    sql_content_1.append("")
    
    # Inserir primeiros dados
    if registros_primeira_parte > 0:
        sql_content_1.append("-- Inserir primeiros dados")
        sql_content_1.append(f"INSERT INTO public.{nome_tabela} (")
        
        # Lista de colunas para INSERT
        colunas_insert = [col for col in df.columns if col != 'geometry']
        colunas_insert.append('wkb_geometry')
        sql_content_1.append("    " + ", ".join(colunas_insert))
        sql_content_1.append(") VALUES")
        
        # Processar primeiras linhas
        valores = []
        for idx in range(registros_primeira_parte):
            row = df.iloc[idx]
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
        
        sql_content_1.append(",\n".join(valores))
        sql_content_1.append(";")
        sql_content_1.append("")
    
    # Adicionar comentários finais
    sql_content_1.append("-- =============================================")
    sql_content_1.append(f"-- Fim da PARTE 1 para {nome_tabela}")
    sql_content_1.append(f"-- Registros inseridos: {registros_primeira_parte}")
    sql_content_1.append("-- Execute o arquivo parte2.sql para inserir os demais registros")
    sql_content_1.append("-- =============================================")
    
    # Salvar primeiro arquivo SQL
    with open(arquivo_sql_1, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_content_1))
    
    print(f"✅ Arquivo SQL parte 1 gerado: {arquivo_sql_1}")
    print(f"📊 Registros na parte 1: {registros_primeira_parte}")
    print(f"📋 Tamanho do arquivo: {arquivo_sql_1.stat().st_size / 1024 / 1024:.1f} MB")
    
    # ============================================
    # CRIAR SEGUNDO ARQUIVO (restante dos INSERTs)
    # ============================================
    
    if registros_segunda_parte > 0:
        sql_content_2 = []
        
        # Adicionar cabeçalho
        sql_content_2.append("-- =============================================")
        sql_content_2.append(f"-- Tabela: {nome_tabela}")
        sql_content_2.append(f"-- Arquivo fonte: {Path(arquivo_csv).name}")
        sql_content_2.append(f"-- PARTE 2: {registros_segunda_parte} registros restantes")
        sql_content_2.append(f"-- Total de registros: {total_registros}")
        sql_content_2.append(f"-- SRID: {srid}")
        sql_content_2.append(f"-- Tipo geometria: {tipo_geometria}")
        sql_content_2.append("-- Geometria: WKB (Well-Known Binary)")
        sql_content_2.append("-- IMPORTANTE: Execute a parte 1 primeiro!")
        sql_content_2.append("-- =============================================")
        sql_content_2.append("")
        
        # Inserir dados restantes
        sql_content_2.append("-- Inserir dados restantes")
        sql_content_2.append(f"INSERT INTO public.{nome_tabela} (")
        
        # Lista de colunas para INSERT
        colunas_insert = [col for col in df.columns if col != 'geometry']
        colunas_insert.append('wkb_geometry')
        sql_content_2.append("    " + ", ".join(colunas_insert))
        sql_content_2.append(") VALUES")
        
        # Processar linhas restantes
        valores = []
        for idx in range(registros_primeira_parte, total_registros):
            row = df.iloc[idx]
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
        
        sql_content_2.append(",\n".join(valores))
        sql_content_2.append(";")
        sql_content_2.append("")
        
        # Adicionar comentários finais
        sql_content_2.append("-- =============================================")
        sql_content_2.append(f"-- Fim da PARTE 2 para {nome_tabela}")
        sql_content_2.append(f"-- Registros inseridos: {registros_segunda_parte}")
        sql_content_2.append(f"-- Total final: {total_registros} registros")
        sql_content_2.append("-- Geometria em formato WKB")
        sql_content_2.append("-- =============================================")
        
        # Salvar segundo arquivo SQL
        with open(arquivo_sql_2, 'w', encoding='utf-8') as f:
            f.write("\n".join(sql_content_2))
        
        print(f"✅ Arquivo SQL parte 2 gerado: {arquivo_sql_2}")
        print(f"📊 Registros na parte 2: {registros_segunda_parte}")
        print(f"📋 Tamanho do arquivo: {arquivo_sql_2.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"ℹ️  Não há segunda parte necessária (todos os registros na parte 1)")
    
    print(f"🔧 Formato geometria: WKB")
    print(f"🗂️  Colunas detectadas: {len(df.columns)}")
    
    return True

def csv_para_sql_pasta(pasta_csv="dados_com_geometria_csv", padrao="*_com_geometria.csv", pasta_saida="dados_sql", srid=31983, tipo_geometria='MULTIPOLYGON', registros_por_lote=1000):
    """
    Converte todos os arquivos CSV com geometria em uma pasta para formato SQL
    Divide cada arquivo em duas partes para melhor performance
    
    Args:
        pasta_csv (str): Pasta com os arquivos CSV
        padrao (str): Padrão para encontrar arquivos CSV
        pasta_saida (str): Pasta onde salvar os arquivos SQL
        srid (int): SRID para a geometria
        tipo_geometria (str): Tipo de geometria
        registros_por_lote (int): Número de registros por lote no primeiro arquivo
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
        if csv_para_sql_arquivo(str(arquivo_csv), pasta_saida, srid=srid, tipo_geometria=tipo_geometria, registros_por_lote=registros_por_lote):
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
    parser = argparse.ArgumentParser(description='Converter arquivos CSV com geometria para SQL')
    parser.add_argument('--arquivo', type=str, help='Arquivo CSV específico para processar')
    parser.add_argument('--pasta-csv', type=str, default="dados_com_geometria_csv",
                       help='Pasta com os arquivos CSV (padrão: dados_com_geometria_csv)')
    parser.add_argument('--padrao', type=str, default="*_com_geometria.csv",
                       help='Padrão para encontrar arquivos CSV (padrão: *_com_geometria.csv)')
    parser.add_argument('--pasta-saida', type=str, default="dados_sql",
                       help='Pasta onde salvar os arquivos SQL (padrão: dados_sql)')
    parser.add_argument('--nome-tabela', type=str, help='Nome da tabela (se não fornecido, usa o nome do arquivo)')
    parser.add_argument('--srid', type=int, default=31983, help='SRID para a geometria (padrão: 31983)')
    parser.add_argument('--tipo-geometria', type=str, default='MULTIPOLYGON',
                       help='Tipo de geometria (padrão: MULTIPOLYGON)')
    parser.add_argument('--registros-por-lote', type=int, default=1000,
                       help='Número de registros por lote no primeiro arquivo (padrão: 1000)')
    
    args = parser.parse_args()
    
    if args.arquivo:
        # Processar arquivo específico
        csv_para_sql_arquivo(args.arquivo, args.pasta_saida, args.nome_tabela, args.srid, args.tipo_geometria, args.registros_por_lote)
    else:
        # Processar todos os arquivos que seguem o padrão
        csv_para_sql_pasta(args.pasta_csv, args.padrao, args.pasta_saida, args.srid, args.tipo_geometria, args.registros_por_lote)

if __name__ == "__main__":
    # Se não houver argumentos, usar o comportamento padrão
    import sys
    if len(sys.argv) == 1:
        csv_para_sql_pasta()
    else:
        main() 
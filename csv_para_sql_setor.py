#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para converter arquivos CSV de setores com geometria para formato SQL
Inclui AddGeometryColumn para a coluna de geometria
Geometria em formato WKB (Well-Known Binary)
OTIMIZADO PARA SETORES: Divisão automática baseada no tamanho do arquivo
- Arquivos grandes (>50k): 5k registros por parte (~19 partes para 94k)
- Arquivos médios (>20k): 10k registros por parte
- Arquivos pequenos: tamanho padrão ou único arquivo
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

def csv_para_sql_setor_arquivo(arquivo_csv, pasta_saida="dados_sql_setor", nome_tabela=None, srid=31983, tipo_geometria='MULTIPOLYGON', registros_por_lote=10000):
    """
    Converte um arquivo CSV de setores com geometria para formato SQL
    Divide automaticamente em múltiplas partes para melhor performance de inserção
    Otimizado para arquivos de setores (~94k registros): divisão automática baseada no tamanho
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV
        pasta_saida (str): Pasta onde salvar o arquivo SQL
        nome_tabela (str): Nome da tabela (se None, usa o nome do arquivo)
        srid (int): SRID para a geometria (padrão: 31983)
        tipo_geometria (str): Tipo de geometria (padrão: MULTIPOLYGON)
        registros_por_lote (int): Número de registros por lote (padrão: 10000, ajusta automaticamente para arquivos grandes)
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
    
    # Detectar tipos de colunas automaticamente
    tipos_colunas = detectar_tipos_colunas(df)
    
    # Calcular divisão dos dados
    total_registros = len(df)
    
    # Para arquivos grandes (>50k registros), usar divisão mais agressiva
    if total_registros > 50000:
        registros_por_lote = 5000  # Reduzir para 5k por arquivo
        print(f"⚠️  Arquivo grande detectado ({total_registros} registros). Usando divisão mais agressiva (5k por arquivo)")
    elif total_registros > 20000:
        registros_por_lote = 10000  # Manter 10k por arquivo
    else:
        registros_por_lote = min(registros_por_lote, total_registros)
    
    # Calcular número de partes necessárias
    num_partes = (total_registros + registros_por_lote - 1) // registros_por_lote
    
    print(f"📊 Total de registros: {total_registros}")
    print(f"📁 Registros por parte: {registros_por_lote}")
    print(f"📁 Número de partes: {num_partes}")
    
    # Gerar nomes dos arquivos SQL
    arquivos_sql = []
    for i in range(1, num_partes + 1):
        arquivos_sql.append(pasta_saida / f"{nome_tabela}_parte{i}.sql")
    
    # ============================================
    # CRIAR MÚLTIPLAS PARTES AUTOMATICAMENTE
    # ============================================
    
    # Criar primeira parte com CREATE TABLE
    sql_content_1 = []
    
    # Adicionar cabeçalho
    sql_content_1.append("-- =============================================")
    sql_content_1.append(f"-- Tabela: {nome_tabela}")
    sql_content_1.append(f"-- Arquivo fonte: {Path(arquivo_csv).name}")
    sql_content_1.append(f"-- PARTE 1: CREATE TABLE + primeiros {registros_por_lote} registros")
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
    
    # Processar todas as partes
    for parte in range(1, num_partes + 1):
        inicio = (parte - 1) * registros_por_lote
        fim = min(parte * registros_por_lote, total_registros)
        registros_esta_parte = fim - inicio
        
        print(f"📝 Processando parte {parte}/{num_partes} ({registros_esta_parte} registros)")
        
        # Se for a primeira parte, adicionar os dados à estrutura existente
        if parte == 1:
            sql_content = sql_content_1
            sql_content.append("-- Inserir primeiros dados")
        else:
            # Criar novo conteúdo para as outras partes
            sql_content = []
            
            # Adicionar cabeçalho
            sql_content.append("-- =============================================")
            sql_content.append(f"-- Tabela: {nome_tabela}")
            sql_content.append(f"-- Arquivo fonte: {Path(arquivo_csv).name}")
            sql_content.append(f"-- PARTE {parte}: {registros_esta_parte} registros")
            sql_content.append(f"-- Total de registros: {total_registros}")
            sql_content.append(f"-- SRID: {srid}")
            sql_content.append(f"-- Tipo geometria: {tipo_geometria}")
            sql_content.append("-- Geometria: WKB (Well-Known Binary)")
            sql_content.append("-- IMPORTANTE: Execute as partes anteriores primeiro!")
            sql_content.append("-- =============================================")
            sql_content.append("")
            sql_content.append("-- Inserir dados")
        
        sql_content.append(f"INSERT INTO public.{nome_tabela} (")
        
        # Lista de colunas para INSERT
        colunas_insert = [col for col in df.columns if col != 'geometry']
        colunas_insert.append('wkb_geometry')
        sql_content.append("    " + ", ".join(colunas_insert))
        sql_content.append(") VALUES")
        
        # Processar registros desta parte
        valores = []
        for idx in range(inicio, fim):
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
        
        sql_content.append(",\n".join(valores))
        sql_content.append(";")
        sql_content.append("")
        
        # Adicionar comentários finais
        sql_content.append("-- =============================================")
        sql_content.append(f"-- Fim da PARTE {parte} para {nome_tabela}")
        sql_content.append(f"-- Registros inseridos: {registros_esta_parte}")
        if parte < num_partes:
            sql_content.append(f"-- Execute o arquivo parte{parte + 1}.sql para inserir os demais registros")
        else:
            sql_content.append(f"-- Total final: {total_registros} registros")
        sql_content.append("-- Geometria em formato WKB")
        sql_content.append("-- =============================================")
        
        # Salvar arquivo SQL
        with open(arquivos_sql[parte - 1], 'w', encoding='utf-8') as f:
            f.write("\n".join(sql_content))
        
        tamanho_mb = arquivos_sql[parte - 1].stat().st_size / 1024 / 1024
        print(f"✅ Arquivo SQL parte {parte} gerado: {arquivos_sql[parte - 1].name}")
        print(f"📊 Registros na parte {parte}: {registros_esta_parte}")
        print(f"📋 Tamanho do arquivo: {tamanho_mb:.1f} MB")
    
    print(f"🔧 Formato geometria: WKB")
    print(f"🗂️  Colunas detectadas: {len(df.columns)}")
    print(f"🎉 Total de arquivos gerados: {num_partes}")
    
    return True

def csv_para_sql_setor_pasta(pasta_csv="dados_com_geometria_setor_csv", padrao="*_com_geometria.csv", pasta_saida="dados_sql_setor", srid=31983, tipo_geometria='MULTIPOLYGON', registros_por_lote=10000):
    """
    Converte todos os arquivos CSV de setores com geometria em uma pasta para formato SQL
    Divide automaticamente cada arquivo em múltiplas partes para melhor performance
    Otimizado para arquivos de setores (~94k registros): divisão automática baseada no tamanho
    
    Args:
        pasta_csv (str): Pasta com os arquivos CSV
        padrao (str): Padrão para encontrar arquivos CSV
        pasta_saida (str): Pasta onde salvar os arquivos SQL
        srid (int): SRID para a geometria
        tipo_geometria (str): Tipo de geometria
        registros_por_lote (int): Número de registros por lote (padrão: 10000, ajusta automaticamente para arquivos grandes)
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
        if csv_para_sql_setor_arquivo(str(arquivo_csv), pasta_saida, srid=srid, tipo_geometria=tipo_geometria, registros_por_lote=registros_por_lote):
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
    parser = argparse.ArgumentParser(description='Converter arquivos CSV de setores com geometria para SQL (divisão automática para arquivos grandes)')
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
    parser.add_argument('--registros-por-lote', type=int, default=10000,
                       help='Número de registros por lote (padrão: 10000, ajusta automaticamente para arquivos grandes)')
    
    args = parser.parse_args()
    
    if args.arquivo:
        # Processar arquivo específico
        csv_para_sql_setor_arquivo(args.arquivo, args.pasta_saida, args.nome_tabela, args.srid, args.tipo_geometria, args.registros_por_lote)
    else:
        # Processar todos os arquivos que seguem o padrão
        csv_para_sql_setor_pasta(args.pasta_csv, args.padrao, args.pasta_saida, args.srid, args.tipo_geometria, args.registros_por_lote)

if __name__ == "__main__":
    # Se não houver argumentos, usar o comportamento padrão
    import sys
    if len(sys.argv) == 1:
        csv_para_sql_setor_pasta()
    else:
        main() 
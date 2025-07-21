#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script genérico para adicionar coluna de geometria e colunas adicionais aos dados
Baseado na correspondência do código do município (cd_mun)
Gera apenas arquivos CSV com geometria em formato WKB
"""

import pandas as pd
import geopandas as gpd
import os
from pathlib import Path
from shapely import wkb
import argparse

def adicionar_geometria_arquivo(arquivo_csv, pasta_geometria="dados_comparar", arquivo_geometria="geodata_hidrologia_municipios_2025.gpkg", pasta_saida="dados_com_geometria_csv"):
    """
    Adiciona geometria a um arquivo CSV específico
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV de entrada
        pasta_geometria (str): Pasta onde está o arquivo de geometria
        arquivo_geometria (str): Nome do arquivo de geometria (.gpkg)
        pasta_saida (str): Pasta onde salvar os arquivos de saída
    """
    
    # Criar pasta de saída
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(exist_ok=True)
    
    # Verificar se o arquivo CSV existe
    if not os.path.exists(arquivo_csv):
        print(f"❌ Arquivo CSV não encontrado: {arquivo_csv}")
        return False
    
    # Verificar se o arquivo de geometria existe
    arquivo_geo = Path(pasta_geometria) / arquivo_geometria
    if not arquivo_geo.exists():
        print(f"❌ Arquivo de geometria não encontrado: {arquivo_geo}")
        return False
    
    print(f"Processando arquivo: {arquivo_csv}")
    
    # Carregar dados de geometria
    print("Carregando dados de geometria...")
    geometria_gdf = gpd.read_file(arquivo_geo)
    
    # Selecionar apenas as colunas necessárias e converter geometria para WKB
    colunas_geometria = ['CD_MUN', 'NM_MUN', 'CD_RGI', 'NM_RGI', 'CD_RGINT', 'NM_RGINT', 'CD_UF', 'NM_UF', 'SIGLA_UF', 'geometry']
    geometria_df = geometria_gdf[colunas_geometria].copy()
    
    # Converter geometria para WKB (Well-Known Binary)
    print("Convertendo geometria para formato WKB...")
    geometria_df['geometry_wkb'] = geometria_df['geometry'].apply(lambda geom: geom.wkb_hex if geom is not None else None)
    
    # Remover a coluna geometry original e renomear WKB
    geometria_df = geometria_df.drop('geometry', axis=1)
    geometria_df = geometria_df.rename(columns={'geometry_wkb': 'geometry'})
    
    # Renomear colunas para minúsculas para manter consistência
    geometria_df = geometria_df.rename(columns={
        'CD_MUN': 'cd_mun_geo',
        'NM_MUN': 'nm_mun_geo', 
        'CD_RGI': 'cd_rgi',
        'NM_RGI': 'nm_rgi',
        'CD_RGINT': 'cd_rgint',
        'NM_RGINT': 'nm_rgint',
        'CD_UF': 'cd_uf',
        'NM_UF': 'nm_uf',
        'SIGLA_UF': 'sigla_uf'
    })
    
    # Converter cd_mun_geo para string para garantir compatibilidade no merge
    geometria_df['cd_mun_geo'] = geometria_df['cd_mun_geo'].astype(str)
    
    print(f"Dados de geometria carregados: {len(geometria_df)} registros")
    
    # Carregar dados do CSV
    dados_csv = pd.read_csv(arquivo_csv)
    
    # Verificar se a coluna cd_mun existe
    if 'cd_mun' not in dados_csv.columns:
        print(f"❌ Coluna 'cd_mun' não encontrada em {arquivo_csv}")
        print(f"Colunas disponíveis: {dados_csv.columns.tolist()}")
        return False
    
    # Converter cd_mun para string para garantir compatibilidade
    dados_csv['cd_mun'] = dados_csv['cd_mun'].astype(str)
    
    # Fazer o merge com os dados de geometria
    dados_com_geometria = dados_csv.merge(
        geometria_df, 
        left_on='cd_mun', 
        right_on='cd_mun_geo', 
        how='left'
    )
    
    # Remover colunas duplicadas
    if 'cd_mun_geo' in dados_com_geometria.columns:
        dados_com_geometria = dados_com_geometria.drop('cd_mun_geo', axis=1)
    if 'nm_mun_geo' in dados_com_geometria.columns:
        dados_com_geometria = dados_com_geometria.drop('nm_mun_geo', axis=1)
    
    # Verificar quantos registros foram encontrados
    registros_com_geometria = dados_com_geometria['geometry'].notna().sum()
    total_registros = len(dados_com_geometria)
    
    print(f"✅ Registros processados: {total_registros}")
    print(f"✅ Registros com geometria: {registros_com_geometria}")
    print(f"✅ Taxa de sucesso: {(registros_com_geometria/total_registros)*100:.1f}%")
    
    # Gerar nome do arquivo de saída
    nome_arquivo = Path(arquivo_csv).stem
    arquivo_saida = pasta_saida / f"{nome_arquivo}_com_geometria.csv"
    
    # Salvar arquivo CSV
    dados_com_geometria.to_csv(arquivo_saida, index=False)
    print(f"💾 Arquivo salvo: {arquivo_saida}")
    
    # Mostrar algumas informações sobre as colunas adicionadas
    colunas_adicionadas = ['cd_rgi', 'nm_rgi', 'cd_rgint', 'nm_rgint', 'cd_uf', 'nm_uf', 'sigla_uf', 'geometry']
    colunas_presentes = [col for col in colunas_adicionadas if col in dados_com_geometria.columns]
    print(f"📊 Colunas adicionadas: {', '.join(colunas_presentes)}")
    
    return True

def adicionar_geometria_pasta(padrao="geodata_icv-pcv-pop-psi_por_municipio_*.csv", pasta_geometria="dados_comparar", arquivo_geometria="geodata_hidrologia_municipios_2025.gpkg", pasta_saida="dados_com_geometria_csv"):
    """
    Adiciona geometria a todos os arquivos CSV que seguem um padrão
    
    Args:
        padrao (str): Padrão para encontrar arquivos CSV (ex: "*.csv")
        pasta_geometria (str): Pasta onde está o arquivo de geometria
        arquivo_geometria (str): Nome do arquivo de geometria (.gpkg)
        pasta_saida (str): Pasta onde salvar os arquivos de saída
    """
    
    # Listar todos os arquivos CSV que seguem o padrão
    arquivos_csv = [f for f in os.listdir('.') if f.endswith('.csv') and any(p in f for p in padrao.split('*'))]
    arquivos_csv.sort()
    
    if not arquivos_csv:
        print(f"❌ Nenhum arquivo CSV encontrado com o padrão: {padrao}")
        return
    
    print(f"Encontrados {len(arquivos_csv)} arquivos para processar:")
    for arquivo in arquivos_csv:
        print(f"  - {arquivo}")
    
    # Processar cada arquivo
    sucessos = 0
    for arquivo in arquivos_csv:
        print(f"\n{'='*60}")
        if adicionar_geometria_arquivo(arquivo, pasta_geometria, arquivo_geometria, pasta_saida):
            sucessos += 1
    
    print(f"\n🎉 Processamento concluído!")
    print(f"📁 Arquivos gerados na pasta: {pasta_saida}")
    print(f"📋 Total de arquivos processados: {len(arquivos_csv)}")
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {len(arquivos_csv) - sucessos}")

def main():
    """
    Função principal que permite usar o script de diferentes formas
    """
    parser = argparse.ArgumentParser(description='Adicionar geometria a arquivos CSV')
    parser.add_argument('--arquivo', type=str, help='Arquivo CSV específico para processar')
    parser.add_argument('--padrao', type=str, default="geodata_icv-pcv-pop-psi_por_municipio_*.csv", 
                       help='Padrão para encontrar arquivos CSV (padrão: geodata_icv-pcv-pop-psi_por_municipio_*.csv)')
    parser.add_argument('--pasta-geometria', type=str, default="dados_comparar",
                       help='Pasta onde está o arquivo de geometria (padrão: dados_comparar)')
    parser.add_argument('--arquivo-geometria', type=str, default="geodata_hidrologia_municipios_2025.gpkg",
                       help='Nome do arquivo de geometria (padrão: geodata_hidrologia_municipios_2025.gpkg)')
    parser.add_argument('--pasta-saida', type=str, default="dados_com_geometria_csv",
                       help='Pasta onde salvar os arquivos de saída (padrão: dados_com_geometria_csv)')
    
    args = parser.parse_args()
    
    if args.arquivo:
        # Processar arquivo específico
        adicionar_geometria_arquivo(args.arquivo, args.pasta_geometria, args.arquivo_geometria, args.pasta_saida)
    else:
        # Processar todos os arquivos que seguem o padrão
        adicionar_geometria_pasta(args.padrao, args.pasta_geometria, args.arquivo_geometria, args.pasta_saida)

if __name__ == "__main__":
    # Se não houver argumentos, usar o comportamento padrão
    import sys
    if len(sys.argv) == 1:
        adicionar_geometria_pasta()
    else:
        main() 
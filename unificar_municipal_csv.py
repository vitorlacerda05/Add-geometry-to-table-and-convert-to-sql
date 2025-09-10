#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para unificar dados municipais de 2016 a 2024
Remove colunas de geometria e arredonda valores numéricos
"""

import pandas as pd
import os
from pathlib import Path
import argparse

def unificar_dados_municipais(anos=range(2016, 2025), nome_arquivo_saida="dados_vegetacao_por_municipio", pasta_saida="muncipal_unificado_csv"):
    """
    Unifica dados municipais de múltiplos anos em um único CSV
    
    Args:
        anos: range de anos para processar (padrão: 2016-2024)
        nome_arquivo_saida: nome do arquivo CSV de saída (sem extensão)
        pasta_saida: pasta onde salvar o arquivo unificado
    """
    
    print(f"Iniciando unificação de dados municipais para os anos {list(anos)}...")
    
    # Criar pasta de saída se não existir
    Path(pasta_saida).mkdir(exist_ok=True)
    
    # Lista para armazenar todos os DataFrames
    dataframes = []
    
    # Processar cada ano
    for ano in anos:
        nome_arquivo = f"geodata_icv_pcv_pop_psi_por_municipio_{ano}.csv"
        
        if os.path.exists(nome_arquivo):
            print(f"Processando arquivo: {nome_arquivo}")
            
            # Ler o CSV
            df = pd.read_csv(nome_arquivo)
            
            # Verificar se tem colunas de geometria e removê-las
            colunas_geometria = ['geom', 'geojson', 'geometry']
            colunas_para_remover = [col for col in colunas_geometria if col in df.columns]
            
            if colunas_para_remover:
                print(f"  Removendo colunas de geometria: {colunas_para_remover}")
                df = df.drop(columns=colunas_para_remover)
            
            # Arredondar colunas numéricas para 2 casas decimais
            colunas_numericas = df.select_dtypes(include=['float64', 'float32']).columns
            for col in colunas_numericas:
                df[col] = df[col].round(2)
            
            print(f"  Linhas processadas: {len(df)}")
            dataframes.append(df)
            
        else:
            print(f"  Arquivo não encontrado: {nome_arquivo}")
    
    if not dataframes:
        print("Nenhum arquivo foi encontrado para processar!")
        return
    
    # Unificar todos os DataFrames
    print("Unificando todos os dados...")
    df_unificado = pd.concat(dataframes, ignore_index=True)
    
    # Ordenar por código do município e ano
    if 'cd_mun' in df_unificado.columns and 'ano' in df_unificado.columns:
        df_unificado = df_unificado.sort_values(['cd_mun', 'ano'])
    
    # Caminho do arquivo de saída
    arquivo_saida = os.path.join(pasta_saida, f"{nome_arquivo_saida}.csv")
    
    # Salvar o arquivo unificado
    print(f"Salvando arquivo unificado: {arquivo_saida}")
    df_unificado.to_csv(arquivo_saida, index=False, encoding='utf-8')
    
    # Estatísticas finais
    print(f"\n=== RESUMO ===")
    print(f"Total de linhas unificadas: {len(df_unificado)}")
    print(f"Anos processados: {sorted(df_unificado['ano'].unique()) if 'ano' in df_unificado.columns else 'N/A'}")
    print(f"Municípios únicos: {df_unificado['cd_mun'].nunique() if 'cd_mun' in df_unificado.columns else 'N/A'}")
    print(f"Colunas no arquivo final: {list(df_unificado.columns)}")
    print(f"Arquivo salvo em: {arquivo_saida}")

def main():
    """Função principal com argumentos de linha de comando"""
    parser = argparse.ArgumentParser(description='Unifica dados municipais de múltiplos anos')
    parser.add_argument('--anos', nargs='+', type=int, default=list(range(2016, 2025)),
                       help='Anos para processar (padrão: 2016-2024)')
    parser.add_argument('--nome-arquivo', type=str, default="dados_vegetacao_por_municipio",
                       help='Nome do arquivo de saída (sem extensão)')
    parser.add_argument('--pasta-saida', type=str, default="muncipal_unificado_csv",
                       help='Pasta onde salvar o arquivo unificado')
    
    args = parser.parse_args()
    
    # Converter lista de anos para range se necessário
    if len(args.anos) > 1:
        anos = sorted(args.anos)
    else:
        anos = args.anos
    
    unificar_dados_municipais(anos=anos, nome_arquivo_saida=args.nome_arquivo, pasta_saida=args.pasta_saida)

if __name__ == "__main__":
    main()

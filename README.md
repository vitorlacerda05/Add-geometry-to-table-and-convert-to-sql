# Adicionar Geometria ao CSV e Converter para SQL

Este projeto contém scripts para adicionar geometria a arquivos CSV (gerados normalmente pelo Google Earth Engine) e convertê-los para formato SQL para inserção em banco de dados.

## 🎯 Objetivo

Adicionar geometria a um arquivo CSV gerado (normalmente pelo Google Earth Engine) e converter para SQL para adicionar no banco de dados.

## 📁 Estrutura da Pasta

```
add_geometry_to_csv_convert_sql/
├── adicionar_geometria_csv_municipal.py    # Script para adicionar geometria por município
├── adicionar_geometria_csv_setor.py        # Script para adicionar geometria por setor
├── csv_para_sql_municipal.py               # Script para converter CSV municipal para SQL
├── csv_para_sql_setor.py                   # Script para converter CSV de setor para SQL
├── dados_comparar/                         # Pasta com arquivos de geometria de referência
│   ├── geodata_hidrologia_municipios_2025.gpkg  # Exemplo do arquivo para municipal
│   └── geodata_pracas_por_setor_2024.gpkg       # Exemplo do arquivo para setor
├── dados_com_geometria_csv/                # Pasta com CSVs processados (municipal)
├── dados_com_geometria_setor_csv/          # Pasta com CSVs processados (setor)
├── dados_sql/                              # Pasta com arquivos SQL (municipal)
├── dados_sql_setor/                        # Pasta com arquivos SQL (setor)
└── README.md
```

## 📋 Pré-requisitos

1. **Adicionar arquivos de geometria** na pasta `dados_comparar/`:
   - Para municípios: arquivo `.gpkg` com coluna `CD_MUN` e geometria do municipio
   - Para setores: arquivo `.gpkg` com coluna `CD_SETOR` e geometria do setor

2. **Adicionar arquivo CSV** que será processado na pasta base:
   - Para municípios: CSV com coluna `cd_mun`
   - Para setores: CSV com coluna `cd_setor`

## 🔧 Como Usar

### 1. Para Adicionar Geometria de Município (CD_MUN)

#### 1.1. Preparar os arquivos:
- Coloque o arquivo `.gpkg` com geometria dos municípios em `dados_comparar/`
- Coloque o arquivo CSV com dados na raiz do projeto

#### 1.2. Modificar o script `adicionar_geometria_csv_municipal.py`:

```python
# Linha 18: Alterar nome do arquivo de geometria
arquivo_geometria="seu_arquivo_municipios.gpkg"

# Linha 18: Alterar nome do arquivo CSV se necessário
arquivo_csv="seu_arquivo.csv"

# Linha 18: Alterar padrão de busca se necessário
padrao="seu_padrao_*.csv"
```

#### 1.3. Executar o script:

```bash
# Processar todos os arquivos com padrão padrão
python adicionar_geometria_csv_municipal.py

# Processar arquivo específico
python adicionar_geometria_csv_municipal.py --arquivo seu_arquivo.csv

# Usar parâmetros customizados
python adicionar_geometria_csv_municipal.py \
  --arquivo-geometria seu_arquivo.gpkg \
  --pasta-geometria dados_comparar \
  --pasta-saida dados_com_geometria_csv
```

#### 1.4. Converter para SQL:

```bash
# Converter todos os arquivos processados
python csv_para_sql_municipal.py

# Converter arquivo específico
python csv_para_sql_municipal.py --arquivo dados_com_geometria_csv/seu_arquivo_com_geometria.csv

# Usar parâmetros customizados
python csv_para_sql_municipal.py \
  --pasta-csv dados_com_geometria_csv \
  --pasta-saida dados_sql \
  --srid 31983 \
  --tipo-geometria MULTIPOLYGON
```

### 2. Para Adicionar Geometria de Setor (CD_SETOR)

#### 2.1. Preparar os arquivos:
- Coloque o arquivo `.gpkg` com geometria dos setores em `dados_comparar/`
- Coloque o arquivo CSV com dados em `dados_comparar/` ou na raiz do projeto

#### 2.2. Modificar o script `adicionar_geometria_csv_setor.py`:

```python
# Linha 18: Alterar nome do arquivo de geometria
arquivo_geometria="seu_arquivo_setores.gpkg"

# Linha 18: Alterar nome do arquivo CSV se necessário
arquivo_csv="seu_arquivo.csv"

# Linha 18: Alterar padrão de busca se necessário
padrao="seu_padrao_*.csv"
```

#### 2.3. Executar o script:

```bash
# Processar todos os arquivos com padrão padrão
python adicionar_geometria_csv_setor.py

# Processar arquivo específico
python adicionar_geometria_csv_setor.py --arquivo seu_arquivo.csv

# Usar parâmetros customizados
python adicionar_geometria_csv_setor.py \
  --arquivo-geometria seu_arquivo.gpkg \
  --pasta-geometria dados_comparar \
  --pasta-saida dados_com_geometria_setor_csv
```

#### 2.4. Converter para SQL:

```bash
# Converter todos os arquivos processados
python csv_para_sql_setor.py

# Converter arquivo específico
python csv_para_sql_setor.py --arquivo dados_com_geometria_setor_csv/seu_arquivo_com_geometria.csv

# Usar parâmetros customizados
python csv_para_sql_setor.py \
  --pasta-csv dados_com_geometria_setor_csv \
  --pasta-saida dados_sql_setor \
  --srid 31983 \
  --tipo-geometria MULTIPOLYGON
```

## 📊 Colunas Adicionadas

### Para Municípios:
- `cd_rgi`: Código da Região Geográfica Imediata
- `nm_rgi`: Nome da Região Geográfica Imediata
- `cd_rgint`: Código da Região Geográfica Intermediária
- `nm_rgint`: Nome da Região Geográfica Intermediária
- `cd_uf`: Código da Unidade da Federação
- `nm_uf`: Nome da Unidade da Federação
- `sigla_uf`: Sigla da Unidade da Federação
- `geometry`: Geometria em formato WKB

### Para Setores:
- `cd_uf`: Código da Unidade da Federação
- `nm_uf`: Nome da Unidade da Federação
- `cd_rgint`: Código da Região Geográfica Intermediária
- `nm_rgint`: Nome da Região Geográfica Intermediária
- `cd_rgi`: Código da Região Geográfica Imediata
- `nm_rgi`: Nome da Região Geográfica Imediata
- `geometry`: Geometria em formato WKB

## 🔧 Parâmetros dos Scripts

### Scripts de Adicionar Geometria:

- `--arquivo`: Arquivo CSV específico para processar
- `--padrao`: Padrão para encontrar arquivos CSV
- `--pasta-geometria`: Pasta onde está o arquivo de geometria
- `--arquivo-geometria`: Nome do arquivo de geometria (.gpkg)
- `--pasta-saida`: Pasta onde salvar os arquivos de saída

### Scripts de Conversão para SQL:

- `--arquivo`: Arquivo CSV específico para processar
- `--pasta-csv`: Pasta com os arquivos CSV
- `--padrao`: Padrão para encontrar arquivos CSV
- `--pasta-saida`: Pasta onde salvar os arquivos SQL
- `--nome-tabela`: Nome da tabela (se não fornecido, usa o nome do arquivo)
- `--srid`: SRID para a geometria (padrão: 31983)
- `--tipo-geometria`: Tipo de geometria (padrão: MULTIPOLYGON)

## 📝 Formato dos Arquivos

### Arquivo de Geometria (.gpkg):
- Deve conter coluna `CD_MUN` (para municípios) ou `CD_SETOR` (para setores)
- Deve conter coluna `geometry` com as geometrias
- Pode conter colunas adicionais que serão incluídas no resultado

### Arquivo CSV de Entrada:
- Deve conter coluna `cd_mun` (para municípios) ou `cd_setor` (para setores)
- Pode conter qualquer número de colunas adicionais

### Arquivo SQL de Saída:
- Cria tabela com todas as colunas do CSV + geometria
- Usa `AddGeometryColumn` para adicionar coluna de geometria
- Geometria em formato WKB (Well-Known Binary)
- Compatível com PostGIS

## ⚠️ Observações Importantes

1. **Compatibilidade de códigos**: Os códigos de município/setor devem ser compatíveis entre o arquivo CSV e o arquivo de geometria
2. **Formato de geometria**: A geometria é convertida para formato WKB para compatibilidade com PostGIS
3. **SRID**: Por padrão usa SRID 31983 (UTM Zone 23S), mas pode ser alterado
4. **Tipo de geometria**: Por padrão usa MULTIPOLYGON, mas pode ser alterado conforme necessário
5. **Arquivos grandes**: Para arquivos muito grandes, o processamento pode demorar

## 🚀 Fluxo de Trabalho Recomendado

1. **Preparar dados**: Colocar arquivos de geometria e CSV na pasta `dados_comparar/`
2. **Adicionar geometria**: Executar script de adicionar geometria
3. **Verificar resultados**: Verificar arquivos gerados na pasta de saída
4. **Converter para SQL**: Executar script de conversão para SQL
5. **Importar no banco**: Usar arquivos SQL gerados para importar no banco de dados 
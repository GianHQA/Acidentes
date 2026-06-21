# Dashboard Executivo — Acidentes de Trânsito (PRF)

Dashboard interativo em Python (Streamlit + Plotly + Pandas) para análise de acidentes
de trânsito em rodovias federais brasileiras, construído a partir das bases públicas da
**Polícia Rodoviária Federal (PRF)**: `Datatran` (acidente) e `Acidentes` (pessoas/veículos
envolvidos), anos 2022–2025.

## Estrutura de Pastas

```
.
├── acidentes/                  # CSVs brutos — grão = pessoa/veículo envolvido
├── datatran/                   # CSVs brutos — grão = acidente
├── data_model/                 # Modelo otimizado (Parquet) gerado pelo ETL
│   ├── fact_acidentes.parquet
│   ├── fact_pessoas.parquet
│   └── dim_uf.parquet
├── etl/
│   └── build_model.py          # Script de ETL: lê os CSVs, limpa e gera o modelo Parquet
├── app/
│   ├── Home.py                 # Página inicial (entrypoint do Streamlit)
│   ├── pages/
│   │   ├── 1_Visao_Executiva.py
│   │   ├── 2_Visao_Operacional.py
│   │   ├── 3_Analise_Geografica.py
│   │   ├── 4_Analise_Temporal.py
│   │   ├── 5_Fatores_de_Risco.py
│   │   └── 6_Insights_e_Recomendacoes.py
│   └── utils/
│       ├── data_loader.py      # Carregamento cacheado do Parquet
│       ├── filters.py          # Filtros globais sincronizados
│       ├── style.py            # Paleta de cores e CSS
│       ├── charts.py           # Construtores de gráficos Plotly
│       ├── insights.py         # Geração de insights em linguagem natural
│       └── export.py           # Exportação para Excel/PDF
├── requirements.txt
└── README.md
```

## Instalação

Requer Python 3.10+.

```bash
pip install -r requirements.txt
```

## Como Executar

**1. Gerar o modelo de dados** (necessário apenas na primeira vez, ou quando novos CSVs
forem adicionados às pastas `acidentes/` e `datatran/`):

```bash
python etl/build_model.py
```

Isso lê todos os `.csv` das duas pastas, aplica a limpeza de dados e grava os arquivos
Parquet em `data_model/` (processo leva ~30-60s e roda uma única vez).

**2. Rodar o dashboard:**

```bash
python -m streamlit run app/Home.py
```

O navegador abre automaticamente em `http://localhost:8501`. Navegue pelas páginas
pelo menu lateral esquerdo (abaixo dos filtros globais).

## Modelo de Dados

A base original possui duas granularidades distintas, ligadas pela chave `id`:

| Tabela              | Grão                              | Linhas (2022-2025) | Origem        |
|---------------------|------------------------------------|--------------------|---------------|
| `fact_acidentes`     | 1 linha por **acidente**           | ~271 mil           | `datatran/`   |
| `fact_pessoas`       | 1 linha por **pessoa/veículo envolvido** | ~726 mil      | `acidentes/`  |
| `dim_uf`             | 1 linha por UF (27)                | 27                 | derivado      |

### Tratamentos de qualidade aplicados pelo ETL
- **Encoding**: arquivos lidos em `latin-1` (ISO-8859-1) e convertidos para UTF-8.
- **Duplicidade**: remoção de linhas 100% idênticas; `fact_acidentes` garante 1 linha por `id`.
  (Linhas com `pesid = 0` em `acidentes/` representam veículos sem ocupante — não são duplicidade.)
- **Datas/horários**: parsing de `data_inversa`/`horario`, derivação de `ano`, `mes`, `dia_semana`,
  `hora`, `periodo_dia` (Madrugada/Manhã/Tarde/Noite).
- **Números com vírgula (pt-BR)**: `km`, `latitude`, `longitude` convertidos de string `"12,34"` para `float`.
- **Coordenadas inválidas**: registros com lat/long fora do território brasileiro são marcados como nulos
  (cerca de **27%** dos acidentes não possuem coordenadas válidas na base oficial — os mapas
  consideram apenas o subconjunto válido, isso é informado na própria página de Análise Geográfica).
- **Categorias ausentes**: nulos em `classificacao_acidente`, `sexo`, `tipo_envolvido`, `estado_fisico`,
  `tipo_veiculo`, `marca` recebem rótulo explícito ("Não informado" / "Veículo sem ocupante"), nunca silenciosamente descartados.
- **Idade inconsistente**: valores fora de 0–120 anos são tratados como nulos; faixas etárias derivadas.
- **Integridade referencial**: `fact_pessoas` é filtrada para conter apenas `id`s existentes em `fact_acidentes`.

### Métricas derivadas
- **`gravidade`**: Fatal / Grave / Leve / Sem Vítimas — derivada de `mortos`, `feridos_graves`,
  `feridos_leves` (mais granular e sem nulos que o campo oficial `classificacao_acidente`, que possui
  apenas 3 categorias e ~0,03% de ausência).
- **`periodo_dia`**: faixa horária (Madrugada/Manhã/Tarde/Noite), derivada de `hora`.
- **`taxa_mortalidade_acidente`**: `mortos / pessoas` por acidente.
- **Taxa de mortalidade (executiva)**: `Σ mortos / Σ pessoas` no recorte filtrado.

Por que Parquet? Os CSVs somam ~350 MB e exigem parsing de texto a cada leitura; o modelo
em Parquet (tipado, colunar e comprimido) ocupa **~26 MB no total** e carrega em milissegundos
com `st.cache_data`, garantindo boa performance mesmo filtrando centenas de milhares de linhas
interativamente.

## Filtros Globais

Painel lateral, presente em todas as páginas e sincronizado via `st.session_state`:
Ano, Mês, Estado (UF), Município (em cascata com UF), BR, Tipo de Acidente, Gravidade,
Período do Dia.

## Páginas

1. **Visão Executiva** — KPIs estratégicos (total de acidentes, vítimas, óbitos, taxa de
   mortalidade), evolução anual/mensal, ranking de regiões mais críticas.
2. **Visão Operacional** — análise cruzada por tipo/causa/clima/pista/via/dia/município/UF,
   tabela dinâmica configurável e fluxo de **drill-down → drill-through** (de acidente até
   pessoa/veículo envolvido).
3. **Análise Geográfica** — mapa de calor (densidade), bolhas por estado, clusterização
   geográfica via K-Means e rankings por estado/município.
4. **Análise Temporal** — série temporal com tendência (média móvel), sazonalidade mensal,
   padrão por dia da semana e comparação interativa entre dois períodos (anos).
5. **Fatores de Risco** — heatmap dia×hora, causas mais letais, condição climática × taxa de
   mortalidade, tipo de pista/traçado × gravidade, perfil de vítimas (idade/sexo).
6. **Insights e Recomendações** — narrativa automática (linguagem natural) recalculada a
   partir do recorte filtrado + recomendações acionáveis + exportação (Excel/PDF).

## Storytelling Adotado

O dashboard é estruturado para responder, em sequência, às perguntas que orientam a tomada
de decisão em segurança viária:

1. **Onde?** → Visão Executiva / Análise Geográfica (ranking e mapas por UF/município).
2. **Quando?** → Análise Temporal (sazonalidade, tendência, dia/hora crítico).
3. **Por quê?** → Fatores de Risco (causas, clima, pista associados a gravidade).
4. **Quem é afetado?** → Fatores de Risco (perfil de vítimas) / Visão Operacional (drill-through).
5. **O que fazer?** → Insights e Recomendações (síntese automática + ações sugeridas).

Cada insight da última página é **recalculado dinamicamente** sobre os filtros ativos —
a narrativa muda conforme o gestor explora o dashboard, em vez de apresentar números fixos.

## Exportações

- **Excel**: dados do recorte filtrado (página *Insights e Recomendações*).
- **PDF**: relatório executivo resumido com KPIs + insights automáticos.
- **Imagem**: cada gráfico Plotly possui o ícone de câmera no canto superior direito
  para captura/exportação individual em PNG.

## Sugestões de Evolução Futura

- Migrar a camada de filtros para um backend leve (DuckDB/SQLite sobre o Parquet) caso o
  volume de dados cresça significativamente (>10 milhões de linhas).
- Adicionar autenticação/perfis de acesso (ex.: gestor regional vê apenas sua UF).
- Incorporar dados de tráfego/frota por município para calcular taxas per-capita ou
  por veículos circulantes, e não apenas valores absolutos.
- Modelo preditivo (ex.: regressão/XGBoost) para estimar risco de acidente grave por
  trecho de BR, horário e condição climática prevista.
- Atualização automática incremental (agendada) do ETL ao chegar um novo arquivo anual.
- Versão mobile-first / modo apresentação para reuniões executivas.

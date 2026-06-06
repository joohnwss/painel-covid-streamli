# Painel Hospitalar | PNAD COVID-19

Dashboard analítico desenvolvido para o Tech Challenge da pós-graduação em Data Analytics, com foco na análise da PNAD COVID-19 e no apoio ao planejamento hospitalar em cenários de novos surtos respiratórios.

## Objetivo do projeto

O objetivo do projeto é analisar dados da PNAD COVID-19 para identificar sinais clínicos, sociais, econômicos e territoriais que possam apoiar decisões hospitalares em caso de novo surto.

A análise busca responder perguntas como:

- Quais indicadores podem sinalizar aumento de pressão assistencial?
- Quais grupos apresentam maior vulnerabilidade clínica ou social?
- Como renda, plano de saúde, trabalho e território se relacionam com o acesso ao cuidado?
- Quais ações o hospital deve priorizar diante de novos sinais de alerta?

## Fonte e preparação dos dados

A base utilizada no projeto foi a PNAD COVID-19, disponibilizada pelo IBGE. Os dados foram organizados em uma arquitetura de processamento em nuvem na AWS, contemplando armazenamento, tratamento, consultas analíticas e geração de tabelas finais para consumo no painel.

A estrutura de dados seguiu o modelo em camadas:

- **Bronze**: armazenamento dos dados originais.
- **Prata**: dados tratados, padronizados e preparados para análise.
- **Gold/Ouro**: tabelas analíticas materializadas, com indicadores clínicos, sociais, econômicos e territoriais.

O dashboard em Streamlit utiliza os arquivos da pasta `dados_dashboard/`, que representam as tabelas finais materializadas a partir do pipeline em nuvem. Essa abordagem permite que o painel seja executado de forma estável durante a apresentação, preservando a lógica da camada Gold/Ouro e evitando dependência direta das credenciais temporárias do ambiente AWS Academy.

## Fluxo geral da solução

```text
PNAD COVID-19 IBGE
        ↓
AWS S3 - Camada Bronze
        ↓
AWS Glue - Tratamento e padronização
        ↓
AWS S3 - Camada Prata
        ↓
Athena / Glue - Consultas e materializações analíticas
        ↓
AWS S3 - Camada Gold/Ouro
        ↓
Exportação das tabelas finais
        ↓
Streamlit Dashboard
```

## Camada de visualização

O painel foi construído em Streamlit e organiza os indicadores em uma narrativa voltada à tomada de decisão hospitalar.

As principais dimensões analisadas são:

- evolução mensal de sinais de alerta;
- testagem e positividade;
- dificuldade respiratória e gravidade;
- acesso ao cuidado;
- dependência potencial do SUS;
- vulnerabilidade territorial;
- trabalho, renda e proteção social;
- correlações econômico-clínicas;
- plano de ação hospitalar.

## Estrutura do projeto

```text
Techchallenger_dashboard_streamlit_pnad_Entrega/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
└── dados_dashboard/
    ├── analise_01_barreira_economica.csv
    ├── analise_02_informalidade_risco.csv
    ├── analise_03_perfil_grave.csv
    ├── analise_04_protecao_social.csv
    ├── analise_05_mapa_desigualdade.csv
    ├── analise_06_evolucao_mensal.csv
    ├── analise_07_escolaridade_genero.csv
    ├── analise_08_moradia_endividamento.csv
    ├── analise_09_sus_privado.csv
    └── correlacoes_economico_clinico.csv
```

## Arquivos de dados utilizados

Os arquivos da pasta `dados_dashboard/` correspondem às saídas analíticas geradas após o tratamento e materialização dos dados.

| Arquivo | Uso principal |
|---|---|
| `analise_01_barreira_economica.csv` | Renda, plano de saúde e acesso ao cuidado |
| `analise_02_informalidade_risco.csv` | Trabalho, informalidade, home office e exposição |
| `analise_03_perfil_grave.csv` | Perfil clínico e sinais de gravidade |
| `analise_04_protecao_social.csv` | Benefícios sociais e vulnerabilidade |
| `analise_05_mapa_desigualdade.csv` | Recortes territoriais por UF e região |
| `analise_06_evolucao_mensal.csv` | Série mensal de indicadores de alerta |
| `analise_07_escolaridade_genero.csv` | Recortes por escolaridade e gênero |
| `analise_08_moradia_endividamento.csv` | Moradia, endividamento e proteção domiciliar |
| `analise_09_sus_privado.csv` | Local de atendimento e relação SUS/privado |
| `correlacoes_economico_clinico.csv` | Correlações entre fatores sociais e desfechos clínicos |

## Páginas do dashboard

O painel está dividido em blocos de análise:

1. **Visão executiva**  
   Síntese dos principais indicadores para decisão assistencial.

2. **Sinais de alerta**  
   Evolução mensal de testagem, positividade, sintomas e gravidade.

3. **Acesso ao cuidado**  
   Análise da relação entre renda, plano de saúde e busca por atendimento.

4. **Perfil clínico**  
   Leitura de grupos com maior risco clínico e sinais de agravamento.

5. **Territórios e rede**  
   Identificação de UFs e regiões com maior vulnerabilidade e dependência potencial da rede pública.

6. **Trabalho e proteção social**  
   Análise de condições econômicas, trabalho, proteção social e exposição.

7. **Correlações e cautelas**  
   Relações entre fatores econômico-sociais e indicadores clínicos, com atenção às limitações metodológicas.

8. **Plano de ação**  
   Matriz executiva com sinais observados, riscos hospitalares, respostas recomendadas e áreas responsáveis.

## Regras de leitura temporal

A análise utiliza três meses de referência da PNAD COVID-19.

Para manter a coerência dos gráficos:

- gráficos de evolução mensal utilizam a série completa disponível;
- rankings e comparações transversais usam o mês selecionado no filtro;
- quando o filtro está em **Todos**, rankings e comparações utilizam o último mês disponível em cada arquivo materializado, evitando mistura de recortes mensais.

Essa regra evita que uma mesma UF, grupo ou categoria apareça duplicada por representar meses diferentes.

## Notas metodológicas

Alguns cuidados foram adotados na interpretação dos resultados:

- recortes com amostras pequenas devem ser tratados como sinais exploratórios;
- internação entre atendidos não representa taxa sobre toda a população;
- correlação não significa causalidade;
- locais de atendimento não devem ser somados como partes exclusivas de um total, pois uma pessoa pode ter marcado mais de uma opção;
- os indicadores foram construídos para apoiar planejamento e priorização, não para diagnóstico individual.

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/vtfarias/tech-challenge-pnad-covid.git
cd tech-challenge-pnad-covid
```

### 2. Criar ambiente virtual

No Windows:

```powershell
py -m venv .venv
```

### 3. Instalar dependências

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Rodar o dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O Streamlit abrirá no navegador, geralmente em:

```text
http://localhost:8501
```

Caso a porta esteja ocupada, é possível executar em outra porta:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

## Dependências principais

As bibliotecas utilizadas estão listadas no arquivo `requirements.txt`.

Principais dependências:

- Streamlit
- Pandas
- Plotly
- NumPy

## Entrega e interpretação

O dashboard deve ser entendido como a camada de visualização da solução analítica. A etapa de preparação e materialização dos dados foi realizada no ambiente AWS, enquanto o Streamlit organiza os resultados finais em uma interface executiva voltada ao contexto hospitalar.

A proposta final combina:

- arquitetura de dados em nuvem;
- tratamento e materialização analítica;
- visualização em BI;
- recomendações práticas para planejamento hospitalar.

## Equipe

Projeto desenvolvido para o Tech Challenge da pós-graduação em Data Analytics.
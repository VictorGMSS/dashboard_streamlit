import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title='Dashboard de Vendas',
    page_icon='🛒',
    layout='wide',
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor, prefixo=''):
    """
    Formata números grandes para:
    mil, milhões e bilhões.
    """

    match valor:

        case _ if valor < 1_000:
            return f'{prefixo} {valor:.2f}'

        case _ if valor < 1_000_000:
            valor /= 1_000
            return f'{prefixo} {valor:.2f} mil'

        case _ if valor < 1_000_000_000:
            valor /= 1_000_000
            return f'{prefixo} {valor:.2f} milhões'

        case _:
            valor /= 1_000_000_000
            return f'{prefixo} {valor:.2f} bilhões'


@st.cache_data
def carregar_dados(url, regiao='', ano=''):
    """
    Carrega dados da API.

    O cache evita múltiplas requisições
    desnecessárias.
    """

    query_string = {
        'regiao': regiao.lower(),
        'ano': ano
    }

    response = requests.get(url, params=query_string)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    # Converte coluna de data
    df['Data da Compra'] = pd.to_datetime(
        df['Data da Compra'],
        format='%d/%m/%Y'
    )

    return df


# =========================================================
# TÍTULO
# =========================================================

st.title('🛒 Dashboard de Vendas')

# =========================================================
# FILTROS SIDEBAR
# =========================================================

URL = 'https://labdados.com/produtos'

REGIOES = [
    'Brasil',
    'Centro-Oeste',
    'Nordeste',
    'Norte',
    'Sudeste',
    'Sul'
]

st.sidebar.title('🔎 Filtros')

# ---------------------------------------------------------
# REGIÃO
# ---------------------------------------------------------

regiao = st.sidebar.selectbox(
    'Região',
    REGIOES
)

# API usa string vazia para Brasil
regiao_api = '' if regiao == 'Brasil' else regiao

# ---------------------------------------------------------
# ANO
# ---------------------------------------------------------

todos_anos = st.sidebar.checkbox(
    'Dados de todo o período',
    value=True
)

ano = ''

if not todos_anos:

    ano = st.sidebar.slider(
        'Ano',
        2020,
        2023
    )

# =========================================================
# CARREGAMENTO DOS DADOS
# =========================================================

dados = carregar_dados(
    URL,
    regiao=regiao_api,
    ano=ano
)

# ---------------------------------------------------------
# FILTRO DE VENDEDORES
# ---------------------------------------------------------

filtro_vendedores = st.sidebar.multiselect(
    'Vendedores',
    options=dados['Vendedor'].unique()
)

if filtro_vendedores:

    dados = dados[
        dados['Vendedor'].isin(filtro_vendedores)
    ]

# =========================================================
# TABELAS - RECEITA
# =========================================================

# Receita por estado
receita_estados = (
    dados
    .groupby('Local da compra')[['Preço']]
    .sum()
)

receita_estados = (
    dados
    .drop_duplicates(subset='Local da compra')
    [['Local da compra', 'lat', 'lon']]
    .merge(
        receita_estados,
        left_on='Local da compra',
        right_index=True
    )
    .sort_values('Preço', ascending=False)
)

# Receita mensal
receita_mensal = (
    dados
    .set_index('Data da Compra')
    .groupby(pd.Grouper(freq='ME'))['Preço']
    .sum()
    .reset_index()
)

receita_mensal['Ano'] = (
    receita_mensal['Data da Compra']
    .dt.year
)

receita_mensal['Mes'] = (
    receita_mensal['Data da Compra']
    .dt.month_name()
)

# Receita por categoria
receita_categorias = (
    dados
    .groupby('Categoria do Produto')[['Preço']]
    .sum()
    .sort_values('Preço', ascending=False)
)

# =========================================================
# TABELAS - QUANTIDADE DE VENDAS
# =========================================================

# Quantidade por estado
vendas_estados = (
    dados
    .groupby('Local da compra')['Preço']
    .count()
    .to_frame()
    .rename(columns={'Preço': 'Quantidade'})
)

vendas_estados = (
    dados
    .drop_duplicates(subset='Local da compra')
    [['Local da compra', 'lat', 'lon']]
    .merge(
        vendas_estados,
        left_on='Local da compra',
        right_index=True
    )
    .sort_values('Quantidade', ascending=False)
)

# Quantidade mensal
vendas_mensal = (
    dados
    .set_index('Data da Compra')
    .groupby(pd.Grouper(freq='ME'))['Preço']
    .count()
    .reset_index()
    .rename(columns={'Preço': 'Quantidade'})
)

vendas_mensal['Ano'] = (
    vendas_mensal['Data da Compra']
    .dt.year
)

vendas_mensal['Mes'] = (
    vendas_mensal['Data da Compra']
    .dt.month_name()
)

# Quantidade por categoria
vendas_categorias = (
    dados
    .groupby('Categoria do Produto')['Preço']
    .count()
    .to_frame()
    .rename(columns={'Preço': 'Quantidade'})
    .sort_values('Quantidade', ascending=False)
)

# =========================================================
# TABELA - VENDEDORES
# =========================================================

vendedores = (
    dados
    .groupby('Vendedor')['Preço']
    .agg(['sum', 'count'])
)

# =========================================================
# GRÁFICOS - RECEITA
# =========================================================

fig_mapa_receita = px.scatter_geo(
    receita_estados,
    lat='lat',
    lon='lon',
    scope='south america',
    size='Preço',
    hover_name='Local da compra',
    hover_data={
        'lat': False,
        'lon': False
    },
    template='seaborn',
    title='Receita por estado'
)

fig_receita_mensal = px.line(
    receita_mensal,
    x='Mes',
    y='Preço',
    color='Ano',
    line_dash='Ano',
    markers=True,
    title='Receita mensal'
)

fig_receita_estados = px.bar(
    receita_estados.head(),
    x='Local da compra',
    y='Preço',
    text_auto=True,
    title='Top estados por receita'
)

fig_receita_categorias = px.bar(
    receita_categorias,
    y='Preço',
    text_auto=True,
    title='Receita por categoria'
)

# =========================================================
# GRÁFICOS - VENDAS
# =========================================================

fig_mapa_vendas = px.scatter_geo(
    vendas_estados,
    lat='lat',
    lon='lon',
    scope='south america',
    size='Quantidade',
    hover_name='Local da compra',
    hover_data={
        'lat': False,
        'lon': False
    },
    template='seaborn',
    title='Quantidade de vendas por estado'
)

fig_vendas_mensal = px.line(
    vendas_mensal,
    x='Mes',
    y='Quantidade',
    color='Ano',
    line_dash='Ano',
    markers=True,
    title='Quantidade de vendas mensal'
)

fig_vendas_estados = px.bar(
    vendas_estados.head(),
    x='Local da compra',
    y='Quantidade',
    text_auto=True,
    title='Top estados por vendas'
)

fig_vendas_categorias = px.bar(
    vendas_categorias,
    y='Quantidade',
    text_auto=True,
    title='Vendas por categoria'
)

# =========================================================
# ABAS
# =========================================================

aba1, aba2, aba3, aba4 = st.tabs([
    '💰 Receita',
    '📦 Quantidade',
    '🏆 Vendedores',
    '🗂 Dados'
])

# =========================================================
# ABA 1 - RECEITA
# =========================================================

with aba1:

    coluna1, coluna2 = st.columns(2)

    with coluna1:

        st.metric(
            'Receita Total',
            formatar_numero(
                dados['Preço'].sum(),
                'R$'
            )
        )

        st.plotly_chart(
            fig_mapa_receita,
            use_container_width=True
        )

        st.plotly_chart(
            fig_receita_estados,
            use_container_width=True
        )

    with coluna2:

        st.metric(
            'Quantidade de vendas',
            formatar_numero(dados.shape[0])
        )

        st.plotly_chart(
            fig_receita_mensal,
            use_container_width=True
        )

        st.plotly_chart(
            fig_receita_categorias,
            use_container_width=True
        )

# =========================================================
# ABA 2 - QUANTIDADE DE VENDAS
# =========================================================

with aba2:

    coluna1, coluna2 = st.columns(2)

    with coluna1:

        st.metric(
            'Receita Total',
            formatar_numero(
                dados['Preço'].sum(),
                'R$'
            )
        )

        st.plotly_chart(
            fig_mapa_vendas,
            use_container_width=True
        )

        st.plotly_chart(
            fig_vendas_estados,
            use_container_width=True
        )

    with coluna2:

        st.metric(
            'Quantidade de vendas',
            formatar_numero(dados.shape[0])
        )

        st.plotly_chart(
            fig_vendas_mensal,
            use_container_width=True
        )

        st.plotly_chart(
            fig_vendas_categorias,
            use_container_width=True
        )

# =========================================================
# ABA 3 - VENDEDORES
# =========================================================

with aba3:

    qtd_vendedores = st.number_input(
        'Quantidade de vendedores',
        min_value=2,
        max_value=10,
        value=5
    )

    coluna1, coluna2 = st.columns(2)

    # -----------------------------------------------------
    # RECEITA
    # -----------------------------------------------------

    with coluna1:

        st.metric(
            'Receita Total',
            formatar_numero(
                dados['Preço'].sum(),
                'R$'
            )
        )

        top_receita = (
            vendedores[['sum']]
            .sort_values('sum', ascending=False)
            .head(qtd_vendedores)
        )

        fig_receita_vendedores = px.bar(
            top_receita,
            x='sum',
            y=top_receita.index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
        )

        st.plotly_chart(
            fig_receita_vendedores,
            use_container_width=True
        )

    # -----------------------------------------------------
    # QUANTIDADE
    # -----------------------------------------------------

    with coluna2:

        st.metric(
            'Quantidade de vendas',
            formatar_numero(dados.shape[0])
        )

        top_vendas = (
            vendedores[['count']]
            .sort_values('count', ascending=False)
            .head(qtd_vendedores)
        )

        fig_vendas_vendedores = px.bar(
            top_vendas,
            x='count',
            y=top_vendas.index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (vendas)'
        )

        st.plotly_chart(
            fig_vendas_vendedores,
            use_container_width=True
        )

# =========================================================
# ABA 4 - DATAFRAMES
# =========================================================

with aba4:

    coluna1, coluna2 = st.columns(2)

    with coluna1:

        st.metric(
            'Receita Total',
            formatar_numero(
                dados['Preço'].sum(),
                'R$'
            )
        )

    with coluna2:

        st.metric(
            'Quantidade de vendas',
            formatar_numero(dados.shape[0])
        )

    st.badge(
        'Dados',
        color='primary'
    )

    st.dataframe(
        dados,
        use_container_width=True
    )

    st.badge(
        'Vendas por categoria',
        color='primary'
    )

    st.dataframe(
        vendas_categorias,
        use_container_width=True
    )
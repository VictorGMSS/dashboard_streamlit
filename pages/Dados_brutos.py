import time
import requests
import pandas as pd
import streamlit as st

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title='Dados Brutos',
    page_icon='📊',
    layout='wide'
)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

@st.cache_data
def carregar_dados(url):
    """
    Faz requisição da API e retorna um DataFrame.
    
    O cache evita novas requisições toda vez
    que o Streamlit atualiza a página.
    """

    response = requests.get(url)
    response.raise_for_status()

    df = pd.DataFrame(response.json())

    # Converte coluna de data para datetime
    df['Data da Compra'] = pd.to_datetime(
        df['Data da Compra'],
        format='%d/%m/%Y'
    )

    return df


@st.cache_data
def converter_csv(df):
    """
    Converte DataFrame para CSV.
    
    Necessário para o botão de download.
    """

    return df.to_csv(index=False).encode('utf-8')


def mensagem_sucesso():
    """
    Exibe mensagem temporária de sucesso
    após download do arquivo.
    """

    sucesso = st.success(
        'Arquivo baixado com sucesso!',
        icon='✅'
    )

    time.sleep(3)

    sucesso.empty()


# =========================================================
# CARREGAMENTO DOS DADOS
# =========================================================

URL = 'https://labdados.com/produtos'

dados = carregar_dados(URL)

# =========================================================
# TÍTULO DA PÁGINA
# =========================================================

st.title('📊 Dados Brutos')

# =========================================================
# SELEÇÃO DE COLUNAS
# =========================================================

with st.expander('📁 Colunas da tabela'):

    colunas = st.multiselect(
        'Selecione as colunas',
        options=dados.columns,
        default=dados.columns
    )

# =========================================================
# SIDEBAR - FILTROS
# =========================================================

st.sidebar.title('🔎 Filtros')

# ---------------------------------------------------------
# PRODUTO
# ---------------------------------------------------------

with st.sidebar.expander('Nome do produto'):

    produtos = st.multiselect(
        'Selecione os produtos',
        options=dados['Produto'].unique(),
        default=dados['Produto'].unique()
    )

# ---------------------------------------------------------
# CATEGORIA
# ---------------------------------------------------------

with st.sidebar.expander('Categoria do produto'):

    categorias = st.multiselect(
        'Selecione as categorias',
        options=dados['Categoria do Produto'].unique(),
        default=dados['Categoria do Produto'].unique()
    )

# ---------------------------------------------------------
# PREÇO
# ---------------------------------------------------------

with st.sidebar.expander('Preço do produto'):

    preco = st.slider(
        'Selecione o intervalo de preço',
        min_value=0.0,
        max_value=float(dados['Preço'].max()),
        value=(
            0.0,
            float(dados['Preço'].max())
        )
    )

# ---------------------------------------------------------
# FRETE
# ---------------------------------------------------------

with st.sidebar.expander('Frete'):

    frete = st.slider(
        'Selecione o intervalo de frete',
        min_value=0.0,
        max_value=float(dados['Frete'].max()),
        value=(
            0.0,
            float(dados['Frete'].max())
        )
    )

# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------

with st.sidebar.expander('Data da compra'):

    data_compra = st.date_input(
        'Selecione o período',
        value=(
            dados['Data da Compra'].min(),
            dados['Data da Compra'].max()
        )
    )

# ---------------------------------------------------------
# VENDEDOR
# ---------------------------------------------------------

with st.sidebar.expander('Vendedor'):

    vendedores = st.multiselect(
        'Selecione os vendedores',
        options=dados['Vendedor'].unique(),
        default=dados['Vendedor'].unique()
    )

# ---------------------------------------------------------
# LOCAL DA COMPRA
# ---------------------------------------------------------

with st.sidebar.expander('Local da compra'):

    locais = st.multiselect(
        'Selecione os locais',
        options=dados['Local da compra'].unique(),
        default=dados['Local da compra'].unique()
    )

# ---------------------------------------------------------
# AVALIAÇÃO
# ---------------------------------------------------------

with st.sidebar.expander('Avaliação da compra'):

    avaliacao = st.slider(
        'Selecione a avaliação',
        min_value=0,
        max_value=int(dados['Avaliação da compra'].max()),
        value=(
            0,
            int(dados['Avaliação da compra'].max())
        )
    )

# ---------------------------------------------------------
# TIPO DE PAGAMENTO
# ---------------------------------------------------------

with st.sidebar.expander('Tipo de pagamento'):

    pagamento = st.multiselect(
        'Selecione os pagamentos',
        options=dados['Tipo de pagamento'].unique(),
        default=dados['Tipo de pagamento'].unique()
    )

# ---------------------------------------------------------
# PARCELAS
# ---------------------------------------------------------

with st.sidebar.expander('Quantidade de parcelas'):

    parcelas = st.slider(
        'Selecione as parcelas',
        min_value=0,
        max_value=int(dados['Quantidade de parcelas'].max()),
        value=(
            0,
            int(dados['Quantidade de parcelas'].max())
        )
    )

# ---------------------------------------------------------
# LATITUDE
# ---------------------------------------------------------

with st.sidebar.expander('Latitude'):

    lat = st.slider(
        'Selecione latitude',
        min_value=float(dados['lat'].min()),
        max_value=float(dados['lat'].max()),
        value=(
            float(dados['lat'].min()),
            float(dados['lat'].max())
        )
    )

# ---------------------------------------------------------
# LONGITUDE
# ---------------------------------------------------------

with st.sidebar.expander('Longitude'):

    lon = st.slider(
        'Selecione longitude',
        min_value=float(dados['lon'].min()),
        max_value=float(dados['lon'].max()),
        value=(
            float(dados['lon'].min()),
            float(dados['lon'].max())
        )
    )

# =========================================================
# QUERY DE FILTRO
# =========================================================

query = (
    'Produto in @produtos and '
    '`Categoria do Produto` in @categorias and '
    '@preco[0] <= Preço <= @preco[1] and '
    '@frete[0] <= Frete <= @frete[1] and '
    '@data_compra[0] <= `Data da Compra` <= @data_compra[1] and '
    'Vendedor in @vendedores and '
    '`Local da compra` in @locais and '
    '@avaliacao[0] <= `Avaliação da compra` <= @avaliacao[1] and '
    '`Tipo de pagamento` in @pagamento and '
    '@parcelas[0] <= `Quantidade de parcelas` <= @parcelas[1] and '
    '@lat[0] <= lat <= @lat[1] and '
    '@lon[0] <= lon <= @lon[1]'
)

# Aplica filtros
dados_filtrados = dados.query(query)

# Mantém apenas colunas selecionadas
dados_filtrados = dados_filtrados[colunas]

# =========================================================
# EXIBIÇÃO DOS DADOS
# =========================================================

st.badge('Dados filtrados', color='primary')

st.dataframe(
    dados_filtrados,
    width='stretch'
)

# =========================================================
# MÉTRICAS DA TABELA
# =========================================================

st.markdown(
    f'''
    A tabela possui:

    - :blue[{dados_filtrados.shape[0]}] linhas
    - :blue[{dados_filtrados.shape[1]}] colunas
    '''
)

# =========================================================
# DOWNLOAD CSV
# =========================================================

st.markdown('### 📥 Download dos dados')
st.markdown('Escreva um nome para o arquivo')
coluna1, coluna2 = st.columns([1, 1])

# Nome do arquivo
# with coluna1:

#     nome_arquivo = st.text_input(
#         'Nome do arquivo',
#         value='dados_filtrados'
#     )

#     nome_arquivo += '.csv'

# Nome do arquivo
with coluna1:
    nome_arquivo = st.text_input('Nome do arquivo', label_visibility = 'collapsed', value = 'dados')
    nome_arquivo += '.csv'

# Botão de download
with coluna2:

    st.download_button(
        label='Fazer download CSV',
        data=converter_csv(dados_filtrados),
        file_name=nome_arquivo,
        mime='text/csv',
        on_click=mensagem_sucesso,
        width='content'
    )
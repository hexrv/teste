import streamlit as st
import pandas as pd
import altair as alt
import awswrangler as wr
import boto3
from datetime import datetime

# Dicionário de usuários
USERS = {
    "Henri.Santos": "Carbon@2024",
    "Cassio.Luis": "Carbon@2023",
    "Rafael.Augusto": "Carbon@2022",
    "Marcelo.Alves": "Carbon@2021"
}

# Função para configurar a região da AWS
def configure_aws():
    if "aws" in st.secrets:
        region = st.secrets["aws"].get("region")
        if region:
            boto3.setup_default_session(region_name=region)
            wr.config.aws.region = region  # Configura a região para awswrangler
            st.write(f"Região configurada corretamente: {region}")
        else:
            st.error("Região AWS não encontrada nos segredos.")
    else:
        st.error("Seção AWS não encontrada no arquivo de segredos.")

# Função para carregar dados da AWS Athena com caching
@st.experimental_memo(ttl=150)  # Cache por 150 segundos (2,5 minutos)
def load_data_from_athena():
    try:
        query = """
        SELECT status, key, modelo, marca, dt_finalizacao, summary, issuetype, dt_contrato, prazo
        FROM awsdatacatalog.jira_sbm.vw_veiculos_finalizados
        """
        # Executa a consulta e retorna um DataFrame
        df = wr.athena.read_sql_query(query, database='jira_sbm')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do Athena: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

# Função para processar e exibir dados
def process_and_display_data(data, dashboard):
    if 'dt_finalizacao' in data.columns:
        # Converte dt_finalizacao para datetime
        data['data_finalizacao'] = pd.to_datetime(data['dt_finalizacao'], format=None, infer_datetime_format=True)
        data.dropna(subset=['data_finalizacao'], inplace=True)
    else:
        st.error("Coluna 'dt_finalizacao' não encontrada na tabela.")
        return
    
    # Renomeia colunas para facilitar uso
    data.rename(columns={'marca': 'marca', 'modelo': 'modelo', 'prazo': 'prazo'}, inplace=True)
    
    # Converte a coluna prazo para numérico, tratando erros
    data['prazo'] = pd.to_numeric(data['prazo'], errors='coerce')
    
    # Adiciona colunas de tempo
    data['mes'] = data['data_finalizacao'].dt.to_period('M').astype(str)
    data['semana'] = data['data_finalizacao'].dt.to_period('W').astype(str)
    data['dia'] = data['data_finalizacao'].dt.date
    data['ano'] = data['data_finalizacao'].dt.year
    
    # Adiciona coluna de semana numerada (de 1 a 4)
    data['semana_numero'] = (data['data_finalizacao'].dt.day - 1) // 7 + 1
    data['semana_descricao'] = data['data_finalizacao'].dt.strftime('%B %Y') + ' - Semana ' + data['semana_numero'].astype(str)
    
    # Obtém o mês atual
    mes_atual = datetime.now().strftime('%Y-%m')

    # Configura o tamanho do gráfico
    chart_width = 800
    chart_height = 600

    if dashboard == 'Veículos Finalizados':
        st.title('Veículos Finalizados')

        # 1. Veículos Finalizados por Mês
        st.subheader('Veículos Finalizados por Mês')
        trend_monthly = data.groupby('mes').size().reset_index(name='quantidade')
        chart_trend = alt.Chart(trend_monthly).mark_bar().encode(
            x=alt.X('mes:O', title='Mês', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('mes:N', title='Mês', scale=alt.Scale(scheme='category20')),
            tooltip=['mes', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados por Mês'
        )
        st.altair_chart(chart_trend, use_container_width=True)
        
        # 2. Veículos Finalizados por Semana
        st.subheader('Veículos Finalizados por Semana')
        mes_selecionado = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='semanas_selectbox')
        data_filtrada_semana = data[data['mes'] == mes_selecionado]
        semana_count = data_filtrada_semana.groupby('semana_descricao').size().reset_index(name='quantidade')
        chart_semana = alt.Chart(semana_count).mark_bar().encode(
            x=alt.X('semana_descricao:N', title='Semana', axis=alt.Axis(labelAngle=45)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('semana_descricao:N', title='Semana', scale=alt.Scale(scheme='category20')),
            tooltip=['semana_descricao', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados por Semana'
        )
        st.altair_chart(chart_semana, use_container_width=True)

        # 3. Veículos Finalizados por Marca
        st.subheader('Veículos Finalizados por Marca')
        mes_selecionado_marca = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_selecionado_marca')
        data_filtrada_marca = data[data['mes'] == mes_selecionado_marca]
        marca_count = data_filtrada_marca.groupby('marca').size().reset_index(name='quantidade')
        chart_marca = alt.Chart(marca_count).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=90)),  # Legenda do eixo x na vertical
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('marca:N', title='Marca', scale=alt.Scale(scheme='category20')),
            tooltip=['marca', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados por Marca'
        )
        st.altair_chart(chart_marca, use_container_width=True)

        # 4. Veículos Finalizados por Modelo
        st.subheader('Veículos Finalizados por Modelo')
        mes_selecionado_modelo = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_modelo_selectbox')
        marca_selecionada = st.selectbox('Selecione a Marca', data['marca'].unique(), key='marca_modelo_selectbox')
        
        try:
            data_filtrada_modelo = data[(data['mes'] == mes_selecionado_modelo) & (data['marca'] == marca_selecionada)]
            
            if data_filtrada_modelo.empty:
                st.warning("Não há dados disponíveis para a combinação selecionada de mês e marca.")
                return
            
            modelo_count = data_filtrada_modelo.groupby('modelo').size().reset_index(name='quantidade')
            
            if modelo_count.empty:
                st.warning("Não há dados disponíveis para o modelo.")
                return
            
            chart_modelo = alt.Chart(modelo_count).mark_bar().encode(
                x=alt.X('modelo:N', title='Modelo', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color=alt.Color('modelo:N', title='Modelo', scale=alt.Scale(scheme='category20')),
                tooltip=['modelo', 'quantidade']
            ).properties(
                width=chart_width,
                title='Veículos Finalizados por Modelo'
            )
            st.altair_chart(chart_modelo, use_container_width=True)
        
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar os dados: {e}")

    elif dashboard == 'Termômetro de Prazo':
        st.title('Termômetro de Prazo')

        # 1. Veículos Finalizados - Prazo
        st.subheader('Veículos Finalizados - Prazo')
        prazo_df = data[['modelo', 'marca', 'dt_contrato', 'dt_finalizacao', 'prazo']].dropna()
        prazo_df['dentro_prazo'] = prazo_df.apply(lambda x: x['dt_finalizacao'] <= x['dt_contrato'] + pd.to_timedelta(x['prazo'], unit='d'), axis=1)
        prazo_count = prazo_df['dentro_prazo'].value_counts().reset_index()
        prazo_count.columns = ['Dentro do Prazo', 'Quantidade']
        chart_prazo = alt.Chart(prazo_count).mark_bar().encode(
            x=alt.X('Dentro do Prazo:N', title='Dentro do Prazo'),
            y=alt.Y('Quantidade:Q', title='Quantidade'),
            color=alt.Color('Dentro do Prazo:N', scale=alt.Scale(scheme='category10')),
            tooltip=['Dentro do Prazo', 'Quantidade']
        ).properties(
            width=chart_width,
            title='Quantidade de Veículos Dentro e Fora do Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        mes_selecionado_prazo = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_prazo_selectbox')
        data_filtrada_prazo = data[data['mes'] == mes_selecionado_prazo]
        prazo_por_marca = data_filtrada_prazo.groupby('marca')['prazo'].mean().reset_index()
        chart_prazo_marca = alt.Chart(prazo_por_marca).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=90)),
            y=alt.Y('prazo:Q', title='Prazo Médio (dias)'),
            color=alt.Color('marca:N', title='Marca', scale=alt.Scale(scheme='category20')),
            tooltip=['marca', 'prazo']
        ).properties(
            width=chart_width,
            title='Prazo Médio por Marca'
        )
        st.altair_chart(chart_prazo_marca, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor')
        mes_selecionado_calor = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_calor_selectbox')
        data_filtrada_calor = data[data['mes'] == mes_selecionado_calor]
        heatmap = data_filtrada_calor.groupby(['marca', 'modelo']).size().reset_index(name='quantidade')
        chart_calor = alt.Chart(heatmap).mark_rect().encode(
            x=alt.X('marca:N', title='Marca'),
            y=alt.Y('modelo:N', title='Modelo'),
            color=alt.Color('quantidade:Q', title='Quantidade', scale=alt.Scale(scheme='viridis')),
            tooltip=['marca', 'modelo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Mapa de Calor - Quantidade por Marca e Modelo'
        )
        st.altair_chart(chart_calor, use_container_width=True)

# Configuração inicial da AWS
configure_aws()

# Interface de Login
st.title("Área de Login")
username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if username in USERS and USERS[username] == password:
    st.session_state.user_logged_in = True
    st.session_state.user_name = username
    st.sidebar.write(f"Bem-vindo, {username.split('.')[0]}!")  # Exibe apenas o primeiro nome
else:
    if st.button("Entrar"):
        st.error("Usuário ou senha incorretos.")

if 'user_logged_in' in st.session_state and st.session_state.user_logged_in:
    # Menu Lateral
    st.sidebar.title("Navegação")
    dashboard_option = st.sidebar.radio("Escolha o Dashboard", ["Veículos Finalizados", "Termômetro de Prazo"])
    
    # Carregamento de dados
    data = load_data_from_athena()

    # Processamento e exibição dos dados
    process_and_display_data(data, dashboard_option)
else:
    st.warning("Você deve fazer login para acessar os dashboards.")



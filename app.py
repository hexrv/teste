import streamlit as st
import pandas as pd
import altair as alt
import awswrangler as wr
from datetime import datetime

# Dicionário de usuários e senha
USERS = {
    "Henri.Santos": "Carbon@2024",
    "Cassio.Luis": "Carbon@2023",
    "Rafael.Augusto": "Carbon@2022",
    "Marcelo.Alves": "Carbon@2021"
}

# Defina o usuário administrador
ADMIN_USER = "Henri.Santos"

# Função para carregar dados da AWS Athena com caching
@st.cache_data(ttl=300)  # Cache por 300 segundos (5 minutos)
def load_data_from_athena():
    query = """
    SELECT status, key, modelo, marca, dt_finalizacao, summary, issuetype, dt_contrato, prazo
    FROM awsdatacatalog.jira_sbm.vw_veiculos_finalizados
    """
    # Executa a consulta e retorna um DataFrame
    df = wr.athena.read_sql_query(query, database='jira_sbm')
    return df

# Função para processar e exibir dados
def process_and_display_data(data, dashboard):
    # Verifica se a coluna dt_finalizacao está presente
    if 'dt_finalizacao' in data.columns:
        # Converte dt_finalizacao para datetime
        data['data_finalizacao'] = pd.to_datetime(data['dt_finalizacao'], errors='coerce')
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

    elif dashboard == 'Termômetro de Prazo':
        st.title('Termômetro de Prazo')

        # 1. Veículos Finalizados - Prazo
        st.subheader('Veículos Finalizados - Prazo')
        mes_selecionado_prazo = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_prazo_selectbox')
        data_filtrada_prazo = data[data['mes'] == mes_selecionado_prazo].copy()
        data_filtrada_prazo['dentro_prazo'] = (data_filtrada_prazo['data_finalizacao'] <= data_filtrada_prazo['dt_contrato']).fillna(False)
        prazo_status = data_filtrada_prazo.groupby('dentro_prazo').size().reset_index(name='quantidade')
        prazo_status['dentro_prazo'] = prazo_status['dentro_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})
        
        chart_prazo = alt.Chart(prazo_status).mark_bar().encode(
            x=alt.X('dentro_prazo:N', title='Status do Prazo'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', title='Status do Prazo', scale=alt.Scale(scheme='category20')),
            tooltip=['dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados Dentro/Fora do Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        mes_selecionado_marca_prazo = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_marca_prazo_selectbox')
        data_filtrada_marca_prazo = data[data['mes'] == mes_selecionado_marca_prazo].copy()
        data_filtrada_marca_prazo['dentro_prazo'] = (data_filtrada_marca_prazo['data_finalizacao'] <= data_filtrada_marca_prazo['dt_contrato']).fillna(False)
        marca_prazo_status = data_filtrada_marca_prazo.groupby(['marca', 'dentro_prazo']).size().reset_index(name='quantidade')
        marca_prazo_status['dentro_prazo'] = marca_prazo_status['dentro_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})
        chart_marca_prazo = alt.Chart(marca_prazo_status).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=90)),  # Legenda do eixo x na vertical
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', title='Status do Prazo', scale=alt.Scale(scheme='category20')),
            tooltip=['marca', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Prazo por Marca'
        )
        st.altair_chart(chart_marca_prazo, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor')
        mes_selecionado_calor = st.selectbox('Selecione o Mês', data['mes'].unique(), index=list(data['mes'].unique()).index(mes_atual), key='mes_calor_selectbox')
        data_filtrada_calor = data[data['mes'] == mes_selecionado_calor].copy()
        data_filtrada_calor['dentro_prazo'] = (data_filtrada_calor['data_finalizacao'] <= data_filtrada_calor['dt_contrato']).fillna(False)
        data_filtrada_calor['semana_numero'] = (data_filtrada_calor['data_finalizacao'].dt.day - 1) // 7 + 1
        calor_data = data_filtrada_calor.groupby(['semana_numero', 'dentro_prazo']).size().reset_index(name='quantidade')
        calor_data['dentro_prazo'] = calor_data['dentro_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})
        
        chart_heatmap = alt.Chart(calor_data).mark_rect().encode(
            x=alt.X('semana_numero:O', title='Semana do Mês'),
            y=alt.Y('dentro_prazo:N', title='Status do Prazo'),
            color=alt.Color('quantidade:Q', title='Quantidade', scale=alt.Scale(scheme='reds')),
            tooltip=['semana_numero', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Mapa de Calor - Finalização Dentro/Fora do Prazo'
        )
        st.altair_chart(chart_heatmap, use_container_width=True)

# Função de login
def login():
    st.title('Plataforma de Dados')
    st.write("Por favor, faça login para acessar o sistema.")
    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')

    if st.button('Login'):
        if USERS.get(username) == password:
            st.session_state['user'] = username
            st.experimental_rerun()
        else:
            st.error('Usuário ou senha inválidos')

# Verifica o login
if 'user' not in st.session_state:
    login()
else:
    username = st.session_state['user']
    
    # Cria o menu lateral
    st.sidebar.title(f"Olá, {username.split('.')[0]}")
    dashboard = st.sidebar.radio("Selecione o dashboard desejado abaixo para visualização", ('Veículos Finalizados', 'Termômetro de Prazo'))
    
    # Exibe opções de gerenciamento se o usuário for o administrador
    if username == ADMIN_USER:
        st.sidebar.subheader('Gerenciamento e Configurações')
        st.sidebar.markdown("[Gerenciar Configurações](#)")
        st.sidebar.markdown("[Outras Opções](#)")
    
    # Carrega os dados
    data = load_data_from_athena()
    
    # Processa e exibe os dados de acordo com o dashboard selecionado
    process_and_display_data(data, dashboard)







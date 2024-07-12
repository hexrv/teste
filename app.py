import streamlit as st
import pandas as pd
import altair as alt
import awswrangler as wr
import boto3

# Dicionário de usuários
USERS = {
    "Henri.Santos": "Carbon@2024",
    "Cassio.Luis": "Carbon@2023",
    "Rafael.Augusto": "Carbon@2022",
    "Marcelo.Alves": "Carbon@2021"
}

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
    
    # Encontra o mês mais recente
    mes_mais_recente = sorted(data['mes'].unique())[-1]

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
        meses = sorted(data['mes'].unique())
        mes_selecionado = st.selectbox('Selecione o Mês', meses, index=meses.index(mes_mais_recente), key='mes_selecionado_semana')
        data_filtrada = data[data['mes'] == mes_selecionado]
        
        # Nomeia as semanas e agrupa por semana
        semanas = data_filtrada.groupby('semana_numero').size().reset_index(name='quantidade')
        semanas['semana_descricao'] = semanas['semana_numero'].apply(lambda x: f'{x}ª semana de {data_filtrada["data_finalizacao"].dt.strftime("%B %Y").iloc[0]}')
        
        chart_semanal = alt.Chart(semanas).mark_bar().encode(
            x=alt.X('semana_descricao:N', title='Semana', axis=alt.Axis(labelAngle=45)),  # Legenda do eixo x na vertical
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('semana_descricao:N', title='Semana', scale=alt.Scale(scheme='category20')),
            tooltip=['semana_descricao', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados por Semana'
        )
        st.altair_chart(chart_semanal, use_container_width=True)

        # 3. Veículos Finalizados por Marca
        st.subheader('Veículos Finalizados por Marca')
        mes_selecionado_marca = st.selectbox('Selecione o Mês', sorted(data['mes'].unique()), index=meses.index(mes_mais_recente), key='mes_selecionado_marca')
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
        mes_selecionado_modelo = st.selectbox('Selecione o Mês', sorted(data['mes'].unique()), index=meses.index(mes_mais_recente), key='mes_modelo_selectbox')
        marca_selecionada = st.selectbox('Selecione a Marca', data['marca'].unique(), key='marca_modelo_selectbox')
        data_filtrada_modelo = data[(data['mes'] == mes_selecionado_modelo) & (data['marca'] == marca_selecionada)]
        modelo_count = data_filtrada_modelo.groupby('modelo').size().reset_index(name='quantidade')
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
        mes_selecionado_prazo = st.selectbox('Selecione o Mês', data['mes'].unique(), index=meses.index(mes_mais_recente), key='mes_prazo_selectbox')
        data_filtrada_prazo = data[data['mes'] == mes_selecionado_prazo]
        data_filtrada_prazo['dentro_prazo'] = data_filtrada_prazo['data_finalizacao'] <= data_filtrada_prazo['dt_contrato']
        prazo_status = data_filtrada_prazo.groupby('dentro_prazo').size().reset_index(name='quantidade')
        prazo_status['dentro_prazo'] = prazo_status['dentro_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})
        prazo_status_chart = alt.Chart(prazo_status).mark_bar().encode(
            x=alt.X('dentro_prazo:N', title='Status'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', title='Status', scale=alt.Scale(domain=['Dentro do Prazo', 'Fora do Prazo'], range=['#1f77b4', '#ff7f0e'])),
            tooltip=['dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados Dentro e Fora do Prazo'
        )
        st.altair_chart(prazo_status_chart, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        mes_selecionado_prazo_marca = st.selectbox('Selecione o Mês', data['mes'].unique(), index=meses.index(mes_mais_recente), key='mes_prazo_marca_selectbox')
        data_filtrada_prazo_marca = data[data['mes'] == mes_selecionado_prazo_marca]
        prazo_marca_count = data_filtrada_prazo_marca.groupby(['marca', 'dentro_prazo']).size().reset_index(name='quantidade')
        prazo_marca_chart = alt.Chart(prazo_marca_count).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=45)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', title='Status', scale=alt.Scale(domain=['Dentro do Prazo', 'Fora do Prazo'], range=['#1f77b4', '#ff7f0e'])),
            tooltip=['marca', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Prazo por Marca'
        )
        st.altair_chart(prazo_marca_chart, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor')
        mes_selecionado_prazo_calor = st.selectbox('Selecione o Mês', data['mes'].unique(), index=meses.index(mes_mais_recente), key='mes_calor_selectbox')
        data_filtrada_prazo_calor = data[data['mes'] == mes_selecionado_prazo_calor]
        mapa_calor = data_filtrada_prazo_calor.groupby(['semana_descricao', 'dentro_prazo']).size().reset_index(name='quantidade')
        mapa_calor_chart = alt.Chart(mapa_calor).mark_rect().encode(
            x=alt.X('semana_descricao:N', title='Semana', axis=alt.Axis(labelAngle=45)),
            y=alt.Y('dentro_prazo:N', title='Status'),
            color=alt.Color('quantidade:Q', title='Quantidade', scale=alt.Scale(scheme='viridis')),
            tooltip=['semana_descricao', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Mapa de Calor de Prazo'
        )
        st.altair_chart(mapa_calor_chart, use_container_width=True)

# Função de login
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.sidebar.error("Credenciais inválidas")

# Função principal
def main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login()
    else:
        st.sidebar.title(f"Bem-vindo, {st.session_state.username}")
        st.sidebar.write("Navegue pelos dashboards abaixo:")

        dashboard = st.sidebar.radio("Escolha um Dashboard", ["Veículos Finalizados", "Termômetro de Prazo"])

        # Carrega os dados
        data = load_data_from_athena()

        # Processa e exibe os dados
        process_and_display_data(data, dashboard)

if __name__ == "__main__":
    main()




























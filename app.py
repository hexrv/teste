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
        semanas = sorted(data['semana_descricao'].unique())
        semana_selecionada = st.selectbox('Selecione a Semana', semanas, key='semanas_selectbox')
        data_filtrada_semana = data[data['semana_descricao'] == semana_selecionada]
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
        mes_selecionado_marca = st.selectbox('Selecione o Mês', data['mes'].unique(), key='mes_selecionado_marca')
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
        mes_selecionado_modelo = st.selectbox('Selecione o Mês', data['mes'].unique(), key='mes_modelo_selectbox')
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
        mes_selecionado_prazo = st.selectbox('Selecione o Mês', data['mes'].unique(), key='mes_prazo_selectbox')
        data_filtrada_prazo = data[data['mes'] == mes_selecionado_prazo]
        data_filtrada_prazo['dentro_prazo'] = data_filtrada_prazo['data_finalizacao'] <= data_filtrada_prazo['dt_contrato']
        prazo_status = data_filtrada_prazo.groupby('dentro_prazo').size().reset_index(name='quantidade')
        prazo_status['dentro_prazo'] = prazo_status['dentro_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})
        chart_prazo = alt.Chart(prazo_status).mark_bar().encode(
            x=alt.X('dentro_prazo:N', title='Status do Prazo', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', scale=alt.Scale(scheme='category20')),
            tooltip=['dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Veículos Finalizados - Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        data_filtrada_prazo_marca = data_filtrada_prazo.groupby(['marca', 'dentro_prazo']).size().reset_index(name='quantidade')
        prazo_por_marca_chart = alt.Chart(data_filtrada_prazo_marca).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', scale=alt.Scale(scheme='category20')),
            tooltip=['marca', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            title='Prazo por Marca'
        )
        st.altair_chart(prazo_por_marca_chart, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor')
        data_filtrada_calor = data[data['mes'] == mes_selecionado_prazo]
        data_filtrada_calor['dentro_prazo'] = data_filtrada_calor['data_finalizacao'] <= data_filtrada_calor['dt_contrato']
        heatmap_data = data_filtrada_calor.groupby(['mes', 'dentro_prazo']).size().reset_index(name='quantidade')
        heatmap_chart = alt.Chart(heatmap_data).mark_rect().encode(
            x=alt.X('mes:N', title='Mês'),
            y=alt.Y('dentro_prazo:N', title='Status do Prazo'),
            color=alt.Color('quantidade:Q', scale=alt.Scale(scheme='greenblue')),
            tooltip=['mes', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Mapa de Calor - Veículos Finalizados'
        )
        st.altair_chart(heatmap_chart, use_container_width=True)

def login_screen():
    st.title('Login')
    st.write('Por favor, faça login para acessar o sistema.')

    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')
    login_button = st.button('Entrar')

    if login_button:
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f'Bem-vindo, {username}!')
            st.experimental_rerun()
        else:
            st.error('Usuário ou senha incorretos.')

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.sidebar.title('Menu')
        menu_options = ['Veículos Finalizados', 'Termômetro de Prazo']
        choice = st.sidebar.selectbox('Selecione o Dashboard', menu_options)
        
        if choice == 'Veículos Finalizados':
            data = load_data_from_athena()
            process_and_display_data(data, 'Veículos Finalizados')
        elif choice == 'Termômetro de Prazo':
            data = load_data_from_athena()
            process_and_display_data(data, 'Termômetro de Prazo')
    else:
        login_screen()

if __name__ == '__main__':
    # Verifica e configura as credenciais da AWS
    if 'AWS_REGION' in st.secrets:
        boto3.setup_default_session(region_name=st.secrets["AWS_REGION"])
        print("Região configurada corretamente: ", st.secrets["AWS_REGION"])
    else:
        st.error("Região AWS não configurada. Verifique seu arquivo de segredos.")
    main()





















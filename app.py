import streamlit as st
import pandas as pd
import altair as alt

# Função para verificar login
def check_login(username, password):
    # Definir credenciais de login válidas
    valid_username = "admin"
    valid_password = "password123"
    return username == valid_username and password == valid_password

# Função para carregar os dados
@st.cache_data
def load_data():
    return pd.read_csv('carga.csv', delimiter=';')

# Inicializar o estado de sessão para login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# Interface de login
if not st.session_state.logged_in:
    st.title('Login para o Dashboard')

    # Campos de entrada para nome de usuário e senha
    username = st.text_input('Nome de Usuário')
    password = st.text_input('Senha', type='password')

    # Verificar credenciais
    if st.button('Entrar'):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()  # Recarregar a página após login bem-sucedido
        else:
            st.error('Nome de usuário ou senha incorretos.')
else:
    # Mostrar o nome do usuário no menu lateral
    st.sidebar.title(f'Bem-vindo, {st.session_state.username}!')

    # Selecionar o dashboard no menu lateral
    dashboard = st.sidebar.radio('Selecionar Dashboard', ['Veículos Finalizados', 'Termômetro de Prazo'])

    # Carregar os dados após login
    data = load_data()

    # Ajustar os nomes das colunas se necessário
    data.columns = [col.strip() for col in data.columns]  # Remover espaços extras dos nomes das colunas

    # Certifique-se de que as colunas têm o tipo de dado correto
    if 'Datafinalizacao' in data.columns:
        data['Datafinalizacao'] = pd.to_datetime(data['Datafinalizacao'], format='%d/%m/%Y %H:%M', dayfirst=True)
    else:
        st.error("Coluna 'Datafinalizacao' não encontrada no CSV.")

    # Renomear as colunas para facilitar o uso
    data.rename(columns={'Marca': 'marca', 'Modelo': 'modelo', 'Datafinalizacao': 'data_finalizacao'}, inplace=True)

    if dashboard == 'Veículos Finalizados':
        # Streamlit
        st.title('Dashboard de Carros Finalizados')

        # Filtros
        marca = st.selectbox('Escolha a marca', options=['Todos'] + list(data['marca'].unique()))
        if marca == 'Todos':
            modelos_selecionados = st.multiselect('Escolha os modelos', options=data['modelo'].unique())
        else:
            modelos_filtrados = data[data['marca'] == marca]['modelo'].unique()
            modelos_selecionados = st.multiselect('Escolha os modelos', options=modelos_filtrados)

        # Filtrar dados com base nos filtros aplicados
        if marca == 'Todos' and modelos_selecionados:
            filtered_data = data[data['modelo'].isin(modelos_selecionados)]
        elif marca == 'Todos':
            filtered_data = data
        elif modelos_selecionados:
            filtered_data = data[(data['marca'] == marca) & (data['modelo'].isin(modelos_selecionados))]
        else:
            filtered_data = data[data['marca'] == marca]

        # Adicionar colunas de tempo
        data['mes'] = data['data_finalizacao'].dt.to_period('M').astype(str)  # Convertendo para string para exibição
        data['semana'] = data['data_finalizacao'].dt.to_period('W').astype(str)  # Convertendo para string para exibição
        data['dia'] = data['data_finalizacao'].dt.date  # Data como objeto datetime.date

        # Contagem de finalizações
        finalizados_por_mes = data.groupby('mes').size().reset_index(name='quantidade')
        finalizados_por_semana = data.groupby('semana').size().reset_index(name='quantidade')
        finalizados_por_dia = data.groupby('dia').size().reset_index(name='quantidade')

        # Contagem de finalizações por marca
        finalizados_por_marca = data.groupby('marca').size().reset_index(name='quantidade')

        # Exibição dos dados filtrados
        st.write("Dados Filtrados")
        st.dataframe(filtered_data)

        # Gráfico de Finalizações por Mês
        st.subheader('Finalizações por Mês')
        chart_mes = alt.Chart(finalizados_por_mes).mark_bar().encode(
            x=alt.X('mes:O', title='Mês', axis=alt.Axis(labelAngle=0)),  # Ajustar ângulo dos rótulos para horizontal
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('mes:N', title='Mês'),  # Adicionar cor por mês
            tooltip=['mes', 'quantidade']
        ).properties(
            title='Quantidade de Finalizações por Mês'
        )
        st.altair_chart(chart_mes, use_container_width=True)

        # Seletor de Semana
        selected_week = st.selectbox(
            'Escolha uma semana',
            options=['Todos'] + sorted(data['semana'].unique())
        )

        # Filtrar dados para a semana selecionada
        if selected_week == 'Todos':
            filtered_data_by_week = data
        else:
            filtered_data_by_week = data[data['semana'] == selected_week]

        # Gráfico de Finalizações por Semana
        st.subheader(f'Finalizações para a Semana {selected_week}')
        chart_semana = alt.Chart(filtered_data_by_week).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Ajustar ângulo dos rótulos para horizontal
            y=alt.Y('count():Q', title='Quantidade'),
            tooltip=['marca', 'count()']
        ).properties(
            title=f'Quantidade de Finalizações para a Semana {selected_week}'
        )
        st.altair_chart(chart_semana, use_container_width=True)

        # Seletor de Data
        selected_date = st.date_input('Escolha uma data', min_value=data['dia'].min(), max_value=data['dia'].max())

        # Filtrar dados para a data selecionada
        filtered_data_by_date = data[data['dia'] == selected_date]

        # Gráfico de Finalizações por Dia
        st.subheader(f'Finalizações para o Dia {selected_date.strftime("%d/%m/%Y")}')
        chart_dia = alt.Chart(filtered_data_by_date).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Ajustar ângulo dos rótulos para horizontal
            y=alt.Y('count():Q', title='Quantidade'),
            color=alt.Color('marca:N', title='Marca'),  # Adicionar cor por marca
            tooltip=['marca', 'count()']
        ).properties(
            title=f'Quantidade de Finalizações para o Dia {selected_date.strftime("%d/%m/%Y")}'
        )
        st.altair_chart(chart_dia, use_container_width=True)

        # Gráfico de Pizza por Marca
        st.subheader('Finalizações por Marca')
        chart_marca = alt.Chart(finalizados_por_marca).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('quantidade:Q', stack=True),
            color=alt.Color('marca:N', legend=alt.Legend(title='Marca')),
            tooltip=['marca', 'quantidade']
        ).properties(
            title='Quantidade de Finalizações por Marca'
        )
        st.altair_chart(chart_marca, use_container_width=True)

    elif dashboard == 'Termômetro de Prazo':
        st.title('Termômetro de Prazo')
        st.write('Aqui você poderá visualizar o prazo de finalização dos veículos.')

        # Lógica e visualizações do Termômetro de Prazo
        # (Esta parte ainda precisa ser implementada de acordo com os requisitos específicos do Termômetro de Prazo)

        # Exemplo de gráfico temporário
        st.subheader('Exemplo de Gráfico do Termômetro de Prazo')
        example_data = pd.DataFrame({
            'Prazo': ['No prazo', 'Atrasado'],
            'Quantidade': [80, 20]
        })
        chart_prazo = alt.Chart(example_data).mark_bar().encode(
            x=alt.X('Prazo:N', title='Prazo'),
            y=alt.Y('Quantidade:Q', title='Quantidade'),
            color=alt.Color('Prazo:N', title='Prazo'),
            tooltip=['Prazo', 'Quantidade']
        ).properties(
            title='Exemplo de Termômetro de Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

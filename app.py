import streamlit as st
import pandas as pd
import altair as alt

# Função para verificar login
def check_login(username, password):
    valid_username = "admin"
    valid_password = "password123"
    return username == valid_username and password == valid_password

# Função para carregar os dados de veículos
@st.cache_data
def load_data():
    return pd.read_csv('carga.csv', delimiter=';')

# Função para carregar os dados de prazo
@st.cache_data
def load_prazo_data():
    return pd.read_csv('prazo.csv', delimiter=';')

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

    if dashboard == 'Veículos Finalizados':
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
        data['ano'] = data['data_finalizacao'].dt.year  # Adicionar coluna de ano

        # Contagem de finalizações
        finalizados_por_mes = data.groupby('mes').size().reset_index(name='quantidade')
        finalizados_por_semana = data.groupby('semana').size().reset_index(name='quantidade')
        finalizados_por_dia = data.groupby('dia').size().reset_index(name='quantidade')
        finalizados_por_ano = data.groupby('ano').size().reset_index(name='quantidade')  # Contagem por ano
        finalizados_por_marca = data.groupby('marca').size().reset_index(name='quantidade')
        finalizados_por_marca_modelo = data.groupby(['marca', 'modelo']).size().reset_index(name='quantidade')  # Contagem por marca e modelo

        # Exibição dos dados filtrados
        st.write("Dados Filtrados")
        st.dataframe(filtered_data)

        # Gráfico de Finalizações por Mês
        st.subheader('Finalizações por Mês')
        chart_mes = alt.Chart(finalizados_por_mes).mark_bar().encode(
            x=alt.X('mes:O', title='Mês', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('mes:N', title='Mês'),
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
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
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
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
            y=alt.Y('count():Q', title='Quantidade'),
            color=alt.Color('marca:N', title='Marca'),
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

        # Gráfico de Finalizações por Ano
        st.subheader('Finalizações por Ano')
        chart_ano = alt.Chart(finalizados_por_ano).mark_bar().encode(
            x=alt.X('ano:O', title='Ano', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('ano:N', title='Ano'),
            tooltip=['ano', 'quantidade']
        )
        st.altair_chart(chart_ano, use_container_width=True)

        # Gráfico de Finalizações por Marca e Modelo
        st.subheader('Finalizações por Marca e Modelo')
        chart_marca_modelo = alt.Chart(finalizados_por_marca_modelo).mark_bar().encode(
            x=alt.X('marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('modelo:N', title='Modelo'),
            tooltip=['marca', 'modelo', 'quantidade']
        ).properties(
            title='Quantidade de Finalizações por Marca e Modelo'
        )
        st.altair_chart(chart_marca_modelo, use_container_width=True)

        # Média de Tempo de Finalização por Marca
        st.subheader('Média de Tempo de Finalização por Marca')
        data['tempo_finalizacao'] = (data['data_finalizacao'] - data['data_finalizacao'].min()).dt.days
        media_tempo_finalizacao = data.groupby('marca')['tempo_finalizacao'].mean().reset_index()
        media_tempo_finalizacao.columns = ['Marca', 'Tempo Médio (dias)']
        chart_tempo_medio = alt.Chart(media_tempo_finalizacao).mark_bar().encode(
            x=alt.X('Marca:N', title='Marca', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
            y=alt.Y('Tempo Médio (dias):Q', title='Tempo Médio (dias)'),
            color='Marca:N',
            tooltip=['Marca', 'Tempo Médio (dias)']
        ).properties(
            title='Tempo Médio de Finalização por Marca'
        )
        st.altair_chart(chart_tempo_medio, use_container_width=True)

    elif dashboard == 'Termômetro de Prazo':
        # Carregar os dados de prazo
        prazo_data = load_prazo_data()

        # Remover espaços extras dos nomes das colunas
        prazo_data.columns = [col.strip() for col in prazo_data.columns]

        # Verificar se o CSV contém as colunas esperadas
        expected_columns = ['Resumo', 'Datacontrato', 'Marca', 'Modelo', 'Datafinalizacao', 'prazo']
        missing_columns = [col for col in expected_columns if col not in prazo_data.columns]
        if missing_columns:
            st.error(f"Colunas ausentes no CSV: {', '.join(missing_columns)}")
        else:
            # Verificar se as colunas estão no formato correto
            prazo_data['Datafinalizacao'] = pd.to_datetime(prazo_data['Datafinalizacao'], format='%d/%m/%Y %H:%M', errors='coerce')
            prazo_data['Datacontrato'] = pd.to_datetime(prazo_data['Datacontrato'], format='%d/%m/%Y', errors='coerce')
            prazo_data['prazo'] = pd.to_numeric(prazo_data['prazo'], errors='coerce')

            # Adicionar coluna de status
            prazo_data['status'] = prazo_data.apply(
                lambda row: 'Dentro do Prazo' if pd.notna(row['prazo']) and pd.notna(row['Datacontrato']) and pd.notna(row['Datafinalizacao']) and row['Datafinalizacao'] <= row['Datacontrato'] + pd.Timedelta(days=row['prazo'])
                else 'Fora do Prazo' if pd.notna(row['prazo']) and pd.notna(row['Datacontrato']) and pd.notna(row['Datafinalizacao']) and row['Datafinalizacao'] > row['Datacontrato'] + pd.Timedelta(days=row['prazo'])
                else 'Antecipado' if pd.notna(row['Datacontrato']) and pd.notna(row['Datafinalizacao']) and row['Datafinalizacao'] < row['Datacontrato']
                else 'Indeterminado', axis=1
            )

            # Contagem de status
            status_counts = prazo_data['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'quantidade']

            # Gráfico de barras dos status
            st.subheader('Termômetro de Prazo')
            chart_status = alt.Chart(status_counts).mark_bar().encode(
                x=alt.X('status:N', title='Status', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color='status:N',
                tooltip=['status', 'quantidade']
            ).properties(
                title='Quantidade de Veículos por Status'
            )
            st.altair_chart(chart_status, use_container_width=True)

            # Adicionar coluna de mês para filtrar os dados
            prazo_data['mes'] = prazo_data['Datafinalizacao'].dt.to_period('M').astype(str)

            # Seletor de mês
            selected_month = st.selectbox(
                'Escolha um mês',
                options=sorted(prazo_data['mes'].unique())
            )

            # Filtrar dados pelo mês selecionado
            filtered_data_by_month = prazo_data[prazo_data['mes'] == selected_month]

            # Contagem de status por mês
            status_counts_month = filtered_data_by_month['status'].value_counts().reset_index()
            status_counts_month.columns = ['status', 'quantidade']

            # Gráfico de barras dos status por mês
            st.subheader(f'Termômetro de Prazo para {selected_month}')
            chart_status_month = alt.Chart(status_counts_month).mark_bar().encode(
                x=alt.X('status:N', title='Status', axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color='status:N',
                tooltip=['status', 'quantidade']
            ).properties(
                title=f'Quantidade de Veículos por Status em {selected_month}'
            )
            st.altair_chart(chart_status_month, use_container_width=True)

            # Distribuição dos Prazos
            st.subheader('Distribuição dos Prazos')
            prazo_data['prazo'] = prazo_data['prazo'].fillna(0)  # Preencher valores ausentes com 0 para o histograma
            chart_distribuicao_prazos = alt.Chart(prazo_data).mark_bar().encode(
                x=alt.X('prazo:Q', title='Prazo (dias)', bin=alt.Bin(maxbins=30)),
                y=alt.Y('count():Q', title='Quantidade'),
                tooltip=['prazo:Q', 'count()']
            ).properties(
                title='Distribuição dos Prazos'
            )
            st.altair_chart(chart_distribuicao_prazos, use_container_width=True)

            # Comparação de Prazos por Marca
            st.subheader('Comparação de Prazos por Marca')
            prazo_marca_media = prazo_data.groupby('Marca')['prazo'].mean().reset_index()
            prazo_marca_media.columns = ['Marca', 'Prazo Médio (dias)']
            chart_prazos_marca = alt.Chart(prazo_marca_media).mark_bar().encode(
                x=alt.X('Marca:N', title='Marca', axis=alt.Axis(labelAngle=90)),  # Rótulos verticais
                y=alt.Y('Prazo Médio (dias):Q', title='Prazo Médio (dias)'),
                color='Marca:N',
                tooltip=['Marca', 'Prazo Médio (dias)']
            ).properties(
                title='Comparação de Prazos Médios por Marca'
            )
            st.altair_chart(chart_prazos_marca, use_container_width=True)

            # Evolução dos Status ao Longo do Tempo
            st.subheader('Evolução dos Status ao Longo do Tempo')
            prazo_data['ano_mes'] = prazo_data['Datafinalizacao'].dt.to_period('M').astype(str)
            status_counts_time = prazo_data.groupby(['ano_mes', 'status']).size().reset_index(name='quantidade')
            chart_evolucao_status = alt.Chart(status_counts_time).mark_line().encode(
                x=alt.X('ano_mes:O', title='Ano e Mês', axis=alt.Axis(labelAngle=45)),
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color='status:N',
                tooltip=['ano_mes', 'status', 'quantidade']
            ).properties(
                title='Evolução dos Status ao Longo do Tempo'
            )
            st.altair_chart(chart_evolucao_status, use_container_width=True)




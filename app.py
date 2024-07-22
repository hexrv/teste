import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import awswrangler as wr

# Configurações iniciais
st.set_page_config(page_title="Dashboard de Veículos e Kits", layout="wide")

# Função para autenticação
def authenticate(username, password):
    return username == "henri.santos" and password == "Carbon@2024"

# Exibir a tela de login
def show_login():
    st.title("Plataforma de Dados")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("Login successful")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# Verificar autenticação
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login()
else:
    # Conexão com a fonte de dados
    @st.cache_resource
    def get_veiculos_data():
        query = "SELECT * FROM vw_veiculos_finalizados"
        df = wr.athena.read_sql_query(query, database="jira_sbm")
        return df

    @st.cache_resource
    def get_kits_data():
        query = "SELECT * FROM vw_vidros_kits"
        df = wr.athena.read_sql_query(query, database="jira_sbm")
        return df

    veiculos_data = get_veiculos_data()
    kits_data = get_kits_data()

    # Processamento e exibição dos dados
    def process_and_display_data(data, kits_data):
        # Processamento dos dados de veículos
        if 'dt_finalizacao' in data.columns:
            data['dt_finalizacao'] = pd.to_datetime(data['dt_finalizacao'], errors='coerce')
            data.dropna(subset=['dt_finalizacao'], inplace=True)
        else:
            st.error("Coluna 'dt_finalizacao' não encontrada na tabela de veículos.")
            return
        
        # Processamento dos dados de kits
        if 'dt_faturado' in kits_data.columns:
            kits_data['dt_faturado'] = pd.to_datetime(kits_data['dt_faturado'], errors='coerce')
            kits_data.dropna(subset=['dt_faturado'], inplace=True)
        else:
            st.error("Coluna 'dt_faturado' não encontrada na tabela de kits.")
            return

        kits_data['mes'] = kits_data['dt_faturado'].dt.to_period('M').astype(str)
        kits_data['semana'] = kits_data['dt_faturado'].dt.to_period('W').astype(str)
        kits_data['dia'] = kits_data['dt_faturado'].dt.date
        kits_data['ano'] = kits_data['dt_faturado'].dt.year
        kits_data['semana_numero'] = (kits_data['dt_faturado'].dt.day - 1) // 7 + 1
        kits_data['semana_descricao'] = kits_data['dt_faturado'].dt.strftime('%B %Y') + ' - Semana ' + kits_data['semana_numero'].astype(str)
        mes_atual = datetime.now().strftime('%Y-%m')

        return kits_data, mes_atual

    kits_data, mes_atual = process_and_display_data(veiculos_data, kits_data)

    # Configurações dos dashboards
    st.sidebar.title(f"Bem-vindo, {st.session_state.username.split('.')[0].capitalize()}")
    dashboard = st.sidebar.selectbox("Selecione o Dashboard", ["Veículos Finalizados", "Termômetro de Prazo", "Kits Faturados"])

    chart_width = 800  # Largura dos gráficos
    chart_height = 400  # Altura dos gráficos

    if dashboard == "Veículos Finalizados":
        st.title("Veículos Finalizados")

        # 1. Veículos Finalizados por Mês
        st.subheader('Veículos Finalizados por Mês')
        veiculos_por_mes = veiculos_data.groupby(veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str)).size().reset_index(name='quantidade')
        chart_veiculos_mes = alt.Chart(veiculos_por_mes).mark_bar().encode(
            x=alt.X('dt_finalizacao:N', title='Mês', axis=alt.Axis(labelAngle=0)),  # Define o ângulo das labels do eixo X
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dt_finalizacao:N', title='Mês'),
            tooltip=['dt_finalizacao', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Veículos Finalizados por Mês'
        )
        st.altair_chart(chart_veiculos_mes, use_container_width=True)

        # 2. Selecione o Mês para Veículos Finalizados por Semana
        st.subheader('Veículos Finalizados por Semana')
        mes_selecionado = st.selectbox('Selecione o Mês', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique())
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_selecionado = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado]
        veiculos_mes_selecionado['semana'] = veiculos_mes_selecionado['dt_finalizacao'].dt.to_period('W').astype(str)
        veiculos_mes_selecionado['numero_semana'] = (veiculos_mes_selecionado['dt_finalizacao'].dt.day - 1) // 7 + 1
        veiculos_mes_selecionado['semana_descricao'] = veiculos_mes_selecionado['numero_semana'].astype(str) + 'ª Semana'

        # Contagem de veículos por semana
        veiculos_por_semana = veiculos_mes_selecionado.groupby('semana_descricao').size().reset_index(name='quantidade')
        veiculos_por_semana = veiculos_por_semana.sort_values('semana_descricao')

        chart_veiculos_semana = alt.Chart(veiculos_por_semana).mark_bar().encode(
            x=alt.X('semana_descricao:N', title='Semana', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('semana_descricao:N', title='Semana'),
            tooltip=['semana_descricao', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Veículos Finalizados por Semana ({mes_selecionado})'
        )
        st.altair_chart(chart_veiculos_semana, use_container_width=True)

        # 3. Veículos Finalizados por Marca
        st.subheader('Veículos Finalizados por Marca')
        mes_selecionado_marca = st.selectbox('Selecione o Mês para Verificar as Marcas', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique())
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_marca = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_marca]
        veiculos_por_marca = veiculos_mes_marca.groupby('marca').size().reset_index(name='quantidade')
        veiculos_por_marca = veiculos_por_marca.sort_values('quantidade', ascending=False)

        chart_veiculos_marca = alt.Chart(veiculos_por_marca).mark_bar().encode(
            x=alt.X('marca:N', title='Marca'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('marca:N', title='Marca'),
            tooltip=['marca', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Veículos Finalizados por Marca ({mes_selecionado_marca})'
        )
        st.altair_chart(chart_veiculos_marca, use_container_width=True)

        # 4. Veículos Finalizados por Modelo
        st.subheader('Veículos Finalizados por Modelo')
        mes_selecionado_modelo = st.selectbox('Selecione o Mês', veiculos_data['mes'].unique(), index=list(veiculos_data['mes'].unique()).index(mes_atual), key='mes_modelo_selectbox')
        marca_selecionada = st.selectbox('Selecione a Marca', veiculos_data['marca'].unique(), key='marca_modelo_selectbox')
        data_filtrada_modelo = veiculos_data[(veiculos_data['mes'] == mes_selecionado_modelo) & (veiculos_data['marca'] == marca_selecionada)]
        
        if data_filtrada_modelo.empty:
            st.warning("Não há dados disponíveis para a combinação selecionada de mês e marca.")
        else:
            veiculos_por_modelo = data_filtrada_modelo.groupby('modelo').size().reset_index(name='quantidade')
            chart_veiculos_modelo = alt.Chart(veiculos_por_modelo).mark_bar().encode(
                x=alt.X('modelo:N', title='Modelo',axis=alt.Axis(labelAngle=0)),
                y=alt.Y('quantidade:Q', title='Quantidade'),
                color=alt.Color('modelo:N', title='Modelo'),
                tooltip=['modelo', 'quantidade']
            ).properties(
                width=chart_width,
                height=chart_height,
                title=f'Veículos Finalizados por Modelo ({mes_selecionado_modelo} - {marca_selecionada})'
            )
            st.altair_chart(chart_veiculos_modelo, use_container_width=True)

    elif dashboard == "Termômetro de Prazo":
        st.title("Termômetro de Prazo")

        # 1. Veículos Finalizados - Prazo
        st.subheader('Veículos Finalizados - Prazo')
        veiculos_data['no_prazo'] = veiculos_data['dt_finalizacao'] <= veiculos_data['dt_contrato']
        veiculos_prazo = veiculos_data.groupby('no_prazo').size().reset_index(name='quantidade')
        veiculos_prazo['Prazo'] = veiculos_prazo['no_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})

        chart_prazo = alt.Chart(veiculos_prazo).mark_bar().encode(
            x=alt.X('Prazo:N', title='Prazo'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('Prazo:N', title='Prazo'),
            tooltip=['Prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Veículos Finalizados - Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        mes_selecionado_prazo = st.selectbox('Selecione o Mês para Verificar o Prazo por Marca', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique(), key='mes_prazo_selectbox')
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_prazo = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_prazo]
        veiculos_mes_prazo['no_prazo'] = veiculos_mes_prazo['dt_finalizacao'] <= veiculos_mes_prazo['dt_contrato']
        veiculos_prazo_marca = veiculos_mes_prazo.groupby(['marca', 'no_prazo']).size().reset_index(name='quantidade')
        veiculos_prazo_marca['Prazo'] = veiculos_prazo_marca['no_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})

        chart_prazo_marca = alt.Chart(veiculos_prazo_marca).mark_bar().encode(
            x=alt.X('marca:N', title='Marca'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('Prazo:N', title='Prazo'),
            tooltip=['marca', 'Prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Prazo por Marca ({mes_selecionado_prazo})'
        )
        st.altair_chart(chart_prazo_marca, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor')
        mes_selecionado_mapa_calor = st.selectbox('Selecione o Mês para Verificar o Mapa de Calor', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique(), key='mes_mapa_calor_selectbox')
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_mapa_calor = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_mapa_calor]
        veiculos_mes_mapa_calor['dia'] = veiculos_mes_mapa_calor['dt_finalizacao'].dt.day
        veiculos_mes_mapa_calor['no_prazo'] = veiculos_mes_mapa_calor['dt_finalizacao'] <= veiculos_mes_mapa_calor['dt_contrato']
        veiculos_mapa_calor = veiculos_mes_mapa_calor.groupby(['dia', 'no_prazo']).size().reset_index(name='quantidade')
        veiculos_mapa_calor['Prazo'] = veiculos_mapa_calor['no_prazo'].map({True: 'Dentro do Prazo', False: 'Fora do Prazo'})

        chart_mapa_calor = alt.Chart(veiculos_mapa_calor).mark_rect().encode(
            x=alt.X('dia:O', title='Dia'),
            y=alt.Y('Prazo:N', title='Prazo'),
            color=alt.Color('quantidade:Q', title='Quantidade'),
            tooltip=['dia', 'Prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Mapa de Calor ({mes_selecionado_mapa_calor})'
        )
        st.altair_chart(chart_mapa_calor, use_container_width=True)

    elif dashboard == "Kits Faturados":
        st.title("Kits Faturados")

        # 1. Kits Terminados - Atual
        kits_terminados_atual = kits_data[kits_data['mes'] == mes_atual]['key'].nunique()

        # 2. Kits Faturados - D-1
        dia_anterior = (datetime.now() - pd.Timedelta(days=1)).date()
        kits_faturados_d1 = kits_data[kits_data['dia'] == dia_anterior]['key'].nunique()

        # 3. Kits Faturados - Semana Atual
        semana_atual = kits_data[kits_data['dt_faturado'].dt.isocalendar().week == datetime.now().isocalendar()[1]]
        kits_faturados_semana_atual = semana_atual['key'].nunique()

        # 4. Kits Faturados - Mês Atual
        kits_faturados_mes_atual = kits_data[kits_data['mes'] == mes_atual]['key'].nunique()

        # Exibição dos cards lado a lado
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"### Kits Terminados - Atual\n# {kits_terminados_atual}")

        with col2:
            st.markdown(f"### Kits Faturados - D-1\n# {kits_faturados_d1}")

        with col3:
            st.markdown(f"### Kits Faturados - Semana Atual\n# {kits_faturados_semana_atual}")

        with col4:
            st.markdown(f"### Kits Faturados - Mês Atual\n# {kits_faturados_mes_atual}")

        # Outros gráficos para "Kits Faturados"
        # 2. Selecione o Mês para Veículos Finalizados por Semana
        st.subheader('Kits Finalizados por Semana')
        mes_selecionado = st.selectbox('Selecione o Mês', kits_data['dt_faturado'].dt.to_period('M').astype(str).unique())
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_selecionado = kits_data[kits_data['dt_faturado'].dt.to_period('M').astype(str) == mes_selecionado]
        veiculos_mes_selecionado['semana'] = veiculos_mes_selecionado['dt_faturado'].dt.to_period('W').astype(str)
        veiculos_mes_selecionado['numero_semana'] = (veiculos_mes_selecionado['dt_faturado'].dt.day - 1) // 7 + 1
        veiculos_mes_selecionado['semana_descricao'] = veiculos_mes_selecionado['numero_semana'].astype(str) + 'ª Semana'

        # Contagem de veículos por semana
        veiculos_por_semana = veiculos_mes_selecionado.groupby('semana_descricao').size().reset_index(name='quantidade')
        veiculos_por_semana = veiculos_por_semana.sort_values('semana_descricao')

        chart_veiculos_semana = alt.Chart(veiculos_por_semana).mark_bar().encode(
            x=alt.X('semana_descricao:N', title='Semana', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('semana_descricao:N', title='Semana'),
            tooltip=['semana_descricao', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Kits Finalizados por Semana ({mes_selecionado})'
        )
        st.altair_chart(chart_veiculos_semana, use_container_width=True)

        
    



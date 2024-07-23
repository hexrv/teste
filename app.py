import streamlit as st
import pandas as pd
import altair as alt
import awswrangler as wr
from datetime import datetime
import boto3

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
    # Obter a região dos segredos
    region = st.secrets["aws_region"]
    
    # Conexão com a fonte de dados
    @st.cache_resource
    def get_veiculos_data():
        query = "SELECT * FROM vw_veiculos_finalizados"
        df = wr.athena.read_sql_query(query, database="jira_sbm", ctas_approach=False, boto3_session=boto3.Session(region_name=region))
        return df

    @st.cache_resource
    def get_kits_data():
        query = "SELECT * FROM vw_vidros_kits"
        df = wr.athena.read_sql_query(query, database="jira_sbm", ctas_approach=False, boto3_session=boto3.Session(region_name=region))
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
        
        # Adiciona colunas de tempo
        data['mes'] = data['dt_finalizacao'].dt.to_period('M').astype(str)
        data['semana'] = data['dt_finalizacao'].dt.to_period('W').astype(str)
        data['dia'] = data['dt_finalizacao'].dt.date
        data['ano'] = data['dt_finalizacao'].dt.to_period('a').astype(str)
        
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
        mes_selecionado_modelo = st.selectbox('Selecione o Mês para Verificar os Modelos', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique())
        
        # Filtrando os dados pelo mês selecionado
        veiculos_mes_modelo = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_modelo]
        veiculos_por_modelo = veiculos_mes_modelo.groupby('modelo').size().reset_index(name='quantidade')
        veiculos_por_modelo = veiculos_por_modelo.sort_values('quantidade', ascending=False)

        chart_veiculos_modelo = alt.Chart(veiculos_por_modelo).mark_bar().encode(
            x=alt.X('modelo:N', title='Modelo'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('modelo:N', title='Modelo'),
            tooltip=['modelo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Veículos Finalizados por Modelo ({mes_selecionado_modelo})'
        )
        st.altair_chart(chart_veiculos_modelo, use_container_width=True)

    elif dashboard == "Termômetro de Prazo":
        st.title("Termômetro de Prazo")

        # 1. Veículos Finalizados - Prazo
        st.subheader('Veículos Finalizados - Prazo')
        prazo_data = veiculos_data.copy()
        prazo_data['dentro_prazo'] = prazo_data['dt_finalizacao'] <= prazo_data['dt_contrato']
        prazo_summary = prazo_data['dentro_prazo'].value_counts().reset_index()
        prazo_summary.columns = ['Dentro do Prazo', 'Quantidade']

        chart_prazo = alt.Chart(prazo_summary).mark_bar().encode(
            x=alt.X('Dentro do Prazo:N', title='Dentro do Prazo'),
            y=alt.Y('Quantidade:Q', title='Quantidade'),
            color=alt.Color('Dentro do Prazo:N', title='Dentro do Prazo'),
            tooltip=['Dentro do Prazo', 'Quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Quantidade de Veículos Dentro e Fora do Prazo'
        )
        st.altair_chart(chart_prazo, use_container_width=True)

        # 2. Prazo por Marca
        st.subheader('Prazo por Marca')
        mes_selecionado_prazo = st.selectbox('Selecione o Mês para Verificar Prazo por Marca', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique())
        
        # Filtrando os dados pelo mês selecionado
        prazo_mes_marca = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_prazo]
        prazo_mes_marca['dentro_prazo'] = prazo_mes_marca['dt_finalizacao'] <= prazo_mes_marca['dt_contrato']
        prazo_por_marca = prazo_mes_marca.groupby(['marca', 'dentro_prazo']).size().reset_index(name='quantidade')

        chart_prazo_marca = alt.Chart(prazo_por_marca).mark_bar().encode(
            x=alt.X('marca:N', title='Marca'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('dentro_prazo:N', title='Dentro do Prazo'),
            tooltip=['marca', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Prazo por Marca ({mes_selecionado_prazo})'
        )
        st.altair_chart(chart_prazo_marca, use_container_width=True)

        # 3. Mapa de Calor
        st.subheader('Mapa de Calor - Prazo')
        mes_selecionado_heatmap = st.selectbox('Selecione o Mês para o Mapa de Calor', veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str).unique())

        # Filtrando os dados pelo mês selecionado
        prazo_mes_heatmap = veiculos_data[veiculos_data['dt_finalizacao'].dt.to_period('M').astype(str) == mes_selecionado_heatmap]
        prazo_mes_heatmap['dentro_prazo'] = prazo_mes_heatmap['dt_finalizacao'] <= prazo_mes_heatmap['dt_contrato']
        prazo_heatmap = prazo_mes_heatmap.groupby(['dia', 'marca', 'dentro_prazo']).size().reset_index(name='quantidade')

        chart_heatmap = alt.Chart(prazo_heatmap).mark_rect().encode(
            x=alt.X('marca:N', title='Marca'),
            y=alt.Y('dia:T', title='Data'),
            color=alt.Color('quantidade:Q', title='Quantidade'),
            tooltip=['marca', 'dia', 'dentro_prazo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title=f'Mapa de Calor - Prazo ({mes_selecionado_heatmap})'
        )
        st.altair_chart(chart_heatmap, use_container_width=True)

    elif dashboard == "Kits Faturados":
        st.title("Kits Faturados")

        # 1. Cards de Kits Faturados
        st.subheader('Cards de Kits Faturados')
        st.write(f"**Kits Terminados - Atual:** {kits_data[kits_data['dt_faturado'] == kits_data['dt_faturado'].max()].shape[0]}")
        st.write(f"**Kits Faturados - D-1:** {kits_data[kits_data['dt_faturado'] == (kits_data['dt_faturado'].max() - pd.DateOffset(days=1))].shape[0]}")
        st.write(f"**Kits Faturados - Semana Atual:** {kits_data[kits_data['semana_descricao'] == datetime.now().strftime('%B %Y - Semana %W')].shape[0]}")
        st.write(f"**Kits Faturados - Mês Atual:** {kits_data[kits_data['mes'] == mes_atual].shape[0]}")

        # 2. Gráficos de Kits Faturados
        st.subheader('Kits Faturados por Dia')
        kits_por_dia = kits_data.groupby('dia').size().reset_index(name='quantidade')
        chart_kits_dia = alt.Chart(kits_por_dia).mark_line().encode(
            x=alt.X('dia:T', title='Data'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            tooltip=['dia', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Faturados por Dia'
        )
        st.altair_chart(chart_kits_dia, use_container_width=True)

        st.subheader('Kits Faturados por Semana')
        kits_por_semana = kits_data.groupby('semana_descricao').size().reset_index(name='quantidade')
        chart_kits_semana = alt.Chart(kits_por_semana).mark_line().encode(
            x=alt.X('semana_descricao:N', title='Semana'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            tooltip=['semana_descricao', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Faturados por Semana'
        )
        st.altair_chart(chart_kits_semana, use_container_width=True)

        st.subheader('Kits Faturados por Mês')
        kits_por_mes = kits_data.groupby('mes').size().reset_index(name='quantidade')
        chart_kits_mes = alt.Chart(kits_por_mes).mark_line().encode(
            x=alt.X('mes:N', title='Mês'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            tooltip=['mes', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Faturados por Mês'
        )
        st.altair_chart(chart_kits_mes, use_container_width=True)

        st.subheader('Kits Faturados por Tipo de Blindagem')
        kits_por_tipo_blindagem = kits_data.groupby('tipo_blindagem').size().reset_index(name='quantidade')
        chart_kits_tipo_blindagem = alt.Chart(kits_por_tipo_blindagem).mark_bar().encode(
            x=alt.X('tipo_blindagem:N', title='Tipo de Blindagem'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('tipo_blindagem:N', title='Tipo de Blindagem'),
            tooltip=['tipo_blindagem', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Faturados por Tipo de Blindagem'
        )
        st.altair_chart(chart_kits_tipo_blindagem, use_container_width=True)

        st.subheader('Kits Faturados por Veículos')
        kits_por_veiculo = kits_data.groupby('veiculo_marca_modelo').size().reset_index(name='quantidade')
        chart_kits_veiculo = alt.Chart(kits_por_veiculo).mark_bar().encode(
            x=alt.X('veiculo_marca_modelo:N', title='Veículo'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            color=alt.Color('veiculo_marca_modelo:N', title='Veículo'),
            tooltip=['veiculo_marca_modelo', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Faturados por Veículos'
        )
        st.altair_chart(chart_kits_veiculo, use_container_width=True)

        st.subheader('Kits Acumulados')
        kits_acumulados = kits_data.groupby('dt_faturado').size().cumsum().reset_index(name='quantidade')
        chart_kits_acumulados = alt.Chart(kits_acumulados).mark_line().encode(
            x=alt.X('dt_faturado:T', title='Data'),
            y=alt.Y('quantidade:Q', title='Quantidade'),
            tooltip=['dt_faturado', 'quantidade']
        ).properties(
            width=chart_width,
            height=chart_height,
            title='Kits Acumulados'
        )
        st.altair_chart(chart_kits_acumulados, use_container_width=True)

        
    



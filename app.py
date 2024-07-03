import streamlit as st
import pandas as pd
import datetime

# Carregar dados do CSV com o delimitador correto
@st.cache_data
def load_data():
    return pd.read_csv('carga.csv', delimiter=';')  # Usando ';' como delimitador

data = load_data()

# Verificar os nomes das colunas
st.write("Nomes das Colunas:", data.columns.tolist())

# Ajustar os nomes das colunas se necessário
data.columns = [col.strip() for col in data.columns]  # Remover espaços extras dos nomes das colunas

# Certifique-se de que as colunas têm o tipo de dado correto
if 'Datafinalizacao' in data.columns:
    # Converter a coluna Datafinalizacao para datetime especificando o formato correto
    data['Datafinalizacao'] = pd.to_datetime(data['Datafinalizacao'], format='%d/%m/%Y %H:%M', dayfirst=True)
else:
    st.error("Coluna 'Datafinalizacao' não encontrada no CSV.")

# Renomear as colunas para facilitar o uso
data.rename(columns={'Marca': 'marca', 'Modelo': 'modelo', 'Datafinalizacao': 'data_finalizacao'}, inplace=True)

# Streamlit
st.title('Dashboard de Carros Finalizados')

# Filtros
marca = st.selectbox('Escolha a marca', options=data['marca'].unique())
modelos_filtrados = data[data['marca'] == marca]['modelo'].unique()
modelo = st.selectbox('Escolha o modelo', options=modelos_filtrados if len(modelos_filtrados) > 0 else [])

filtered_data = data[(data['marca'] == marca) & (data['modelo'] == modelo)]

# Adicionar colunas de tempo
data['mes'] = data['data_finalizacao'].dt.to_period('M')
data['semana'] = data['data_finalizacao'].dt.to_period('W')
data['dia'] = data['data_finalizacao'].dt.date

# Contagem de finalizações
finalizados_por_mes = data.groupby('mes').size()
finalizados_por_semana = data.groupby('semana').size()
finalizados_por_dia = data.groupby('dia').size()

# Exibição dos dados filtrados
st.write("Dados Filtrados")
st.dataframe(filtered_data)

# Exibição dos gráficos
st.subheader('Finalizações por Mês')
st.line_chart(finalizados_por_mes)

st.subheader('Finalizações por Semana')
st.line_chart(finalizados_por_semana)

st.subheader('Finalizações por Dia')
st.line_chart(finalizados_por_dia)







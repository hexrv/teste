import streamlit as st
import pandas as pd
import altair as alt

# Carregar dados do CSV com o delimitador correto
@st.cache_data
def load_data():
    return pd.read_csv('carga.csv', delimiter=';')

data = load_data()

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
modelos_selecionados = st.multiselect('Escolha os modelos', options=modelos_filtrados)

# Filtrar dados com base nos modelos selecionados
if modelos_selecionados:
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
    options=sorted(data['semana'].unique())
)

# Filtrar dados para a semana selecionada
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


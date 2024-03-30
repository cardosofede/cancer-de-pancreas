import streamlit as st
import pandas as pd

from graphs import create_ultima_linea_graph, create_ps_counts_graph, create_schema_plp_graph, create_line_plp_graph, \
    create_percentage_completion_graph, create_overall_survival_by_schema_graph, create_overall_survival_by_ps_graph

st.set_page_config(layout="wide")


def analyze_end_line(row):
    # Convert to datetime, errors='coerce' will turn invalid parsing into NaT
    row = row.apply(lambda x: pd.to_datetime(x, errors='coerce') if pd.api.types.is_string_dtype(x) else x)

    if pd.notna(row["4L_Fecha inicio"]):
        return 4
    elif pd.notna(row["3L_Fecha inicio"]):
        return 3
    elif pd.notna(row["2L_Fecha inicio"]):
        return 2
    elif pd.notna(row["1L_Fecha inicio"]):
        return 1
    else:
        return 0

def process_data(df):
    # Process data here
    df["4L_fecha_inicio"] = pd.to_datetime(df["4L_Fecha inicio"], errors="coerce")
    df["3L_fecha_inicio"] = pd.to_datetime(df["3L_Fecha inicio"], errors="coerce")
    df["2L_fecha_inicio"] = pd.to_datetime(df["2L_Fecha inicio"], errors="coerce")
    df["1L_fecha_inicio"] = pd.to_datetime(df["1L_Fecha inicio"], errors="coerce")

    df["4L_fecha_progresion"] = pd.to_datetime(df["4L_Fecha progresión"], errors="coerce")
    df["3L_fecha_progresion"] = pd.to_datetime(df["3L_Fecha progresión"], errors="coerce")
    df["2L_fecha_progresion"] = pd.to_datetime(df["2L_Fecha progresión"], errors="coerce")
    df["1L_fecha_progresion"] = pd.to_datetime(df["1L_Fecha progresión"], errors="coerce")
    df["fecha_fallecimiento"] = pd.to_datetime(df["Fecha Fallecimiento"], errors="coerce")
    df["ultima_linea"] = df.apply(analyze_end_line, axis=1)
    df = df[df["ultima_linea"] > 0]
    # Replace 'df' with your DataFrame's name
    for i in range(1, 5):  # Assuming you have up to 4L
        inicio_col = f"{i}L_fecha_inicio"
        progresion_col = f"{i}L_fecha_progresion"
        plp_col = f"{i}L_PLP"

        df[plp_col] = (df[progresion_col] - df[inicio_col]).dt.days

    filtered_df = df[df['fecha_fallecimiento'].notna()]
    df["is_dead"] = df['fecha_fallecimiento'].notna()
    df["overall_survival"] = 0
    df.loc[filtered_df.index, 'overall_survival'] = (filtered_df['fecha_fallecimiento'] - filtered_df['1L_fecha_inicio']).dt.days

    return df
# File uploader
st.title("Patient Treatment Data Analysis")
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, header=1)
    df = process_data(df)
    st.write(df)

    # Assuming '1L_' is a datetime column in your DataFrame
    if '1L_fecha_inicio' in df.columns:
        # Convert to datetime if not already
        df['1L_fecha_inicio'] = pd.to_datetime(df['1L_fecha_inicio'], errors='coerce')

        # Date Range Selector
        min_date = df['1L_fecha_inicio'].min()
        max_date = df['1L_fecha_inicio'].max()
        start_date, end_date = st.sidebar.date_input("Select Date Range for Fecha Inicio", [min_date, max_date])

        df = df[(df['1L_fecha_inicio'] >= pd.to_datetime(start_date)) & (df['1L_fecha_inicio'] <= pd.to_datetime(end_date))]

    # Filter for 1L_Esquema
    if '1L_Esquema' in df.columns:
        schema_labels = {
            1: 'FFX', 2: 'Gem-Nab', 3: 'Gemcitabina', 4: 'Capecitabina',
            5: 'FOLFIRI', 6: 'NALIRI', 7: 'FOLFOX', 8: 'CAPOX',
            9: 'GEMOX', 10: 'PEMBRO', 11: 'QT_RT', 12: 'Otro', 13: 'NA'
        }
        df['1L_Esquema'] = df['1L_Esquema'].map(schema_labels).fillna(df['1L_Esquema'])

        # Filters
        unique_schemas = df['1L_Esquema'].unique()
        selected_schemas = st.sidebar.multiselect("Select 1L_Esquema", unique_schemas, default=unique_schemas)

        df = df[df['1L_Esquema'].isin(selected_schemas)]


    df_with_errors = df[(df['ultima_linea'] == 0) | (df["1L_PLP"] < 0) | (df["2L_PLP"] < 0) | (df["3L_PLP"] < 0) | (df["4L_PLP"] < 0) | (df["overall_survival"] < 0)]
    if not df_with_errors.empty:
        st.write("Data with errors:")
        st.write(df_with_errors)
    else:
        st.write("No data with errors")
    df_cleaned = df[~df.index.isin(df_with_errors.index)]

    # Display graphs
    st.plotly_chart(create_ultima_linea_graph(df_cleaned))
    st.plotly_chart(create_ps_counts_graph(df_cleaned))
    st.plotly_chart(create_schema_plp_graph(df_cleaned, schema_labels))
    st.plotly_chart(create_line_plp_graph(df_cleaned))
    st.plotly_chart(create_percentage_completion_graph(df_cleaned, schema_labels))
    st.plotly_chart(create_overall_survival_by_schema_graph(df_cleaned, schema_labels))
    st.plotly_chart(create_overall_survival_by_ps_graph(df_cleaned))

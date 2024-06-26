import datetime

import streamlit as st
import pandas as pd

from common import schema_labels
from graphs import create_ultima_linea_graph, create_line_plp_graph, \
    create_percentage_completion_graph, create_overall_survival_by_schema_graph, \
    create_pie_chart_metastasic_vs_locally_advanced, create_pie_chart_ps, create_pie_chart_marcador_tumoral, \
    create_pie_chart_schema_by_line, create_overall_survival_graph, create_schema_plp_graph

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
    df["fecha_ultimo_contacto"] = pd.to_datetime(df["Fecha ultimo contacto"], errors="coerce")
    df["ultima_linea"] = df.apply(analyze_end_line, axis=1)
    df["fecha_final"] = df.apply(lambda x: x["fecha_fallecimiento"] if pd.notna(x["fecha_fallecimiento"]) else x["fecha_ultimo_contacto"], axis=1)
    # Duration calculation
    df['duration_survival_1L'] = (df['fecha_final'] - df['1L_fecha_inicio']).dt.days / 30.44
    df['duration_survival_2L'] = (df['fecha_final'] - df['2L_fecha_inicio']).dt.days / 30.44
    df['duration_survival_3L'] = (df['fecha_final'] - df['3L_fecha_inicio']).dt.days / 30.44

    df["1L_fecha_progresion_final"] = df["1L_fecha_progresion"].fillna(df["fecha_final"])
    df['duration_plp_1L'] = (df['1L_fecha_progresion_final'] - df['1L_fecha_inicio']).dt.days / 30.44

    # Replace 'df' with your DataFrame's name
    for i in range(1, 5):  # Assuming you have up to 4L
        inicio_col = f"{i}L_fecha_inicio"
        progresion_col = f"{i}L_fecha_progresion"
        plp_col = f"{i}L_PLP"

        df[plp_col] = (df[progresion_col] - df[inicio_col]).dt.days

    filtered_df = df[df['fecha_fallecimiento'].notna()]
    df["is_dead"] = df['fecha_fallecimiento'].notna()
    df["overall_survival"] = 0
    df["age"] = (pd.to_datetime(df["Fecha Diagnostico"], errors="coerce") - pd.to_datetime(df["Fecha Nacimiento"], errors="coerce")).dt.days / 365
    df.loc[filtered_df.index, 'overall_survival'] = (filtered_df['fecha_fallecimiento'] - filtered_df['1L_fecha_inicio']).dt.days
    # Assuming '1L_' is a datetime column in your DataFrame
    df['1L_fecha_inicio'] = pd.to_datetime(df['1L_fecha_inicio'], errors='coerce')

    # Map 1L_Esquema
    df['1L_Esquema'] = df['1L_Esquema'].map(schema_labels)
    df['2L_Esquema'] = df['2L_Esquema'].map(schema_labels)
    df['3L_Esquema'] = df['3L_Esquema'].map(schema_labels)
    df['4L_Esquema'] = df['4L_Esquema'].map(schema_labels)

    df["metastasico_vs_locally_advanced"] = df["Sitio metastasis"].apply(lambda x: "Locally Advanced" if x == 0 else "Metastasic")
    df["CA 19-9 basal (U/mL)"] = pd.to_numeric(df["CA 19-9 basal (U/mL)"], errors="coerce")
    df["marcador_tumoral"] = df["CA 19-9 basal (U/mL)"].apply(lambda x: "Normal" if x < 34 else "Elevated")
    return df


# File uploader
st.title("Patient Treatment Data Analysis")
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df = process_data(df)
    # Filters
    df["fecha_diagnostico_mts"] = pd.to_datetime(df["Fecha Diagnostico Mts"], errors="coerce")
    min_date = datetime.date(2017, 1, 1)
    max_date = datetime.date(2022, 12, 31)
    start_date, end_date = st.sidebar.date_input("Select Date Range for Fecha Diagnostico Mts", [min_date, max_date])
    unique_schemas = df['1L_Esquema'].unique()
    selected_schemas = st.sidebar.multiselect("Select 1L_Esquema", unique_schemas, default=unique_schemas)
    df = df[df['1L_Esquema'].isin(selected_schemas)]

    df = df[(df['fecha_diagnostico_mts'] >= pd.to_datetime(start_date)) & (
                df['fecha_diagnostico_mts'] <= pd.to_datetime(end_date))]

    df_with_errors = df[(df['ultima_linea'] == 0) | (df["1L_PLP"] < 0) | (df["2L_PLP"] < 0) | (df["3L_PLP"] < 0) | (df["4L_PLP"] < 0) | (df["overall_survival"] < 0)]
    with st.expander("Data"):
        st.write(df)
        if not df_with_errors.empty:
            st.write("Data with errors:")
            st.write(df_with_errors)
        else:
            st.write("No data with errors")
    df_cleaned = df[~df.index.isin(df_with_errors.index)]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Patients", len(df))
    with c2:
        st.metric("Median Age", round(df["age"].median(), 2))
    with c3:
        st.metric("Total Female", df["Sexo"].value_counts().get(1, 0))
    with c4:
        st.metric("Total Male", df["Sexo"].value_counts().get(2, 0))
    # Display graphs
    c11, c21, c31 = st.columns(3)
    with c11:
        st.plotly_chart(create_pie_chart_metastasic_vs_locally_advanced(df_cleaned))
    with c21:
        st.plotly_chart(create_pie_chart_marcador_tumoral(df_cleaned))
    with c31:
        st.plotly_chart(create_pie_chart_ps(df_cleaned))

    c12, c22, c32, c42 = st.columns(4)
    with c12:
        st.plotly_chart(create_pie_chart_schema_by_line(df_cleaned, "1L"))
    with c22:
        st.plotly_chart(create_pie_chart_schema_by_line(df_cleaned, "2L"))
    with c32:
        st.plotly_chart(create_pie_chart_schema_by_line(df_cleaned, "3L"))
    with c42:
        st.plotly_chart(create_pie_chart_schema_by_line(df_cleaned, "4L"))

    st.plotly_chart(create_ultima_linea_graph(df_cleaned))
    st.plotly_chart(create_overall_survival_graph(df_cleaned, "1L"))
    st.plotly_chart(create_overall_survival_graph(df_cleaned, "2L"))
    st.plotly_chart(create_overall_survival_graph(df_cleaned, "3L"))
    st.plotly_chart(create_overall_survival_by_schema_graph(df_cleaned))
    st.plotly_chart(create_schema_plp_graph(df_cleaned))
    st.plotly_chart(create_line_plp_graph(df_cleaned))
    st.plotly_chart(create_percentage_completion_graph(df_cleaned))

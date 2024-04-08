from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from lifelines import KaplanMeierFitter

from common import schema_labels

HEIGHT = 800
WIDTH = 1500


# Function to create the graph for "Patients Completing Each Treatment Line"
def create_ultima_linea_graph(df):
    # Counting patients in each line
    counts = df['ultima_linea'].value_counts().sort_index()

    # Calculating cumulative sum in reverse order
    cum_counts = counts[::-1].cumsum()[::-1]

    # Converting to percentages
    total_patients = df['ultima_linea'].count()
    percentages = (cum_counts / total_patients) * 100

    # Creating labels that include both percentage and count
    labels = ["{:.1f}%\n({} patients)".format(perc, count) for perc, count in zip(percentages, cum_counts)]

    # Creating the plot
    fig = go.Figure([go.Bar(x=percentages.index, y=percentages, text=labels, textposition='outside', marker_color='blue')])

    fig.update_layout(
        title="Percentage of Patients Reaching Each Treatment Line",
        xaxis_title="Therapeutic Line",
        yaxis_title="Percentage of Patients",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        xaxis=dict(type='category'),
        width=WIDTH,
        height=HEIGHT
    )

    fig.update_yaxes(title_standoff=25)

    return fig


def create_pie_chart_metastasic_vs_locally_advanced(df):
    counts = df['metastasico_vs_locally_advanced'].value_counts()
    fig = go.Figure([go.Pie(labels=counts.index, values=counts, textinfo='label+percent', hole=0.3)])
    fig.update_layout(
        title="Metastasic vs Locally Advanced",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        width=WIDTH / 3,
        height=HEIGHT
    )
    return fig


def create_pie_chart_ps(df):
    counts = df['PS'].value_counts()
    fig = go.Figure([go.Pie(labels=counts.index, values=counts, textinfo='label+percent', hole=0.3)])
    fig.update_layout(
        title="ECOG Performance Status (PS)",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        width=WIDTH / 3,
        height=HEIGHT
    )
    return fig


def create_pie_chart_marcador_tumoral(df):
    counts = df['marcador_tumoral'].value_counts()
    fig = go.Figure([go.Pie(labels=counts.index, values=counts, textinfo='label+percent', hole=0.3)])
    fig.update_layout(
        title="Marcador Tumoral",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        width=WIDTH / 3,
        height=HEIGHT
    )
    return fig


def create_pie_chart_schema_by_line(df, line: str = "1L"):
    counts = df[f"{line}_Esquema"].value_counts()
    counts_without_na = counts[counts.index != "NA"]
    fig = go.Figure([go.Pie(labels=counts_without_na.index, values=counts_without_na, textinfo='label+percent', hole=0.3)])
    fig.update_layout(
        title=f"Esquema de Tratamiento {line}",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        width=WIDTH / 3,
        height=HEIGHT
    )
    return fig


# Function to create the graph for "Patients Completing Each Treatment Line by ECOG PS"
def create_ps_counts_graph(df):
    ps_counts = df.groupby(['ultima_linea', 'PS']).size().unstack(fill_value=0)
    total_sums = ps_counts.sum(axis=1)
    fig = go.Figure()
    for idx, ps in enumerate(ps_counts.columns):
        fig.add_trace(go.Bar(x=ps_counts.index, y=ps_counts[ps], name=f"PS {ps}", text=ps_counts[ps], textposition='outside'))
    fig.update_layout(title="Patients Completing Each Treatment Line by ECOG PS",
                      xaxis_title="Therapeutic Line", yaxis_title="Count", plot_bgcolor='white', font=dict(family="Arial, sans-serif", size=12, color="black"), width=WIDTH, height=HEIGHT)
    return fig


# Function to create the box plot for "PLP según el Esquema de Tratamiento de 1L"
def create_schema_plp_graph(df):
    kmf = KaplanMeierFitter()
    fig = go.Figure()

    for schema in df['1L_Esquema'].unique():
        label = schema_labels.get(schema, schema)

        # Subset the DataFrame for the current schema
        subset = df[df['1L_Esquema'] == schema]
        subset = subset.dropna(subset=['1L_fecha_inicio', '1L_fecha_progresion'])

        # Event occurrence (1 if progression occurred, 0 if censored)
        subset['event_occurred'] = ~subset['1L_fecha_progresion'].isna()

        # Fit Kaplan-Meier model
        kmf.fit(subset['duration_plp_1L'], subset['event_occurred'], label=label)

        # Adding the Kaplan-Meier curve to the plot
        fig.add_trace(go.Scatter(x=kmf.survival_function_.index, y=kmf.survival_function_[label], mode='lines', name=label))

    fig.update_layout(
        title="PLP según el Esquema de Tratamiento de 1L",
        yaxis_title="Probabilidad de Progresión",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        xaxis_title="Tiempo (meses)",
        width=WIDTH,
        height=HEIGHT
    )

    return fig


def create_line_plp_graph(df):
    fig = go.Figure()
    for i in range(1, 5):
        plp_col = f"{i}L_PLP"
        fig.add_trace(go.Box(y=df[plp_col].dropna(), name=f"{i}L"))
    fig.update_layout(title="PLP para cada línea de tratamiento", yaxis_title="PLP (días)",
                      plot_bgcolor='white',
                      font=dict(family="Arial, sans-serif", size=12, color="black"),
                      xaxis_title="Línea de Tratamiento", width=WIDTH, height=HEIGHT)
    return fig


def create_percentage_completion_graph(df):
    line_counts = df.groupby(['ultima_linea', '1L_Esquema']).size().unstack(fill_value=0)
    line_percentages = line_counts.divide(line_counts.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for idx, line in enumerate(line_percentages.columns):
        line_label = schema_labels.get(line, f"Line {line}")
        fig.add_trace(go.Bar(x=line_percentages.index, y=line_percentages[line], name=line_label, text=line_percentages[line].apply(lambda x: '{:.1f}%'.format(x) if x != 0 else ''), textposition='outside'))
    fig.update_layout(title="Percentage of Patients Completing Each Treatment Line by First Treatment Line",
                      plot_bgcolor='white',
                      font=dict(family="Arial, sans-serif", size=12, color="black"),
                      xaxis_title="Ultima Linea", yaxis_title="Percentage", width=WIDTH, height=HEIGHT)
    return fig


def create_overall_survival_by_schema_graph(df):
    kmf = KaplanMeierFitter()
    fig = go.Figure()

    # Use current date or end of study date for censored data
    for schema in df['1L_Esquema'].unique():
        label = schema_labels.get(schema, schema)

        # Subset the DataFrame for the current schema
        subset = df[df['1L_Esquema'] == schema]
        subset = subset.dropna(subset=['1L_fecha_inicio'])

        subset["event"] = subset.apply(lambda x: x["fecha_fallecimiento"] if pd.notna(x["fecha_fallecimiento"]) else x["fecha_ultimo_contacto"], axis=1)
        # Duration calculation
        subset['event_occurred'] = ~subset['fecha_fallecimiento'].isna()
        # Fit Kaplan-Meier model
        kmf.fit(subset['duration_survival'], subset['event_occurred'], label=label)

        # Adding the Kaplan-Meier curve to the plot
        fig.add_trace(go.Scatter(x=kmf.survival_function_.index, y=kmf.survival_function_[label], mode='lines', name=label))

    fig.update_layout(
        title="Overall Survival by Treatment Schema",
        yaxis_title="Probability of Survival",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        xaxis_title="Time (months)",
        width=WIDTH,
        height=HEIGHT
    )

    return fig

# Function to create the box plot for "Overall Survival by PS"
def create_overall_survival_by_ps_graph(df):
    # Filter and calculate overall survival
    filtered_df = df[df['fecha_fallecimiento'].notna()]
    filtered_df['overall_survival'] = (filtered_df['fecha_fallecimiento'] - filtered_df['1L_fecha_inicio']).dt.days

    fig = go.Figure()

    for ps in sorted(filtered_df['PS'].unique()):
        fig.add_trace(go.Box(y=filtered_df[filtered_df['PS'] == ps]['overall_survival'], name=f"PS {ps}"))

    fig.update_layout(
        title="Overall survival by PS",
        xaxis_title="ECOG Performance Status (PS)",
        yaxis_title="Días",
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        height=HEIGHT,
        width=WIDTH
    )
    return fig

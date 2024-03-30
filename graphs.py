import plotly.graph_objects as go
import pandas as pd

# Function to create the graph for "Patients Completing Each Treatment Line"
def create_ultima_linea_graph(df):
    counts = df['ultima_linea'].value_counts().sort_index()
    fig = go.Figure([go.Bar(x=counts.index, y=counts, text=counts, textposition='outside', marker_color='blue')])
    for line, total in counts.items():
        fig.add_annotation(x=line, y=total, text=str(total), showarrow=False, yshift=10)
    fig.update_layout(title="Patients Completing Each Treatment Line", xaxis_title="Therapeutic Line", yaxis_title="Count", plot_bgcolor='white', font=dict(family="Arial, sans-serif", size=12, color="black"))
    fig.update_yaxes(title_standoff=25)
    return fig

# Function to create the graph for "Patients Completing Each Treatment Line by ECOG PS"
def create_ps_counts_graph(df):
    ps_counts = df.groupby(['ultima_linea', 'PS']).size().unstack(fill_value=0)
    total_sums = ps_counts.sum(axis=1)
    fig = go.Figure()
    for idx, ps in enumerate(ps_counts.columns):
        fig.add_trace(go.Bar(x=ps_counts.index, y=ps_counts[ps], name=f"PS {ps}", text=ps_counts[ps], textposition='outside'))
    fig.update_layout(title="Patients Completing Each Treatment Line by ECOG PS", xaxis_title="Therapeutic Line", yaxis_title="Count", plot_bgcolor='white', font=dict(family="Arial, sans-serif", size=12, color="black"))
    return fig

# Function to create the box plot for "PLP según el Esquema de Tratamiento de 1L"
def create_schema_plp_graph(df, schema_labels):
    fig = go.Figure()
    for schema in df['1L_Esquema'].unique():
        label = schema_labels.get(schema, schema)
        fig.add_trace(go.Box(y=df[df['1L_Esquema'] == schema]['1L_PLP'], name=label))
    fig.update_layout(title="PLP según el Esquema de Tratamiento de 1L", yaxis_title="PLP (días)", xaxis_title="Esquema de Tratamiento 1L")
    return fig

# Function to create the box plot for "PLP para cada línea de tratamiento"
def create_line_plp_graph(df):
    fig = go.Figure()
    for i in range(1, 5):
        plp_col = f"{i}L_PLP"
        fig.add_trace(go.Box(y=df[plp_col].dropna(), name=f"{i}L"))
    fig.update_layout(title="PLP para cada línea de tratamiento", yaxis_title="PLP (días)", xaxis_title="Línea de Tratamiento")
    return fig

# Function to create the percentage bar chart for "Percentage of Patients Completing Each Treatment Line by First Treatment Line"
def create_percentage_completion_graph(df, first_line_labels):
    line_counts = df.groupby(['ultima_linea', '1L_Esquema']).size().unstack(fill_value=0)
    line_percentages = line_counts.divide(line_counts.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for idx, line in enumerate(line_percentages.columns):
        line_label = first_line_labels.get(line, f"Line {line}")
        fig.add_trace(go.Bar(x=line_percentages.index, y=line_percentages[line], name=line_label, text=line_percentages[line].apply(lambda x: '{:.1f}%'.format(x) if x != 0 else ''), textposition='outside'))
    fig.update_layout(title="Percentage of Patients Completing Each Treatment Line by First Treatment Line", xaxis_title="Ultima Linea", yaxis_title="Percentage")
    return fig

# Add additional functions for other graphs as needed

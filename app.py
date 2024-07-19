import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from flask import Flask, render_template
from scan import realizar_escaneo, realizar_escaneo_puertos, realizar_escaneo_equipo, leer_escaneo_anterior, guardar_escaneo
from email_alerts import enviar_alerta

server = Flask(__name__)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

IP_RANGE = '10.72.2.0-9'
EMPRESA_NOMBRE = 'Mi Red'

@server.route('/')
def index():
    return render_template('index.html')

app.layout = html.Div([
    html.H1(f"Escaneo de Red - {EMPRESA_NOMBRE}", className="main-title"),
    html.H2(f"Rango de IP: {IP_RANGE}", className="sub-title"),
    html.Button('Iniciar Escaneo', id='scan-button', className="btn btn-primary"),
    html.Div(id='alert-container', className="alert alert-info", style={'display': 'none'}),
    html.H3("Estado de los Dispositivos en la Red", className="section-title"),
    html.Div(id='network-table-container', className='dash-table-container'),
    html.H3("Estado de los Puertos", className="section-title"),
    dcc.Graph(id='port-status'),
    html.Div(id='port-table-container', className='dash-table-container'),
    html.Div(className='loader mx-auto', id='loading-indicator', style={'display': 'none'})
])

@app.callback(
    [Output('network-table-container', 'children'),
     Output('port-status', 'figure'),
     Output('port-table-container', 'children'),
     Output('alert-container', 'children'),
     Output('loading-indicator', 'style'),
     Output('alert-container', 'style')],
    [Input('scan-button', 'n_clicks')]
)
def scan_network(n_clicks):
    print(f"Button clicked {n_clicks} times")
    if n_clicks is None:
        print("No clicks detected, returning no updates.")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, {'display': 'none'}, {'display': 'none'}

    print("Iniciando escaneo...")

    loading_style = {'display': 'block'}
    alert_style = {'display': 'none'}

    scan_results_df = realizar_escaneo(IP_RANGE)
    print("Escaneo de red completado.")
    if scan_results_df.empty:
        print("No se encontraron resultados en el escaneo de red.")
        return dash.no_update, dash.no_update, dash.no_update, "No se encontraron resultados en el escaneo de red.", {'display': 'none'}, {'display': 'block'}

    ip_list = scan_results_df['ip'].tolist()
    port_results_df = realizar_escaneo_puertos(ip_list)
    equipo_results_df = realizar_escaneo_equipo(ip_list)
    print("Escaneo de puertos y equipos completado.")

    # Leer escaneo anterior
    prev_scan_results_df = leer_escaneo_anterior(tipo='ip')
    prev_port_results_df = leer_escaneo_anterior(tipo='puerto')
    prev_equipo_results_df = leer_escaneo_anterior(tipo='equipo')

    # Print the data of all dataframes
    print("Datos de scan_results_df:")
    print(scan_results_df)
    print("Datos de port_results_df:")
    print(port_results_df)
    print("Datos de equipo_results_df:")
    print(equipo_results_df)

    if 'puerto' not in port_results_df.columns or 'puerto' not in prev_port_results_df.columns:
        print("La columna 'puerto' no está presente en uno de los DataFrames de puertos.")
        return dash.no_update, dash.no_update, dash.no_update, "Error: La columna 'puerto' no está presente en los resultados del escaneo de puertos.", {'display': 'none'}, {'display': 'block'}

    alerts = []

    combined_ports_df = pd.merge(port_results_df, prev_port_results_df, on=['ip', 'puerto'], how='outer', suffixes=('', '_previous'))
    combined_ports_df['estado_previous'].fillna('closed', inplace=True)
    combined_ports_df['estado'].fillna('closed', inplace=True)
    changed_ports = combined_ports_df[combined_ports_df['estado'] != combined_ports_df['estado_previous']]

    for _, row in changed_ports.iterrows():
        if row['estado'] == 'open':
            alerts.append(f"El puerto {row['puerto']} en la IP {row['ip']} ha cambiado de estado a open")
        elif row['estado'] == 'closed':
            alerts.append(f"El puerto {row['puerto']} en la IP {row['ip']} ha cambiado de estado a closed")

    # Comparar el estado de las IPs
    combined_ips_df = pd.merge(scan_results_df, prev_scan_results_df, on='ip', how='outer', suffixes=('', '_previous'))
    combined_ips_df['estado_previous'].fillna('down', inplace=True)
    combined_ips_df['estado'].fillna('down', inplace=True)
    changed_ips = combined_ips_df[combined_ips_df['estado'] != combined_ips_df['estado_previous']]

    for _, row in changed_ips.iterrows():
        if row['estado'] == 'up' and row['estado_previous'] == 'down':
            alerts.append(f"La IP {row['ip']} ha cambiado de estado a up")
        elif row['estado'] == 'down' and row['estado_previous'] == 'up':
            alerts.append(f"La IP {row['ip']} ha cambiado de estado a down")

    print("Estado de puertos revisado.")
    print("Estado de IPs revisado.")

    guardar_escaneo(port_results_df, tipo='puerto')
    guardar_escaneo(scan_results_df, tipo='ip')
    guardar_escaneo(equipo_results_df, tipo='equipo')
    print("Resultados guardados en CSV.")

    if alerts:
        alert_message = html.Ul([html.Li(alert) for alert in alerts])
        enviar_alerta(alerts)  # Enviar la lista de alertas en lugar de una cadena
        alert_style = {'display': 'block'}
        print(f"Alertas enviadas: {' | '.join(alerts)}")
    else:
        alert_message = "No se encontraron cambios en el estado de las IPs y puertos."
        alert_style = {'display': 'block'}
        print("No se encontraron cambios en el estado de las IPs y puertos.")

    loading_style = {'display': 'none'}

    # Combina los DataFrames para la tabla final
    combined_df = pd.merge(scan_results_df, equipo_results_df, on='ip', how='left')

    # Eliminar columnas duplicadas de fechas y renombrar la columna de fecha
    combined_df = combined_df.drop_duplicates(subset=['ip', 'estado'])
    combined_df = combined_df.drop(columns=['fecha_escaneo_y'])
    combined_df = combined_df.rename(columns={'fecha_escaneo_x': 'fecha_escaneo'})

    network_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in combined_df.columns],
        data=combined_df.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_header={
            'backgroundColor': '#343a40',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_cell={
            'backgroundColor': '#495057',
            'color': 'white',
            'textAlign': 'center',
            'padding': '10px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#3a3f44',
            }
        ]
    )

    port_fig = px.pie(port_results_df, names='estado', title='Estado de los Puertos')

    port_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in port_results_df.columns],
        data=port_results_df.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'},
        style_header={
            'backgroundColor': '#343a40',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_cell={
            'backgroundColor': '#495057',
            'color': 'white',
            'textAlign': 'center',
            'padding': '10px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#3a3f44',
            }
        ]
    )

    print("Datos preparados para la visualización.")
    return network_table, port_fig, port_table, alert_message, loading_style, alert_style

if __name__ == '__main__':
    app.run_server(debug=True)

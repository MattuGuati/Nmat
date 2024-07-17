import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from flask import Flask, render_template
from scan import realizar_escaneo, realizar_escaneo_puertos, leer_escaneo_anterior, guardar_escaneo
from email_alerts import enviar_alerta

server = Flask(__name__)
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

IP_RANGE = '10.72.2.0-9'
EMPRESA_NOMBRE = 'Mi Red'

@server.route('/')
def index():
    return render_template('index.html')

app.layout = html.Div([
    html.H1(f"Escaneo de Red - {EMPRESA_NOMBRE}"),
    html.H2(f"Rango de IP: {IP_RANGE}"),
    html.Button('Iniciar Escaneo', id='scan-button', className="btn btn-primary"),
    html.Div(id='alert-container', className="alert alert-info", style={'display': 'none'}),
    dcc.Graph(id='network-status'),
    html.Div(id='network-table-container', className='dash-table-container'),
    dcc.Graph(id='port-status'),
    html.Div(id='port-table-container', className='dash-table-container'),
    html.Div(className='loader mx-auto', id='loading-indicator', style={'display': 'none'})
])

@app.callback(
    [Output('network-status', 'figure'),
     Output('port-status', 'figure'),
     Output('network-table-container', 'children'),
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
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, {'display': 'none'}, {'display': 'none'}

    print("Iniciando escaneo...")

    loading_style = {'display': 'block'}
    alert_style = {'display': 'none'}

    scan_results_df = realizar_escaneo(IP_RANGE)
    print("Escaneo de red completado.")
    if scan_results_df.empty:
        print("No se encontraron resultados en el escaneo de red.")
        return dash.no_update, dash.no_update, "No se encontraron resultados en el escaneo de red.", dash.no_update, dash.no_update, {'display': 'none'}, {'display': 'block'}

    ip_list = scan_results_df['ip'].tolist()
    port_results_df = realizar_escaneo_puertos(ip_list)
    print("Escaneo de puertos completado.")

    # Leer escaneo anterior
    prev_scan_results_df = leer_escaneo_anterior(tipo='ip')
    prev_port_results_df = leer_escaneo_anterior(tipo='puerto')

    # Print the data of both dataframes
    print("Datos de scan_results_df:")
    print(scan_results_df)
    print("Datos de port_results_df:")
    print(port_results_df)

    if 'puerto' not in port_results_df.columns or 'puerto' not in prev_port_results_df.columns:
        print("La columna 'puerto' no está presente en uno de los DataFrames de puertos.")
        return dash.no_update, dash.no_update, "Error: La columna 'puerto' no está presente en los resultados del escaneo de puertos.", dash.no_update, dash.no_update, {'display': 'none'}, {'display': 'block'}

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
    print("Resultados guardados en CSV.")

    if alerts:
        alert_message = html.Ul([html.Li(alert) for alert in alerts])
        enviar_alerta(" | ".join(alerts))
        alert_style = {'display': 'block'}
        print(f"Alertas enviadas: {' | '.join(alerts)}")
    else:
        alert_message = "No se encontraron cambios en el estado de las IPs y puertos."
        alert_style = {'display': 'block'}
        print("No se encontraron cambios en el estado de las IPs y puertos.")

    loading_style = {'display': 'none'}

    network_fig = px.pie(scan_results_df, names='estado', title='Estado de los Dispositivos en la Red')
    port_fig = px.pie(port_results_df, names='estado', title='Estado de los Puertos')

    network_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in scan_results_df.columns],
        data=scan_results_df.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'}
    )

    port_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in port_results_df.columns],
        data=port_results_df.to_dict('records'),
        style_table={'height': '300px', 'overflowY': 'auto'}
    )

    print("Datos preparados para la visualización.")
    return network_fig, port_fig, network_table, port_table, alert_message, loading_style, alert_style

if __name__ == '__main__':
    app.run_server(debug=True)

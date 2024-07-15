import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from scan import realizar_escaneo, realizar_escaneo_puertos
from email_alerts import enviar_alerta

app = dash.Dash(__name__)

# Rango de IP predefinido y empresa
IP_RANGE = '10.72.2.0-8'
EMPRESA_NOMBRE = 'Mi Red'

app.layout = html.Div([
    html.H1(f"Escaneo de Red - {EMPRESA_NOMBRE}"),
    html.H2(f"Rango de IP: {IP_RANGE}"),
    html.Button('Iniciar Escaneo', id='scan-button'),
    html.Div(className='loader', id='loading-indicator'),  # Indicador de carga
    html.Div(id='alert-container'),
    dcc.Graph(id='network-status'),
    html.Div(id='network-table-container', className='dash-table-container'),
    dcc.Graph(id='port-status'),
    html.Div(id='port-table-container', className='dash-table-container')
])

@app.callback(
    [Output('network-status', 'figure'),
     Output('port-status', 'figure'),
     Output('network-table-container', 'children'),
     Output('port-table-container', 'children'),
     Output('alert-container', 'children'),
     Output('loading-indicator', 'style')],
    [Input('scan-button', 'n_clicks')]
)
def scan_network(n_clicks):
    if n_clicks is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, {'display': 'none'}

    print("Iniciando escaneo...")

    # Mostrar el indicador de carga
    loading_style = {'display': 'block'}

    scan_results_df = realizar_escaneo(IP_RANGE)
    if scan_results_df.empty:
        print("No se encontraron resultados en el escaneo de red.")
        return dash.no_update, dash.no_update, "No se encontraron resultados en el escaneo de red.", dash.no_update, dash.no_update, {'display': 'none'}

    port_results_df = realizar_escaneo_puertos(scan_results_df['ip'].tolist())
    if port_results_df.empty:
        print("No se encontraron resultados en el escaneo de puertos.")
        return dash.no_update, dash.no_update, dash.no_update, "No se encontraron resultados en el escaneo de puertos.", dash.no_update, {'display': 'none'}

    print("Escaneo completado. Comparando resultados...")

    # Comparar con resultados anteriores
    scan_results_previous_df = pd.read_csv('scan_results.csv', dtype={'ip': str})
    port_results_previous_df = pd.read_csv('port_results.csv', dtype={'ip': str})

    alerts = []

    # Detectar cambios en las IPs
    combined_df = pd.merge(scan_results_df, scan_results_previous_df, on='ip', how='outer', suffixes=('', '_previous'))
    combined_df['estado_previous'].fillna('down', inplace=True)
    combined_df['estado'].fillna('down', inplace=True)
    changed_ips = combined_df[combined_df['estado'] != combined_df['estado_previous']]

    for _, row in changed_ips.iterrows():
        if row['estado'] == 'up':
            alerts.append(f"La IP {row['ip']} ha cambiado de estado a up")
        elif row['estado'] == 'down':
            alerts.append(f"La IP {row['ip']} ha cambiado de estado a down")

    # Detectar cambios en los puertos
    combined_ports_df = pd.merge(port_results_df, port_results_previous_df, on=['ip', 'puerto'], how='outer', suffixes=('', '_previous'))
    combined_ports_df['estado_previous'].fillna('closed', inplace=True)
    combined_ports_df['estado'].fillna('closed', inplace=True)
    changed_ports = combined_ports_df[combined_ports_df['estado'] != combined_ports_df['estado_previous']]

    for _, row in changed_ports.iterrows():
        if row['estado'] == 'open':
            alerts.append(f"El puerto {row['puerto']} en la IP {row['ip']} ha cambiado de estado a open")
        elif row['estado'] == 'closed':
            alerts.append(f"El puerto {row['puerto']} en la IP {row['ip']} ha cambiado de estado a closed")

    # Guardar los resultados actuales como históricos
    scan_results_df.to_csv('scan_results.csv', index=False)
    port_results_df.to_csv('port_results.csv', index=False)

    if alerts:
        alert_message = "\n".join(alerts)
        enviar_alerta(alert_message)
    else:
        alert_message = "No se encontraron cambios en el estado de las IPs y puertos."

    # Ocultar el indicador de carga
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

    return network_fig, port_fig, network_table, port_table, alert_message, loading_style

if __name__ == '__main__':
    app.run_server(debug=True)

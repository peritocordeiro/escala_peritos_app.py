
import pandas as pd
from datetime import datetime, timedelta
import json

try:
    import streamlit as st
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ModuleNotFoundError:
    print("Este código requer as bibliotecas Streamlit e Google API Client. Execute localmente com: pip install streamlit google-api-python-client google-auth")
    raise SystemExit

st.set_page_config(page_title="Escala de Peritos", layout="wide")

st.title("📅 Escala de Plantões - Peritos")

# Entrada de dados dos peritos
st.sidebar.header("👥 Peritos")
n_peritos = 5
peritos = []

with st.sidebar:
    for i in range(n_peritos):
        nome = st.text_input(f"Perito {i+1} - Nome", f"Perito {i+1}")
        email = st.text_input(f"Perito {i+1} - E-mail", f"perito{i+1}@email.com")
        peritos.append({"nome": nome, "email": email})

# Parâmetros da escala
st.sidebar.header("📆 Parâmetros da Escala")
data_inicio = st.sidebar.date_input("Data de Início", datetime.today())
dias = st.sidebar.slider("Número de dias da escala", 7, 60, 30)
hora_inicio = st.sidebar.time_input("Hora de Início do Plantão", datetime.strptime("08:00", "%H:%M"))
hora_fim = st.sidebar.time_input("Hora de Término do Plantão", datetime.strptime("17:00", "%H:%M"))

# Gerar escala
if st.button("🔄 Gerar Escala"):
    datas = [data_inicio + timedelta(days=i) for i in range(dias)]
    escala = []

    for i, dia in enumerate(datas):
        perito = peritos[i % n_peritos]
        escala.append({
            "Data": dia.strftime("%Y-%m-%d"),
            "Dia da Semana": dia.strftime("%A"),
            "Perito": perito["nome"],
            "E-mail": perito["email"],
            "Início": hora_inicio.strftime("%H:%M"),
            "Fim": hora_fim.strftime("%H:%M")
        })

    df_escala = pd.DataFrame(escala)
    st.success("✅ Escala gerada com sucesso!")
    st.dataframe(df_escala, use_container_width=True)

    # Exportar como CSV
    csv = df_escala.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Escala (CSV)", csv, "escala.csv", "text/csv")

    # Enviar para Google Agenda
    st.subheader("📤 Enviar para Google Calendar")
    credentials_file = st.file_uploader("Selecione o arquivo de credenciais do Google (credentials.json)", type="json")

    if credentials_file and st.button("📆 Enviar eventos para Agenda"):
        credentials_info = json.load(credentials_file)
        creds = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)

        calendar_id = 'primary'

        for _, row in df_escala.iterrows():
            start = datetime.strptime(f"{row['Data']} {row['Início']}", "%Y-%m-%d %H:%M")
            end = datetime.strptime(f"{row['Data']} {row['Fim']}", "%Y-%m-%d %H:%M")

            event = {
                'summary': f"Plantão - {row['Perito']}",
                'description': f"Plantão de {row['Perito']}",
                'start': {'dateTime': start.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'end': {'dateTime': end.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'attendees': [{'email': row['E-mail']}]
            }

            service.events().insert(calendarId=calendar_id, body=event).execute()

        st.success("✅ Eventos enviados para o Google Agenda com sucesso!")

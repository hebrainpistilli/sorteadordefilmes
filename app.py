import streamlit as st
import pandas as pd
import json
import random
from datetime import datetime
import os

# --- Configurações e Constantes ---
STRICT_PASSWORD = "123456789"
FILE_MOVIES = "filmes.json"
FILE_HISTORY = "historico.json"
HINT_PASSWORD = "Sequência"

st.set_page_config(layout="wide", page_title="Sorteador de Filmes")
st.markdown(
    """
    <style>
    .st-emotion-cache-18ni7ap {
        text-align: center;
    }
    .st-emotion-cache-163fv0c p {
        font-size: 1.25rem;
    }
    .st-emotion-cache-z1bnq {
        background-color: #262730;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .st-emotion-cache-l9bibi {
        border-radius: 12px;
    }
    .st-emotion-cache-1kyx2w7 {
        border-radius: 12px;
    }
    .st-emotion-cache-ocqbe5 {
        border-radius: 12px;
        color: #fff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Funções de Persistência ---
def load_data():
    """Carrega os dados dos arquivos persistentes. Cria arquivos vazios se não existirem."""
    if 'df_movies' not in st.session_state:
        if os.path.exists(FILE_MOVIES) and os.path.getsize(FILE_MOVIES) > 0:
            st.session_state.df_movies = pd.read_json(FILE_MOVIES)
        else:
            st.session_state.df_movies = pd.DataFrame(columns=['Filme'])

    if 'df_history' not in st.session_state:
        if os.path.exists(FILE_HISTORY) and os.path.getsize(FILE_HISTORY) > 0:
            st.session_state.df_history = pd.read_json(FILE_HISTORY, orient='records', lines=True)
        else:
            st.session_state.df_history = pd.DataFrame(columns=['Data', 'Hora', 'Filme'])

def save_data():
    """Salva os DataFrames atuais nos arquivos JSON."""
    st.session_state.df_movies.to_json(FILE_MOVIES, orient='records', lines=False, indent=2)
    st.session_state.df_history.to_json(FILE_HISTORY, orient='records', lines=True)

# --- Funções de Ação ---
def draw_movie():
    """Sorteia um filme, move para o histórico e salva os dados."""
    if not st.session_state.df_movies.empty:
        # Sorteia um filme
        movie = random.choice(st.session_state.df_movies['Filme'].tolist())

        # Remove o filme da lista de disponíveis
        st.session_state.df_movies = st.session_state.df_movies[st.session_state.df_movies['Filme'] != movie].reset_index(drop=True)

        # Adiciona o filme ao histórico
        now = datetime.now()
        new_row = pd.DataFrame([{
            'Data': now.strftime("%d/%m/%Y"),
            'Hora': now.strftime("%H:%M:%S"),
            'Filme': movie
        }])
        st.session_state.df_history = pd.concat([st.session_state.df_history, new_row], ignore_index=True)

        save_data()
        st.success(f"🎥 Filme sorteado: {movie}!")
        st.balloons()
    else:
        st.error("Não há filmes disponíveis para sorteio. Por favor, adicione mais filmes.")

def restore_movie(movie, password):
    """Repõe um filme do histórico para a lista de disponíveis."""
    if password == STRICT_PASSWORD:
        # Remove o filme do histórico
        st.session_state.df_history = st.session_state.df_history[st.session_state.df_history['Filme'] != movie].reset_index(drop=True)

        # Adiciona o filme de volta à lista de disponíveis (se ainda não estiver lá)
        if movie not in st.session_state.df_movies['Filme'].tolist():
            new_row = pd.DataFrame([{'Filme': movie}])
            st.session_state.df_movies = pd.concat([st.session_state.df_movies, new_row], ignore_index=True)

        save_data()
        st.success(f"✅ Filme '{movie}' reposto na lista de disponíveis!")
        st.session_state.restore_initiated = False
    else:
        st.error("❌ Senha incorreta. Ação cancelada.")

def clear_all(password):
    """Exclui toda a lista de filmes e o histórico."""
    if password == STRICT_PASSWORD:
        st.session_state.df_movies = pd.DataFrame(columns=['Filme'])
        st.session_state.df_history = pd.DataFrame(columns=['Data', 'Hora', 'Filme'])
        save_data()
        st.success("🗑️ Lista de filmes e histórico excluídos com sucesso.")
        st.session_state.delete_initiated = False
    else:
        st.error("❌ Senha incorreta. Ação cancelada.")

# --- Inicialização ---
load_data()
st.title("🎬 Sorteador de Filmes da Biribolas e Hebrinbous")
st.write("Bem-vindo, Biribolas e Hebrinbous! Carregue uma lista de filmes e sorteie um aleatoriamente.")
st.divider()

# --- Upload de Arquivo ---
uploaded_file = st.file_uploader("Carregar lista de filmes (.csv ou .json)", type=["csv", "json"], help="O arquivo não será excluído, e os filmes serão adicionados à sua lista atual.")
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_new = pd.read_csv(uploaded_file)
        else:
            df_new = pd.read_json(uploaded_file)

        # Adiciona apenas a coluna 'Filme' e remove duplicatas
        df_new = df_new[['Filme']].copy()
        
        # Concatena com a lista atual, remove duplicatas e reseta o índice
        st.session_state.df_movies = pd.concat([st.session_state.df_movies, df_new]).drop_duplicates(subset='Filme', keep='first').reset_index(drop=True)
        save_data()
        st.success("Filmes carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")

# --- Layout de Colunas ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Filmes Disponíveis")
    st.dataframe(st.session_state.df_movies, use_container_width=True, hide_index=True)

    st.button("Sortear Filme!", on_click=draw_movie, use_container_width=True, type="primary")
    
    # Botão para iniciar a exclusão total
    if st.button("Excluir Lista Completa", use_container_width=True, type="secondary"):
        st.session_state.delete_initiated = True
        st.session_state.restore_initiated = False

    # Formulário de confirmação de exclusão
    if 'delete_initiated' in st.session_state and st.session_state.delete_initiated:
        with st.form("delete_form"):
            st.markdown("⚠️ **Confirmar exclusão da lista?** Esta ação é irreversível.")
            delete_password = st.text_input("Senha", type="password", help=HINT_PASSWORD)
            submit_delete = st.form_submit_button("Confirmar Exclusão", type="primary")
            if submit_delete:
                clear_all(delete_password)


with col2:
    st.subheader("Histórico de Sorteios")
    st.dataframe(st.session_state.df_history, use_container_width=True, hide_index=True)
    
    # Botão para iniciar a reposição
    if st.button("Repor Filme Sorteado", use_container_width=True, type="secondary"):
        if not st.session_state.df_history.empty:
            st.session_state.restore_initiated = True
            st.session_state.delete_initiated = False
        else:
            st.info("Não há filmes no histórico para repor.")

    # Formulário de reposição
    if 'restore_initiated' in st.session_state and st.session_state.restore_initiated and not st.session_state.df_history.empty:
        with st.form("restore_form"):
            movie_to_restore = st.selectbox("Selecione o filme para repor:", st.session_state.df_history['Filme'].tolist())
            restore_password = st.text_input("Senha", type="password", help=HINT_PASSWORD)
            submit_restore = st.form_submit_button("Confirmar Reposição", type="primary")
            if submit_restore:
                restore_movie(movie_to_restore, restore_password)

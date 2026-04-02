import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG Бот")
st.title("RAG Бот")

#Проверка на наличие doc_id
if 'doc_id' not in st.session_state:
    st.session_state.doc_id = None

#Загрузка документа
st.header("1. Загрузить документ")
uploaded_file = st.file_uploader("Выберите текстовый файл", type=["txt"])
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
    if st.button("Загрузить"):
        with st.spinner("Загружаю и индексирую..."):
            response = requests.post(f"{API_URL}/upload", json={"text": text})
            if response.status_code == 200:
                data = response.json()
                st.success(f"Документ загружен! ID: {data['doc_id']}, чанков: {data['chunks_amount']}")
                st.session_state.doc_id = response.json()["doc_id"]
            else:
                st.error(f"Ошибка: {response.status_code} - {response.text}")

#Задать вопрос
st.header("2. Задать вопрос")
question = st.text_input("Введите вопрос:")
if st.button("Спросить"):
    if st.session_state.doc_id is None:
        st.warning("Сначала загрузите документ")
    else:   
        if not question.strip():
            st.warning("Введите вопрос")
        else:
            with st.spinner("Ищу ответ..."):
                resp = requests.post(f"{API_URL}/ask", json={"question": question})
                if resp.status_code == 200:
                    answer = resp.json()["Ответ"]
                    st.success("Ответ:")
                    st.write(answer)
                else:
                    st.error(f"Ошибка: {resp.status_code} - {resp.text}")
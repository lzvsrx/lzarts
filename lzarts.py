import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import uuid
import io
from streamlit_drawable_canvas import st_canvas
from moviepy.editor import ImageClip
import requests
import json

# ------------------ Funções auxiliares ------------------ #
def criar_canvas_base(largura, altura, cor_fundo):
    return Image.new("RGB", (largura, altura), cor_fundo)

def guardar_projeto(nome, imagem, tipo, texto, descricao, utilizador):
    pasta_utilizador = f"projetos/{utilizador}"
    os.makedirs(pasta_utilizador, exist_ok=True)
    caminho_img = f"{pasta_utilizador}/{nome}.png"
    caminho_json = f"{pasta_utilizador}/{nome}.json"
    imagem.save(caminho_img)
    
    dados = {
        "nome": nome,
        "tipo": tipo,
        "texto": texto,
        "descricao": descricao,
        "imagem": caminho_img,
        "data": datetime.now().isoformat()
    }
    with open(caminho_json, "w") as f:
        json.dump(dados, f)

    return caminho_img

def guardar_video(nome, imagem):
    caminho = f"projetos/{nome}.mp4"
    clip = ImageClip(imagem).set_duration(5)
    clip.write_videofile(caminho, fps=24)
    return caminho

def obter_dimensoes(tipo):
    tamanhos = {
        "Post Instagram": (1080, 1080),
        "Story Instagram": (1080, 1920),
        "Post Facebook": (1200, 630),
        "Story Facebook": (1080, 1920),
        "Status WhatsApp": (1080, 1920),
        "Logo": (500, 500)
    }
    return tamanhos.get(tipo, (1080, 1080))

def gerar_logo_com_ia(prompt):
    resposta = requests.post(
        "https://api.deepai.org/api/text2img",
        data={ 'text': prompt },
        headers={ 'api-key': 'sua_chave_de_api_deepai' }
    )
    if resposta.status_code == 200:
        return resposta.json().get('output_url')
    return None

# ------------------ Interface Streamlit ------------------ #
st.set_page_config(page_title="Criador de Conteúdos", layout="wide")
st.title("🎨 Criador de Conteúdos para Redes Sociais")
st.markdown("Cria posts, stories, logótipos e anúncios para Instagram, Facebook e WhatsApp com facilidade.")

menu = st.sidebar.selectbox("Menu", ["Login", "Registar", "Criar Projeto", "Meus Projetos"])

if "login" not in st.session_state:
    st.session_state.login = False
if "utilizador" not in st.session_state:
    st.session_state.utilizador = ""

if menu == "Login":
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Entrar"):
        if email and password:
            st.session_state.login = True
            st.session_state.utilizador = email.split("@")[0]
            st.success("Login realizado com sucesso.")
        else:
            st.error("Preencha todos os campos.")

elif menu == "Registar":
    nome = st.sidebar.text_input("Nome")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Registar"):
        if nome and email and password:
            st.success("Registo realizado com sucesso. Faça login para continuar.")
        else:
            st.error("Preencha todos os campos.")

elif menu == "Criar Projeto" and st.session_state.login:
    col1, col2 = st.columns(2)

    with col1:
        tipo = st.selectbox("Tipo de conteúdo", ["Post Instagram", "Story Instagram", "Post Facebook", "Story Facebook", "Status WhatsApp", "Logo"])
        texto = st.text_area("Texto a incluir na imagem")
        cor_fundo = st.color_picker("Cor de fundo", "#ffffff")
        gerar_video = st.checkbox("Gerar também um vídeo com este conteúdo")

    with col2:
        st.markdown("### Especificações de Design")
        descricao = st.text_area("Descreve o estilo visual desejado (cores, fontes, elementos)")

    largura, altura = obter_dimensoes(tipo)

    if tipo != "Logo":
        st.markdown("### Editor Visual")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0.3)",
            stroke_width=3,
            stroke_color="#000000",
            background_color=cor_fundo,
            background_image=None,
            update_streamlit=True,
            height=altura,
            width=largura,
            drawing_mode="freedraw",
            key="canvas"
        )

    if st.button("Gerar imagem e vídeo"):
        imagem_final = criar_canvas_base(largura, altura, cor_fundo)
        draw = ImageDraw.Draw(imagem_final)
        fonte = ImageFont.load_default()
        draw.text((50, 50), texto, fill="black", font=fonte)

        if tipo != "Logo" and canvas_result.image_data is not None:
            imagem_canvas = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA').convert('RGB')
            imagem_final.paste(imagem_canvas, (0, 0), imagem_canvas)

        nome_arquivo = f"{tipo}_{uuid.uuid4().hex[:8]}"
        caminho_imagem = guardar_projeto(nome_arquivo, imagem_final, tipo, texto, descricao, st.session_state.utilizador)

        st.image(imagem_final, caption=f"Pré-visualização: {tipo}", use_column_width=True)
        st.download_button("📥 Fazer download da imagem", data=open(caminho_imagem, "rb"), file_name=f"{nome_arquivo}.png")

        if gerar_video:
            caminho_video = guardar_video(nome_arquivo, caminho_imagem)
            st.video(caminho_video)
            st.download_button("📥 Fazer download do vídeo", data=open(caminho_video, "rb"), file_name=f"{nome_arquivo}.mp4")

        if tipo == "Logo":
            st.info("Logótipo simples criado com texto e fundo definidos. Podes também gerar um logótipo com IA abaixo.")
            prompt_logo = st.text_input("Descreve o logótipo que queres gerar com IA")
            if st.button("Gerar logótipo com IA"):
                url_logo = gerar_logo_com_ia(prompt_logo)
                if url_logo:
                    st.image(url_logo, caption="Logótipo gerado por IA")
                    st.markdown(f"[🔗 Abrir imagem em nova aba]({url_logo})")
                else:
                    st.error("Não foi possível gerar o logótipo com IA. Verifica a tua chave de API.")

elif menu == "Meus Projetos" and st.session_state.login:
    st.header("📁 Meus Projetos")
    pasta_utilizador = f"projetos/{st.session_state.utilizador}"
    os.makedirs(pasta_utilizador, exist_ok=True)
    for ficheiro in os.listdir(pasta_utilizador):
        if ficheiro.endswith(".json"):
            with open(os.path.join(pasta_utilizador, ficheiro)) as f:
                dados = json.load(f)
                with st.expander(dados['nome']):
                    st.text(f"Tipo: {dados['tipo']}")
                    st.text(f"Texto: {dados['texto']}")
                    st.text(f"Descrição: {dados['descricao']}")
                    st.image(dados['imagem'], width=300)
                    st.download_button("⬇️ Download", data=open(dados['imagem'], "rb"), file_name=os.path.basename(dados['imagem']))
                    if st.button(f"✏️ Editar {dados['nome']}"):
                        st.session_state['editando'] = dados
                        st.experimental_rerun()

# Edição de projeto
if 'editando' in st.session_state:
    dados = st.session_state['editando']
    st.header(f"✏️ Editar Projeto: {dados['nome']}")
    novo_texto = st.text_area("Novo texto", value=dados['texto'])
    nova_desc = st.text_area("Nova descrição", value=dados['descricao'])
    if st.button("Guardar alterações"):
        dados['texto'] = novo_texto
        dados['descricao'] = nova_desc
        with open(dados['imagem'].replace('.png', '.json'), "w") as f:
            json.dump(dados, f)
        st.success("Alterações guardadas com sucesso.")
        del st.session_state['editando']
        st.experimental_rerun()
else:
    if menu in ["Criar Projeto", "Meus Projetos"] and not st.session_state.login:
        st.warning("É necessário estar autenticado para aceder a esta funcionalidade.")

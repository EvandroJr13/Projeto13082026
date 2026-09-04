import datetime
import io
import re
import threading
import webbrowser
import customtkinter as ctk
from PIL import Image
import requests

# Configuração de Tema Dark Moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


def limpar_html(texto):
    """Remove tags HTML do texto da sinopse."""
    if not texto:
        return "Sinopse não disponível para este anime."
    clean = re.compile("<.*?>")
    return re.sub(clean, "", texto)


class AppCalendarioAnime(ctk.CTk):

    DIAS_DA_SEMANA = [
        ("SEGUNDA", "MON", 0),
        ("TERÇA", "TUE", 1),
        ("QUARTA", "WED", 2),
        ("QUINTA", "THU", 3),
        ("SEXTA", "FRI", 4),
        ("SÁBADO", "SAT", 5),
        ("DOMINGO", "SUN", 6),
    ]

    GENEROS_DISPONIVEIS = [
        "Todos", "Action", "Adventure", "Comedy", "Drama", 
        "Fantasy", "Horror", "Mecha", "Mystery", "Romance", 
        "Sci-Fi", "Slice of Life", "Sports", "Supernatural", "Thriller"
    ]

    # Paleta de Cores
    COLOR_BG = "#0B0E14"           # Fundo Principal
    COLOR_SIDEBAR = "#121824"      # Fundo do Sidebar
    COLOR_CARD = "#1A2332"         # Fundo dos Cards
    COLOR_ACCENT = "#00A8FF"       # Azul Neon
    COLOR_TEXT_MAIN = "#FFFFFF"    # Texto Primário
    COLOR_TEXT_MUTED = "#8A99AD"   # Texto Secundário

    def __init__(self):
        super().__init__()
        self.title("CALENDÁRIO DE LANÇAMENTOS | SÉRIES & ANIME")
        self.geometry("1100x720")
        self.configure(fg_color=self.COLOR_BG)

        # Gerenciamento de Estado de Favoritos / Minha Lista
        # Armazena dicionários de animes indexados pelo ID: { anime_id: anime_data }
        self.favoritos = {}

        # Estado da Navegação e Filtros
        self.aba_atual = "dashboard"
        self.dia_selecionado = datetime.datetime.now().weekday()
        self.botoes_dias = {}
        self.botoes_menu = {}

        # Layout Principal: Sidebar + Conteúdo
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()

        # Iniciar no Dashboard
        self.mudar_aba("dashboard")

    # ================= 1. CRIAÇÃO DO SIDEBAR (MENU LATERAL) =================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=self.COLOR_SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # Logo / Ícone Superior
        lbl_logo = ctk.CTkLabel(
            self.sidebar,
            text="▶",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.COLOR_ACCENT,
        )
        lbl_logo.pack(pady=(25, 20))

        # Menu de Navegação
        itens_menu = [
            ("🏠 Dashboard", "dashboard"),
            ("📅 Meu Calendário", "calendario"),
            ("🔍 Explorar", "explorar"),
            ("⭐ Populares", "populares"),
            ("⚙️ Configurações", "configuracoes"),
        ]

        for texto, chave in itens_menu:
            btn = ctk.CTkButton(
                self.sidebar,
                text=texto,
                anchor="w",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color=self.COLOR_TEXT_MUTED,
                hover_color="#1E293B",
                command=lambda k=chave: self.mudar_aba(k),
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.botoes_menu[chave] = btn

        # Perfil do Usuário no Rodapé
        frame_perfil = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame_perfil.pack(side="bottom", fill="x", padx=15, pady=20)

        lbl_perfil_icon = ctk.CTkLabel(
            frame_perfil, text="👤", font=ctk.CTkFont(size=20)
        )
        lbl_perfil_icon.pack(side="left", padx=(0, 10))

        frame_user_info = ctk.CTkFrame(frame_perfil, fg_color="transparent")
        frame_user_info.pack(side="left")

        lbl_user_name = ctk.CTkLabel(
            frame_user_info,
            text="PERFIL",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN,
        )
        lbl_user_name.pack(anchor="w")

        lbl_user_status = ctk.CTkLabel(
            frame_user_info,
            text="Usuário Conectado",
            font=ctk.CTkFont(size=10),
            text_color=self.COLOR_TEXT_MUTED,
        )
        lbl_user_status.pack(anchor="w")

    # ================= 2. CRIAÇÃO DA ÁREA PRINCIPAL =================
    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=25, pady=20)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Cabeçalho Principal
        self.lbl_header = ctk.CTkLabel(
            self.main_frame,
            text="CALENDÁRIO DE LANÇAMENTOS | SÉRIES & ANIME",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN,
            anchor="w",
        )
        self.lbl_header.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Container Secundário para Filtros/Dias (Linha 1)
        self.frame_top_controls = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_top_controls.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Container Rolar de Cards / Conteúdo (Linha 2)
        self.scroll_cards = ctk.CTkScrollableFrame(
            self.main_frame, fg_color="transparent"
        )
        self.scroll_cards.grid(row=2, column=0, sticky="nsew")

        for i in range(4):
            self.scroll_cards.grid_columnconfigure(i, weight=1)

    # ================= GERENCIADOR DE ABAS =================
    def mudar_aba(self, chave_aba):
        self.aba_atual = chave_aba

        # Atualiza a interface visual dos botões da sidebar
        for k, btn in self.botoes_menu.items():
            if k == chave_aba:
                btn.configure(fg_color="#1E293B", text_color=self.COLOR_ACCENT, font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=self.COLOR_TEXT_MUTED, font=ctk.CTkFont(size=13, weight="normal"))

        # Limpar controles superiores e grid de conteúdo
        for w in self.frame_top_controls.winfo_children():
            w.destroy()
        for w in self.scroll_cards.winfo_children():
            w.destroy()

        # Renderizar de acordo com a aba selecionada
        if chave_aba == "dashboard":
            self.lbl_header.configure(text="🏠 DASHBOARD DE LANÇAMENTOS")
            self.setup_bar_dias()
            self.selecionar_dia(self.dia_selecionado)

        elif chave_aba == "calendario":
            self.lbl_header.configure(text="📅 MEU CALENDÁRIO (FAVORITOS)")
            self.carregar_meu_calendario()

        elif chave_aba == "explorar":
            self.lbl_header.configure(text="🔍 EXPLORAR ANIMES")
            self.setup_filtros_explorar()
            self.executar_busca_explorar()

        elif chave_aba == "populares":
            self.lbl_header.configure(text="⭐ POPULARES DOS ÚLTIMOS 3 MESES")
            self.carregar_populares_3_meses()

        elif chave_aba == "configuracoes":
            self.lbl_header.configure(text="⚙️ CONFIGURAÇÕES DO SISTEMA")
            self.setup_tela_configuracoes()

    # ================= LÓGICA DE FAVORITOS / "MEU CALENDÁRIO" =================
    def alternar_favorito(self, anime):
        anime_id = anime["id"]
        if anime_id in self.favoritos:
            del self.favoritos[anime_id]
        else:
            self.favoritos[anime_id] = anime

        # Se estiver no "Meu Calendário", re-renderiza a lista imediatamente
        if self.aba_atual == "calendario":
            self.carregar_meu_calendario()

    def carregar_meu_calendario(self):
        lista_favs = list(self.favoritos.values())
        self.renderizar_cards(lista_favs, modo_meu_calendario=True)

    # ================= 3. ABA: DASHBOARD / CALENDÁRIO GERAL =================
    def setup_bar_dias(self):
        for idx in range(7):
            self.frame_top_controls.grid_columnconfigure(idx, weight=1)

        for nome_pt, nome_en, num_dia in self.DIAS_DA_SEMANA:
            btn = ctk.CTkButton(
                self.frame_top_controls,
                text=f"{nome_pt}\n{nome_en}",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=50,
                corner_radius=10,
                fg_color=self.COLOR_CARD,
                text_color=self.COLOR_TEXT_MUTED,
                hover_color="#243044",
                command=lambda d=num_dia: self.selecionar_dia(d),
            )
            btn.grid(row=0, column=num_dia, padx=4, sticky="ew")
            self.botoes_dias[num_dia] = btn

    def selecionar_dia(self, num_dia):
        self.dia_selecionado = num_dia

        for d, btn in self.botoes_dias.items():
            if d == num_dia:
                btn.configure(fg_color=self.COLOR_ACCENT, text_color="#FFFFFF")
            else:
                btn.configure(fg_color=self.COLOR_CARD, text_color=self.COLOR_TEXT_MUTED)

        self.mostrar_loading()
        threading.Thread(
            target=self.buscar_animes_anilist, args=(num_dia,), daemon=True
        ).start()

    def buscar_animes_anilist(self, dia_num):
        url = "https://graphql.anilist.co"
        query = """
        query {
          Page(page: 1, perPage: 50) {
            media(status: RELEASING, type: ANIME, sort: POPULARITY_DESC) {
              id
              title { english romaji native }
              coverImage { extraLarge large }
              averageScore
              episodes
              genres
              description(asHtml: false)
              trailer { id site }
              nextAiringEpisode { airingAt episode }
              startDate { year month day }
            }
          }
        }
        """
        try:
            response = requests.post(url, json={"query": query}, timeout=10)
            if response.status_code == 200:
                dados = response.json().get("data", {}).get("Page", {}).get("media", [])
                animes_filtrados = []

                for anime in dados:
                    next_ep = anime.get("nextAiringEpisode")
                    if next_ep and "airingAt" in next_ep:
                        dt = datetime.datetime.fromtimestamp(next_ep["airingAt"])
                        if dt.weekday() == dia_num:
                            animes_filtrados.append(anime)
                    else:
                        st = anime.get("startDate", {})
                        if st.get("year") and st.get("month") and st.get("day"):
                            try:
                                dt = datetime.date(st["year"], st["month"], st["day"])
                                if dt.weekday() == dia_num:
                                    animes_filtrados.append(anime)
                            except ValueError:
                                pass

                for anime in animes_filtrados:
                    cover_url = anime.get("coverImage", {}).get("large")
                    anime["pil_image"] = self.baixar_imagem(cover_url)

                self.after(0, lambda: self.renderizar_cards(animes_filtrados))
        except Exception as e:
            self.after(0, lambda: self.exibir_erro(f"Erro de conexão ao buscar animes: {e}"))

    # ================= 4. ABA: EXPLORAR (BUSCA & GÊNEROS) =================
    def setup_filtros_explorar(self):
        self.frame_top_controls.grid_columnconfigure(0, weight=3)
        self.frame_top_controls.grid_columnconfigure(1, weight=1)
        self.frame_top_controls.grid_columnconfigure(2, weight=1)

        self.entry_busca = ctk.CTkEntry(
            self.frame_top_controls,
            placeholder_text="Digite o nome do anime...",
            height=40,
            fg_color=self.COLOR_CARD,
            border_color="#243044",
            text_color=self.COLOR_TEXT_MAIN
        )
        self.entry_busca.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.entry_busca.bind("<Return>", lambda e: self.executar_busca_explorar())

        self.combo_genero = ctk.CTkOptionMenu(
            self.frame_top_controls,
            values=self.GENEROS_DISPONIVEIS,
            height=40,
            fg_color=self.COLOR_CARD,
            button_color=self.COLOR_ACCENT,
            dropdown_fg_color=self.COLOR_CARD,
            text_color=self.COLOR_TEXT_MAIN
        )
        self.combo_genero.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        btn_buscar = ctk.CTkButton(
            self.frame_top_controls,
            text="Buscar",
            height=40,
            fg_color=self.COLOR_ACCENT,
            font=ctk.CTkFont(weight="bold"),
            command=self.executar_busca_explorar
        )
        btn_buscar.grid(row=0, column=2, sticky="ew")

    def executar_busca_explorar(self):
        texto = self.entry_busca.get().strip() if hasattr(self, 'entry_busca') else ""
        genero = self.combo_genero.get() if hasattr(self, 'combo_genero') else "Todos"
        
        self.mostrar_loading()
        threading.Thread(
            target=self.api_buscar_explorar, args=(texto, genero), daemon=True
        ).start()

    def api_buscar_explorar(self, termo, genero):
        url = "https://graphql.anilist.co"
        query = """
        query ($search: String, $genre: String) {
          Page(page: 1, perPage: 28) {
            media(search: $search, genre: $genre, type: ANIME, sort: POPULARITY_DESC) {
              id
              title { english romaji native }
              coverImage { extraLarge large }
              averageScore
              episodes
              genres
              description(asHtml: false)
              trailer { id site }
              nextAiringEpisode { airingAt episode }
            }
          }
        }
        """
        variables = {}
        if termo:
            variables["search"] = termo
        if genero and genero != "Todos":
            variables["genre"] = genero

        try:
            response = requests.post(url, json={"query": query, "variables": variables}, timeout=10)
            if response.status_code == 200:
                dados = response.json().get("data", {}).get("Page", {}).get("media", [])
                for anime in dados:
                    cover_url = anime.get("coverImage", {}).get("large")
                    anime["pil_image"] = self.baixar_imagem(cover_url)
                self.after(0, lambda: self.renderizar_cards(dados))
        except Exception as e:
            self.after(0, lambda: self.exibir_erro(f"Erro ao buscar explorar: {e}"))

    # ================= 5. ABA: POPULARES =================
    def carregar_populares_3_meses(self):
        self.mostrar_loading()
        threading.Thread(target=self.api_buscar_populares, daemon=True).start()

    def api_buscar_populares(self):
        data_3_meses_atras = datetime.date.today() - datetime.timedelta(days=90)
        start_date_int = int(data_3_meses_atras.strftime("%Y%m%d"))

        url = "https://graphql.anilist.co"
        query = """
        query ($startDate: Int) {
          Page(page: 1, perPage: 24) {
            media(startDate_greater: $startDate, type: ANIME, sort: [SCORE_DESC, POPULARITY_DESC]) {
              id
              title { english romaji native }
              coverImage { extraLarge large }
              averageScore
              episodes
              genres
              description(asHtml: false)
              trailer { id site }
              nextAiringEpisode { airingAt episode }
            }
          }
        }
        """
        try:
            response = requests.post(url, json={"query": query, "variables": {"startDate": start_date_int}}, timeout=10)
            if response.status_code == 200:
                dados = response.json().get("data", {}).get("Page", {}).get("media", [])
                for anime in dados:
                    cover_url = anime.get("coverImage", {}).get("large")
                    anime["pil_image"] = self.baixar_imagem(cover_url)
                self.after(0, lambda: self.renderizar_cards(dados))
        except Exception as e:
            self.after(0, lambda: self.exibir_erro(f"Erro ao buscar populares: {e}"))

    # ================= 6. ABA: CONFIGURAÇÕES =================
    def setup_tela_configuracoes(self):
        frame_config = ctk.CTkFrame(self.scroll_cards, fg_color=self.COLOR_CARD, corner_radius=12)
        frame_config.pack(fill="x", padx=20, pady=20)

        lbl_titulo = ctk.CTkLabel(
            frame_config, 
            text="Personalização Visual", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN
        )
        lbl_titulo.pack(anchor="w", padx=20, pady=(20, 15))

        lbl_cor = ctk.CTkLabel(frame_config, text="Cor de Fundo da Aplicação:", text_color=self.COLOR_TEXT_MUTED)
        lbl_cor.pack(anchor="w", padx=20, pady=(0, 5))

        cores = [
            ("Escuro Padrão", "#0B0E14"),
            ("Preto Puro", "#000000"),
            ("Azul Noturno", "#0A1128"),
            ("Cinza Chumbo", "#18181B"),
            ("Roxo Escuro", "#130E26")
        ]

        frame_botoes_cor = ctk.CTkFrame(frame_config, fg_color="transparent")
        frame_botoes_cor.pack(anchor="w", padx=20, pady=(0, 20))

        for nome, hex_code in cores:
            btn_c = ctk.CTkButton(
                frame_botoes_cor,
                text=nome,
                fg_color=hex_code,
                hover_color="#334155",
                width=100,
                command=lambda c=hex_code: self.alterar_cor_fundo(c)
            )
            btn_c.pack(side="left", padx=5)

        lbl_tema = ctk.CTkLabel(frame_config, text="Modo de Exibição:", text_color=self.COLOR_TEXT_MUTED)
        lbl_tema.pack(anchor="w", padx=20, pady=(10, 5))

        switch_tema = ctk.CTkOptionMenu(
            frame_config,
            values=["Dark", "Light", "System"],
            command=lambda modo: ctk.set_appearance_mode(modo),
            fg_color="#243044",
            button_color=self.COLOR_ACCENT
        )
        switch_tema.pack(anchor="w", padx=20, pady=(0, 20))

    def alterar_cor_fundo(self, nova_cor_hex):
        self.COLOR_BG = nova_cor_hex
        self.configure(fg_color=self.COLOR_BG)

    # ================= UTILITÁRIOS E AUXILIARES =================
    def mostrar_loading(self):
        for widget in self.scroll_cards.winfo_children():
            widget.destroy()
        lbl_loading = ctk.CTkLabel(
            self.scroll_cards,
            text="⏳ Carregando dados...",
            font=ctk.CTkFont(size=16),
            text_color=self.COLOR_TEXT_MUTED,
        )
        lbl_loading.grid(row=0, column=0, columnspan=4, pady=50)

    def baixar_imagem(self, url):
        if not url:
            return None
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content))
        except Exception:
            pass
        return None

    def exibir_erro(self, mensagem):
        for widget in self.scroll_cards.winfo_children():
            widget.destroy()
        lbl_err = ctk.CTkLabel(
            self.scroll_cards, text=mensagem, text_color="#EF4444"
        )
        lbl_err.grid(row=0, column=0, columnspan=4, pady=40)

    # ================= RENDERIZAÇÃO DOS CARDS =================
    def renderizar_cards(self, lista_animes, modo_meu_calendario=False):
        for widget in self.scroll_cards.winfo_children():
            widget.destroy()

        if not lista_animes:
            texto_vazio = (
                "Sua lista está vazia! Adicione animes aos favoritos no Dashboard para acompanhá-los aqui."
                if modo_meu_calendario else
                "Nenhum anime encontrado para este filtro."
            )
            lbl_vazio = ctk.CTkLabel(
                self.scroll_cards,
                text=texto_vazio,
                font=ctk.CTkFont(size=14),
                text_color=self.COLOR_TEXT_MUTED,
            )
            lbl_vazio.grid(row=0, column=0, columnspan=4, pady=50)
            return

        col_max = 4
        for index, anime in enumerate(lista_animes):
            row = index // col_max
            col = index % col_max

            card = ctk.CTkFrame(
                self.scroll_cards,
                fg_color=self.COLOR_CARD,
                corner_radius=12,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=8, pady=10, sticky="nsew")

            # Imagem de Capa
            pil_img = anime.get("pil_image")
            if pil_img:
                ctk_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img, size=(180, 240)
                )
                lbl_cover = ctk.CTkLabel(card, image=ctk_img, text="")
            else:
                lbl_cover = ctk.CTkLabel(
                    card,
                    text="Sem Imagem",
                    width=180,
                    height=240,
                    fg_color="#1E293B",
                    corner_radius=8,
                )
            lbl_cover.pack(padx=10, pady=(10, 8))

            # Título do Anime
            titles = anime.get("title", {})
            titulo = titles.get("english") or titles.get("romaji") or "Sem Título"

            lbl_title = ctk.CTkLabel(
                card,
                text=titulo,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.COLOR_TEXT_MAIN,
                wraplength=170,
                justify="center",
            )
            lbl_title.pack(padx=8, pady=(0, 2))

            # Informações do Episódio / Nota
            next_ep = anime.get("nextAiringEpisode")
            ep_txt = f"EP {next_ep['episode']}" if next_ep else "Lançado / Em breve"

            lbl_info = ctk.CTkLabel(
                card,
                text=ep_txt,
                font=ctk.CTkFont(size=11),
                text_color=self.COLOR_TEXT_MUTED,
            )
            lbl_info.pack(padx=8, pady=(0, 4))

            # BOTÕES DE AÇÃO (Favoritar e Assistido)
            frame_acoes = ctk.CTkFrame(card, fg_color="transparent")
            frame_acoes.pack(fill="x", padx=8, pady=(0, 10))

            is_fav = anime["id"] in self.favoritos

            if modo_meu_calendario:
                # Na aba "Meu Calendário": Botão para marcar como Assistido (remover da lista)
                btn_assistido = ctk.CTkButton(
                    frame_acoes,
                    text="✅ Assistido",
                    height=30,
                    fg_color="#10B981",
                    hover_color="#059669",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda a=anime: self.alternar_favorito(a)
                )
                btn_assistido.pack(fill="x", expand=True)
            else:
                # Nas outras abas: Botão de Favoritar (❤️)
                btn_fav = ctk.CTkButton(
                    frame_acoes,
                    text="❤️ Favorito" if is_fav else "🤍 Favoritar",
                    height=30,
                    fg_color="#EC4899" if is_fav else "#334155",
                    hover_color="#DB2777" if is_fav else "#475569",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda a=anime, b=card: self.acao_favoritar_card(a)
                )
                btn_fav.pack(fill="x", expand=True)

            # Clique no Card/Imagem abre detalhes
            bind_click = lambda e, a=anime: self.abrir_modal_detalhes(a)
            card.bind("<Button-1>", bind_click)
            lbl_cover.bind("<Button-1>", bind_click)
            lbl_title.bind("<Button-1>", bind_click)

    def acao_favoritar_card(self, anime):
        self.alternar_favorito(anime)
        # Se estivéssemos numa listagem normal, recarregamos a aba atual para atualizar as cores dos botões
        if self.aba_atual == "explorar":
            self.executar_busca_explorar()
        elif self.aba_atual == "dashboard":
            self.selecionar_dia(self.dia_selecionado)
        elif self.aba_atual == "populares":
            self.carregar_populares_3_meses()

    # ================= POP-UP DE DETALHES =================
    def abrir_modal_detalhes(self, anime):
        modal = ctk.CTkToplevel(self)
        modal.title("Detalhes do Anime")
        modal.geometry("600x550")
        modal.configure(fg_color=self.COLOR_BG)
        modal.transient(self)
        modal.grab_set()

        scroll_modal = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll_modal.pack(fill="both", expand=True, padx=20, pady=20)

        titles = anime.get("title", {})
        titulo = titles.get("english") or titles.get("romaji") or "Sem Título"

        lbl_modal_titulo = ctk.CTkLabel(
            scroll_modal,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.COLOR_TEXT_MAIN,
            wraplength=540,
            justify="left",
        )
        lbl_modal_titulo.pack(anchor="w", pady=(0, 10))

        trailer = anime.get("trailer")
        if trailer and trailer.get("site") == "youtube" and trailer.get("id"):
            youtube_url = f"https://www.youtube.com/watch?v={trailer['id']}"
            btn_trailer = ctk.CTkButton(
                scroll_modal,
                text="🎬 Assistir Trailer no YouTube",
                fg_color="#DC2626",
                hover_color="#B91C1C",
                font=ctk.CTkFont(weight="bold"),
                command=lambda: webbrowser.open(youtube_url),
            )
            btn_trailer.pack(fill="x", pady=(0, 15))

        lbl_syn_title = ctk.CTkLabel(
            scroll_modal,
            text="Sinopse:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLOR_ACCENT,
        )
        lbl_syn_title.pack(anchor="w", pady=(5, 2))

        sinopse_limpa = limpar_html(anime.get("description"))
        lbl_sinopse = ctk.CTkLabel(
            scroll_modal,
            text=sinopse_limpa,
            font=ctk.CTkFont(size=12),
            text_color=self.COLOR_TEXT_MUTED,
            justify="left",
            anchor="w",
            wraplength=540,
        )
        lbl_sinopse.pack(fill="x", anchor="w", pady=(0, 15))


if __name__ == "__main__":
    app = AppCalendarioAnime()
    app.mainloop()
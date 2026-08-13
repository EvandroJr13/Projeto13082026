import datetime
import io
import re
import threading
import webbrowser
import customtkinter as ctk
from PIL import Image
import requests

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def limpar_html(texto):
    """Remove tags HTML (como <br>, <i>) do texto da sinopse."""
    if not texto:
        return "Sinopse não disponível para este anime."
    clean = re.compile("<.*?>")
    return re.sub(clean, "", texto)


class AppPainelRedimensionavel(ctk.CTk):

    DIAS_DA_SEMANA = [
        ("Segunda-feira", 0),
        ("Terça-feira", 1),
        ("Quarta-feira", 2),
        ("Quinta-feira", 3),
        ("Sexta-feira", 4),
        ("Sábado", 5),
        ("Domingo", 6),
    ]

    def __init__(self):
        super().__init__()
        self.title("Calendário de Animes - AniList API")
        self.geometry("950x700")

        self.grid_rowconfigure(0, weight=1)

        self.largura_minima = 160
        self.largura_maxima = 400
        self.largura_atual = 220

        # ================= 1. PAINEL LATERAL =================
        self.sidebar = ctk.CTkFrame(self, width=self.largura_atual, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.sidebar.pack_propagate(False)
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # ---------------- 7 BOTÕES (SEGUNDA A DOMINGO) ----------------
        self.botoes = {}

        for index, (nome_dia, dia_num) in enumerate(self.DIAS_DA_SEMANA):
            self.sidebar.grid_rowconfigure(index, weight=1)

            btn = ctk.CTkButton(
                self.sidebar,
                text=f"📅 {nome_dia}",
                command=lambda d_num=dia_num, n_dia=nome_dia: self.ao_clicar_botao(
                    d_num, n_dia
                ),
            )
            btn.grid(row=index, column=0, sticky="nsew", padx=10, pady=5)
            self.botoes[f"btn_dia_{dia_num}"] = btn

        # ================= 2. BARRA DIVISÓRIA (SPLITTER) =================
        self.splitter = ctk.CTkFrame(
            self, width=6, cursor="sb_h_double_arrow", fg_color="#374151"
        )
        self.splitter.grid(row=0, column=1, sticky="nsew")
        self.splitter.bind("<B1-Motion>", self.arrastar_divisoria)

        # ================= 3. CONTEÚDO PRINCIPAL =================
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=2, sticky="nsew")
        self.grid_columnconfigure(2, weight=1)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.lbl_main = ctk.CTkLabel(
            self.main_frame,
            text="Selecione um dia da semana no menu lateral",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.lbl_main.grid(row=0, column=0, pady=20, padx=20, sticky="w")

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.main_frame, label_text="Animes Agendados (Clique em um card para ver detalhes)"
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

    # ================= MÉTODOS DE FUNCIONALIDADE =================

    def arrastar_divisoria(self, event):
        x_mouse_janela = event.x_root - self.winfo_rootx()
        if self.largura_minima <= x_mouse_janela <= self.largura_maxima:
            self.sidebar.configure(width=x_mouse_janela)

    def ao_clicar_botao(self, dia_num, nome_dia):
        self.lbl_main.configure(
            text=f"⏳ Buscando animes de {nome_dia} na AniList..."
        )

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        threading.Thread(
            target=self.buscar_animes_anilist,
            args=(dia_num, nome_dia),
            daemon=True,
        ).start()

    def buscar_animes_anilist(self, dia_num, nome_dia):
        """Consulta AniList buscando dados completos incluindo sinopse, estúdio e links externos."""
        url = "https://graphql.anilist.co"

        # Consulta GraphQL expandida
        query = """
        query {
          Page(page: 1, perPage: 100) {
            media(status: RELEASING, type: ANIME, sort: POPULARITY_DESC) {
              id
              title {
                romaji
                english
                native
              }
              coverImage {
                large
                extraLarge
              }
              bannerImage
              averageScore
              episodes
              genres
              status
              seasonYear
              description(asHtml: false)
              trailer {
                id
                site
              }
              studios(isMain: true) {
                nodes {
                  name
                }
              }
              externalLinks {
                site
                url
                type
                icon
              }
              nextAiringEpisode {
                airingAt
                episode
              }
              startDate {
                year
                month
                day
              }
            }
          }
        }
        """

        try:
            response = requests.post(url, json={"query": query}, timeout=12)

            if response.status_code == 200:
                dados = (
                    response.json()
                    .get("data", {})
                    .get("Page", {})
                    .get("media", [])
                )

                animes_do_dia = []

                for anime in dados:
                    next_ep = anime.get("nextAiringEpisode")

                    if next_ep and "airingAt" in next_ep:
                        timestamp = next_ep["airingAt"]
                        dt = datetime.datetime.fromtimestamp(timestamp)
                        if dt.weekday() == dia_num:
                            animes_do_dia.append(anime)
                    else:
                        st = anime.get("startDate", {})
                        if st.get("year") and st.get("month") and st.get("day"):
                            try:
                                dt = datetime.date(st["year"], st["month"], st["day"])
                                if dt.weekday() == dia_num:
                                    animes_do_dia.append(anime)
                            except ValueError:
                                pass

                # Pré-carrega as capas
                for anime in animes_do_dia:
                    cover_url = anime.get("coverImage", {}).get("large")
                    anime["pil_image"] = self.baixar_imagem_pil(cover_url)

                self.after(
                    0, lambda: self.exibir_animes(animes_do_dia, nome_dia)
                )
            else:
                msg = f"Erro HTTP {response.status_code}: Servidor AniList indisponível."
                self.after(0, lambda: self.lbl_main.configure(text=msg))

        except Exception as e:
            self.after(
                0, lambda: self.lbl_main.configure(text=f"Erro de conexão: {e}")
            )

    def baixar_imagem_pil(self, url):
        if not url:
            return None
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content))
        except Exception:
            pass
        return None

    def exibir_animes(self, lista_animes, nome_dia):
        """Renderiza os retângulos dos animes com clique habilitado."""
        if lista_animes:
            titulo_txt = f"📅 Animes de {nome_dia} ({len(lista_animes)} encontrados)"
        else:
            titulo_txt = f"📅 Nenhum anime agendado para {nome_dia} no momento."

        self.lbl_main.configure(text=titulo_txt)

        for anime in lista_animes:
            titles = anime.get("title", {})
            titulo = titles.get("english") or titles.get("romaji") or "Sem Título"

            score = anime.get("averageScore")
            nota = f"{score / 10:.1f}" if score else "N/A"

            episodes = anime.get("episodes") or "Em exibição"
            generos = ", ".join(anime.get("genres", [])[:3]) or "Geral"

            next_ep = anime.get("nextAiringEpisode")
            ep_info = f"Episódio {next_ep['episode']}" if next_ep else "Lançamento em dia"

            # CARD RETANGULAR
            card = ctk.CTkFrame(self.scroll_frame, corner_radius=10, cursor="hand2")
            card.pack(fill="x", pady=8, padx=5)

            card.grid_columnconfigure(1, weight=1)

            # Capa
            pil_img = anime.get("pil_image")
            if pil_img:
                ctk_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img, size=(110, 155)
                )
                lbl_foto = ctk.CTkLabel(card, image=ctk_img, text="")
            else:
                lbl_foto = ctk.CTkLabel(
                    card,
                    text="🖼️\nSem Foto",
                    width=110,
                    height=155,
                    fg_color="#1f2937",
                    corner_radius=6,
                )

            lbl_foto.grid(row=0, column=0, padx=12, pady=12, sticky="n")

            # Área de textos
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")

            lbl_titulo = ctk.CTkLabel(
                info_frame,
                text=titulo,
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w",
                justify="left",
                wraplength=420,
            )
            lbl_titulo.pack(fill="x", anchor="w", pady=(0, 4))

            lbl_nota = ctk.CTkLabel(
                info_frame,
                text=f"⭐ Avaliação: {nota} / 10 | 📺 Total Eps: {episodes}",
                font=ctk.CTkFont(size=13),
                anchor="w",
            )
            lbl_nota.pack(fill="x", anchor="w", pady=2)

            lbl_proximo = ctk.CTkLabel(
                info_frame,
                text=f"🚀 Próximo: {ep_info} | 🏷️ Gêneros: {generos}",
                font=ctk.CTkFont(size=12),
                text_color="#9ca3af",
                anchor="w",
            )
            lbl_proximo.pack(fill="x", anchor="w", pady=2)

            # Botão de Ação para Detalhes
            btn_detalhes = ctk.CTkButton(
                info_frame,
                text="🔍 Ver Onde Assistir & Detalhes",
                height=28,
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                command=lambda a=anime: self.abrir_modal_detalhes(a),
            )
            btn_detalhes.pack(anchor="w", pady=(8, 0))

            # Torna o card inteiro clicável
            card.bind("<Button-1>", lambda e, a=anime: self.abrir_modal_detalhes(a))
            lbl_foto.bind("<Button-1>", lambda e, a=anime: self.abrir_modal_detalhes(a))
            info_frame.bind("<Button-1>", lambda e, a=anime: self.abrir_modal_detalhes(a))

    # ================= POP-UP DE DETALHES (MODAL) =================

    def abrir_modal_detalhes(self, anime):
        """Abre uma janela Pop-up com detalhes, trailer e plataformas de streaming."""
        modal = ctk.CTkToplevel(self)
        modal.title("Detalhes do Anime")
        modal.geometry("700x650")
        modal.transient(self)
        modal.grab_set()  # Foca no Pop-up até fechar

        # Frame com scroll no modal
        scroll_modal = ctk.CTkScrollableFrame(modal)
        scroll_modal.pack(fill="both", expand=True, padx=15, pady=15)

        titles = anime.get("title", {})
        titulo_principal = titles.get("english") or titles.get("romaji") or "Sem Título"
        titulo_nativo = titles.get("native", "")

        # 1. TÍTULO
        lbl_modal_titulo = ctk.CTkLabel(
            scroll_modal,
            text=titulo_principal,
            font=ctk.CTkFont(size=20, weight="bold"),
            wraplength=630,
            justify="left",
        )
        lbl_modal_titulo.pack(anchor="w", pady=(0, 2))

        if titulo_nativo:
            lbl_nativo = ctk.CTkLabel(
                scroll_modal,
                text=f"Original: {titulo_nativo}",
                font=ctk.CTkFont(size=12),
                text_color="#9ca3af",
            )
            lbl_nativo.pack(anchor="w", pady=(0, 10))

        # 2. INFORMAÇÕES TÉCNICAS (GRID)
        info_tech_frame = ctk.CTkFrame(scroll_modal, fg_color="#1f2937", corner_radius=8)
        info_tech_frame.pack(fill="x", pady=10, ipady=5)

        score = anime.get("averageScore")
        nota = f"{score/10:.1f} / 10" if score else "N/A"
        
        studios = anime.get("studios", {}).get("nodes", [])
        estudio_nome = studios[0]["name"] if studios else "Desconhecido"
        
        generos = ", ".join(anime.get("genres", [])) or "Geral"
        ano = anime.get("seasonYear") or "N/A"

        txt_info = (
            f"⭐ **Nota:** {nota}   |   🏢 **Estúdio:** {estudio_nome}   |   📅 **Ano:** {ano}\n"
            f"🏷️ **Gêneros:** {generos}"
        )
        lbl_info_tech = ctk.CTkLabel(
            info_tech_frame,
            text=txt_info,
            font=ctk.CTkFont(size=13),
            justify="left",
            anchor="w",
        )
        lbl_info_tech.pack(fill="x", padx=15, pady=8)

        # 3. BOTÃO DE TRAILER (SE HOUVER YOUTUBE)
        trailer_data = anime.get("trailer")
        if trailer_data and trailer_data.get("site") == "youtube" and trailer_data.get("id"):
            youtube_url = f"https://www.youtube.com/watch?v={trailer_data['id']}"
            btn_trailer = ctk.CTkButton(
                scroll_modal,
                text="🎬 Assistir Trailer Oficial no YouTube",
                fg_color="#dc2626",
                hover_color="#b91c1c",
                font=ctk.CTkFont(weight="bold"),
                command=lambda: webbrowser.open(youtube_url),
            )
            btn_trailer.pack(fill="x", pady=10)

        # 4. ONDE ASSISTIR (STREAMING LINKS)
        lbl_onde = ctk.CTkLabel(
            scroll_modal,
            text="📺 Onde Assistir (Plataformas Oficiais):",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        lbl_onde.pack(anchor="w", pady=(15, 5))

        links_externos = anime.get("externalLinks", [])
        # Filtra apenas links de streaming ou oficiais
        stream_links = [
            l for l in links_externos if l.get("type") in ["STREAMING", "INFO"] or "Crunchyroll" in l.get("site", "") or "Netflix" in l.get("site", "")
        ]

        if stream_links:
            frame_links = ctk.CTkFrame(scroll_modal, fg_color="transparent")
            frame_links.pack(fill="x", pady=5)

            for link in stream_links:
                nome_site = link.get("site", "Link")
                url_site = link.get("url")

                if url_site:
                    btn_stream = ctk.CTkButton(
                        frame_links,
                        text=f"🔗 {nome_site}",
                        height=32,
                        fg_color="#059669",
                        hover_color="#047857",
                        command=lambda u=url_site: webbrowser.open(u),
                    )
                    btn_stream.pack(side="left", padx=4, pady=4)
        else:
            lbl_sem_link = ctk.CTkLabel(
                scroll_modal,
                text="Nenhuma plataforma de streaming cadastrada diretamente para esta região.",
                font=ctk.CTkFont(size=12),
                text_color="#9ca3af",
            )
            lbl_sem_link.pack(anchor="w")

        # 5. SINOPSE COMPLETA
        lbl_sinopse_titulo = ctk.CTkLabel(
            scroll_modal,
            text="📖 Sinopse:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        lbl_sinopse_titulo.pack(anchor="w", pady=(20, 5))

        sinopse_limpa = limpar_html(anime.get("description"))
        lbl_sinopse = ctk.CTkLabel(
            scroll_modal,
            text=sinopse_limpa,
            font=ctk.CTkFont(size=13),
            justify="left",
            anchor="w",
            wraplength=630,
        )
        lbl_sinopse.pack(fill="x", anchor="w", pady=(0, 15))


if __name__ == "__main__":
    app = AppPainelRedimensionavel()
    app.mainloop()
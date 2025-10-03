import pygame
import sys
import json
import copy
import bot
import chess_core
import gui

def carica_config(path="config.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def scegli_modalita_gui(screen):
    """Schermata di selezione modalità con grafica migliorata."""
    pygame.font.init()
    
    # Dimensioni finestra
    larg, alt = 800, 600
    screen = pygame.display.set_mode((larg, alt))
    pygame.display.set_caption("Scacchi Facili - Selezione Modalità")
    
    # Font
    font_title = pygame.font.SysFont("arial", 72, bold=True)
    font_subtitle = pygame.font.SysFont("arial", 28)
    font_card_title = pygame.font.SysFont("arial", 28, bold=True)  # Ridotto da 32
    font_card_desc = pygame.font.SysFont("arial", 16)  # Ridotto da 18
    font_emoji = pygame.font.SysFont("segoe ui emoji", 48)
    
    # Colori tema scacchi
    color_light = (235, 235, 208)
    color_dark = (119, 148, 85)
    color_accent = (255, 215, 0)
    
    # Opzioni con emoji e descrizioni
    opzioni = [
        {
            "code": "PvP",
            "emoji": "👥",
            "title": "Giocatore vs Giocatore",
            "desc": "Sfida un amico sulla stessa scacchiera",
            "color": (100, 150, 255)
        },
        {
            "code": "PvE",
            "emoji": "🤖",
            "title": "Giocatore vs Bot",
            "desc": "Affronta l'intelligenza artificiale",
            "color": (255, 100, 100)
        },
        {
            "code": "PvE_UNDO",
            "emoji": "⏪",
            "title": "PvE + Annulla Mossa",
            "desc": "Gioca vs bot con possibilità di annullare",
            "color": (150, 100, 255)
        }
    ]
    
    # Dimensioni card (aumentate)
    card_width = 450  # Aumentato da 320
    card_height = 120  # Ridotto da 140 per compattare
    card_spacing = 30
    total_height = len(opzioni) * card_height + (len(opzioni) - 1) * card_spacing
    start_y = (alt - total_height) // 2 + 80
    
    # Animazione titolo
    title_offset = 0
    clock = pygame.time.Clock()
    
    # Hover state
    hovered_card = None
    
    while True:
        # === SFONDO CON PATTERN SCACCHIERA ===
        # Gradiente verticale
        for y in range(alt):
            color_ratio = y / alt
            r = int(color_dark[0] + (color_light[0] - color_dark[0]) * color_ratio)
            g = int(color_dark[1] + (color_light[1] - color_dark[1]) * color_ratio)
            b = int(color_dark[2] + (color_light[2] - color_dark[2]) * color_ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (larg, y))
        
        # Pattern scacchiera trasparente in background
        tile_size = 60
        pattern_surface = pygame.Surface((larg, alt), pygame.SRCALPHA)
        for row in range(alt // tile_size + 1):
            for col in range(larg // tile_size + 1):
                if (row + col) % 2 == 0:
                    alpha = 20
                    color = (*color_dark, alpha)
                    pygame.draw.rect(pattern_surface, color, 
                                   (col * tile_size, row * tile_size, tile_size, tile_size))
        screen.blit(pattern_surface, (0, 0))
        
        # === TITOLO PRINCIPALE ===
        title_offset = (title_offset + 0.5) % 10
        
        # Ombra titolo
        title_shadow = font_title.render("♔ SCACCHI FACILI ♔", True, (0, 0, 0))
        title_rect_shadow = title_shadow.get_rect(center=(larg // 2 + 3, 70 + 3))
        screen.blit(title_shadow, title_rect_shadow)
        
        # Titolo con effetto oro
        title = font_title.render("♔ SCACCHI FACILI ♔", True, color_accent)
        title_rect = title.get_rect(center=(larg // 2, 70))
        screen.blit(title, title_rect)
        
        # Sottotitolo
        subtitle = font_subtitle.render("Scegli la tua modalità di gioco", True, (255, 255, 255))
        subtitle_rect = subtitle.get_rect(center=(larg // 2, 130))
        screen.blit(subtitle, subtitle_rect)
        
        # === CARD MODALITÀ ===
        mx, my = pygame.mouse.get_pos()
        cards_rects = []
        
        for i, opt in enumerate(opzioni):
            # Posizione card
            x = (larg - card_width) // 2
            y = start_y + i * (card_height + card_spacing)
            
            card_rect = pygame.Rect(x, y, card_width, card_height)
            cards_rects.append((card_rect, opt["code"]))
            
            # Hover detection
            is_hovered = card_rect.collidepoint(mx, my)
            if is_hovered:
                hovered_card = i
            
            # Animazione hover (lift effect)
            if is_hovered:
                y -= 5
                card_rect.y = y
            
            # === DISEGNA CARD ===
            # Ombra card
            shadow_rect = pygame.Rect(x + 6, y + 6, card_width, card_height)
            shadow_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 80))
            screen.blit(shadow_surface, shadow_rect)
            
            # Background card
            card_color = (255, 255, 255) if not is_hovered else (245, 245, 245)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            
            # Bordo colorato a sinistra
            border_rect = pygame.Rect(x, y, 8, card_height)
            pygame.draw.rect(screen, opt["color"], border_rect, border_radius=15)
            
            # Emoji
            emoji_surf = font_emoji.render(opt["emoji"], True, (0, 0, 0))
            emoji_rect = emoji_surf.get_rect(center=(x + 50, y + card_height // 2))
            screen.blit(emoji_surf, emoji_rect)
            
            # Area testo (con padding per evitare overflow)
            text_x = x + 100
            text_max_width = card_width - 110  # Margine destro
            
            # Titolo card
            title_card = font_card_title.render(opt["title"], True, (40, 40, 40))
            # Verifica che non esca dalla card
            if title_card.get_width() > text_max_width:
                # Riduci font se necessario (fallback)
                font_card_title_small = pygame.font.SysFont("arial", 24, bold=True)
                title_card = font_card_title_small.render(opt["title"], True, (40, 40, 40))
            screen.blit(title_card, (text_x, y + 25))
            
            # Descrizione
            desc_card = font_card_desc.render(opt["desc"], True, (100, 100, 100))
            screen.blit(desc_card, (text_x, y + 58))
            
            # Indicatore hover
            if is_hovered:
                hover_indicator = font_card_desc.render("▶ Clicca per iniziare", True, opt["color"])
                screen.blit(hover_indicator, (text_x, y + 85))
        
        # === FOOTER ===
        footer_font = pygame.font.SysFont("arial", 16)
        footer_text = footer_font.render("Creato con ❤️ - Usa i tasti 1, 2, 3 o il mouse", True, (255, 255, 255, 150))
        footer_rect = footer_text.get_rect(center=(larg // 2, alt - 30))
        screen.blit(footer_text, footer_rect)
        
        # === EVENTI ===
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for rect, code in cards_rects:
                    if rect.collidepoint(ev.pos):
                        # Animazione click
                        flash_surface = pygame.Surface((larg, alt), pygame.SRCALPHA)
                        flash_surface.fill((255, 255, 255, 100))
                        screen.blit(flash_surface, (0, 0))
                        pygame.display.flip()
                        pygame.time.delay(100)
                        return code
            
            # Supporto tastiera (1, 2, 3)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_1:
                    return "PvP"
                elif ev.key == pygame.K_2:
                    return "PvE"
                elif ev.key == pygame.K_3:
                    return "PvE_UNDO"
        
        pygame.display.flip()
        clock.tick(60)


def ricostruisci_cimiteri(storia):
    """Ricostruisce i cimiteri dalle mosse nella storia."""
    cem_w, cem_b = [], []
    board_temp = chess_core.crea_scacchiera()
    
    for notazione, board_after, _ in storia:
        for r in range(8):
            for c in range(8):
                prima = board_temp[r][c]
                dopo = board_after[r][c]
                if prima and not dopo:
                    found = False
                    for r2 in range(8):
                        for c2 in range(8):
                            if board_after[r2][c2] == prima and board_temp[r2][c2] != prima:
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        (cem_b if prima[0] == "b" else cem_w).append(gui.PEZZI_UNICODE[prima])
        
        board_temp = copy.deepcopy(board_after)
    
    return cem_w, cem_b


def calcola_valutazione_rapida(board, colore_turno):
    """Calcola velocemente la valutazione della posizione usando il bot."""
    return bot.valuta_posizione(board, "w")


def main():
    config = carica_config()
    screen = gui.inizializza_gui()
    clock = pygame.time.Clock()

    # Modalità di gioco
    modalita = scegli_modalita_gui(screen)
    bot_delay = config.get("bot_delay_ms", 0)
    screen = gui.inizializza_gui()

    # === STATO PARTITA ===
    partita_attiva = True
    replay_mode = False
    
    # === STORIA PARTITA ===
    storia_partita = []
    posizione_replay = 0
    
    # === STATO CORRENTE ===
    scacchiera = chess_core.crea_scacchiera()
    chess_core.reset_completo()
    selected = None
    cem_white, cem_black = [], []
    hint_free = hint_cap = None
    valutazione_corrente = 0
    
    # Salva stato iniziale
    board_iniziale = copy.deepcopy(scacchiera)
    stato_iniziale = chess_core.salva_stato_completo()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # === CONTROLLI REPLAY ===
            if not partita_attiva or replay_mode:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    buttons = gui.disegna_controlli_replay(screen)
                    
                    if buttons["start"].collidepoint(event.pos):
                        posizione_replay = 0
                        scacchiera = copy.deepcopy(board_iniziale)
                        chess_core.ripristina_stato_completo(stato_iniziale)
                        cem_white, cem_black = [], []
                        valutazione_corrente = 0
                        replay_mode = True
                        
                    elif buttons["prev"].collidepoint(event.pos) and posizione_replay > 0:
                        posizione_replay -= 1
                        if posizione_replay == 0:
                            scacchiera = copy.deepcopy(board_iniziale)
                            chess_core.ripristina_stato_completo(stato_iniziale)
                            cem_white, cem_black = [], []
                            valutazione_corrente = 0
                        else:
                            _, scacchiera, stato = storia_partita[posizione_replay - 1]
                            scacchiera = copy.deepcopy(scacchiera)
                            chess_core.ripristina_stato_completo(stato)
                            cem_white, cem_black = ricostruisci_cimiteri(storia_partita[:posizione_replay])
                            valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                        replay_mode = True
                        
                    elif buttons["next"].collidepoint(event.pos) and posizione_replay < len(storia_partita):
                        _, scacchiera, stato = storia_partita[posizione_replay]
                        scacchiera = copy.deepcopy(scacchiera)
                        chess_core.ripristina_stato_completo(stato)
                        posizione_replay += 1
                        cem_white, cem_black = ricostruisci_cimiteri(storia_partita[:posizione_replay])
                        valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                        replay_mode = True
                        
                    elif buttons["end"].collidepoint(event.pos):
                        if storia_partita:
                            posizione_replay = len(storia_partita)
                            _, scacchiera, stato = storia_partita[-1]
                            scacchiera = copy.deepcopy(scacchiera)
                            chess_core.ripristina_stato_completo(stato)
                            cem_white, cem_black = ricostruisci_cimiteri(storia_partita)
                            valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                        replay_mode = True
                        
                    elif buttons["resume"].collidepoint(event.pos):
                        if posizione_replay < len(storia_partita):
                            storia_partita = storia_partita[:posizione_replay]
                        partita_attiva = True
                        replay_mode = False
                        selected = None
                        hint_free = hint_cap = None
                        
                    elif buttons["new"].collidepoint(event.pos):
                        scacchiera = chess_core.crea_scacchiera()
                        chess_core.reset_completo()
                        storia_partita = []
                        posizione_replay = 0
                        cem_white, cem_black = [], []
                        selected = None
                        hint_free = hint_cap = None
                        partita_attiva = True
                        replay_mode = False
                        valutazione_corrente = 0
                        board_iniziale = copy.deepcopy(scacchiera)
                        stato_iniziale = chess_core.salva_stato_completo()

            # === GIOCO NORMALE ===
            if partita_attiva and not replay_mode:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    r, c = gui.ottieni_posizione_click()
                    if r is None:
                        continue
                        
                    if selected is None:
                        pezzo = scacchiera[r][c]
                        if pezzo and pezzo[0]==chess_core.turno:
                            selected = (r, c)
                            hint_free, hint_cap = gui.calcola_mosse_legali(scacchiera, selected, chess_core)
                    else:
                        dest = scacchiera[r][c]
                        board_before = copy.deepcopy(scacchiera)
                        
                        if chess_core.esegui_mossa(scacchiera, selected, (r, c)):
                            # Calcola valutazione
                            valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                            
                            # Animazione
                            gui.anima_mossa(screen, scacchiera, selected, (r, c), 
                                           durata_ms=400, cem_white=cem_white, cem_black=cem_black,
                                           valutazione=valutazione_corrente)
                            
                            # Cimitero
                            if dest:
                                (cem_black if dest[0]=="b" else cem_white).append(gui.PEZZI_UNICODE[dest])
                            
                            # Promozione
                            p = scacchiera[r][c]
                            if p[1]=="P" and ((p[0]=="w" and r==0) or (p[0]=="b" and r==7)):
                                nuovo = gui.chiedi_promozione(screen, p[0])
                                scacchiera[r][c] = nuovo
                                valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                            
                            # Salva nella storia
                            notazione = chess_core.converti_mossa_notazione(selected, (r, c), board_before)
                            board_after = copy.deepcopy(scacchiera)
                            stato_after = chess_core.salva_stato_completo()
                            storia_partita.append((notazione, board_after, stato_after))
                            posizione_replay = len(storia_partita)
                            
                            selected = None
                            hint_free = hint_cap = None

                            # Verifica stato
                            esito = chess_core.stato_partita(scacchiera, chess_core.turno)
                            if esito == "check":
                                gui.anim_message(screen, "SCACCO!", (255, 100, 100), 1000)
                            elif esito == "checkmate":
                                vincitore = "w" if chess_core.turno == "b" else "b"
                                valutazione_corrente = 10000 if vincitore == "w" else -10000
                                gui.mostra_schermata_fine_partita(screen, "checkmate", vincitore)
                                partita_attiva = False
                                replay_mode = True
                            elif esito == "stalemate":
                                valutazione_corrente = 0
                                gui.mostra_schermata_fine_partita(screen, "stalemate")
                                partita_attiva = False
                                replay_mode = True
     
                            # BOT
                            if partita_attiva and modalita in ("PvE", "PvE_UNDO") and chess_core.turno == "b":
                                pygame.time.delay(bot_delay)
                                
                                mossa_bot = bot.scegli_mossa_bot(scacchiera, "b", config)
                                    
                                if mossa_bot:
                                    partenza_bot, arrivo_bot = mossa_bot
                                    r0, c0 = partenza_bot
                                    r1, c1 = arrivo_bot
                                    captured_bot = scacchiera[r1][c1]
                                    
                                    board_before_bot = copy.deepcopy(scacchiera)
                                    
                                    chess_core.esegui_mossa(scacchiera, partenza_bot, arrivo_bot)
                                    
                                    # Calcola valutazione
                                    valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                                    
                                    # Animazione bot
                                    gui.anima_mossa(screen, scacchiera, partenza_bot, arrivo_bot,
                                                   durata_ms=450, cem_white=cem_white, cem_black=cem_black,
                                                   valutazione=valutazione_corrente)

                                    # Cimitero bot
                                    if captured_bot:
                                        (cem_white if captured_bot[0]=="w" else cem_black).append(gui.PEZZI_UNICODE[captured_bot])

                                    # Promozione bot
                                    p = scacchiera[r1][c1]
                                    if p[1]=="P" and ((p[0]=="w" and r1==0) or (p[0]=="b" and r1==7)):
                                        scacchiera[r1][c1] = p[0] + "Q"
                                        valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                                    
                                    # Salva nella storia
                                    notazione = chess_core.converti_mossa_notazione(partenza_bot, arrivo_bot, board_before_bot)
                                    board_after_bot = copy.deepcopy(scacchiera)
                                    stato_after_bot = chess_core.salva_stato_completo()
                                    storia_partita.append((notazione, board_after_bot, stato_after_bot))
                                    posizione_replay = len(storia_partita)

                                    # Stato partita dopo bot
                                    esito = chess_core.stato_partita(scacchiera, chess_core.turno)
                                    if esito == "check":
                                        gui.anim_message(screen, "SCACCO!", (255, 100, 100), 1000)
                                    elif esito == "checkmate":
                                        vincitore = "w" if chess_core.turno == "b" else "b"
                                        valutazione_corrente = 10000 if vincitore == "w" else -10000
                                        gui.mostra_schermata_fine_partita(screen, "checkmate", vincitore)
                                        partita_attiva = False
                                        replay_mode = True
                                    elif esito == "stalemate":
                                        valutazione_corrente = 0
                                        gui.mostra_schermata_fine_partita(screen, "stalemate")
                                        partita_attiva = False
                                        replay_mode = True
                        else:
                            selected = None
                            hint_free = hint_cap = None

                # Undo (solo PvE_UNDO)
                if event.type == pygame.KEYDOWN and modalita == "PvE_UNDO":
                    if event.key == pygame.K_z and len(storia_partita) >= 2:
                        storia_partita.pop()
                        storia_partita.pop()
                        
                        if storia_partita:
                            _, scacchiera, stato = storia_partita[-1]
                            scacchiera = copy.deepcopy(scacchiera)
                            chess_core.ripristina_stato_completo(stato)
                            cem_white, cem_black = ricostruisci_cimiteri(storia_partita)
                            valutazione_corrente = calcola_valutazione_rapida(scacchiera, chess_core.turno)
                        else:
                            scacchiera = copy.deepcopy(board_iniziale)
                            chess_core.ripristina_stato_completo(stato_iniziale)
                            cem_white, cem_black = [], []
                            valutazione_corrente = 0
                        
                        posizione_replay = len(storia_partita)
                        selected = None
                        hint_free = hint_cap = None

        # === AGGIORNA TITOLO ===
        if replay_mode:
            pygame.display.set_caption(f"Scacchi Facili – REPLAY (Mossa {posizione_replay}/{len(storia_partita)})")
        else:
            pygame.display.set_caption(f"Scacchi Facili – Turno: {'Bianco' if chess_core.turno == 'w' else 'Nero'}")

        # === DISEGNO ===
        gui.disegna_scacchiera(screen, scacchiera,
                               selected if not replay_mode else None, 
                               hint_free if not replay_mode else None, 
                               hint_cap if not replay_mode else None,
                               cem_white, cem_black, valutazione_corrente)
        
        # Storia mosse
        if storia_partita:
            gui.disegna_storia_mosse(screen, storia_partita, posizione_replay - 1)
        
        # Controlli replay
        if not partita_attiva or replay_mode:
            gui.disegna_controlli_replay(screen)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
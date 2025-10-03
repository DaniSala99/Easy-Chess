import pygame, sys, os
import json

THEMES = {
    "Classic": {"light":(235,235,208),"dark":(119,148,85),"pieces":"unicode"},
    "DarkWood": {"light":(181,136,99),"dark":(95,57,38),"pieces":"unicode"},
    "Neo": {"light":(220,220,220),"dark":(70,70,70),"pieces":"png"}
}
CURRENT = THEMES[ json.load(open("config.json"))["current_theme"] ]

# ---------- Costanti globali ----------
PEZZI_UNICODE = {
    "wK":"♔","wQ":"♕","wR":"♖","wB":"♗","wN":"♘","wP":"♙",
    "bK":"♚","bQ":"♛","bR":"♜","bB":"♝","bN":"♞","bP":"♟"
}

TILE   = 90                  # lato casella
BOARD  = TILE * 8            # 720px
SIDE_W = 250                 # colonna laterale (aumentata per barra)
WIDTH  = BOARD + SIDE_W
HEIGHT = BOARD

COLOR_LIGHT = CURRENT["light"]
COLOR_DARK  = CURRENT["dark"]
COLOR_HINT    = (120,120,120)    # pallino grigio (mosse libere)
COLOR_CAPTURE = (200,60,60)      # cerchio rosso (catture)

# Colori barra valutazione
COLOR_EVAL_WHITE = (240, 240, 240)
COLOR_EVAL_BLACK = (40, 40, 40)
COLOR_EVAL_BORDER = (100, 100, 100)

def _load_piece_png(name):
    return pygame.transform.smoothscale(
        pygame.image.load(f"immagini/pezzi/{name}.png").convert_alpha(), (TILE,TILE))

if CURRENT["pieces"] == "png":
    PIECE_IMG = {k:_load_piece_png(k) for k in PEZZI_UNICODE}
else:
    PIECE_IMG = {}  # non usato


# ---------- Setup finestra -------------
def inizializza_gui():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Scacchi Facili")
    return screen

# ---------- Calcolo mosse legali -------
def calcola_mosse_legali(board, pos, engine):
    """Ritorna tuple (libere, capture) di caselle legali dal pezzo selezionato."""
    libere, cap = [], []
    r0,c0 = pos
    if not board[r0][c0]:     # casella vuota
        return libere, cap
    for r in range(8):
        for c in range(8):
            if engine.mossa_valida(board, pos, (r,c)):
                if board[r][c]=="":
                    libere.append((r,c))
                else:
                    cap.append((r,c))
    return libere, cap

# ---------- Popup promozione -----------
def chiedi_promozione(screen, color):
    """Mostra finestra scelta pezzo. Ritorna stringa tipo 'wQ'."""
    FONT = pygame.font.Font("Font/DejaVuSans.ttf", 64)
    scelte = ["Q","R","B","N"]
    simboli = "♕♖♗♘" if color=="w" else "♛♜♝♞"
    rect = pygame.Rect(BOARD//2-140, HEIGHT//2-70, 280, 140)
    pygame.draw.rect(screen, (250,250,210), rect)
    pygame.draw.rect(screen, (0,0,0), rect, 2)
    btns=[]
    for i,ch in enumerate(simboli):
        txt = FONT.render(ch, True, (0,0,0))
        x = rect.x+20+i*65
        screen.blit(txt,(x,rect.y+20))
        btns.append(pygame.Rect(x,rect.y+20,60,80))
    pygame.display.flip()

    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.MOUSEBUTTONDOWN:
                x,y = ev.pos
                for i,b in enumerate(btns):
                    if b.collidepoint(x,y):
                        return color+scelte[i]
            if ev.type==pygame.QUIT:
                pygame.quit(); sys.exit()

# ---------- ANIMAZIONE MOSSA MIGLIORATA -----------
def anima_mossa(screen, board, start, end, durata_ms=400, cem_white=None, cem_black=None, valutazione=0):
    """
    Anima il movimento di un pezzo dalla casella start a end con effetti visivi.
    
    Args:
        screen: superficie pygame
        board: scacchiera corrente
        start: (riga, col) partenza
        end: (riga, col) arrivo
        durata_ms: durata animazione in millisecondi (default 400 per essere più visibile)
        cem_white, cem_black: cimiteri per disegno background
        valutazione: punteggio posizione per barra eval
    """
    r0, c0 = start
    r1, c1 = end
    pezzo = board[r0][c0]
    if not pezzo:
        return
    
    # Coordinate pixel
    x0, y0 = c0 * TILE, r0 * TILE
    x1, y1 = c1 * TILE, r1 * TILE
    
    clock = pygame.time.Clock()
    tempo_trascorso = 0
    
    FONT = pygame.font.Font("Font/DejaVuSans.ttf", 48)
    
    # Effetto highlight caselle partenza/arrivo
    highlight_start = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    highlight_start.fill((255, 255, 0, 100))  # Giallo trasparente
    
    highlight_end = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    highlight_end.fill((100, 255, 100, 100))  # Verde trasparente
    
    while tempo_trascorso < durata_ms:
        dt = clock.tick(60)  # 60 FPS
        tempo_trascorso += dt
        
        # Interpolazione con easing (accelerazione/decelerazione)
        t = tempo_trascorso / durata_ms
        # Ease-in-out cubic per movimento più fluido
        if t < 0.5:
            t_eased = 4 * t * t * t
        else:
            t_eased = 1 - pow(-2 * t + 2, 3) / 2
        
        x_curr = x0 + (x1 - x0) * t_eased
        y_curr = y0 + (y1 - y0) * t_eased
        
        # Ridisegna scacchiera SENZA il pezzo in movimento
        temp_board = [row[:] for row in board]
        temp_board[r0][c0] = ""  # Nascondi pezzo originale
        
        # Disegna background
        disegna_scacchiera_base(screen, temp_board, None, None, None, cem_white, cem_black, valutazione)
        
        # Highlight casella partenza (fade out)
        alpha_start = int(255 * (1 - t))
        highlight_start.set_alpha(alpha_start)
        screen.blit(highlight_start, (x0, y0))
        
        # Highlight casella arrivo (fade in)
        alpha_end = int(255 * t)
        highlight_end.set_alpha(alpha_end)
        screen.blit(highlight_end, (x1, y1))
        
        # Disegna pezzo in movimento con ombra
        # Ombra
        shadow = pygame.Surface((TILE + 10, TILE + 10), pygame.SRCALPHA)
        if CURRENT["pieces"] == "unicode":
            txt_shadow = FONT.render(PEZZI_UNICODE[pezzo], True, (0, 0, 0, 100))
            shadow.blit(txt_shadow, (5, 5))
            screen.blit(shadow, (x_curr - 5, y_curr - 5))
            
            # Pezzo
            txt = FONT.render(PEZZI_UNICODE[pezzo], True, (0, 0, 0))
            rect = txt.get_rect(center=(x_curr + TILE//2, y_curr + TILE//2))
            screen.blit(txt, rect)
        else:
            screen.blit(PIECE_IMG[pezzo], (x_curr, y_curr))
        
        pygame.display.flip()
    
    # Assicura posizione finale precisa
    board[r1][c1] = pezzo
    board[r0][c0] = ""
    
    # Flash finale sulla casella di arrivo
    for _ in range(2):
        disegna_scacchiera_base(screen, board, None, None, None, cem_white, cem_black, valutazione)
        pygame.draw.rect(screen, (255, 255, 255), (x1, y1, TILE, TILE), 4)
        pygame.display.flip()
        pygame.time.delay(50)
        
        disegna_scacchiera_base(screen, board, None, None, None, cem_white, cem_black, valutazione)
        pygame.display.flip()
        pygame.time.delay(50)


# ---------- BARRA VALUTAZIONE -----------
def disegna_barra_valutazione(screen, valutazione, x_pos=BOARD + 10, larghezza=30):
    """
    Disegna la barra di valutazione verticale.
    
    Args:
        screen: superficie pygame
        valutazione: punteggio da -10000 a +10000 (positivo = vantaggio bianco)
        x_pos: posizione X della barra
        larghezza: larghezza della barra in pixel
    """
    altezza_barra = HEIGHT - 40
    y_start = 20
    
    # Normalizza valutazione tra -1 e +1
    # Valutazioni oltre ±2000 sono considerate vittoria
    val_norm = max(-1, min(1, valutazione / 2000))
    
    # Calcola altezza parte bianca (in basso) e nera (in alto)
    # 0.5 = pareggio, 1 = bianco vince, 0 = nero vince
    percentuale_bianco = (val_norm + 1) / 2
    altezza_bianco = int(altezza_barra * percentuale_bianco)
    altezza_nero = altezza_barra - altezza_bianco
    
    # Disegna sfondo
    pygame.draw.rect(screen, COLOR_EVAL_BORDER, 
                    (x_pos - 2, y_start - 2, larghezza + 4, altezza_barra + 4))
    
    # Parte nera (in alto)
    pygame.draw.rect(screen, COLOR_EVAL_BLACK, 
                    (x_pos, y_start, larghezza, altezza_nero))
    
    # Parte bianca (in basso)
    pygame.draw.rect(screen, COLOR_EVAL_WHITE, 
                    (x_pos, y_start + altezza_nero, larghezza, altezza_bianco))
    
    # Linea centrale (pareggio)
    y_centro = y_start + altezza_barra // 2
    pygame.draw.line(screen, (255, 0, 0), 
                    (x_pos, y_centro), (x_pos + larghezza, y_centro), 2)
    
    # Testo valutazione
    font_small = pygame.font.Font("Font/DejaVuSans.ttf", 16)
    
    # Converti valutazione in formato leggibile
    if abs(valutazione) > 9000:  # Scacco matto
        if valutazione > 0:
            txt = "M"  # Matto per bianco
            color = (0, 0, 0)
            y_txt = y_start + altezza_nero + 10
        else:
            txt = "M"  # Matto per nero
            color = (255, 255, 255)
            y_txt = y_start + 10
    else:
        val_pawns = valutazione / 100  # Converti in pedoni
        txt = f"{val_pawns:+.1f}"
        if val_pawns > 0:
            color = (0, 0, 0)
            y_txt = y_start + altezza_nero + 10
        else:
            color = (255, 255, 255)
            y_txt = y_start + 10
    
    txt_surf = font_small.render(txt, True, color)
    txt_rect = txt_surf.get_rect(center=(x_pos + larghezza // 2, y_txt))
    screen.blit(txt_surf, txt_rect)


# ---------- Disegno base scacchiera -----------
def disegna_scacchiera_base(screen, board, selected=None, hint_free=None, hint_cap=None, 
                           cem_white=None, cem_black=None, valutazione=0):
    """Disegna scacchiera senza pygame.display.flip() per permettere overlay."""
    FONT = pygame.font.Font("Font/DejaVuSans.ttf", 48)

    # Scacchiera
    for r in range(8):
        for c in range(8):
            color = COLOR_LIGHT if (r+c)%2==0 else COLOR_DARK
            pygame.draw.rect(screen, color, (c*TILE, r*TILE, TILE, TILE))
            pezzo = board[r][c]
            if pezzo:
                if CURRENT["pieces"]=="unicode":
                    txt = FONT.render(PEZZI_UNICODE[pezzo], True, (0,0,0))
                    rect = txt.get_rect(center=(c*TILE+TILE//2, r*TILE+TILE//2))
                    screen.blit(txt, rect)
                else:
                    screen.blit(PIECE_IMG[pezzo], (c*TILE, r*TILE))

    # Highlight casella selezionata
    if selected:
        sr,sc = selected
        pygame.draw.rect(screen, (255,0,0), (sc*TILE,sr*TILE,TILE,TILE), 4)

    # Pallini / cerchi mosse
    if hint_free:
        for r,c in hint_free:
            pygame.draw.circle(screen, COLOR_HINT,
                               (c*TILE+TILE//2, r*TILE+TILE//2), TILE//10)
    if hint_cap:
        for r,c in hint_cap:
            pygame.draw.circle(screen, COLOR_CAPTURE,
                               (c*TILE+TILE//2, r*TILE+TILE//2),
                               TILE//3, 3)

    # Colonna laterale
    pygame.draw.rect(screen, (245,245,245), (BOARD,0,SIDE_W,HEIGHT))
    
    # BARRA VALUTAZIONE
    disegna_barra_valutazione(screen, valutazione, BOARD + 10, 30)
    
    # Cimiteri (spostati a destra della barra)
    font_cem = pygame.font.Font("Font/DejaVuSans.ttf", 30)
    x_cem = BOARD + 50  # Dopo la barra
    if cem_white:
        for i,p in enumerate(cem_white):
            txt = font_cem.render(p, True, (0,0,0))
            screen.blit(txt, (x_cem, 20+i*35))
    if cem_black:
        for i,p in enumerate(cem_black):
            txt = font_cem.render(p, True, (0,0,0))
            screen.blit(txt, (x_cem + 80, 20+i*35))

    # Banner immagine (più in basso)
    banner_img = None
    _BANNER_PATH = os.path.join("immagini", "banner.png")
    try:
        banner_img = pygame.image.load(_BANNER_PATH).convert_alpha()
    except Exception as e:
        if not hasattr(disegna_scacchiera_base, "_banner_warned"):
            print(f"[gui] Impossibile caricare banner da {_BANNER_PATH}: {e}")
            disegna_scacchiera_base._banner_warned = True

    if banner_img:
        max_p = max(len(cem_white or []), len(cem_black or []))
        y0 = 20 + max_p * 35 + 30
        target_w = SIDE_W - 60
        target_h = 150  # Dimensione fissa per banner
        ow, oh = banner_img.get_size()
        scale = min(target_w/ow, target_h/oh)
        nw, nh = int(ow*scale), int(oh*scale)
        banner_img = pygame.transform.smoothscale(banner_img, (nw, nh))
        x0 = BOARD + (SIDE_W - nw)//2
        screen.blit(banner_img, (x0, y0))


# ---------- Disegno completo -----------
def disegna_scacchiera(screen, board, selected=None, hint_free=None, hint_cap=None,
                       cem_white=None, cem_black=None, valutazione=0):
    """Disegna board completo con flip finale."""
    disegna_scacchiera_base(screen, board, selected, hint_free, hint_cap, 
                           cem_white, cem_black, valutazione)
    pygame.display.flip()


def ottieni_posizione_click():
    """Ritorna (riga, colonna) se il click è sulla scacchiera, altrimenti (None, None)."""
    x, y = pygame.mouse.get_pos()
    if x >= BOARD:        # click nella colonna laterale
        return None, None
    riga = y // TILE
    col  = x // TILE
    return riga, col

def anim_message(screen, msg, color=(200,30,30), durata=1500):
    """Animazione messaggio con fade in/out."""
    font = pygame.font.SysFont("arial", 72, bold=True)
    txt = font.render(msg, True, color)
    surf = pygame.Surface((WIDTH,120), pygame.SRCALPHA)
    
    # Fade in
    for alpha in range(0, 200, 20):
        surf.fill((0,0,0,0))
        surf.fill((0,0,0,alpha))
        surf.blit(txt, txt.get_rect(center=(WIDTH//2,60)))
        temp_screen = screen.copy()
        temp_screen.blit(surf, (0, HEIGHT//2 - 60))
        pygame.display.flip()
        pygame.time.delay(30)
    
    # Hold
    pygame.time.delay(durata)
    
    # Fade out
    for alpha in range(200, 0, -20):
        surf.fill((0,0,0,0))
        surf.fill((0,0,0,alpha))
        surf.blit(txt, txt.get_rect(center=(WIDTH//2,60)))
        temp_screen = screen.copy()
        temp_screen.blit(surf, (0, HEIGHT//2 - 60))
        pygame.display.flip()
        pygame.time.delay(30)


# ============================================================
# INTERFACCIA REPLAY MOSSE
# ============================================================

def disegna_storia_mosse(screen, storia, posizione_corrente, y_offset=380):
    """Disegna la storia delle mosse nella colonna laterale."""
    font_small = pygame.font.Font("Font/DejaVuSans.ttf", 18)
    font_tiny = pygame.font.Font("Font/DejaVuSans.ttf", 14)
    
    # Titolo
    titolo = font_small.render("Storia Mosse:", True, (0, 0, 0))
    screen.blit(titolo, (BOARD + 55, y_offset))  # Spostato a destra dopo la barra
    
    # Mosse (ultime 6 visibili)
    y = y_offset + 25
    start_idx = max(0, posizione_corrente - 5)
    end_idx = min(len(storia), start_idx + 6)
    
    for i in range(start_idx, end_idx):
        notazione, _, _ = storia[i]
        mossa_num = i + 1
        
        # Evidenzia mossa corrente
        if i == posizione_corrente:
            pygame.draw.rect(screen, (255, 255, 150), 
                           (BOARD + 50, y - 2, SIDE_W - 55, 22), border_radius=4)
        
        # Numero mossa e notazione
        color = (0, 0, 0) if i <= posizione_corrente else (150, 150, 150)
        txt = font_tiny.render(f"{mossa_num}. {notazione}", True, color)
        screen.blit(txt, (BOARD + 55, y))  # Spostato a destra
        y += 24
    
    # Indicatore posizione
    pos_text = f"Mossa {posizione_corrente + 1}/{len(storia)}"
    if posizione_corrente == len(storia):
        pos_text = "Fine partita"
    
    pos_surf = font_tiny.render(pos_text, True, (100, 100, 100))
    screen.blit(pos_surf, (BOARD + 55, y + 5))


def disegna_controlli_replay(screen, y_offset=540):
    """Disegna i pulsanti di controllo replay."""
    font = pygame.font.Font("Font/DejaVuSans.ttf", 16)
    btn_color = (100, 150, 100)
    btn_hover = (80, 120, 80)
    
    mx, my = pygame.mouse.get_pos()
    
    buttons = {}
    btn_width = 110
    btn_height = 30
    btn_spacing = 6
    
    x_start = BOARD + (SIDE_W - btn_width) // 2
    
    labels = [
        ("start", "⏮ Inizio"),
        ("prev", "◀ Indietro"),
        ("next", "Avanti ▶"),
        ("end", "Fine ⏭"),
        ("resume", "▶ Riprendi"),
        ("new", "🔄 Nuova")
    ]
    
    y = y_offset
    for key, label in labels:
        rect = pygame.Rect(x_start, y, btn_width, btn_height)
        buttons[key] = rect
        
        color = btn_hover if rect.collidepoint(mx, my) else btn_color
        
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (50, 50, 50), rect, 2, border_radius=6)
        
        txt = font.render(label, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=rect.center)
        screen.blit(txt, txt_rect)
        
        y += btn_height + btn_spacing
    
    return buttons


def mostra_schermata_fine_partita(screen, esito, vincitore=None):
    """Mostra un overlay elegante alla fine della partita."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    font_big = pygame.font.SysFont("arial", 64, bold=True)
    font_small = pygame.font.SysFont("arial", 32)
    
    if esito == "checkmate":
        msg_main = "SCACCO MATTO!"
        colore_main = "Bianco" if vincitore == "w" else "Nero"
        msg_sub = f"Vince il {colore_main}"
        color = (255, 215, 0) if vincitore == "w" else (200, 200, 255)
    else:
        msg_main = "PATTA"
        msg_sub = "Stallo - Nessun vincitore"
        color = (200, 200, 200)
    
    txt_main = font_big.render(msg_main, True, color)
    txt_sub = font_small.render(msg_sub, True, (255, 255, 255))
    
    main_rect = txt_main.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
    sub_rect = txt_sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
    
    screen.blit(txt_main, main_rect)
    screen.blit(txt_sub, sub_rect)
    
    font_tiny = pygame.font.SysFont("arial", 20)
    istruzioni = [
        "Usa i controlli a destra per:",
        "• Rivedere le mosse",
        "• Tornare indietro nel tempo",
        "• Riprendere da una posizione",
        "• Iniziare una nuova partita"
    ]
    
    y = HEIGHT // 2 + 100
    for linea in istruzioni:
        txt = font_tiny.render(linea, True, (220, 220, 220))
        txt_rect = txt.get_rect(center=(WIDTH // 2, y))
        screen.blit(txt, txt_rect)
        y += 30
    
    pygame.display.flip()
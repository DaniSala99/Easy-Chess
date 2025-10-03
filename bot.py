import random
import chess_core as core

# ============================================================
# VALUTAZIONE POSIZIONALE
# ============================================================

# Valori materiali standard
VALORI_PEZZI = {
    "P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000
}

# Tabelle posizionali per pedoni (bonus per posizioni avanzate/centrali)
TABELLA_PEDONI_W = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

TABELLA_PEDONI_B = [list(reversed(riga)) for riga in reversed(TABELLA_PEDONI_W)]

# Tabelle posizionali per cavalli (bonus per centro)
TABELLA_CAVALLI = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

# Tabelle per alfieri (diagonali lunghe)
TABELLA_ALFIERI = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

# Tabelle per torri (colonne aperte)
TABELLA_TORRI = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

# Tabelle per regina (centro e mobilità)
TABELLA_REGINA = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

# Tabelle per re (early game: castello, late game: centro)
TABELLA_RE_EARLY = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

TABELLE_POSIZIONALI = {
    "P": (TABELLA_PEDONI_W, TABELLA_PEDONI_B),
    "N": (TABELLA_CAVALLI, TABELLA_CAVALLI),
    "B": (TABELLA_ALFIERI, TABELLA_ALFIERI),
    "R": (TABELLA_TORRI, TABELLA_TORRI),
    "Q": (TABELLA_REGINA, TABELLA_REGINA),
    "K": (TABELLA_RE_EARLY, TABELLA_RE_EARLY)
}


def valuta_posizione(board, colore_massimizza):
    """
    Valuta la posizione dalla prospettiva di colore_massimizza.
    Positivo = vantaggio per colore_massimizza, Negativo = svantaggio.
    """
    punteggio = 0
    
    for r in range(8):
        for c in range(8):
            pezzo = board[r][c]
            if not pezzo:
                continue
            
            colore_pezzo = pezzo[0]
            tipo_pezzo = pezzo[1]
            
            # Valore materiale base
            valore = VALORI_PEZZI[tipo_pezzo]
            
            # Valore posizionale
            if tipo_pezzo in TABELLE_POSIZIONALI:
                tabella_w, tabella_b = TABELLE_POSIZIONALI[tipo_pezzo]
                if colore_pezzo == "w":
                    valore += tabella_w[r][c]
                else:
                    valore += tabella_b[r][c]
            
            # Aggiungi o sottrai dal punteggio
            if colore_pezzo == colore_massimizza:
                punteggio += valore
            else:
                punteggio -= valore
    
    return punteggio


# ============================================================
# GENERAZIONE MOSSE
# ============================================================

def _tutte_mosse_pezzo(board, r0, c0):
    """Restituisce tutte le caselle di arrivo valide per il pezzo su (r0,c0)."""
    mosse = []
    for r1 in range(8):
        for c1 in range(8):
            if core.mossa_valida(board, (r0, c0), (r1, c1)):
                mosse.append((r1, c1))
    return mosse


def lista_mosse_valide(board, colore="b"):
    """Raccoglie tutte le mosse (partenza, arrivo) per il colore indicato."""
    elenco = []
    for r in range(8):
        for c in range(8):
            pezzo = board[r][c]
            if pezzo and pezzo[0] == colore:
                for arrivo in _tutte_mosse_pezzo(board, r, c):
                    elenco.append(((r, c), arrivo))
    return elenco


def ordina_mosse(board, mosse, colore):
    """
    Ordina le mosse per migliorare l'efficienza del pruning:
    1. Catture di pezzi preziosi
    2. Mosse verso il centro
    3. Altre mosse
    """
    def punteggio_mossa(mossa):
        start, end = mossa
        score = 0
        
        # Catture (priorità alta)
        pezzo_catturato = board[end[0]][end[1]]
        if pezzo_catturato:
            score += VALORI_PEZZI[pezzo_catturato[1]] * 10
            # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
            pezzo_attaccante = board[start[0]][start[1]]
            score -= VALORI_PEZZI[pezzo_attaccante[1]]
        
        # Mosse centrali
        r, c = end
        distanza_centro = abs(3.5 - r) + abs(3.5 - c)
        score += (7 - distanza_centro) * 2
        
        return score
    
    return sorted(mosse, key=punteggio_mossa, reverse=True)


# ============================================================
# MINIMAX CON ALPHA-BETA PRUNING
# ============================================================

def minimax(board, profondita, alpha, beta, massimizza, colore_bot, stats):
    """
    Algoritmo Minimax con Alpha-Beta Pruning.
    
    Args:
        board: scacchiera corrente
        profondita: profondità rimanente di ricerca
        alpha: miglior valore per il massimizzatore
        beta: miglior valore per il minimizzatore
        massimizza: True se turno del bot, False altrimenti
        colore_bot: colore del bot ('w' o 'b')
        stats: dizionario per statistiche (nodi visitati, pruning)
    
    Returns:
        Valore della posizione
    """
    stats['nodi'] += 1
    
    # Condizioni di terminazione
    colore_turno = colore_bot if massimizza else ('w' if colore_bot == 'b' else 'b')
    stato = core.stato_partita(board, colore_turno)
    
    if stato == "checkmate":
        # Scacco matto: massima penalità/vantaggio
        return -100000 if massimizza else 100000
    
    if stato == "stalemate":
        # Stallo: pareggio
        return 0
    
    if profondita == 0:
        # Foglia: valuta posizione
        return valuta_posizione(board, colore_bot)
    
    # Genera e ordina mosse
    mosse = lista_mosse_valide(board, colore_turno)
    mosse = ordina_mosse(board, mosse, colore_turno)
    
    if not mosse:
        # Nessuna mossa disponibile
        return valuta_posizione(board, colore_bot)
    
    if massimizza:
        max_eval = float('-inf')
        for mossa in mosse:
            # Simula mossa
            temp_board = [row[:] for row in board]
            start, end = mossa
            temp_board[end[0]][end[1]] = temp_board[start[0]][start[1]]
            temp_board[start[0]][start[1]] = ""
            
            # Ricorsione
            eval_pos = minimax(temp_board, profondita - 1, alpha, beta, False, colore_bot, stats)
            max_eval = max(max_eval, eval_pos)
            alpha = max(alpha, eval_pos)
            
            if beta <= alpha:
                stats['pruning'] += 1
                break  # Beta cut-off
        
        return max_eval
    else:
        min_eval = float('inf')
        for mossa in mosse:
            # Simula mossa
            temp_board = [row[:] for row in board]
            start, end = mossa
            temp_board[end[0]][end[1]] = temp_board[start[0]][start[1]]
            temp_board[start[0]][start[1]] = ""
            
            # Ricorsione
            eval_pos = minimax(temp_board, profondita - 1, alpha, beta, True, colore_bot, stats)
            min_eval = min(min_eval, eval_pos)
            beta = min(beta, eval_pos)
            
            if beta <= alpha:
                stats['pruning'] += 1
                break  # Alpha cut-off
        
        return min_eval


# ============================================================
# FUNZIONE PRINCIPALE BOT
# ============================================================

def scegli_mossa_bot(board, colore="b", config=None):
    """
    Sceglie la mossa migliore usando Minimax con alpha-beta pruning.
    
    Args:
        board: scacchiera corrente
        colore: 'w' o 'b'
        config: dizionario configurazione (profondità, ecc.)
    
    Returns:
        (partenza, arrivo) oppure None
    """
    if config is None:
        config = {}
    
    # Profondità di ricerca (3 = buono, 4 = forte, 5+ = molto lento)
    profondita = config.get("bot_depth", 3)
    
    mosse = lista_mosse_valide(board, colore)
    if not mosse:
        return None
    
    # Ordina mosse per migliorare pruning
    mosse = ordina_mosse(board, mosse, colore)
    
    migliore_mossa = None
    migliore_valore = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Statistiche
    stats = {'nodi': 0, 'pruning': 0}
    
    print(f"[BOT] Analizzando {len(mosse)} mosse a profondità {profondita}...")
    
    for mossa in mosse:
        # Simula mossa
        temp_board = [row[:] for row in board]
        start, end = mossa
        temp_board[end[0]][end[1]] = temp_board[start[0]][start[1]]
        temp_board[start[0]][start[1]] = ""
        
        # Valuta con minimax
        valore = minimax(temp_board, profondita - 1, alpha, beta, False, colore, stats)
        
        if valore > migliore_valore:
            migliore_valore = valore
            migliore_mossa = mossa
            alpha = max(alpha, valore)
    
    print(f"[BOT] Nodi esplorati: {stats['nodi']}, Pruning: {stats['pruning']}")
    print(f"[BOT] Mossa scelta: {migliore_mossa}, Valutazione: {migliore_valore}")
    
    return migliore_mossa


# ============================================================
# BOT RANDOM+ (MANTENUTO PER RETROCOMPATIBILITÀ/TESTING)
# ============================================================

def scegli_mossa_random(board, colore="b"):
    """Bot casuale puro."""
    mosse = lista_mosse_valide(board, colore)
    return random.choice(mosse) if mosse else None


def scegli_mossa_random_plus(board, colore="b"):
    """Bot euristico semplice (catture + centro)."""
    mosse = lista_mosse_valide(board, colore)
    if not mosse:
        return None
    
    # Catture
    catture = [m for m in mosse if board[m[1][0]][m[1][1]] != ""]
    if catture:
        return random.choice(catture)
    
    # Centro
    centro = {(3, 3), (3, 4), (4, 3), (4, 4)}
    centrali = [m for m in mosse if m[1] in centro]
    if centrali:
        return random.choice(centrali)
    
    return random.choice(mosse)
# chess_core.py
# ============================================================
#  Engine didattico: regole base + arrocco sicuro, en-passant,
#  promozione automatica a regina, scacco/matto/stallo
# ============================================================

# ---------- Stato globale --------------------------------------------------
storico_mosse: list = []
turno = "w"                           # 'w' bianco, 'b' nero

# Flag di "non ha ancora mosso" (per arrocco)
w_king_moved = b_king_moved = False
w_rook_a_moved = w_rook_h_moved = False
b_rook_a_moved = b_rook_h_moved = False

# Target en-passant del turno successivo (riga, col) oppure None
en_passant_target = None

# ---------- Board iniziale -------------------------------------------------
def crea_scacchiera():
    return [
        ["bR","bN","bB","bQ","bK","bB","bN","bR"],
        ["bP"]*8,
        [""]*8,[""]*8,[""]*8,[""]*8,
        ["wP"]*8,
        ["wR","wN","wB","wQ","wK","wB","wN","wR"]
    ]

# ---------- Helper geometrici ---------------------------------------------
def _direzione_libera(board,r0,c0,r1,c1):
    dr = (r1-r0) and ((r1-r0)//abs(r1-r0))
    dc = (c1-c0) and ((c1-c0)//abs(c1-c0))
    r, c = r0+dr, c0+dc
    while (r,c)!=(r1,c1):
        if board[r][c]!="": return False
        r += dr; c += dc
    return True

def _libero(board,row,ca,cb):             # inclusi ca..cb
    return all(board[row][c]=="" for c in range(ca,cb+1))

# ---------- Funzioni scacco & controlli ------------------------------------
def _trova_re(board,color):
    for r in range(8):
        for c in range(8):
            if board[r][c]==f"{color}K":
                return (r,c)
    return None

def _square_attacked(board,square,attacker):
    r_sq,c_sq = square
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p[0]==attacker:
                if _mossa_valida_grezza(board,(r,c),(r_sq,c_sq)):
                    return True
    return False

# ---------- Movimento "grezzo" pezzi (senza self-check) ---------------------
def _mossa_valida_grezza(board,start,end):
    r0,c0 = start; r1,c1 = end
    piece = board[r0][c0]
    if piece=="": return False
    col, tp = piece
    dest = board[r1][c1]
    if dest!="" and dest[0]==col: return False

    if tp=="P":
        dir_ = -1 if col=="w" else 1
        base  = 6 if col=="w" else 1
        # avanti 1
        if c0==c1 and r1==r0+dir_ and board[r1][c1]=="": return True
        # avanti 2
        if (c0==c1 and r0==base and r1==r0+2*dir_
            and board[r0+dir_][c0]=="" and board[r1][c1]==""): return True
        # cattura diag o en-passant
        if abs(c1-c0)==1 and r1==r0+dir_:
            if board[r1][c1]!="" and board[r1][c1][0]!=col: return True
            if (r1,c1)==en_passant_target: return True
        return False

    if tp=="R":
        if r0!=r1 and c0!=c1: return False
        return _direzione_libera(board,r0,c0,r1,c1)

    if tp=="N":
        return sorted([abs(r1-r0),abs(c1-c0)])==[1,2]

    if tp=="B":
        if abs(r1-r0)!=abs(c1-c0): return False
        return _direzione_libera(board,r0,c0,r1,c1)

    if tp=="Q":
        ok_linea  = (r0==r1 or c0==c1) and _direzione_libera(board,r0,c0,r1,c1)
        ok_diag   = abs(r1-r0)==abs(c1-c0) and _direzione_libera(board,r0,c0,r1,c1)
        return ok_linea or ok_diag

    if tp=="K":
        # Arrocco
        if col=="w" and r0==7 and not w_king_moved:
            if c1-c0==2 and not w_rook_h_moved and _libero(board,7,5,6): return True
            if c0-c1==2 and not w_rook_a_moved and board[7][1]==board[7][2]==board[7][3]=="": return True
        if col=="b" and r0==0 and not b_king_moved:
            if c1-c0==2 and not b_rook_h_moved and _libero(board,0,5,6): return True
            if c0-c1==2 and not b_rook_a_moved and board[0][1]==board[0][2]==board[0][3]=="": return True
        # passo singolo
        return max(abs(r1-r0),abs(c1-c0))==1
    return False

# ---------- Mossa valida "sicura" (non lascia re sotto scacco) --------------
def mossa_valida(board,start,end):
    if not _mossa_valida_grezza(board,start,end):
        return False
    # Simula la mossa
    temp = [row[:] for row in board]
    _applica_mossa_raw(temp,start,end)
    col = board[start[0]][start[1]][0]
    king_sq = _trova_re(temp,col)
    if _square_attacked(temp,king_sq,'b' if col=='w' else 'w'):
        return False
    # Arrocco: verifica che il re non attraversi case attaccate
    r0,c0 = start; r1,c1 = end
    piece = board[r0][c0]
    if piece[1]=="K" and abs(c1-c0)==2:
        path_cols = (range(c0,c1+1) if c1>c0 else range(c1,c0+1))
        for col_ in path_cols:
            if _square_attacked(board,(r0,col_),'b' if piece[0]=='w' else 'w'):
                return False
    return True

def _applica_mossa_raw(board,start,end):
    r0,c0 = start; r1,c1 = end
    board[r1][c1]=board[r0][c0]
    board[r0][c0]=""

# ---------- Esegui mossa (con storico) -------------------------------------
def esegui_mossa(board,start,end):
    global turno,en_passant_target
    global w_king_moved,b_king_moved,w_rook_a_moved,w_rook_h_moved,b_rook_a_moved,b_rook_h_moved
    if not mossa_valida(board,start,end): return False

    r0,c0=start; r1,c1=end
    piece = board[r0][c0]
    dest  = board[r1][c1]

    # Salva stato per undo
    storico_mosse.append((start,end,dest,en_passant_target,
                          w_king_moved,b_king_moved,
                          w_rook_a_moved,w_rook_h_moved,b_rook_a_moved,b_rook_h_moved))

    # ---------- Arrocco ----------
    if piece[1]=="K" and abs(c1-c0)==2:
        if c1>c0:    # corto
            board[r0][6]=piece; board[r0][5]=board[r0][7]; board[r0][7]=""
            board[r0][c0]=""
        else:        # lungo
            board[r0][2]=piece; board[r0][3]=board[r0][0]; board[r0][0]=""
            board[r0][c0]=""
    # ---------- En-passant ----------
    elif piece[1]=="P" and (r1,c1)==en_passant_target:
        board[r1][c1]=piece; board[r0][c0]=""
        board[r0][c1]=""                       # pedone catturato
    else:
        board[r1][c1]=piece; 
        board[r0][c0]=""              # casella di partenza diventa vuota

    # ---------- Aggiorna flag movimento ----------
    if piece=="wK": w_king_moved=True
    if piece=="bK": b_king_moved=True
    if piece=="wR" and start==(7,0): w_rook_a_moved=True
    if piece=="wR" and start==(7,7): w_rook_h_moved=True
    if piece=="bR" and start==(0,0): b_rook_a_moved=True
    if piece=="bR" and start==(0,7): b_rook_h_moved=True

    # ---------- Promozione ----------
    promo = False
    if piece[1] == "P" and ((piece[0] == "w" and r1 == 0) or (piece[0] == "b" and r1 == 7)):
        promo = True  # segnalo che è arrivato in ultima riga

    # ---------- Gestione en-passant target ----------
    en_passant_target = ((r0+r1)//2,c0) if piece[1]=="P" and abs(r1-r0)==2 else None

    turno = 'b' if turno=='w' else 'w'
    return True

# ---------- Undo -----------------------------------------------------------
def annulla_mossa(board):
    global turno,en_passant_target
    global w_king_moved,b_king_moved,w_rook_a_moved,w_rook_h_moved,b_rook_a_moved,b_rook_h_moved
    if not storico_mosse: return
    start,end,catturato,ep,wk,bk,wra,wrh,bra,brh = storico_mosse.pop()
    r0,c0=start; r1,c1=end
    piece = board[r1][c1] or board[r0][c0]

    # Arrocco
    if piece[1]=="K" and abs(c1-c0)==2:
        if c1>c0:   # corto
            board[r0][c0]=piece; board[r0][7]=board[r0][5]; board[r0][5]=""; board[r0][6]=""
        else:       # lungo
            board[r0][c0]=piece; board[r0][0]=board[r0][3]; board[r0][3]=""; board[r0][2]=""
    # En-passant
    elif piece[1]=="P" and (r1,c1)==ep and catturato=="":
        board[r0][c0]=piece; board[r1][c1]=""               # pedone torna
        board[r0][c1]="bP" if piece[0]=="w" else "wP"       # ripristina catturato
    else:
        board[r0][c0]=piece; board[r1][c1]=catturato

    en_passant_target = ep
    w_king_moved,b_king_moved = wk,bk
    w_rook_a_moved, w_rook_h_moved = wra,wrh
    b_rook_a_moved, b_rook_h_moved = bra,brh
    turno = 'b' if turno=='w' else 'w'

# ---------- Stato partita --------------------------------------------------
def _has_legal_move(board,color):
    for r0 in range(8):
        for c0 in range(8):
            if board[r0][c0] and board[r0][c0][0]==color:
                for r1 in range(8):
                    for c1 in range(8):
                        if mossa_valida(board,(r0,c0),(r1,c1)):
                            return True
    return False

def stato_partita(board,color_turno):
    king_sq = _trova_re(board,color_turno)
    in_check = _square_attacked(board,king_sq,'b' if color_turno=='w' else 'w')
    has_move = _has_legal_move(board,color_turno)
    if in_check and not has_move:   return "checkmate"
    if not in_check and not has_move:return "stalemate"
    if in_check:                    return "check"
    return "ok"

# ---------- FUNZIONI REPLAY ------------------------------------------------
def salva_stato_completo():
    """
    Salva lo stato completo del gioco per permettere replay.
    Returns: dizionario con tutto lo stato
    """
    return {
        'turno': turno,
        'en_passant': en_passant_target,
        'w_king_moved': w_king_moved,
        'b_king_moved': b_king_moved,
        'w_rook_a_moved': w_rook_a_moved,
        'w_rook_h_moved': w_rook_h_moved,
        'b_rook_a_moved': b_rook_a_moved,
        'b_rook_h_moved': b_rook_h_moved,
        'storico_len': len(storico_mosse)
    }


def ripristina_stato_completo(stato):
    """
    Ripristina lo stato completo del gioco.
    Args: dizionario stato salvato con salva_stato_completo()
    """
    global turno, en_passant_target
    global w_king_moved, b_king_moved
    global w_rook_a_moved, w_rook_h_moved, b_rook_a_moved, b_rook_h_moved
    global storico_mosse
    
    turno = stato['turno']
    en_passant_target = stato['en_passant']
    w_king_moved = stato['w_king_moved']
    b_king_moved = stato['b_king_moved']
    w_rook_a_moved = stato['w_rook_a_moved']
    w_rook_h_moved = stato['w_rook_h_moved']
    b_rook_a_moved = stato['b_rook_a_moved']
    b_rook_h_moved = stato['b_rook_h_moved']
    
    # Taglia storico alla lunghezza salvata
    while len(storico_mosse) > stato['storico_len']:
        storico_mosse.pop()


def reset_completo():
    """Reset completo di tutte le variabili globali."""
    global turno, en_passant_target, storico_mosse
    global w_king_moved, b_king_moved
    global w_rook_a_moved, w_rook_h_moved, b_rook_a_moved, b_rook_h_moved
    
    storico_mosse.clear()
    turno = "w"
    en_passant_target = None
    w_king_moved = b_king_moved = False
    w_rook_a_moved = w_rook_h_moved = False
    b_rook_a_moved = b_rook_h_moved = False


def ottieni_storico_mosse():
    """Ritorna copia dello storico mosse."""
    return storico_mosse[:]


def converti_mossa_notazione(start, end, board_before):
    """
    Converte una mossa in notazione algebrica semplificata.
    Es: "e2-e4", "Nf3", "Qxd5", "O-O"
    """
    r0, c0 = start
    r1, c1 = end
    pezzo = board_before[r0][c0]
    cattura = board_before[r1][c1] != ""
    
    cols = "abcdefgh"
    rows = "87654321"
    
    if not pezzo:
        return "???"
    
    tipo = pezzo[1]
    
    # Arrocco
    if tipo == "K" and abs(c1 - c0) == 2:
        return "O-O" if c1 > c0 else "O-O-O"
    
    # Pedone
    if tipo == "P":
        if cattura:
            return f"{cols[c0]}x{cols[c1]}{rows[r1]}"
        else:
            return f"{cols[c1]}{rows[r1]}"
    
    # Altri pezzi
    pezzo_simbolo = tipo if tipo != "N" else "N"  # Cavallo = N
    cattura_simbolo = "x" if cattura else ""
    return f"{pezzo_simbolo}{cattura_simbolo}{cols[c1]}{rows[r1]}"
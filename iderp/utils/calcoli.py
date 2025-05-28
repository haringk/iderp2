def calcola_prezzo(base, altezza, prezzo_unitario):
    try:
        mq = float(base) * float(altezza)
        return mq * float(prezzo_unitario)
    except Exception:
        return 0

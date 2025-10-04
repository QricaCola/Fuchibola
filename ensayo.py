for bloque in estrofa:
    try:
        h3 = bloque.find_element(By.TAG_NAME, "h3")
        versos = h3.text.strip().split('\n')   # Separa los versos

        # Une versos de a dos
        versos_pareados = []
        for i in range(0, len(versos), 2):
            if i + 1 < len(versos):
                versos_pareados.append(f"{versos[i]} {versos[i+1]}")
            else:
                versos_pareados.append(versos[i])  # si hay uno suelto

        estrofa_unida = '\n'.join(versos_pareados)
        estrofas.append(estrofa_unida)
    except:
        continue

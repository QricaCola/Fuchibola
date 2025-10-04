import pandas
import pyautogui
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
import re

#Letra del himno
prehimn= "https://www.nuevohimnario.com/Himno?no="
i=False
himno = None
while i == False:  
    numero_himno = int(input("Introduzca el numero del himno: "))
    if numero_himno > 614 or numero_himno <= 0:
        print("Introduzca un himno válido")
        i = False
    else:
        himno = prehimn + str(numero_himno)
        driver = webdriver.Chrome()
        driver.get(himno)
        i = True

estrofa = driver.find_elements(By.CLASS_NAME,"block-heading-five")

estrofas = []

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


#for i, estrofa in enumerate(estrofas, 1):
#    print(f"Estrofa {i}:\n{estrofa}\n")
k = 0
while k < len(estrofas):
    print(estrofas[k])
    k += 1




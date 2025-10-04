import pandas
import pyautogui
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys



def diapositiva(numero_himno, numero_de_estrofa,  url):
    driver = webdriver.Chrome()
    #Compu iglesia
    #pyautogui.moveTo(760,790)

    #Compu Elias
    pyautogui.moveTo(500, 605)
    pyautogui.doubleClick()
    time.sleep(1)
    pyautogui.write("Al jorge le gusta el guevo")
    time.sleep(6)

    #Exporta el archivo

    #click en "Archivo"
    btn_archivo = "body > div.flexrow.app > div:nth-child(1) > div:nth-child(3) > div:nth-child(2) > div.topbar > span:nth-child(1) > button:nth-child(1)"
    driver.find_element(By.CSS_SELECTOR,btn_archivo).click()
    time.sleep(1)

    #click en "exportar"
    pyautogui.moveTo(90, 449)
    pyautogui.click()

    #click en "PNG."
    pyautogui.moveTo(250,449)
    pyautogui.click()
    time.sleep(5)

    #titulo de la diapositiva
    titulo_diapositiva = "#\\37 28"
    driver.find_element(By.CSS_SELECTOR, titulo_diapositiva).click()
    pyautogui.hotkey("ctrl","a")
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, titulo_diapositiva).send_keys("345 - 1")
    time.sleep(3)

    #descargar el archivo
    btn_guardar = "body > div.flexrow.app > div:nth-child(1) > div:nth-child(1) > div.window.saveforweb > div.body.flexrow > div:nth-child(2) > div > button:nth-child(6)"
    #driver.find_element(By.CSS_SELECTOR, btn_guardar).click()
    time.sleep(4)

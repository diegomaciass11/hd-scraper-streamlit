import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from PIL import Image
from io import BytesIO
import requests

def buscar_producto(sku: str):
    # Configuración de Selenium en modo headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path="chromedriver")  # Asegúrate de tener 'chromedriver' en PATH
    driver = webdriver.Chrome(service=service, options=chrome_options)

    resultado = {
        "nombre": "No encontrado",
        "descripcion": "No encontrada",
        "precio": "No disponible",
        "stock": "No detectado",
        "imagen": None
    }

    try:
        url = f"https://www.homedepot.com.mx/s/{sku}"
        driver.get(url)
        time.sleep(2)

        # Cerrar popup si aparece
        try:
            close_icon = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "dialogStore--icon--highlightOff"))
            )
            close_icon.click()
        except:
            pass

        # Obtener nombre del producto
        try:
            resultado["nombre"] = driver.find_element(By.CLASS_NAME, "product-name").text
        except:
            pass

        # Obtener descripción
        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, "p.MuiTypography-root.sc-hsWlPz.juosUc.sc-hrDvXV.iuUlyx.MuiTypography-body1")
            resultado["descripcion"] = desc_elem.text
        except:
            pass

        # Obtener precio con JavaScript
        try:
            price_elem = driver.find_element(By.CSS_SELECTOR, "p.product-price")
            js_script = """
                var element = arguments[0];
                var mainText = '';
                var supText = '';
                var supCount = 0;
                for (var i = 0; i < element.childNodes.length; i++) {
                    var node = element.childNodes[i];
                    if (node.nodeType === Node.TEXT_NODE) {
                        mainText += node.textContent.trim();
                    } else if (node.nodeType === Node.ELEMENT_NODE && node.tagName === 'SUP') {
                        supCount++;
                        if (supCount === 2) {
                            supText = node.textContent.trim();
                        }
                    }
                }
                return mainText + '.' + supText;
            """
            price_text = driver.execute_script(js_script, price_elem).replace(',', '')
            resultado["precio"] = f"${round(float(price_text), 2)}"
        except:
            pass

        # Obtener stock
        try:
            stock_elem = driver.find_element(By.XPATH, "//p[contains(text(), 'disponibles')]")
            resultado["stock"] = stock_elem.text
        except:
            pass

        # Obtener imagen
        try:
            img_elem = driver.find_element(By.CSS_SELECTOR, "div.product-image img")
            img_url = img_elem.get_attribute("src")
            if img_url:
                img_response = requests.get(img_url)
                resultado["imagen"] = Image.open(BytesIO(img_response.content))
        except:
            pass

    finally:
        driver.quit()

    return resultado

# --- Interfaz con Streamlit ---

st.set_page_config(page_title="Buscador de Productos", layout="centered")

st.title("🔍 Buscador de Productos - Home Depot")
sku_input = st.text_input("Introduce el SKU del producto:", "")

if st.button("Buscar"):
    if sku_input.strip():
        with st.spinner("Buscando producto..."):
            data = buscar_producto(sku_input.strip())
        st.subheader("🛒 Resultado de la búsqueda:")
        st.write(f"**Nombre:** {data['nombre']}")
        st.write(f"**Descripción:** {data['descripcion']}")
        st.write(f"**Precio:** {data['precio']}")
        st.write(f"**Stock:** {data['stock']}")

        if data["imagen"]:
            st.image(data["imagen"], caption="Imagen del producto", use_column_width=True)
        else:
            st.write("❌ Imagen no disponible.")
    else:
        st.warning("Por favor introduce un SKU válido.")

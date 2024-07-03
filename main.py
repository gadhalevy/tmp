#This will not run on online IDE
import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from io import StringIO

@st.cache_resource
def init():
    firefoxOptions = Options()
    firefoxOptions.add_argument("--headless")
    firefoxOptions.add_argument("--disable-gpu")
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(
        options=firefoxOptions,
        # service=service,
    )
    return  driver

def get_url(words):
    # driver=webdriver.Firefox()
    driver=init()
    driver.get('https://geek.co.il/~mooffie/crossword/')
    form=driver.find_element(by='id',value='crossword-form')
    area=form.find_element(by='id',value='raw-words')
    area.clear()
    area.send_keys(words)
    submit=form.find_element(by='name',value='action_same')
    submit.click()
    form=driver.find_element(by='id',value='crossword-form')
    time.sleep(1)
    link=form.find_element(by='id',value='save-create-temp-btn')
    link.click()
    url=driver.current_url
    time.sleep(2)
    driver.quit()
    return url

def progress():
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()

def main():
    kovets=None
    st.set_page_config(layout="wide")
    ofen=st.sidebar.radio('בחר אופן יצירת התשבץ',('העלאת קובץ','יצירה במקום'))
    if ofen=='העלאת קובץ':
        tmp=st.file_uploader('העלה בבקשה את קובץ התשבץ')
        if tmp:
            kovets=StringIO(tmp.getvalue().decode('utf-8'))
    else:
        txt=st.text_area('כתוב הגדרות')
        if st.sidebar.button('העלה'):
            kovets=txt
    # if tmp:
    #     kovets=StringIO(tmp.getvalue().decode('utf-8'))
    if kovets is not None:
        url=get_url(kovets)
        progress()
        st.write(url)
        if 'url' not in st.session_state:
            st.session_state.url=url

if __name__=='__main__':
    main()
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
        service=service,
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
    driver.implicitly_wait(2)
    form=driver.find_element(by='id',value='crossword-form')
    driver.implicitly_wait(2)
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

def set_session_state(url,length):
    if 'url' not in st.session_state:
        st.session_state.url=url
    if 'length' not in st.session_state:
        st.session_state.length=length

def main():
    kovets=None
    st.set_page_config(layout="wide")
    ofen=st.sidebar.radio('בחר אופן יצירת התשבץ',('העלאת קובץ','יצירה במקום','קישור ישיר'))
    if ofen=='העלאת קובץ':
        tmp=st.file_uploader('העלה בבקשה את קובץ התשבץ')
        if tmp:
            kovets=StringIO(tmp.getvalue().decode('utf-8'))
            length=len(kovets.readlines())
    elif ofen=='יצירה במקום':
        st.info('לאחר סיום כתיבת ההגדרות מומלץ לגבות אותן בקובץ לפני מעבר לשלב הבא')
        txt=st.text_area('כתוב הגדרות')
        if st.sidebar.button('העלה'):
            kovets=txt
            length=len(txt.split('\n'))
    else:
        url=st.text_input('כתוב קישור לתשבץ',value='https://geek.co.il/~mooffie/crossword/temporary/')
        if url:
            send_url=st.button('שלח קישור')
            if send_url:
                set_session_state(url,length=0)
    if kovets is not None:
        url=get_url(kovets)
        progress()
        st.write(url)
        set_session_state(url, length)

if __name__=='__main__':
    main()
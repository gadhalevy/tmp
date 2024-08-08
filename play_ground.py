from playwright.sync_api import sync_playwright
from playwright.sync_api import Playwright
import streamlit as st
from io import StringIO
import time
import os
os.system("playwright install")
os.system("playwright install-deps")
def run(playwright: Playwright,words) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://geek.co.il/~mooffie/crossword/")
    page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").click()
    page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").press("ControlOrMeta+a")
    page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").fill(words)
    page.get_by_role("button", name="בנה את התשבץ").click()
    page.get_by_role("button", name="צוֹר קישור").click()
    url=page.url
    # ---------------------
    context.close()
    browser.close()
    return url

def get_url(words):
    with sync_playwright() as playwright:
        url=run(playwright,words)
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
            kovets=tmp.getvalue().decode('utf-8')
            length=len(kovets.split('\n'))
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
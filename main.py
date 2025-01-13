import os
os.system("playwright install")
os.system("playwright install-deps")
import st_pages
import requests,string,os,html5lib
from bs4 import BeautifulSoup
import time,streamlit as st
from playwright.sync_api import Playwright, sync_playwright



def run(playwright:Playwright,words=None,url=None) -> None:
    browser =  playwright.firefox.launch(headless=True)
    context =  browser.new_context()
    page =  context.new_page()
    if url is None:
         page.goto("https://geek.co.il/~mooffie/crossword/")
         page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").press("ControlOrMeta+a")
         page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").fill(words)
         page.get_by_role("button", name="בנה את התשבץ").click()
         page.get_by_role("button", name="צוֹר קישור").click()
    else:
         page.goto(url)
         page.get_by_role("button", name="ההצעה הבאה").click()
         page.get_by_role("button", name="צוֹר קישור").click()
    url=page.url
    # ---------------------
    context.close()
    browser.close()
    return url

def get_url(words=None,cond=None):
    st.write('words=',words,'cond=',cond)
    with sync_playwright() as playwright:
        url =  run(playwright, words,cond)
        return url

def progress():
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()


@st.cache_data
def set_session_state(url):
    if 'url' not in st.session_state:
        st.session_state.url=url
    else:
        st.session_state.url = url

def get_msg(url):
    r =  requests.get(url)
    soup = BeautifulSoup(r.content,'html5lib')  # If this line causes an error, run 'pip install html5lib' or install html5lib
    try:
        msg=soup.find('div',attrs={'class':"messages warning"}).get_text()
        if 'הושמטו' in msg:
            again=st.button('לא כל ההגדרות נוצרו אנא הרץ פעם נוספת')
            if again:
                get_url(cond=url)
        st.write(msg)
    except AttributeError:
        pass

def main():
    '''
    Run playwrite to make cross creation automatic.
    Suppressed, have to create cross in advance, using send link option.
    Uncomment code if you want to use the automatic version.

    :return:
    '''
    st.set_page_config(
        layout="wide",
        page_title="צור תשבץ",
        page_icon="🏁",
    )
    st_pages.show_pages([
        st_pages.Page("main.py", "צור תשבץ", "🏁"),
        st_pages.Page("pages/main_st.py", "פתור תשבץ", "🤔"),
    ])
    kovets=None
    ofen=st.sidebar.radio('בחר אופן יצירת התשבץ',('העלאת קובץ','יצירה במקום','קישור ישיר'),index=2)
    if ofen=='העלאת קובץ':
        tmp=st.file_uploader('העלה בבקשה את קובץ התשבץ')
        if tmp:
            kovets=tmp.getvalue().decode('utf-8')
            set_session_state(kovets)
    elif ofen=='יצירה במקום':
        st.info('לאחר סיום כתיבת ההגדרות מומלץ לגבות אותן בקובץ לפני מעבר לשלב הבא')
        txt=st.text_area('כתוב הגדרות')
        if st.sidebar.toggle('העלה'):
            kovets=txt
    else:
        url=st.text_input('כתוב קישור לתשבץ',value='https://geek.co.il/~mooffie/crossword/temporary/')
        if url:
            send_url=st.button('שלח קישור')
            if send_url:
                set_session_state(url)
                st.info('!הקישור נשלח בהצלחה')
    if kovets is not None:
        url= get_url(words=kovets,cond=None)
        st.write(url)
        get_msg(url)
        progress()
        if url:
            set_session_state(url)
            # st.write(url)

if __name__=='__main__':
    main()
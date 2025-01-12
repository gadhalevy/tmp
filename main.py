import os
os.system("playwright install")
os.system("playwright install-deps")
import asyncio
from playwright.async_api import async_playwright
import requests,string,os
from bs4 import BeautifulSoup
import time,streamlit as st

async def run(playwright,words=None,url=None) -> None:
    browser = await playwright.firefox.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    if url is None:
        await page.goto("https://geek.co.il/~mooffie/crossword/")
        await page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").press("ControlOrMeta+a")
        await page.get_by_text("אנטיביוטיקה - תרופה המשמידה חיידקים קריקטורה - ציור הומוריסטי").fill(words)
        await page.get_by_role("button", name="בנה את התשבץ").click()
        await page.get_by_role("button", name="צוֹר קישור").click()
    else:
        await page.goto(url)
        await page.get_by_role("button", name="ההצעה הבאה").click()
        await page.get_by_role("button", name="צוֹר קישור").click()
    url=page.url
    # ---------------------
    await context.close()
    await browser.close()
    return url

async def get_url(words=None,cond=None):
    async with async_playwright() as playwright:
        url = await run(playwright, words,cond)
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

async def get_msg(url):
    r =  requests.get(url)
    soup = BeautifulSoup(r.content,'html5lib')  # If this line causes an error, run 'pip install html5lib' or install html5lib
    msg=soup.find('div',attrs={'class':"messages warning"}).get_text()
    st.write(msg)
    if 'הושמטו' in msg:
        again=st.button('לא כל ההגדרות נוצרו אנא הרץ פעם נוספת')
        if again:
            await get_url(url)
    st.write(msg)

async def main():
    '''
    Run playwrite to make cross creation automatic.
    Suppressed, have to create cross in advance, using send link option.
    Uncomment code if you want to use the automatic version.

    :return:
    '''
    st.set_page_config(layout="wide")
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
        url=await get_url(kovets)
        await get_msg(url)
        progress()
        if url:
            set_session_state(url)
            st.write(url)

if __name__=='__main__':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
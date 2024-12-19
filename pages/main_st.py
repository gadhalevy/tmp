#This will not run on online IDE
from idlelib.autocomplete import AutoComplete

import requests,string
from bs4 import BeautifulSoup
import time,streamlit as st
import pandas as pd, numpy as np
from streamlit_searchbox import st_searchbox
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from streamlit_lottie import st_lottie

@st.cache_resource()
def init():
    '''
    Init firebase through cloud. Same as verifier
    :return:
    '''
    try:
        firebase_admin.delete_app(firebase_admin.get_app())
    except ValueError:
        pass
    cred = credentials.Certificate(dict(st.secrets['fb']))
    # cred = credentials.Certificate('fb_key.json')
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://Lab9-c9743.firebaseio.com/'})

@st.cache_data
def set_places(url=None):
    '''
    Find indexes x,y of solutions
    :param url: Url of cross-word
    :return: Df of x,y indexes
    '''
    url = url+'/print'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
    table=soup.find('div',attrs={'id':'crossword_wrapper'})
    row_count=0
    dic={}
    for row in table.find_all('tr'):
        col_count=0
        for col in row.findAllNext('td'):
            if col.text.isdigit():
                dic[col.text]=row_count,col_count
            col_count+=1
        row_count+=1
    df=pd.DataFrame.from_dict(dic,orient='index',columns=['X','Y'])
    return df

@st.cache_data
def find_len(url):
    '''
    Find length, clue, answer of each def.
    :param url:
    :return: Df of answer length, clue, answer of each def.
    '''
    r = requests.get(url)
    tmp = BeautifulSoup(r.content, 'html5lib')
    # Where user put definitions.
    defs=tmp.find('textarea',attrs={'id':'raw-words'}).get_text()
    splited=defs.split('\n')
    ques=[];ans=[]
    for s in splited:
        try:
            # a answer, q question
            a,q=s.split('-')
        except ValueError:
            continue
        ques.append(q)
        ans.append(a)
    df=pd.DataFrame({'defs':ques,'answers':ans,'length':[len(a.replace(' ','').strip()) for a in ans]})
    return df

@st.cache_data
def pd_idx_txt(orientation,lst):
    '''
    Find index of answer, clue and orientation.
    :param orientation: Ver, Hor
    :param lst: Got from beautiful soup.
    :return: Df of indexes, clues, and orientation.
    '''
    txts=[]
    idxs=[]
    for l in lst:
        idx=l[:3].strip().replace('.','')
        txt=l[3:]
        if idx.isdigit():
            idxs.append(idx)
        if len(txt)>2:
            txts.append(txt)
    tmp=pd.DataFrame({'index':idxs,'defs':txts,'orientation':[orientation]*len(idxs)})
    return tmp

@st.cache_data
def make_df(url):
    '''
    Summarize all into Df.
    :param url:
    :return: Df defs,answers,index,orientation,x,y
    '''
    # Find x,y location on grid
    places=set_places(url)
    r = requests.get(url+'/print')
    soup = BeautifulSoup(r.content, 'html5lib')
    table=soup.find('table',attrs={'class':'print-nobreak'})
    # Indexes and clues horizontal and vertical.
    tds=table.findAll('td')
    txt=[]
    for t in tds:
        txt.append(t.get_text())
    # Lst of index and horizontal clue
    hor=txt[0].split('\n')
    # Lst of index and vertical clue
    ver=txt[2].split('\n')
    # Df index clue and orientation horizontal
    df_hor=pd_idx_txt('H',hor)
    # Df index clue and orientation vertical
    df_ver=pd_idx_txt('V',ver)
    res=pd.concat([df_hor,df_ver])
    # Add x,y places to Df
    df=res.merge(places,left_on='index',right_index=True)
    df.defs=df.defs.str.strip()
    # Find length, clue, answer of each def.
    txts=find_len(url)
    txts.defs=txts.defs.str.strip()
    final=txts.merge(df)
    return final

@st.cache_data
def clues(url):
    '''
    To do delete it duplicate code
    :param url:
    :return: 2 lists of indexes and clues
    '''
    r = requests.get(url+'/print')
    soup = BeautifulSoup(r.content, 'html5lib')
    table=soup.find('table',attrs={'class':'print-nobreak'})
    tds=table.findAll('td')
    txt=[]
    for t in tds:
        txt.append(t.get_text())
    hor=txt[0].split('\n')[3:]
    ver=txt[2].split('\n')[3:]
    return hor,ver

@st.cache_data
def build_df(url):
    '''
    Build grid using beautiful soup, should use the Df instead.
    :param url:
    :return: Grid as df, row count, col count
    '''
    tmp=np.empty((20,20),dtype='<U3')
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
    table=soup.find('table',attrs={'id':'pzl1'})
    row_count=0
    for row in table.find_all('tr'):
        col_count=0
        for col in row.findAll('td'):
            if col.text:
                num=''.join(c for c in col.text if c.isdigit())
                if num:
                    # tmp[row_count,col_count]=string.ascii_lowercase[int(num)-1]
                    tmp[row_count,col_count]=num
            else:
              tmp[row_count,col_count]=' '
            col_count+=1
        row_count+=1
    fliped=np.fliplr(tmp)
    df=pd.DataFrame(fliped)
    return df,row_count,col_count

@st.cache_data
def make_clues_idxs(lst):
    nums=[h[:3].strip().replace('.','') for h in lst if h[:3].strip().replace('.','').isdigit()]
    abc=[string.ascii_lowercase[int(n)-1] for n in nums]
    return abc

@st.cache_data
def hilight(s):
    # return props if v==' ' else None
    return  ['background-color: red' if ss==' ' else '' for ss in s  ]

@st.cache_data
def txt_color(v, p=''):
    return p if v is not None else None
    # return p if v.strip().isalnum() else None

@st.cache_data
def slider_nums(lst):
    nums=[h[:3] for h in lst if h[:3].strip().replace('.','').isdigit()]
    nums.insert(0,'0')
    return nums

def find_indxs(kivun,name):
    '''

    :param kivun: list of horizontal or vertical clues
    :param kivun_name: direction name
    :return: session states of indexes of each direction
    '''
    idxs=slider_nums(kivun)[1:]
    idxs=[i.strip().replace('.','') for i in idxs]
    if name=='ver':
        idx='v_idxs'
    else:
        idx='h_idxs'
    if f'{idx}' not in st.session_state:
        st.session_state[f'{idx}']=idxs

@st.cache_data
def get_params(df,txt):
    res = df.loc[(df['defs'] == txt[3:]) | (df['defs'] == txt[4:])]
    try:
        length = res['length'].values[0]
        x = res['X'].values[0]
        y = res['Y'].values[0]
        y=19-y
        return length, x, y
    except IndexError:
        pass

def insert_ot(x,y,a,num,kivun):
    if kivun=='hor':
        curr='h_idxs'
        other='v_idxs'
    else:
        other='h_idxs'
        curr='v_idxs'
    # st.write(num)
    # st.write(st.session_state[f'{idx}'])
    if num in st.session_state[f'{other}']:
        st.session_state.cross.iloc[x, y] = a + ' ' + num
        try:
            st.session_state[f'{curr}'].remove(num)
        except ValueError:
            pass
    else:
        st.session_state.cross.iloc[x, y] = a

@st.cache_data
def on_ans(ans,length,x,y,curr):
    if len(ans.strip())==length:
        for i,a in enumerate(ans):
            if len(st.session_state.cross.iloc[x,y])==0:
                st.session_state.cross.iloc[x, y] = a
            elif len(st.session_state.cross.iloc[x, y]) <= 2:
                num=st.session_state.cross.iloc[x,y]
                if num.isnumeric():
                    insert_ot(x,y,a,num,curr)
            elif len(st.session_state.cross.iloc[x, y]) >= 3:
                ot,num=st.session_state.cross.iloc[x,y].strip().split()
                insert_ot(x,y,a,num,curr)
            if curr=='hor':
                y -= 1
            elif curr=='ver':
                x+=1
    else:
        st.error('הגדרה באורך שגוי',icon="🚨")

@st.cache_data
def slider_txt(lst,slide_val):
    txt=[h for h in lst if h.strip().startswith(str(slide_val))]
    return txt[0]

def process(direction,slider,writer,df,user_input,btn,kivun):
    nums = slider_nums(direction)
    choose_h = slider.select_slider('בחר הגדרה ', options=nums, value='0')
    if choose_h != '0':
        txt = slider_txt(direction, choose_h)
        writer.markdown(f'<div style=direction:rtl;font-weight:bold;>{txt}</div>',unsafe_allow_html=True)
        length, x, y = get_params(df, txt)
        ans = user_input.text_input( 'פתרון ' ,)
        pitaron = btn.button('השב ')
        if pitaron:
            on_ans(ans, length, x, y, kivun)

def search_scores(searchterm: str) -> list:
    try:
        return db.reference('/cross/scores/').get().keys() if searchterm else []
    except AttributeError:
        return []

def get_scores(poter):
    '''
    :param poter: What was filled in searchBox
    :return:
    '''
    ref = db.reference('/cross/scores/')
    scores = ref.get()
    # Session contains what it finds
    new_ref = db.reference(f'/cross/scores/{st.session_state.poter['search']}')
    val = 1
    if scores:
        if poter in scores.keys():
            new_ref = db.reference(f'/cross/scores/{poter}')
            score = scores.get(poter)
            val = int(score) + 1
    new_ref.set(val)

def show_res(col3):
    ref=db.reference(f'/cross/scores/')
    tmp=ref.get()
    dic=dict(sorted(tmp.items(), key=lambda item: item[1],reverse=True))
    keys=list(dic.keys())
    scores=list(dic.values())
    colors=['red','green','blue','orange','violet']
    for i in range(len(keys)):
        num= '#' * (7-int(scores[i]))
        col3.write(f' {num}  :{colors[i % len(colors)]}[{keys[i]} {scores[i]}]')

def del_ref():
    ref=db.reference('/cross/scores/')
    ref.delete()

def main():
    st.set_page_config(layout="wide")
    tab1, tab2 = st.tabs(['תשבץ', 'דירוג'])
    with tab1:
        if 'url' in st.session_state:
            st.session_state.url=st.session_state.url
        st.write(st.session_state.url)
        url=st.session_state.url
        if url:
            tashbets,rows,cols = build_df(url)
            if 'cross' not in st.session_state:
                st.session_state.cross=tashbets
            df = make_df(url)
            hor, ver = clues(url)
            # for i in (ver,hor):
            #     find_indxs(i)
            find_indxs(hor,'hor')
            find_indxs(ver, 'ver')
            # st.write(st.session_state.v_idxs)
            # st.write(st.session_state.h_idxs)
            if (len(df))<int(st.session_state.length):
                st.info('לא כל ההגדרות הושמו בתשבץ חזור למסך קודם וטען קובץ פעם נוספת')
            kivun=st.sidebar.radio('בחר כיוון',['מאוזן','מאונך'])
            st.sidebar.header(kivun)
            slider=st.sidebar.empty()
            writer=st.sidebar.empty()
            user_input=st.sidebar.empty()
            btn=st.sidebar.empty()
            st.sidebar.button('רענן מסך')
            if kivun=='מאוזן':
                process(hor,slider,writer,df,user_input,btn,'hor')
            else:
                process(ver,slider,writer,df,user_input,btn,'ver')
            pitaronot=st.sidebar.checkbox('האם להציג פיתרונות?')
            col1,col2=st.columns([10,1])
            styled = st.session_state.cross.style.set_table_styles([{'selector': '', 'props': 'color: blue;font-weight:bold;font-size:1.5em;'}],overwrite=False)
            styled=styled.apply(hilight).hide().hide(axis="columns")
            # Styler not fully implemented in streamlit, switch to html.
            col1.markdown(styled.to_html(), unsafe_allow_html=True)
            # col1.dataframe(styled,height=38 * len(tashbets), hide_index=True)
            if pitaronot:
                col2.info('|'.join(df['answers'].values))
    with tab2:
        # st.write(df['answers'].to_list())
        init()
        col1,col2,col3=st.columns([4,1,2])
        with col3:
            poter = st_searchbox(
                search_scores,
                placeholder="Search User... ",
                key="poter",
            )
        with col2:
            submit=col2.button('נקד פותר')
        if submit:
            get_scores(poter)
            show_res(col3)
        if col3.button('סיום',type='primary'):
            show_res(col3)
            st_lottie('https://lottie.host/ea1fa0a7-3547-458d-868e-b14f85b8d82d/rTfCy1CzPo.json',height=800,width=1200)
            del_ref()




if __name__=='__main__':
    main()

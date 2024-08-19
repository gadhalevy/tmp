#This will not run on online IDE
import requests,string
from bs4 import BeautifulSoup
import time,streamlit as st
import pandas as pd, numpy as np

@st.cache_data
def set_places(url=None):
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
    # url=url.replace('/print','')
    r = requests.get(url)
    tmp = BeautifulSoup(r.content, 'html5lib')
    # st.write(tmp.prettify())
    defs=tmp.find('textarea',attrs={'id':'raw-words'}).get_text()
    splited=defs.split('\n')
    ques=[];ans=[]
    for s in splited:
        try:
            a,q=s.split('-')
        except ValueError:
            continue
        ques.append(q)
        ans.append(a)
    df=pd.DataFrame({'defs':ques,'answers':ans,'length':[len(a.replace(' ','').strip()) for a in ans]})
    return df

@st.cache_data
def pd_idx_txt(orientation,lst):
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
    places=set_places(url)
    r = requests.get(url+'/print')
    soup = BeautifulSoup(r.content, 'html5lib')
    table=soup.find('table',attrs={'class':'print-nobreak'})
    tds=table.findAll('td')
    txt=[]
    for t in tds:
        txt.append(t.get_text())
    hor=txt[0].split('\n')
    ver=txt[2].split('\n')
    df_hor=pd_idx_txt('H',hor)
    df_ver=pd_idx_txt('V',ver)
    res=pd.concat([df_hor,df_ver])
    df=res.merge(places,left_on='index',right_index=True)
    df.defs=df.defs.str.strip()
    txts=find_len(url)
    txts.defs=txts.defs.str.strip()
    final=txts.merge(df)
    return final

@st.cache_data
def clues(url):
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
    return ['background-color: red' if ss==' ' else '' for ss in s  ]

@st.cache_data
def slider_nums(lst):
    nums=[h[:3] for h in lst if h[:3].strip().replace('.','').isdigit()]
    nums.insert(0,'0')
    return nums

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

@st.cache_data
def on_ans(ans,length,x,y,curr):
    if len(ans.strip())==length:
        for a in ans:
            if len(st.session_state.cross.iloc[x,y])==0:
                st.session_state.cross.iloc[x,y]='  '+a
            elif len(st.session_state.cross.iloc[x,y])<=2:
                num=st.session_state.cross.iloc[x,y]
                if num.isnumeric():
                    st.session_state.cross.iloc[x,y]=num+' '+a
            elif len(st.session_state.cross.iloc[x,y])>=3:
                if len(st.session_state.cross.iloc[x,y].strip())>=3:
                    num,ot=st.session_state.cross.iloc[x,y].strip().split()
                    st.session_state.cross.iloc[x,y]=num+'  '+a
                else:
                    st.session_state.cross.iloc[x,y]='  '+a
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
        writer.write(txt)
        length, x, y = get_params(df, txt)
        ans = user_input.text_input( 'פתרון ' ,)
        pitaron = btn.button('השב ')
        if pitaron:
            on_ans(ans, length, x, y, kivun)

def main():
    st.set_page_config(layout="wide")
    # st.write('הקש על הקישור וצור תשבץ')
    # st.write('https://geek.co.il/~mooffie/crossword')
    # url = st.text_input('כתוב את כתובת התשבץ')
    st.write(st.session_state.url)
    url=st.session_state.url
    if url:
        tashbets,rows,cols = build_df(url)
        if 'cross' not in st.session_state:
            st.session_state.cross=tashbets.iloc[:rows,19-cols:]
        df = make_df(url)
        hor, ver = clues(url)
        st.write(len(hor),len(ver),st.session_state.length)
        if (len(hor)+len(ver))>int(st.session_state.length)+2:
            st.info('לא כל ההגדרות הושמו בתשבץ חזור למסך קודם וטען קובץ פעם נוספת')
        styled = st.session_state.cross.style.hide().apply(hilight)
        kivun=st.sidebar.radio('בחר כיוון',['מאוזן','מאונך'])
        st.sidebar.header(kivun)
        slider=st.sidebar.empty()
        writer=st.sidebar.empty()
        user_input=st.sidebar.empty()
        btn=st.sidebar.empty()
        if kivun=='מאוזן':
            process(hor,slider,writer,df,user_input,btn,'hor')
        else:
            process(ver,slider,writer,df,user_input,btn,'ver')
        st.dataframe(styled,height=38 * len(tashbets.iloc[:rows+1,19-cols:]), hide_index=True)

if __name__=='__main__':
    main()
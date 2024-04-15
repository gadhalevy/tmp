#This will not run on online IDE
import requests,string
from bs4 import BeautifulSoup
import pandas as pd,numpy as np
from taipy.gui import Gui,notify

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

def digit_font(state,index,vals):
    for i in range(20):
        if vals[i].isdigit():
            return "small-digit"
        else:
            return "big-ascii"

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
                    tmp[row_count,col_count]=string.ascii_lowercase[int(num)-1]
            else:
              tmp[row_count,col_count]='X'
            col_count+=1
        row_count+=1
    fliped=np.fliplr(tmp)[:row_count+1,:col_count+1]
    df=pd.DataFrame(fliped)
    return fliped

def make_clues_idxs(lst):
    nums=[h[:3].strip().replace('.','') for h in lst if h[:3].strip().replace('.','').isdigit()]
    abc=[string.ascii_lowercase[int(n)-1] for n in nums]
    return abc

current=''
value_hor=0
value_ver=0
url=''
data_hor=''
data_ver=''
df=pd.DataFrame(np.empty((100,100)))
hor=''
ver=''
tashbets=np.empty((20,20),dtype='<U3')
ans_hor=''
ans_ver=''
idx_hor=''
idx_ver=''

def cross(state):
    state.tashbets=build_df(state.url)
    state.df=make_df(state.url)
    state.hor,state.ver=clues(state.url)
    state.idx_hor=make_clues_idxs(state.hor)
    state.idx_ver=make_clues_idxs(state.ver)


def on_ans(state):
    if state.current=='hor':
        data=state.data_hor
        ans=state.ans_hor
    elif state.current=='ver':
        data=state.data_ver
        ans=state.ans_ver
    res = state.df.loc[(state.df['defs'] == data[2:]) | (state.df['defs'] == data[3:])]
    length=res['length'].values[0]
    x=res['X'].values[0]
    y=res['Y'].values[0]
    y=19-y
    newdf=state.tashbets.copy()
    if len(ans.strip())==length:
        for a in ans:
            if len(newdf[x,y])==1:
                if newdf[x,y] in string.ascii_lowercase:
                    num=newdf[x,y]
                    newdf[x,y]=a+' '+num
            elif len(newdf[x,y])==0:
                newdf[x,y]=a
            if state.current=='hor':
                y-=1
            elif state.current=='ver':
                x+=1
        state.tashbets=newdf
        state.ans_hor=state.ans_ver=''
    else:
        notify(state,'warning','תשובה באורך שגוי')

def on_slider(state):
    state.data_hor=state.data_ver=''
    if state.current=='hor':
        value=state.value_hor
        clue=state.hor
    elif state.current=='ver':
        value=state.value_ver
        clue=state.ver
    tmp=[h for h in clue if h.strip().startswith(str(value)+'.')]
    tmp=tmp[0].replace(str(value)+'.',string.ascii_lowercase[value-1])
    if state.current=='hor':
        state.data_hor=tmp
    elif state.current=='ver':
        state.data_ver=tmp
def on_slider_hor(state):
    state.current='hor'
    on_slider(state)

def on_slider_ver(state):
    state.current='ver'
    on_slider(state)

def on_input_hor(state,var,val):
    state.ans_hor=val

def on_input_ver(state,var,value):
    state.ans_ver=value

page="""
<|toggle|theme|>

## הקש על הקישור וצור תשבץ

[https://geek.co.il/~mooffie/crossword](https://geek.co.il/~mooffie/crossword)

### אנא כתוב את כתובת התשבץ

<|{url}|input|>
<|צור תשבץ|button|on_action=cross|>

<|{tashbets}|table|>

<|layout|columns=1 1|
<|
## מאוזן
<|{idx_hor}|text|>{: .big-letter }

<|{value_hor}|slider|on_change=on_slider_hor|min=0|max=20|>

<|{data_hor}|text|>{: .big-letter }

<|{ans_hor}|input|on_change=on_input_hor|>
<|השב|button|on_action=on_ans|>
|>

<|
## מאונך
<|{idx_ver}|text|>{: .big-letter }

<|{value_ver}|slider|on_change=on_slider_ver|min=0|max=20|>

<|{data_ver}|text|>{: .big-letter }

<|{ans_ver}|input|on_change=on_input_ver|>
<|השב|button|on_action=on_ans|>
|>
|>
"""
Gui(page).run(debug=True)
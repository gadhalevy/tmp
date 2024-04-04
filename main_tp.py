#This will not run on online IDE
import requests
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

def build_df(url):
    # row=[None,]*20
    # data={str(i):row for i in range(20)}
    # df=pd.DataFrame(data=data)
    tmp=np.empty((20,20),dtype='<U2')
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
                    tmp[row_count,col_count]=num
                # elif not col.text.isdigit():
                #     tmp[row_count,col_count]='o'
            # else:
            #     tmp[row_count,col_count]='x'
            col_count+=1
        row_count+=1
    fliped=np.fliplr(tmp)
    lst=[str(i) for i in range(col_count)]
    idx=[str(i) for i in range(row_count)]
    df=pd.DataFrame(fliped,columns=lst,index=idx)
    return df

def make_options(lst):
    nums=[h[:3] for h in lst if h[:3].strip().replace('.','').isdigit()]
    nums.insert(0,'0')
    return nums
    # choose=st.select_slider('בחר הגדרה',options=nums,value='0')
    # if choose!='0':
    #     txt=[h for h in lst if h.strip().startswith(choose)]
    #     return txt[0]
    # return 'בחר הגדרה'
value_hor=0
value_ver=0
url=''
data_hor=''
data_ver=''
df=pd.DataFrame(np.empty((100,100)))
hor=''
ver=''
tashbets=pd.DataFrame(np.empty((20,20),dtype='<U3'))
ans_hor=''
ans_ver=''
id_hor=''
h_prop={'name':'hor'}
# v_prop={'name':'ver'}

def cross(state):
    state.tashbets=build_df(state.url)
    state.df=make_df(state.url)
    state.hor,state.ver=clues(state.url)

def on_slider_hor(state):
    state.data_hor=[h for h in state.hor if h.strip().startswith(str(state.value_hor)+'.')]

def prepare(state):
    res = state.df.loc[(state.df['defs'] == state.data_hor[0][3:]) | (state.df['defs'] == state.data_hor[0][4:])]
    length=res['length'].values[0]
    x=res['X'].values[0]
    y=res['Y'].values[0]
    y=19-y
    newdf=state.tashbets.copy()
    return res,length,x,y,newdf

def on_ans_hor(state,id,dic):
    res = state.df.loc[(state.df['defs'] == state.data_hor[0][3:]) | (state.df['defs'] == state.data_hor[0][4:])]
    length=res['length'].values[0]
    x=res['X'].values[0]
    y=res['Y'].values[0]
    y=19-y
    newdf=state.tashbets.copy()
    if len(state.ans_hor.strip())==length:
        for a in state.ans_hor:
            if len(newdf.iloc[x,y])==1:
                if newdf.iloc[x,y].isdigit():
                    newdf.iloc[x,y]+=' '+a
                    newdf.iloc[x,y]=newdf.iloc[x,y][::-1]
            elif len(newdf.iloc[x,y])==0:
                newdf.iloc[[x],[y]]=a
            y-=1
        state.tashbets=newdf
        ans_hor=''
    else:
        notify(state,'warning','תשובה באורך שגוי')

def on_ans_ver(state):
    res = state.df.loc[(state.df['defs'] == state.data_ver[0][3:]) | (state.df['defs'] == state.data_ver[0][4:])]
    length=res['length'].values[0]
    x=res['X'].values[0]
    y=res['Y'].values[0]
    y=19-y
    newdf=state.tashbets.copy()
    if len(state.ans_ver.strip())==length:
        for a in state.ans_ver:
            if len(newdf.iloc[x,y])==1:
                if newdf.iloc[x,y].isdigit():
                    num=newdf.iloc[x,y]
                    newdf.iloc[x,y]=num+a
            elif len(newdf.iloc[x,y])==0:
                newdf.iloc[[x],[y]]=a
            x+=1
        state.tashbets=newdf
        ans_ver=''
    else:
        notify(state,'warning','תשובה באורך שגוי')

def on_slider_ver(state):
    state.data_ver=[h for h in state.ver if h.strip().startswith(str(state.value_ver)+'.')]

def on_input_hor(state,var,val):
    state.ans_hor=val

def on_input_ver(state,var,value):
    state.ans_ver=value

h_prop={"name":"h"}

page="""
<|toggle|theme|>

## הקש על הקישור וצור תשבץ

[https://geek.co.il/~mooffie/crossword](https://geek.co.il/~mooffie/crossword)

### אנא כתוב את כתובת התשבץ

<|{url}|input|>
<|צור תשבץ|button|on_action=cross|>

<|{tashbets}|table|editable={True}|class_name=rows-bordered|>

<|layout|columns=1 1|
<|
## מאוזן
<|{value_hor}|slider|on_change=on_slider_hor|min=0|max=20|>

<|{data_hor}|text|>

<|{ans_hor}|input|on_change=on_input_hor|>
<|השב|button|properties={h_prop}|on_action=on_ans_hor|>
|>

<|
## מאונך
<|{value_ver}|slider|on_change=on_slider_ver|min=0|max=20|>

<|{data_ver}|text|>

<|{ans_ver}|input|on_change=on_input_ver|>
<|השב|button|on_action=on_ans_ver|>
|>
|>
"""
Gui(page).run(debug=True)
    # st.write('הקש על הקישור וצור תשבץ')
        # st.write('https://geek.co.il/~mooffie/crossword')
        # url=st.text_input('כתוב את כתובת התשבץ')
        # if url:
        #     tashbets=build_df(url)
        #     tashbets
        #     df=make_df(url)
        #     df
        #
        #     # builder = GridOptionsBuilder.from_dataframe(df)
        #     # builder.configure_columns(column_names=[str(i) for i in range(20)],  width=35,editable=True)
        #     # go = builder.build()
        #     # # uses the gridOptions dictionary to configure AgGrid behavior.
        #     # AgGrid(df, gridOptions=go)
        #     hor,ver=clues()
        #
        #     col1, col2 = st.columns(2)
        #
        #     with col1:
        #         st.header("מאוזן")
        #         choose_h=st.empty()
        #         txt=extract_def(hor,choose_h)
        #         txt
        #         res=df.loc[(df['defs']==txt[3:]) | (df['defs']==txt[4:])]
        #         length=res['length'].values[0]
        #         x=res['X'].values[0]
        #         y=res['Y'].values[0]
        #         y=19-y
        #         # tashbets.iloc[[14],[13,14,15,16]]
        #         tashbets.iloc[[x],[y]]
        #         ans=st.text_input('פתרון אופקי',max_chars=length)
        #         if ans:
        #             for a in ans:
        #                 tashbets.iloc[[x],[y]]+=a
        #                 y-=1
        #         tashbets
        #
        #     with col2:
        #         st.header("מאונך")
        #         choose_v=st.empty()
        #         txt=extract_def(ver,choose_v)
        #         txt
        #         res=df.loc[(df['defs']==txt[3:]) | (df['defs']==txt[4:])]
        #         length=res['length'].values[0]
        #         x=res['X'].values[0]
        #         y=res['Y'].values[0]
        #         y=19-y
        #         # tashbets.iloc[[14],[13,14,15,16]]
        #         tashbets.iloc[[x],[y]]
        #         ans=st.text_input('פתרון אנכי',max_chars=length)
        #         if ans:
        #             for a in ans:
        #                 tashbets.iloc[[x],[y]]+=a
        #                 x+=1
        #         tashbets
        #

        # grid_return = AgGrid(df, editable=True)
        # new_df = grid_return['data']
        # new_df










# if __name__=='__main__':
#     cross=Cross()
#     cross.main()
    # cross.build_df('https://geek.co.il/~mooffie/crossword/7433')
    # cross.set_places()
    # cross.find_len()
    # cross.main()
    # cross.set_places()
    # st.write(cross.set_places())
    # cross.find_len()
    # cross.find_len(orientation='V',attrVal='<div class="direction-title">מאונך</div>')
    # cross.make_cross()
    # print(cross.set_places())
    # set_places()
    # make_cross()



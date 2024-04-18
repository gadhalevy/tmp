#This will not run on online IDE
import requests,string
from bs4 import BeautifulSoup
import time,streamlit as st
import pandas as pd, numpy as np
from docutils.nodes import header
import streamlit.components.v1 as components
from sympy.unify.core import index


#
# def set_places(url=None):
#     url = url+'/print'
#     r = requests.get(url)
#     soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
#     table=soup.find('div',attrs={'id':'crossword_wrapper'})
#     row_count=0
#     dic={}
#     for row in table.find_all('tr'):
#         col_count=0
#         for col in row.findAllNext('td'):
#             if col.text.isdigit():
#                 dic[col.text]=row_count,col_count
#             col_count+=1
#         row_count+=1
#     df=pd.DataFrame.from_dict(dic,orient='index',columns=['X','Y'])
#     return df
#
# def find_len(url):
#     # url=url.replace('/print','')
#     r = requests.get(url)
#     tmp = BeautifulSoup(r.content, 'html5lib')
#     # st.write(tmp.prettify())
#     defs=tmp.find('textarea',attrs={'id':'raw-words'}).get_text()
#     splited=defs.split('\n')
#     ques=[];ans=[]
#     for s in splited:
#         try:
#             a,q=s.split('-')
#         except ValueError:
#             continue
#         ques.append(q)
#         ans.append(a)
#     df=pd.DataFrame({'defs':ques,'answers':ans,'length':[len(a.replace(' ','').strip()) for a in ans]})
#     return df
#
#
# def pd_idx_txt(orientation,lst):
#     txts=[]
#     idxs=[]
#     for l in lst:
#         idx=l[:3].strip().replace('.','')
#         txt=l[3:]
#         if idx.isdigit():
#             idxs.append(idx)
#         if len(txt)>2:
#             txts.append(txt)
#     tmp=pd.DataFrame({'index':idxs,'defs':txts,'orientation':[orientation]*len(idxs)})
#     return tmp
#
#
# def make_df(url):
#     places=set_places(url)
#     table=soup.find('table',attrs={'class':'print-nobreak'})
#     tds=table.findAll('td')
#     txt=[]
#     for t in tds:
#         txt.append(t.get_text())
#     hor=txt[0].split('\n')
#     ver=txt[2].split('\n')
#     df_hor=pd_idx_txt('H',hor)
#     df_ver=pd_idx_txt('V',ver)
#     res=pd.concat([df_hor,df_ver])
#     df=res.merge(places,left_on='index',right_index=True)
#     df.defs=df.defs.str.strip()
#     txts=find_len(url)
#     txts.defs=txts.defs.str.strip()
#     final=txts.merge(df)
#     return final
#
# def build_df(url):
#     tmp = np.empty((20, 20), dtype='<U3')
#     r = requests.get(url)
#     soup = BeautifulSoup(r.content,
#                          'html5lib')  # If this line causes an error, run 'pip install html5lib' or install html5lib
#     table = soup.find('table', attrs={'id': 'pzl1'})
#     row_count = 0
#     for row in table.find_all('tr'):
#         col_count = 0
#         for col in row.findAll('td'):
#             if col.text:
#                 num = ''.join(c for c in col.text if c.isdigit())
#                 if num:
#                     tmp[row_count, col_count] = string.ascii_lowercase[int(num) - 1]
#             col_count += 1
#         row_count += 1
#     fliped = np.fliplr(tmp)[:row_count + 1, :col_count + 1]
#     df = pd.DataFrame(fliped)
#     return fliped, row_count, col_count

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
    fliped=np.fliplr(tmp)[:row_count+1,:col_count+1]
    df=pd.DataFrame(fliped)
    return df

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
            if 2>=len(st.session_state.cross.iloc[x,y])>0:
                num=st.session_state.cross.iloc[x,y]
                if num.isnumeric():
                    st.session_state.cross.iloc[x,y]=num+' '+a
            elif len(st.session_state.cross.iloc[x,y])==0:
                st.session_state.cross.iloc[x,y]=a
            # st.session_state.cross.iloc[[x], [y]] +=' '+ a
            if curr=='hor':
                y -= 1
            elif curr=='ver':
                x+=1
    else:
       st.error('הגדרה באורך שגוי',icon="🚨")


def slider_txt(lst,slide_val):
    txt=[h for h in lst if h.strip().startswith(str(slide_val))]
    return txt[0]
# @st.cache_data
# def extract_def(lst):# @st.cache_data
# def extract_def(lst):
#     nums=[h[:3] for h in lst if h[:3].strip().replace('.','').isdigit()]
#     nums.insert(0,'0')
#     nums=[h[:3] for h in lst if h[:3].strip().replace('.','').isdigit()]
#     nums.insert(0,'0')
#     choose=st.select_slider('בחר הגדרה',options=nums,value='0')
#     if choose!='0':
#         txt=[h for h in lst if h.strip().startswith(str(choose))]
#         return txt[0]
#     return 'בחר הגדרה'
def main():
    st.write('הקש על הקישור וצור תשבץ')
    st.write('https://geek.co.il/~mooffie/crossword')
    url = st.text_input('כתוב את כתובת התשבץ')
    if url:
        tashbets = build_df(url)
        if 'cross' not in st.session_state:
            st.session_state.cross=tashbets
        df = make_df(url)
        hor, ver = clues(url)
        styled = st.session_state.cross.style.hide().apply(hilight)
        # s='הצגת תשבץ כיישום ברשת'[::-1]
        # dic={i: ss for i,ss in enumerate(s)}
        # st.dataframe(styled,height=35*len(tashbets),hide_index=True)
        place_holder=st.empty()
        col1, col2 = st.columns(2)
        with col1:
            st.header("מאוזן")
            nums=slider_nums(hor)
            choose_h = st.select_slider('בחר הגדרה אופקית',options=nums,value='0')
            if choose_h!='0':
                txt=slider_txt(hor,choose_h)
                st.write(txt)
                length,x,y=get_params(df,txt)
                ans=st.text_input('פתרון אופקי')
                pitaron=st.button('השב אופקי')
                if pitaron:
                    on_ans(ans,length,x,y,'hor')
        with col2:
            st.header("מאונך")
            nums=slider_nums(ver)
            choose_v = st.select_slider('בחר הגדרה אנכית',options=nums,value='0')
            if choose_v!='0':
                txt=slider_txt(ver,choose_v)
                st.write(txt)
                length,x,y=get_params(df,txt)
                ans=st.text_input('פתרון אנכי')
                pitaron=st.button('השב אנכי')
                if pitaron:
                    on_ans(ans,length,x,y,'ver')
        place_holder.dataframe(styled, height=35 * len(tashbets), hide_index=True)



        #     txt = extract_def(hor)
        #     st.write(txt)
        #     res = df.loc[(df['defs'] == txt[3:]) | (df['defs'] == txt[4:])]
        #     try:
        #         length = res['length'].values[0]
        #         x = res['X'].values[0]
        #         y = res['Y'].values[0]
        #     except IndexError:
        #         pass
        #     y = 19 - y
        #     # tashbets.iloc[[14],[13,14,15,16]]
        #     # tashbets.iloc[[x], [y]]
        #     ans = st.text_input('פתרון אופקי', max_chars=length)
        #     st.write(len(ans) ==length)
        #     if len(ans) ==length:
        #         for a in ans:
        #             tashbets.iloc[[x], [y]] += a
        #             y -= 1
        #     # components.html(tashbets.to_html(header=False,index=False),height=len(tashbets)*26)
        #
        # with col2:
        #     st.header("מאונך")
        #     choose_v = st.empty()
        #     txt = extract_def(ver, choose_v)
        #     st.write(txt)
        #     res = df.loc[(df['defs'] == txt[3:]) | (df['defs'] == txt[4:])]
        #     try:
        #         length = res['length'].values[0]
        #         x = res['X'].values[0]
        #         y = res['Y'].values[0]
        #     except IndexError:
        #         pass
        #     y = 19 - y
        #     # tashbets.iloc[[14],[13,14,15,16]]
        #     # tashbets.iloc[[x], [y]]
        #     ans = st.text_input('פתרון אנכי', max_chars=length)
        #     if ans:
        #         for a in ans:
        #             tashbets.iloc[[x], [y]] += a
        #             x += 1
        # components.html(tashbets.to_html(header=False,index=False),height=len(tashbets)*26,width=500)


    # builds a gridOptions dictionary using a GridOptionsBuilder instance.
    # builder = GridOptionsBuilder.from_dataframe(df)
    # builder.configure_columns(column_names=[str(i) for i in range(20)],  width=35,editable=True)
    # go = builder.build()
    # # uses the gridOptions dictionary to configure AgGrid behavior.
    # AgGrid(df, gridOptions=go)
    # # grid_return = AgGrid(df, editable=True)
    # # new_df = grid_return['data']
    # # new_df










if __name__=='__main__':
    main()
# cross.set_places()
# st.write(cross.set_places())
# cross.find_len()
# cross.find_len(orientation='V',attrVal='<div class="direction-title">מאונך</div>')
# cross.make_cross()
# print(cross.set_places())
# set_places()
# make_cross()

# import streamlit as st
# import pandas as pd
#
# # Sample DataFrame
# df = pd.DataFrame({
#     'A': [1, 2, 3, 4],
#     'B': [10, 20, 30, 40],
#     'C': [100, 200, 300, 400]
# })
#
# # Function to apply custom styling to the maximum cell
# def highlight_max_cell(s):
#     # st.write(s)
#     is_max = s == s.max()
#     # st.write(is_max)
#     # st.write(['background-color: yellow' if v else '' for v in is_max])
#     return ['background-color: yellow' if ss==400 else '' for ss in s  ]
#
# # Apply custom styling to the maximum cell
# styled_df = df.style.hide().apply(highlight_max_cell)
# # Display styled DataFrame
# st.write(styled_df)
# import pandas as pd,numpy as np,streamlit as st
# weather_df = pd.DataFrame(np.random.rand(10,2)*5,
#                           index=pd.date_range(start="2021-01-01", periods=10),
#                           columns=["Tokyo", "Beijing"])
#
# def rain_condition(v):
#     if v < 1.75:
#         return "Dry"
#     elif v < 2.75:
#         return "Rain"
#     return "Heavy Rain"
#
# def make_pretty(styler):
#     styler.set_caption("Weather Conditions")
#     styler.format(rain_condition)
#     styler.format_index(lambda v: v.strftime("%A"))
#     styler.background_gradient(axis=None, vmin=1, vmax=5, cmap="YlGnBu")
#     return styler
#
# weather_df.iloc[0:4].style.pipe(make_pretty)
# st.write(weather_df)
#This will not run on online IDE
import requests
from bs4 import BeautifulSoup
import time,streamlit as st
import pandas as pd,numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder


class Cross:
    def set_places(self,url=None):
        url = url+'/print'
        r = requests.get(url)
        self.soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
        table=self.soup.find('div',attrs={'id':'crossword_wrapper'})
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

    def find_len(self,url):
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


    def pd_idx_txt(self,orientation,lst):
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


    def make_df(self,url):
        places=self.set_places(url)
        table=self.soup.find('table',attrs={'class':'print-nobreak'})
        tds=table.findAll('td')
        txt=[]
        for t in tds:
            txt.append(t.get_text())
        hor=txt[0].split('\n')
        ver=txt[2].split('\n')
        df_hor=self.pd_idx_txt('H',hor)
        df_ver=self.pd_idx_txt('V',ver)
        res=pd.concat([df_hor,df_ver])
        df=res.merge(places,left_on='index',right_index=True)
        df.defs=df.defs.str.strip()
        txts=self.find_len(url)
        txts.defs=txts.defs.str.strip()
        final=txts.merge(df)
        return final


    def build_df(self,url):
        # row=[None,]*20
        # data={str(i):row for i in range(20)}
        # df=pd.DataFrame(data=data)
        tmp=np.empty((20,20),dtype='<U2')
        r = requests.get(url)
        self.soup = BeautifulSoup(r.content, 'html5lib') # If this line causes an error, run 'pip install html5lib' or install html5lib
        table=self.soup.find('table',attrs={'id':'pzl1'})
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
                else:
                    tmp[row_count,col_count]='x'
                col_count+=1
            row_count+=1
        fliped=np.fliplr(tmp)
        df=pd.DataFrame(fliped,columns=[str(i) for i in range(20)])
        return df




    def main(self):
        st.write('הקש על הקישור וצור תשבץ')
        st.write('https://geek.co.il/~mooffie/crossword')
        url=st.text_input('כתוב את כתובת התשבץ')
        if url:
            df=self.build_df(url)
            builder = GridOptionsBuilder.from_dataframe(df)
            builder.configure_columns(column_names=[str(i) for i in range(20)],  width=35,editable=True)
            go = builder.build()
            # uses the gridOptions dictionary to configure AgGrid behavior.
            AgGrid(df, gridOptions=go)
        # grid_return = AgGrid(df, editable=True)
        # new_df = grid_return['data']
        # new_df










if __name__=='__main__':
    cross=Cross()
    cross.main()
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



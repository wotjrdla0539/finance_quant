# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 15:34:23 2020

@author: LeeHJ
"""

import pymysql
import pandas as pd
import numpy as np
import datetime as dt
import uuid
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.optimize as optm
from matplotlib.dates import MonthLocator, DateFormatter, WeekdayLocator
import warnings

warnings.filterwarnings(action='ignore')


### DB 접속
stock_db = pymysql.connect(
    user='crawler',
    passwd='crawler123!',
    host='172.30.1.46', 
    #host='137.68.198.32', 
    port=3306,
    db='stockdata', 
    charset='utf8'
    )
cur = stock_db.cursor()

const_exit = '#exit'

#%%
### 로그인!
def idpw_check(id, pw):
    sql = "SELECT * FROM TB_USER WHERE ID = '%s'" % id
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    res = cur.fetchone()
    print(res)
    
    if pd.isnull(res):
        return (False, -1, "존재하지 않는 ID 입니다.")    
    elif res[2] != pw:
        return (False, -2, "잘못된 비밀번호 입니다.")
    else:
        return (True, res[0], "로그인 성공, '" + res[3] +"'님 환영합니다.")

def do_login():
    res = False
    user_id = -1
    while(res == False):
        print('\n\nlogin: ID 를 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        id = ip
        
        print('\n\nlogin: PW 를 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        pw = ip
        
        #print(id, pw)
        res, user_id, msg = idpw_check(id, pw)
        print(msg)
        print()
    
    return res, user_id
    
### 회원가입!
def register_id(id, pw):
    res = idpw_check(id, pw)
    # 존재하지 않는 ID, 회원가입 처리
    
    if(res[0] == False and res[1] == -1):
        print('\n\nregister: 이름을 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        name = ip
        
        print('\n\nregister: 생년월일을 입력해주세요. ex. 1990-01-01 (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        birth = ip
        birth = dt.datetime.strptime(birth,'%Y-%m-%d').date()
        
        print('\n\nregister: 부양 가족 수를 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        f_num = ip
        
        print(id, pw, name, birth, f_num)
        
        u_id = str(uuid.uuid4().fields[-1])[:5]
        sql = "INSERT INTO TB_USER VALUES(%s, '%s', '%s', '%s', '%s', %s)" % (u_id, id, pw, name, birth, f_num)
    
        print('\n[SQL-log] '+sql+"\n")   
        cur.execute(sql)
        
        res, user_id, msg = idpw_check(id, pw)
        
        stock_db.commit()
        
        return (res, user_id, msg)
        
    else:
        return (False, -1, "이미 존재하는 ID 입니다.")

def do_register():
    res = False
    user_id = -1
    
    while(res == False):
        print('\n\nregister: ID 를 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        id = ip
        
        print('\n\nregister: PW 를 입력해주세요. (나가기 : %s)'% const_exit)
        ip = input()
        if ip == const_exit : return (False, -1)
        pw = ip
        
        #print(id, pw)
        res, user_id, msg = register_id(id, pw)
        print(msg)
    
    return res, user_id
    
### 투자성향 조사!
def do_survey(user_id):
    iv_period = 1
    
    # 설문 문제 LIST 추출
    sql = "SELECT * FROM TB_SURV_QUES"
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    res = cur.fetchall()
    
    ans_li = []
    print("< 투자성향 조사 >")
    for ques in list(res):
        
        # 문제에 대한 답변 리스트 호출.
        sql = "SELECT * FROM TB_SURV_ANS WHERE QUES = %s" % ques[0]
        print('\n[SQL-log] '+sql+"\n")
        cur.execute(sql)
        show_ans = cur.fetchall()
        
        tmp_acc = False
        while(tmp_acc == False):
            
            print()
            print(str(ques[0]) + ". " + ques[1])
        
            for show in list(show_ans):
                print("   "+str(show[1]) + ") " + show[2])
            
            try:
                u_ans = int(input())
                
                if u_ans >= 1 and u_ans <= len(show_ans):
                    tmp_acc = True
                else:
                    print('잘못된 값이 입력되었습니다.')
            except:
                print('잘못된 값이 입력되었습니다.')
        ans_li.append(u_ans)
    
    tmp_acc = False
    while(tmp_acc == False):
        print()
        print('** 실제 투자할 기간을 선택해주세요. **')
        print('  1) 3M')
        print('  2) 6M')
        print('  3) 1Y')
        try:
            iv_period = int(input())
            
            if iv_period >= 1 and iv_period <= 3:
                tmp_acc = True
            else:
                print('잘못된 값이 입력되었습니다.')
        except:
            print('잘못된 값이 입력되었습니다.')
    if iv_period == 1: iv_period = '3M'
    if iv_period == 2: iv_period = '6M'
    if iv_period == 3: iv_period = '1Y'
    
    print(ans_li)
    print('투자기간 : ' + iv_period)
    
    sql = "SELECT IFNULL(MAX(SRNO),0) + 1 FROM TB_SURV WHERE USER_ID = '%s'" % user_id
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    srno = cur.fetchone()
    srno = srno[0]
    
    
    sql = "INSERT INTO TB_SURV VALUES( %s, %s, now(), '%s', 0)" %(user_id, srno, iv_period)
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    
    
    sql = "INSERT INTO TB_SURV_DETAIL VALUES( %s, %s, %s, %s)"
    
    surv_detail = pd.DataFrame(np.array([np.arange(1,7),ans_li]).T, columns=['ques','ans'])
    surv_detail['user_id'] = user_id
    surv_detail['srno'] = srno
    surv_detail = surv_detail[['user_id','srno','ques','ans']]
    val = np.array(surv_detail).tolist()
    print('\n[SQL-log] '+sql+"\n")
    cur.executemany(sql,val)
    
    sql = """
    UPDATE   TB_SURV A
       SET   CLASS = (
                      SELECT C_S.CLASS
                      FROM
                         (
                         SELECT USER_ID, AGE_T.USER_SCORE + FAMILY_T.USER_SCORE AS P_SCORE
                            FROM TB_USER 
                               ,(SELECT MIN, MAX, USER_SCORE
                                FROM TB_USER_SCORE
                                WHERE USER_INFO = 'AGE') AS AGE_T
                               ,(SELECT MIN, MAX, USER_SCORE
                                FROM TB_USER_SCORE
                                WHERE USER_INFO = 'FAMILY_NUM') AS FAMILY_T
                            WHERE (YEAR(NOW()) - YEAR(BIRTH) + 1) BETWEEN AGE_T.MIN AND AGE_T.MAX
                            AND TB_USER.FAMILY_NUM BETWEEN FAMILY_T.MIN AND FAMILY_T.MAX
                          ) AS P_DATA,
                         (
                            SELECT A.USER_ID, A.SRNO, SUM(B.SCORE) AS R_SCORE
                            FROM TB_SURV_DETAIL A, TB_SURV_ANS B
                            WHERE A.QUES = B.QUES
                              AND A.ANS = B.ANS
                              GROUP BY USER_ID, SRNO
                         ) AS R_DATA 
                         , TB_CLASS_SCORE AS C_S
                      WHERE P_DATA.USER_ID = R_DATA.USER_ID
                        AND C_S.R_SCORE = R_DATA.R_SCORE
                        AND C_S.P_SCORE = P_DATA.P_SCORE
                        AND R_DATA.USER_ID = A.USER_ID
                        AND R_DATA.SRNO = A.SRNO
                  )
     WHERE   USER_ID = %s
       AND  SRNO = %s
    """ %(user_id, srno)
    
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    
    stock_db.commit()
    print(val)
    
    return (user_id, srno)

### 과거 히스토리 조회!
def load_history(user_id):
    ans = 0
    sql = """
    SELECT A.USER_ID, A.SRNO, A.SURV_DATE, A.PERIOD, A.CLASS, B.DETAIL
    FROM TB_SURV A,TB_CLASS B 
    WHERE A.CLASS = B.CLASS AND USER_ID = %s
    ORDER BY A.USER_ID, A.SRNO
    """ % user_id
   
    print('\n[SQL-log] '+sql+"\n")          
    cur.execute(sql)
    res = cur.fetchall()
    
    if res == ():
        print('추천받은 포트폴리오 내역이 없습니다.\n')
        return False, res
        
    tmp_acc = False
    while(tmp_acc == False):         
        print('< history >')
        for surv in res:
            print("  %d. 투자기간(%s) / 투자성향(%s) / 일시(%s)" %(surv[1],surv[3],surv[5],surv[2]))
            
        try:
            print("  %d. exit" %(len(res) + 1))
            print('- 확인하고 싶은 포트폴리오를 선택해주세요.')
            ans = int(input())
            
            if ans >= 1 and ans <= len(res):
                tmp_acc = True
            elif ans == len(res) + 1:
                return False, res
            else:
                print('잘못된 값이 입력되었습니다.')
        except:
            print('잘못된 값이 입력되었습니다.')
    return True, res[ans-1]

### 포트폴리오 최적화 목적함수
def op_func(w, idx_info, corr_info, rf):
    excess_return = np.dot(w, idx_info['mean']) - rf
    std = np.dot(np.dot((idx_info['sd'] * w).T, corr_info), idx_info['sd'] * w)
    return - excess_return / std    

### 포트폴리오 구성하기
def make_pf(user_id, srno):
    
    #1. 투자기간, 투자성향, risk-free rate 구하기.
    sql = """
    SELECT USER_ID, SRNO, PERIOD, CLASS, START_DATE, END_DATE, 3M, 6M, 1Y
         ,(SELECT AVG(CLOSE) FROM TB_STK_PRICE 
           WHERE TICKER = 'KR1YT' 
             AND K_DATE BETWEEN REQ.START_DATE AND REQ.END_DATE) AS RF_RATE
    FROM
        (
            SELECT A.USER_ID, A.SRNO, A.PERIOD, A.CLASS, 
                   CASE WHEN B.PERIOD = '3M' THEN B.3M
                        WHEN B.PERIOD = '6M' THEN B.6M
                        WHEN B.PERIOD = '1Y' THEN B.1Y
                        ELSE B.1Y END AS START_DATE, B.END_DATE, B.3M, B.6M, B.1Y
            FROM TB_SURV A,
                (
                    SELECT  USER_ID, SRNO
                          , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 3 MONTH) AS 3M
                          , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 6 MONTH) AS 6M
                          , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 1 YEAR ) AS 1Y
                          , DATE( LEAST( (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE))
                                 ,(SELECT MAX(SURV_DATE) FROM TB_ETF_STAT) ) 
                                 ) AS END_DATE
                          , PERIOD, CLASS
                    FROM TB_SURV
                    WHERE USER_ID = %s
                      AND SRNO = %s
                ) B
            WHERE A.USER_ID = B.USER_ID
              AND A.SRNO = B.SRNO
        ) REQ
    """ %(user_id, srno)
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    res = cur.fetchone()
    print(res)
    
    iv_period, r_class, start_date, end_date, _3m, _6m, _1y, rf = res[2:]
    rf = float(rf)
    
    #2. 불러온 투자기간, 투자성향에 따라 투자할 ETF 종목 선정
    sql = """
    SELECT    A.TICKER
            , A.MEAN * B.MULTIPLE      AS ANNUALIZED_MEAN
            , A.SD * SQRT(B.MULTIPLE)  AS ANNUALIZED_SD
            , A.SR * SQRT(B.MULTIPLE)  AS ANNUALIZED_SR
            , B.MULTIPLE
            
    FROM tb_etf_stat A,
       (
          select TICKER, PERIOD, COUNT(*) AS CNT,
                    CASE WHEN PERIOD = '3M' THEN 63
                         WHEN PERIOD = '6M' THEN 126
                         WHEN PERIOD = '1Y' THEN 252
                         ELSE 252 END AS MULTIPLE
          FROM tb_etf_stat A
          WHERE PERIOD = '%s'
          AND CLASS = '%s'
            AND SURV_DATE BETWEEN DATE_SUB(DATE(NOW()), INTERVAL 1 YEAR) AND '%s'
          GROUP BY TICKER, PERIOD
          ORDER BY CNT DESC 
          LIMIT 10
       ) B
    WHERE A.TICKER = B.TICKER 
    AND A.PERIOD = B.PERIOD
    AND A.SURV_DATE = '%s'
    ORDER BY SR DESC
    LIMIT 5
    ;
    """ %  (iv_period, r_class, end_date, end_date)
    print('\n[SQL-log] '+sql+"\n")
    cur.execute(sql)
    pf = cur.fetchall()
    pf = pd.DataFrame(pf, columns=['ticker','sd','mean','sr','multi'])
    pf['sd'] = pf['sd'].map(float)
    pf['mean'] = pf['mean'].map(float)
    
    print(pf)
    
    #3. 투자할 ETF 종목에 대해서 과거 투자기간에 대해서 최적의 S.R를 산출하도록 최적화 MVO.
    #3-1. ETF 종목들에 대해 과거 투자기간 동안의 Corr 계산.
    price_li = []
    for tk in pf.ticker:
        
        sql = """
        SELECT TICKER, K_DATE, PCT_CHANGE
        FROM TB_ETF_PRICE
        WHERE TICKER = %s
        AND K_DATE BETWEEN '%s' AND '%s'
        """% (tk, start_date, end_date)
        
        print('\n[SQL-log] '+sql+"\n")
        cur.execute(sql)
        tk_price = cur.fetchall()
        
        tk_price = pd.Series(list(map(lambda x:float(x[2]), tk_price)), name=tk)
        price_li.append(tk_price)
    
    corr = pd.DataFrame(price_li).T.corr()
    
    bnds = tuple([(0.05, 0.5)] * len(pf))
    cons = [{'type':'eq', 'fun': lambda x: sum(x) - 1 }]
    sol = optm.minimize(op_func, x0=[ 1/len(pf) ] * len(pf), bounds=bnds, constraints=cons, args=(pf,corr,rf))
    
    data = pd.DataFrame(np.array([list(pf.ticker), list(map(lambda x:round(x,3),sol.x))]).T, columns=['ticker','weight'])
    data['user_id'] = user_id
    data['srno'] = srno
    data['num'] = range(len(data))
    data = data[['user_id','srno','num','ticker','weight']]
    
    sql = "INSERT INTO TB_PORT_DETAIL VALUES( %s, %s, %s, %s, %s)"
    val = np.array(data).tolist()
    print('\n[SQL-log] '+sql+"\n")
    print(data)
    
    cur.executemany(sql, val)
    stock_db.commit()
    
### 파이 시각화!
def visualize_pie(user_id, srno):
    sql = """
    SELECT B.USER_ID, B.SRNO, D.CLASS, D.DETAIL, B.NUM, B.TICKER, B.WEIGHT, C.TICKER_NAME
    FROM TB_SURV A, TB_PORT_DETAIL B, TB_ETF_INFO C, TB_CLASS D
    WHERE A.USER_ID = B.USER_ID
      AND A.SRNO = B.SRNO
      AND B.TICKER = C.TICKER
      AND A.CLASS = D.CLASS
      AND A.USER_ID = %s
      AND A.SRNO = %s
    ORDER BY B.NUM, B.TICKER, B.WEIGHT
    """ % (user_id, srno)
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    pf = cur.fetchall()
    pf = pd.DataFrame(pf, columns=['user_id', 'srno', 'class', 'c_name','num', 'ticker', 'weight', 't_name'])
    
    #테마설정
    sns.set_style('dark')
    #한글폰트 안깨지도록 하기
    plt.rcParams['font.family'] = 'NanumGothic'
    #폰트 크기 설정
    plt.rcParams['font.size'] = 20
    #시각화
    plt.figure(figsize = (16,10))
    
    font1 = {'color':  'red',
          'weight': 'normal',
          'size': 30}
    plt.text(-1.8, 1.2, "<고객성향 : " + pf['c_name'][0] + ">", fontdict = font1)
    
    plt.pie(pf['weight'], labels = pf['t_name'], autopct='%0.1f%%')
    plt.show()
    
    visualize_chart(user_id, srno)
    
###
def visualize_chart(user_id, srno):
    # 수익률 검증 
    sql = """
    SELECT A.USER_ID, A.SRNO, A.PERIOD, A.CLASS, B.END_DATE, B.1M, B.3M, B.6M, B.1Y
    FROM TB_SURV A,
       (
          SELECT  USER_ID, SRNO
               , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 1 MONTH) AS 1M
                  , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 3 MONTH) AS 3M
               , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 6 MONTH) AS 6M
               , (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE) - INTERVAL 1 YEAR ) AS 1Y
               , DATE( LEAST( (SELECT MAX(K_DATE) FROM TB_ETF_PRICE WHERE K_DATE <= DATE(SURV_DATE))
                                              ,(SELECT MAX(SURV_DATE) FROM TB_ETF_STAT) ) 
                    ) AS END_DATE
               , PERIOD, CLASS
          FROM TB_SURV
          WHERE USER_ID = %s
            AND SRNO = %s
       ) B
    WHERE A.USER_ID = B.USER_ID
      AND A.SRNO = B.SRNO
    """ % (user_id, srno)
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    res = cur.fetchone()
    end_date, date_1m, date_3m, date_6m, date_1y = res[4:]
    
    # 포트폴리오의 daily 수익률 산출하기.
    sql = """
    SELECT K_DATE, SUM(TK_WEIGHT_RET) + 1 AS DAILY_PF_RET
    FROM (
       SELECT A.TICKER, B.K_DATE, A.WEIGHT * B.PCT_CHANGE AS TK_WEIGHT_RET
       FROM TB_PORT_DETAIL A
          ,TB_ETF_PRICE B
       WHERE USER_ID = %s
       AND SRNO = %s
       AND A.TICKER = B.TICKER
       AND B.K_DATE BETWEEN '%s' AND '%s'
       ) PF
    GROUP BY K_DATE
    ORDER BY K_DATE
    """ % (user_id, srno, date_1y, end_date)
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    pf = cur.fetchall()
    pf = pd.DataFrame(pf, columns=['k_date','ret'])
    pf.ret = pf.ret.map(float)
    pf = pf.set_index('k_date')
    
    #한글폰트 안깨지도록 하기
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'NanumGothic'
    #폰트 크기 설정
    sns.set_style('dark')
    plt.rcParams['font.size'] = 15
    weekFmt = DateFormatter('%Y-%m-%d')
    weeks = WeekdayLocator(interval=2)
    insert__list = [(0, 0, pf[date_1m:].index, pf[date_1m:].cumprod().ret, 'Holding Period : 1 Month'), 
                    (0, 1, pf[date_3m:].index, pf[date_3m:].cumprod().ret, 'Holding Period : 3 Month'),
                    (1, 0, pf[date_6m:].index, pf[date_6m:].cumprod().ret, 'Holding Period : 6 Month'), 
                    (1, 1, pf[date_1y:].index, pf[date_1y:].cumprod().ret, 'Holding Period : 1 Year')]
    
    fig, ax = plt.subplots(2, 2, figsize=(20, 20))
    
    for i in insert__list :
        ax[i[0]][i[1]].set_title(i[4])
        ax[i[0]][i[1]].set_xticklabels(labels = i[2], rotation = 45)
        ax[i[0]][i[1]].set_yticklabels(labels = pd.Series(i[3]).map(lambda x : round(x, 2)).sort_values())
        ax[i[0]][i[1]].plot_date(pd.to_datetime(i[2]), i[3],'-')     
        ax[i[0]][i[1]].xaxis.set_major_locator(weeks)   
        ax[i[0]][i[1]].xaxis.set_major_locator(weeks)
        ax[i[0]][i[1]].xaxis.set_major_formatter(weekFmt) 
    
    plt.show()
    
    # bm 가격 불러오기
    # 069500 - 코스피 / 148070 - kosef 국고채 10년
    sql = """
    SELECT TICKER, K_DATE, PCT_CHANGE + 1
    FROM TB_ETF_PRICE
    WHERE TICKER IN ( '%s', '%s' )
    AND K_DATE BETWEEN '%s' AND '%s'
    """ %('069500', '148070', date_1y, end_date)
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    
    bm = cur.fetchall()
    bm = pd.DataFrame(bm, columns=['ticker','k_date','ret'])
    bm.ret = bm.ret.map(float)
    
    bm_li = []
    for tk in bm.ticker.unique():
        bm_li.append( bm[bm.ticker == tk].set_index('k_date') )
        
    sql = """
    SELECT TICKER_NAME
    FROM TB_ETF_INFO
    WHERE TICKER IN %s
    """ % str(tuple(bm.ticker.unique()))
    
    print('\n[SQL-log] '+sql+"\n")   
    cur.execute(sql)
    
    tk_name = cur.fetchall()
    
    label_li = ['Optimalized_PF'] + list(map(lambda x:x[0], tk_name))
        
    std_ret_li = []
    for std_date in [date_1m, date_3m, date_6m, date_1y]:
        tmp = pd.concat([pf[std_date:].cumprod() ] + [ x[std_date:].ret.cumprod() for x in bm_li ], axis=1)
        tmp.columns = label_li
        std_ret_li.append(tmp)
    
    #한글폰트 안깨지도록 하기
    plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['font.size'] = 15
    
    #폰트 크기 설정
    sns.set_style('dark')
    
    weekFmt = DateFormatter('%Y-%m-%d')
    weeks = WeekdayLocator(interval=2)
    insert__list = [(0, 0, std_ret_li[0].index, std_ret_li[0], 'Holding Period : 1 Month'),
                    (0, 1, std_ret_li[1].index, std_ret_li[1], 'Holding Period : 3 Month'),
                    (1, 0, std_ret_li[2].index, std_ret_li[2], 'Holding Period : 6 Month'),
                    (1, 1, std_ret_li[3].index, std_ret_li[3], 'Holding Period : 1 Year')]
    
    fig, ax = plt.subplots(2, 2, figsize=(20, 20))
    
    for i in insert__list :
        ax[i[0]][i[1]].set_title(i[4])
        ax[i[0]][i[1]].set_xticklabels(labels = i[2], rotation = 45)
        ax[i[0]][i[1]].set_yticklabels(labels = pd.Series(i[3]['Optimalized_PF']).map(lambda x : round(x, 2)).sort_values())
        ax[i[0]][i[1]].plot_date(pd.to_datetime(i[2]), i[3],'-')     
        ax[i[0]][i[1]].xaxis.set_major_locator(weeks)
        ax[i[0]][i[1]].xaxis.set_major_formatter(weekFmt) 
        
    plt.legend(['Optimized_port', 'KODEX_200', 'KOSEF_Bond_10Y'], loc = 'upper left')
    plt.show()
###
def start():
    user_id = -1
    srno = -1
    sel = 0
    
    ret = False
    while(ret == False):
        try:
            print('< Init.Menu >')
            print(' 1. login')
            print(' 2. register')
            print(' 3. exit')
            print('- 메뉴를 선택해주세요.')
    
            sel = int(input())
            
            if sel == 1: 
                ret, user_id = do_login()
                
            elif sel == 2: 
                ret, user_id = do_register()
            elif sel == 3:
                ret = True
                print('<Exit> - 종료') 
                return
            else:
                print('잘못된 값을 입력했습니다.')
        except:
            print('잘못된 값을 입력했습니다.')
    
    ret = False
    while(ret == False):
        try:
            print('< Menu >')
            print(' 1. survey')
            print(' 2. show my portfolio')
            print(' 3. exit')
            print('- 메뉴를 선택해주세요.')
    
            sel = int(input())
            
            if sel == 1: 
                user_id, srno = do_survey(user_id)
                make_pf(user_id, srno)
                visualize_pie(user_id, srno)
            elif sel == 2: 
                ret, res = load_history(user_id)
                if ret == True:
                    #user_id, srno, surv_date, period, r_class, r_name = res
                    user_id, srno = res[:2]
                    visualize_pie(user_id, srno)
                    ret = False
            elif sel == 3:
                ret = True
                print('<Exit> - 종료')
                return
            else:
                print('잘못된 값을 입력했습니다.')
        except:
            print('잘못된 값을 입력했습니다.')
    

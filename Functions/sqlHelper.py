import sqlite3
''' Initialize SQL'''
conn = sqlite3.connect('./windbotDB.db')
cur = conn.cursor()

arcdb = sqlite3.connect('./arcsong.db')
arcur = arcdb.cursor()

def getid():
    return time.strftime("%Y%m%d%H%M%S")

def output(msg,logtype = 'SYSTEM',mode = 'DEFAULT',background = 'DEFAULT'):
    # print('got output')
    LogColor = {
        'SYSTEM': '034',
        'ERROR': '037',
        'GROUPCHAT': '036',
        'DM' : '033',
        'HEART_BEAT': '035',
        'PAT': '037',
        'SEND': '032',
        'CALL' : '031',
        'WARNING': '031',
        'CREATE_LINK':'032',
        'STOP_LINK':'031'
    }
    LogMode = {
        'DEFAULT': '0',
        'HIGHLIGHT': '1',
        'UNDERLINE': '4'
    }
    LogBG = {
        'DEFAULT': '',
        'RED' : ';41',
        'YELLOW' : ';43',
        'BLUE' : ';44',
        'WHITE' : ';47',
        'GREEN' : ';42',
        'MINT' : ';46'
    }
    color = LogColor.get(logtype)
    mode = LogMode.get(mode)
    bg = LogBG.get(background)


    now=time.strftime("%Y-%m-%d %X")
    print(f"[{now} \033[{mode};{color}{bg}m{logtype}\033[0m] {msg}")

    # Write Error Logs on to Local File
    if logtype == 'ERROR':
        error_log_file = open('ErrorLog.txt','a')
        error_log_file.write(f"[{now} {logtype}] {msg}\n")
        error_log_file.close()

    # print("["+f"{color}[1;35m{LogType}{color}[0m"+"]"+' Success')
    # print(f'[{now}]:{msg}')

def sql_insert(db,dbcur,table,rows,values):
    '''
    Pre-Process
    '''
    # table = f'r{table[:-9]}'
    test_row = rows[-1]
    test_value = values[-1]
    rows = str(rows)[1:-1].replace('\'','')
    values = str(values)[1:-1]
    '''
    Check if line exsists
    '''
    if isinstance(test_value,str):
        check_txt = f"SELECT 1 FROM {table} WHERE {test_row}='{test_value}'"
    else:
        check_txt = f"SELECT 1 FROM {table} WHERE {test_row}={test_value}"
    # output(check_txt)
    dbcur.execute(check_txt)
    result = dbcur.fetchone()
    # output(result,mode = 'HIGHLIGHT')
    '''
    Value Exists or not
    '''
    if result:
        # output('Skipping This Insert Because Column Exists','WARNING')
        return
    else:
        insert_txt = f"INSERT INTO {table}({rows}) VALUES({values})"
        # print(insert_txt)
        db.execute(insert_txt)
        db.commit()

def sql_update(db,table,col,value,condition = None):
    # table = f'r{table[:-9]}'
    # col = str(col).replace('\'','')

    if isinstance(value,str):
        if condition:
            update_txt = f"UPDATE {table} SET {col} = '{value}' WHERE {condition}"
        else:
            update_txt = f"UPDATE {table} SET {col} = '{value}'"
    else:
        if condition:
            update_txt = f"UPDATE {table} SET {col} = {value} WHERE {condition}"
        else:
            update_txt = f"UPDATE {table} SET {col} = {value}"

    # output(update_txt,mode = 'HIGHLIGHT')
    db.execute(update_txt)
    db.commit()

def sql_fetch(dbcur,table,cols = ['*'],condition = None):
    cols = str(cols)[1:-1].replace('\'','')
    # cols = str(cols)[1:-1]

    if condition:
        fetch_txt = f"SELECT {cols} FROM {table} WHERE {condition}"
    else:
        fetch_txt = f"SELECT {cols} FROM {table}"
    # output(fetch_txt,mode = 'HIGHLIGHT')
    dbcur.execute(fetch_txt)
    result = dbcur.fetchall()
    return [i for i in result]

def sql_match(db,dbcur,table,cols = ['*'],conditionCol = None,keyword = None):
    if not keyword:
        return ['-1']
    elif not conditionCol:
        return ['-1']

    dbcur.execute('DROP TABLE IF EXISTS fuzzysearch')

    fetchcols = cols
    fetchcols.append(conditionCol)
    origin_data = sql_fetch(dbcur,table,fetchcols)
    # output(origin_data)

    cols = str(cols)[1:-1].replace('\'','')
    fetchcols_str = str(fetchcols)[1:-1].replace('\'','')

    dbcur.execute(f'create virtual table fuzzysearch using fts5({fetchcols_str}, tokenize="porter unicode61");')

    for row in origin_data:
        # output(str(row)[1:-1])
        dbcur.execute(f'insert into fuzzysearch ({fetchcols_str}) values ({str(row)[1:-1]});')

    db.commit()

    if isinstance(keyword,str):
        match_txt = f"SELECT {cols} FROM fuzzysearch WHERE {conditionCol} MATCH '{keyword}*'"
    else:
        match_txt = f"SELECT {cols} FROM fuzzysearch WHERE {conditionCol} MATCH {keyword}*"

    # output(match_txt)
    result = dbcur.execute(match_txt).fetchall()
    # output(result)

    dbcur.execute('DROP TABLE IF EXISTS fuzzysearch')
    db.commit()

    return [i for i in result]

def sql_destroy(db,table):
    destroy_txt = f"DROP TABLE {table}"
    db.execute(destroy_txt)
    db.commit()

def sql_delete(db,table,condition = None):
    if not condition:
        output('Did not specify which delete condition.','WARNING',background = "WHITE")
        return ['-1']

    delete_txt = f"DELETE FROM {table} WHERE {condition}"
    db.execute(delete_txt)
    db.commit()

def sql_initialize_link(linkroomid,allselect):
    initialize_link = f'''CREATE TABLE IF NOT EXISTS {linkroomid}
            (wxid TEXT,
            arcID NUMBER,
            allselect NUMBER NOT NULL DEFAULT {allselect},
            songselect NUMBER NOT NULL DEFAULT 0,
            song TEXT NOT NULL DEFAULT -1,
            chartLevel NUMBER NOT NULL DEFAULT -1,
            songStarted NUMBER NOT NULL DEFAULT -1,
            isOwner NUMBER NOT NULL DEFAULT 0);'''
    # output(initialize_link)
    conn.execute(initialize_link)
    conn.commit()
    output(f'Created Link Play Room of ID {linkroomid}','CREATE_LINK',background = 'WHITE')
# WindBot SQL Helper Functions
# May 2024

# Third Party Imports
import sqlite3

class SQLHelper(object):
    """SQL Related Functions"""
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
         return sqlite3.connect(self.db_path)
    
    def cursor(self, connection) -> sqlite3.Cursor:
         return connection.cursor()

    # Execute a SQL Command. Returns False if Exception Occurred
    def execute(self, sql_cmd) -> Bool:
        try:
            conn = self.connect()
            conn.execute(sql_cmd)
            conn.close()
            return True
        except Exception as e:
            return False

    # SQL Insertion Wrapper. Returns False if aborted insertion, True elsewise
    def insert(self, table, rows, values, id_row, id_value) -> Bool:
        # str_rows = str(rows)[1:-1].replace('\'','')

        # String-ify rows and values
        str_rows = ", ".join(rows).replace('\'', '')
        str_values = ", ".join(values)
        
        # id_row Check Duplicates
        if isinstance(id_value, str):
            check_dup_cmd = f"SELECT 1 FROM {table} WHERE {id_row}='{id_value}'"
        else:
            check_dup_cmd = f"SELECT 1 FROM {table} WHERE {id_row}={id_value}"
        
        conn = self.connect()
        cur = self.cursor(conn)

        cur.execute(check_dup_cmd)
        result = cur.fetchone()

        # Duplicate. Abort the insertion
        if result != None:
            return False

        # Insert Row
		insert_cmd = f"INSERT INTO {table}({rows}) VALUES({values})"
        
        # Execute & Commit
        conn.execute(insert_cmd)
        conn.commit()
        cur.close()
        conn.close()
        return True
    
    # SQL Update Wrapper. 
    def update(self, table, col, value, condition = None) -> None:
        if isinstance(value,str):
            update_cmd = f"UPDATE {table} SET {col} = '{value}'"
        else:
            update_cmd = f"UPDATE {table} SET {col} = {value}"

        if condition:
            update_cmd += f" WHERE {condition}"

        conn = self.connect()
        conn.execute(update_cmd)
        conn.commit()
        conn.close()

    # SQL Select Wrapper.
    def fetch(self, table, cols = None, condition = None, cur = None): -> List:
        cols = ['*'] if cols == None else cols

        str_cols = ", ".join(cols).replace('\'', '')

        fetch_cmd = f"SELECT {cols} FROM {table}"
        if condition:
            fetch_cmd += f" WHERE {condition}"

        if cur == None:
            conn = self.connect()
            cur = self.cursor(conn)

            cur.execute(fetch_cmd)
            result = cur.fetchall()

            cur.close()
            conn.close()
        # Given a Cursor
        else:
            cur.execute(fetch_cmd)
            result = cur.fetchall()

        return [i for i in result]

    # SQL Fuzzy Match.
    def match(self, table, cols = None, condition_col, keyword) -> List:
        cols = ['*'] if cols == None else cols

        conn = self.connect()
        source = conn
        tmp_db = sqlite3.connect(":memory:")
        source.backup(tmp_db)
        tmp_cur = tmp_db.cursor()

        tmp_cur.execute('DROP TABLE IF EXISTS fuzzysearch')

        fetchcols = cols
        fetchcols.append(condition_col)
        origin_data = self.fetch(table, fetchcols, cur = tmp_cur)

        str_cols = str(cols)[1:-1].replace('\'','')

        str_fcols = str(fetchcols)[1:-1].replace('\'','')

        tmp_cur.execute(f'create virtual table fuzzysearch using fts5({str_fcols}, tokenize="porter unicode61");')

        for row in origin_data:
            tmp_cur.execute(f'insert into fuzzysearch ({str_fcols}) values ({str(row)[1:-1]});')

        tmp_db.commit()

        if isinstance(keyword,str):
            match_txt = f"SELECT {str_cols} FROM fuzzysearch WHERE {condition_col} MATCH '{keyword}*'"
        else:
            match_txt = f"SELECT {str_cols} FROM fuzzysearch WHERE {condition_col} MATCH {keyword}*"

        result = tmp_cur.execute(match_txt).fetchall()

        tmp_cur.execute('DROP TABLE IF EXISTS fuzzysearch')
        tmp_db.commit()
        tmp_db.close()

        return [i for i in result]

    # SQL Destroy Wrapper.
    def destroy(self, table) -> None:
        conn = self.connect()

        destroy_cmd = f"DROP TABLE {table}"

        conn.execute(destroy_cmd)
        conn.commit()
        conn.close()

    # SQL Delete Wrapper.
    def delete(self, table, condition) -> None:
        conn = self.connect()

        delete_cmd = f"DELETE FROM {table} WHERE {condition}"

        conn.execute(delete_cmd)
        conn.commit()
        conn.close()

    # WB DB Structure: Initialize the User Table.
    def _usr_table_init(self) -> None:
        conn = self.connect()
        init_usr_cmd = f'''CREATE TABLE IF NOT EXISTS Users
                (wxid TEXT,
                wxcode TEXT,
                realUsrName TEXT,
                patTimes NUMBER NOT NULL DEFAULT 0,
                patAction TEXT NOT NULL DEFAULT -1,
                arcID NUMBER NOT NULL DEFAULT -1,
                pjskID NUMBER NOT NULL DEFAULT -1,
                maiID TEXT NOT NULL DEFAULT -1,
                qqID NUMBER NOT NULL DEFAULT -1,
                powerLevel NUMBER NULL DEFAULT 0,
                banned BOOL NOT NULL DEFAULT 0);'''
        conn.execute(init_usr_cmd)
        conn.commit()
        conn.close()

    # WB DB Structure: Initialize the Groupchats (Group Overview) Table.
    def _group_overview_table_init(self) -> None:
        conn = self.connect()
        init_gc_overview_cmd = f'''CREATE TABLE IF NOT EXISTS Groupchats
                (roomid TEXT,
                groupname TEXT
                announce BOOL NOT NULL DEFAULT 0,
                rssPush BOOL NOT NULL DEFAULT 1);'''
        conn.execute(init_gc_overview_cmd)
        conn.commit()
        conn.close()
        
    # WB DB Structure: Initialize a Groupchat Data Table.
    def _gc_table_init(self, roomid) -> None:
        conn = self.connect()
        init_gc_cmd = f'''CREATE TABLE IF NOT EXISTS {roomid}
                (wxid TEXT,
                groupUsrName TEXT);'''
        conn.execute(init_gc_cmd)
        conn.commit()
        conn.close()


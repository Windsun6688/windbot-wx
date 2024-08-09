# WindBot SQL Helper Functions
# May 2024

# Standard Lib Imports
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
    def execute(self, sql_cmd) -> bool:
        try:
            conn = self.connect()
            conn.execute(sql_cmd)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False

    # SQL Insertion Wrapper. Returns False if aborted insertion, True elsewise
    def insert(self, table, rows, values, id_row, id_value) -> bool:
        # Connect to DB
        conn = self.connect()
        cur = self.cursor(conn)

        # Check Duplicate by id_row & id_value 
        cur.execute(f"SELECT 1 FROM {table} WHERE {id_row} = ?", [id_value])
        result = cur.fetchone()

        # Duplicate. Abort the insertion
        if result != None:
            return False

        # Insert Row
        rows_str = ", ".join(rows)
        placehldr = ", ".join(["?"] * len(values))
        insert_cmd = f"INSERT INTO {table} ({rows_str}) VALUES ({placehldr})"
        conn.executemany(insert_cmd, [values])

        # Commit & Close
        conn.commit()
        cur.close()
        conn.close()
        return True
    
    # SQL Update Wrapper. 
    def update(self, table, col, val, condi_row, condi_val) -> None:
        # Connect to DB
        conn = self.connect()
        cur = self.cursor(conn)

        # Update Row 
        update_cmd = f"UPDATE {table} SET {col} = ? WHERE {condi_row} = ?"
        conn.execute(update_cmd, [val, condi_val])

        # Commit & Close
        conn.commit()
        conn.close()

    # SQL Select Wrapper.
    def fetch(self, table, cols, condi_row, condi_val) -> list:
        # Connect to DB
        conn = self.connect()
        cur = self.cursor(conn)

        # Fetch Rows
        cols_str = ", ".join(cols)
        fetch_cmd = f"SELECT {cols_str} FROM {table} WHERE {condi_row} = ?"

        cur.execute(fetch_cmd, [condi_val])
        result = cur.fetchall()

        # Close
        cur.close()
        conn.close()

        return [i for i in result]

    # SQL Fuzzy Match. *DEPRECIATED*
    def match(self, table, condition_col, keyword, col = None) -> list:
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
        # Connect to DB
        conn = self.connect()
        cur = self.cursor(conn)

        # ━━━━[]
        #     / \＞
        #     ＜ ＼
        destroy_cmd = f"DROP TABLE {table}"
        cur.execute(destroy_cmd)

        # Commit & Close
        conn.commit()
        cur.close()
        conn.close()

    # SQL Delete Wrapper.
    def delete(self, table, condi_row, condi_val) -> None:
        # Connect to DB
        conn = self.connect()
        cur = self.cursor(conn)

        # Delete Records
        delete_cmd = f"DELETE FROM {table} WHERE {condi_row} = ?"
        cur.execute(delete_cmd, [condi_val])

        # Commit & Close
        conn.commit()
        cur.close()
        conn.close()

    # WB DB Structure: Initialize the User Table.
    def _usr_table_init(self) -> None:
        conn = self.connect()

        init_usr_cmd = '''CREATE TABLE IF NOT EXISTS Users
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

        init_gc_overview_cmd = '''CREATE TABLE IF NOT EXISTS Groupchats
                (roomid TEXT,
                groupname TEXT,
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

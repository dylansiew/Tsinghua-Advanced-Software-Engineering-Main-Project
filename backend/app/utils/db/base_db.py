import os
from pathlib import Path

from crate import client
from dotenv import load_dotenv

load_dotenv()

class BaseDB:
    def __init__(self, query_dir: str, table_names: list[str]):
        self.conn = client.connect(
            os.getenv("DB_URL"),
            username=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            verify_ssl_cert=os.getenv("DB_VERIFY_SSL_CERT"))
        self.cursor = self.conn.cursor()
        
        self.query_dir = Path(__file__).parent / "query" / query_dir
        if not os.path.exists(self.query_dir):
            print(f"Creating query directory {self.query_dir}")
            os.makedirs(self.query_dir, exist_ok=True)
        
        self.table_names = table_names
        # self._run_connection_test()
        # self.create_tables()

    def _format_query_path(self, query_name: str):
        file_path = os.path.join(self.query_dir, f"{query_name}.sql")
        if not os.path.exists(file_path):
            print(f"Query file {file_path} does not exist")
            raise FileNotFoundError(f"Query file {file_path} does not exist")
        return file_path
    
    def with_refresh(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.run_refresh()
            return result
        return wrapper

    
    def run_refresh(self):
        for table_name in self.table_names:
            self.cursor.execute(f"REFRESH TABLE {table_name}") 
            self.conn.commit()
        
    def _run_connection_test(self):
        def create_test_table():
            self.cursor.execute("CREATE TABLE IF NOT EXISTS test (id INT PRIMARY KEY)")
            self.conn.commit()
        
        def create_insert_test():
            self.cursor.execute("INSERT INTO test (id) VALUES (1)")
            self.conn.commit()
            self.cursor.execute("REFRESH TABLE test") 
            self.conn.commit()
        
        def select_test():
            self.cursor.execute("SELECT * FROM test")
            res = self.cursor.fetchone()
            assert res[0] == 1
        
        def drop_test_table():  
            self.cursor.execute("DROP TABLE IF EXISTS test")
            self.conn.commit()
        
        try:
            drop_test_table()
            create_test_table()
            create_insert_test()
            select_test()
            drop_test_table()
        except Exception as e:
            print(f"Database connection test failed with error: {str(e)}")
            raise
    
    def create_tables(self):
        print("Creating tables...")
        tables_to_create = os.listdir(Path(__file__).parent / "query" / "create")
        for table in tables_to_create:
            self.cursor.execute(open(f"app/utils/db/query/create/{table}", "r").read())
            self.conn.commit()
    
    # def insert_message(self, conversation_id: str, message_role: str, message_content: str):
    #     self.cursor.execute(open("app/utils/db/query/insert/message.sql", "r").read(), (conversation_id, message_role, message_content))
    #     self.conn.commit()
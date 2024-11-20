import _sqlite3

class SQL:
    def __init__(self):
        self._conn = _sqlite3.connect("../Temperature_sql_database.db")
        self._cur = self._conn.cursor()
        
    def add_login(self, username, password):
    # Création de la table users si elle n'existe pas
        self.cur.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        
        query = "INSERT INTO users (username, password) VALUES (?, ?)"
        try:
            self._cur.execute(query, (username, password))
            self._conn.commit()
            print("User added with succes.")
        except _sqlite3.IntegrityError:
            print("The username allready exist.")
        #finally:
        #    self._conn.close()
        
        
    def login(self, username, password):
        # Verify the login
        self._cur.execute('''
            SELECT * FROM users WHERE username = ? AND password = ?
        ''', (username, password))

        result = self._cur.fetchone()

        if result:
            return True
        else:
            return False
    
    def insert_data(self, temperature, output, target, time):
        try:
            query = "INSERT INTO airHeater (temperature, output, target, time) VALUES (?, ?, ?, ?);"
            self._cur.execute(query, (temperature, output, target, time))
            self._conn.commit()
        except _sqlite3.OperationalError as e:
            print("Error SQL : ", e)
        
        
    def create_table(self, tableName="airHeater"):
        try:
            res = self._cur.execute("CREATE TABLE " + tableName + " ("
                "number INTEGER PRIMARY KEY AUTOINCREMENT,"
                "temperature REAL,"
                "output REAL,"
                "target REAL,"
                "time REAL"
                ");")
        except Exception as e:
            print(f"Error while creating the table : {e}")
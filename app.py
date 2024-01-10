from flask import Flask, render_template, request, send_file
from faker import Faker
from MongoDB_views import mongo_db
from MySQL_views import mysql_db


# Initialize the Faker instance
fake = Faker()


# Initialize the Flask instance
app = Flask(__name__)

app.register_blueprint(mongo_db)
app.register_blueprint(mysql_db)

@app.route('/' , methods = ['GET' , 'POST'])
def db_choice() :

    if request.method == 'POST' :

        db_name = request.form['DBchoice']
        print(db_name)
        
        if db_name == "mongodb" :
            
            return render_template('Mongo/index.html')          
        
        if db_name == "mysql" :
            return render_template('Mysql/index.html')


    return render_template('index.html')

if __name__ == '__main__':
    
    
    app.run(debug=True)

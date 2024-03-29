from flask import Flask, render_template, request, redirect, url_for, send_file, Blueprint
import psycopg2
from faker import Faker
import random
from Postgres_functions import create_table                      # def create_table(column_detail, table_name)
from Postgres_functions import generate_fake_data                # def generate_fake_data(column_name, data_type):
from Postgres_functions import generagte_insert_query            # def generate_schema_sql(db_name)
from Postgres_functions import generate_schema_sql
from config import pdb_config

# Initialize the Faker instance
fake = Faker()

# Blueprint
postgres_db = Blueprint('postgres_db', __name__)

# this function will be triggered by index.html
@postgres_db.route('/create_tables_postgres/', methods=['POST'])
def create_tables():
    global db_name 
    db_name  = request.form['dbName']
    num_tables = int(request.form['numTables'])
    return render_template('Postgres/table.html', db_name=db_name, num_tables=num_tables)



@postgres_db.route('/submit_table_details_postgres/<db_name>/<int:num_tables>/', methods=['POST'])
def table_details(db_name, num_tables):

    table_name_list = request.form.getlist('tableName')
    column_details_list = request.form.getlist('columnDetails')

    messages = []

    connection = psycopg2.connect(**pdb_config)
    # Set autocommit mode to True
    connection.autocommit = True
    cursor = connection.cursor()

    # Check if the database already exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()

    # Create database if not exists
    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
    
    # Close the cursor and connection to commit the database creation outside of the transaction
    cursor.close()
    connection.close()

     # Reset autocommit mode to False
    # connection.autocommit = False

    # Defining new database configuration
    new_db_config = {
        'host': pdb_config['host'],
        'user': pdb_config['user'],
        'password': pdb_config['password'],
        'dbname': db_name,
        'port': pdb_config['port']
    }

    # Reconnect to the newly created database
    connection = psycopg2.connect(**new_db_config)
    cursor = connection.cursor()

    # Iterate through the provided table names and column details
    num = 1
    for table_name, column_details in zip(table_name_list, column_details_list):
        create_query = create_table(column_details, table_name)
        
        try:

            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '{table_name}' ")
            existing_table = cursor.fetchone()

            if existing_table:
                existing_table = existing_table[0]
                messages.append( (f'Table {num}', table_name, 'Table already exists.') )
                num += 1

            else:
                
                # Execute the create table query
                cursor.execute(create_query)
                connection.commit()
                messages.append( (f'Table {num}', table_name, 'Table created successfully') )
                num += 1

                # 
                # Close the cursor and connection to commit the database creation outside of the transaction
                cursor.close()
                connection.close()

                # Reset autocommit mode to False
                # connection.autocommit = False

                # Reconnect to the newly created database
                connection = psycopg2.connect(**new_db_config)
                cursor = connection.cursor()
                # 


                try:
                    for entry in range(50):
                        insert_query = generagte_insert_query(table_name, column_details, db_name, **new_db_config)
                        cursor.execute(insert_query)
                        connection.commit()

                except psycopg2.Error as err:
                    messages.append( (f'Table Name : ', f'{table_name} insertion error', err) )


        except psycopg2.Error as err:
            # Rollback the transaction on exception
            connection.rollback()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            messages.append( (f'Table {num}', f'{table_name} creation error', err) )
            num += 1

    cursor.close()
    connection.close()

    total = 0
    for message in messages:
        if message[2]=='Table created successfully' or message[2]=='Table already exists.':
            total += 1

    return render_template('Postgres/output.html', messages=messages, total= total, num_tables=num_tables, db_name=db_name )


# Route to download PostgreSQL schema
@postgres_db.route("/download_schema_postgres/<db_name>", methods=['GET', 'POST'])
def download_schema(db_name):

    # Define your MySQL database configuration
    new_db_config = {
        'host': pdb_config['host'],
        'user': pdb_config['user'],
        'password': pdb_config['password'],
        'dbname': db_name,
        'port': pdb_config['port']
    }


    if request.method == 'POST':
        schema_sql = generate_schema_sql(db_name, **new_db_config)

        # Save the SQL to a file
        file_path = f"{db_name}_schema.sql"
        with open(file_path, 'w') as file:
            file.write(schema_sql)

        # Provide the file for download
        return send_file(file_path, as_attachment=True)

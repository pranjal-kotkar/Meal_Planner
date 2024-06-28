from flask import Flask, render_template,request, redirect, url_for, session
#Flask for- flask module
#render_template for- generating output based on Jinja2 
#request for- communication between client and server
from flask_mysqldb import MySQL,MySQLdb
from datetime import datetime
# to communicate with MySQL db
import re


app = Flask(__name__)
app.secret_key = 'PSI515356'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Swarali@#123'
app.config['MYSQL_DB'] = 's'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('login.html')  
         
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        height = request.form['height']
        weight = request.form['weight']
        gender = request.form['sex']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            l=0
            cursor.execute(
                'INSERT INTO user (username, email, password,age,height,weight,gender,expectedCal) VALUES (%s, %s, %s,%s,%s,%s,%s,%s)',
                (userName, email, password,age,height,weight,gender,l))
            mysql.connection.commit()
            message = 'You have successfully registered! Please login.'
            return redirect(url_for('login'))
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('signup.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM user WHERE email = %s AND password = %s',
            (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect(url_for('meal_planner'))
        else:
            message = 'Please enter correct email / password!'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)

'''
#not required now
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'loggedin' in session:
        if request.method == 'POST':
            age = request.form['age']
            height = request.form['height']
            weight = request.form['weight']
            gender = request.form['sex']
            # Update the user's information in the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'UPDATE user SET age = %s, height = %s, weight = %s, gender = %s WHERE userid = %s',
                (age, height, weight, gender, session.get('userid'))
            )
            mysql.connection.commit()
            return redirect(url_for('login'))
    return render_template('dashboard.html')
'''
    
@app.route('/calculate_calories', methods=['GET'])
def calculate_calories():
    if request.method == 'GET':
        userID = session.get('userid')
        date_str = request.args.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        print(type(date_obj))
        cur = mysql.connection.cursor()
        print("jjjj")
        date_str_mysql = date_obj.strftime('%Y-%m-%d')
        try:
            cur.callproc('CalculateExpectedCal', [userID])
            
            # Call the procedure to update consumed calories
            date_str_mysql = date_obj.strftime('%Y-%m-%d')
            cur.callproc('UpUserConsumedCal', [userID,date_str_mysql])
            print(date_str_mysql)
            # Call the function to calculate expected calories
            cur.execute("select CalculateAndUpdateDiffCalories(%s)", (userID,))
            
            # Call the function to calculate and update difference in calories
        
            # Call the function to determine if the user's calorie consumption is safe or not
            cur.execute("select UpdateSafeOrNot(%s)", (userID,))

            cur.execute("SELECT expectedCal FROM user WHERE UserID = %s", (userID,))
            expectedCal = cur.fetchone()
            # Fetch the updated values
            cur.execute("SELECT consumedCal,diffCal FROM usercal WHERE UserID = %s", (userID,))
            cals= cur.fetchone()
            
            cur.execute("SELECT safeorNot FROM usercal WHERE UserID = %s", (userID,))
            safeOrNot = cur.fetchone()
            print("tttt")
            print("Consumed Calories:", cals)
            print("Expected Calories:", expectedCal)
           
            print("Safe or Not:", safeOrNot)
            cur.close()
            mysql.connection.commit()
            return render_template('result.html', expectedCal=expectedCal,cals=cals,safeOrNot=safeOrNot)
        except Exception as e:
            print(e)
            return render_template('result.html', consumedCal=0, expectedCal=0, diffCal=0,safeOrNot="None")
    return redirect(url_for('meal_planner'))


@app.route('/meal_planner', methods=['GET', 'POST'])
def meal_planner():
    if request.method == 'POST':
        note = request.form.get('note')
        veg_non = request.form.get('veg/non')
        return redirect(url_for('select_recipes',veg_non=veg_non))
    else:
        return render_template('meal_planner.html')

@app.route('/select_recipes/<veg_non>', methods=['GET', 'POST'])
def select_recipes(veg_non):
    if request.method=='GET':
        if veg_non=='veg':
            VN = 'V'
            searchQueryBf = "SELECT RecipeName,RecipeID from recipe WHERE tag='B' AND  vegNon = %s ORDER BY RecipeName"
            searchQueryLunch = "SELECT RecipeName,RecipeID from recipe WHERE tag='L' AND  vegNon = %s ORDER BY RecipeName"
            searchQueryDinner = "SELECT RecipeName,RecipeID from recipe WHERE tag='D' AND  vegNon = %s ORDER BY RecipeName"
            searchQuerySnack = "SELECT RecipeName,RecipeID from recipe WHERE tag='S' AND  vegNon = %s ORDER BY RecipeName"
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute(searchQueryBf,VN)
            bfRecipes = cur.fetchall()
            print(bfRecipes)
            cur.execute(searchQueryLunch,VN)
            lunchRecipes = cur.fetchall()

            cur.execute(searchQueryDinner,VN)
            dinnerRecipes = cur.fetchall()

            cur.execute(searchQuerySnack,VN)
            snackRecipes = cur.fetchall()
        else:
            searchQueryBf = "SELECT RecipeName,RecipeID from recipe WHERE tag='B' ORDER BY RecipeName"
            searchQueryLunch = "SELECT RecipeName,RecipeID from recipe WHERE tag='L' ORDER BY RecipeName"
            searchQueryDinner = "SELECT RecipeName,RecipeID from recipe WHERE tag='D' ORDER BY RecipeName"
            searchQuerySnack = "SELECT RecipeName,RecipeID from recipe WHERE tag='S' ORDER BY RecipeName"
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
            cur.execute(searchQueryBf)
            bfRecipes = cur.fetchall()
            print(bfRecipes)
            cur.execute(searchQueryLunch)
            lunchRecipes = cur.fetchall()
            print(lunchRecipes)
            cur.execute(searchQueryDinner)
            dinnerRecipes = cur.fetchall()
            

            cur.execute(searchQuerySnack)
            snackRecipes = cur.fetchall()
        
    return render_template('select_recipes.html',bfRecipes=bfRecipes,lunchRecipes=lunchRecipes,dinnerRecipes=dinnerRecipes,snackRecipes=snackRecipes)

@app.route('/submit_schedule',methods=['GET', 'POST'])
def submit_schedule():
    UID = session.get('userid')
    print(UID)
    date = request.form.get('date')
    bfRID = request.form.get('breakfast')
    lRID = request.form.get('lunch')
    dRID = request.form.get('dinner')
    sRID = request.form.get('Snack')
    print("bfRID:", bfRID)
    print("lRID:", lRID)
    print("dRID:", dRID)
    print("sRID:", sRID)

    print("Form data:", request.form)

    a=0
    b=0
    k="N"
    
    searchQueryBf = "INSERT INTO meal(UserID,RecipeID,date,time) VALUES(%s,%s,%s,'B')"
    searchQueryLunch = "INSERT INTO meal(UserID,RecipeID,date,time) VALUES(%s,%s,%s,'L')"
    searchQueryDinner = "INSERT INTO meal(UserID,RecipeID,date,time) VALUES(%s,%s,%s,'D')"
    searchQuerySnack = "INSERT INTO meal(UserID,RecipeID,date,time) VALUES(%s,%s,%s,'S')"
    s="INSERT INTO usercal VALUES(%s,%s,%s,%s,%s)"

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    message = "Schedule added!"
    try:
        cur.execute(searchQueryBf,(UID,bfRID,date))

        cur.execute(searchQueryLunch,(UID,lRID,date))

        cur.execute(searchQueryDinner,(UID,dRID,date))

        cur.execute(searchQuerySnack,(UID,sRID,date))

        cur.execute(s,(UID,a,b,k,date))
        print("Inserted into meal table")
        cur.close()
        mysql.connection.commit()
    except Exception as e:
        print(e)
        message = "This schedule already exists"
       

    return render_template('index1.html',message=message , date=date) 

@app.route('/display_schedules',methods=['GET','POST'])
def display_schedules():
    UID = session.get('userid')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    join_query = "SELECT Date,Time,recipeName FROM meal,recipe WHERE meal.userID=%s AND meal.recipeID=recipe.recipeID ORDER BY Date"
    cur.execute(join_query,(UID,))
    meals = cur.fetchall()
    return render_template('display_schedule.html',meals=meals)
@app.route('/delete_schedules',methods=['GET','POST'])

def delete_schedules():
    if request.method=='GET':
        return render_template('delete_meal.html')
    UID = session.get('userid')
    del_date = request.form.get('date')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    delete_query = "DELETE FROM meal WHERE userID = %s AND Date = %s"
    cur.execute(delete_query,(UID,del_date))
    cur.close()
    mysql.connection.commit()
    return redirect(url_for('meal_planner'))

@app.route('/logout',methods=['GET'])
def logout():
    # Remove session data, this will effectively log the user out
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    session.pop('email', None)
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/check_user_details',methods=['GET'])
def check_user_details():
    UID = session.get('userid')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    check_query = "SELECT username,email,age,height,weight,gender FROM user WHERE userid = %s"
    cur.execute(check_query,(UID,))
    user_details = cur.fetchall()
    print(user_details)
    return render_template('user_details.html',user_details=user_details)

@app.route('/shopping_list_index')
def shopping_list_index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM ingredient")
    ingredients = cursor.fetchall()

    UID = session.get('userid')
    cursor.execute("SELECT IngredientName,ingredient.IngredientID FROM ingredient,user_ingredients WHERE userid=%s AND ingredient.IngredientID=user_ingredients.IngredientID",(UID,))
    user_ingredients = cursor.fetchall()

    return render_template('shopping_list.html', ingredients=ingredients, user_ingredients=user_ingredients)

@app.route('/add', methods=['POST'])
def add_to_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ingredient_id = request.form['ingredient']

    # Retrieve ingredient name from ingredients table
    cursor.execute("SELECT IngredientName FROM ingredient WHERE IngredientID = %s", (ingredient_id,))
    result = cursor.fetchone()
    if result:
        
        UID = session.get('userid')

        # Insert into user_ingredients table
        cursor.execute("INSERT INTO user_ingredients (IngredientID,userid) VALUES (%s,%s)", (ingredient_id,UID))
        mysql.connection.commit()

    return redirect(url_for('shopping_list_index'))

@app.route('/remove/<int:id>')
def remove_from_list(id):
    UID = session.get('userid')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM user_ingredients WHERE IngredientID = %s AND userid=%s", (id,UID))
    mysql.connection.commit()

    return redirect(url_for('shopping_list_index'))



if __name__ == '__main__':
    app.run(debug=True)
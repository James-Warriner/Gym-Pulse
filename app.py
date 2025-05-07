import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask import jsonify
import sqlite3
from helpers import login_required, error, utc_to_local, loadUser, loadExercises,loadLeaderboard,get_db
import pytz
from zoneinfo import ZoneInfo
from collections import defaultdict



app = Flask(__name__)



app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    activeWorkout = bool(session.get("workout_id"))
    user = loadUser()
    print(user)
    exercises = loadExercises()

    if request.method == "GET":
        leaderboard = loadLeaderboard({"exercise_id": 1})
        return render_template(
            "index.html",
            user=user,
            activeWorkout=activeWorkout,
            exercises=exercises,
            leaderboard=leaderboard,
            selected=1,
            name="",
            filter_type="exercise"
        )
    
    selected = int(request.form.get("exercise_id", 1))
    filter_type = request.form.get("filter_type", "exercise")
    name = request.form.get("name", "")

    if filter_type == "exercise_and_name" and name.strip():
        
        leaderboard = loadLeaderboard({"exercise_id": selected, "name": name})
        print(leaderboard)
    else:
        leaderboard = loadLeaderboard({"exercise_id": selected})

    return render_template(
        "index.html",
        user=user,
        activeWorkout=activeWorkout,
        exercises=exercises,
        leaderboard=leaderboard,
        selected=selected,
        name=name,
        filter_type=filter_type
    )

         
    
       






     

@app.route("/login", methods=["GET", "POST"])
def login():

  db = get_db()
  session.clear()
  if request.method == "GET":
    return render_template("login.html")
  else:
    user = request.form.get("username")
    pw = request.form.get("password")

    if not user:
      return error("No username/email provided", 400)
    elif not pw:
      return error("No password", 400)
    
    cursor = db.execute("SELECT * FROM users WHERE username = ? OR email = ?;",(user,user))

    rows = cursor.fetchall()

    if len(rows) != 1 or not check_password_hash(
      rows[0]["hashed_pw"], pw
    ):
      return error("Incorrect credentials",400)
    
    session["user_id"] = rows[0]["id"]

    return jsonify({"redirect":"/"})
  
@app.route("/register", methods=["GET", "POST"])
def register():
  db = get_db()

  if request.method == "GET":
    db = get_db()
    gyms = db.execute("SELECT * FROM gyms").fetchall()
    gyms = [dict(gym) for gym in gyms]
    return render_template("register.html", gyms = gyms)
  elif request.is_json == True:
    username = request.get_json().get("username")
    cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))

    rows = cursor.fetchall()

    print(rows)

    if rows:
      return error("not unique",400)
    else:
      return jsonify({})
  
  else:
    username = request.form.get("username")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    pw = request.form.get("password")
    day = request.form.get("dob_day")
    month = request.form.get("dob_month")
    year = request.form.get("dob_year")
    gym_id = request.form.get("gym_id")

    if not username:
      return error("Provide a username",400)
    if not first_name:
      return error("Provide your first name",400)
    if not last_name:
      return error("Provide last name",400)
    if not email:
      return error("Provide your email",400)
    if not pw:
      return error("Provide a password",400)
    if not gym_id:
       return error("Provide a gym",400)


    current_year = datetime.now().year


    if not day or not day.isdigit() or int(day) < 1 or int(day) > 31:
        return jsonify({"message": "Enter a valid day (1-31)"})


    if not month or not month.isdigit() or int(month) < 1 or int(month) > 12:
        return jsonify({"message": "Enter a valid month (1-12)"})


    if not year or not year.isdigit() or len(year) != 4 or int(year) < 1900 or int(year) > current_year:
        return jsonify({"message": f"Enter a valid year (1900–{current_year})"})
    
    if len(day) == 1:
      day = "0"+day
    if len(month) ==1:
      month = "0"+month
    
    dob = day+"-"+month+"-"+year

    
    cursor = db.execute("SELECT id FROM users WHERE username = ?", (username,))

    rows = cursor.fetchall()

    if rows:
      return error("Username not unique",400)
    
    else:
      hashed_pw = generate_password_hash(pw)

      db.execute("INSERT INTO users (username, first_name, last_name, email, hashed_pw, dob, gym_id ) VALUES (?,?,?,?,?,?,?)",(username, first_name,last_name,email,hashed_pw,dob,gym_id))
      db.commit()

      rows = db.execute("SELECT id FROM users WHERE username = ?",(username,))

      cursor = rows.fetchall()

      session["user_id"] = cursor[0]["id"]

      return jsonify({"redirect":"/"})
    
@app.route("/logout", methods=["GET"])
def logout():
  session.clear()
  return redirect("/login")


@app.route("/workout", methods=["GET", "POST"])
@login_required
def workout():
    db = get_db()
    user_id = session["user_id"]

    if request.method == "GET":
        
        workout = db.execute("""
            SELECT id, strftime('%Y-%m-%d %H:%M', start_time) as formatted_time 
            FROM workouts 
            WHERE user_id = ? AND end_time IS NULL
            ORDER BY start_time DESC LIMIT 1
        """, (user_id,)).fetchone()

        if not workout:
            # No active workout, create a new one
            db.execute("""
                INSERT INTO workouts (user_id, start_time) 
                VALUES (?, datetime('now'))
            """, (user_id,))
            db.commit()
            workout_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            workout_id = workout["id"]
            formatted_time = utc_to_local(workout["formatted_time"]+':00')

        session["workout_id"] = workout_id

        exercises = db.execute("""
            SELECT id, name FROM exercises ORDER BY name
        """).fetchall()

        return render_template("workout.html", time=formatted_time, exercises=exercises)

    data = request.get_json()
    workout_id = session.get("workout_id")

    if not workout_id:
        return jsonify({"error": "No active workout"}), 400

    action = data.get("action")

    if action == "add_exercise":
        exercise_id = data.get("exercise_id")
        if not exercise_id:
            return jsonify({"error": "Missing exercise_id"}), 400
        return jsonify({"success": True, "exercise_id": exercise_id})

    elif action == "save_set":
        try:
            db.execute("""
                INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                workout_id,
                data["exercise_id"],
                data["set_number"],
                data["reps"],
                data["weight"],
                data["notes"]
            ))
            db.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    elif action == "finish":
        try:
            
            db.execute("""
                UPDATE workouts SET end_time = datetime('now') WHERE id = ?
            """, (workout_id,))
            db.commit()
            session["workout_id"] = None
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif action == "save_name":
      name = request.get_json().get("name")
      try:
        db.execute("UPDATE workouts SET name = ? WHERE id = ?",(name,workout_id))
        db.commit()
        return jsonify({"success":True})
      except Exception as e:
       return jsonify({"error":str(e)}),400
    
    elif action == "get_name":
      name = request.get_json().get("name")
      try:
        row = db.execute("SELECT name FROM workouts WHERE id = ?",(workout_id,)).fetchall()[0]

        return jsonify({"success":True, "name":row["name"]})
      except Exception as e:
       return jsonify({"error":str(e)}),400
      


    return jsonify({"error": "Invalid action"}), 400

    

@app.route("/api/workouts/<int:workout_id>/sets")
@login_required
def get_workout_sets(workout_id):
    db = get_db()
    sets = db.execute("""
        SELECT s.id, s.exercise_id, e.name as exercise_name, 
               s.set_number, s.reps, s.weight, s.notes
        FROM sets s
        JOIN exercises e ON s.exercise_id = e.id
        WHERE s.workout_id = ?
        ORDER BY s.exercise_id, s.set_number
    """, (workout_id,)).fetchall()
    
    return jsonify([dict(row) for row in sets])



@app.route('/api/workout_id', methods=['GET'])
@login_required
def get_workout_id():
    workout_id = session.get('workout_id', 0)
    return jsonify({'workout_id': workout_id})

@app.route('/q', methods=["POST"])
@login_required
def searchExercises():
    db = get_db()
    query = request.form.get('query')


    cursor = db.execute("SELECT name,id FROM exercises WHERE name LIKE ?", ('%' + query + '%',))

    rows = cursor.fetchall()

    if rows:

        exercises = [{"name": row[0],"id":row[1]} for row in rows]
   
        return jsonify(exercises)
    else:
        return jsonify([])  
    
@app.route('/delete_workout',methods=['POST'])
@login_required
def delete():
  db = get_db()

  id = request.get_json().get('id')
  
  type = request.get_json().get('table')

  if id:
     if type == 'one':
        db.execute("DELETE FROM sets WHERE id = ?",(id))
        db.commit()
     elif type == 'all':
        exercise_name = request.get_json().get('exercise_name')
        print(exercise_name)
        cursor = db.execute("SELECT id FROM exercises WHERE name = ?",(exercise_name,))
        rows = cursor.fetchall()
        exercise = rows[0]["id"]
        print(exercise)

        db.execute("DELETE FROM sets WHERE exercise_id = ? AND workout_id = ?",(exercise,id))
        db.commit()

        return jsonify("Success")


@app.route("/history",methods=["GET","POST"])
@login_required
def history():
   db = get_db()
   def getData():
      rows = db.execute("SELECT * FROM workouts WHERE user_id = ? AND end_time NOT NULL ORDER BY end_time DESC",(session["user_id"],)).fetchall()

      user = dict(db.execute("SELECT * FROM users WHERE id = ?",(session["user_id"],)).fetchall()[0])
      workouts = [dict(row) for row in rows]
      for workout in workouts:
         workout["end_time"] = utc_to_local(workout["end_time"])
      return render_template("history.html",workouts = workouts, user = user)
   if request.method == "GET":
      return getData()
   
   data = request.get_json()
   action = data.get("action")

   if action == "delete":
      id = data.get("workoutId")

      db.execute("DELETE FROM workouts WHERE id = ?",(id,))
      db.commit()
      db.execute("DELETE FROM sets WHERE workout_id = ?",(id,))
      db.commit()
      return getData()

   if action == "view":
      id = request.get_json().get("workoutId")
      print(id)
      sets = db.execute("SELECT * FROM sets JOIN exercises ON sets.exercise_id = exercises.id WHERE sets.workout_id = ? ORDER BY sets.created_at ASC",(id,)).fetchall()

      workout = db.execute("SELECT * FROM workouts WHERE id = ?",(id,)).fetchall()[0]

      workout = dict(workout)

      workout["end_time"] = utc_to_local(workout["end_time"])
      workout["start_time"] = utc_to_local(workout["start_time"])

      grouped_sets = defaultdict(list)

      print([dict(set) for set in sets])

      for s in sets:
         grouped_sets[s["name"]].append(s)
      
      print(grouped_sets)

      return render_template("view_workout.html", workout = workout, grouped_sets = grouped_sets)
   


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        try:
            with sqlite3.connect("gym.db") as conn:
                conn.row_factory = sqlite3.Row
                username = request.form["username"]
                gym_id = request.form.get("gym_id")
                user_id = session["user_id"]

                conn.execute("UPDATE users SET username = ?, gym_id = ? WHERE id = ?", (username, gym_id, user_id))

                current_pw = request.form["current_password"]
                new_pw = request.form["new_password"]
                confirm_pw = request.form["confirm_password"]

                if new_pw:
                    if new_pw != confirm_pw:
                        flash("New passwords do not match", "danger")
                        return redirect("/profile")
                    
                    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
                    if not check_password_hash(user["hashed_pw"], current_pw):
                        flash("Current password is incorrect", "danger")
                        return redirect("/profile")

                    conn.execute("UPDATE users SET hashed_pw = ? WHERE id = ?", (generate_password_hash(new_pw), user_id))

                conn.commit()
                flash("Profile updated successfully", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")

        return redirect("/profile")

    db = get_db()
    gyms = db.execute("SELECT id, name FROM gyms").fetchall()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return render_template("profile.html", user=user, gyms=gyms)


      
   
@app.route("/browse_profiles",methods=["POST","GET"])
@login_required
def browse():
  db = get_db()
  gym_id = db.execute("SELECT gym_id FROM users WHERE id = ?",(session["user_id"],)).fetchall()[0]["gym_id"]

  if request.method == "GET":

    users = db.execute("SELECT u.id,u.timestamp, u.username, u.gym_id, u.first_name, u.last_name, u.dob, COALESCE(SUM(w.duration_minutes), 0) AS total_duration, (SELECT e.name FROM sets s JOIN workouts w2 ON s.workout_id = w2.id JOIN exercises e ON s.exercise_id = e.id WHERE w2.user_id = u.id GROUP BY e.name ORDER BY COUNT(*) DESC LIMIT 1) AS most_used_exercise FROM users u LEFT JOIN workouts w ON w.user_id = u.id WHERE u.gym_id = ? GROUP BY u.id", (gym_id,)).fetchall()


   
    users = [dict(user) for user in users]
    print(users)

    return render_template("browse_profiles.html", users = users)
  else:
    userId = request.get_json().get("id")

    print(userId)
    print(gym_id)

    user = db.execute("SELECT u.id,u.timestamp, u.username, u.first_name, u.last_name, u.dob, COALESCE(SUM(w.duration_minutes), 0) AS total_duration, COUNT(w.id) AS count, (SELECT e.name FROM sets s JOIN workouts w2 ON s.workout_id = w2.id JOIN exercises e ON s.exercise_id = e.id WHERE w2.user_id = u.id GROUP BY e.name ORDER BY COUNT(*) DESC LIMIT 1) AS most_used_exercise, g.name AS gym_name FROM users u LEFT JOIN workouts w ON w.user_id = u.id LEFT JOIN gyms g ON g.id = u.gym_id WHERE u.id = ? AND u.gym_id = ? GROUP BY u.id", (userId, gym_id)).fetchall()[0]

    print(dict(user))
    html_content = render_template("other_profiles.html", user=user)
    return jsonify({"html":html_content})




     


     
    








    






app.run(debug=True,host='0.0.0.0',port=5000)
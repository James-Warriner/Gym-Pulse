from flask import redirect, render_template, session,jsonify,g
from functools import wraps
from datetime import datetime, timedelta
import sqlite3



import pytz

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("gym.db")
        g.db.row_factory = sqlite3.Row
    return g.db


def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if session.get("user_id") is None:
      return redirect("/login")
    return f(*args, **kwargs)
  return decorated_function

def error(message, status):
  return jsonify({"message":message}),status

def utc_to_local(time):
  print(time)
  naive_dt = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
  from_tz = pytz.timezone("UTC")
  to_tz = pytz.timezone("Europe/London")


  localized_dt = from_tz.localize(naive_dt)
  converted_dt = localized_dt.astimezone(to_tz)

  return converted_dt.strftime("%Y-%m-%d %H:%M")

def loadUser():
  db = get_db()

  

  cursor = db.execute("SELECT * FROM users JOIN gyms ON users.gym_id = gyms.id WHERE users.id = ?",(session["user_id"],))

  row = cursor.fetchall()
  user = row[0]
  user = dict(user)
  
      
  cursor = db.execute("SELECT * FROM workouts WHERE user_id = ?",(session["user_id"],))
  rows = cursor.fetchall()
  duration_counter = 0
  count = 0
  for row in rows:
        
    if row["duration_minutes"]:
      duration_counter += int(row["duration_minutes"])
      duration_counter +=0
      count+=1
    else:
      count+=1
        


      
  cursor = db.execute("SELECT exercises.name, COUNT(*) AS count FROM sets JOIN exercises ON sets.exercise_id = exercises.id JOIN workouts ON workouts.id = sets.workout_id WHERE workouts.user_id = ? ORDER BY count DESC",(session["user_id"],))
  rows = cursor.fetchall()

  user["favourite"] = rows[0]["name"]
      
  user["count"] = count
  user["duration"] = round(duration_counter/60,1)
  print(user)

  return user
    
def loadExercises():
  db = get_db()
  cursor = db.execute("SELECT * FROM exercises").fetchall()
  return [dict(row) for row in cursor]
    
def loadLeaderboard(query):
    db = get_db()
    leaderboard = []
    gym_id = db.execute("SELECT gym_id FROM users WHERE id = ? ",(session["user_id"],)).fetchall()[0]["gym_id"]
    print(gym_id)
    
    try:
        exercise_id = query.get("exercise_id")
        name_filter = query.get("name")
        
        if exercise_id and not name_filter:
            leaderboard = db.execute("""
                SELECT 
                    RANK() OVER (ORDER BY sets.weight DESC) AS rank,
                    exercises.name, 
                    sets.weight, 
                    users.username, 
                    sets.reps
                FROM sets
                JOIN exercises ON sets.exercise_id = exercises.id
                JOIN workouts ON sets.workout_id = workouts.id
                JOIN users ON workouts.user_id = users.id
                WHERE exercises.id = ? AND users.gym_id = ?
                ORDER BY sets.weight DESC
                LIMIT 10
            """, (exercise_id,gym_id)).fetchall()
        
        elif exercise_id and name_filter:
            name = name_filter + '%'
            print(name)
            print(exercise_id)
            leaderboard = db.execute("""
                SELECT * FROM (
                    SELECT 
                        RANK() OVER (ORDER BY sets.weight DESC) AS rank,
                        exercises.name, 
                        sets.weight, 
                        users.username,
                        users.first_name,
                        users.last_name, 
                        users.gym
                        sets.reps
                    FROM sets
                    JOIN exercises ON sets.exercise_id = exercises.id
                    JOIN workouts ON sets.workout_id = workouts.id
                    JOIN users ON workouts.user_id = users.id
                    WHERE exercises.id = ? AND users.gym_id = ?
                )
                WHERE (first_name || ' ' || last_name) LIKE ? OR username LIKE ? AND 
                ORDER BY rank
            """, (exercise_id, name,name,gym_id)).fetchall()

    except Exception as e:
        print("Error loading leaderboard:", e)
        return []
    

    leaderboard = [dict(row) for row in leaderboard]
    return leaderboard


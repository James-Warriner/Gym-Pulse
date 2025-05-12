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

def admin_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if session.get("is_admin") is not True:
      return redirect("/")
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
        


      
  cursor = db.execute("SELECT exercises.name, COUNT(*) AS count FROM sets JOIN exercises ON sets.exercise_id = exercises.id JOIN workouts ON workouts.id = sets.workout_id WHERE workouts.user_id = ? GROUP BY exercises.name ORDER BY count DESC",(session["user_id"],))
  rows = cursor.fetchall()
  if rows:
    user["favourite"] = rows[0]["name"]
      
    user["count"] = count
    user["duration"] = round(duration_counter/60,1)
  else:
    user["favourite"] = ""
      
    user["count"] = 0
    user["duration"] = 0
  print(user)

  return user
    
def loadExercises():
  db = get_db()
  cursor = db.execute("SELECT * FROM exercises").fetchall()
  return [dict(row) for row in cursor]
    
def loadLeaderboard(query):
    db = get_db()
    leaderboard = []
    gym_id = db.execute("SELECT gym_id FROM users WHERE id = ?", (session["user_id"],)).fetchone()["gym_id"]

    try:
        exercise_id = query.get("exercise_id")
        name_filter = query.get("name")

        if exercise_id:

            complete_leaderboard_sql = """
            WITH UserBestSets AS (
                SELECT
                    users.id,
                    exercises.name,
                    sets.weight,
                    sets.reps,
                    ROUND(sets.weight * (1 + sets.reps / 30.0), 2) AS estimated_1RM,
                    users.username,
                    users.first_name,
                    users.last_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY users.id 
                        ORDER BY sets.weight * (1 + sets.reps / 30.0) DESC
                    ) AS set_rank
                FROM sets
                JOIN exercises ON sets.exercise_id = exercises.id
                JOIN workouts ON sets.workout_id = workouts.id
                JOIN users ON workouts.user_id = users.id
                WHERE exercises.id = ? AND users.gym_id = ?
            )
            SELECT
                RANK() OVER (ORDER BY estimated_1RM DESC) AS rank,
                id,
                username,
                name,
                weight,
                reps,
                estimated_1RM,
                first_name,
                last_name
            FROM UserBestSets
            WHERE set_rank = 1
            ORDER BY rank ASC
            """
            

            complete_leaderboard = db.execute(complete_leaderboard_sql, (exercise_id, gym_id)).fetchall()
            

            if name_filter:

                filtered_leaderboard = []
                name_lower = name_filter.lower()
                
                for entry in complete_leaderboard:
                    full_name = f"{entry['first_name']} {entry['last_name']}".lower()
                    username = entry['username'].lower()
                    
                    if (name_lower in full_name) or (name_lower in username):
                        filtered_leaderboard.append(entry)
                
                leaderboard = filtered_leaderboard
            else:
                leaderboard = complete_leaderboard[:10]

    except Exception as e:
        print("Error loading leaderboard:", e)
        return []

    return [dict(row) for row in leaderboard]






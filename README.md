# GymPulse

A workout tracker tht incoorporates healthy competition between users.

Video demo: https://youtu.be/c6k1P9JwcfM

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Code](#code)



## Overview

This project was created to emphasise the social impact of fitness. I believe that having an app that rewards users with satisfaction of being on a leaderboard is a key step in encouraging all to improve their health.

## Features


- Gym-Based leaderboards
- In depth workout tracker
- Self managed exercises through admin portal

## Code

### helpers.py:

Helpers.py is set up to manage login routes and enforce a user has a session id before acessing certain routes. Additionally, I added an admin_required function to also protect admin routes such as altering stored exercises. 

Additionally, helpers.py has reusable functions that load data such as: loadUser - gets logged in users favourite exercises, total workout time and general info, loadExercises - loads all stored exercises along with muscle groups, loadLeaderboard - takes "query" as a parameter and then fetches data from databases: sets, workouts, users, exercises, outputting the rank of users that match the query.

Helpers.py also has functions to load the database and convert timezones.

### app.py

app.py is where the magic really happens. Due to the minimal code (around 500 lines) I decided to keep the app's code in one file to save complexity.

#### index - login required

index is the route that loads the dashboard page, calling loadUser(), loadExercises() and loadLeaderboard() with params "bench press" (this is the default filter for leaderboard). This is all rendered onto index.html using Jinja when the page is loaded. If a POST request is made, loadLeaderboard is simply called with the query passed to it.

#### login

The login route is simply a route that returns the login.html page upon load. When a user sends a completed login form, it checks for correct password and username or email. It will return an identical error to the frontend if username or password is incorrect to reduce brute force likelihood. If a user's password is correct, their id is set as session ID and if they are marked as an admin their session["is_admin"] is set to true.

#### register

Upon load, the register route returns register.html. This has a form containing: username ,first name, last name, email, date of birth, affiliated gym, password.

As the username is typed, the frontend makes POST requests to register(), checking if the name is unique. If not, it returns an error not unique. Once the user completes their registration, checks take place to make sure all fields exist. If they do, all info is committed to users table.

#### logout

Clears session cookies to remove the logged in user's access.

#### workout - login required

Arguably the main function as it provides the user the ability to add workouts.

##### GET

GET requests check if the user has a workout ongoing, if not a new workout session is created. The workout_id is then stored in the session. It then retrives all exercises and renders them to the frontend.

##### POST
add_exercise - Confirms selection of exercise

save_set - Adds or updates a set for the current exercise in the workout

finish - Ends workout by clearing session workout id and saving end time.

save_name - Saves the workouts new name retrived from frontend.

#### get_workout_sets - login required

I will split this into frontend and backend due to its complexity.

##### Backend

Fetches sets and exercises that have the workout id passed to it. This returns a dictionary of all exercises/sets from the current workout to preserve data between saves/ reloads. 

##### Frontend

loadExistingSets() - Fetches and groups sets by exercise, creating blocks for each exercise.

addExerciseContainer() - Creates new container for exercise.

addSetToExercise() - Adds new row with input fields and auto saves on change.

updateTitle() - Updates the workouts name in real time when the user types.

finishWorkoutBtn.onclick - Sends a request to finish workput then redirects home.

### /q - login required

This endpoint searches the exercise table and joins muscles onto it with a search query. Thi query can resemble the name, muscle groups or mucle area.

### delete()

This function is passed an exercise_name which is used to get its id. Then from sets table, the exercise is deleted along with all sets associated in that workout.


### history() - login required

#### GET

Fetches all completed workouts for the logged in user, converts timestamps to local, passes the workouts to history.html to be displayed.

#### POST

delete - deletes the workout from the workouts table with id passed from frontend

view - Retrives all sets and exercises that match the workout_id selected. These are then rendered with view_workout.html.










## Installation

Instructions for setting up the project locally:

```bash
# Clone the repository
git clone https://https://github.com/James-Warriner/Gym-Pulse.git


cd Gym-Pulse

python -m venv venv
source venv/Scripts/Activate  

# Install dependencies
pip install -r requirements.txt

pip run flask --debug





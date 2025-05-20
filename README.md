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





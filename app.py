from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

DATABASE = 'highscores.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db_connection()
    db.execute('''
        CREATE TABLE IF NOT EXISTS high_scores (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            score INTEGER
            
        ); 
    ''')
    db.execute('''
    CREATE TABLE IF NOT EXISTS snake_scores (
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            score INTEGER
        );
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS wordle_high_scores (
            id INTEGER PRIMARY KEY,
            name TEXT,
            score INTEGER
            )''')

    db.commit()
    db.close()


# Manually pushing the application context
with app.app_context():
    init_db()


def add_score(name, score):
    conn = get_db_connection()
    conn.execute('INSERT INTO high_scores (name, score) VALUES (?, ?)', (name, score))
    conn.commit()
    conn.close()


def get_high_scores(limit=10):
    conn = get_db_connection()
    scores = conn.execute('SELECT name, MAX(score) AS score FROM high_scores GROUP BY name ORDER BY MAX(score) DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return scores


def snake_add_score(name, score):
    conn = get_db_connection()
    conn.execute('INSERT INTO snake_scores (name, score) VALUES (?, ?)', (name, score))
    conn.commit()
    conn.close()


def snake_get_high_scores(limit=10):
    conn = get_db_connection()
    scores = conn.execute('SELECT name, MAX(score) AS score FROM snake_scores GROUP BY name ORDER BY MAX(score) DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return scores


@app.route('/snake_high_scores', methods=['GET'])
def snake_get_high_scores_route():
    scores = snake_get_high_scores()
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])

@app.route('/add_score', methods=['POST'])
def add_score_route():
    score_data = request.json
    add_score(score_data['name'], score_data['score'])
    return jsonify({'message': 'Score added successfully!'}), 201


@app.route('/high_scores', methods=['GET'])
def get_high_scores_route():
    scores = get_high_scores()
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])


@app.route('/snake_add_score', methods=['POST'])
def snake_add_score_route():
    score_data = request.json
    snake_add_score(score_data['name'], score_data['score'])
    return jsonify({'message': 'Snake score added successfully!'}), 201

@app.route('/snake_high_scores', methods=['GET'])
def get_snake_high_scores_route():
    scores = snake_get_high_scores()
    return jsonify([{'name': row['name'], 'score': row['score']} for row in scores])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/snake')
def snake():
    return render_template('snake.html')



@app.route('/snake_score', methods=['POST', 'GET'])
def snake_score():
    score_data = request.args.get('score')
    snake_top_scores = snake_get_high_scores()
    return render_template('snake_scoreboard.html', score_data=score_data, snake_top_scores=snake_top_scores)

@app.route('/hilo')
def hilo():
    # Initialize points to 100 if it's not already in the session
    if 'hilo_points' not in session:
        session['hilo_points'] = 100

    # Retrieve points from session
    points = session['hilo_points']

    if 'hilo_errors' not in session:
        session['hilo_errors'] = 3

    errors = session['hilo_errors']
    if errors == 0:
        final_points = session['hilo_points']
        session['hilo_points'] = 100  # reset game points
        session['hilo_errors'] = 3  # reset errors
        top_scores = get_high_scores()
        return render_template('hilo_gameover.html',
                               points=final_points,
                               top_scores=top_scores)

    while True:
        number_first = random.randint(1,10)
        number_second = random.randint(1,10)
        if number_first != number_second:
            break

    return render_template('hilo.html',
                           points=points,
                           errors=errors,
                           number_first=number_first,
                           number_second=number_second)


@app.route('/hilo_guess', methods=['POST'])
def hilo_guess():
    number_first = int(request.form.get('number_first'))
    number_second = int(request.form.get('number_second'))
    guess = request.form.get('guess')
    points = int(request.form.get('points'))

    # Update points and determine result based on the guess
    if guess == 'Higher' and number_second > number_first:
        result = 'correct'
        session['hilo_points'] += 50
    elif guess == 'Lower' and number_second < number_first:
        result = 'correct'
        session['hilo_points'] += 50
    else:
        result = 'incorrect'
        session['hilo_points'] -= 50
        session['hilo_errors'] -= 1

    return render_template('hilo_result.html',
                           number_first=number_first,
                           number_second=number_second,
                           result=result)

def get_wordle_scores():
    conn = get_db_connection()
    scores = conn.execute('SELECT name, score FROM wordle_high_scores ORDER BY score DESC LIMIT ?', (10,)).fetchall()
    conn.close()
    return scores

@app.route('/wordle')
def wordle():
    with open('words.txt', 'r') as file:
        words = []
        for line in file:
            words.append(line)

    return render_template('wordle.html', word=random.choice(words).rstrip())

@app.route('/wordle-win', methods=['POST'])
def wordle_win():
    try:
        guesses = int(request.form['total-guesses'])
    except:
        flash('Invalid guesses data.')
        return redirect(url_for('wordle'))

    return render_template('wordle_entry.html', guesses=guesses, top_scores=get_wordle_scores())
@app.route('/add_score_wordle', methods=['POST'])
def add_score_wordle():
    try:
        name = request.form['name']
        score = int(request.form['score'])
    except:
        flash('INVALID FORM DATA SUBMISSION')
        return redirect(url_for('wordle_scores'))

    conn = get_db_connection()
    conn.execute('INSERT INTO wordle_high_scores (name, score) VALUES (?, ?)', (name, score))
    conn.commit()
    conn.close()

    return redirect(url_for('wordle_scores'))

@app.route('/wordle-scores')
def wordle_scores():
    return render_template('wordle_board.html', top_scores=get_wordle_scores())

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask
from flask import request, render_template, url_for, session, redirect
from datetime import timedelta
import random
from cube import Cube, DEFAULT_CUBECODE

app = Flask(__name__)
app.secret_key = 'adamka'
app.permanent_session_lifetime = timedelta(seconds=10)

@app.route('/')
def hello_world():
    return redirect(url_for('cube'))

@app.route('/cube')
def cube():
    cubecode = request.args.get('cubecode', DEFAULT_CUBECODE) 
    cubecode_userinput = request.args.get('cubecode-userinput', None) 
    
    if cubecode_userinput is not None:
        cubecode = ''.join([c for c in cubecode_userinput if c in 'wbogry'])
        return redirect(url_for('cube', cubecode=cubecode))
    else:
        cube = Cube(cubecode)
        return render_template('cube.html', cubecode=cube.cubecode, cube_color=cube.colors, cube_label=cube.strickers)



@app.route('/move')
def move():    
    cubecode = request.args.get('cubecode', DEFAULT_CUBECODE)
    moves = request.args.get('moves', 'U')

    cube = Cube(cubecode).moves(moves)

    return redirect(url_for('cube', cubecode=cube.cubecode))
    print(cube.strickers)
    return render_template('cube.html', cube_color=cube.colors, cube_label=cube.strickers)

@app.route('/page/<num>')
def view_page(num):
    num = int(num)
    session['path'] = session.get('path', []) + [num]
    path = session['path']
    return render_template('page.html', num=num, url=url_for('view_page', num=num*2), path=path)

    

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

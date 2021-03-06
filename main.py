from flask import Flask
from flask import request, render_template, url_for, session, redirect, jsonify, g, Response
import random
from cube import Cube
from solution import Solution
from moves import moves_to_human_readable
import yaml
import logging
from cube_url import cube_from_url_args, cube_to_url_args
from setup_moves import get_setup_moves, get_reverse_setup_moves
import os
from perms import PERM_MOVES
from get_pref import get_pref

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = 'adamka'
app.logger.setLevel(logging.INFO)


@app.errorhandler(404)
def error(e):
    return render_template('error.html')


@app.route('/')
def hello_world():
    return redirect(url_for('cube'))


@app.route('/robots.txt')
def robots_txt():
    robots_txt = '''\
User-agent: *
Allow: /
'''
    return Response(robots_txt, mimetype='text/plain')


@app.route('/guide')
def guide():
    return render_template(
        'guide.html',
        default_cube=Cube.create(),
        example_cube_for_dummy_selection=Cube.create().setup_moves('F').alg_y().undo_setup_moves('F').setup_moves('I').alg_y().undo_setup_moves('I')
    )


@app.before_request
def before_request():
    g.get_pref = get_pref
    g.moves_to_human_readable = moves_to_human_readable
    g.cube_from_url_args = cube_from_url_args
    g.cube_to_url_args = cube_to_url_args
    g.random = random
    g.str = str
    g.PERM_MOVES = PERM_MOVES
    g.get_setup_moves = get_setup_moves
    g.get_reverse_setup_moves = get_reverse_setup_moves

from letter_scheme import letter_to_user_scheme


@app.template_filter()
def user_letter_scheme(letter):
    return letter_to_user_scheme(letter)



@app.route('/hello')
def hello():
    return render_template('hello.html')


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if request.method == 'POST':
        for k, v in request.form.items():
            processed_v = v
            if k.startswith('pref_i_'):
                processed_v = int(v)
            elif k.startswith('pref_f_'):
                processed_v = float(v)
            elif k.startswith('pref_b_'):
                processed_v = v not in ['False', '0', 'false']
            session[k] = processed_v
            app.logger.info(f"Preference {k:30} set to {processed_v}")

    next_page = request.args.get('next', False)
    if next_page:
        return redirect(next_page)

    return render_template('preferences.html')


mnemonics_data = yaml.load(open('mnemonics.yaml').read(), Loader=yaml.Loader)


@app.route('/mnemonics')
def mnemonics():
    return render_template('mnemonics.html', mnemonics=mnemonics_data)


@app.route('/cube')
def cube():
    cubecode_userinput = request.args.get('cubecode-userinput', None)

    g.random = random
    g.str = str

    if cubecode_userinput is not None:
        cubecode = ''.join([c for c in cubecode_userinput if c in 'wbogry'])
        return redirect(url_for('cube', cubecode=cubecode))
    else:
        shuffle = session.get('shuffle', '')
        cube = cube_from_url_args(request.args)
        return render_template(
            'cube.html',
            cube=cube,
            shuffle=' '.join(moves_to_human_readable(list(shuffle))) if cube.cubestate_equal(Cube.create().moves(shuffle)) else None
        )


@app.route('/shuffle')
def shuffle():
    n = g.get_pref('pref_i_shufflen')
    shuffle = ''.join([random.choice('RrLlUuDdBbFf') for i in range(random.choice([n, n+1]))])
    session['shuffle'] = shuffle

    return redirect(
        url_for(
            'cube',
            **cube_to_url_args(Cube.create(shuffle=shuffle))
            )
        )


@app.route('/move')
def move():
    moves = request.args.get('moves', 'U')

    cube = cube_from_url_args(request.args)
    cube = cube.moves(list(moves))

    return redirect(url_for('cube', **cube_to_url_args(cube)))


@app.route('/solution')
def solution():
    cube = cube_from_url_args(request.args)
    solution = Solution.solve(cube)

    def get_mnemonic(que):
        que_lower = que.lower()
        mnemonic = mnemonics_data.get(que_lower, [{'name': que}])

        if mnemonic == []:
            mnemonic = [{'name': que}]

        return random.choice(mnemonic)['name']

    g.get_mnemonic = get_mnemonic
    g.random = random
    g.str = str
    g.zip = zip

    return render_template('solution.html', solution=solution, cube=cube)


@app.route('/_parse-cubecode-userinput')
def _verify_userinput():
    cubecode_userinput = request.args.get('userinput', None)

    print(list(request.args.items()))
    print(list(request.form.items()))
    if cubecode_userinput is not None:
        cubecode = ''.join([c for c in cubecode_userinput if c in 'wbogry'])

        if len(cubecode) > 3*3*6:
            return jsonify(valid=False, message='Input too long.')
        elif len(cubecode) < 3*3*6:
            return jsonify(valid=False, message='Input too short.')
        else:
            return jsonify(valid=True, cubecode=cubecode, message='Input OK.')

    else:
        return jsonify(valid=False, message='No userinput provided.')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

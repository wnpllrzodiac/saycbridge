# Copyright (c) 2013 The SAYCBridge Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from flask import Flask, Response, send_from_directory

GAE_DIR = os.path.dirname(os.path.abspath(__file__))

COFFEE_BIN = '/home/zodiac/work/tools/node-v22.21.0-linux-x64/bin/coffee'

app = Flask(__name__, template_folder='templates')

URL_PREFIX = os.environ.get('URL_PREFIX', '').rstrip('/')
app.config['URL_PREFIX'] = URL_PREFIX

@app.context_processor
def inject_url_prefix():
    return {'url_prefix': URL_PREFIX}

def serve_scripts(filename):
    scripts_dir = os.path.join(GAE_DIR, 'scripts')
    js_path = os.path.join(scripts_dir, filename)
    if not os.path.exists(js_path) and filename.endswith('.js'):
        coffee_path = js_path[:-3] + '.coffee'
        if os.path.exists(coffee_path):
            result = subprocess.run(
                [COFFEE_BIN, '--compile', '--print', coffee_path],
                capture_output=True, text=True)
            return Response(result.stdout, mimetype='application/javascript')
    return send_from_directory(scripts_dir, filename)

app.add_url_rule('/scripts/<path:filename>', endpoint='static_scripts', view_func=serve_scripts)

# Static directories not under /static
for _folder in ('stylesheets', 'images', 'static'):
    _path = os.path.join(GAE_DIR, _folder)
    app.add_url_rule(
        '/%s/<path:filename>' % _folder,
        endpoint='static_%s' % _folder,
        view_func=lambda filename, d=_path: send_from_directory(d, filename),
    )

app.add_url_rule(
    '/fight',
    endpoint='fight',
    view_func=lambda: send_from_directory(os.path.join(GAE_DIR, 'static'), 'fight.html'),
)

from handlers.autobid_handler import autobid
from handlers.explore_handler import explore, json_interpret
from handlers.bidder_handler import bidder
from handlers.scores_handler import scores
from handlers.score_flashcards_handler import score_flashcards
from handlers.unittest_handler import unittests
from handlers.priorities_handler import json_priorities

app.add_url_rule('/', view_func=bidder, endpoint='bidder_root')
app.add_url_rule('/bid', view_func=bidder, endpoint='bidder')
app.add_url_rule('/bid/<path:rest>', view_func=bidder, endpoint='bidder_path')
app.add_url_rule('/play', view_func=bidder, endpoint='play')
app.add_url_rule('/play/<path:rest>', view_func=bidder, endpoint='play_path')

app.add_url_rule('/explore', view_func=explore, endpoint='explore_root', defaults={'calls_string': None})
app.add_url_rule('/explore/<path:calls_string>', view_func=explore, endpoint='explore')
app.add_url_rule('/explore2', view_func=explore, endpoint='explore2_root', defaults={'calls_string': None})
app.add_url_rule('/explore2/<path:calls_string>', view_func=explore, endpoint='explore2')

app.add_url_rule('/json/autobid', view_func=autobid)
app.add_url_rule('/json/interpret', view_func=json_interpret)
app.add_url_rule('/json/interpret2', view_func=json_interpret, endpoint='json_interpret2')
app.add_url_rule('/json/priorities', view_func=json_priorities)

app.add_url_rule('/scores', view_func=scores)
app.add_url_rule('/scoring', view_func=score_flashcards, endpoint='scoring', defaults={'rest': None})
app.add_url_rule('/scoring/<path:rest>', view_func=score_flashcards, endpoint='scoring_path')

app.add_url_rule('/unittests', view_func=unittests)

if __name__ == '__main__':
    import os
    debug = os.environ.get('DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=19883, debug=debug, threaded=False)

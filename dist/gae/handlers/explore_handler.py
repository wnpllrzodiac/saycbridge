# Copyright (c) 2013 The SAYCBridge Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json
import subprocess
import urllib.parse

from flask import current_app, request, make_response, redirect, render_template

from core.call import Pass
from core.callexplorer import CallExplorer
from core.callhistory import CallHistory
from proxy import ConstraintsSerializer
from z3b.bidder import Interpreter, InconsistentHistoryException
from z3b.forcing import SAYCForcingOracle
from z3b.preconditions import annotations


BIDDER_REVISION = subprocess.check_output(['git', 'rev-parse', 'HEAD']).rstrip()


def _history_from_calls_string(calls_string):
    history_identifier = "N:NO:%s" % calls_string  # FIXME: may not be right with new identifiers
    return CallHistory.from_identifier(history_identifier)


def explore(calls_string=None):
    calls_string = calls_string or ""
    calls_string = urllib.parse.unquote(calls_string)
    history = _history_from_calls_string(calls_string)
    if calls_string and history.comma_separated_calls() != calls_string:
        url_prefix = current_app.config.get('URL_PREFIX', '')
        return redirect("%s/explore/%s" % (url_prefix, history.comma_separated_calls()))
    return render_template('explore.html', bidder_revision=BIDDER_REVISION)


def _set_if_not_none(dictionary, key, value):
    if value is not None:
        dictionary[key] = value


def _json_from_rule(knowledge_string, rule, call):
    explore_dict = {'call_name': call.name}
    _set_if_not_none(explore_dict, 'knowledge_string', knowledge_string)
    if rule:
        explore_dict['rule_name'] = rule.name
        priority = rule.priority.index if hasattr(rule, 'priority') and rule.priority else None
        _set_if_not_none(explore_dict, 'priority', priority)
        _set_if_not_none(explore_dict, 'explanation', rule.explanation_for_bid(call))
    return explore_dict


def _knowledge_string(position_view, interpreter):
    explore_string = ConstraintsSerializer(position_view).explore_string()
    annotations_whitelist = {annotations.Artificial, annotations.NotrumpSystemsOn}
    annotations_for_last_call = set(position_view.annotations_for_last_call) & annotations_whitelist
    pretty_string = "%s %s" % (explore_string, ", ".join(map(str, annotations_for_last_call)))
    if position_view.rule_for_last_call:
        try:
            partner_future = interpreter.extend_history(position_view.history, Pass())
            if SAYCForcingOracle().forced_to_bid(partner_future):
                pretty_string += " Forcing"
        except InconsistentHistoryException:
            pass
    return pretty_string


def _knowledge_string_and_rule_for_additional_call(history, call, interpreter):
    try:
        history = interpreter.extend_history(history, call)
        knowledge_string = _knowledge_string(history.rho, interpreter)
        return knowledge_string, history.rho.rule_for_last_call
    except InconsistentHistoryException:
        return None, None


def json_interpret():
    interpreter = Interpreter()
    calls_string = request.args.get('calls_string') or ''
    dealer_char = request.args.get('dealer') or ''
    vulnerability_string = request.args.get('vulnerability') or ''
    call_history = CallHistory.from_string(calls_string, dealer_char, vulnerability_string)

    interpretations = []
    with interpreter.create_history(call_history) as history:
        for call in CallExplorer().possible_calls_over(call_history):
            knowledge_string, rule = _knowledge_string_and_rule_for_additional_call(history, call, interpreter)
            explore_dict = _json_from_rule(knowledge_string, rule, call)
            interpretations.append(explore_dict)

    expires_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
    response = make_response(json.dumps(interpretations))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'public'
    response.headers['Expires'] = expires_str
    return response

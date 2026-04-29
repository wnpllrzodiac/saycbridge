# Copyright (c) 2013 The SAYCBridge Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json

import networkx.readwrite.json_graph
from flask import make_response

from z3b.sayc import StandardAmericanYellowCard


def json_priorities():
    graph = StandardAmericanYellowCard.priority_ordering.ordering._graph
    link_data = networkx.readwrite.json_graph.node_link_data(graph)

    for node in link_data['nodes']:
        node['id'] = repr(node['id'])

    response = make_response(json.dumps(link_data))
    response.headers['Content-Type'] = 'application/json'
    return response

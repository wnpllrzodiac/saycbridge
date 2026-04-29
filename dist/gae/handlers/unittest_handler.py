# Copyright (c) 2013 The SAYCBridge Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os.path
import re

from flask import render_template


_unittest_file_path = "../../src/tests/test_sayc.py"
_baseline_file_path = "../../src/z3b_baseline.txt"

_test_method_regexp = re.compile(r"\s+def (test_\w*)\(")
_hand_regexp = re.compile(r"(\w*\.\w*\.\w*\.\w*)")
_history_matcher = r"((?:(?:\d(?:C|D|H|S|N)|P|X|XX)\s?)+)"
_history_regexp = re.compile(r"history: %s" % _history_matcher)
_subtest_of_regexp = re.compile(r"subtest of %s" % _history_matcher)
_test_name_header_regexp = re.compile(r"(test_\w+)")


def _compute_test_method_lines(unittest_file_path):
    method_name_to_line = {}
    with open(unittest_file_path) as f:
        for line_number, line in enumerate(f.readlines()):
            m = _test_method_regexp.match(line)
            if m:
                method_name_to_line[m.group(1)] = line_number + 1
    return method_name_to_line


def _link_to_file(file_path, line_number=None):
    base_url = "https://github.com/eseidel/saycbridge/blob/master"
    url = "%s/%s" % (base_url, file_path)
    if line_number:
        url += "#L%s" % line_number
    return url


def _test_name_header(test_name, line_number=None):
    if not line_number:
        return test_name
    return "<a href='%s'>%s</a>" % (_link_to_file(_unittest_file_path, line_number), test_name)


def _page_from_unittest_output(output_file_path):
    test_method_lines = _compute_test_method_lines(_unittest_file_path)
    test_link = lambda name: _test_name_header(name, test_method_lines.get(name))

    with open(output_file_path) as f:
        content = f.read()
    content = content.replace("\n", "<br>")
    content = content.replace("FAIL", "<font color='red'>FAIL</font>")
    content = content.replace("WARNING", "<font color='orange'>WARNING</font>")
    content = _hand_regexp.sub(r"<a href='/hand/\1'>\1</a>", content)
    content = _history_regexp.sub(r"history: <a href='/explore/\1'>\1</a>", content)
    content = _subtest_of_regexp.sub(r"subtest of <a href='/explore/\1'>\1</a>", content)
    content = _test_name_header_regexp.sub(lambda m: test_link(m.group(0)), content)
    return content


def unittests():
    return render_template('unittests.html',
        unittests_output=_page_from_unittest_output(_baseline_file_path),
        unittest_file_name=os.path.basename(_baseline_file_path),
    )

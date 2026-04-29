# Copyright (c) 2013 The SAYCBridge Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from flask import render_template


def score_flashcards(rest=None):
    return render_template('score_flashcards.html')

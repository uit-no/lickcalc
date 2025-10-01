# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 12:53:14 2021

@author: admin
"""

from flask import Flask, render_template, request

app = Flask(__name__)
app.config["DEBUG"] = True

variables = {}

# Root URL
@app.route("/", methods=['GET', "POST"])
def index():
    if request.method == "GET":
        return render_template("test.html")
    
    try:
        variables["text 1"] = request.form["text1"]
    except: pass

    try:
        variables["text 2"] = request.form["text2"]
    except: pass
    
    return render_template("test.html", VARS=variables)

if __name__ == "__main__":
    app.run(debug=True)
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 16:06:09 2021

@author: admin
"""

from flask import Flask, request, flash, redirect, url_for, send_from_directory, render_template, Response
from werkzeug.utils import secure_filename
import os
import trompy as tp
import io

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = ".\\uploads"
app.config['MAX_CONTENT_PATH'] = 100000

FILETYPES = ["Med Associates", ".txt", ".csv", "DD Lab", "SF Lab"]

variables = {}
variables["options"] = ["No file loaded"]

# Root URL
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        print(os.path.join(".\\figs", "fig1.png"))
        return render_template("index.html", filetype_list=FILETYPES, option_list=variables["options"])
    
    try:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            variables["filename"] = filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)      
            extractdata(filepath)
        return redirect(url_for('index'))
    except: pass
    return


def extractdata(filepath):
    try:
        variables["data"] = tp.medfilereader_licks(filepath)
        variables["options"] = ["{}: {}".format(x, str(len(variables["data"][x]))) for x in variables["data"]]
        print("Extracted data")
        print(variables["options"])
    except:
        print("Cannot load file properly")
    return

# Root URL
@app.route("/analysis", methods=['POST'])
def analyze():
    variables["onset"] = request.form["onset"]
    variables["offset"] = request.form["offset"]
    
    variables["onsetArray"] = variables["data"][variables["onset"].split(':')[0]]
    
    variables["lickdata"] = tp.lickCalc(variables["onsetArray"], offset=[])
    
    return redirect(url_for('index'))

@app.route("/plot.png", methods=['POST'])
def plot():
        
    f = Figure(figsize=(8.27, 5))
    # f.suptitle(self.shortfilename.get())
    grid = mpl.gridspec.GridSpec(2, 3, wspace=0.5, hspace=0.5)
    ax1 = f.add_subplot(grid[0,:])
    ax2 = f.add_subplot(grid[1,0])
    ax3 = f.add_subplot(grid[1,1])
    ax4 = f.add_subplot(grid[1,2])

    try:
    # Licks over session 
        tp.sessionlicksFig(ax1, variables["onsetArray"])
    
    # Lick parameter figures
        tp.iliFig(ax2, variables["lickdata"])

        # if plotburstprob.get() == False:
        #     burstlengthFig(ax3, lickdata)
        # else:
        #     weibull_fit = burstprobFig(ax3, lickdata)
            
        tp.licklengthFig(ax4, variables["lickdata"])
    except:
        print("No data yet")
    
    output = io.BytesIO()
    FigureCanvas(f).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')
    
    # f.savefig(os.path.join(".\\static", "fig1.png"))
    
    # return redirect(url_for('index'))
# @app.route("/upload", methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # if user does not select file, browser also
#         # submit an empty part without filename
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file:
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], "__data__"))
#             return redirect(url_for('uploaded_file',
#                                     filename="__data__"))
#     return '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#     <form method=post enctype=multipart/form-data>
#       <input type=file name=file>
#       <input type=submit value=Upload>
#     </form>
#     '''
# @app.route('/uploads/<filename>')

# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)

if __name__ == "__main__":
    app.run(debug=True)
    
"""
Useful links:
https://www.freecodecamp.org/news/how-to-build-a-web-application-using-flask-and-deploy-it-to-the-cloud-3551c985e492/
https://blog.pythonanywhere.com/121/

"""
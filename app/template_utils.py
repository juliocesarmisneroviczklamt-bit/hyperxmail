from flask import render_template

def get_index_template():
    """
    Renders the index page.
    """
    return render_template('index.html')

def get_reports_template():
    """
    Renders the reports page.
    """
    return render_template('reports.html')
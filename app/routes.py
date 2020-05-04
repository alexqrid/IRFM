from app import app, es
from flask import render_template, jsonify, url_for, request, escape
from .tasks import process_report
import os


@app.route('/')
@app.route('/index')
def hello_world():
    return render_template('index.html',
                           title=app.config['title'],
                           reports=app.config['links']
                           )


@app.route("/search", methods=('GET', 'POST'))
def search():
    q = escape(request.args.get('q'))
    body = {
        "_source": {"excludes": ["path", "attachment.content", "data", "attachment.language"]},
        "from": 0, "size": 100,
        "query": {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": q,
                            "type": "phrase",
                            "fields": ["attachment.title^10", "attachment.content"],
                            "analyzer": "english"}},
                    {
                        "multi_match": {
                            "query": q,
                            "type": "most_fields",
                            "fields": ["attachment.title^2", "attachment.content"],
                            "analyzer": "english"}}],
                "minimum_should_match": 1}},
        "highlight": {
            "pre_tags": "<mark>",
            "post_tags": "</mark>",
            "boundary_scanner": "sentence",
            "fields":
                {"attachment.title": {
                    "number_of_fragments": 1,
                    "fragment_size": 175},
                    "attachment.content": {
                        "number_of_fragments": 3,
                        "fragment_size": 80
                    }
                }}
    }
    res = es.search(index="reports", doc_type="pdf", body=body)
    return jsonify(res['hits']['hits'])


@app.route('/process/<string:year>')
def process(year):
    task = process_report.apply_async(args=[app.config['STATIC_DIR'], year])
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = process_report.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'year' in task.info:
            response['year'] = task.info['year']
            response['common'] = task.info['common']
            return jsonify({"year": response['year'],
                            "top": response['common'],
                            'state': task.state,
                            'current': task.info.get('current', 0),
                            'total': task.info.get('total', 1),
                            'status': task.info.get('status', '')
                            }
                           )
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@app.route('/processed/<string:year>', methods=['GET', 'POST'])
def processed(year):
    if request.method == "POST":
        common = request.get_json()
        if os.path.exists(f"{app.config['STATIC_DIR']}/reports/report{year}.txt") and \
                os.path.exists(f"{app.config['STATIC_DIR']}/reports/report_tokenized{year}.txt") and \
                os.path.exists(f"{app.config['STATIC_DIR']}/reports/report_normalized{year}.txt") and \
                os.path.exists(f"{app.config['STATIC_DIR']}/reports/fig_norm{year}.png") and \
                os.path.exists(f"{app.config['STATIC_DIR']}/reports/fig_denorm{year}.png") and \
                os.path.exists(f"{app.config['STATIC_DIR']}/reports/fig_zipf{year}.png"):
            images = {"norm": f"/static/reports/fig_norm{year}.png",
                      "denorm": f"/static/reports/fig_denorm{year}.png",
                      "zipf": f"/static/reports/fig_zipf{year}.png", }
            return render_template("report.html",
                                   processed=True,
                                   graph=images,
                                   common=common)
    else:
        return jsonify({"Error": "Unknown data to process"}), 403

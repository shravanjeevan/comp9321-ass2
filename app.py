from flask import Flask, render_template
from flask_restplus import Api, fields, inputs, Resource, reqparse

# APPLICATION AND API SETUP

app = Flask(__name__)
api = Api(app)

# API ENDPOINT DEFINTIONS
# One with no param
@api.route('/hello')
class Hello(Resource):
    def get(self):
        return {'hello': 'world'}

# Example only
tasks = {
    'task1': "Get movie",
    'task2': "Return director name"
}

# One with param
@api.route('/task/<taskid>')
class ToDo(Resource):
    @api.doc('Get a specific task')
    @api.response(200, 'Success. Collection was found.')
    @api.response(404, 'Not found. Collection was not found')
    def get(self, taskid):

        if taskid not in tasks:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        return { 
            'task_id': taskid,
            'task_information': tasks[taskid]
        }, 200
    
    
    @api.doc('Delete a specific task')

    @api.response(200, 'Success. Collection was deleted.')
    @api.response(404, 'Not found. Collection was not found')
    def delete(self, taskid):

        if taskid not in tasks:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        del tasks[taskid]

        if taskid not in tasks:
            return { 
                'message': 'Collection deleted successfully.'
            }, 200

# APP ROUTING FUNCTIONS
@app.route('/home', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
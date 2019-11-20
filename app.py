from flask import Flask, render_template
from flask_restplus import Api, fields, inputs, Resource, reqparse

from preprocess import process_dataset2
# APPLICATION AND API SETUP

app = Flask(__name__)
api = Api(app)

# GLOBAL VARIABLES
actorDF, keywordsDF, genresDF, masterDF = process_dataset2()

# TODO Refer to these links for api creation:
# https://flask-restplus.readthedocs.io/en/stable/quickstart.html
# https://flask-restplus.readthedocs.io/en/stable/example.html
# https://flask-restplus.readthedocs.io/en/stable/parsing.html

# API INPUT MODELS
actors_model = api.model('ActorsModel', {
    'name': fields.String(
        description="Name of the actor required"
    ),
    'gender': fields.String(
        description="Actor gender",
        enum=["F", "M", "O"]
    )
}) 

# API OUTPUT MODELS

# API ENDPOINT DEFINTIONS

# -- Actors --
actors_parser = reqparse.RequestParser()
actors_parser.add_argument('name', type=str)
actors_parser.add_argument('gender', type=str)

@api.route('/actors')
class Actors(Resource):
    @api.doc('get_actors')
    @api.expect(actors_model)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global actorDF

        args = actors_parser.parse_args()

        if 'name' in args and args['name'] is not None:
            actor_name = args['name']
            print(actor_name)
            q = 'actor_name == ' + actor_name
            actor_record = actorDF.query(q)
            
            if actor_record.empty:
                return {
                    'error': 'Not Found',
                    'message': 'Collection was not found'
                }, 404
            
            return {
                'actor': actor_record.to_dict(orient='index')
            }, 200

        all_actors = actorDF.to_dict(orient='index')

        return {
            'actors': all_actors
        }, 200

# Example only
tasks = {
    'task1': {
        'movie' : "GET MOVEI"
    },
    'task2': "Return director name"
}

# One with param
@api.route('/tasks')
class ToDoAll(Resource):
    @api.doc('get_all_tasks')
    def get(self):
        return tasks

@api.route('/tasks/<taskid>')
@api.doc(params={'taskid': 'Id of task stored.'})
class ToDo(Resource):
    @api.doc('get_a_task')
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
    
    
    @api.doc('delete_a_task')
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
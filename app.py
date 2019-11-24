from flask import Flask, render_template, request
from flask_restplus import Api, fields, inputs, Resource, reqparse
from urllib.parse import quote_plus as urlencode
import json
from preprocess import process_dataset2
from machinelearning import predict_score
import requests as req
# TODO Things that must be done before submission
# - API:
#   1. Authentication
#   2. Pagination
#   3. Caching?
#   4. Data Analytics (also create webpage to display the data analytics)
#   5. Error codes (revisit)
#   6. Make sure all the params are labelled in the docs with a description

# APPLICATION AND API SETUP

app = Flask(__name__)

api = Api(app, title='COMP9321 Assignment 2 - API Documentation', validate=True)

# GLOBAL VARIABLES
directorDF, screenwriterDF, actorDF, keywordsDF, genresDF, movieDF = process_dataset2()
analytics_api_call_count = {
    'actors': 0,
    'specific actor': 0,
    'directors': 0,
    'specific director': 0,
    'screenwriters': 0,
    'specific screenwriter': 0,
    'movies': 0,
    'specific movie': 0,
    'keywords': 0,
    'genres': 0,
    'score predictor': 0
}

top_actor = dict()
top_movie = dict()
top_director = dict()
top_screenwriter = dict()

# TODO Refer to these links for api creation:
# https://flask-restplus.readthedocs.io/en/stable/quickstart.html
# https://flask-restplus.readthedocs.io/en/stable/example.html
# https://flask-restplus.readthedocs.io/en/stable/parsing.html

# API INPUT MODELS
# actors_model = api.model('ActorsModel', {
#     'name': fields.String(
#         description="Name of the actor queried",
#         required=False,
#         example="Tom Hanks"
#     ),
#     'gender': fields.String(
#         description="Actor gender",
#         required=False,
#         enum=["F", "M", "O"],
#         example="M"
#     ),
#     'offset': fields.Integer(
#         description="Start",
#         required="False",
#         example="0"
#     ),
#     'limit': fields.Integer(
#         description="Number of returned results",
#         required=False,
#         example="10"
#     )
# })


# directors_model = api.model('DirectorsModel', {
#     'name': fields.String(
#         description="Name of the director queried"
#     )
# })

# writers_model = api.model('WritersModel', {
#     'name': fields.String(
#         description="Name of the screenwriter queried"
#     )
# })


# API OUTPUT MODELS

# API ENDPOINT DEFINTIONS

# -- Actors --
# actors_parser
actors_parser = reqparse.RequestParser()
actors_parser.add_argument('name', type=str, help="Name of the actor queried")
actors_parser.add_argument('gender', type=str, choices=('M', 'F', 'O'), help="Actor gender")
actors_parser.add_argument('offset', type=int, help="offset given")
actors_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/actors', doc={"description" : "Actors 123"})
class Actors(Resource):
    @api.doc('get_actors')
    @api.expect(actors_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    # @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global actorDF
        global analytics_api_call_count
        global top_actor
        analytics_api_call_count['actors'] += 1
        args = actors_parser.parse_args()
        actor_record = actorDF

        # If name param is set
        if 'name' in args and args['name'] is not None:
            actor_name = args['name'].lower().strip('\'').strip('\"')

            # Old way (just in case we need it)
            # q = 'actor_name == \'' + actor_name + '\''
            # actor_record = actor_record.query(q)

            actor_record = actor_record[actor_record['actor_name'].str.contains(actor_name) == True]

        # If gender param is set:
        if 'gender' in args and args['gender'] is not None:
            gender = args['gender'].upper().strip('\'').strip('\"')
            # TODO validate gender is M, F or O

            q = 'gender == \'' + gender + '\''
            actor_record = actor_record.query(q)

        actor_record, response = pagination(request, args, actor_record)

        if actor_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        first_actor = actor_record['actor_name'].iloc[0]
        if first_actor in top_actor:
            top_actor[first_actor] += 1
        else:
            top_actor[first_actor] = 1
        # print(top_actor)
        print(actor_record['actor_name'].iloc[0])
        if(len(actor_record.index) == 1):
            response['actor'] = actor_record.to_dict(orient='index')
        else :
            response['actors'] = actor_record.to_dict(orient='index')

        return response, 200

# -- Specific Actor --
@api.route('/actors/<int:actor_id>')
class SpecificActor(Resource):
    @api.doc('get_specific_actor')
    @api.response(200, 'Success. Collection entries retrieved.')
    # @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self, actor_id):
        # print()
        global analytics_api_call_count
        analytics_api_call_count['specific actor'] += 1
        if not actorDF.index.isin([actor_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        actor_record = actorDF.iloc[[actor_id]]

        return {
            'actors': actor_record.to_dict(orient='index')
        }, 200


# -- Directors --
# director_parser
director_parser = reqparse.RequestParser()
director_parser.add_argument('name', type=str, help="Name of the director queried")
director_parser.add_argument('offset', type=int, help="offset given")
director_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/directors')
class Director(Resource):
    @api.doc('get_directors')
    @api.expect(director_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global directorDF
        global analytics_api_call_count
        global top_director
        analytics_api_call_count['directors'] += 1

        args = director_parser.parse_args()
        director_record = directorDF
        if 'name' in args and args['name'] is not None:
            director_name = args['name'].lower().strip('\'').strip('\"')
            director_record = director_record[director_record['director_name'].str.contains(director_name) == True]

            # OLD
            # q = 'director_name == \'' + director_name + '\''
            # director_record = directorDF.query(q)

        director_record, response = pagination(request, args, director_record)

        if director_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        first_director = director_record['director_name'].iloc[0]
        if first_director in top_director:
            top_director[first_director] += 1
        else:
            top_director[first_director] = 1

        if(len(director_record.index) == 1):
            response['director'] = director_record.to_dict(orient='index')
        else :
            response['directors'] = director_record.to_dict(orient='index')

        return response, 200


# -- Specific Director --

@api.route('/directors/<int:director_id>')
class SpecificDirector(Resource):
    @api.doc('get_specific_director')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self, director_id):
        global analytics_api_call_count
        analytics_api_call_count['specific director'] += 1
        if not directorDF.index.isin([director_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404


        director_record = directorDF.iloc[[director_id]]


        return {
            'director': director_record.to_dict(orient='index')
        }, 200

# -- Writers --
# writer_parser
writer_parser = reqparse.RequestParser()
writer_parser.add_argument('name', type=str, help="Name of the screenwriter queried")
writer_parser.add_argument('offset', type=int, help="offset given")
writer_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/screenwriters')
class Screenwriter(Resource):
    @api.doc('get_screenwriters')
    @api.expect(writer_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global screenwriterDF
        global analytics_api_call_count
        analytics_api_call_count['screenwriters'] += 1

        args = writer_parser.parse_args()
        writer_record = screenwriterDF
        if 'name' in args and args['name'] is not None:
            writer_name = args['name'].lower().strip('\'').strip('\"')
            writer_record = writer_record[writer_record['writer_name'].str.contains(writer_name) == True]

            # OLD
            # q = 'writer_name == \'' + writer_name + '\''
            # writer_record = screenwriterDF.query(q)

        writer_record, response = pagination(request, args, writer_record)

        if writer_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        first_screenwriter = writer_record['writer_name'].iloc[0]
        # print(first_screenwriter)
        if first_screenwriter in top_screenwriter:
            top_screenwriter[first_screenwriter] += 1
        else:
            top_screenwriter[first_screenwriter] = 1

        if(len(writer_record.index) == 1):
            response['writer'] = writer_record.to_dict(orient='index')
        else :
            response['writers'] = writer_record.to_dict(orient='index')

        return response, 200

# -- Specific Writer --
@api.route('/screenwriters/<int:screenwriter_id>')
class Screenwriter(Resource):
    @api.doc('get_specific_screenwriter')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self, screenwriter_id):
        global analytics_api_call_count
        global top_screenwriter
        analytics_api_call_count['specific screenwriter'] += 1
        if not screenwriterDF.index.isin([screenwriter_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        # print(screenwriterDF.to_string)
        screenwriter_record = screenwriterDF.iloc[[screenwriter_id]]

        return {
            'screenwriter': screenwriter_record.to_dict(orient='index')
        }, 200

# -- Movie --
# movie_parser
movie_parser = reqparse.RequestParser()
movie_parser.add_argument('name', type=str, help="Name of the movie queried")
movie_parser.add_argument('actor', type=str) # Multiple actors (union / intersection ?)
movie_parser.add_argument('director', type=str)
movie_parser.add_argument('screenwriter', type=str)
movie_parser.add_argument('keyword', type=str)
movie_parser.add_argument('genre', type=str)
movie_parser.add_argument('budget', type=int)
movie_parser.add_argument('revenue', type=int)
movie_parser.add_argument('offset', type=int, help="offset given")
movie_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/movies')
class Movies(Resource):
    @api.doc('get_all_movies')
    @api.expect(movie_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global movieDF
        global analytics_api_call_count
        global top_movie
        analytics_api_call_count['movies'] += 1
        movie_record = movieDF
        expr = '(?=.*{})'
        args = movie_parser.parse_args()


        if 'name' in args and args['name'] is not None:
            name = args['name'].lower()
            q = 'title == \'' + name + '\''
            movie_record = movie_record.query(q)

        if 'actor' in args and args['actor'] is not None:
            words = args['actor'].lower().strip('\'').strip('\"').split(',')
            movie_record = movie_record[movie_record["cast"].str.contains(r''.join(expr.format(w) for w in words), regex=True)]

        if 'director' in args and args['director'] is not None:
            words = args['director'].lower().strip('\'').strip('\"').split(',')
            movie_record = movie_record[movie_record["directors"].str.contains(r''.join(expr.format(w) for w in words), regex=True)]

        if 'screenwriter' in args and args['screenwriter'] is not None:
            words = args['screenwriter'].lower().strip('\'').strip('\"').split(',')
            movie_record = movie_record[movie_record["screenwriters"].str.contains(r''.join(expr.format(w) for w in words), regex=True)]

        if 'keyword' in args and args['keyword'] is not None:
            words = args['keyword'].lower().strip('\'').strip('\"').split(',')
            movie_record = movie_record[movie_record["keywords"].str.contains(r''.join(expr.format(w) for w in words), regex=True)]

        if 'genre' in args and args['genre'] is not None:
            words = args['genre'].lower().strip('\'').strip('\"').split(',')
            movie_record = movie_record[movie_record["genres"].str.contains(r''.join(expr.format(w) for w in words), regex=True)]

        # TODO Discuss whether budget should be <= or >=
        if 'budget' in args and args['budget'] is not None:
            movie_record = movie_record[movie_record["budget"] >= args['budget']]

        if 'revenue' in args and args['revenue'] is not None:
            movie_record = movie_record[movie_record["revenue"] >= args['revenue']]

        movie_record, response = pagination(request, args, movie_record)
        # print(movie_record.to_string)


        if movie_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        first_movie = movie_record['title'].iloc[0]
        if first_movie in top_movie:
            top_movie[first_movie] += 1
        else:
            top_movie[first_movie] = 1

        if(len(movie_record.index) == 1):
            response['movie'] = movie_record.to_dict(orient='index')
        else :
            response['movies'] = movie_record.to_dict(orient='index')

        return response, 200


# -- Specific Movie
@api.route('/movies/<int:movie_id>')
class SpecificMovie(Resource):
    @api.doc('get_specific_movie')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self, movie_id):
        global analytics_api_call_count
        analytics_api_call_count['specific movie'] += 1
        if not movieDF.index.isin([movie_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        movie_record = movieDF.iloc[[movie_id]]


        return {
            'movie': movie_record.to_dict(orient='index')
        }, 200


keyword_parser = reqparse.RequestParser()
keyword_parser.add_argument('offset', type=int, help="offset given")
keyword_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/keywords')
class Keywords(Resource):
    @api.doc('get_keywords')
    @api.expect(keyword_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global keywordsDF
        global analytics_api_call_count
        analytics_api_call_count['keywords'] += 1
        keywords_record = keywordsDF
        args = keyword_parser.parse_args()
        keywords_record, response = pagination(request, args, keywords_record)

        if keywords_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        if(len(keywords_record.index) == 1):
            response['keyword'] = keywords_record.to_dict(orient='index')
        else :
            response['keywords'] = keywords_record.to_dict(orient='index')

        return response, 200


genre_parser = reqparse.RequestParser()
genre_parser.add_argument('offset', type=int, help="offset given")
genre_parser.add_argument('limit', type=int, help="number of results to return")

@api.route('/genres')
class Genres(Resource):
    @api.doc('get_genres')
    @api.expect(genre_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global genresDF
        global analytics_api_call_count
        analytics_api_call_count['genres'] += 1
        genres_record = genresDF
        args = genre_parser.parse_args()
        genres_record, response = pagination(request, args, genres_record)

        if genres_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        if(len(genres_record.index) == 1):
            response['genre'] = genres_record.to_dict(orient='index')
        else :
            response['genres'] = genres_record.to_dict(orient='index')

        return response, 200



def pagination(request, args, record):

        offset = 0
        limit = 20
        if 'offset' in args and args['offset'] is not None:
            offset = args['offset']

        if 'limit' in args and args['limit'] is not None:
            limit = args['limit']

        qsize = len(record.index)
        record = record.iloc[offset : offset + limit]
        qpagesize = len(record.index)

        querystring = ""
        for key in args.keys():
            if key == 'offset' or key == 'limit': continue
            if args[key] is not None:
                querystring += key + "=" + urlencode(str(args[key])) + "&"
        baseURL     = request.base_url + "?" + querystring
        print(baseURL)
        firstURL    = baseURL + 'limit=' + str(limit) + "&"
        lastURL     = baseURL
        prevURL     = baseURL
        nextURL     = baseURL

        if offset - limit > 0: # if there's nothing previous then it's just the original url
            prevURL += 'offset=' + str((offset - limit)) + '&limit=' + str(limit) + "&"
        else:
            prevURL += 'limit=' + str(limit) + "&"

        if offset + limit < qsize:
            nextURL += 'offset=' + str((offset + limit)) + "&"
            if offset + limit + limit > qsize:
                nextURL += 'limit=' + str(qsize - offset - limit) + "&"
                lastURL = nextURL
            else:
                nextURL += 'limit=' + str(limit) + "&"
                lastURL += 'offset=' + str((qsize - (qsize % limit))) + '&limit=' + str(limit) + "&"
        else:
            nextURL = None
            lastURL = None

        if firstURL is not None : firstURL = firstURL[:-1]
        if lastURL  is not None : lastURL = lastURL[:-1]
        if prevURL  is not None : prevURL = prevURL[:-1]
        if nextURL  is not None : nextURL = nextURL[:-1]


        return record, {
            'href'  : request.url,
            'offset': offset,
            'limit' : limit,
            'results_shown' : qpagesize,
            'total_results' : qsize,
            'first' : {
                'href'  : firstURL
            },
            'prev'  : {
                'href'  : prevURL
            },
            'next'  : {
                'href'  : nextURL
            },
            'last'  : {
                'href'  :lastURL
            }
        }

# -- Movie --
# movie_parser
imdb_score_parser = reqparse.RequestParser()
# imdb_score_parser.add_argument('num_critic_for_reviews', type=int, help="Number of Critic Reviews")
imdb_score_parser.add_argument('director_facebook_likes', type=int, help="Number of Facebook Likes for Director", required=True)
imdb_score_parser.add_argument('actor_1_facebook_likes', type=int, help="Number of Facebook likes for Actor 1", required=True)
imdb_score_parser.add_argument('actor_2_facebook_likes', type=int, help="Number of Facebook likes for Actor 2", required=True)
# imdb_score_parser.add_argument('num_voted_users', type=int, help="Number of votes by users")
imdb_score_parser.add_argument('actor_3_facebook_likes', type=int, help="Number of Facebook likes for Actor 3", required=True)
# imdb_score_parser.add_argument('num_user_for_reviews', type=int, , help="")
imdb_score_parser.add_argument('budget', type=int, help="Budget", required=True)
# imdb_score_parser.add_argument('movie_facebook_likes', type=int, help="Number of Facebook likes on the movie", required=True)

@api.route('/imdb_score_prediction')
class IMDBScorePredictor(Resource):
    @api.doc('get_imdb_score_prediction')
    @api.expect(imdb_score_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global analytics_api_call_count
        analytics_api_call_count['score predictor'] += 1
        args = imdb_score_parser.parse_args()
        director_facebook_likes = args['director_facebook_likes']
        actor_1_facebook_likes = args['actor_1_facebook_likes']
        actor_2_facebook_likes = args['actor_2_facebook_likes']
        actor_3_facebook_likes = args['actor_3_facebook_likes']
        # cast_total_facebook_likes = args['cast_total_facebook_likes']
        budget = args['budget']

        # movie_facebook_likes = args['movie_facebook_likes']

        return {
            'movie_prediction_score': predict_score(director_facebook_likes,actor_1_facebook_likes,actor_2_facebook_likes,actor_3_facebook_likes,budget)
        }, 200


@api.route('/analytics_api_call_count')
class Analytics(Resource):
    @api.doc('get_analytics')
    # @api.expect(analytics_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global analytics_api_call_count
        # print(json.dumps(analytics))
        response = { "href": "http://127.0.0.1:5000/analytics_api_call_count",
                    "results_shown": len(analytics_api_call_count),
                    "total_results": len(analytics_api_call_count),
                    "analytics_api_call_count": ""
                }
        response['analytics_api_call_count'] = analytics_api_call_count
        return response, 200


@api.route('/analytics_top_actor')
class TopActorAnalytics(Resource):
    @api.doc('get_analytics_top_actor')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global top_actor
        # print(top_actor)
        # sorted(top_actor, key=numbermap.__getitem__)
        response = { "href": "http://127.0.0.1:5000/analytics_top_actor",
                    "results_shown": len(top_actor),
                    "total_results": len(top_actor),
                    "analytics_top_actor": ""
                }
        response['analytics_top_actor'] = top_actor
        return response, 200


@api.route('/analytics_top_movie')
class TopMovieAnalytics(Resource):
    @api.doc('get_analytics_top_movie')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global top_movie
        # print(top_actor)
        # sorted(top_actor, key=numbermap.__getitem__)
        response = { "href": "http://127.0.0.1:5000/analytics_top_movie",
                    "results_shown": len(top_movie),
                    "total_results": len(top_movie),
                    "analytics_top_movie": ""
                }
        response['analytics_top_movie'] = top_movie
        return response, 200


@api.route('/analytics_top_director')
class TopMovieAnalytics(Resource):
    @api.doc('get_analytics_top_director')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global top_director
        # print(top_actor)
        # sorted(top_actor, key=numbermap.__getitem__)
        response = { "href": "http://127.0.0.1:5000/analytics_top_director",
                    "results_shown": len(top_director),
                    "total_results": len(top_director),
                    "analytics_top_director": ""
                }
        response['analytics_top_director'] = top_director
        return response, 200


@api.route('/analytics_top_screenwriter')
class TopScreenwriterAnalytics(Resource):
    @api.doc('get_analytics_top_screenwriter')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self):
        global top_screenwriter
        # print(top_actor)
        # sorted(top_actor, key=numbermap.__getitem__)
        response = { "href": "http://127.0.0.1:5000/analytics_top_director",
                    "results_shown": len(top_screenwriter),
                    "total_results": len(top_screenwriter),
                    "analytics_top_screenwriter": ""
                }
        response['analytics_top_screenwriter'] = top_screenwriter
        return response, 200
# # Example only
# tasks = {
#     'task1': {
#         'movie' : "GET MOVEI"
#     },
#     'task2': "Return director name"
# }

# # One with param
# @api.route('/tasks')
# class ToDoAll(Resource):
#     @api.doc('get_all_tasks')
#     def get(self):
#         return tasks

# @api.route('/tasks/<taskid>')
# @api.doc(params={'taskid': 'Id of task stored.'})
# class ToDo(Resource):
#     @api.doc('get_a_task')
#     @api.response(200, 'Success. Collection was found.')
#     @api.response(404, 'Not found. Collection was not found')
#     def get(self, taskid):

#         if taskid not in tasks:
#             return {
#                 'error': 'Not Found',
#                 'message': 'Collection was not found'
#             }, 404

#         return {
#             'task_id': taskid,
#             'task_information': tasks[taskid]
#         }, 200


#     @api.doc('delete_a_task')
#     @api.response(200, 'Success. Collection was deleted.')
#     @api.response(404, 'Not found. Collection was not found')
#     def delete(self, taskid):

#         if taskid not in tasks:
#             return {
#                 'error': 'Not Found',
#                 'message': 'Collection was not found'
#             }, 404

#         del tasks[taskid]

#         if taskid not in tasks:
#             return {
#                 'message': 'Collection deleted successfully.'
#             }, 200

# APP ROUTING FUNCTIONS
@app.route('/application/home', methods=['GET'])
def index():

    return render_template('index.html', directors=list(directorDF['director_name']),
                                         actors=list(actorDF['actor_name']),
                                         genres=list(genresDF['genres']))

@app.route('/application/imdbscoreprediction_ui', methods=['GET'])
def imdbscoreprediction_ui():

    return render_template('imdbscoreprediction.html', directors=list(directorDF['director_name']),
                                         actors=list(actorDF['actor_name']),
                                         genres=list(genresDF['genres']))

@app.route('/application/genres_ui', methods=['GET', 'POST'])
def genres_ui():

    if request.method == 'GET':
        return render_template('genres.html')
    elif request.method == 'POST':
        # Get perform API call
        url = str(request.url_root) + 'genres'
        result = req.get(url).json()
        return render_template('genres.html', genres_dict=result)

@app.route('/application/directors_ui', methods=['GET'])
def directors_ui():

    return render_template('directors.html')

@app.route('/application/actors_ui', methods=['GET'])
def actors_ui():

    return render_template('actors.html')

@app.route('/application/keywords_ui', methods=['GET'])
def keywords_ui():

    return render_template('keywords.html')

@app.route('/application/movies_ui', methods=['GET'])
def movies_ui():

    return render_template('movies.html')

@app.route('/application/screenwriters_ui', methods=['GET'])
def screenwriters_ui():

    return render_template('screenwriters.html')



if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

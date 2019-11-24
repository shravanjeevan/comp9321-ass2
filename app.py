from flask import Flask, render_template, request
from flask_restplus import Api, fields, inputs, Resource, reqparse
from urllib.parse import quote_plus as urlencode
import json
from preprocess import process_dataset2
from machinelearning import predict_score

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

api = Api(app, title='COMP9321 Assignment 2 - API Documentation')

# GLOBAL VARIABLES
directorDF, screenwriterDF, actorDF, keywordsDF, genresDF, movieDF = process_dataset2()
global analytics
analytics = {
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

# TODO Refer to these links for api creation:
# https://flask-restplus.readthedocs.io/en/stable/quickstart.html
# https://flask-restplus.readthedocs.io/en/stable/example.html
# https://flask-restplus.readthedocs.io/en/stable/parsing.html

# API OUTPUT MODELS

# API ENDPOINT DEFINTIONS

# -- Actors --
# actors_parser
actors_parser = reqparse.RequestParser()
actors_parser.add_argument('name', type=str, help="Name of the actor queried.")
actors_parser.add_argument('gender', type=str, choices=('M', 'F', 'O'), help="Actor gender.\nEnsure that there are NO quotation marks around the gender letter (either \' or \" ).")
actors_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
actors_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/actors', doc={
    "description" : "Endpoint which gets all actors and each of their corresponding information, or accepts parameters to refine the list of actors returned."
})
class Actors(Resource):
    @api.doc('get_actors')
    @api.expect(actors_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global actorDF
        global analytics
        analytics['actors'] += 1
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
            gender = args['gender'].upper()

            q = 'gender == \'' + gender + '\''
            actor_record = actor_record.query(q)

        actor_record, response_message, response_code = pagination(request, args, actor_record)

        if actor_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(actor_record.index) == 1):
            response_message['actor'] = actor_record.to_dict(orient='index')
        else :
            response_message['actors'] = actor_record.to_dict(orient='index')

        return response_message, 200

# -- Specific Actor --
@api.route('/actors/<int:actor_id>', doc={
    "description" : "Endpoint which gets a specific actor and their corresponding information based on a unique id number."
})
class SpecificActor(Resource):
    @api.doc('get_specific_actor')
    @api.response(200, 'Success. Collection entry retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collection.')
    @api.response(403, 'Forbidden access to collection.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self, actor_id):
        global analytics
        analytics['specific actor'] += 1
        if not actorDF.index.isin([actor_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        actor_record = actorDF.iloc[[actor_id]]

        return {
            'actors': actor_record.to_dict(orient='index')
        }, 200

# -- Analytics --
@api.route('/analytics', doc={
    "description": "Endpoint which returns API usage metrics, such as number of times an endpoint has been called."
})
class Analytics(Resource):
    @api.doc('get_analytics')
    @api.response(200, 'Success. Collection retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collection.')
    @api.response(403, 'Forbidden access to collection.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global analytics
        # print(json.dumps(analytics)) 
        response = { "href": request.base_url,
                    "results_shown": len(analytics),
                    "total_results": len(analytics),
                    "analytics": ""
                }
        response['analytics'] = analytics
        return response, 200

# -- Directors --
# director_parser
director_parser = reqparse.RequestParser()
director_parser.add_argument('name', type=str, help="Name of the director queried.")
director_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
director_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/directors', doc={
    "description" : "Endpoint which gets all directors and each of their corresponding information, or accepts parameters to refine the list of directors returned."
})
class Director(Resource):
    @api.doc('get_directors')
    @api.expect(director_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global directorDF
        global analytics
        analytics['directors'] += 1

        args = director_parser.parse_args()
        director_record = directorDF
        if 'name' in args and args['name'] is not None:
            director_name = args['name'].lower().strip('\'').strip('\"')
            director_record = director_record[director_record['director_name'].str.contains(director_name) == True]

        director_record, response_message, response_code = pagination(request, args, director_record)

        if director_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(director_record.index) == 1):
            response_message['director'] = director_record.to_dict(orient='index')
        else :
            response_message['directors'] = director_record.to_dict(orient='index')

        return response_message, 200


# -- Specific Director --
@api.route('/directors/<int:director_id>', doc={
    "description": "Endpoint which gets a specific director and their corresponding information based on a unique id number."
})
class SpecificDirector(Resource):
    @api.doc('get_specific_director')
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(404, 'Not found. Collection not found.')
    def get(self, director_id):
        global analytics
        analytics['specific director'] += 1
        if not directorDF.index.isin([director_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        director_record = directorDF.iloc[[director_id]]

        return {
            'director': director_record.to_dict(orient='index')
        }, 200

# -- Genres --
# genre_parser
genre_parser = reqparse.RequestParser()
genre_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
genre_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/genres', doc={
    "description": "Endpoint which retrieves all movie genres."
})
class Genres(Resource):
    @api.doc('get_genres')
    @api.expect(genre_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collections not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global genresDF
        global analytics
        analytics['genres'] += 1
        genres_record = genresDF
        args = genre_parser.parse_args()
        genres_record, response_message, response_code = pagination(request, args, genres_record)

        if genres_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(genres_record.index) == 1):
            response_message['genre'] = genres_record.to_dict(orient='index')
        else :
            response_message['genres'] = genres_record.to_dict(orient='index')

        return response_message, 200

# -- IMDB Score Prediction --
# imdb_score_parser
imdb_score_parser = reqparse.RequestParser()
imdb_score_parser.add_argument('director_facebook_likes', type=int, help="Number of Facebook Likes for Director", required=True)
imdb_score_parser.add_argument('actor_1_facebook_likes', type=int, help="Number of Facebook likes for Actor 1", required=True)
imdb_score_parser.add_argument('actor_2_facebook_likes', type=int, help="Number of Facebook likes for Actor 2", required=False)
imdb_score_parser.add_argument('actor_3_facebook_likes', type=int, help="Number of Facebook likes for Actor 3", required=False)
imdb_score_parser.add_argument('budget', type=int, help="Budget Amount", required=True)

@api.route('/imdb_score_prediction', doc={
    "description": "Endpoint which returns an IMDB score prediction for a given director name, at least one actor name and a given movie budget amount."
})
class IMDBScorePredictor(Resource):
    @api.doc('get_imdb_score_prediction')
    @api.expect(imdb_score_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collections not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global analytics
        analytics['score predictor'] += 1
        args = imdb_score_parser.parse_args()
        director_facebook_likes = args['director_facebook_likes']
        actor_1_facebook_likes = args['actor_1_facebook_likes']
        actor_2_facebook_likes = args['actor_2_facebook_likes']
        actor_3_facebook_likes = args['actor_3_facebook_likes']
        budget = args['budget']
        

        return {
            'movie_prediction_score': predict_score(director_facebook_likes,actor_1_facebook_likes,actor_2_facebook_likes,actor_3_facebook_likes,budget)
        }, 200

# -- Keywords --
# keyword_parser
keyword_parser = reqparse.RequestParser()
keyword_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
keyword_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/keywords', doc={
    "description": "Endpoint which retrieves all the keywords ever used to classify IMDB movies."
})
class Keywords(Resource):
    @api.doc('get_keywords')
    @api.expect(keyword_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collections not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global keywordsDF
        global analytics
        analytics['keywords'] += 1
        keywords_record = keywordsDF
        args = keyword_parser.parse_args()
        keywords_record, response_message, response_code = pagination(request, args, keywords_record)

        if keywords_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(keywords_record.index) == 1):
            response_message['keyword'] = keywords_record.to_dict(orient='index')
        else :
            response_message['keywords'] = keywords_record.to_dict(orient='index')

        return response_message, 200

# -- Movie --
# movie_parser
movie_parser = reqparse.RequestParser()
movie_parser.add_argument('name', type=str, help="Name of the movie queried.")
movie_parser.add_argument('actor', type=str, help="Name of the actor(s) in the movie.") # Multiple actors (union / intersection ?)
movie_parser.add_argument('director', type=str, help="Name of the director of the movie.")
movie_parser.add_argument('screenwriter', type=str, help="Name of the screenwriter of the movie.")
movie_parser.add_argument('keyword', type=str, help="Movie keywords.")
movie_parser.add_argument('genre', type=str, help="Movie genres.")
movie_parser.add_argument('budget', type=int, help="Movie budget.")
movie_parser.add_argument('revenue', type=int, help="Movie revenue.")
movie_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
movie_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/movies', doc={
    "description": "Endpoint which gets all movies and each of their corresponding information, or accepts parameters to refine the list of movies returned."
})
class Movies(Resource):
    @api.doc('get_all_movies')
    @api.expect(movie_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global movieDF
        global analytics
        analytics['movies'] += 1
        movie_record = movieDF
        expr = '(?=.*{})'
        args = movie_parser.parse_args()

        if 'name' in args and args['name'] is not None:
            words = args['name'].lower().strip('\'').strip('\"')
            movie_record = movie_record[movie_record["title"].str.contains(words) == True]

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
            movie_record = movie_record[movie_record["budget"] <= args['budget']]

        if 'revenue' in args and args['revenue'] is not None:
            movie_record = movie_record[movie_record["revenue"] >= args['revenue']]

        movie_record, response_message, response_code = pagination(request, args, movie_record)

        if movie_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(movie_record.index) == 1):
            response_message['movie'] = movie_record.to_dict(orient='index')
        else :
            response_message['movies'] = movie_record.to_dict(orient='index')

        return response_message, 200


# -- Specific Movie --
@api.route('/movies/<int:movie_id>', doc={
    "description": "Endpoint which gets a specific movie and their corresponding information based on a unique id number."
})
class SpecificMovie(Resource):
    @api.doc('get_specific_movie')
    @api.response(200, 'Success. Collection entry retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collection.')
    @api.response(403, 'Forbidden access to collection.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self, movie_id):
        global analytics
        analytics['specific movie'] += 1
        if not movieDF.index.isin([movie_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404

        movie_record = movieDF.iloc[[movie_id]]


        return {
            'movie': movie_record.to_dict(orient='index')
        }, 200


# -- Writers --
# writer_parser
writer_parser = reqparse.RequestParser()
writer_parser.add_argument('name', type=str, help="Name of the screenwriter queried.")
writer_parser.add_argument('offset', type=int, help="An integer indicating the distance between the first record and the input offset record.\nDefault value: 0.")
writer_parser.add_argument('limit', type=int, help="Number of results returned per query.\nDefault value: 20 records.")

@api.route('/screenwriters', doc={
    "description": "Endpoint which gets all screenwriters and each of their corresponding information, or accepts parameters to refine the list of screenwriters returned."
})
class Screenwriter(Resource):
    @api.doc('get_screenwriters')
    @api.expect(writer_parser)
    @api.response(200, 'Success. Collection entries retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collections.')
    @api.response(403, 'Forbidden access to collections.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self):
        global screenwriterDF
        global analytics
        analytics['screenwriters'] += 1

        args = writer_parser.parse_args()
        writer_record = screenwriterDF
        if 'name' in args and args['name'] is not None:
            writer_name = args['name'].lower().strip('\'').strip('\"')
            writer_record = writer_record[writer_record['writer_name'].str.contains(writer_name) == True]

            # OLD
            # q = 'writer_name == \'' + writer_name + '\''
            # writer_record = screenwriterDF.query(q)

        writer_record, response_message, response_code = pagination(request, args, writer_record)

        if writer_record.empty:
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404
        elif response_code != 200:
            return response_message, response_code

        if(len(writer_record.index) == 1):
            response_message['writer'] = writer_record.to_dict(orient='index')
        else :
            response_message['writers'] = writer_record.to_dict(orient='index')

        return response_message, 200

# -- Specific Writer --
@api.route('/screenwriters/<int:screenwriter_id>', doc={
    "description": "Endpoint which gets a specific screenwriter and their corresponding information based on a unique id number."
})
class Screenwriter(Resource):
    @api.doc('get_specific_screenwriter')
    @api.response(200, 'Success. Collection entry retrieved.')
    @api.response(400, 'Bad request. Incorrect syntax.')
    @api.response(401, 'Unauthorised access to collection.')
    @api.response(403, 'Forbidden access to collection.')
    @api.response(404, 'Not found. Collection not found.')
    @api.response(500, 'Internal Service Error.')
    def get(self, screenwriter_id):
        global analytics
        analytics['specific screenwriter'] += 1
        if not screenwriterDF.index.isin([screenwriter_id]).any():
            return {
                'error': 'Not Found',
                'message': 'Collection was not found'
            }, 404


        screenwriter_record = screenwriterDF.iloc[[screenwriter_id]]


        return {
            'screenwriter': screenwriter_record.to_dict(orient='index')
        }, 200



# Handles query pagination
def pagination(request, args, record):

        offset = 0
        limit = 20
        if 'offset' in args and args['offset'] is not None and args['offset'] > 0:
            offset = args['offset']
        elif 'offset' in args and args['offset'] is not None and args['offset'] < 0:
            return record, {
                'error': "Bad request.",
                'message': "Invalid offset input. Offset should be >= 0."
            }, 400

        if 'limit' in args and args['limit'] is not None and args['limit'] > 0:
            limit = args['limit']
        elif 'limit' in args and args['limit'] is not None and args['limit'] < 0:
            return record, {
                'error': "Bad request.",
                'message': "Invalid limit input. Limit should be >= 0."
            }, 400

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
        }, 200


# APP ROUTING FUNCTIONS
@app.route('/application/home', methods=['GET'])
def index():

    return render_template('index.html', directors=list(directorDF['director_name']),
                                         actors=list(actorDF['actor_name']),
                                         genres=list(genresDF['genres']))

@app.route('/imdbscoreprediction_ui', methods=['GET'])
def imdbscoreprediction_ui():

    return render_template('imdbscoreprediction.html', directors=list(directorDF['director_name']),
                                         actors=list(actorDF['actor_name']),
                                         genres=list(genresDF['genres']))

@app.route('/genres_ui', methods=['GET'])
def genres_ui():

    return render_template('genres.html', genres=list(genresDF['genres']))

@app.route('/directors_ui', methods=['GET'])
def directors_ui():

    return render_template('directors.html')

@app.route('/actors_ui', methods=['GET'])
def actors_ui():

    return render_template('actors.html')

@app.route('/keywords_ui', methods=['GET'])
def keywords_ui():

    return render_template('keywords.html')

@app.route('/movies_ui', methods=['GET'])
def movies_ui():

    return render_template('movies.html')

@app.route('/screenwriters_ui', methods=['GET'])
def screenwriters_ui():

    return render_template('screenwriters.html')



if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

#import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
#from matplotlib.lines import Line2D


def process_dataset1(): # USE THIS ONE FOR ML MAYBE
    df = pd.read_csv("datasets/movie_metadata.csv")
    df['movie_title'] = df['movie_title'].str.strip()
    df['movie_title'] = df['movie_title'].str.lower()

    
    df = df.drop(["color", "duration", "num_critic_for_reviews", "movie_imdb_link", "aspect_ratio"], axis=1)    # WHAT SHOULD WE DROP?    
    
    df = df.replace(0,float("NaN"))
    df = df.dropna()
    # df['title_year'] = df['title_year'].astype(int)
    df = df.set_index('movie_title')
    # print(df.columns.values)
    # print(df.loc[['avatar']].to_string())
    # print(df.head(5))
    
    return df


#MERGING 2 DATASETS AND GETTING RID OF ALL THE ARRAYS/JSON TO WORDS SEPARATED BY |
#CREATING MOVIES BY ___ LISTS FOR USE BY API

def process_dataset2(): # USE THIS ONE JUST FOR API DATA POINTS
    df=pd.read_csv("datasets/tmdb_5000_movies.csv")
    df1=pd.read_csv("datasets/tmdb_5000_credits.csv")


    df = df.drop(["title"], axis=1)
    df = df.set_index('id')
    df1 = df1.set_index('movie_id')
    result = pd.concat([df, df1], axis=1, join='inner')
    df = df.replace(0,float("NaN"))
    result = result.dropna()
    print(len(result))
    # # dropped production_companies and crew - do we want this?
    #     "original_title", "homepage", "release_date", "production_countries", "original_language", "runtime", "spoken_languages", "vote_count", "overview", "status", "tagline"
    result = result[['title', 'budget', 'revenue', 'cast', 'genres', 'keywords', 'popularity', 'revenue']]


    titlelist = np.array(result['title'])
    genreslist = np.array(result['genres'])
    keywordslist = np.array(result['keywords'])
    castlist = np.array(result['cast'])

    print(result.columns.values)
    moviesbygenre = {}  # list of movies by genre {"genre1" : ["movie1", "movie2"]}
    modifiedGenres = [] # modified genre list separated by | for dataframe
    moviesbykeywords = {}  # list of movies by genre {"genre1" : ["movie1", "movie2"]}
    modifiedKeywords = [] # modified genre list separated by | for dataframe
    newCast = []
    actorlist = {}
    actresslist = {}

    for i in range(len(titlelist)):
        title = titlelist[i].lower()
        titlelist[i] = title
        genres = genreslist[i]
        keywords = keywordslist[i]
        cast = castlist[i]
        genresstr = ""
        keywordstr = ""
        caststr = ""
        for genre in json.loads(genres):
            name = genre['name'].lower()
            if name not in moviesbygenre:
                moviesbygenre[name] = []
            moviesbygenre[name].append(title)
            genresstr += name + "|"
        modifiedGenres.append(genresstr[:-1])
        for keyword in json.loads(keywords):
            name = keyword['name'].lower()
            if name not in moviesbykeywords:
                moviesbykeywords[name] = []
            moviesbykeywords[name].append(title)
            keywordstr += name + "|"
        modifiedKeywords.append(keywordstr[:-1])
        for actor in json.loads(cast):
            if actor['order'] > 10: continue # only taking the top 10 actors per movie
            name = actor['name'].lower()
            caststr += name + "|"
            if actor['gender'] == 2:
                if name not in actorlist:
                    actorlist[name] = []
                actorlist[name].append(title)
            else :
                if name not in actresslist:
                    actresslist[name] = []
                actresslist[name].append(title)
        newCast.append(caststr[:-1])
    result = result.drop(['genres', "keywords", "cast", "title"], axis=1)
    result["genres"] = modifiedGenres
    result["keywords"] = modifiedKeywords
    result["cast"] = newCast
    result["title"] = titlelist

    # ######################

    # # print(result.columns.values)

    # # print(result.columns.values)
    # # print(result.head(5).to_string())

    return moviesbygenre, moviesbykeywords, actorlist, actresslist, result
    

if __name__ == '__main__':
    process_dataset1()
    moviesbygenre, moviesbykeywords, actorlist, actresslist, result = process_dataset2()
    print("======================== ACTION =========================")
    # print(moviesbygenre['Action'])
    print("======================== SPY ======================")
    print(moviesbykeywords['spy'])
    print("======================== ZOE SALDANA ======================")
    print(actresslist['zoe saldana'])
    print("===================== FIRST 3 RESULTS ===================")
    print(result.head(3).to_string())
    # print(moviesbykeywords)
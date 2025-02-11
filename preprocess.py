#import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
#from matplotlib.lines import Line2D


def process_dataset_forML(df): # USE THIS ONE FOR ML MAYBE
    # df = pd.read_csv("datasets/movie_metadata.csv")
    # df['movie_title'] = df['movie_title'].str.strip()
    # df['movie_title'] = df['movie_title'].str.lower()
    columns_to_drop = [
        'color',
        'director_name',
        'duration',
        'actor_2_name',
        'gross',
        'genres',
        'actor_1_name',
        'movie_title',
        'actor_3_name',
        'facenumber_in_poster',
        'plot_keywords',
        'movie_imdb_link',
        'language',
        'country',
        'content_rating',
        'title_year',
        'aspect_ratio',
        'num_critic_for_reviews',
        'num_voted_users',
        'num_user_for_reviews',
        'cast_total_facebook_likes',
        'movie_facebook_likes'
    ]

    df = df.drop(columns_to_drop, axis=1)

    df = df[['director_facebook_likes', 
            'actor_1_facebook_likes', 
            'actor_2_facebook_likes', 
            'actor_3_facebook_likes',  
            'budget',
            'imdb_score']]
    df = df.replace(0,float("NaN"))
    df = df.dropna(axis=0, how='any')
    df = df.astype(int)
    
    return df


#MERGING 2 DATASETS AND GETTING RID OF ALL THE ARRAYS/JSON TO WORDS SEPARATED BY |
#CREATING MORE DFs FOR USE BY API

def process_dataset2(): # USE THIS ONE JUST FOR API DATA POINTS
    df  = pd.read_csv("datasets/tmdb_5000_movies.csv")
    df1 = pd.read_csv("datasets/tmdb_5000_credits.csv")
    df2 = pd.read_csv("datasets/movie_metadata.csv")
    # merging datasets
    df      = df.drop(["title"], axis=1) 
    df      = df.set_index('id')
    df1     = df1.set_index('movie_id')
    result  = pd.concat([df, df1], axis=1, join='inner')

    df2_columns = ['director_name', 'director_facebook_likes', 'actor_1_name', 'actor_1_facebook_likes', 'actor_2_name', 'actor_2_facebook_likes', 'actor_3_name', 'actor_3_facebook_likes']
    df2 = df2[df2_columns]
    df2 = df2.replace(0,float("NaN"))
    df2 = df2.dropna(axis=0, how='any')

    result_columns          = ['title', 'cast', 'crew', 'genres', 'keywords', 'budget', 'revenue', 'popularity', 'vote_average']
    result                  = result[result_columns]

    result  = result.replace(0,float("NaN"))
    result  = result.dropna()

    # columns 
    titlelist       = np.array(result['title'])
    genreslist      = np.array(result['genres'])
    keywordslist    = np.array(result['keywords'])
    castlist        = np.array(result['cast'])
    crewlist        = np.array(result['crew'])
    
    # modified lists separated by | for dataframe to add to df
    modifiedGenres = [] 
    modifiedKeywords = [] 
    modifiedDirector = []
    modifiedScreenwriter = []
    modifiedCast = []

    # For creating new dataframes
    keyword_resource = []
    genre_resource = []
    actors_resource = {}
    # genders_resource = []
    directors_resource = []
    writers_resource = []

    for i in range(len(titlelist)):
        title           = titlelist[i].lower().strip()
        titlelist[i]    = title
        genres          = genreslist[i]
        keywords        = keywordslist[i]
        cast            = castlist[i]
        crew            = crewlist[i]

        # Clean String
        genresstr = ""
        keywordstr = ""
        caststr = ""
        directorstr = ""
        writerstr = ""

        # Loop for Director and Screenwriters
        for crew_member in json.loads(crew):
            job = crew_member['job']
            name = crew_member['name'].lower().strip()
            if name == "" : continue
            if(job == 'Director'):
                directorstr += name + "|"
                if name not in directors_resource:
                    directors_resource.append(name)
            if(job == 'Screenplay'):
                writerstr += name + "|"
                if name not in directors_resource:
                    writers_resource.append(name)

        # Loop for Genres
        for genre in json.loads(genres):
            name = genre['name'].lower().strip()
            if name == "" : continue
            if name not in genre_resource:
                genre_resource.append(name)
            genresstr += name + "|"

        # Loop for Keywords
        for keyword in json.loads(keywords):
            name = keyword['name'].lower().strip()
            if name == "" : continue
            if name not in keyword_resource:
                keyword_resource.append(name)
            keywordstr += name + "|"

        # Loop for Cast
        for actor in json.loads(cast):
            if actor['order'] > 10: continue # only taking the top 10 actors per movie
            name = actor['name'].lower().strip()
            if name == "" : continue
            if name not in actors_resource:
                if actor['gender'] == 2:
                    actors_resource[name] = 'M'
                    # genders_resource.append('M')
                elif actor['gender'] == 1 :
                    actors_resource[name] = 'F'
                    # genders_resource.append('F')
                else :
                    actors_resource[name] = 'O'
                    # genders_resource.append('O')
            caststr += name + "|"

        # Append for df
        modifiedDirector.append(directorstr[:-1])
        modifiedScreenwriter.append(writerstr[:-1])
        modifiedGenres.append(genresstr[:-1])        
        modifiedKeywords.append(keywordstr[:-1])
        modifiedCast.append(caststr[:-1])

    actor_fb_likes = {}
    director_fb_likes = {}
    for i in range(len(df2.index)) :
        name = str(df2['actor_1_name'].iloc[i])
        name = name.lower().strip()
        if name == "" : continue
        if name not in actor_fb_likes :
            actor_fb_likes[name] = df2['actor_1_facebook_likes'].iloc[i]
        name = str(df2['actor_2_name'].iloc[i])
        name = name.lower().strip()
        if name not in actor_fb_likes :
            actor_fb_likes[name] = df2['actor_2_facebook_likes'].iloc[i]
        name = str(df2['actor_3_name'].iloc[i])
        name = name.lower().strip()
        if name not in actor_fb_likes :
            actor_fb_likes[name] = df2['actor_3_facebook_likes'].iloc[i]
        name = str(df2['director_name'].iloc[i])
        name = name.lower().strip()
        if name not in director_fb_likes :
            director_fb_likes[name] = df2['director_facebook_likes'].iloc[i]
        
    # Creating the Dataframes
    genderdf = pd.Series(actors_resource, name='gender')
    actorlikesdf = pd.Series(actor_fb_likes, name='facebook_likes')    
    actorlikesdf = actorlikesdf.to_frame()
    actorlikesdf.index.name = 'actor_name'
    genderdf = genderdf.to_frame()
    genderdf.index.name = 'actor_name'
    actordf  = pd.concat([genderdf, actorlikesdf], axis=1, join='inner')
    actordf = actordf.reset_index()
    actordf = actordf.drop_duplicates()
    actordf = actordf.sort_values(by=["actor_name"])
    actordf = actordf.reset_index()
    actordf = actordf.drop(['index'], axis=1)
    keyworddf = pd.DataFrame(keyword_resource, columns=['keywords'])
    keyworddf = keyworddf.drop_duplicates()
    keyworddf = keyworddf.sort_values(by=["keywords"])
    keyworddf = keyworddf.reset_index()
    keyworddf = keyworddf.drop(['index'], axis=1)

    genredf = pd.DataFrame(genre_resource, columns=['genres'])
    genredf = genredf.drop_duplicates()
    genredf = genredf.sort_values(by=["genres"])
    genredf = genredf.reset_index()
    genredf = genredf.drop(['index'], axis=1)

    directordf = pd.DataFrame(directors_resource, columns=['director_name'])
    directorlikesdf = pd.Series(director_fb_likes, name='facebook_likes')
    directorlikesdf = directorlikesdf.to_frame()
    directorlikesdf.index.name = 'director_name'
    directorlikesdf = directorlikesdf.reset_index()
    directordf = directordf.merge(directorlikesdf, on='director_name', how='inner', suffixes=('_1', '_2'))
    directordf = directordf.drop_duplicates()
    directordf = directordf.sort_values(by=["director_name"])
    directordf = directordf.reset_index()
    directordf = directordf.drop(['index'], axis=1)

    screenwriterdf = pd.DataFrame(writers_resource, columns=['writer_name'])
    screenwriterdf = screenwriterdf.drop_duplicates()
    screenwriterdf = screenwriterdf.sort_values(by=["writer_name"])
    screenwriterdf = screenwriterdf.reset_index()
    screenwriterdf = screenwriterdf.drop(['index'], axis=1)

    result                  = result.drop(['genres', "keywords", "cast", "title", "crew"], axis=1)
    result["title"]         = titlelist
    result["directors"]     = modifiedDirector
    result["screenwriters"] = modifiedScreenwriter
    result["cast"]          = modifiedCast
    result["genres"]        = modifiedGenres
    result["keywords"]      = modifiedKeywords
    result                  = result.reset_index(drop=True)
    result_columns          = ['title', 'cast', 'directors', 'screenwriters', 'genres', 'keywords', 'budget', 'revenue', 'popularity', 'vote_average']
    result                  = result[result_columns]

    actor_average = actordf['facebook_likes'].mean(axis=0)

    return actor_average, directordf, screenwriterdf, actordf, keyworddf, genredf, result
    

if __name__ == '__main__':
    # process_dataset1()
    actor_average, directordf, screenwriterdf, actordf, keyworddf, genredf, result = process_dataset2()
    # print(genredf)
    # print(actordf)
    # print(keyworddf)
    # print(screenwriterdf)
    # print(directordf)
    # print(result)
    # print("======================== ACTION =========================")
    # print(moviesbygenre['Action'])
    # print("======================== SPY ======================")
    # expr = '(?=.*{})'
    # words = ['spy']
    # print(result[result["keywords"].str.contains(r''.join(expr.format(w) for w in words), regex=True)])
    # print("======================== ZOE SALDANA ======================")
    # words = ['zoe saldana']
    # print(result[result["cast"].str.contains(r''.join(expr.format(w) for w in words), regex=True)])
    # print(actresslist['zoe saldana'])
    # print("===================== FIRST 3 RESULTS ===================")
    # print(result.head(3).to_string())
    # print(moviesbykeywords)
    # print(process_dataset_forML(pd.read_csv("datasets/movie_metadata.csv")).columns)
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
    result = result.replace(0,float("NaN"))
    result = result.dropna()
    # print(len(result))
    # # dropped production_companies and crew - do we want this?
    #     "original_title", "homepage", "release_date", "production_countries", "original_language", "runtime", "spoken_languages", "vote_count", "overview", "status", "tagline"
    
    # print(result['crew'])

    result = result[['title', 'budget', 'revenue', 'cast', 'genres', 'keywords', 'popularity', 'revenue', 'crew']]


    titlelist = np.array(result['title'])
    genreslist = np.array(result['genres'])
    keywordslist = np.array(result['keywords'])
    castlist = np.array(result['cast'])
    crewlist = np.array(result['crew'])
    


    # modified lists separated by | for dataframe to add to df
    modifiedGenres = [] 
    modifiedKeywords = [] 
    modifiedDirector = []
    modifiedScreenwriter = []
    modifiedCast = []

    # For creating new dataframes
    keyword_resource = []
    genre_resource = []
    actors_resource = []
    directors_resource = []
    writers_resource = []



    for i in range(len(titlelist)):
        title = titlelist[i].lower()
        titlelist[i] = title
        genres = genreslist[i]
        keywords = keywordslist[i]
        cast = castlist[i]
        crew = crewlist[i]
        genresstr = ""
        keywordstr = ""
        caststr = ""
        directorstr = ""
        writerstr = ""
        for crew_member in json.loads(crew):
            job = crew_member['job']
            name = crew_member['name'].lower().strip()
            if(job == 'Director'):
                directorstr += name + "|"
                if name not in directors_resource:
                    directors_resource.append(name)
            if(job == 'Screenplay'):
                writerstr += name + "|"
                if name not in directors_resource:
                    writers_resource.append(name)
        modifiedDirector.append(directorstr[:-1])
        modifiedScreenwriter.append(writerstr[:-1])
   
        for genre in json.loads(genres):
            name = genre['name'].lower().strip()
            if name not in genre_resource:
                genre_resource.append(name)
            genresstr += name + "|"
        modifiedGenres.append(genresstr[:-1])
        for keyword in json.loads(keywords):
            name = keyword['name'].lower().strip()
            if name not in keyword_resource:
                keyword_resource.append(name)
            keywordstr += name + "|"
        modifiedKeywords.append(keywordstr[:-1])
        for actor in json.loads(cast):
            if actor['order'] > 10: continue # only taking the top 10 actors per movie
            name = actor['name'].lower().strip()
            
            caststr += name + "|"
            if name not in actors_resource:
                if actor['gender'] == 2:
                    actors_resource.append([name, "M"])
                elif actor['gender'] == 1 :
                    actors_resource.append([name, "F"])
                else :
                    actors_resource.append([name, "O"])
        modifiedCast.append(caststr[:-1])


    keyword_resource.sort()
    genre_resource.sort()
    directors_resource.sort()
    writers_resource.sort()
    # print(directors_resource)

    actordf = pd.DataFrame(actors_resource, columns=['actor_name', 'gender'])

    actordf = actordf.drop_duplicates()
    actordf = actordf.sort_values(by=["actor_name"])


    keyworddf = pd.DataFrame(keyword_resource, columns=['keywords'])
    genredf = pd.DataFrame(genre_resource, columns=['actor_name'])
    directordf = pd.DataFrame(directors_resource, columns=['director'])
    screenwriterdf = pd.DataFrame(writers_resource, columns=['writer'])
    
    result = result.drop(['genres', "keywords", "cast", "title", "crew"], axis=1)
    result["genres"] = modifiedGenres
    result["keywords"] = modifiedKeywords
    result["cast"] = modifiedCast
    result["title"] = titlelist
    result["director"] = modifiedDirector
    result["screenwriter"] = modifiedScreenwriter

    # # print(result.columns.values)

    # # print(result.columns.values)
    # # print(result.head(5).to_string())

    return directordf, screenwriterdf, actordf, keyworddf, genredf, result
    

if __name__ == '__main__':
    process_dataset1()
    directordf, screenwriterdf, actordf, keyworddf, genredf, result = process_dataset2()
    print(genredf)
    print(actordf)
    print(keyworddf)
    print(screenwriterdf)
    print(directordf)
    print(result)
    print("======================== ACTION =========================")
    # print(moviesbygenre['Action'])
    print("======================== SPY ======================")
    expr = '(?=.*{})'
    words = ['spy']
    print(result[result["keywords"].str.contains(r''.join(expr.format(w) for w in words), regex=True)])
    print("======================== ZOE SALDANA ======================")
    words = ['zoe saldana']
    print(result[result["cast"].str.contains(r''.join(expr.format(w) for w in words), regex=True)])
    
    # print(actresslist['zoe saldana'])
    print("===================== FIRST 3 RESULTS ===================")
    # print(result.head(3).to_string())
    # print(moviesbykeywords)
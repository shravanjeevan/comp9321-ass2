import pandas as pd
import numpy as np
import json
from sklearn.metrics import confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.utils import shuffle
from sklearn.metrics import precision_score, accuracy_score, recall_score
import pickle
from preprocess import process_dataset_forML

def pickle_model(model,filename):
    f = open('models/'+filename,'wb')
    pickle.dump(model, f, -1)
    f.close() 

def training():
    df = pd.read_csv("datasets/movie_metadata.csv")
    df = process_dataset_forML(df)
    df = shuffle(df)

    split_percentage = 0.75
    X = df.drop('imdb_score', axis=1).values
    y = df['imdb_score'].values
    split_point = int(len(X) * split_percentage)
    movie_X_train = X[:split_point]
    movie_y_train = y[:split_point]
    movie_X_test = X[split_point:]
    movie_y_test = y[split_point:]

    # training a classifier
    knn = KNeighborsClassifier()
    knn.fit(movie_X_train, movie_y_train)

    # predictions
    predictions = knn.predict(movie_X_test)

    # representations of prediction
    confusion_matrix(movie_y_test, predictions)

    # accuracy
    print(accuracy_score(movie_y_test, predictions))

    # dump model to file
    pickle_model(knn, "Knn")

def predict_score(i_director_facebook_likes, i_actor_1_facebook_likes, i_actor_2_facebook_likes, i_actor_3_facebook_likes,  i_budget):
    # values that need to be provided are: num_critic_for_reviews, director_facebook_likes, actor_1_facebook_likes, num_voted_users, cast_total_facebook_likes, num_user_for_reviews, budget, actor_2_facebook_likes, movie_facebook_likes
    # num_critic_for_reviews = 200
    director_facebook_likes = i_director_facebook_likes
    actor_1_facebook_likes = i_actor_1_facebook_likes
    # num_voted_users = 80000
    actor_2_facebook_likes = i_actor_2_facebook_likes
    # num_user_for_reviews = 5000
    actor_3_facebook_likes = i_actor_3_facebook_likes
    # imdb_score = ?
    budget = i_budget

    movie_X = np.array([[director_facebook_likes, actor_1_facebook_likes, actor_2_facebook_likes, actor_3_facebook_likes, budget]])

    model = pickle.load(open("./models/Knn", "rb"))

    prediction = model.predict(movie_X)

    # return prediction[0]
    return np.array2string(prediction)

if __name__ == '__main__':
    training()
######################################################################################
# 1.Perform data preprocessing
######################################################################################

import pandas as pd
pd.set_option('display.max_columns', 5)
def create_user_movie_df():
    movie = pd.read_csv("datasets/movie_lens_dataset/movie.csv")
    rating = pd.read_csv("datasets/movie_lens_dataset/rating.csv")
    df = movie.merge(rating, how="left", on="movieId")
    comment_counts = pd.DataFrame(df["title"].value_counts())
    rare_movies = comment_counts[comment_counts["title"] <= 1000].index
    common_movies = df[~df["title"].isin(rare_movies)]
    user_movie_df = common_movies.pivot_table(index=["userId"], columns=["title"], values="rating")
    user_movie_df.head()
    return user_movie_df

user_movie_df = create_user_movie_df()

#random_user = int(pd.Series(user_movie_df.index).sample(1, random_state=45).values)
random_user = 108170

######################################################################################
# 2.Determine the movies watched by the user to be suggested
######################################################################################

random_user = 108170
random_user_df = user_movie_df[user_movie_df.index == random_user]
movies_watched = random_user_df.columns[random_user_df.notna().any()].tolist()
len(movies_watched)
user_movie_df.loc[user_movie_df.index == random_user, user_movie_df.columns == "Stargate (1994)"]

######################################################################################
# 3.Access the data and IDs of other users watching the same movies.
######################################################################################

movies_watched_df= user_movie_df[movies_watched]
user_movie_count = movies_watched_df.T.notnull().sum()
user_movie_count = user_movie_count.reset_index()
user_movie_count.columns = ["userId", "movie_count"]
# user_movie_count[user_movie_count["movie_count"] > 20].sort_values(by="movie_count", ascending = False)
perc = len(movies_watched) * 70 / 100
user_movie_count[user_movie_count["movie_count"] == 33].count()
# users_same_movies = user_movie_count[user_movie_count["movie_count"] > 20]["userId"]
users_same_movies = user_movie_count[user_movie_count["movie_count"] > perc]["userId"]
users_same_movies.head()
users_same_movies.count()

######################################################################################
# 4.Identify the users who are most similar to the user for whom the movie will be recommended
######################################################################################
# 1. Combine random user and other users' data
# 2. Create correlation df
# 3. Find most similar users(top users)

final_df = pd.concat([movies_watched_df[movies_watched_df.index.isin(users_same_movies)], random_user_df[movies_watched]])
final_df.head()
final_df.T.corr().head()

corr_df = final_df.T.corr().unstack().sort_values().drop_duplicates()
corr_df = pd.DataFrame(corr_df, columns=["corr"])
corr_df.index.names = ['user_id_1', 'user_id_2']
corr_df = corr_df.reset_index()

top_users = corr_df[(corr_df["user_id_1"] == random_user) & (corr_df["corr"] >= 0.70)][["user_id_2", "corr"]].reset_index(drop=True)
top_users.sort_values(by='corr', inplace=True, ascending=False)
top_users.rename(columns={"user_id_2": "userId"}, inplace=True)

rating = pd.read_csv('datasets/movie_lens_dataset/rating.csv')
top_users_ratings = top_users.merge(rating[["userId", "movieId", "rating"]], how="inner")
top_users_ratings = top_users_ratings[top_users_ratings["userId"] != random_user]

######################################################################################
# 5.Calculate the Weighted Average Recommendation Score and keep the first 5 movies
######################################################################################

top_users_ratings['weighted_rating'] = top_users_ratings['corr'] * top_users_ratings['rating']
top_users_ratings.head()

recommendation_df = top_users_ratings.groupby('movieId').agg({"weighted_rating": "mean"})
recommendation_df.reset_index(inplace=True)
recommendation_df[["movieId"]].nunique()

movies_to_be_recommend = recommendation_df[recommendation_df["weighted_rating"] > 3.6].sort_values("weighted_rating", ascending=False)

movie = pd.read_csv('datasets/movie_lens_dataset/movie.csv')
movies_to_be_recommend.head(5).merge(movie[["movieId", "title"]])

######################################################################################
# 6.Make an item-based suggestion based on the name of the movie that the user has watched last and gave the highest score
# Make 10 suggesstions
# 5 suggestions user-based
# 5 suggestions item-based

######################################################################################

movie = pd.read_csv('datasets/movie_lens_dataset/movie.csv')
rating = pd.read_csv('datasets/movie_lens_dataset/rating.csv')

movie_id = rating[(rating["userId"] == random_user) & (rating["rating"] == 5.0)].sort_values(by="timestamp", ascending=False)["movieId"][:1].values[0]


# Item-Based
df = movie.merge(rating, how="left", on="movieId")
comment_counts = pd.DataFrame(df["title"].value_counts())
rare_movies = comment_counts[comment_counts["title"] <= 1000].index
common_movies = df[~df["title"].isin(rare_movies)]
user_movie_df = common_movies.pivot_table(index=["userId"], columns=["title"], values="rating")

movie_name = movie[movie["movieId"] == movie_id]["title"].values[0]
movie_name = user_movie_df[movie_name]
movies_from_item_based = user_movie_df.corrwith(movie_name).sort_values(ascending=False)
movies_from_item_based[1:6].index


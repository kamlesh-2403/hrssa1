
users_file = 'https://static.turi.com/datasets/millionsong/10000.txt'
songs_file = 'https://static.turi.com/datasets/millionsong/song_data.csv'

song_df_1 = pd.read_table(users_file, header = None)
song_df_1.columns = ['user_id', 'song_id', 'listen_count']

song_df_2 =  pd.read_csv(songs_file)

#song_df_1.head()

#song_df_2.head()

#print("artist =", len(song_df_2.artist_name.unique()))
#print("title =", len(song_df_2.title.unique()))

song_id_le = preprocessing.LabelEncoder()
song_id_le.fit(song_df_2.song_id)
song_df_2.song_id = song_id_le.transform(song_df_2.song_id)
song_df_1.song_id = song_id_le.transform(song_df_1.song_id)

user_id_le = preprocessing.LabelEncoder()
song_df_1.user_id = user_id_le.fit_transform(song_df_1.user_id)

song_df = pd.merge(song_df_1, song_df_2.drop_duplicates(['song_id']), on="song_id", how="left")

#song_df.describe(include=[np.int, np.object])

song_df = song_df.fillna(value=0)


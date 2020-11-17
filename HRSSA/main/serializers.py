from rest_framework import serializers
from django.contrib.auth.hashers import make_password
import re
from .models import User,ForgotPassword,Otp,Song,SearchHistory,Artist,Favourites,Playlist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate_password(self, str) -> str:
        """ A function to save the password for storing the values """
        return make_password(str)

class UserDataSerializer(serializers.ModelSerializer):
    artist_preference = ArtistSerializer(many = True)
    class Meta:
        model = User
        fields = '__all__'

class ForgotPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForgotPassword
        fields= '__all__'

class OtpSerializer(serializers.ModelSerializer):

    class Meta:
        model = Otp
        fields = '__all__'

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'


class FavouritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourites
        fields = '__all__'

class FavouritesListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    song = SongSerializer(many = True)
    class Meta:
        model = Favourites
        fields = '__all__'

class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = '__all__'

class PlaylistListSerializer(serializers.ModelSerializer):
    user = UserSerializer
    class Meta:
        model = Playlist
        fields = '__all__'

class PlaylistSongsListSerializer(serializers.ModelSerializer):
    song = SongSerializer(many =True)
    class Meta:
        model = Playlist
        fields = '__all__'

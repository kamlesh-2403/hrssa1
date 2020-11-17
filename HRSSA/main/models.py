from django.db import models
import uuid  # for generating uuid
import datetime
from .managers import UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.fields import ArrayField, JSONField

LANGUAGE = (("English","English"),("Hindi","Hindi"))
GENRE = (("Big Band","Big Band"),("Blues Contemporary","Blues Contemporary"), ("Seasonal","Seasonal"),("Country Traditional","Country Traditional"), ("Dance","Dance"), ("Electronica","Electronica"), ("Experimental","Experimental"),("Folk International","Folk International"), ("Gospel","Gospel"), ("Grunge Emo","Grunge Emo"), ("Hip Hop Rap","Hip Hop Rap"), ("Jazz Classic","Jazz Classic"), ("Metal Alternative","Metal Alternative"),("Metal Death","Metal Death"), ("Metal Heavy","Metal Heavy"),("Pop Contemporary","Pop Contemporary"), ("Pop Indie","Pop Indie"), ("Pop Latin","Pop Latin"), ("Punk","Punk"), ("Reggae","Reggae"),("Rock Alternative","Rock Alternative"), ("Rock College","Rock College"), ("Rock Contemporary","Rock Contemporary"), ("Rock Hard","Rock Hard"), ("Rock Neo Psychedelia","Rock Neo Psychedelia"))

# base model
class BaseModel(models.Model):
    """Base ORM model"""
    # create uuid field
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # created and updated at date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # meta class
    class Meta:
        abstract = True

    # Time elapsed since creation
    def get_seconds_since_creation(self):
        """
        Find how much time has been elapsed since creation, in seconds.
        This function is timezone agnostic, meaning this will work even if
        you have specified a timezone.
        """
        return (datetime.datetime.utcnow() -
                self.created_at.replace(tzinfo=None)).seconds

class Artist(BaseModel):
    artist_name = models.CharField(max_length=1000)
    artist_image = models.URLField(null=True,blank=True)
    class Meta:
        db_table =  'artist'

    def __str__(self):
        return self.artist_name

# User model table
class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """A ORM model for Managing User and Authentication"""
    
    user_name = models.CharField(max_length=200,null=True)
    first_name = models.CharField(max_length=200,null=True)
    last_name = models.CharField(max_length=200,null=True)
    email = models.TextField(unique=True)
    mobile = models.BigIntegerField(unique=True,null =True)
    password = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender =models.CharField(max_length=100,null=True)
    profile_path = models.URLField(null=True,blank=True)
    lang_preference = models.CharField(max_length=10, choices=LANGUAGE, null=True, blank=True)
    genre_preference = ArrayField(models.CharField(max_length=40, choices=GENRE, null=True, blank=True),default=list, blank=True)
    artist_preference = models.ManyToManyField(Artist ,related_name="artist_selected", null=True, blank= True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    
    # create objs for management
    objects = UserManager()

    # SET email field as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # create a meta class
    
    class Meta:
        db_table= 'user'

class ForgotPassword(BaseModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE,default= None)
    email = models.EmailField(max_length=150,null=True, blank=True)
    mobile = models.BigIntegerField(null=True, blank=True)
    code = models.IntegerField()
    is_used = models.BooleanField(default=False)

class Otp(BaseModel):
    user = models.ForeignKey(User, related_name="otp_set_user", on_delete = models.CASCADE)
    otp_type = models.CharField(max_length = 50)
    otp_code = models.IntegerField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return str(self.otp_code)

    class Meta:
        db_table = 'OTP'

class Song(BaseModel):
    song_name = models.CharField(max_length=200)
    album_name = models.CharField(max_length=200,null=True,blank=True)
    artist_name = models.ForeignKey(Artist, on_delete= models.CASCADE)
    poster_path = models.URLField(null=True,blank=True)
    genre_name = ArrayField(models.CharField(max_length=40, choices=GENRE, null=True, blank=True), blank=True)
    
    class Meta:
        db_table =  'song'

    def __str__(self):
        return self.song_name

class SearchHistory(BaseModel):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    history_song = models.ForeignKey(Song, on_delete= models.CASCADE,null=True)
    is_hidden = models.BooleanField(default=False)

class Listing(BaseModel):
    listing_name = models.CharField(max_length=200) 
    song = models.ManyToManyField(Song,related_name="trending_songs")

class Favourites(BaseModel):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    song = models.ManyToManyField(Song,related_name="favourite_songs")

class Playlist(BaseModel):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    song = models.ManyToManyField(Song,related_name="songs_in_playlist")
    playlist_name = models.CharField(max_length=200,unique=True)
    playlist_pic =  models.URLField(null=True,blank=True)

class ListenCount(BaseModel):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    song = models.ForeignKey(Song, on_delete= models.CASCADE)
    listencount = models.BigIntegerField(unique=True,null =True)
from django.contrib import admin
from main.models import User,Song,Artist,Favourites,Playlist,ListenCount

admin.site.register(User)
admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Favourites)
admin.site.register(Playlist)
admin.site.register(ListenCount)
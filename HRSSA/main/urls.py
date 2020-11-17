from django.contrib import admin
from django.urls import path
from main import views


urlpatterns = [
    path('registeruser', views.RegisterUser.as_view()),
    path('login', views.UserLogin.as_view()),
    path('changepassword', views.ChangePassword.as_view()),
    path('forgetpasswordotp', views.ForgotPasswordOTP.as_view()),
    path('otpvalidation', views.ForgotPasswordOTPValidation.as_view()),
    path('forgotpasswordchange', views.ForgotPasswordChange.as_view()),
    path('sendotp', views.SendOtp.as_view()),
    path('validateotp', views.ValidateOtp.as_view()),

    path('viewprofile', views.ViewProfile.as_view()),
    path('editprofile', views.EditProfile.as_view()),
    path('deleteprofile/<str:pk>', views.DeleteProfile.as_view()),

    path('listselectedgenre', views.ListSelectedGenres.as_view()),
    path('addgenre', views.AddGenres.as_view()),
    path('removegenre/<str:pk>', views.RemoveGenres.as_view()),

    path('listartists',views.ListAllArtist.as_view()),
    path('listuserartists',views.ListAllUserArtist.as_view()),
    path('addartist', views.AddArtist.as_view()),
    path('removeartist', views.RemoveArtist.as_view()),

    path('listfavourites',views.ListAllFavourites.as_view()),
    path('createfavourites',views.CreateFavourites.as_view()),
    path('addfavourites', views.AddFavourites.as_view()),
    path('removefavourties', views.RemoveFavourites.as_view()),

    path('listplaylists',views.ListAllPlaylists.as_view()),
    path('createplaylists',views.CreatePlaylist.as_view()),
    path('removeplaylists', views.RemovePlaylist.as_view()),
    path('listplaylistsongs',views.ListPlaylistSongs.as_view()),
    path('addplaylistsong/<str:pk>', views.AddPlaylistSongs.as_view()),
    path('removeplaylistsong/<str:pk>', views.RemovePlaylistSongs.as_view()),
]
from django.shortcuts import render
from django.db.models import Q,Count
from random import randint
from django.contrib.auth import authenticate, login

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from rest_framework import generics, status , permissions
from django.core.mail import send_mail

from .models import User,ForgotPassword,Otp,SearchHistory,Artist,Favourites,Playlist
from .serializers import UserSerializer,ForgotPasswordSerializer,OtpSerializer,ArtistSerializer,FavouritesSerializer,FavouritesListSerializer,PlaylistListSerializer,PlaylistSerializer,PlaylistSongsListSerializer,UserDataSerializer


SENDGRID_API_KEY='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'

# Email Function
def send_email(recipient, subject, body, msg_html=None):
    message = Mail(from_email='recommenderhybrid@gmail.com',to_emails=recipient if type(recipient) is list else [recipient],subject=subject,html_content=body)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def send_otp(mobile,otp_code):
    import requests
    Otp = otp_code
    url = "https://www.fast2sms.com/dev/bulk"

    payload = "sender_id=FSTSMS&message=Your%20OTP%20is%20{}&language=english&route=p&numbers={}".format(Otp,mobile)
    headers = {
        'authorization': "Pa6ecieKEJoo9u0MtosZyjX78laUCg0enFeJKIhjyUvNnovhXZLzrDI9FCq7",
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
        }
    response = requests.request("POST", url, data=payload, headers=headers)

    return Otp

def responsedata(status, message, data=None):
    if status:
        return {"status":status,"message":message,"data":data}
    else:
        return {"status":status,"message":message,}


###   Auth Module   ###
class RegisterUser(TokenObtainPairView):
    """To register new User via email or mobile"""

    token_obtain_pair = TokenObtainPairView.as_view()

    def post(self, request, *args, **kwargs):
        if request.data['email'] == '':
            del request.data['email']

        if request.data:
            data = request.data

            if data.get('email'):
                try:
                    if User.objects.filter(email=data.get('email')).values().exists():
                        return Response(responsedata(False, "User already present"), status=status.HTTP_409_CONFLICT)
                except:
                    pass
            user_data = {"email":data.get("email"), "password": data.get("password"),"first_name" : data.get("first_name"),"last_name" : data.get("last_name"),"mobile":data.get("mobile") }
            serializer = UserSerializer(data=user_data)
    
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                tokenserializer = TokenObtainPairSerializer(data={"uuid": str(serializer.data.get("uuid")), "password":data.get("password"), "email":data.get("email")})
                if tokenserializer.is_valid(raise_exception=True):
                    data = tokenserializer.validate({"uuid": str(serializer.data.get("uuid")), "password": request.data.get("password"), "email":data.get("email")})
                tempid = serializer.data.get("uuid")
            else:
                return Response(responsedata(False, "Can't insert data"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(responsedata(True, "Data Inserted",serializer.data), status=status.HTTP_200_OK)
        else:
            return Response(responsedata(False, "No Data provided"), status=status.HTTP_400_BAD_REQUEST)

class UserLogin(TokenObtainPairView):
    """To login using email/mobile and password"""
    
    token_obtain_pair = TokenObtainPairView.as_view()

    def post(self, request, *args, **kwargs):
        if request.data.get('email'):
            try:
                user = User.objects.filter(email=request.data.get('email')).values().first()
                request.data['uuid'] = user['uuid']
            except:
                pass
        elif request.data.get('mobile'):
            try:
                user = User.objects.filter(mobile=request.data.get('mobile')).values().first()
                request.data['uuid'] = user['uuid']
            except:
                pass
        
        else:
            return Response(responsedata(False, "Email ID or Mobile is required"), status=status.HTTP_400_BAD_REQUEST)
        

        try:
            userinfo = list(User.objects.filter(uuid=request.data.get("uuid")).values('uuid', 'email', 'mobile','first_name','last_name'))[0]
        except:
            return Response(responsedata(False, "No User Found"), status=status.HTTP_404_NOT_FOUND)


        if not request.data.get("password"):
            return Response(responsedata(False, "Password is required"), status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(uuid=request.data.get("uuid")).exists():
            return Response(responsedata(False, "No User found"), status=status.HTTP_404_NOT_FOUND)
        
        if not User.objects.get(uuid=request.data.get("uuid")).check_password(request.data.get("password")):
            return Response(responsedata(False, "Incorrect Password"), status=status.HTTP_400_BAD_REQUEST)
        
        request.data['uuid'] = str(request.data['uuid'])

        serializer = TokenObtainPairSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            data = serializer.validate(request.data)
            data.update(userinfo)

            if serializer.user.is_active:
                return Response(responsedata(True, "Login Successfull", data), status=status.HTTP_200_OK)
            else:
                return Response(responsedata(False, "Please Validate Your Email Id"), status=status.HTTP_400_BAD_REQUEST)

class ChangePassword(APIView):

    def put(self, request):
        if not request.data.get('password'):
            return Response(responsedata(False, "Enter all the fields"), status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get('new_password') or not request.data.get('confirm_password'):
            return Response(responsedata(False, "Enter all the fields"), status=status.HTTP_400_BAD_REQUEST)
        if (request.data.get('new_password') !=  request.data.get('confirm_password')):
            return Response(responsedata(False, "Password doesn't match"), status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.get(uuid=request.user.uuid).check_password(request.data.get("password")):
            return Response(responsedata(False, "Incorrect Password"), status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(uuid = request.user.uuid)
        data = {'password':request.data.get('new_password')}
        serializer = UserSerializer(user, data = data, partial = True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(responsedata(True, "Password reset done"), status=status.HTTP_200_OK)
        return Response(responsedata(False, "Something went wrong"), status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordOTP(APIView):
    """To send otp to email or mobile to reset password"""

    def post(self, request):
        if request.data.get('email'):

            if not User.objects.filter(email=request.data.get("email")).exists():
                return Response(responsedata(False, "No User found with this Email Id"), status=status.HTTP_404_NOT_FOUND)
            user = User.objects.filter(email=request.data.get("email")).values().first()
            number = str(randint(10000, 99999))
            data = {"user":user['uuid'],"code":int(number), "email": request.data.get("email")}
            serializer = ForgotPasswordSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                try:
                    send_email([request.data.get("email")], "Code for Email Verification",number)
                    serializer.save()
                    return Response(responsedata(True, "Mail sent successfully"), status=status.HTTP_200_OK)
                except:
                    return Response(responsedata(False, "Cant send mail"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        elif request.data.get('mobile'):

            if not User.objects.filter(mobile_num=request.data.get("mobile")).exists():
                return Response(responsedata(False, "No User found with this Mobile Number"), status=status.HTTP_404_NOT_FOUND)
            user =User.objects.filter(email=request.data.get("mobile")).values().first()
            number = str(randint(1000, 9999))

            data = {"user":user['uuid'],"code":int(number), "mobile":request.data.get("mobile")}
            serializer = ForgotPasswordSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    contact = request.data.get('mobile')
                    msg = 'Your+OTP+is+' + number

                    return Response(responsedata(True, "OTP Sent Successfully", {"fr":msg}), status=status.HTTP_200_OK)

                except:
                    return Response(responsedata(False, "Cant send sms"), status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(responsedata(False, "Please provide Email "), status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordOTPValidation(APIView):
    """To check if OTP is correct or not"""

    def post(self, request):

        if request.data.get('code'):
            data = request.data
            setup = ForgotPassword.objects.filter((Q(email=data.get('email')) | Q(mobile=data.get('mobile'))),code=data.get('code'),is_used=False).first()
            if not setup:
                return Response(responsedata(False, "otp provided is incorrect"), status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    val = {"is_used": True}
                    serializer = ForgotPasswordSerializer(setup,data=val,partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                    return Response(responsedata(True, "Correct OTP"), status=status.HTTP_200_OK)
                except:
                    return Response(responsedata(False, "Something Went Wrong"), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(responsedata(False, "OTP not provided"), status=status.HTTP_404_NOT_FOUND)

class ForgotPasswordChange(APIView):
    "To reset passsword if don't recall the present one"

    def post(self, request):
        
        if not request.data.get('new_password') or not request.data.get('confirm_password'):
            return Response(responsedata(False, "Enter all the fields"), status=status.HTTP_400_BAD_REQUEST)

        if (request.data.get('new_password') !=  request.data.get('confirm_password')):
            return Response(responsedata(False, "Password doesn't match"), status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('email'):
            user  = User.objects.filter(email=request.data['email']).first()
            data = {"password":request.data['new_password'],'email_verified':True}


        #if request.data.get('mobile'):
        #    user  = User.objects.filter(mobile_num=request.data['mobile']).first()
        #    data = {"password":request.data['new_password'],'mobile_verified':True}

        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(responsedata(True, "Password Updated",200), status=status.HTTP_200_OK)
        else:
            return Response(responsedata(False, "Something went wrong",500), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendOtp(APIView):
    """To send otp to email address or mobile"""

    def post(self, request):
        if request.data.get('email'):
            number = str(randint(10000,99999))
            data = {"user":request.user.uuid,'otp_type':'email', 'otp_code':int(number) }
            serializer = OtpSerializer(data=data,partial=True)
            if serializer.is_valid(raise_exception=True):
                try:
                    send_email([request.data.get("email")], "Code for Email Verification",number)
                    serializer.save()
                    return Response(responsedata(True, "Mail sent successfully"), status=status.HTTP_200_OK)
                except:
                    return Response(responsedata(False, "Cant send mail"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.data.get('mobile'):
            number = str(randint(10000,99999))
            data = {"user":request.user.uuid,'otp_type':'mobile', 'otp_code':int(number) }
            serializer = OtpSerializer(data=data,partial=True)
            if serializer.is_valid(raise_exception=True):
                try:
                    send_otp(request.data.get('mobile'),number)
                    serializer.save()
                    return Response(responsedata(True, "Message sent successfully"), status=status.HTTP_200_OK)
                except:
                   return Response(responsedata(False, "Cant send message"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ValidateOtp(APIView):
    """To check if OTP is correct or not"""

    def post(self, request):

        if request.data.get('otp_code'):
            data = request.data
            setup = Otp.objects.get(user = request.user.uuid,otp_code=data.get('otp_code'),is_used=False)
            if not setup:
                return Response(responsedata(False, "otp provided is incorrect"), status=status.HTTP_400_BAD_REQUEST)
            else:
                try:
                    val = {"is_used": True}
                    serializer = OtpSerializer(setup,data=val,partial=True)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                    return Response(responsedata(True, "Correct OTP"), status=status.HTTP_200_OK)
                except:
                    return Response(responsedata(False, "Something Went Wrong"), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(responsedata(False, "OTP not provided"), status=status.HTTP_404_NOT_FOUND)

""" ------------------------------------------------------------------------------------------------------------------------------ """

### Search History ###

class SearchHistoryDetail(APIView):
    """To mark hidden or delete history"""

    def put(self,request, pk):
        from main.models import SearchHistory

        if request.auth is None:
            return Response(responsedata(False, "You need to login first"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user

        history = SearchHistory.objects.filter(uuid=pk, user=user.uuid)
        data = {'is_hidden':not(history.values('is_hidden').first()['is_hidden'])}
        serializer = SearchHistorySerializer(history.first(), data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
        
        return Response(responsedata(True, "Hide status changed", serializer.data), status=status.HTTP_200_OK)


    def delete(self,request,pk):
        from main.models import SearchHistory
        history = SearchHistory.objects.filter(uuid=pk)
        history.delete()
        return Response(responsedata(True, "History deleted"), status=status.HTTP_200_OK)

class ClearSearchHistory(APIView):
    """Clear entire search history"""

    def post(self, request):
        
        if request.auth is None:
            return Response(responsedata(False, "You need to login first"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user

        from main.models import SearchHistory
        history = SearchHistory.objects.filter(user=user.uuid)
        history.delete()
        return Response(responsedata(True, "History deleted"), status=status.HTTP_200_OK)

class DisplayHistory(APIView):
    def get(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)

        genres_list = User.objects.filter(genre = request.data.get('genre_preference')).values()
        return Response(responsedata(True, "Genres List", list(genres_list)), status=status.HTTP_200_OK)

""" ------------------------------------------------------------------------------------------------------------------------------ """



class ViewProfile(APIView):
    """To view user's profile"""

    def get(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.filter(uuid=user.uuid).values().first()
        return Response(responsedata(True, "Profile fetched", user), status=status.HTTP_200_OK)
        
class EditProfile(APIView):
    """To edit user's profile"""

    def put(self,request):

        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.filter(uuid=user.uuid).values().first()
        data = {}

        
        # Updating Username or DOB
        if request.data.get('username'):
            data['username'] = request.data.get('username')
        if request.data.get('dob'):
            data['dob'] = request.data.get('dob')

        # Updating User
        user = User.objects.get(uuid=user['uuid'])
        serializer = UserSerializer(user, data=data, partial=True)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        except:
            return Response(responsedata(False, "Something went wrong"), status=status.HTTP_400_BAD_REQUEST)

        return Response(responsedata(True, "Profile updated", serializer.data), status=status.HTTP_200_OK)

class DeleteProfile(APIView):
    
    def post(self, request, pk, format=None):
        if request.auth is None:
            return Response(responsedata(False, "You need to login first"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.filter(uuid=user.uuid)
        user.delete()
        return Response(responsedata(True, "Profile deleted"), status=status.HTTP_200_OK)

""" ------------------------------------------------------------------------------------------------------------------------------ """

### Genres ###

class ListSelectedGenres(APIView):

    def get(self,request):

        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        selected = user.genre_preference
        if len(selected)==0:
            return Response(responsedata(True, "No Genre Selected Yet!!"), status=status.HTTP_200_OK)
        return Response(responsedata(True,"list of selected genres", selected), status=status.HTTP_200_OK)

class AddGenres(APIView):

    def put(self,request):

        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.get(uuid=user.uuid)
        data = {}

        # Genre Preference 
        if request.data.get('genre_preference'):
            data['genre_preference'] = request.data.get('genre_preference')
            genre_list = user.genre_preference
            genre_list.extend(data['genre_preference'])
            genre_list = set(genre_list)

        # Updating User
        serializer = UserSerializer(user, data={'genre_preference': genre_list}, partial=True)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        except:
            return Response(responsedata(False, "Something went wrong"), status=status.HTTP_400_BAD_REQUEST)

        return Response(responsedata(True, "Profile updated", serializer.data), status=status.HTTP_200_OK)

class RemoveGenres(APIView):

    def post(self, request, pk):

        if request.auth is None:
            return Response(responsedata(False, "You need to login first"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.get(uuid=request.user.uuid)
        data = {}

        # Genre Preference 
        if request.data.get('genre_preference'):
            data['genre_preference'] = request.data.get('genre_preference')
            genre_list = user.genre_preference
            genre_list = set(genre_list)
            genre_list1 = set(data['genre_preference'])
            genre_data =  list(list(genre_list - genre_list1) + list(genre_list1 - genre_list))
        
        serializer = UserSerializer(user, data={'genre_preference': genre_data}, partial=True)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        except:
            return Response(responsedata(False, "Something went wrong"), status=status.HTTP_400_BAD_REQUEST)

        return Response(responsedata(True, "Profile updated", serializer.data), status=status.HTTP_200_OK)

""" ------------------------------------------------------------------------------------------------------------------------------ """

### Artists ###

class ListAllArtist(APIView):

    def get(self,request):
        artists = Artist.objects.all()
        serializer = ArtistSerializer(artists, many = True)
        return Response(responsedata(True, "Listing Artists", serializer.data), status=status.HTTP_200_OK)

class ListAllUserArtist(APIView):

    def get(self,request):
        import pdb;pdb.set_trace()
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.get(uuid = user.uuid)
        serializer = UserDataSerializer(user)
        return Response(responsedata(True, "Listing User Artists", serializer.data), status=status.HTTP_200_OK)
        
class AddArtist(APIView):
    
    def put(self,request):

        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.get(uuid=user.uuid)
        data = {}

        # Artists Preference 
        if request.data.get('artist_preference'):
            data['artist_preference'] = request.data.get('artist_preference')
        for artist in data['artist_preference']:
            if user.artist_preference == artist:
                return Response(responsedata(False, "Artist already present"), status=status.HTTP_409_CONFLICT)
            else:
                user = User.objects.get(uuid = request.user.uuid)
                user.artist_preference.add(artist)
        user.save()
        return Response(responsedata(True, "Artist Added"), status=status.HTTP_200_OK)

class RemoveArtist(APIView):

    def put(self,request):

        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user = User.objects.get(uuid=user.uuid)
        data = {}

        # Artists Preference 
        if request.data.get('artist_preference'):
            data['artist_preference'] = request.data.get('artist_preference')
        for artist in data['artist_preference']:
            if user.artist_preference == artist:
                return Response(responsedata(False, "Artist already present"), status=status.HTTP_409_CONFLICT)
            else:
                user = User.objects.get(uuid = request.user.uuid)
                user.artist_preference.remove(artist)
        user.save()
        return Response(responsedata(True, "Artist Added"), status=status.HTTP_200_OK)

""" ------------------------------------------------------------------------------------------------------------------------------ """

### Favourites ###

class ListAllFavourites(APIView):
    def get(self,request):
        favourites = Favourites.objects.all()
        serializer = FavouritesListSerializer(favourites, many= True)
        return Response(responsedata(True, "Listing Favourites", serializer.data),status=status.HTTP_200_OK)

class CreateFavourites(APIView):

    def post(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get("song"):
            return Response(responsedata(False, "Song is required"), status=status.HTTP_400_BAD_REQUEST)
        if request.data:
            data = request.data
            user_data = {"user":request.user.uuid, "song":data.get('song')}
            serializer = FavouritesSerializer(data = user_data)
            if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response(responsedata(False, "Can't insert data"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(responsedata(True, "Data Inserted",serializer.data), status=status.HTTP_200_OK)
        else:
            return Response(responsedata(False, "No Data provided"), status=status.HTTP_400_BAD_REQUEST)

class AddFavourites(APIView):
    
    def put(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        fav_list  =Favourites.objects.get(user = user)
        serializer = FavouritesSerializer(fav_list)
        lst = serializer.data['song']
        lst1 = list(map(str,lst))
        data = {}
        # add to favourites
        if request.data.get('song'):
            data['song'] = request.data.get('song')
        for fav in data['song']:
            if fav in lst1:
                return Response(responsedata(False, "Song already present"), status=status.HTTP_409_CONFLICT)
            else:
                fav_list.song.add(fav)
        fav_list.save()
        return Response(responsedata(True, "Song Added"), status=status.HTTP_200_OK)

class RemoveFavourites(APIView):

    def put(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        fav_list  =Favourites.objects.get(user = user)
        serializer = FavouritesSerializer(fav_list)
        lst = serializer.data['song']
        lst1 = list(map(str,lst))
        data = {}
        # remove from favourites
        if request.data.get('song'):
            data['song'] = request.data.get('song')
        for fav in data['song']:
            if fav not in lst1:
                return Response(responsedata(False, "Song not present"), status=status.HTTP_409_CONFLICT)
            else:
                fav_list.song.remove(fav)   
        fav_list.save()
        return Response(responsedata(True, "Song Removed"), status=status.HTTP_200_OK)

#class SuggestFavouriteSongs

""" ------------------------------------------------------------------------------------------------------------------------------ """

### Playlist ###

class ListAllPlaylists(APIView):
    def get(self,request):
        playlists = Playlist.objects.all()
        serializer = PlaylistListSerializer(playlists,many = True)
        return Response(responsedata(True, "Listing Playlists", serializer.data),status=status.HTTP_200_OK)

class CreatePlaylist(APIView):

    def post(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get("playlist_name"):
            return Response(responsedata(False, "Playlist Name is required"), status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get("song"):
            return Response(responsedata(False, "Atleast one song is required"), status=status.HTTP_400_BAD_REQUEST)

        if request.data:
            data = request.data
            user_data = {"user":request.user.uuid, "playlist_name":data.get('playlist_name'), "song":data.get('song')}
            serializer = PlaylistSerializer(data = user_data)
            if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response(responsedata(False, "Can't insert data"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(responsedata(True, "Data Inserted",serializer.data), status=status.HTTP_200_OK)
        else:
            return Response(responsedata(False, "No Data provided"), status=status.HTTP_400_BAD_REQUEST)

class RemovePlaylist(APIView):

    def put(self,request):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        obj = Playlist.objects.filter(user = user).values(playlist_name)
        data = {}

        if request.data.get('playist_name'):
            data['playlist_name'] = request.data.get('playlist_name')
        for play in data['playlist_name']:
            try:
                lists = Playlist.objects.filter(user = user, playlist_name = play)
                lists.delete()
            except:
                    return Response(responsedata(False, "Playlist not present"), status=status.HTTP_409_CONFLICT)      
        lists.save()
        return Response(responsedata(True, "Playlist Removed"), status=status.HTTP_200_OK)

class ListPlaylistSongs(APIView):

    def get(self,request):
        playlists = Playlist.objects.all()
        serializer = PlaylistSongsListSerializer(playlists,many = True)
        return Response(responsedata(True, "Listing Playlist Songs", serializer.data),status=status.HTTP_200_OK)

class AddPlaylistSongs(APIView):

    def put(self,request,pk):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        playlist_list  =Playlist.objects.get(uuid= pk)
        serializer = PlaylistSerializer(playlist_list)
        lst = serializer.data['song']
        lst1 = list(map(str,lst))
        data = {}
        # add to playlist
        if request.data.get('song'):
            data['song'] = request.data.get('song')
        for s in data['song']:
            if s in lst1:
                return Response(responsedata(False, "Song already present"), status=status.HTTP_409_CONFLICT)
            else:
                playlist_list.song.add(s)
        playlist_list.save()
        return Response(responsedata(True, "Song Added"), status=status.HTTP_200_OK)

class RemovePlaylistSongs(APIView):

    def put(self,request,pk):
        if request.auth is None:
            return Response(responsedata(False, "You are Unauthorized"), status=status.HTTP_400_BAD_REQUEST)
        playlist_list  =Playlist.objects.get(uuid= pk)
        serializer = PlaylistSerializer(playlist_list)
        lst = serializer.data['song']
        lst1 = list(map(str,lst))
        data = {}
        # add to playlist
        if request.data.get('song'):
            data['song'] = request.data.get('song')
        for s in data['song']:
            if s not in lst1:
                return Response(responsedata(False, "Song not present"), status=status.HTTP_409_CONFLICT)
            else:
                playlist_list.song.remove(s)
        playlist_list.save()
        return Response(responsedata(True, "Song Removed"), status=status.HTTP_200_OK)

#class SuggestPlaylistSongs

""" ------------------------------------------------------------------------------------------------------------------------------ """


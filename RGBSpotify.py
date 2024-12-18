import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
from samplebase import SampleBase
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
from datetime import datetime
from PIL import Image
from multiprocessing import Process, Manager, Value
from ctypes import c_wchar_p
import json
import WeatherAPI

class SpotifyAPI:

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="",
                                                            client_secret="",
                                                            redirect_uri="http://localhost/",
                                                            scope="user-read-currently-playing"))
                                                            #user-read-currently-playing
                                                            #user-modify-playback-state

    rate_limit = 2
    
    def defaults(track_name,track_artists,image_url,album_name,savedTrack):
        track_name.value = None
        track_artists.value = ''
        image_url.value = ''
        album_name.value = ''
        savedTrack.value = ''

        currentTrack = SpotifyAPI.sp.current_user_playing_track()

        while currentTrack == None:
            time.sleep(SpotifyAPI.rate_limit)
            currentTrack = SpotifyAPI.sp.current_user_playing_track()
        else:
            savedTrack.value = currentTrack
            SpotifyAPI.apiCalls(track_name,track_artists,image_url,album_name,savedTrack)

    def apiCalls(track_name,track_artists,image_url,album_name,savedTrack):
        print('thread1 starts...', datetime.now())
        #authenticate user and authorize using read-currently-playing scope
        
        #print('grabbing api', datetime.now())
        #create insance of the current user's current track
        currentTrack = SpotifyAPI.sp.current_user_playing_track()

        if currentTrack == None:
            WeatherAPI.WeatherAPI.WeatherRGBLayer(track_name,track_artists,image_url,album_name,savedTrack)
        
        #print('api request granted', datetime.now())
        #parse json response into the name, artists and image of album cover
        try:
            #we can't set the track_name.value yet because we haven't downloaded the album cover at this point
            currentTrack['item']['name']
            track_artists.value = currentTrack['item']['album']['artists'][0]['name']
            image_url.value = currentTrack['item']['album']['images'][0]['url']
            if currentTrack['item']['album']['name'].__contains__('/'):
                album_name.value = currentTrack['item']['album']['name'].replace('/', ' ')
            else:
                album_name.value = currentTrack['item']['album']['name']
        except:
            track_name.value = currentTrack['item']['name']
            track_artists.value = currentTrack['item']['artists'][0]['name']
            image_url.value = ''
            album_name.value = 'DefaultAlbumCover'

        savedTrack.value = track_name.value
        if image_url.value != '':
            #Download album cover
            img_data = requests.get(image_url.value).content
            with open("/home/remote/Desktop/Images/" + album_name.value, 'wb') as handler:
                handler.write(img_data)

        track_name.value = currentTrack['item']['name']

        print(track_name.value, " by ", track_artists.value)
        print(album_name.value)
        print(image_url.value)
        
        try:
            while currentTrack['item']['name'] == savedTrack.value:
                currentTrack = SpotifyAPI.sp.current_user_playing_track()
                time.sleep(SpotifyAPI.rate_limit)
                if currentTrack == None:
                    WeatherAPI.WeatherAPI.WeatherRGBLayer(track_name,track_artists,image_url,album_name,savedTrack)
            else:
                savedTrack.value = currentTrack
                SpotifyAPI.apiCalls(track_name,track_artists,image_url,album_name,savedTrack)
        except:
            WeatherAPI.WeatherAPI.WeatherRGBLayer(track_name,track_artists,image_url,album_name,savedTrack)


    def RGBLayer(track_name,track_artists,album_name,savedTrack):
        print('thread2 starts...', datetime.now())
        time.sleep(0.5)

        #this makes it so that the screen is cleared and stays that way for when the weather api things are happening
        while track_name.value == None:
            continue
        
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat'
        options.gpio_slowdown = 5
        options.brightness = 1
        options.drop_privileges = False
        # options.pwm_lsb_nanoseconds = 120
        # options.limit_refresh_rate_hz = 160
        options.show_refresh_rate = False

        matrix = RGBMatrix(options=options)

        fade_speed = 0.005
        max_brightness = 100
        red = 255
        green = 0
        blue = 0
        offscreen_canvas = matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("fonts/5x8.bdf")
        textColor = graphics.Color(red, green, blue)
        songNamePos = 0
        songNameVPos = 30
        clockPos = 30
        clockVPos = 6
        #'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz 0123456789;:\'\",.!@#$%^&*()[]{}<>'
        if track_artists.value != '':
            my_text = (track_name.value + " by " + track_artists.value)
        else:
            my_text = (track_name.value)
        movingLeft = True
        firstRun = True
        imageWidth = 22
        image = Image.open("/home/remote/Desktop/Images/" + album_name.value)

        # Make image fit our screen.
        print("albumname: ", album_name.value)
        image.thumbnail((imageWidth, matrix.height), Image.ANTIALIAS)
        matrix.SetImage(image.convert('RGB'))

        currentTrack = SpotifyAPI.sp.current_user_playing_track() 
        if currentTrack == None:
            with open('/home/remote/Desktop/Default.json', 'r') as openfile:
                currentTrack = json.load(openfile)
        while track_name.value != None:            
            while movingLeft:
                if currentTrack['item']['name'] != savedTrack.value:
                    for x in range(1, max_brightness):
                                matrix.brightness = (max_brightness - x)
                                matrix.SetImage(image.convert('RGB'))   
                                offscreen_canvas.Clear()
                                len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                                clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                        
                                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                                matrix.SetImage(image.convert('RGB'))
                                time.sleep(fade_speed)
                    offscreen_canvas.Clear()
                    matrix = None
                    SpotifyAPI.RGBLayer(track_name,track_artists,album_name,savedTrack)

                matrix.SetImage(image.convert('RGB'))        
      
                offscreen_canvas.Clear()
                len = graphics.DrawText(offscreen_canvas, font, songNamePos, songNameVPos, textColor, my_text)
                clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                songNamePos -= 1

                #red -= 2
                #textColor = graphics.Color(red, green, blue)
                time.sleep(0.05)

                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                matrix.SetImage(image.convert('RGB'))

                if(songNamePos <= 0 - len + 64):
                    if firstRun:
                        for x in range(1, max_brightness):
                            matrix.brightness += 1
                            matrix.SetImage(image.convert('RGB'))   
                            offscreen_canvas.Clear()
                            len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                            clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                    
                            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                            matrix.SetImage(image.convert('RGB'))
                            time.sleep(fade_speed)
                    songNamePos += 1
                    movingLeft = False
                    firstRun = False
                    time.sleep(2)
                    break
                        
                        
                if(firstRun):
                    for x in range(1, max_brightness):
                        matrix.brightness += 1
                        matrix.SetImage(image.convert('RGB'))   
                        offscreen_canvas.Clear()
                        len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                        clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                
                        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                        matrix.SetImage(image.convert('RGB'))
                        time.sleep(fade_speed)

                    for x in range(6):
                        time.sleep(1)
                        if currentTrack['item']['name'] != savedTrack.value:
                            for x in range(1, max_brightness):
                                matrix.brightness = (max_brightness - x)
                                matrix.SetImage(image.convert('RGB'))   
                                offscreen_canvas.Clear()
                                len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                                clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                        
                                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                                matrix.SetImage(image.convert('RGB'))
                                time.sleep(fade_speed)
                            offscreen_canvas.Clear()
                            matrix = None
                            SpotifyAPI.RGBLayer(track_name,track_artists,album_name,savedTrack)
                    firstRun = False

            while movingLeft == False:
                if currentTrack['item']['name'] != savedTrack.value:
                    for x in range(1, max_brightness):
                        matrix.brightness = (max_brightness - x)
                        matrix.SetImage(image.convert('RGB'))   
                        offscreen_canvas.Clear()
                        len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                        clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                
                        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                        matrix.SetImage(image.convert('RGB'))
                        time.sleep(fade_speed)
                    offscreen_canvas.Clear()
                    matrix = None
                    SpotifyAPI.RGBLayer(track_name,track_artists,album_name,savedTrack)

                matrix.SetImage(image.convert('RGB'))        

                offscreen_canvas.Clear()
                len = graphics.DrawText(offscreen_canvas, font, songNamePos, songNameVPos, textColor, my_text)
                clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                songNamePos += 1
                #red += 2
                #textColor = graphics.Color(red, green, blue)
                time.sleep(0.05)

                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                matrix.SetImage(image.convert('RGB'))
                        
                if(songNamePos == 1):                    
                    songNamePos -= 1
                    for x in range(10):
                        time.sleep(1)
                        if currentTrack['item']['name'] != savedTrack.value:
                            for x in range(1, max_brightness):
                                matrix.brightness = (max_brightness - x)
                                matrix.SetImage(image.convert('RGB'))   
                                offscreen_canvas.Clear()
                                len = graphics.DrawText(offscreen_canvas, font, songNamePos + 1, songNameVPos, textColor, my_text)
                                clock = graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, graphics.Color(red,green,blue), datetime.now().strftime("%I:%M%p"))
                        
                                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                                matrix.SetImage(image.convert('RGB'))
                                time.sleep(fade_speed)
                            offscreen_canvas.Clear()
                            matrix = None
                            SpotifyAPI.RGBLayer(track_name,track_artists,album_name,savedTrack)
                    movingLeft = True
                    break
            # else:
            #     return



if __name__ == "__main__":
    manager = Manager()
    track_name = manager.Value(c_wchar_p, '')
    track_artists = manager.Value(c_wchar_p, '')
    image_url = manager.Value(c_wchar_p, '')
    album_name = manager.Value(c_wchar_p, '')
    savedTrack = manager.Value(c_wchar_p, '')

    t1 = Process(target=SpotifyAPI.apiCalls, args=(track_name,track_artists,image_url,
                                                   album_name,savedTrack,))
    t2 = Process(target=SpotifyAPI.RGBLayer, args=(track_name,track_artists,
                                                   album_name,savedTrack,))
    t1.start()
    time.sleep(1)
    t2.start()

    t1.join()
    t2.join()
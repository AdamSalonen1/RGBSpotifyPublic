from urllib.request import urlopen
import json
import datetime
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
import time
from RGBSpotify import SpotifyAPI

class WeatherAPI:

    currentTemp = ''
    currentTime = ''
    noChange = True

    def WeatherRGBLayer(track_name,track_artists,image_url,album_name,savedTrack):
        track_name.value = None
        track_artists.value = ''
        image_url.value = ''
        album_name.value = ''
        savedTrack.value = ''

        time.sleep(2.25)

        currentTrack = SpotifyAPI.sp.current_user_playing_track()

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
        font.LoadFont("fonts/9x15.bdf")
        clockColor = graphics.Color(red, green, blue)
        tempColor = graphics.Color(green,red,blue)
        tempPos = 0
        tempVPos = 28
        clockPos = 0
        clockVPos = 14
        firstRun = True

        while currentTrack == None:
            currentTrack = SpotifyAPI.sp.current_user_playing_track()
            
            WeatherAPI.noChange = True

            WeatherAPI.UpdateTemp()
            WeatherAPI.currentTime = datetime.datetime.now().strftime("%I:%M%p")

            offscreen_canvas.Clear()
            

            if firstRun:
                for x in range(max_brightness):
                    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)            
                    offscreen_canvas.Clear()
                    matrix.brightness += 1
                    time.sleep(0.005)
                    offscreen_canvas.Clear()
                    graphics.DrawText(offscreen_canvas, font, tempPos, tempVPos, tempColor, WeatherAPI.currentTemp)
                    graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, clockColor, datetime.datetime.now().strftime("%I:%M%p"))

                firstRun = False

            if WeatherAPI.noChange == False:

                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
                
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, tempPos, tempVPos, tempColor, WeatherAPI.currentTemp)
                graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, clockColor, datetime.datetime.now().strftime("%I:%M%p"))

                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)

            time.sleep(1)    

        else:       
            for x in range(max_brightness):
                offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)            
                offscreen_canvas.Clear()
                matrix.brightness -= 1
                time.sleep(0.005)
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, font, tempPos, tempVPos, tempColor, WeatherAPI.currentTemp)
                graphics.DrawText(offscreen_canvas, font, clockPos, clockVPos, clockColor, datetime.datetime.now().strftime("%I:%M%p"))

            offscreen_canvas.Clear()
            matrix = None
            
            SpotifyAPI.apiCalls(track_name,track_artists,image_url,album_name,savedTrack)

    def UpdateTemp():
        degree = '°F'

        apikey = ''

        zipcode = ''

        baseurl = "http://api.weatherapi.com/v1/forecast.json?key={}&q={}&aqi=yes"
        url = baseurl.format(apikey, zipcode)

        response = urlopen(url)

        data = json.loads(response.read())

        localTemp = data['current']['temp_f'].__str__()[0:2] + degree

        localTime = datetime.datetime.now().strftime("%I:%M%p")

        if localTemp != WeatherAPI.currentTemp or localTime != WeatherAPI.currentTime:
            WeatherAPI.noChange = False

        WeatherAPI.currentTemp = localTemp
        WeatherAPI.currentTime = localTime

        #print(WeatherAPI.currentTemp)

if __name__ == "__main__":
    WeatherAPI.WeatherRGBLayer()
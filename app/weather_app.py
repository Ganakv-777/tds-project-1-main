import requests

def get_weather(city):
    api_key = "YOUR_API_KEY"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url).json()
    print(f"{city}: {res['main']['temp']}°C, {res['weather'][0]['description']}")

if __name__ == "__main__":
    city = input("Enter city name: ")
    get_weather(city)

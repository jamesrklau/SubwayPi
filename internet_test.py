from urllib.request import urlopen

response = urlopen("https://api.github.com")
print(response.status)
print (response.read(200).decode("utf-8"))

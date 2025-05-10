import requests

username = "asvgfumc-1"   
password = "e8k8jz8svt86"
address = "p.webshare.io"
port = "80"
proxy = {
    "http": f"http://{username}:{password}@{address}:{port}",
    "https": f"https://{username}:{password}@{address}:{port}"
}

# Function to make a request through the authenticated proxy and print the response
def fetch_ip(url):
    response = requests.get(url, proxies=proxy)
    print(response)

# Make requests through the authenticated proxy

fetch_ip("https://httpbin.org/ip")
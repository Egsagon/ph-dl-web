# PHFETCH ONLINE

This project is a proof of concept at implementing [PHFetch](https://github.com/Egsagon/pornhub-fetch) - a Pornhub video downloading interface - on a downloading website.

### Usage
Screenshot from the frontend:
![image](https://github.com/Egsagon/ph-webui-2/assets/83862309/18830134-24f6-4db1-bd69-f6c3a135f168)

### Run
To run in debug mode, simply run the `app.py` file.
```sh
python3 app.py
```

To run for production, use Gunicorn.
```sh
gunicorn --timeout app:app
```
###### Note: removing worker timeout is needed for long downloads

If you wished to use a local version of PHFetch, try [PH-downloader-webui](https://github.com/Egsagon/pornhub-downloader-webui), a WebUI built on top of PHFetch, or make your own scripts with [PHFetch](https://github.com/Egsagon/pornhub-fetch).

### Structure
On start, the server creates a `Turntable` object responsible for distributing download requests to the least busy workers. `Workers` are threads that have their own queue. Each time a request (a `Call` object) is received, it will be assigned to a worker that will start downloading it or put in its queue. During the download, the frontends are given a token representing their requests. With it, they will be able to make /status requests to get the status of the download (every 3 seconds) and download the video file once the server as finished uploading it locally.

### Note
The frontend is very likely to be unstable.

The frontend has extra features, like downloading multiple videos (the + button), choosing a quality, auto-checking for video availablity, etc.

The server is running on a free render.com service [there](https://ph-dl.onrender.com/) so you can check it out (very laggy tho).

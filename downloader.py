import os
import re
import uuid
import phfetch
import threading
from time import sleep
from dataclasses import dataclass


ALLOWED_QUALITIES = {
    phfetch.Quality.BEST,
    phfetch.Quality.MIDDLE,
    phfetch.Quality.WORST
}

RE_URL = r'https:\/\/..\.pornhub\.com\/view_video\.php\?viewkey=[a-z\d]{15}'


@dataclass
class Call:
    # Video info
    url: str
    token: str
    quality: str
    
    title: str = None
    image: str = None
    path: str = None
    error: str = None
    fail: bool = False
    
    # Progress infos
    progress: int = None
    total: int = None
    
    def to_dict(self) -> dict:
        '''
        Returns a dict version of the call.
        '''
        
        return {
            'progress': self.progress,
            'total': self.total,
            'error': self.error,
            'image': self.image,
            'path': self.path,
            'title': self.title,
            'fail': self.fail
        }


class Worker:
    
    def __init__(self, id: int) -> None:
        '''
        Represents a worker capable of downloading one
        thing at a time.
        '''
        
        self.id = id
        self.queue: list = []
        self.running = False
    
    def run(self) -> None:
        '''
        Main worker loop. Meant to be run as a thread.
        '''
        
        self.running = True
        while self.running:
            
            sleep(.1)
            
            # Select element in queue
            if not len(self.queue): continue
            call = self.queue.pop(0)
            
            print(f'[{self.id}] Processing', call)
            
            call.path = f'client/output/{call.token}.mp4'
            
            # Create folder if needed
            if not os.path.exists('client/output/'):
                os.makedirs('client/output/')
            
            def receiver(cur: int, total: int) -> None:
                # Handle updating the call data
                
                call.progress = cur
                call.total = total
                
                print(f'[{self.id}] Downloading', cur, '/', total)
            
            # Download
            try:
                video = phfetch.video(url = call.url)
                call.image = video.image
                call.title = video.title
                
                print(f'[{self.id}] Fetched video page')
                video.download(call.path,
                               call.quality,
                               callback = receiver,
                               quiet = True)
            
            except Exception as err:
                print(f'[{self.id}] DL/scrape error:', repr(err))
                call.error = repr(err)
                call.fail = True
            
            finally:
                # Delete the call after 3min
                
                def d1():
                    print(f'[{self.id}] Deleting call', call)
                    del call
                
                threading.Timer(30000, d1)
            
            if call.error: continue
            
            # Delete file
            def d2():
                print(f'[{self.id}] Hard deleting call', call)
                del call
                    
                os.remove(call.path)
            
            threading.Timer(1800000, d2)
    
    def start(self) -> None:
        '''
        Start the worker as a thread.
        '''
        
        threading.Thread(target = self.run).start()


class Turntable:
    
    def __init__(self, childs: int = 5) -> None:
        '''
        Represents a turntable capable of deciding how
        to download things.
        '''

        self.child_counts = 5
        self.childs: list = []
        self.tracked: list = []
    
    def start(self) -> None:
        '''
        Create and start all threads.
        '''
        
        for i in range(self.child_counts):
            
            child = Worker(id = i)
            child.start()
            self.childs.append(child)
            print('Started worker with id =', i)
    
    def new(self, args: dict) -> str:
        '''
        Create a new call and returns a token.
        '''
        
        print('[T] Received new call:', list(args.values()))
        
        call = Call(
            url = args.get('url', ''),
            token = uuid.uuid4().hex,
            quality = args.get('quality', 'best')
        )
        
        # Check availability of the call
        assert call.quality in ALLOWED_QUALITIES, 'invalid quality'
        assert 'https://' in call.url and 'pornhub.com/view_video.php?viewkey=' in call.url, 'invalid url'
        
        # Assignate to a worker
        best = self.childs[0]
        for worker in self.childs[1:]:
            if len(worker.queue) < len(best.queue):
                best = worker
        
        # Queue request
        print('[T] Queueing call to worker id =', worker.id)
        best.queue.append(call)        
        self.tracked.append(call)
        
        return call

# EOF
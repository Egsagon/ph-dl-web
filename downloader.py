import os
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

COLORS = (100, 102, 103, 104, 105, 106, 107)


def log(title: str, *text) -> None:
    '''
    Pretty log print.
    '''
    
    # Attribute color to title
    color = COLORS[ hash(title) % len(COLORS) ]
    
    print(f'\033[{color}m{title.upper()}\033[0m\033[{color - 10}m', *text, '\033[0m')

def err(title: str, *text) -> None:
    '''
    Log an error.
    '''
    
    print(f'\033[101m{title.upper()}\033[0m\033[91m', *text, '\033[0m')


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
        
        self.title = f'WK-{id}'
    
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
            log(self.title, 'Processing call:', id(call))
            
            call.path = f'client/output/{call.token}.mp4'
            
            # Create folder if needed
            if not os.path.exists('client/output/'):
                os.makedirs('client/output/')
            
            partials = 0
            
            def receiver(cur: int, total: int) -> None:
                # Handle updating the call data
                
                global partials
                
                # Update call status
                call.progress = cur
                call.total = total
                
                # Log
                partials += 1
                if partials > 50:
                    partials = 0
                    log(self.title, f'Downloading {cur}/{total}')
                
                if cur + 1 == total:
                    log(self.title, f'Download finished.')
            
            # Download
            try:
                video = phfetch.video(url = call.url)
                call.image = video.image
                call.title = video.title
                
                log(self.title, 'Fetched data')
                
                video.download(call.path,
                               call.quality,
                               callback = receiver,
                               quiet = True)
            
            except Exception as error:
                err(self.title, 'Download error:', error)
                
                call.error = repr(error)
                call.fail = True
            
            # Clean call and file
            filepath = call.path
            
            def del_call():
                log('cleaner', 'Deleting call', id(call))
                del call
            
            def del_file():
                log('cleaner', 'Deleting file', id(call))
                
                try: os.remove(filepath)
                except Exception as error:
                    err('cleaner', f'Failed to delete {filepath}, error:', error)
            
            # Delete call after 1min and file after 1h
            threading.Timer(60_000, del_call)
            threading.Timer(1_800_000 * 2, del_file) # 30min *2
    
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
            
            log('table', f'Started worker id={i}')
        
        log('table', 'Started all workers')
    
    def new(self, args: dict) -> str:
        '''
        Create a new call and returns a token.
        '''
        
        log('table', 'Handling request:', list(args.values()))
        
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
        log('table', f'Assigning task to worker id={worker.id}')
        
        best.queue.append(call)
        self.tracked.append(call)
        return call

# EOF
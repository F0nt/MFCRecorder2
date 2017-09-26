import threading
import asyncio
import requests
import mfcauto

SERVER_CONFIG_URL = 'http://www.myfreecams.com/_js/serverconfig.js'

def get_online_models():
    '''returns a dictionary of all online models in free chat'''
    server_config = requests.get(SERVER_CONFIG_URL).json()
    servers = server_config['h5video_servers'].keys()
    models = {}
    models_lock = threading.Lock()

    def on_tags(_):
        '''function for the TAGS event in mfcclient'''
        nonlocal models

        #locking to prevent from disconnecting too early
        with models_lock:
            #test for data in models. Data in models means that we
            #already had this function running and we can disconnect safely
            if models:
                return

            #merging tags and models (needed due to a possible bug in mfcauto)
            all_results = mfcauto.Model.find_models(lambda m: True)
            models = {int(model.uid): Model(model) for model in all_results
                      if model.tags is None and int(model.uid) > 0
                      and model.bestsession['vs'] == mfcauto.STATE.FreeChat
                      and str(model.bestsession['camserv']) in servers}
            tags = (tag for tag in all_results if tag.tags is not None)
            for tag in tags:
                model = models.get(int(tag.uid), None)
                if model:
                    model.tags = tag.tags

            print('{} models online'.format(len(models)))
            client.disconnect()

    #setting a new event loop, because it gets closed in the mfcauo client (feels dirty)
    asyncio.set_event_loop(asyncio.new_event_loop())
    #we dont want to query the models in CLIENT_MODELSLOADED, because we are
    #missing the tags at this point. Rather query everything on TAGS
    client = mfcauto.SimpleClient()
    client.on(mfcauto.FCTYPE.TAGS, on_tags)
    client.connect()

    return models

class Model():
    '''custom Model class to preserve the session information'''
    def __init__(self, model):
        self.name = model.nm
        self.uid = model.uid
        self.tags = model.tags
        #vs info will be lost
        self.session = model.bestsession

    def __repr__(self):
        return '{{"name": {}, "uid": {}, "tags": {}, "session": {}}}'.format(
            self.name, self.uid, self.tags, self.session)

    def merge_tags(self, model):
        '''merges tags into a model or vice versa and returns new object'''
        base = self if self.tags is None else model
        base.tags = self.tags if self.tags is not None else model.tags
        return base

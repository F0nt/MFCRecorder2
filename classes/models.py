import threading
import asyncio
import requests
import mfcauto

SERVER_CONFIG_URL = 'http://www.myfreecams.com/_js/serverconfig.js'

class TestClient:
    def __init__(self):
        self._loaded = False
        loop = asyncio.get_event_loop()
        self._client = mfcauto.Client(loop)
        self._client.on(mfcauto.FCTYPE.CLIENT_TAGSLOADED, self._set_loaded)
        loop.run_until_complete(self._client.connect(True))
        threading.Thread(target=loop.run_forever).start()

    def _set_loaded(self):
        self._loaded = True

    def get_online_models(self):
        print('mfcauto loaded: {}'.format(self._loaded))
        success = False
        remaining_tries = 10
        while not success:
            try:
                server_config = requests.get(SERVER_CONFIG_URL).json()
                servers = server_config['h5video_servers'].keys()
                success = True
                print('url loaded')
            except Exception as e:
                remaining_tries -= 1
                if remaining_tries > 0:
                    print(e)
                else:
                    raise
        try:
            all_results = mfcauto.Model.find_models(lambda m: True)
            models = {int(model.uid): Model(model) for model in all_results
                      if model.uid > 0 and model.bestsession['vs'] == mfcauto.STATE.FreeChat
                      and str(model.bestsession['camserv']) in servers}
            print('{} models online'.format(len(models)))
            return models
        except Exception as e:
            print(e)

def get_model(uid_or_name):
    '''returns a tuple with uid and name'''
    async def query(loop):
        client = mfcauto.Client(loop)
        await client.connect(False)
        msg = await client.query_user(uid_or_name)
        client.disconnect()
        return msg
    
    #asyncio in a threaded environment...
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    msg = loop.run_until_complete(query(loop))
    return msg if msg is None else (msg['uid'], msg['nm'])

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

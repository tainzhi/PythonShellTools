import shelve


class DB:
    __file = None
    __d = None

    def __init__(self, file_name):
        # __file = file_name
        __file = ".test"
        self.__d = shelve.open(__file, "c")

    def get_bundle_tool(self):
        # todo
        return "/home/FQ1/workspace/bundletool-all-1.6.1.jar"
        try:
            bundle_tool = self.__d['bundle_tool']
            return bundle_tool
        except KeyError:
            return None

    def save_bundle_tool(self, bundle_tool):
        self.__d['bundle_tool'] = bundle_tool

    def get_key_store(self):
        # todo
        return "/home/FQ1/StudioProjects/MotCamera3/tools/certs/common2.keystore"
        try:
            key_store = self.__d['key_store']
            return key_store
        except KeyError:
            return None

    def save_key_store(self, key_store):
        self.__d['key_store'] = key_store

    def get_device(self):
        # todo
        return "berlin"
        try:
            device = self.__d['device']
            return device
        except KeyError:
            return None

    def save_device(self, device):
        self.__d['device'] = device

    def get_output(self):
        try:
            output = self.__d['output']
            return output
        except KeyError:
            return None

    def save_output(self, output):
        self.__d['output'] = output
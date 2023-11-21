import ast

import beniget
import gast


# Class to fetch all uses of self vars in a class
class Attributes(gast.NodeVisitor):
    def __init__(self, module_node, class_name):
        # compute the def-use of the module
        self.chains = beniget.DefUseChains()
        self.chains.visit(module_node)
        self.users = set()  # all users of `self`
        self.attributes = []  # attributes of current class
        self.class_name = class_name
        self.function_scopes = {}

    def visit_ClassDef(self, node):
        # walk methods and fill users of `self`
        for stmt in node.body:
            if isinstance(stmt, gast.FunctionDef):
                if stmt.args.args:
                    self_def = self.chains.chains[stmt.args.args[0]]
                    self.users.update(use.node for use in self_def.users())
                    self.function_scopes = self.function_scopes | {
                        str(use.node): stmt.name for use in self_def.users()
                    }

        self.generic_visit(node)

    def visit_Attribute(self, node):
        # any attribute of `self` is registered
        if node.value in self.users:
            if isinstance(node.ctx, gast.Store):
                self.attributes.append(
                    {
                        "name": f"{self.class_name}.{node.attr}",
                        "lineno": node.lineno,
                        "function": self.function_scopes.get(str(node.value), ""),
                    }
                )


class UseDefManager(gast.NodeVisitor):
    use_def_cache = {}

    def __init__(self, module_path):
        # compute the def-use of the module
        self.chains = beniget.DefUseChains()
        self.attributes = set()  # attributes of current class
        self.module_path = module_path
        self.locals_defs_modules = {}

        self.module_node = gast.parse(open(module_path).read())
        self.chains.visit(self.module_node)
        self.udc = beniget.UseDefChains(self.chains)

        if module_path not in UseDefManager.use_def_cache:
            self.analyze()
        else:
            self.line_uses = UseDefManager.use_def_cache[module_path]["line_uses"]
            self.locals_defs = UseDefManager.use_def_cache[module_path]["locals_defs"]
            self.class_vars = UseDefManager.use_def_cache[module_path]["class_vars"]
            self.locals_defs_modules[module_path] = UseDefManager.use_def_cache[
                module_path
            ]["locals_defs"]

    def analyze(self):
        self.generic_visit(self.module_node)
        (
            self.line_uses,
            self.locals_defs,
            self.class_vars,
            self.meta_data,
        ) = self.get_all_definitions_for_use()
        self.locals_defs_modules[self.module_path] = self.locals_defs
        UseDefManager.use_def_cache[self.module_path] = {
            "line_uses": self.line_uses,
            "locals_defs": self.locals_defs,
            "class_vars": self.class_vars,
            "meta_data": self.meta_data,
        }

    def get_all_definitions_for_use(self, full_nodes=True):
        node = self.module_node
        variable_defs = {}
        locals_defs = []
        class_vars = []
        meta_data = {}

        # for _chain in self.duc.chains.values():
        #     print(_chain)
        # for _use in _chain.users():
        #     _use
        def _visit_child_locals(inner_node):
            inner_locals = self.chains.locals[inner_node]
            # inner_locals
            for _var in inner_locals:
                # for _use in self.duc.chains[_var.node].users():
                #     _use
                # print(_var)
                if isinstance(_var.node, gast.ClassDef):
                    _id = _var.node.name + ":" + str(_var.node.lineno)
                    self.attr = Attributes(self.module_node, _id)
                    self.attr.visit(_var.node)
                    class_vars.extend(self.attr.attributes)
                    _visit_child_locals(_var.node)
                    metadata = {
                        "lineno": _var.node.lineno,
                        "col_offset": _var.node.col_offset,
                    }
                    if _var.node.name in meta_data:
                        meta_data[_var.node.name].append(metadata)
                    else:
                        meta_data[_var.node.name] = [metadata]
                elif isinstance(_var.node, gast.FunctionDef):
                    _id = _var.node.name + ":" + str(_var.node.lineno)
                    metadata = {
                        "lineno": _var.node.lineno,
                        "col_offset": _var.node.col_offset,
                    }
                    if _var.node.name in meta_data:
                        meta_data[_var.node.name].append(metadata)
                    else:
                        meta_data[_var.node.name] = [metadata]
                    _visit_child_locals(_var.node)
                elif isinstance(_var.node, gast.Name):
                    _id = _var.node.id + ":" + str(_var.node.lineno)
                    metadata = {
                        "lineno": _var.node.lineno,
                        "col_offset": _var.node.col_offset,
                    }
                    if _var.node.id in meta_data:
                        meta_data[_var.node.id].append(metadata)
                    else:
                        meta_data[_var.node.id] = [metadata]
                    if isinstance(_var.node.ctx, gast.Param):
                        _node_type = "param"
                    else:
                        _node_type = "local_variable"

                    _def_info = {
                        "name": _id,
                        "id": _var.node.id,
                        "lineno": _var.node.lineno,
                        "node_type": _node_type,
                    }
                    locals_defs.append(_def_info)
                elif isinstance(_var.node, gast.alias):
                    if _var.node.asname:
                        _id = _var.node.asname
                    else:
                        _id = _var.node.name
                # elif isinstance(_var.node, gast.Attribute):
                #     _id = _var.node.name + ":" + str(_var.node.lineno)
                #     _visit_child_locals(_var.node)

                for _use in _var.users():
                    if _use.node.lineno not in variable_defs:
                        variable_defs[_use.node.lineno] = []
                    if full_nodes:
                        variable_defs[_use.node.lineno].append(_var.node)
                    else:
                        variable_defs[_use.node.lineno].append(_id)

                # TODO: Revisit collection of uses

        _visit_child_locals(node)

        return variable_defs, locals_defs, class_vars, meta_data

    def visit_ClassDef(self, node):
        # walk methods and fill users of `self`
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self_def = self.chains.chains[stmt.args.args[0]]
                self.users.update(use.node for use in self_def.users())
        self.generic_visit(node)

    # def visit_Attribute(self, node):
    #     # any attribute of `self` is registered
    #     if node.value in self.users:
    #         self.attributes.add(node.attr)

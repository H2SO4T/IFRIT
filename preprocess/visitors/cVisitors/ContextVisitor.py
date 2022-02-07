from pycparser import c_ast

class ContextVisitor(c_ast.NodeVisitor):
    def __init__(self, name):
        self.name = name
        # track context name and set of names marked as `global`
        self.context = [('global', ())]

    def visit_FuncDecl(self, node):
        self.context.append(('function', set()))
        self.generic_visit(node)
        self.context.pop()

    def visit_Global(self, node):
        assert self.context[-1][0] == 'function'
        self.context[-1][1].update(node.names)

    def visit_Decl(self, node):
        ctx, g = self.context[-1]
        if node.name == self.name and (ctx == 'global' or node.name in g):
            print('{} used at line {}'.format(node.name, node.coord))

#    def visit_Constant(self, node):
#        ctx, g = self.context[-1]
#        if node.name == self.name and (ctx == 'global' or node.name in g):
#            print('{} used at line {}'.format(node.name, node.coord))

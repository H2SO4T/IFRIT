from pycparser import c_ast

class BlockCreator(c_ast.NodeVisitor):
    def generic_visit(self, node):
        #print(node.coord)
        if(isinstance(node,c_ast.If)):
            if(node.iftrue and not(isinstance(node.iftrue,c_ast.Compound))):
                node.iftrue = c_ast.Compound([node.iftrue])
            if(node.iffalse and not(isinstance(node.iffalse,c_ast.Compound))):
                node.iffalse = c_ast.Compound([node.iffalse])
        elif (isinstance(node,c_ast.For)):
            if(node.stmt and not(isinstance(node.stmt,c_ast.Compound))):
                node.stmt = c_ast.Compound([node.stmt])
        for c_name, c in node.children():
            self.visit(c)

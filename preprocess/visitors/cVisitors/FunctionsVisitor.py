from pycparser import c_ast, parse_file
import sys

class FunctionsVisitor(c_ast.NodeVisitor):
    retVal=None
    decVal=None
    def visit_FuncDef(self, node):
#        print(node.expr.name)
        print(node.decl.name)
        
visitor = FunctionsVisitor()
ast = parse_file(sys.argv[1])
visitor.visit(ast)

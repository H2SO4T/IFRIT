import parser
import ast
from math import sin, cos, tan

formulas = [
    "Or(And(guard_5, a_0_1_10 == a_0_1_9),And(Not(guard_5), a_0_1_10 == 2))",
    "not(a)",
    "guard_1 == (not(not(b_0_1_2 * y_0_1_1 == 1) and not(x_0_1_1 >= 4)))",
    "guard == (not( not( x_0_1_1 >= 101 ) or y_0_1_1 >= 101))",
    "not( not( x_0_1_1 >= 101 ) and y_0_1_1 >= 101)",
    "not( not( x_0_1_1 <= 101 ) or y_0_1_1 <= 101)",
    "not( not( x_0_1_1 <= 101 ) or y_0_1_1 == 101)",
    "not(  x_0_1_1 >= 101 or y_0_1_1 >= 101)",
    "Or(And(guard_7, b_0_1_14 == b_0_1_13),And(Not(guard_7), b_0_1_14 == b_0_1_8))",
    "not(x_0_1_1 >= 101)",
    "not 2",
    "1+2",
    "1+2*3",
    "1/2",
    "(1+2)*3",
    "sin(x)*x**2",
    "cos(x)",
    "True and False",
    "not(not(b_0_1_2 * y_0_1_1 == ( 1) and not(x_0_1_1 >= 4)))",
    "sin(w*time)"
]


class v(ast.NodeVisitor):
    sign=1
    compare=0
    def __init__(self):
        self.tokens = []
    def f_continue(self, node):
        super(v, self).generic_visit(node)
    def visit_Add(self, node):
        self.tokens.append('+')
        self.f_continue(node)
    def visit_And(self, node):
        if(self.sign==1):
            self.tokens.append('And')
        else:
            self.tokens.append('Or')
        self.f_continue(node)
    def visit_Or(self, node):
        if(self.sign==1):
            self.tokens.append('Or')
        else:
            self.tokens.append('And')
        self.f_continue(node)
    def visit_Not(self, node):
#        self.tokens.append('NOT')
        self.sign=self.sign*(-1)
        self.f_continue(node)
    def visit_Lt(self, node):
        if(self.sign==1):
            self.tokens.append('<')
        else:
            self.tokens.append('>=')
        self.f_continue(node)
    def visit_LtE(self, node):
        if(self.sign==1):
            self.tokens.append('<=')
        else:
            self.tokens.append('>')
        self.f_continue(node)
    def visit_Gt(self, node):
        if(self.sign==1):
            self.tokens.append('>')
        else:
            self.tokens.append('<=')
        self.f_continue(node)
    def visit_GtE(self, node):
        if(self.sign==1):
            self.tokens.append('>=')
        else:
            self.tokens.append('<')
        self.f_continue(node)
    def visit_NotEq(self, node):
        if(self.sign==1):
            self.tokens.append('/=')
        else:
            self.tokens.append('==')
        self.f_continue(node)
    def visit_Eq(self, node):
        if(self.sign==1):
            self.tokens.append('==')
        else:
            self.tokens.append('/=')
        self.f_continue(node)
    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.op)
        self.visit(node.right)
#        self.tokens.append('(')
#        self.visit(node.op)
#        self.visit(node.left)
#        self.visit(node.right)
#        self.tokens.append(')')
    def visit_UnaryOp(self, node):
        csing=self.sign
        change=0
        self.visit(node.op)
        if(csing!=self.sign):
            change=1
        self.visit(node.operand)
        if(change==1):
            self.sign=(-1)*self.sign
    def visit_Compare(self, node):
#        self.tokens.append('(')
#        for val in node.ops:
#            self.visit(val)
#        self.visit(node.left)
#        for val in node.comparators:
#            self.visit(val)
#        self.tokens.append(')')
        self.compare=1
        self.visit(node.left)
        for val in node.ops:
            self.visit(val)
        for val in node.comparators:
            self.visit(val)
        self.compare=0
    def visit_BoolOp(self, node):
#        self.visit(node.values[0])
#        for val in node.values[1:]:
#            self.visit(node.op)
#            self.visit(val)
        self.visit(node.op)
        self.tokens.append('(')
        for val in node.values[:-1]:
            self.visit(val)
            self.tokens.append(',')
        self.visit(node.values[-1])
        self.tokens.append(')')
    def visit_Call(self, node):
        self.visit(node.func)
        self.tokens.append('(')
        for arg in node.args[:-1]:
            self.visit(arg)
            self.tokens.append(',')
        self.visit(node.args[-1])
        self.tokens.append(')')
    def visit_Div(self, node):
        self.tokens.append('/')
        self.f_continue(node)
    def visit_Expr(self, node):
        self.f_continue(node)
    def visit_Import(self, stmt_import):
        for alias in stmt_import.names:
            print('import name "%s"' % alias.name)
            print('import object %s' % alias)
        self.f_continue(stmt_import)
    def visit_Load(self, node):
        # print('visit_Load')
        self.f_continue(node)
    def visit_Module(self, node):
        # print('visit_Module')
        self.f_continue(node)
    def visit_Mult(self, node):
        self.tokens.append('*')
        self.f_continue(node)
    def visit_Name(self, node):
        if(self.sign==-1 and self.compare==0):
            self.tokens.append("Not")
            self.tokens.append("(")
            self.tokens.append(node.id)
            self.tokens.append(")")
        else:
            self.tokens.append(node.id)
        self.f_continue(node)
    def visit_NameConstant(self, node):
        if(self.sign==-1 and self.compare==0):
            self.tokens.append("Not")
            self.tokens.append("(")
            self.tokens.append(node.value)
            self.tokens.append(")")
        else:
            self.tokens.append(node.value)
        self.f_continue(node)
    def visit_Num(self, node):
        if(self.sign==-1 and self.compare==0):
            self.tokens.append("Not")
            self.tokens.append("(")
            self.tokens.append(node.n)
            self.tokens.append(")")
        else:
            self.tokens.append(node.n)
        self.f_continue(node)
    def visit_Pow(self, node):
        self.tokens.append('pow')
        self.f_continue(node)

for index, f in enumerate(formulas):
    print('{} - {:*^76}'.format(index, f))
    visitor = v()
    visitor.visit(ast.parse(f))
    print(visitor.tokens)
    print(' '.join(map(str, visitor.tokens)))

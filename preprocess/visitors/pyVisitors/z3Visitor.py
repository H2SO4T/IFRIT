#from __future__ import print_function

from z3 import *

class Z3Visitor:
    def visitor(self,e, seen):
        if e in seen:
            return
        seen[e] = True
        yield e
        if is_app(e):
            for ch in e.children():
                for e in self.visitor(ch, seen):
                    yield e
            return
        if is_quantifier(e):
            for e in self.visitor(e.body(), seen):
                yield e
            return

    def getDeclarations(self,constraints):
        seen = {}
        decls=[]
        for e in self.visitor(constraints, seen):
            if is_const(e) and e.decl().kind() == Z3_OP_UNINTERPRETED:
                decls.append(e)


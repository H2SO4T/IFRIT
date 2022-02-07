from pycparser import c_generator, c_ast
from .AssertVisitor import AssertVisitor


def instrument_function(index):
    expressList = [c_ast.Constant(type='string',value='"pp'+str(index)+'"')]
    return (c_ast.FuncCall(c_ast.ID(name="printStates"),c_ast.ExprList(expressList)))



def instrument_ast(node,dictio,index,ppRef):
    if isinstance(node, tuple):
        node = node[1]
    for child in node.children():
        if(dictio[str(child)]=="DELETE" or dictio[str(child)]=="INSERT" or dictio[str(child)]=="TRANSFORM"):
            ppRef.append(tuple([child,child[1].coord.line]))
        else:
            print(child)
            print(dictio[str(child)])
        instrument_ast(child,dictio,index,ppRef)


def instrumentation(ast,dictio):
    index=[0]
    ppRef=[]
    places=[]
#    name=ast.decl.name
    instrument_ast(ast,dictio,index,ppRef)
    print(ppRef)
    for refer in reversed(ppRef):
        print(refer)
        print(dictio[str(refer[0])])
#        if(dictio[str(refer[0])]!='KEEP'):
#            if(isinstance(refer[0],tuple)):
#                place=refer[0][1].block_items
#            else:
#                place=refer[0].block_items
#            if(not(place in places)):
#               places.append(place)
        #       place.insert(0,instrument_function(refer[2]))
#               break
#    contextVis=ContextVisitor(name)
#    contextVis.generic_visit(ast)

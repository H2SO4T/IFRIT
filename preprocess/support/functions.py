from z3 import *
from functools import reduce

def sub(b,ctx=main_ctx()):
    n = b.size()
    bits = [ Extract(i, i, b) for i in range(n) ]
    bvs  = [ Concat(BitVecVal(0, n - 1,ctx=ctx), b) for b in bits ]
    nb   = reduce(lambda a, b: (a + b) % 2, bvs)
    return nb

def readPaths(fileName,l=16):
    F = open(fileName,"r")
    mylist = F.read().splitlines()
    s = Solver()
    for i in range(len(mylist)):
        line = mylist[i]
        typesC= line.split(',')
        if ( typesC[len(typesC)-1] == 'Ints'):
            rightStr = ' '.join(typesC[:-1])
            leftStr = ','.join(typesC[:-1])
            if(len(typesC)>2):
                oper="BitVecs"
            else:
                oper="BitVec"
            exec(leftStr + "= "+ oper +"('"+rightStr+"'"+","+str(l)+")")
        elif (typesC[len(typesC)-1] == 'Bools'):
            guards=[item for item in typesC if "guard" in item]
            rightStr = ' '.join(typesC[:-1])
            leftStr = ','.join(typesC[:-1])
            if(len(typesC)>2):
            	oper="Bools"
            else:
                oper="Bool"
            exec(leftStr + "= "+ oper +"('"+rightStr+"')")
        else:
            s.add(eval(line))
    F.close()
    exec("guardVec = BitVec('guardVec',"+str(len(guards))+")")
    for i,guard in enumerate(guards):
        s.add(eval("If("+guard+", Extract("+str(i)+","+ str(i)+",guardVec)==1, Extract("+str(i)+","+ str(i)+",guardVec)==0)"))
    return s,len(guards)

def readDecls(fileName,l=16):
    F = open(fileName,"r")
    mylist = F.read().splitlines()
    s = Solver()
    decls=[]
    for i in range(len(mylist)):
        line = mylist[i]
        typesC= line.split(',')
        if ( typesC[len(typesC)-1] == 'Ints'):
            decls.append(typesC[:-1])
        elif (typesC[len(typesC)-1] == 'Bools'):
            decls.append(typesC[:-1])
    return decls

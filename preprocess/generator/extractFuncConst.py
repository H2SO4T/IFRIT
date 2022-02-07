from z3 import *
from .InputGenerator import InputGenerator
from ..ga.genAlgMul import GAOptimizerMul
from ..evaluators.UniformComparator import uniformFitness
from ..evaluators.UniformComparator import uniformFitnessGranular
from random import random,randint
import numpy
#ctx = Context()
#f = parse_smt2_file("test.clean.z3",ctx=ctx)
#bitval = BitVecVal(2,32,ctx=ctx)
#_start__y_0_1 = Function('_start__y_0_1', BitVecSort(32,ctx))


#Extra processing


class ConstraintInputGenerator(InputGenerator):
    
    def __init__(self,fileName,functionName,filez3):
        InputGenerator.__init__(self,fileName,functionName)
        self.ctx = Context()
        self.f = parse_smt2_file(filez3,ctx=self.ctx)
#        print(self.f)
        self.lsolvers=[]
        self.forbidden=['if']
        self.sons=self.f.children()
        self.expressions=[]
        self.finalExpr=[]
        #We need to optimize the following parameters
        self.degFreedom=len(self.varNames)-1
        self.pathsProbs=[]#Depends on the number of solvers
        self.exprProb=[]
        self.pMin=[]
        self.pMax=[]
        self.dicti={}
        for pos,var in enumerate(self.varNames):
            if self.varTypes[pos]=="int" or self.varTypes[pos]=="bool":
                self.dicti["_start__"+str(var)+"_0_1"]=eval('Function("'+'_start__'+str(var)+'_0_1",BitVecSort(32,self.ctx))')
#                print("_start__"+str(var)+"_0_1")
            elif self.varTypes[pos]=="float" or  self.varTypes[pos]=="double":
                self.dicti["_start__"+str(var)+"_0_1"]=eval('Function("'+'_start__'+str(var)+'_0_1",FloatDouble(self.ctx))')
            self.exprProb.append(1.0)
            self.pMin.append(-10000)
            self.pMax.append(10000)
            self.finalExpr.append(self.dicti["_start__"+str(var)+"_0_1"]())
        self.dicti.update(globals())

    def stats(self):
        print("DF:" + str(self.degFreedom))
        print("Vars:" + str(len(self.varNames)))
        print("Total Expr:" + str(len(self.exprProb)))
        print("Total Paths:" + str(len(self.pathsProbs)))
        
    def extractPaths(self):
        self.paths=[]
        self.mandatory=[]
        for son in self.sons:
            if(son.decl().name() == 'or'):
                self.paths = self.paths + simplify(son).children()
                self.sons.remove(son)
            elif(son.decl().name() != '='):
                self.mandatory = self.mandatory + [son]
                self.sons.remove(son)

    def simpliSons(self):
        l=[]
        for son in self.sons:
            l.append(simplify(son,elim_and=True))
        self.sonsSimply=l

    def createSolvers(self):
        other=self.sons+self.mandatory
        self.lsolvers=[]
        if(len(self.paths)==0):
            s=Solver(ctx=self.ctx)
            s.add(other)
            self.lsolvers.append(s)
            self.pathsProbs.append(1.0)
        else:
            for i,path in enumerate(self.paths):
                s=Solver(ctx=self.ctx)
                s.add(other)
                s.add(path)
                for extpath in self.paths[:i]+self.paths[(i+1):]:
                    s.push()
                    s.add(Not(extpath))
                    if(s.check()!=sat):
                        s.pop()
                self.lsolvers.append(s)
                self.pathsProbs.append(1.0)

    def extractGodelExp(self,sons):
        for son in sons:
            if(str(son.decl()) in ["<=","<",">","=>"] and (
                    son.children()[0].decl().name() == 'bv' or
                    son.children()[1].decl().name() == 'bv') and
               not(son.children()[0].decl().name() in self.forbidden) and
               not(son.children()[1].decl().name() in self.forbidden)):
               self.expressions.append(son)
            if(son.decl().name() in self.forbidden):
                continue
            if(son.children()):
                self.extractGodelExp(son.children())

    def createGodelConst(self):
        for i,expr in enumerate(self.expressions):
            #self.dicti["godel_p_"+str(i)]=eval('Function("'+'godel_p_'+str(i)+'",BitVecSort(32,self.ctx))')
            left=expr.children()[0]
            right=expr.children()[1]
            if(left.decl().name() == 'bv'):
                if isinstance(left,z3.z3.BitVecNumRef):
                    self.varTypes.append('int')
                else:
                    self.varTypes.append('float')
                self.finalExpr.append(right)
            else:
                if isinstance(right,z3.z3.BitVecNumRef):
                    self.varTypes.append('int')
                else:
                    self.varTypes.append('float')
                self.finalExpr.append(left)
            self.exprProb.append(1.0)
            self.pMin.append(-10000)
            self.pMax.append(10000)

    def finalSetUp(self):
        self.extractPaths()
        self.simpliSons()
        self.extractGodelExp(self.sonsSimply)
        if(self.expressions == None):
            print("No expressions found")
        self.createGodelConst()
        self.createSolvers()

    def getRandomExpres(self):
        q=[random() for i in range(self.degFreedom)]
        totalExp=sum(self.exprProb)
        realProbExp=list([x/totalExp for x in self.exprProb])
        chosenExpr=[]
        chosenExp=0
        finalChoExpr=[]
        for val in q:
            accum=0
            for chosenExp,prob in enumerate(realProbExp):
                accum=accum+prob
                if(val<=accum):
                    break
            if chosenExp not in chosenExpr:
                chosenExpr.append(chosenExp)
        for exprNum in chosenExpr:
#            print(self.varTypes)
#            print(chosenExp)
#            print(realProbExp)
            if(self.varTypes[chosenExp]=="int" or self.varTypes[chosenExp]=="bool"):
                p_value=BitVecVal(randint(round(self.pMin[chosenExp]),round(self.pMax[chosenExp])),32,ctx=self.ctx)
            elif(self.varTypes[chosenExp]=="float" or self.varTypes[chosenExp]=="double"):
                p_value=FPVal(randint(round(self.pMin[chosenExp]),round(self.pMax[chosenExp])),FloatDouble(),ctx=self.ctx)
            else:
                p_value=BitVecVal(randint(round(self.pMin[chosenExp]),round(self.pMax[chosenExp])),32,ctx=self.ctx)
            expr=p_value==self.finalExpr[chosenExp]
            finalChoExpr.append(expr)
#        print(finalChoExpr)
        return(finalChoExpr)
        
    def createInput(self):
        p=random()
        totalSol=sum(self.pathsProbs)
        realProbSol=list([x/totalSol for x in self.pathsProbs])
        accum=0
        chosenSol=0
        for chosenSol,prob in enumerate(realProbSol):
            accum=accum+prob
            if(p<=accum):
                break
        #print(exprs)
        #print(expr)
        if(self.degFreedom > 0):
#            print(chosenSol)
#            print(len(self.lsolvers))
            exprs=self.getRandomExpres()
            self.lsolvers[chosenSol].push()
            self.lsolvers[chosenSol].add(exprs)
            solCheck=self.lsolvers[chosenSol].check()
            if(str(solCheck)=='sat'):
                sol=self.lsolvers[chosenSol].model()
                input=[]
                for pos,var in enumerate(self.varNames):
                    if self.varTypes[pos]=="int" or self.varTypes[pos]=="bool":
                        input.append(sol[self.dicti['_start__'+str(var)+'_0_1']].as_signed_long())
                    elif self.varTypes[pos]=="float" or self.varTypes[pos]=="double":
                        if str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="oo":
                            input.append('INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="+oo":
                            input.append('INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="-oo":
                            input.append('-INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="NaN":
                            input.append('void')
                        else:
                            input.append(eval(str(sol[self.dicti['_start__'+str(var)+'_0_1']])))
                self.lsolvers[chosenSol].pop()
                return(input)
            else:
                self.lsolvers[chosenSol].pop()
        else:
            if(str(self.lsolvers[chosenSol].check())=='sat'):
                sol=self.lsolvers[chosenSol].model()
                input=[]
                for pos,var in enumerate(self.varNames):
                    if self.varTypes[pos]=="int" or self.varTypes[pos]=="bool":
                        input.append(sol[self.dicti['_start__'+str(var)+'_0_1']].as_signed_long())
                    elif self.varTypes[pos]=="float" or self.varTypes[pos]=="double":
                        if str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="oo":
                            input.append('INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="+oo":
                            input.append('INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="-oo":
                            input.append('-INFINITY')
                        elif str(sol[self.dicti['_start__'+str(var)+'_0_1']])=="NaN":
                            input.append('void')
                        else:
                            input.append(eval(str(sol[self.dicti['_start__'+str(var)+'_0_1']])))
                return(input)
#            print(chosenSol)
#            print(chosenExp)
#            print(p_value)
#            print("unsat")

    def setParams(self,individual):
        self.degFreedom=max(round(individual[0]*len(self.varNames)),1)
        self.pathsProbs=individual[1:(len(self.pathsProbs)+1)]
        self.exprProb=individual[(len(self.pathsProbs)+1):(len(self.pathsProbs)+len(self.exprProb)+1)]
        self.pMin=individual[(len(self.pathsProbs)+len(self.exprProb)+1):(len(self.pathsProbs)+2*len(self.exprProb)+1)]
        self.pMin=[elem*(-10000) for elem in self.pMin]
        self.pMax=individual[(len(self.pathsProbs)+len(self.exprProb)+1):(len(self.pathsProbs)+3*len(self.exprProb)+1)]
        self.pMax=[elem*(10000) for elem in self.pMax]

    def randomParams(self):
        totalLength=len(self.pathsProbs)+3*len(self.exprProb)+1
        individual=list([random() for i in range(totalLength)])
        self.setParams(individual)
        
    def fitness(self,individual):
        self.setParams(individual)
        l=[]
        for i in range(100):
            sol=self.createInput()
            if sol: l.append(sol)
        if(len(l)>0):    
        #print(len(numpy.unique(numpy.array(l),axis=0))/len(l),len(l)/100)
            return(uniformFitness(l),len(l)/100)
        else:
            return(0,0)

    def fitnessGranular(self,individual):
        self.setParams(individual)
        l=[]
        for i in range(100):
            sol=self.createInput()
            if sol: l.append(sol)
        if(len(l)>0):    
        #print(len(numpy.unique(numpy.array(l),axis=0))/len(l),len(l)/100)
            return(uniformFitnessGranular(l),len(l)/100)
        else:
            return(0,0)

        
    def ga_config(self):
        self.config = {
            # GA parameters
            'numgen': 30,
            'mut_prob': 0.1,
            'cross_prob': 0.5,
            'num_sel': 10,
            'mu_sel': 300,
            'lambda_sel': 300,
            'inner_mut_prob': 0.05,
            'population_size': 300,
            'tournament_sel': 7,
            'minInt' : -100000,
            'maxInt' : 100000,
            'minFloat': 0.0,
            'maxFloat' : 1.0
        }
        self.config['sizetuples']=1
        self.config['type0']='float'
        self.config['numtuples']=1+len(self.exprProb)*3+len(self.pathsProbs)
        
            
    def optimizeParams(self):
        self.ga_config()
        opti=GAOptimizerMul(self.fitness,self.config)
        parameter=opti.optimize()
        self.setParams(parameter[0])

    def greedyParameters(self):
        self.ga_config()
        opti=GAOptimizerMul(self.fitness,self.config)
        parameter=opti.greedy()
        self.setParams(parameter[0])

    def optimizeParamsGranular(self):
        self.ga_config()
        opti=GAOptimizerMul(self.fitnessGranular,self.config)
        parameter=opti.optimize()
        self.setParams(parameter[0])

    def greedyParametersGranular(self):
        self.ga_config()
        opti=GAOptimizerMul(self.fitnessGranular,self.config)
        parameter=opti.greedy()
        self.setParams(parameter[0])

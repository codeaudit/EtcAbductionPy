# parsecheck.py
# utility for ensuring that knowledge base axioms are well formulated

from __future__ import print_function

import datetime
import argparse
import sys
sys.path.append('../etcabductionpy')
sys.path.append('./etcabductionpy')

import parse
import unify

argparser = argparse.ArgumentParser(description='Utility for ensuring well-formulated knowledge base axioms')

argparser.add_argument('-i', '--infile',
                       nargs='?',
                       type=argparse.FileType('r'),
                       default=sys.stdin,
                       help='Input file to be checked, defaults to STDIN')

argparser.add_argument('-o', '--outfile',
                       nargs='?',
                       type=argparse.FileType('w'),
                       default=sys.stdout,
                       help='Output file, defaults to STDOUT')



def parsecheck(obs, kb):
    '''Utility for ensuring that knowledge base axioms are well formulated'''
    res = "parsecheck.py report at " + str(datetime.datetime.now()) + "\n\n"
    res += str(len(obs)) + " observations, " + str(len(kb)) + " knowledge base axioms\n\n"
    res += "arity warnings: " + arity_warnings(obs, kb) + "\n\n"
    res += "existential warnings: " + str(existential_warnings(kb)) + "\n\n"
    res += "etcetera warnings: " + str(etcetera_warnings(kb))  + "\n\n"
    res += "missing axiom warnings: " + str(missing_axiom_warnings(kb)) + "\n"

    return res

def arity_warnings(obs, kb):
    '''Checks that predicates and functions have consistent arity throughout observations and knowledge base'''
    warnings = ""
    arity = {}
    ls = []
    for dc in kb:
        ls.extend(parse.literals(dc))
    ls.extend(obs)
    all = []
    for l in ls:
        all.append(l)
        all.extend(parse.functions(l))
    for i in all:
        if i[0] in arity:
            if arity[i[0]] != len(i):
                warnings += "\n  inconsistent arity for predicate: " + str(i[0])
        else:
            arity[i[0]] = len(i)
    if len(warnings) == 0:
        return "none"
    else:
        return warnings

def existential_warnings(definite_clauses):
    '''Definite clauses where there are existential variables in the consequent (not found in antecedent)'''
    warnings = ""
    for dc in definite_clauses:
        va = parse.all_variables(parse.antecedent(dc))
        vc = parse.all_variables(parse.consequent(dc))
        for v in vc:
            if v not in va:
                warnings += "\n  existential variables in the consequent: " + parse.display(dc)
                break;
    if len(warnings) == 0:
        return "none"
    else:
        return warnings


    

def etcetera_warnings(definite_clauses):
    '''Definite clauses with malformed etcetera literals'''
    warnings = ""
    seen_etcs = []
    for dc in definite_clauses:
        etcs = [l for l in parse.literals(dc) if l[0][0:3] == 'etc']
        if len(etcs) < 1:
            warnings += "\n  definite clause without etcetera literal: " + parse.display(dc)
        elif len(etcs) > 1:
            warnings += "\n  definite clause with multiple etcetera literals: " + parse.display(dc)
        elif etcs[0][0] in seen_etcs:
            warnings += "\n  etcetera literal previous seen elsewhere: " + parse.display(dc)
        elif len(etcs[0]) < 2:
            warnings += "\n  too few arguments in etcetera literal: " + parse.display(dc)
        elif not isinstance(etcs[0][1], float):
            warnings += "\n  first argument of etcetera literal is not a floating-point number: " + parse.display(dc)
        elif etcs[0][1] > 1.0 or etcs[0][1] < 0.0:
            warnings += "\n  probability of etcetera literal is out of range: " + parse.display(dc)
        elif len(parse.all_variables(etcs[0])) != len(parse.all_variables(dc)):
            warnings += "\n  etcetera literal missing variables founds elsewhere in definite clause: " + parse.display(dc)
        elif len(parse.all_variables([l for l in parse.literals(dc) if l != etcs[0]])) < len(parse.all_variables(etcs[0])):
            warnings += "\n  etcetera literal includes variables not found elsewhere in definite clause: " + parse.display(dc)
        else:
            seen_etcs.append(etcs[0][0])
    if len(warnings) == 0:
        return "none"
    else:
        return warnings


def missing_axiom_warnings(definite_clauses):
    '''Predicates that appear in antecedents but not in any consequent'''
    warnings = ""
    seen_antecedent_predicates = set()
    seen_consequent_predicates = set()
    for dc in definite_clauses:
        seen_consequent_predicates.add(parse.consequent(dc)[0])
        for literal in parse.antecedent(dc):
            if literal[0][0:3] != 'etc':
                seen_antecedent_predicates.add(literal[0])
    for predicate in seen_consequent_predicates:
        if predicate in seen_antecedent_predicates:
            seen_antecedent_predicates.remove(predicate)
    for predicate in seen_antecedent_predicates:
        warnings +="\n  no etcetera axiom for literal: " + predicate
    if len(warnings) == 0:
        return "none"
    else:
        return warnings


    
# run

args = argparser.parse_args()

inlines = args.infile.readlines()
intext = "".join(inlines)
kb, obs = parse.definite_clauses(parse.parse(intext))
obs = unify.standardize(obs)

report = parsecheck(obs, kb)
print(report, file=args.outfile)
sys.exit()

from ply import lex
from ply import yacc

import re

redirect_re = re.compile(r'(\d*)(>&|>>|>|<)')

class IO_Redirect:
    def __init__(self, s):
        match = redirect_re.match(s.value)
        self.filename = None
        self.type = match.group(2)
        fd = match.group(1)

        if fd is None or fd == '':
            if self.type[0] == '>':
                self.fd = 1
            else:
                self.fd = 0
        else:
            self.fd = int(fd)

    def __repr__(self):
        return 'Redirect({}, {}, {})'.format(self.fd, self.type, self.filename)


tokens = 'REDIRECT DQUOTE_LITERAL SQUOTE_LITERAL AND OR WORD_LITERAL NEWLINE'.split()

literals = '\\|();&'

t_ignore_COMMENT = r'\#.*'

def t_REDIRECT(t):
    r'(\d*)(>&|>>|>|<)'
    t.value = IO_Redirect(t)
    return t

def t_DQUOTE_LITERAL(t):
    r'"(.*)?"'
    t.value = t.value[1:-1]
    return t

def t_SQUOTE_LITERAL(t):
    r"'(.*)?'"
    t.value = t.value[1:-1]
    return t

t_AND = r'&&'
t_OR = r'\|\|'

t_WORD_LITERAL = r'[^|;&<>\s]+'

t_NEWLINE = r'\n'

t_ignore = ' \t'

def t_error(t):
    print("Illegal character: '{}'".format(t.value[0]))
    t.lexer.skip(1)

lexer = lex.lex()


class Complete_Command:
    def __init__(self, cmdlist):
        self.cmdlist = cmdlist

    def __repr__(self):
        return 'Complete_Command({})'.format(self.cmdlist)


class Pipeline:
    def __init__(self, cmd):
        self.cmds = [cmd]

    def add(self, cmd):
        self.cmds.append(cmd)

    def __repr__(self):
        return 'Pipeline({})'.format(self.cmds)


class CommandSuffix:
    def __init__(self):
        self.args = []
        self.redirects = []


class Command:
    def __init__(self, name, cmd_suffix=None):
        self.name = name
        if cmd_suffix:
            self.args = cmd_suffix.args
            self.redirects = cmd_suffix.redirects
        else:
            self.args = []
            self.redirects = []

    def __repr__(self):
        return 'Command({} {} {})'.format(self.name, self.args, self.redirects)


def p_complete_command(p):
    '''complete_command : list separator
                        | list'''
    p[0] = Complete_Command(p[1])
    if len(p) > 2 and p[2] == '&':
        p[0].background = True

def p_list(p):
    '''list : list separator_op and_or
            |                   and_or'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = [p[1], p[2], p[3]]

def p_and_or(p):
    '''and_or :                      pipeline
              | and_or AND linebreak pipeline
              | and_or OR  linebreak pipeline'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])
        p[0].append(p[4])

def p_pipeline(p):
    '''pipeline :                        command
                | pipeline '|' linebreak command'''
    if len(p) == 2:
        p[0] = Pipeline(p[1])
    else:
        p[0] = p[1]
        p[0].add(p[4])

def p_command(p):
    '''command : cmd_name cmd_suffix
               | cmd_name'''
    if len(p) == 3:
        p[0] = Command(p[1], p[2])
    else:
        p[0] = Command(p[1])

def p_word(p):
    '''word : WORD_LITERAL
            | DQUOTE_LITERAL
            | SQUOTE_LITERAL'''
    p[0] = p[1]

def p_cmd_name(p):
    '''cmd_name : word'''
    p[0] = p[1]

def p_cmd_suffix(p):
    '''cmd_suffix :            io_redirect
                  | cmd_suffix io_redirect
                  |            word
                  | cmd_suffix word'''
    if len(p) > 2:
        p[0] = p[1]
        if type(p[2]) is str:
            p[0].args.append(p[2])
        else:
            p[0].redirects.append(p[2])
    else:
        p[0] = CommandSuffix()
        if type(p[1]) is str:
            p[0].args.append(p[1])
        else:
            p[0].redirects.append(p[1])

def p_io_redirect(p):
    '''io_redirect : REDIRECT word'''
    p[0] = p[1]
    p[0].filename = p[2]

def p_newline_list(p):
    '''newline_list :              NEWLINE
                    | newline_list NEWLINE'''
    pass

def p_linebreak(p):
    '''linebreak : newline_list
                 | '''
    pass

def p_separator_op(p):
    '''separator_op : '&'
                    | ';' '''
    p[0] = p[1]

def p_separator(p):
    '''separator : separator_op linebreak
                 | newline_list'''
    if len(p) > 2:
        p[0] = p[1]
    else:
        p[0] = '\n'

def p_error(p):
    print("Syntax error at '{}'".format(t.value))


parser = yacc.yacc()


if __name__ == '__main__':
    import unittest

    class TestCase(unittest.TestCase):
        def test_lexer1(self):
            lexer.input('''foobar -a -b arg1 arg2 "a long arg" 'another arg'>/dev/null 2>&1 &''')
            i = iter(lexer)
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, 'foobar')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, '-a')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, '-b')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, 'arg1')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, 'arg2')
            tok = next(i)
            self.assertEqual(tok.type, 'DQUOTE_LITERAL')
            self.assertEqual(tok.value, 'a long arg')
            tok = next(i)
            self.assertEqual(tok.type, 'SQUOTE_LITERAL')
            self.assertEqual(tok.value, 'another arg')
            tok = next(i)
            self.assertEqual(tok.type, 'REDIRECT')
            self.assertEqual(tok.value.type, '>')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, '/dev/null')
            tok = next(i)
            self.assertEqual(tok.type, 'REDIRECT')
            self.assertEqual(tok.value.fd, 2)
            self.assertEqual(tok.value.type, '>&')
            tok = next(i)
            self.assertEqual(tok.type, 'WORD_LITERAL')
            self.assertEqual(tok.value, '1')
            tok = next(i)
            self.assertEqual(tok.value, '&')

        def test_parser1(self):
            result = parser.parse('cat /foo | grep -v poop && bar || foo')
            print('result=', result)

    unittest.main()

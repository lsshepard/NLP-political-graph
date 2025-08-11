
def GET_STANDPOINTS_PROMPT(topic):
    return f'''Sak: {topic}'''


def GET_SUPPORTING_ARGUMENTS_PROMPT(argument, existing_arguments):
    return f'''
    Argument: {argument}
    Existing arguments: {existing_arguments}
'''
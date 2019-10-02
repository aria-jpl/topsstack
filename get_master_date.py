import json


def load_context():
    """loads the context file into a dict"""
    try:
        context_file = '_context.json'
        with open(context_file, 'r') as fin:
            context = json.load(fin)
        return context
    except Exception as e:
        raise Exception('unable to parse _context.json from work directory: %s' % e)


if __name__ == '__main__':
    ctx = load_context()
    master_date = ctx['master_date']

    if master_date:
        print(master_date)  # print it out into a env variable in run_stack.sh
    else:
        pass  # do nothing

from pyramid.view import view_config

@view_config(route_name='hello', request_method='GET', renderer='json')
def hello_world(request):
    return {'hello': 'world!'}

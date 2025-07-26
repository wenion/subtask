# import pyramid

from h.subtask.config import configure
# from h.security import StreamerPolicy
# from h.sentry_filters import SENTRY_FILTERS


def create_app(_global_config, **settings):
    config = configure(settings=settings)

    # config.include("pyramid_services")

    #config.include("h.security")
    # Override the default authentication policy.
    #config.set_security_policy(StreamerPolicy())

    config.include("h.db")
    #config.include("h.session")
    #config.include("h.services")
    config.include("h.pubsub")
    config.include("h.subtask.api")

    # We include links in order to set up the alternative link registrations
    # for annotations.
    #config.include("h.links")

    # And finally we add routes. Static routes are not resolvable by HTTP
    # clients, but can be used for URL generation within the websocket server.
    # config.add_route("ws", "/ws")
    # config.add_route("annotation", "/a/{id}", static=True)
    # config.add_route("api.annotation", "/api/annotations/{id}", static=True)
    config.add_route("hello", "/")
    config.add_route("query", "/query")
    config.add_route('knowledge', '/knowledge')
    config.add_route('upload', '/upload')

    config.add_route('retrieve_ids', '/retrieve_ids')
    config.add_route('update_doc', '/update_doc')
    config.add_route('summarise_shareflow', '/summarise_shareflow')
    config.add_route('shareflow_segmentation', '/shareflow_segmentation')

    # Health check
    config.scan("h.views.status")
    config.add_route("status", "/_status")

    config.scan("h.subtask.views")
    config.scan("h.subtask.streamer")
    '''
    config.add_tween(
        "h.streamer.tweens.close_db_session_tween_factory",
        over=["pyramid_exclog.exclog_tween_factory", pyramid.tweens.EXCVIEW],
    )
    '''

    # Configure sentry
    # config.add_settings(
    #     {
    #         "h_pyramid_sentry.filters": SENTRY_FILTERS,
    #         "h_pyramid_sentry.celery_support": True,
    #     }
    # )

    # config.include("h_pyramid_sentry")

    # Add support for logging exceptions whenever they arise
    config.include("pyramid_exclog")
    config.add_settings({"exclog.extra_info": True})
    return config.make_wsgi_app()

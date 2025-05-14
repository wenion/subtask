from h.subtask import model


def includeme(config):  # pragma: no cover
    repository = config.registry.settings.get("kn.repository")
    database = config.registry.settings.get("kn.database")
    model_name = config.registry.settings.get("kn.model_name")

    # log

    kn = model.Knowledge_Nuggest(model_name, repository, database)
    config.registry["kn"] = kn

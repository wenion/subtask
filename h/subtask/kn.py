from h.subtask import model


def includeme(config):  # pragma: no cover
    # Create the SQLAlchemy engine and save a reference in the app registry.
    kn = model.Knowledge_Nuggest([
                            './KMASS_data/teachHQ-json',
                            './KMASS_data/AoS-json',
                            './KMASS_data/CourseHB-json',
                            './KMASS_data/EDiQ-json',
                            './KMASS_data/UnitHB-json',
                            './KMASS_data/MEA-json',
                            './KMASS_data/teachHQ-video',
                            './KMASS_data/learnHQ-json',
                            './KMASS_data/PolicyBank-pdf',
                            './KMASS_data/CourseMap-pdf',
                            ])
    config.registry["kn"] = kn
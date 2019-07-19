class DataLoader:
    settings = {}

    @classmethod
    def update_settings(cls, **settings):
        cls.settings.update(settings)

    def init(self, reader, parent, settings):
        self.parent = parent
        self.settings = settings
        return True

    def new(self, loader_class, reader=None, **kw):
        kw.update(self.settings)
        new_loader = loader_class(reader)
        new_loader.init(reader, self, kw)
        new_loader.read()
        return new_loader
